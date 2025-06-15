# 邮件通知功能使用指南

## 概述

本文档介绍了为名医堂AI客服系统新增的邮件通知功能。该功能能够在客户成功预约后，自动发送确认邮件给客户，并通知相关技师。

## 功能特性

- 🎯 **自动邮件生成**: 根据客户电话号码自动生成163邮箱地址
- 📧 **双重通知**: 客户确认邮件 + 技师预约通知邮件
- 🎨 **模板化设计**: 美观的邮件模板，包含所有关键预约信息
- 🔗 **AI集成**: 通过Function Call与AI对话系统无缝集成
- ⚡ **异步处理**: 高效的异步邮件发送机制
- 🛡️ **错误处理**: 完善的错误处理和日志记录

## 架构设计

```
AI对话系统 → Function Call → 邮件通知服务
                  ↓
           预约数据查询 → 技师信息查询 → 邮件模板生成 → SMTP发送
```

### 核心模块

1. **ContactInfoExtractor** - 联系信息提取器
   - 电话号码转163邮箱地址
   - 邮箱地址有效性验证

2. **EmailTemplateManager** - 邮件模板管理器
   - 客户预约确认邮件模板
   - 技师新预约通知邮件模板

3. **EmailNotificationService** - 邮件通知服务
   - 完整的邮件发送流程
   - 错误处理和重试机制

4. **EmailSenderAdapter** - 邮件发送适配器
   - 兼容现有EmailSender类
   - 统一的发送接口

## 使用方法

### 1. Function Call方式（推荐）

在AI对话过程中，当客户成功预约后，AI会自动调用`send_appointment_emails`函数：

```python
# AI会自动生成这样的函数调用
{
    "name": "send_appointment_emails",
    "arguments": {
        "customer_name": "张三",
        "customer_phone": "19357509506", 
        "therapist_id": 1,
        "appointment_date": "2024-03-15",
        "appointment_time": "14:00",
        "service_type": "按摩推拿",
        "notes": "客户希望轻柔一些"
    }
}
```

### 2. 直接调用方式

```python
from aiclient.services.email_notification import EmailNotificationService
from aiclient.services.email_sender_adapter import EmailSenderAdapter
from aiclient.database_service import DatabaseAPIService

# 初始化服务
email_sender = EmailSenderAdapter()
database_service = DatabaseAPIService()
email_service = EmailNotificationService(
    email_sender=email_sender,
    database_service=database_service
)

# 发送邮件通知
appointment_info = {
    "customer_name": "张三",
    "customer_phone": "19357509506",
    "therapist_id": 1,
    "appointment_date": "2024-03-15",
    "appointment_time": "14:00",
    "service_type": "按摩推拿"
}

result = await email_service.send_appointment_notification_emails(appointment_info)
```

## 邮件模板示例

### 客户确认邮件

```
主题: 【预约确认】张三您的预约已确认

内容:
尊敬的张三，您好！

您的预约已成功确认，详情如下：

📋 预约信息：
• 服务项目：按摩推拿
• 预约日期：2024-03-15
• 预约时间：14:00
• 服务技师：李技师
• 服务门店：名医堂中心店

📞 温馨提示：
• 请提前10分钟到达门店
• 如需修改或取消预约，请及时联系我们
• 感谢您的信任与支持！

此邮件为系统自动发送，请勿直接回复。
如有疑问请联系客服。
```

### 技师通知邮件

```
主题: 【新预约通知】李技师，您有新的预约

内容:
亲爱的李技师，您好！

您有一个新的预约，请注意安排：

👤 客户信息：
• 客户姓名：张三
• 联系电话：19357509506

📋 预约详情：
• 服务项目：按摩推拿
• 预约日期：2024-03-15
• 预约时间：14:00
• 服务门店：名医堂中心店
• 备注信息：客户希望轻柔一些

📝 注意事项：
• 请提前准备相关服务用品
• 如有时间冲突请及时联系管理员
• 请确保按时到岗为客户提供优质服务
```

## 配置要求

1. **SMTP配置**: 确保`sender/config.toml`中的邮件配置正确
2. **数据库连接**: 确保数据库API服务正常运行
3. **依赖包**: 安装必要的Python依赖包

## 错误处理

系统包含完善的错误处理机制：

- **无效电话号码**: 自动检测并返回错误信息
- **技师信息缺失**: 查询技师失败时的处理
- **邮件发送失败**: SMTP错误的处理和日志记录
- **网络超时**: 自动重试机制

## 测试验证

运行测试套件确保功能正常：

```bash
# 运行所有邮件通知测试
python -m pytest tests/test_email_notification.py -v

# 运行演示脚本
python examples/email_notification_demo.py
```

## 日志和监控

系统提供详细的日志记录：

```python
import logging
logger = logging.getLogger('aiclient.services.email_notification')
logger.setLevel(logging.INFO)
```

日志包含：
- 邮件发送状态
- 错误详情
- 性能指标
- 调试信息

## 最佳实践

1. **邮箱规则**: 默认使用`{电话号码}@163.com`格式
2. **发送顺序**: 先发客户确认邮件，再发技师通知邮件
3. **错误恢复**: 部分邮件失败不影响整体预约流程
4. **日志记录**: 记录所有邮件发送活动便于追踪

## 扩展功能

未来可扩展的功能：

- [ ] 支持其他邮箱服务商
- [ ] 邮件模板自定义
- [ ] 批量邮件发送
- [ ] 邮件发送统计
- [ ] 邮件追踪和回执

## 技术支持

如遇问题，请查看：

1. 系统日志文件
2. 邮件服务器状态  
3. 数据库连接状态
4. 网络连接情况

联系开发团队获取技术支持。 