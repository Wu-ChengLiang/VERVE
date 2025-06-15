"""
邮件通知服务实现
支持预约确认和技师通知邮件发送
"""

import re
import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


class ContactInfoExtractor:
    """联系信息提取器"""
    
    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)
        # 邮箱验证正则表达式
        self.email_pattern = re.compile(
            r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        )
    
    def phone_to_email(self, phone: Optional[str]) -> str:
        """
        将电话号码转换为163邮箱地址
        
        Args:
            phone: 电话号码
            
        Returns:
            str: 邮箱地址，如果电话无效则返回空字符串
        """
        if not phone or not isinstance(phone, str):
            return ""
        
        phone = phone.strip()
        if not phone:
            return ""
        
        # ✅ 已添加基础验证，可进一步扩展电话号码格式验证
        self.logger.debug(f"转换电话号码 {phone} 为邮箱地址")
        return f"{phone}@163.com"
    
    def is_valid_email(self, email: Optional[str]) -> bool:
        """
        验证邮箱地址是否有效
        
        Args:
            email: 邮箱地址
            
        Returns:
            bool: 是否有效
        """
        if not email or not isinstance(email, str):
            return False
        
        return bool(self.email_pattern.match(email.strip()))


class EmailTemplateManager:
    """邮件模板管理器"""
    
    def __init__(self):
        self.logger = logger.getChild(self.__class__.__name__)
    
    def generate_customer_confirmation_email(self, appointment_info: Dict[str, Any]) -> Tuple[str, str]:
        """
        生成客户预约确认邮件
        
        Args:
            appointment_info: 预约信息
            
        Returns:
            Tuple[str, str]: (主题, 邮件内容)
        """
        customer_name = appointment_info.get("customer_name", "客户")
        therapist_name = appointment_info.get("therapist_name", "技师")
        appointment_date = appointment_info.get("appointment_date", "")
        appointment_time = appointment_info.get("appointment_time", "")
        service_type = appointment_info.get("service_type", "服务")
        store_name = appointment_info.get("store_name", "门店")
        
        # 邮件主题
        subject = f"【预约确认】{customer_name}您的预约已确认"
        
        # 邮件内容
        body = f"""尊敬的{customer_name}，您好！

您的预约已成功确认，详情如下：

📋 预约信息：
• 服务项目：{service_type}
• 预约日期：{appointment_date}
• 预约时间：{appointment_time}
• 服务技师：{therapist_name}
• 服务门店：{store_name}

📞 温馨提示：
• 请提前10分钟到达门店
• 如需修改或取消预约，请及时联系我们
• 感谢您的信任与支持！

此邮件为系统自动发送，请勿直接回复。
如有疑问请联系客服。

{datetime.now().strftime('%Y年%m月%d日 %H:%M')}"""
        
        self.logger.info(f"生成客户确认邮件: {customer_name} - {appointment_date} {appointment_time}")
        return subject, body
    
    def generate_therapist_notification_email(self, appointment_info: Dict[str, Any]) -> Tuple[str, str]:
        """
        生成技师新预约通知邮件
        
        Args:
            appointment_info: 预约信息
            
        Returns:
            Tuple[str, str]: (主题, 邮件内容)
        """
        therapist_name = appointment_info.get("therapist_name", "技师")
        customer_name = appointment_info.get("customer_name", "客户")
        customer_phone = appointment_info.get("customer_phone", "")
        appointment_date = appointment_info.get("appointment_date", "")
        appointment_time = appointment_info.get("appointment_time", "")
        service_type = appointment_info.get("service_type", "服务")
        store_name = appointment_info.get("store_name", "门店")
        notes = appointment_info.get("notes", "")
        
        # 邮件主题
        subject = f"【新预约通知】{therapist_name}，您有新的预约"
        
        # 邮件内容
        body = f"""亲爱的{therapist_name}，您好！

您有一个新的预约，请注意安排：

👤 客户信息：
• 客户姓名：{customer_name}
• 联系电话：{customer_phone}

📋 预约详情：
• 服务项目：{service_type}
• 预约日期：{appointment_date}
• 预约时间：{appointment_time}
• 服务门店：{store_name}"""
        
        if notes:
            body += f"\n• 备注信息：{notes}"
        
        body += f"""

📝 注意事项：
• 请提前准备相关服务用品
• 如有时间冲突请及时联系管理员
• 请确保按时到岗为客户提供优质服务

此邮件为系统自动发送，请勿直接回复。
如有疑问请联系管理员。

{datetime.now().strftime('%Y年%m月%d日 %H:%M')}"""
        
        self.logger.info(f"生成技师通知邮件: {therapist_name} - {customer_name} - {appointment_date} {appointment_time}")
        return subject, body


