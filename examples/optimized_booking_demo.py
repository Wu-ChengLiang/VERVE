"""
优化后的预约流程演示
展示：
1. 简化的预约流程（一次确认即可）
2. 增强的对话记忆（30条）
3. 简洁的AI回复
4. 完整的邮件通知功能
"""

import asyncio
import logging
import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from aiclient import AIClient
from aiclient.services.email_notification import EmailNotificationService
from aiclient.services.email_sender_adapter import EmailSenderAdapter

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def demo_optimized_booking_flow():
    """演示优化后的预约流程"""
    print("🎯 优化后的预约流程演示")
    print("=" * 50)
    
    # 初始化AI客户端
    ai_client = AIClient()
    print(f"✅ AI客户端初始化完成，支持 {len(ai_client.adapters)} 个提供商")
    
    # 模拟完整的预约对话流程
    conversation_scenarios = [
        {
            "title": "场景1：标准预约流程",
            "conversation": [
                {"role": "user", "content": "我想预约按摩"},
                {"role": "assistant", "content": "好的，请问您希望预约哪位技师？"},
                {"role": "user", "content": "杜技师"},
                {"role": "assistant", "content": "请问您希望什么时间预约？"},
                {"role": "user", "content": "今晚8点"},
                {"role": "assistant", "content": "方便给一个姓名和电话吗，预约会用短信的形式通知您"},
                {"role": "user", "content": "张三 13812345678"},
            ],
            "final_message": "确认预约"
        },
        {
            "title": "场景2：快速预约流程",
            "conversation": [
                {"role": "user", "content": "帮我预约吴老师明天下午2点"},
                {"role": "assistant", "content": "好的，方便给一个姓名和电话吗，预约会用短信的形式通知您"},
                {"role": "user", "content": "李四 19987654321"},
            ],
            "final_message": "确认"
        }
    ]
    
    for scenario in conversation_scenarios:
        print(f"\n📋 {scenario['title']}")
        print("-" * 30)
        
        # 显示对话历史
        print("💬 对话历史:")
        for i, msg in enumerate(scenario['conversation'], 1):
            role = "客户" if msg["role"] == "user" else "客服"
            print(f"  {i}. {role}: {msg['content']}")
        
        # 测试AI回复
        print(f"\n🤖 客户说: {scenario['final_message']}")
        print("🔄 AI处理中...")
        
        try:
            response = await ai_client.generate_customer_service_reply(
                customer_message=scenario['final_message'],
                conversation_history=scenario['conversation']
            )
            
            print(f"💬 AI回复: {response.content}")
            
            if response.tool_calls:
                print(f"🔧 执行了 {len(response.tool_calls)} 个函数:")
                for tool_call in response.tool_calls:
                    function_name = tool_call["function"]["name"]
                    print(f"  - {function_name}")
                    
                    # 特别标注预约和邮件功能
                    if function_name == "create_appointment":
                        print("    ✅ 创建预约")
                    elif function_name == "send_appointment_emails":
                        print("    📧 发送邮件通知")
            
        except Exception as e:
            print(f"❌ 处理失败: {e}")
    
    # 演示记忆管理优化
    print(f"\n🧠 记忆管理演示")
    print("-" * 30)
    
    print(f"当前记忆条数: {ai_client.get_memory_count()}")
    
    # 添加大量记忆测试限制
    print("📝 添加35条记忆测试...")
    for i in range(35):
        ai_client.add_to_memory("user", f"测试记忆 {i+1}")
    
    print(f"添加后记忆条数: {ai_client.get_memory_count()}")
    print(f"✅ 记忆正确限制在30条: {'是' if ai_client.get_memory_count() == 30 else '否'}")
    
    # 演示邮件通知功能
    print(f"\n📧 邮件通知功能演示")
    print("-" * 30)
    
    try:
        # 创建邮件服务
        email_sender = EmailSenderAdapter()
        
        # 模拟数据库服务
        class MockDatabaseService:
            async def search_therapists(self):
                return [
                    {
                        "id": 1,
                        "name": "杜技师",
                        "phone": "13812345678",
                        "store_name": "名医堂中心店"
                    }
                ]
        
        database_service = MockDatabaseService()
        email_service = EmailNotificationService(
            email_sender=email_sender,
            database_service=database_service
        )
        
        # 测试邮件发送
        appointment_info = {
            "customer_name": "张三",
            "customer_phone": "13812345678",
            "therapist_id": 1,
            "appointment_date": "2024-03-15",
            "appointment_time": "20:00",
            "service_type": "按摩推拿",
            "notes": "客户希望轻柔一些"
        }
        
        print("📤 发送预约邮件通知...")
        result = await email_service.send_appointment_notification_emails(appointment_info)
        
        print(f"📊 邮件发送结果:")
        print(f"  成功: {result['success']}")
        print(f"  统计: {result['summary']}")
        
    except Exception as e:
        print(f"❌ 邮件演示失败: {e}")
    
    # 总结优化效果
    print(f"\n🎉 优化效果总结")
    print("=" * 50)
    print("✅ 预约流程优化:")
    print("  - 收集信息 → 一次确认 → 立即创建预约+发送邮件")
    print("  - 避免重复确认，提升用户体验")
    print()
    print("✅ 对话记忆增强:")
    print("  - 从15条增加到30条历史记录")
    print("  - 更好的上下文理解能力")
    print()
    print("✅ 回复简洁性:")
    print("  - 系统提示词要求简洁明了")
    print("  - 避免冗长的解释")
    print()
    print("✅ 邮件通知完善:")
    print("  - 客户确认邮件自动发送")
    print("  - 技师通知邮件同步发送")
    print("  - 完整的错误处理和日志记录")

if __name__ == "__main__":
    asyncio.run(demo_optimized_booking_flow()) 