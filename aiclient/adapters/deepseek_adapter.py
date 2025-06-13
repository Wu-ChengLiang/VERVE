"""
Deepseek AI适配器
"""

from .base import BaseAdapter
from ..models import AIRequest, AIResponse


class DeepSeekAdapter(BaseAdapter):
    """Deepseek AI适配器"""
    
    async def chat_completion(self, request: AIRequest) -> AIResponse:
        """执行Deepseek聊天补全请求"""
        url = f"{self.config.base_url.rstrip('/')}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }
        
        data = self._prepare_request(request)
        
        self.logger.info(f"发送Deepseek请求: {self.config.model_name}")
        response_data = await self._make_request(url, headers, data)
        
        return self._parse_response(response_data)
    
    def _prepare_request(self, request: AIRequest) -> dict:
        """准备Deepseek请求数据"""
        data = request.to_openai_format()  # Deepseek兼容OpenAI格式
        data["model"] = self.config.model_name
        return data
    
    def _parse_response(self, response_data: dict) -> AIResponse:
        """解析Deepseek响应数据"""
        try:
            choice = response_data["choices"][0]
            content = choice["message"]["content"]
            
            usage = response_data.get("usage", {})
            
            return AIResponse(
                content=content,
                model=response_data.get("model", self.config.model_name),
                provider="deepseek",
                usage=usage,
                finish_reason=choice.get("finish_reason")
            )
        except (KeyError, IndexError) as e:
            self.logger.error(f"解析Deepseek响应失败: {e}, 响应数据: {response_data}")
            raise Exception(f"解析Deepseek响应失败: {e}") 