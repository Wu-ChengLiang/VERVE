import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr  # 新增

from app.config import config
from app.tool.base import BaseTool


class EmailSender(BaseTool):
    name: str = "email_sender"
    description: str = """向指定收件人发送电子邮件。
当您需要发送通知、警报或其他通信时使用此工具。
该工具需要接收收件人邮箱地址、邮件主题和邮件正文。
"""
    parameters: dict = {
        "type": "object",
        "properties": {
            "recipient_email": {
                "type": "string",
                "description": "(必填) 收件人的邮箱地址",
            },
            "subject": {
                "type": "string",
                "description": "(必填) 邮件的主题",
            },
            "body": {
                "type": "string",
                "description": "(必填) 邮件的正文内容",
            },
        },
        "required": ["recipient_email", "subject", "body"],
    }

    async def execute(self, recipient_email: str, subject: str, body: str) -> str:
        try:
            sender_email = config.email_config.sender_email
            smtp_password = config.email_config.smtp_password
            smtp_server = config.email_config.smtp_server
            server_port = config.email_config.server_port

            if not sender_email or not smtp_password:
                raise ValueError(
                    "邮箱配置无效！请检查config.toml配置文件中[email]部分的 "
                    "sender_email和smtp_password参数是否已正确设置。"
                )

            message = MIMEMultipart()
            message["From"] = formataddr(("系统发件人", sender_email))
            message["To"] = formataddr(("用户", recipient_email))
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain", "utf-8"))

            try:
                # 保持原有端口判断逻辑 注意587端口会失效
                if server_port == 465:
                    server = smtplib.SMTP_SSL(smtp_server, 465, timeout=15)
                elif server_port == 587:
                    server = smtplib.SMTP(smtp_server, 587, timeout=15)
                    server.ehlo()
                    server.starttls()
                    server.ehlo()
                elif server_port == 25:
                    server = smtplib.SMTP(smtp_server, 25)
                else:
                    raise ValueError("不支持的端口号")

                try:
                    server.login(sender_email, smtp_password)
                    server.sendmail(sender_email, recipient_email, message.as_string())
                    return f"邮件已成功发送至 {recipient_email}"
                except smtplib.SMTPAuthenticationError:
                    raise ValueError(
                        "邮箱认证失败！请检查密码是否正确，"
                        "并确认已开启SMTP服务（如Gmail需开启'低安全性应用访问'）"
                    )
                finally:
                    if "server" in locals():
                        server.quit()

            except smtplib.SMTPException as e:
                raise ValueError(f"SMTP协议错误：{str(e)}")

        except Exception as e:
            return f"向 {recipient_email} 发送邮件失败：{str(e)}"
