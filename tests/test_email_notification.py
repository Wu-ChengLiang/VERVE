"""
邮件通知功能的测试用例
遵循TDD原则，先编写测试再实现功能
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List, Optional

# ✅ 导入已实现的模块
from aiclient.services.email_notification import (
    EmailNotificationService,
    EmailTemplateManager, 
    ContactInfoExtractor
)


class TestContactInfoExtractor:
    """联系信息提取器测试"""
    
    def test_phone_to_email_conversion(self):
        """测试电话号码转邮箱地址"""
        extractor = ContactInfoExtractor()
        
        # 测试正常电话号码
        assert extractor.phone_to_email("19357509506") == "19357509506@163.com"
        assert extractor.phone_to_email("13812345678") == "13812345678@163.com"
        
        # 测试边界情况
        assert extractor.phone_to_email("") == ""
        assert extractor.phone_to_email(None) == ""
    
    def test_email_validation(self):
        """测试邮箱地址验证"""
        extractor = ContactInfoExtractor()
        
        # 有效邮箱
        assert extractor.is_valid_email("19357509506@163.com") == True
        assert extractor.is_valid_email("test@qq.com") == True
        
        # 无效邮箱
        assert extractor.is_valid_email("invalid-email") == False
        assert extractor.is_valid_email("@163.com") == False
        assert extractor.is_valid_email("") == False
        assert extractor.is_valid_email(None) == False


class TestEmailTemplateManager:
    """邮件模板管理器测试"""
    
    def test_customer_confirmation_template(self):
        """测试客户预约确认邮件模板"""
        manager = EmailTemplateManager()
        
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "19357509506",
            "therapist_name": "李技师",
            "appointment_date": "2024-03-15",
            "appointment_time": "14:00",
            "service_type": "按摩服务",
            "store_name": "中心店"
        }
        
        subject, body = manager.generate_customer_confirmation_email(appointment_info)
        
        # 验证邮件主题
        assert "预约确认" in subject
        assert "张三" in subject
        
        # 验证邮件内容包含关键信息
        assert "张三" in body
        assert "李技师" in body
        assert "2024-03-15" in body
        assert "14:00" in body
        assert "按摩服务" in body
        assert "中心店" in body
    
    def test_therapist_notification_template(self):
        """测试技师新预约通知邮件模板"""
        manager = EmailTemplateManager()
        
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "19357509506",
            "therapist_name": "李技师",
            "appointment_date": "2024-03-15",
            "appointment_time": "14:00",
            "service_type": "按摩服务",
            "store_name": "中心店"
        }
        
        subject, body = manager.generate_therapist_notification_email(appointment_info)
        
        # 验证邮件主题
        assert "新预约通知" in subject
        assert "李技师" in subject
        
        # 验证邮件内容包含关键信息
        assert "李技师" in body
        assert "张三" in body
        assert "19357509506" in body
        assert "2024-03-15" in body
        assert "14:00" in body


@pytest.mark.asyncio
class TestEmailNotificationService:
    """邮件通知服务测试"""
    
    @pytest.fixture
    def mock_email_sender(self):
        """模拟邮件发送器"""
        return AsyncMock()
    
    @pytest.fixture  
    def mock_database_service(self):
        """模拟数据库服务"""
        mock_service = AsyncMock()
        # 模拟技师查询结果
        mock_service.search_therapists.return_value = [
            {
                "id": 1,
                "name": "李技师",
                "phone": "13812345678",
                "store_name": "中心店"
            }
        ]
        return mock_service
    
    @pytest.fixture
    def email_service(self, mock_email_sender, mock_database_service):
        """邮件通知服务实例"""
        return EmailNotificationService(
            email_sender=mock_email_sender,
            database_service=mock_database_service
        )
    
    async def test_send_customer_confirmation_email_success(self, email_service, mock_email_sender):
        """测试发送客户确认邮件成功场景"""
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "19357509506",
            "therapist_id": 1,
            "appointment_date": "2024-03-15",
            "appointment_time": "14:00",
            "service_type": "按摩服务"
        }
        
        # 模拟邮件发送成功
        mock_email_sender.execute.return_value = "邮件已成功发送至 19357509506@163.com"
        
        result = await email_service.send_customer_confirmation_email(appointment_info)
        
        # 验证结果
        assert result["success"] == True
        assert "19357509506@163.com" in result["message"]
        
        # 验证邮件发送器被正确调用
        mock_email_sender.execute.assert_called_once()
        call_args = mock_email_sender.execute.call_args[1]
        assert call_args["recipient_email"] == "19357509506@163.com"
        assert "预约确认" in call_args["subject"]
        assert "张三" in call_args["body"]
    
    async def test_send_therapist_notification_email_success(self, email_service, mock_email_sender, mock_database_service):
        """测试发送技师通知邮件成功场景"""
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "19357509506", 
            "therapist_id": 1,
            "appointment_date": "2024-03-15",
            "appointment_time": "14:00",
            "service_type": "按摩服务"
        }
        
        # 模拟邮件发送成功
        mock_email_sender.execute.return_value = "邮件已成功发送至 13812345678@163.com"
        
        result = await email_service.send_therapist_notification_email(appointment_info)
        
        # 验证结果
        assert result["success"] == True
        assert "13812345678@163.com" in result["message"]
        
        # 验证数据库查询被调用
        mock_database_service.search_therapists.assert_called_once()
        
        # 验证邮件发送器被正确调用
        mock_email_sender.execute.assert_called_once()
        call_args = mock_email_sender.execute.call_args[1]
        assert call_args["recipient_email"] == "13812345678@163.com"
        assert "新预约通知" in call_args["subject"]
        assert "李技师" in call_args["body"]
    
    async def test_send_appointment_notification_emails_complete_flow(self, email_service, mock_email_sender, mock_database_service):
        """测试完整的预约邮件通知流程"""
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "19357509506",
            "therapist_id": 1,
            "appointment_date": "2024-03-15", 
            "appointment_time": "14:00",
            "service_type": "按摩服务"
        }
        
        # 模拟两次邮件发送都成功
        mock_email_sender.execute.side_effect = [
            "邮件已成功发送至 19357509506@163.com",  # 客户邮件
            "邮件已成功发送至 13812345678@163.com"   # 技师邮件
        ]
        
        result = await email_service.send_appointment_notification_emails(appointment_info)
        
        # 验证整体结果
        assert result["success"] == True
        assert len(result["details"]) == 2
        
        # 验证客户邮件发送结果
        customer_result = result["details"][0]
        assert customer_result["type"] == "customer_confirmation"
        assert customer_result["success"] == True
        assert "19357509506@163.com" in customer_result["message"]
        
        # 验证技师邮件发送结果  
        therapist_result = result["details"][1]
        assert therapist_result["type"] == "therapist_notification"
        assert therapist_result["success"] == True
        assert "13812345678@163.com" in therapist_result["message"]
        
        # 验证邮件发送器被调用两次
        assert mock_email_sender.execute.call_count == 2
    
    async def test_error_handling_invalid_phone(self, email_service):
        """测试无效电话号码的错误处理"""
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "",  # 无效电话
            "therapist_id": 1,
            "appointment_date": "2024-03-15",
            "appointment_time": "14:00"
        }
        
        result = await email_service.send_customer_confirmation_email(appointment_info)
        
        assert result["success"] == False
        assert "无效的客户电话" in result["error"]
    
    async def test_error_handling_therapist_not_found(self, email_service, mock_database_service):
        """测试技师未找到的错误处理"""
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "19357509506",
            "therapist_id": 999,  # 不存在的技师ID
            "appointment_date": "2024-03-15",
            "appointment_time": "14:00"
        }
        
        # 模拟技师查询为空
        mock_database_service.search_therapists.return_value = []
        
        result = await email_service.send_therapist_notification_email(appointment_info)
        
        assert result["success"] == False
        assert "技师信息未找到" in result["error"]
    
    async def test_error_handling_email_send_failure(self, email_service, mock_email_sender):
        """测试邮件发送失败的错误处理"""
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "19357509506",
            "appointment_date": "2024-03-15",
            "appointment_time": "14:00"
        }
        
        # 模拟邮件发送失败
        mock_email_sender.execute.return_value = "发送邮件失败：SMTP连接错误"
        
        result = await email_service.send_customer_confirmation_email(appointment_info)
        
        assert result["success"] == False
        assert "SMTP连接错误" in result["error"]


class TestFunctionCallIntegration:
    """Function Call集成测试"""
    
    def test_send_appointment_emails_function_definition(self):
        """测试邮件发送function call定义"""
        from aiclient.adapters.openai_adapter import OpenAIAdapter
        from aiclient.config import ModelConfig
        
        # 创建一个模拟的配置
        mock_config = ModelConfig(
            provider="openai",
            model_name="gpt-3.5-turbo",
            api_key="test-key",
            base_url="https://api.openai.com/v1"
        )
        
        # 创建OpenAI适配器实例
        adapter = OpenAIAdapter(mock_config)
        tools = adapter.get_email_notification_tools()
        
        # 验证工具定义存在
        assert len(tools) > 0
        
        # 查找邮件发送工具
        email_tool = None
        for tool in tools:
            if tool["function"]["name"] == "send_appointment_emails":
                email_tool = tool
                break
        
        assert email_tool is not None
        assert email_tool["type"] == "function"
        
        # 验证参数定义
        params = email_tool["function"]["parameters"]
        required_params = params["required"]
        assert "customer_name" in required_params
        assert "customer_phone" in required_params
        assert "therapist_id" in required_params
        assert "appointment_date" in required_params
        assert "appointment_time" in required_params


# ✅ 性能测试
class TestEmailNotificationPerformance:
    """邮件通知性能测试"""
    
    @pytest.mark.asyncio
    async def test_concurrent_email_sending(self):
        """测试并发邮件发送性能"""
        # 创建多个预约信息
        appointments = [
            {
                "customer_name": f"客户{i}",
                "customer_phone": f"1995750950{i}",
                "therapist_id": 1,
                "appointment_date": "2024-03-15",
                "appointment_time": "14:00"
            }
            for i in range(10)
        ]
        
        # 模拟并发发送
        mock_email_sender = AsyncMock()
        mock_database_service = AsyncMock()
        mock_database_service.search_therapists.return_value = [{
            "id": 1, "name": "李技师", "phone": "13812345678"
        }]
        
        email_service = EmailNotificationService(
            email_sender=mock_email_sender,
            database_service=mock_database_service  
        )
        
        # 并发执行
        tasks = [
            email_service.send_appointment_notification_emails(appointment)
            for appointment in appointments
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 验证所有任务都成功完成
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) == len(appointments)


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 