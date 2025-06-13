"""
AI配置管理模块
"""

import os
from typing import Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class AIProvider(Enum):
    """AI提供商枚举"""
    ZHIPU = "zhipu"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"


@dataclass
class ModelConfig:
    """单个模型配置"""
    provider: AIProvider
    model_name: str
    api_key: str
    base_url: Optional[str] = None
    max_tokens: int = 1000
    temperature: float = 0.7
    max_retries: int = 3
    timeout: int = 30


class AIConfig:
    """AI配置管理类"""
    
    def __init__(self):
        self.models: Dict[AIProvider, ModelConfig] = {}
        self._load_config()
    
    def _load_config(self):
        """从环境变量加载配置"""
        # 智谱AI配置
        zhipu_key = os.getenv("ZHIPU_API_KEY")
        if zhipu_key:
            self.models[AIProvider.ZHIPU] = ModelConfig(
                provider=AIProvider.ZHIPU,
                model_name=os.getenv("ZHIPU_MODEL", "GLM-4-Flash-250414"),
                api_key=zhipu_key,
                base_url="https://open.bigmodel.cn/api/paas/v4/",
                max_tokens=int(os.getenv("ZHIPU_MAX_TOKENS", "1000")),
                temperature=float(os.getenv("ZHIPU_TEMPERATURE", "0.7"))
            )
        
        # Deepseek配置
        deepseek_key = os.getenv("DEEPSEEK_API_KEY")
        if deepseek_key:
            self.models[AIProvider.DEEPSEEK] = ModelConfig(
                provider=AIProvider.DEEPSEEK,
                model_name=os.getenv("DEEPSEEK_MODEL", "deepseek-chat"),
                api_key=deepseek_key,
                base_url="https://api.deepseek.com/v1/",
                max_tokens=int(os.getenv("DEEPSEEK_MAX_TOKENS", "1000")),
                temperature=float(os.getenv("DEEPSEEK_TEMPERATURE", "0.7"))
            )
        
        # OpenAI配置
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            self.models[AIProvider.OPENAI] = ModelConfig(
                provider=AIProvider.OPENAI,
                model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                api_key=openai_key,
                base_url=os.getenv("OPENAI_BASE_URL", "https://api.openai-next.com/v1"),
                max_tokens=int(os.getenv("OPENAI_MAX_TOKENS", "1000")),
                temperature=float(os.getenv("OPENAI_TEMPERATURE", "0.7"))
            )
    
    def get_model_config(self, provider: AIProvider) -> Optional[ModelConfig]:
        """获取指定提供商的模型配置"""
        return self.models.get(provider)
    
    def get_available_providers(self) -> list[AIProvider]:
        """获取所有可用的AI提供商"""
        return list(self.models.keys())
    
    def is_provider_available(self, provider: AIProvider) -> bool:
        """检查指定提供商是否可用"""
        return provider in self.models 