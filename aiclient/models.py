"""
AI模型数据结构定义
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MessageRole(Enum):
    """消息角色枚举"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class AIMessage:
    """AI消息结构"""
    role: MessageRole
    content: str
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "role": self.role.value,
            "content": self.content
        }


@dataclass
class AIRequest:
    """AI请求结构"""
    messages: List[AIMessage]
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    stream: bool = False
    tools: Optional[List[Dict[str, Any]]] = None
    
    def to_openai_format(self) -> Dict[str, Any]:
        """转换为OpenAI API格式"""
        data = {
            "messages": [msg.to_dict() for msg in self.messages]
        }
        if self.max_tokens:
            data["max_tokens"] = self.max_tokens
        if self.temperature is not None:
            data["temperature"] = self.temperature
        if self.stream:
            data["stream"] = self.stream
        if self.tools:
            data["tools"] = self.tools
            data["tool_choice"] = "auto"
        return data


@dataclass
class AIResponse:
    """AI响应结构"""
    content: str
    model: str
    provider: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class AIModel:
    """AI模型信息"""
    provider: str
    name: str
    description: str = ""
    max_context_length: int = 4096
    supports_streaming: bool = True 