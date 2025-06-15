"""
AI适配器基类
"""

import json
from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
import asyncio
import logging

from ..models import AIRequest, AIResponse, AIMessage, MessageRole
from ..config import ModelConfig


logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """AI适配器基类"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.logger = logger.getChild(self.__class__.__name__)
        self.supports_function_calling = False
    
    @abstractmethod
    async def chat_completion(self, request: AIRequest) -> AIResponse:
        """执行聊天补全请求"""
        pass
    
    @abstractmethod
    def _prepare_request(self, request: AIRequest) -> dict:
        """准备API请求数据"""
        pass
    
    @abstractmethod
    def _parse_response(self, response_data: dict) -> AIResponse:
        """解析API响应数据"""
        pass
    
    def get_database_tools(self) -> List[Dict[str, Any]]:
        """
        获取数据库查询工具定义（最新OpenAI Function Call格式）
        
        Returns:
            工具定义列表
        """
        return [
            {
                "type": "function",
                "function": {
                    "name": "query_available_appointments",
                    "description": "查询指定日期的可用预约时间段，可以指定技师或查询所有技师的可用时间",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "target_date": {
                                "type": "string",
                                "description": "查询日期，格式: YYYY-MM-DD (例如: 2024-01-15)"
                            },
                            "technician_id": {
                                "type": "integer",
                                "description": "技师ID，可选参数。如果指定则只查询该技师的可用时间"
                            }
                        },
                        "required": ["target_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "search_technicians",
                    "description": "搜索技师信息，可以按姓名或技能搜索",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "name": {
                                "type": "string",
                                "description": "技师姓名，支持模糊搜索"
                            },
                            "skill": {
                                "type": "string",
                                "description": "技师技能或专长"
                            }
                        },
                        "required": []
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "query_technician_schedule",
                    "description": "查询指定技师在某个时间段内的排班情况",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "technician_id": {
                                "type": "integer",
                                "description": "技师ID"
                            },
                            "start_date": {
                                "type": "string",
                                "description": "开始日期，格式: YYYY-MM-DD"
                            },
                            "end_date": {
                                "type": "string",
                                "description": "结束日期，格式: YYYY-MM-DD"
                            }
                        },
                        "required": ["technician_id", "start_date", "end_date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_appointment",
                    "description": "创建新的预约记录",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "customer_name": {
                                "type": "string",
                                "description": "客户姓名"
                            },
                            "customer_contact": {
                                "type": "string",
                                "description": "客户联系方式（手机号或微信）"
                            },
                            "technician_id": {
                                "type": "integer",
                                "description": "技师ID"
                            },
                            "scheduled_time": {
                                "type": "string",
                                "description": "预约时间，格式: YYYY-MM-DD HH:MM:SS"
                            },
                            "additional_info": {
                                "type": "string",
                                "description": "附加信息或备注"
                            }
                        },
                        "required": ["customer_name", "customer_contact", "technician_id", "scheduled_time"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_appointment_details",
                    "description": "获取预约详情信息",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "appointment_id": {
                                "type": "integer",
                                "description": "预约ID"
                            }
                        },
                        "required": ["appointment_id"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_stores",
                    "description": "获取所有门店列表信息，包括门店名称、地址、营业时间等",
                    "parameters": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            }
        ]
    
    async def _make_request(self, url: str, headers: dict, data: dict) -> dict:
        """发送HTTP请求"""
        import aiohttp
        
        timeout = aiohttp.ClientTimeout(total=self.config.timeout)
        
        for attempt in range(self.config.max_retries):
            try:
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    async with session.post(url, headers=headers, json=data) as response:
                        if response.status == 200:
                            return await response.json()
                        else:
                            error_text = await response.text()
                            self.logger.error(f"HTTP错误 {response.status}: {error_text}")
                            if attempt == self.config.max_retries - 1:
                                raise Exception(f"HTTP错误 {response.status}: {error_text}")
            except Exception as e:
                self.logger.warning(f"请求失败 (尝试 {attempt + 1}/{self.config.max_retries}): {e}")
                if attempt == self.config.max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # 指数退避
    
    def create_customer_service_prompt(self, customer_message: str) -> AIRequest:
        """创建客服回复的提示词"""
        system_prompt = """你是一个专业的客服代表，请根据客户的消息生成合适的回复。

客户消息：{customer_message}

重要要求：
1. 仔细阅读对话历史，了解客户之前的问题和需求，基于历史对话的上下文，给出连贯、相关的回复
2. 如果客户之前提到过具体需求（如预约、咨询等），要延续这个话题
3. 如果客户的消息很简短或不清楚，结合历史对话来理解其意图
4. 身份：你是名医堂的客服助理，名医堂秉承'传承中医文化，服务百姓健康'理念，专注提供'医养结合'的中医理疗服务。名医堂让优质中医走进社区，为顾客解决疼痛、亚健康及脏腑调理问题。
5. 语气：不要要专业、简短、温柔 不要用!感叹号
6.禁用词：联系方式
7.已知信息
【基础信息】
营业时间：9:30–21:30（全年无休，仅春节放假）
地址导航：优先大众点评搜索，或电话人工指引
停车服务：免费停车/收费（XX元/小时）/周边收费停车区推荐
医保支付：不支持医保
店内餐饮：仅提供养生茶和小食糖果（无正餐）

【预约规则】
预约需提供：姓名+手机号（格式：XXX-XXXX-XXXX）
指定技师：可约/需等待/推荐同级替补
双人间：有空房直接约，满员则改期
女技师：可预约，若无则推荐男技师
迟到处理：短时宽容/影响后续则改期
退款流程：平台直接退款或改约