@dataclass
class EmailSendResult:
    """邮件发送结果"""
    success: bool
    message: str
    error: Optional[str] = None
    recipient_email: Optional[str] = None
    email_type: Optional[str] = None


class EmailNotificationService:
    """邮件通知服务"""
    
    def __init__(self, email_sender=None, database_service=None):
        """
        初始化邮件通知服务
        
        Args:
            email_sender: 邮件发送器实例
            database_service: 数据库服务实例
        """
        self.email_sender = email_sender
        self.database_service = database_service
        self.contact_extractor = ContactInfoExtractor()
        self.template_manager = EmailTemplateManager()
        self.logger = logger.getChild(self.__class__.__name__)
    
    async def send_customer_confirmation_email(self, appointment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送客户预约确认邮件
        
        Args:
            appointment_info: 预约信息
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            # 验证客户电话
            customer_phone = appointment_info.get("customer_phone", "").strip()
            if not customer_phone:
                return {
                    "success": False,
                    "error": "无效的客户电话号码",
                    "message": "客户电话号码不能为空"
                }
            
            # 生成客户邮箱地址
            customer_email = self.contact_extractor.phone_to_email(customer_phone)
            if not self.contact_extractor.is_valid_email(customer_email):
                return {
                    "success": False,
                    "error": "无效的客户邮箱地址",
                    "message": f"无法生成有效的邮箱地址: {customer_email}"
                }
            
            # 生成邮件内容
            subject, body = self.template_manager.generate_customer_confirmation_email(appointment_info)
            
            # 发送邮件
            self.logger.info(f"发送客户确认邮件: {customer_email}")
            send_result = await self.email_sender.execute(
                recipient_email=customer_email,
                subject=subject,
                body=body
            )
            
            # 检查发送结果
            if "成功发送" in send_result:
                return {
                    "success": True,
                    "message": send_result,
                    "recipient_email": customer_email,
                    "email_type": "customer_confirmation"
                }
            else:
                return {
                    "success": False,
                    "error": send_result,
                    "message": f"客户邮件发送失败: {send_result}",
                    "recipient_email": customer_email
                }
        
        except Exception as e:
            self.logger.error(f"发送客户确认邮件失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"发送客户确认邮件时发生错误: {e}"
            }
    
    async def send_therapist_notification_email(self, appointment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送技师新预约通知邮件
        
        Args:
            appointment_info: 预约信息
            
        Returns:
            Dict[str, Any]: 发送结果
        """
        try:
            # 查询技师信息
            therapist_id = appointment_info.get("therapist_id")
            if not therapist_id:
                return {
                    "success": False,
                    "error": "缺少技师ID",
                    "message": "无法确定技师信息"
                }
            
            # 通过数据库服务查询技师详细信息
            therapists = await self.database_service.search_therapists()
            therapist_info = None
            
            for therapist in therapists:
                if therapist.get("id") == therapist_id:
                    therapist_info = therapist
                    break
            
            if not therapist_info:
                return {
                    "success": False,
                    "error": "技师信息未找到",
                    "message": f"无法找到ID为{therapist_id}的技师信息"
                }
            
            # 获取技师电话并生成邮箱地址
            therapist_phone = therapist_info.get("phone", "").strip()
            if not therapist_phone:
                return {
                    "success": False,
                    "error": "技师电话号码缺失",
                    "message": f"技师{therapist_info.get('name', '')}的电话号码不存在"
                }
            
            therapist_email = self.contact_extractor.phone_to_email(therapist_phone)
            if not self.contact_extractor.is_valid_email(therapist_email):
                return {
                    "success": False,
                    "error": "无效的技师邮箱地址",
                    "message": f"无法生成有效的技师邮箱地址: {therapist_email}"
                }
            
            # 补充预约信息中的技师名称和门店信息
            enhanced_appointment_info = appointment_info.copy()
            enhanced_appointment_info["therapist_name"] = therapist_info.get("name", "技师")
            enhanced_appointment_info["store_name"] = therapist_info.get("store_name", "门店")
            
            # 生成邮件内容
            subject, body = self.template_manager.generate_therapist_notification_email(enhanced_appointment_info)
            
            # 发送邮件
            self.logger.info(f"发送技师通知邮件: {therapist_email}")
            send_result = await self.email_sender.execute(
                recipient_email=therapist_email,
                subject=subject,
                body=body
            )
            
            # 检查发送结果
            if "成功发送" in send_result:
                return {
                    "success": True,
                    "message": send_result,
                    "recipient_email": therapist_email,
                    "email_type": "therapist_notification",
                    "therapist_name": therapist_info.get("name", "技师")
                }
            else:
                return {
                    "success": False,
                    "error": send_result,
                    "message": f"技师邮件发送失败: {send_result}",
                    "recipient_email": therapist_email
                }
        
        except Exception as e:
            self.logger.error(f"发送技师通知邮件失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"发送技师通知邮件时发生错误: {e}"
            }
    
    async def send_appointment_notification_emails(self, appointment_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送完整的预约通知邮件（客户确认 + 技师通知）
        
        Args:
            appointment_info: 预约信息
            
        Returns:
            Dict[str, Any]: 完整的发送结果
        """
        self.logger.info(f"开始发送预约通知邮件: 客户={appointment_info.get('customer_name')} 技师ID={appointment_info.get('therapist_id')}")
        
        results = []
        overall_success = True
        
        try:
            # 1. 发送客户确认邮件
            self.logger.debug("发送客户确认邮件...")
            customer_result = await self.send_customer_confirmation_email(appointment_info)
            customer_result["type"] = "customer_confirmation"
            results.append(customer_result)
            
            if not customer_result["success"]:
                overall_success = False
                self.logger.warning(f"客户邮件发送失败: {customer_result.get('error')}")
            
            # 2. 发送技师通知邮件
            self.logger.debug("发送技师通知邮件...")
            therapist_result = await self.send_therapist_notification_email(appointment_info)
            therapist_result["type"] = "therapist_notification"
            results.append(therapist_result)
            
            if not therapist_result["success"]:
                overall_success = False
                self.logger.warning(f"技师邮件发送失败: {therapist_result.get('error')}")
            
            # 汇总结果
            success_count = sum(1 for r in results if r["success"])
            total_count = len(results)
            
            summary_message = f"邮件发送完成: {success_count}/{total_count} 成功"
            if overall_success:
                summary_message += " - 所有邮件发送成功"
            else:
                summary_message += " - 部分邮件发送失败"
            
            self.logger.info(summary_message)
            
            return {
                "success": overall_success,
                "message": summary_message,
                "details": results,
                "summary": {
                    "total_emails": total_count,
                    "successful_emails": success_count,
                    "failed_emails": total_count - success_count
                }
            }
        
        except Exception as e:
            self.logger.error(f"发送预约通知邮件时发生异常: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"发送预约通知邮件时发生异常: {e}",
                "details": results
            } 