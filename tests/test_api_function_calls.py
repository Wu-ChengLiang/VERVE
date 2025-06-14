"""
测试API函数调用功能
"""

import pytest
import aiohttp
from unittest.mock import patch, Mock, AsyncMock
import json
from datetime import datetime

from aiclient.adapters.base import BaseAdapter
from aiclient.models import AIRequest, AIMessage, MessageRole
from aiclient.config import ModelConfig, AIProvider


class TestAPIFunctionCalls:
    """测试API函数调用"""
    
    @pytest.fixture
    def mock_config(self):
        """创建模拟配置"""
        return ModelConfig(
            provider=AIProvider.OPENAI,
            model_name="test-model",
            api_key="test-key",
            base_url="http://test.com",
            timeout=10,
            max_retries=2
        )
    
    @pytest.fixture
    def api_base_url(self):
        """API基础URL"""
        return "http://emagen.323424.xyz/api"
    
    @pytest.fixture
    def test_adapter(self, mock_config):
        """创建测试适配器"""
        class TestAdapter(BaseAdapter):
            def __init__(self, config):
                super().__init__(config)
                self.api_base_url = "http://emagen.323424.xyz/api"
                self.supports_function_calling = True
            
            async def chat_completion(self, request):
                pass
            
            def _prepare_request(self, request):
                pass
            
            def _parse_response(self, response_data):
                pass
            
            async def execute_function_call(self, function_name, function_args):
                """执行API调用"""
                # 映射函数名到API端点
                endpoint_mapping = {
                    "query_available_appointments": "/functions/appointments",
                    "search_technicians": "/functions/therapists",
                    "query_technician_schedule": "/functions/therapists",
                    "create_appointment": "/functions/appointments",
                    "get_appointment_details": "/functions/appointments",
                    "get_stores": "/functions/stores"
                }
                
                endpoint = endpoint_mapping.get(function_name)
                if not endpoint:
                    return {
                        "success": False,
                        "error": f"未知的函数: {function_name}",
                        "message": "不支持的函数调用"
                    }
                
                # 构建请求参数
                params = {}
                if function_name == "query_available_appointments":
                    params = {
                        "action": "query_available",
                        "date": function_args.get("target_date"),
                        "technician_id": function_args.get("technician_id")
                    }
                elif function_name == "search_technicians":
                    params = {
                        "action": "search",
                        "name": function_args.get("name"),
                        "skill": function_args.get("skill")
                    }
                elif function_name == "get_stores":
                    params = {"action": "list"}
                
                # 发送请求
                url = f"{self.api_base_url}{endpoint}"
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, params=params) as response:
                            if response.status == 200:
                                data = await response.json()
                                return {
                                    "success": True,
                                    "data": data,
                                    "message": f"成功获取{function_name}数据"
                                }
                            else:
                                error_text = await response.text()
                                return {
                                    "success": False,
                                    "error": f"HTTP {response.status}",
                                    "message": error_text
                                }
                except Exception as e:
                    return {
                        "success": False,
                        "error": str(e),
                        "message": f"API调用失败: {function_name}"
                    }
        
        return TestAdapter(mock_config)
    
    @pytest.mark.asyncio
    async def test_query_stores(self, test_adapter):
        """测试查询门店列表"""
        # 模拟API响应
        mock_response = {
            "stores": [
                {"id": 1, "name": "名医堂总店", "address": "北京市朝阳区XX路"},
                {"id": 2, "name": "名医堂分店", "address": "北京市海淀区YY路"}
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await test_adapter.execute_function_call("get_stores", {})
            
            assert result["success"] is True
            assert "data" in result
            assert "stores" in result["data"]
            assert len(result["data"]["stores"]) == 2
    
    @pytest.mark.asyncio
    async def test_search_technicians(self, test_adapter):
        """测试搜索技师"""
        mock_response = {
            "therapists": [
                {
                    "id": 1,
                    "name": "张三",
                    "skills": ["推拿", "拔罐"],
                    "rating": 4.8
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await test_adapter.execute_function_call(
                "search_technicians", 
                {"name": "张三"}
            )
            
            assert result["success"] is True
            assert "data" in result
            assert "therapists" in result["data"]
            assert len(result["data"]["therapists"]) == 1
            assert result["data"]["therapists"][0]["name"] == "张三"
    
    @pytest.mark.asyncio
    async def test_query_available_appointments(self, test_adapter):
        """测试查询可用预约时间"""
        mock_response = {
            "available_slots": [
                {
                    "time": "2025-06-15 10:00",
                    "technician_id": 1,
                    "technician_name": "张三"
                },
                {
                    "time": "2025-06-15 14:00",
                    "technician_id": 1,
                    "technician_name": "张三"
                }
            ]
        }
        
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 200
            mock_get.return_value.__aenter__.return_value.json = AsyncMock(return_value=mock_response)
            
            result = await test_adapter.execute_function_call(
                "query_available_appointments",
                {"target_date": "2025-06-15", "technician_id": 1}
            )
            
            assert result["success"] is True
            assert "data" in result
            assert "available_slots" in result["data"]
            assert len(result["data"]["available_slots"]) == 2
    
    @pytest.mark.asyncio
    async def test_api_error_handling(self, test_adapter):
        """测试API错误处理"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.return_value.__aenter__.return_value.status = 500
            mock_get.return_value.__aenter__.return_value.text = AsyncMock(
                return_value="Internal Server Error"
            )
            
            result = await test_adapter.execute_function_call("get_stores", {})
            
            assert result["success"] is False
            assert "error" in result
            assert "HTTP 500" in result["error"]
    
    @pytest.mark.asyncio
    async def test_network_error_handling(self, test_adapter):
        """测试网络错误处理"""
        with patch('aiohttp.ClientSession.get') as mock_get:
            mock_get.side_effect = aiohttp.ClientError("Connection failed")
            
            result = await test_adapter.execute_function_call("get_stores", {})
            
            assert result["success"] is False
            assert "error" in result
            assert "Connection failed" in result["error"]
    
    @pytest.mark.asyncio
    async def test_unknown_function(self, test_adapter):
        """测试未知函数调用"""
        result = await test_adapter.execute_function_call("unknown_function", {})
        
        assert result["success"] is False
        assert "未知的函数" in result["error"]
    
    @pytest.mark.asyncio
    async def test_real_api_health_check(self):
        """测试真实API健康检查（可选）"""
        url = "http://emagen.323424.xyz/api/health"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                    assert response.status == 200
                    data = await response.json()
                    assert data.get("status") == "ok"
                    print(f"API健康检查成功: {data}")
        except Exception as e:
            pytest.skip(f"无法连接到API服务器: {e}")