"""
AI适配器基类
"""

from abc import ABC, abstractmethod
from typing import Optional
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
        
要求：
1. 回复要礼貌、专业、有帮助
2. 语言要自然、友好
3. 尽量解决客户的问题或需求
4. 如果无法解决，要引导客户联系相关人员
5. 回复长度适中，不要太长也不要太短
6. 使用中文回复

客户消息：{customer_message}

请直接回复客户的问题，不要添加额外的解释。"""
        
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
        
        system_prompt = """你是一个专业的客服代表。请根据以下对话历史和客户的最新消息，生成合适的回复。

重要要求：
1. 仔细阅读对话历史，了解客户之前的问题和需求
2. 基于历史对话的上下文，给出连贯、相关的回复
3. 如果客户之前提到过具体需求（如预约、咨询等），要延续这个话题
4. 回复要礼貌、专业、有帮助
5. 语言要自然、友好
6. 如果客户的消息很简短或不清楚，结合历史对话来理解其意图
7. 回复长度适中，直接回答问题
8. 使用中文回复

请直接回复客户的问题，不要添加额外的解释或前缀。"""

        messages = [AIMessage(role=MessageRole.SYSTEM, content=system_prompt)]
        
        # 添加对话历史 - 使用更多历史记录以提供更好的上下文
        for memory_item in conversation_history[-15:]:  # 使用最近15条历史记录
            role = MessageRole.USER if memory_item.get("role") == "user" else MessageRole.ASSISTANT
            content = memory_item.get("content", "")
            if content.strip():
                messages.append(AIMessage(role=role, content=content))
        
        # 添加当前客户消息
        messages.append(AIMessage(role=MessageRole.USER, content=customer_message))
        
        return AIRequest(
            messages=messages,
            max_tokens=self.config.max_tokens,
            temperature=0.7  # 稍微提高创造性，让回复更自然
        ) 