"""
统一AI客户端
"""

import json
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
        self._conversation_memory: List[Dict[str, Any]] = []  # 当前对话记忆
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
                                             preferred_provider: Optional[AIProvider] = None,
                                             conversation_history: Optional[List[Dict[str, Any]]] = None) -> AIResponse:
        """生成客服回复（支持Function Call）"""
        if not customer_message.strip():
            raise ValueError("客户消息不能为空")
        
        # 确定使用的AI提供商
        provider = self._select_provider(preferred_provider)
        adapter = self.adapters[provider]
        
        # 使用传入的对话历史或当前记忆
        history_to_use = conversation_history if conversation_history is not None else self._conversation_memory
        
        # 调试日志
        logger.info(f"[AI调试] 收到客户消息: {customer_message}")
        logger.info(f"[AI调试] 对话历史长度: {len(history_to_use)}")
        if history_to_use:
            logger.info(f"[AI调试] 历史记录预览:")
            for i, mem in enumerate(history_to_use[-3:], 1):
                role = mem.get("role", "unknown")
                content = mem.get("content", "")[:30]
                logger.info(f"  {i}. {role}: {content}...")
        
        # 创建带有对话历史的客服提示词
        request = adapter.create_customer_service_prompt_with_history(customer_message, history_to_use)
        
        logger.info(f"为客户消息生成回复，使用提供商: {provider.value}")
        logger.debug(f"客户消息: {customer_message}")
        logger.debug(f"使用对话历史: {len(history_to_use)}条记录")
        
        try:
            # 第一次AI调用
            response = await adapter.chat_completion(request)
            
            # 检查是否需要处理function call
            if response.tool_calls and len(response.tool_calls) > 0:
                logger.info(f"检测到 {len(response.tool_calls)} 个函数调用")
                
                # 处理函数调用
                tool_results = []
                for tool_call in response.tool_calls:
                    function_name = tool_call["function"]["name"]
                    function_args = json.loads(tool_call["function"]["arguments"])
                    
                    logger.info(f"执行函数: {function_name} 参数: {function_args}")
                    
                    if hasattr(adapter, 'execute_function_call'):
                        result = await adapter.execute_function_call(function_name, function_args)
                        tool_results.append({
                            "tool_call_id": tool_call["id"],
                            "role": "tool",
                            "name": function_name,
                            "content": json.dumps(result, ensure_ascii=False)
                        })
                    else:
                        logger.warning(f"适配器不支持函数调用: {function_name}")
                
                if tool_results:
                    # 构建包含函数调用结果的新请求
                    follow_up_messages = request.messages.copy()
                    
                    # 添加助手的函数调用消息
                    follow_up_messages.append(AIMessage(
                        role=MessageRole.ASSISTANT, 
                        content=response.content or ""
                    ))
                    
                    # 添加函数调用结果
                    for tool_result in tool_results:
                        follow_up_messages.append(AIMessage(
                            role=MessageRole.USER,  # 工具结果作为用户消息
                            content=f"函数 {tool_result['name']} 执行结果: {tool_result['content']}"
                        ))
                    
                    # 创建新的请求
                    follow_up_request = AIRequest(
                        messages=follow_up_messages,
                        max_tokens=request.max_tokens,
                        temperature=request.temperature
                    )
                    
                    # 再次调用AI，让它基于函数调用结果生成最终回复
                    logger.info("基于函数调用结果生成最终回复")
                    final_response = await adapter.chat_completion(follow_up_request)
                    
                    # 合并响应信息
                    final_response.tool_calls = response.tool_calls  # 保留原始工具调用信息
                    return final_response
            
            logger.info(f"AI回复生成成功: {response.content[:100]}...")
            return response
            
        except Exception as e:
            logger.error(f"AI回复生成失败 ({provider.value}): {e}")
            # 尝试备用提供商
            return await self._try_fallback_providers(request, provider)
    
    def _select_provider(self, preferred_provider: Optional[AIProvider] = None) -> AIProvider:
        """选择AI提供商（优先使用OpenAI）"""
        if preferred_provider and preferred_provider in self.adapters:
            return preferred_provider
        
        # 修改默认优先级: OpenAI > 智谱AI > Deepseek 
        priority_order = [AIProvider.OPENAI, AIProvider.ZHIPU, AIProvider.DEEPSEEK]
        
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
    
    def set_conversation_memory(self, memory: List[Dict[str, Any]]):
        """设置当前对话记忆"""
        self._conversation_memory = memory.copy() if memory else []
        logger.info(f"设置对话记忆: {len(self._conversation_memory)}条记录")
    
    def clear_conversation_memory(self):
        """清空当前对话记忆"""
        old_count = len(self._conversation_memory)
        self._conversation_memory = []
        logger.info(f"清空对话记忆: 已清除{old_count}条记录")
    
    def add_to_memory(self, role: str, content: str, message_id: Optional[str] = None):
        """添加消息到记忆中"""
        memory_item = {
            "role": role,  # "user" 或 "assistant"
            "content": content,
            "timestamp": __import__('time').time(),
            "messageId": message_id
        }
        self._conversation_memory.append(memory_item)
        
        # 限制记忆长度，保留最近的30条
        if len(self._conversation_memory) > 30:
            self._conversation_memory = self._conversation_memory[-30:]
        
        logger.debug(f"添加到记忆: {role} - {content[:50]}...")
    
    def get_memory_count(self) -> int:
        """获取当前记忆条数"""
        return len(self._conversation_memory)

    def get_status(self) -> Dict[str, Any]:
        """获取客户端状态"""
        return {
            "available_providers": [p.value for p in self.adapters.keys()],
            "total_providers": len(self.adapters),
            "config_loaded": len(self.config.models) > 0,
            "memory_count": len(self._conversation_memory),
            "default_provider": "openai",  # 标明默认使用OpenAI
            "function_call_enabled": any(
                getattr(adapter, 'supports_function_calling', False) 
                for adapter in self.adapters.values()
            )
        } 