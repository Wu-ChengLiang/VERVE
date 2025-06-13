"""
AI客户端测试
"""

import asyncio
import pytest
from unittest.mock import Mock, patch
from aiclient import AIClient, AIProvider, AIResponse


class TestAIClient:
    """AI客户端测试类"""
    
    def setup_method(self):
        """测试前置设置"""
        self.client = AIClient()
    
    def test_client_initialization(self):
        """测试客户端初始化"""
        assert self.client is not None
        assert isinstance(self.client.adapters, dict)
        assert len(self.client.adapters) >= 0
    
    def test_is_customer_message_positive(self):
        """测试客户消息识别 - 正例"""
        data_list = [
            {"content": "[商家] 您好，有什么可以帮助您的吗？"},
            {"content": "[客户] 您好，我需要女技师为我服务，预计18:30到店"}
        ]
        
        is_customer, message = self.client.is_customer_message(data_list)
        
        assert is_customer is True
        assert message == "您好，我需要女技师为我服务，预计18:30到店"
    
    def test_is_customer_message_negative(self):
        """测试客户消息识别 - 负例"""
        data_list = [
            {"content": "[客户] 我想预约服务"},
            {"content": "[商家] 好的，为您安排"}
        ]
        
        is_customer, message = self.client.is_customer_message(data_list)
        
        assert is_customer is False
        assert message is None
    
    def test_is_customer_message_empty(self):
        """测试空数据列表"""
        data_list = []
        
        is_customer, message = self.client.is_customer_message(data_list)
        
        assert is_customer is False
        assert message is None
    
    @pytest.mark.asyncio
    async def test_process_scraped_data_customer_message(self):
        """测试处理客户消息数据"""
        data_list = [
            {"content": "[客户] 我想了解一下服务项目"}
        ]
        
        # Mock AI回复
        mock_response = AIResponse(
            content="您好！我们提供多种专业服务项目，包括...",
            model="test-model",
            provider="test"
        )
        
        with patch.object(self.client, 'generate_customer_service_reply', return_value=mock_response):
            response = await self.client.process_scraped_data(data_list)
            
            assert response is not None
            assert response.content.startswith("您好！")
    
    @pytest.mark.asyncio
    async def test_process_scraped_data_no_customer_message(self):
        """测试处理非客户消息数据"""
        data_list = [
            {"content": "[商家] 欢迎光临"}
        ]
        
        response = await self.client.process_scraped_data(data_list)
        
        assert response is None
    
    def test_get_status(self):
        """测试获取状态"""
        status = self.client.get_status()
        
        assert "available_providers" in status
        assert "total_providers" in status
        assert "config_loaded" in status
        assert isinstance(status["available_providers"], list)


def run_quick_test():
    """快速测试函数"""
    print("🧪 开始AI客户端快速测试...")
    
    # 测试配置加载
    client = AIClient()
    print(f"✅ 客户端初始化成功，可用提供商: {len(client.adapters)}")
    
    # 测试消息识别
    test_data = [
        {"content": "[客户] 您好，我需要女技师为我服务，预计18:30到店"}
    ]
    
    is_customer, message = client.is_customer_message(test_data)
    print(f"✅ 消息识别测试: 是客户消息={is_customer}, 内容='{message[:30]}...'")
    
    # 测试状态获取
    status = client.get_status()
    print(f"✅ 状态获取测试: {status}")
    
    print("🎉 AI客户端核心功能测试通过！")


if __name__ == "__main__":
    run_quick_test() 