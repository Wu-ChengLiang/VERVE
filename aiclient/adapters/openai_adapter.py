"""
OpenAI API适配器 - 支持Function Call
"""

import json
import logging
from typing import Optional, List, Dict, Any

from .base import BaseAdapter
from ..models import AIRequest, AIResponse
from ..config import ModelConfig


logger = logging.getLogger(__name__)


class OpenAIAdapter(BaseAdapter):
    """OpenAI API适配器 - 支持Function Call"""
    
    def __init__(self, config: ModelConfig):
        super().__init__(config)
        self.supports_function_calling = True
    
    async def chat_completion(self, request: AIRequest) -> AIResponse:
        """执行OpenAI聊天补全请求"""
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = self._prepare_request(request)
        data["model"] = self.config.model_name
        
        self.logger.info(f"发送OpenAI请求: {self.config.model_name}")
        response_data = await self._make_request(url, headers, data)
        
        return self._parse_response(response_data)
    
    def _prepare_request(self, request: AIRequest) -> dict:
        """准备OpenAI API请求数据"""
        data = request.to_openai_format()
        
        # 添加function call工具支持
        if hasattr(request, 'tools') and request.tools:
            data["tools"] = request.tools
            data["tool_choice"] = "auto"  # 让模型自动决定是否调用工具
        
        return data
    
    def _parse_response(self, response_data: dict) -> AIResponse:
        """解析OpenAI API响应数据"""
        try:
            choice = response_data["choices"][0]
            message = choice["message"]
            
            content = message.get("content", "")
            tool_calls = message.get("tool_calls", [])
            
            usage = response_data.get("usage", {})
            
            return AIResponse(
                content=content,
                model=response_data.get("model", self.config.model_name),
                provider="openai",
                usage=usage,
                finish_reason=choice.get("finish_reason"),
                tool_calls=tool_calls  # 添加工具调用信息
            )
        except (KeyError, IndexError) as e:
            self.logger.error(f"解析OpenAI响应失败: {e}, 响应数据: {response_data}")
            raise Exception(f"解析OpenAI响应失败: {e}")
    
    async def execute_function_call(self, function_name: str, function_args: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行function call
        
        Args:
            function_name: 函数名
            function_args: 函数参数
            
        Returns:
            函数执行结果
        """
        from ..database_service import DatabaseAPIService
        
        # 初始化数据库服务
        db_service = DatabaseAPIService()
        
        try:
            if function_name == "query_available_appointments":
                target_date = function_args.get("target_date")
                technician_id = function_args.get("technician_id")
                results = await db_service.query_available_appointments(target_date, technician_id)
                return {
                    "success": True,
                    "data": results,
                    "message": f"查询到 {len(results)} 个可用时间段"
                }
            
            elif function_name == "search_technicians":
                name = function_args.get("name")
                skill = function_args.get("skill")
                results = await db_service.search_technicians(name=name, skill=skill)
                return {
                    "success": True,
                    "data": results,
                    "message": f"查询到 {len(results)} 个技师"
                }
            
            elif function_name == "query_technician_schedule":
                technician_id = function_args.get("technician_id")
                start_date = function_args.get("start_date")
                end_date = function_args.get("end_date")
                results = await db_service.query_technician_schedule(technician_id, start_date, end_date)
                return {
                    "success": True,
                    "data": results,
                    "message": f"查询到 {len(results)} 个排班记录"
                }
            
            elif function_name == "create_appointment":
                customer_name = function_args.get("customer_name")
                customer_contact = function_args.get("customer_contact")
                technician_id = function_args.get("technician_id")
                scheduled_time = function_args.get("scheduled_time")
                additional_info = function_args.get("additional_info")
                
                result = await db_service.create_appointment(
                    customer_name, customer_contact, technician_id, 
                    scheduled_time, additional_info
                )
                return result
            
            elif function_name == "get_appointment_details":
                appointment_id = function_args.get("appointment_id")
                result = await db_service.get_appointment_details(appointment_id)
                return {
                    "success": True,
                    "data": result
                }
            
            elif function_name == "get_stores":
                results = await db_service.get_stores()
                return {
                    "success": True,
                    "data": results,
                    "message": f"查询到 {len(results)} 个门店"
                }
            
            else:
                return {
                    "success": False,
                    "error": f"未知的函数: {function_name}",
                    "message": "不支持的函数调用"
                }
                
        except Exception as e:
            logger.error(f"执行函数调用失败 ({function_name}): {e}")
            return {
                "success": False,
                "error": str(e),
                "message": f"函数 {function_name} 执行失败"
            } 