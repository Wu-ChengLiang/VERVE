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