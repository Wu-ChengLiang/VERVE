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
            # 新API函数调用
            if function_name == "create_appointment":
                username = function_args.get("username")
                customer_name = function_args.get("customer_name")
                customer_phone = function_args.get("customer_phone")
                therapist_id = function_args.get("therapist_id")
                appointment_date = function_args.get("appointment_date")
                appointment_time = function_args.get("appointment_time")
                service_type = function_args.get("service_type")
                notes = function_args.get("notes")
                
                result = await db_service.create_appointment(
                    username, customer_name, customer_phone, therapist_id,
                    appointment_date, appointment_time, service_type, notes
                )
                return result
            
            elif function_name == "get_user_appointments":
                username = function_args.get("username")
                results = await db_service.get_user_appointments(username)
                return {
                    "success": True,
                    "data": results,
                    "message": f"查询到 {len(results)} 个预约记录"
                }
            
            elif function_name == "cancel_appointment":
                appointment_id = function_args.get("appointment_id")
                username = function_args.get("username")
                result = await db_service.cancel_appointment(appointment_id, username)
                return result
            
            elif function_name == "query_therapist_availability":
                therapist_id = function_args.get("therapist_id")
                date = function_args.get("date")
                results = await db_service.query_therapist_availability(therapist_id, date)
                return {
                    "success": True,
                    "data": results,
                    "message": f"查询到 {len(results)} 个可用时间段"
                }
            
            elif function_name == "search_therapists":
                therapist_name = function_args.get("therapist_name")
                store_name = function_args.get("store_name")
                service_type = function_args.get("service_type")
                results = await db_service.search_therapists(
                    therapist_name=therapist_name, 
                    store_name=store_name, 
                    service_type=service_type
                )
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
            
            elif function_name == "get_appointment_details":
                appointment_id = function_args.get("appointment_id")
                result = await db_service.get_appointment_details(appointment_id)
                return {
                    "success": True,
                    "data": result,
                    "message": "预约详情查询成功"
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