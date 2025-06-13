"""
统一AI客户端
"""

import logging
from typing import Optional, List, Dict, Any
import asyncio

from .config import AIConfig, AIProvider
from .models import AIRequest, AIResponse, AIMessage, MessageRole
from .adapters import OpenAIAdapter, ZhipuAdapter, DeepSeekAdapter, BaseAdapter


logger = logging.getLogger(__name__)


class AIClient:
    """统一AI客户端"""
    
    def __init__(self):
        self.config = AIConfig()
        self.adapters: Dict[AIProvider, BaseAdapter] = {}
        self._init_adapters()
    
    def _init_adapters(self):
        """初始化适配器"""
        for provider in self.config.get_available_providers():
            model_config = self.config.get_model_config(provider)
            if not model_config:
                continue
                
            if provider == AIProvider.OPENAI:
                self.adapters[provider] = OpenAIAdapter(model_config)
            elif provider == AIProvider.ZHIPU:
                self.adapters[provider] = ZhipuAdapter(model_config)
            elif provider == AIProvider.DEEPSEEK:
                self.adapters[provider] = DeepSeekAdapter(model_config)
        
        logger.info(f"初始化了 {len(self.adapters)} 个AI适配器: {list(self.adapters.keys())}")
    
    async def generate_customer_service_reply(self, customer_message: str, 
                                             preferred_provider: Optional[AIProvider] = None) -> AIResponse:
        """生成客服回复"""
        if not customer_message.strip():
            raise ValueError("客户消息不能为空")
        
        # 确定使用的AI提供商
        provider = self._select_provider(preferred_provider)
        adapter = self.adapters[provider]
        
        # 创建客服提示词
        request = adapter.create_customer_service_prompt(customer_message)
        
        logger.info(f"为客户消息生成回复，使用提供商: {provider.value}")
        logger.debug(f"客户消息: {customer_message}")
        
        try:
            response = await adapter.chat_completion(request)
            logger.info(f"AI回复生成成功: {response.content[:100]}...")
            return response
        except Exception as e:
            logger.error(f"AI回复生成失败 ({provider.value}): {e}")
            # 尝试备用提供商
            return await self._try_fallback_providers(request, provider)
    
    def _select_provider(self, preferred_provider: Optional[AIProvider] = None) -> AIProvider:
        """选择AI提供商"""
        if preferred_provider and preferred_provider in self.adapters:
            return preferred_provider
        
        # 默认优先级: 智谱AI > OpenAI > Deepseek 
        priority_order = [AIProvider.ZHIPU, AIProvider.OPENAI, AIProvider.DEEPSEEK]
        
        for provider in priority_order:
            if provider in self.adapters:
                return provider
        
        raise Exception("没有可用的AI提供商")
    
    async def _try_fallback_providers(self, request: AIRequest, failed_provider: AIProvider) -> AIResponse:
        """尝试备用提供商"""
        available_providers = [p for p in self.adapters.keys() if p != failed_provider]
        
        for provider in available_providers:
            try:
                logger.info(f"尝试备用提供商: {provider.value}")
                adapter = self.adapters[provider]
                response = await adapter.chat_completion(request)
                logger.info(f"备用提供商成功: {provider.value}")
                return response
            except Exception as e:
                logger.warning(f"备用提供商失败 ({provider.value}): {e}")
                continue
        
        raise Exception("所有AI提供商都失败了")
    
    def is_customer_message(self, data_list: List[Dict[str, Any]]) -> tuple[bool, Optional[str]]:
        """判断数据列表中最后一条消息是否是客户消息
        
        Returns:
            tuple: (是否是客户消息, 客户消息内容)
        """
        if not data_list:
            return False, None
        
        # 获取最后一条消息
        last_item = data_list[-1]
        content = last_item.get('content', '')
        
        if isinstance(content, dict):
            content = str(content)
        
        content = str(content).strip()
        
        # 检查是否以[客户]开头
        if content.startswith('[客户]'):
            # 提取客户消息内容
            customer_message = content[4:].strip()  # 去掉[客户]前缀
            logger.info(f"检测到客户消息: {customer_message[:50]}...")
            return True, customer_message
        
        logger.debug(f"非客户消息: {content[:50]}...")
        return False, None
    
    async def process_scraped_data(self, data_list: List[Dict[str, Any]]) -> Optional[AIResponse]:
        """处理从网页抓取的数据
        
        Args:
            data_list: 抓取到的数据列表
            
        Returns:
            AI生成的回复，如果不需要回复则返回None
        """
        is_customer, customer_message = self.is_customer_message(data_list)
        
        if not is_customer or not customer_message:
            return None
        
        try:
            return await self.generate_customer_service_reply(customer_message)
        except Exception as e:
            logger.error(f"处理数据失败: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            "available_providers": [p.value for p in self.adapters.keys()],
            "total_providers": len(self.adapters),
            "config_loaded": len(self.config.models) > 0
        } 