【服务项目】
推荐套餐：小调理（颈肩腰腿痛专项）
团购建议：到店评估后购买
生理期服务：量少时可艾灸，需预约
技师资质：持推拿证，8年以上经验

【其他咨询】
招聘信息：停招/招聘中（留联系方式）
节假日：全年营业（仅春节放假）

请直接回复客户的问题，不要添加额外的解释或前缀。

"""
        
        messages = [
            AIMessage(role=MessageRole.SYSTEM, content=system_prompt.format(customer_message=customer_message)),
            AIMessage(role=MessageRole.USER, content=customer_message)
        ]
        
        return AIRequest(
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=self.config.temperature
        )
    
    def create_customer_service_prompt_with_history(self, customer_message: str, 
                                                   conversation_history: list = None) -> AIRequest:
        """创建带有对话历史的客服回复提示词"""
        
        # 如果没有历史记录，回退到普通方法
        if not conversation_history:
            return self.create_customer_service_prompt(customer_message)
        
        system_prompt = """你是名医堂的智能客服助理，具备查询实时数据库信息的能力。

你可以调用以下数据库查询功能来为客户提供准确的信息：
- query_available_appointments: 查询可用预约时间
- search_technicians: 搜索技师信息  
- query_technician_schedule: 查询技师排班
- create_appointment: 创建预约（需要客户提供姓名和联系方式）
- get_appointment_details: 查询预约详情

工作原则：
1. 当客户询问预约时间、技师信息、排班等问题时，主动调用相应的数据库查询功能获取最新信息
2. 基于查询结果为客户提供准确、具体的回答
3. 如果需要创建预约，确保收集到客户姓名、电话、期望时间等必要信息
4. 仔细阅读对话历史，了解客户之前的问题和需求，基于历史对话的上下文，给出连贯的回复
注意：请不要出现 联系方式 这个词，一律用电话代替
7.已知信息
【基础信息】
营业时间：9:30–21:30（全年无休，仅春节放假）
地址导航：优先大众点评搜索，或电话人工指引
停车服务：免费停车/收费（XX元/小时）/周边收费停车区推荐
医保支付：不支持医保
店内餐饮：仅提供养生茶和小食糖果（无正餐）

【预约规则】
预约需提供：姓名+手机号（格式：XXX-XXXX-XXXX）
指定技师：可约/需等待/推荐同级替补
双人间：有空房直接约，满员则改期
女技师：可预约，若无则推荐男技师
迟到处理：短时宽容/影响后续则改期
退款流程：平台直接退款或改约

【服务项目】
推荐套餐：小调理（颈肩腰腿痛专项）
团购建议：到店评估后购买
生理期服务：量少时可艾灸，需预约
技师资质：持推拿证，8年以上经验

【其他咨询】
招聘信息：停招/招聘中（留联系方式）
节假日：全年营业（仅春节放假）

请直接回复客户的问题，不要添加额外的解释或前缀。


身份和服务信息：
- 身份：你是名医堂的客服助理，名医堂秉承'传承中医文化，服务百姓健康'理念
- 专注提供'医养结合'的中医理疗服务，为顾客解决疼痛、亚健康及脏腑调理问题
- 营业时间：9:30–21:30（全年无休，仅春节放假）
- 不支持医保，预约需提供姓名+手机号
- 语气：专业、简短、温柔，不使用感叹号

请根据客户消息和对话历史，使用数据库查询功能提供准确回复。"""

        messages = [AIMessage(role=MessageRole.SYSTEM, content=system_prompt)]
        
        # 添加对话历史 - 使用更多历史记录以提供更好的上下文
        for memory_item in conversation_history[-15:]:  # 使用最近15条历史记录
            role = MessageRole.USER if memory_item.get("role") == "user" else MessageRole.ASSISTANT
            content = memory_item.get("content", "")
            if content.strip():
                messages.append(AIMessage(role=role, content=content))
        
        # 添加当前客户消息
        messages.append(AIMessage(role=MessageRole.USER, content=customer_message))
        
        # 如果适配器支持function calling，添加工具
        tools = None
        if self.supports_function_calling:
            tools = self.get_database_tools()
        
        return AIRequest(
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=0.7,  # 稍微提高创造性，让回复更自然
            tools=tools  # 添加数据库查询工具
        )
    
    async def process_tool_calls(self, tool_calls: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        处理工具调用
        
        Args:
            tool_calls: 工具调用列表
            
        Returns:
            工具调用结果列表
        """
        results = []
        
        for tool_call in tool_calls:
            try:
                function_name = tool_call["function"]["name"]
                function_args = json.loads(tool_call["function"]["arguments"])
                
                # 执行函数调用
                if hasattr(self, 'execute_function_call'):
                    result = await self.execute_function_call(function_name, function_args)
                else:
                    result = {
                        "success": False,
                        "error": "适配器不支持函数调用",
                        "message": "当前适配器未实现函数调用功能"
                    }
                
                results.append({
                    "tool_call_id": tool_call["id"],
                    "function_name": function_name,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"处理工具调用失败: {e}")
                results.append({
                    "tool_call_id": tool_call.get("id", "unknown"),
                    "function_name": tool_call.get("function", {}).get("name", "unknown"),
                    "result": {
                        "success": False,
                        "error": str(e),
                        "message": "工具调用处理失败"
                    }
                })
        
        return results 