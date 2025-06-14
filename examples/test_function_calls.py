"""
示例：测试AI客户端函数调用功能
"""

import asyncio
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from aiclient.client import AIClient
from aiclient.config import AIConfig


async def test_function_calls():
    """测试函数调用功能"""
    
    # 初始化AI客户端
    config = AIConfig()
    client = AIClient(config)
    
    # 设置对话历史（模拟客户询问）
    conversation_history = [
        {"role": "user", "content": "你们有哪些门店？"},
        {"role": "assistant", "content": "让我为您查询一下我们的门店信息。"},
    ]
    
    client.set_conversation_memory(conversation_history)
    
    # 测试各种查询
    test_messages = [
        "请帮我查询一下你们的门店列表",
        "有哪些技师？",
        "明天有什么可用的预约时间？",
        "张三技师明天有空吗？",
    ]
    
    for message in test_messages:
        print(f"\n{'='*60}")
        print(f"客户问题: {message}")
        print(f"{'='*60}")
        
        try:
            # 生成回复
            response = await client.generate_customer_service_reply(message)
            
            print(f"\nAI回复:")
            print(f"内容: {response.content}")
            print(f"模型: {response.model} ({response.provider})")
            
            # 如果有工具调用，显示详情
            if response.tool_calls:
                print(f"\n使用的函数调用:")
                for tool_call in response.tool_calls:
                    print(f"  - {tool_call.get('function', {}).get('name', 'unknown')}")
            
            # 添加到对话历史
            client.add_to_memory("user", message)
            client.add_to_memory("assistant", response.content)
            
        except Exception as e:
            print(f"错误: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print(f"测试完成！当前对话记忆包含 {client.get_memory_count()} 条消息")


async def test_direct_api_calls():
    """直接测试API调用"""
    from aiclient.database_service import DatabaseAPIService
    
    print("\n直接API调用测试:")
    print("="*60)
    
    db_service = DatabaseAPIService()
    
    # 测试获取门店
    print("\n1. 获取门店列表:")
    stores = await db_service.get_stores()
    print(f"   找到 {len(stores)} 个门店")
    if stores:
        print(f"   第一个门店: {stores[0].get('name', 'unknown')}")
    
    # 测试搜索技师
    print("\n2. 搜索技师:")
    technicians = await db_service.search_technicians()
    print(f"   找到 {len(technicians)} 个技师")
    
    # 测试查询预约
    print("\n3. 查询明天的可用预约:")
    from datetime import datetime, timedelta
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    appointments = await db_service.query_available_appointments(tomorrow)
    print(f"   {tomorrow} 有 {len(appointments)} 个可用时间段")


if __name__ == "__main__":
    print("AI客户端函数调用测试")
    print("="*60)
    
    # 运行测试
    loop = asyncio.get_event_loop()
    
    # 先测试直接API调用
    loop.run_until_complete(test_direct_api_calls())
    
    # 再测试通过AI客户端的函数调用
    print("\n\nAI客户端函数调用测试:")
    print("="*60)
    loop.run_until_complete(test_function_calls())