"""
AI客户端模块 - 统一多模型AI调用接口
支持智谱AI、Deepseek、OpenAI等多种模型
"""

from .client import AIClient
from .models import AIModel, AIResponse
from .config import AIConfig, AIProvider

__version__ = "1.0.0"
__all__ = ["AIClient", "AIModel", "AIResponse", "AIConfig", "AIProvider"] 