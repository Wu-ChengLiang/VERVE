"""
EmailSender适配器
将现有的EmailSender类包装成我们邮件通知服务需要的接口
"""

import logging
from typing import Dict, Any
import sys
import os

logger = logging.getLogger(__name__)


class EmailSenderAdapter:
    """EmailSender适配器类"""
    
    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)
        self._email_sender = None
        self._init_error = None
        self._init_email_sender()
    
    def _init_email_sender(self):
        """初始化EmailSender实例"""
        try:
            # 添加sender目录到Python路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(os.path.dirname(current_dir))
            sender_path = os.path.join(project_root, 'sender')
            
            self.logger.info(f"当前目录: {current_dir}")
            self.logger.info(f"项目根目录: {project_root}")
            self.logger.info(f"Sender路径: {sender_path}")
            self.logger.info(f"Sender路径是否存在: {os.path.exists(sender_path)}")
            
            if sender_path not in sys.path:
                sys.path.append(sender_path)
                self.logger.info(f"已添加到sys.path: {sender_path}")
            
            # 尝试导入EmailSender相关模块
            try:
                # 检查是否存在app模块
                app_path = os.path.join(sender_path, 'app')
                self.logger.info(f"App路径: {app_path}, 存在: {os.path.exists(app_path)}")
                
                # 如果app目录不存在，使用独立的EmailSender
                if not os.path.exists(app_path):
                    self.logger.warning("app模块不存在，将创建独立的EmailSender")
                    self._create_standalone_email_sender(sender_path)
                    return
                
                # 尝试导入原始EmailSender
                from email_sender import EmailSender
                self._email_sender = EmailSender()
                self.logger.info("EmailSender适配器初始化成功")
                
            except ImportError as import_error:
                self.logger.error(f"导入EmailSender失败: {import_error}")
                # 尝试创建独立版本
                self._create_standalone_email_sender(sender_path)
            
        except Exception as e:
            self.logger.error(f"初始化EmailSender失败: {e}")
            self._email_sender = None
            self._init_error = str(e)
    
    def _create_standalone_email_sender(self, sender_path: str):
        """创建独立的EmailSender实例"""
        try:
            import toml
            import smtplib
            from email.mime.multipart import MIMEMultipart
            from email.mime.text import MIMEText
            from email.utils import formataddr
            
            # 读取配置文件
            config_path = os.path.join(sender_path, 'config.toml')
            self.logger.info(f"配置文件路径: {config_path}, 存在: {os.path.exists(config_path)}")
            
            if not os.path.exists(config_path):
                raise FileNotFoundError(f"配置文件不存在: {config_path}")
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = toml.load(f)
            
            email_config = config.get('email', {})
            self.logger.info(f"邮件配置: {email_config}")
            
            # 创建独立的EmailSender类
            class StandaloneEmailSender:
                def __init__(self, email_config):
                    self.sender_email = email_config.get('sender_email')
                    self.smtp_password = email_config.get('smtp_password')
                    self.smtp_server = email_config.get('smtp_server')
                    self.server_port = email_config.get('server_port')
                    
                    if not self.sender_email or not self.smtp_password:
                        raise ValueError(
                            "邮箱配置无效！请检查config.toml配置文件中[email]部分的 "
                            "sender_email和smtp_password参数是否已正确设置。"
                        )
                
                async def execute(self, recipient_email: str, subject: str, body: str) -> str:
                    try:
                        message = MIMEMultipart()
                        message["From"] = formataddr(("系统发件人", self.sender_email))
                        message["To"] = formataddr(("用户", recipient_email))
                        message["Subject"] = subject
                        message.attach(MIMEText(body, "plain", "utf-8"))

                        # 根据端口选择连接方式
                        if self.server_port == 465:
                            server = smtplib.SMTP_SSL(self.smtp_server, 465, timeout=15)
                        elif self.server_port == 587:
                            server = smtplib.SMTP(self.smtp_server, 587, timeout=15)
                            server.ehlo()
                            server.starttls()
                            server.ehlo()
                        elif self.server_port == 25:
                            server = smtplib.SMTP(self.smtp_server, 25)
                        else:
                            raise ValueError(f"不支持的端口号: {self.server_port}")

                        try:
                            server.login(self.sender_email, self.smtp_password)
                            server.sendmail(self.sender_email, recipient_email, message.as_string())
                            return f"邮件已成功发送至 {recipient_email}"
                        except smtplib.SMTPAuthenticationError:
                            raise ValueError(
                                "邮箱认证失败！请检查密码是否正确，"
                                "并确认已开启SMTP服务"
                            )
                        finally:
                            if "server" in locals():
                                server.quit()

                    except smtplib.SMTPException as e:
                        raise ValueError(f"SMTP协议错误：{str(e)}")
                    except Exception as e:
                        return f"向 {recipient_email} 发送邮件失败：{str(e)}"
            
            self._email_sender = StandaloneEmailSender(email_config)
            self.logger.info("独立EmailSender创建成功")
            
        except Exception as e:
            self.logger.error(f"创建独立EmailSender失败: {e}")
            self._email_sender = None
            self._init_error = str(e)
    
    async def execute(self, recipient_email: str, subject: str, body: str) -> str:
        """
        发送邮件的适配器方法
        
        Args:
            recipient_email: 收件人邮箱
            subject: 邮件主题
            body: 邮件内容
            
        Returns:
            str: 发送结果消息
        """
        if not self._email_sender:
            error_details = f"初始化错误: {self._init_error}" if self._init_error else "未知原因"
            error_msg = f"EmailSender未正确初始化，无法发送邮件。{error_details}"
            self.logger.error(error_msg)
            return f"发送邮件失败：{error_msg}"
        
        try:
            self.logger.info(f"通过适配器发送邮件: {recipient_email}")
            self.logger.debug(f"邮件主题: {subject}")
            self.logger.debug(f"邮件内容长度: {len(body)} 字符")
            
            # 调用EmailSender的execute方法
            result = await self._email_sender.execute(
                recipient_email=recipient_email,
                subject=subject,
                body=body
            )
            
            self.logger.info(f"邮件发送结果: {result}")
            return result
            
        except Exception as e:
            error_msg = f"发送邮件时发生异常: {e}"
            self.logger.error(error_msg)
            return f"发送邮件失败：{error_msg}" 