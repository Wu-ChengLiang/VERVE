"""
AI客户端服务模块
包含各种业务服务实现
"""

from .email_notification import (
    EmailNotificationService,
    EmailTemplateManager, 
    ContactInfoExtractor
)
from .email_sender_adapter import EmailSenderAdapter

__all__ = [
    'EmailNotificationService',
    'EmailTemplateManager',
    'ContactInfoExtractor',
    'EmailSenderAdapter'
] 