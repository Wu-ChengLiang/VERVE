#!/usr/bin/env python3
"""
AI客户端与后端服务器集成测试
"""

import asyncio
import json
import websockets
import logging
from aiclient import AIClient

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_ai_client_standalone():
    """测试AI客户端独立功能"""
    print("🧪 测试AI客户端独立功能...")
    
    client = AIClient()
    status = client.get_status()
    print(f"✅ AI客户端状态: {status}")
    
    # 测试消息识别
    test_data = [
        {"content": "[客户] 您好，我需要女技师为我服务，预计18:30到店"}
    ]
    
    is_customer, message = client.is_customer_message(test_data)
    print(f"✅ 消息识别: {is_customer}, 内容: '{message}'")
    
    return client


async def test_websocket_connection():
    """测试WebSocket连接"""
    print("🌐 测试WebSocket连接...")
    
    try:
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket连接成功")
            
            # 发送测试数据
            test_data = [
                {"content": "[客户] 您好，我想了解一下你们的服务项目"}
            ]
            
            await websocket.send(json.dumps(test_data))
            print("✅ 测试数据发送成功")
            
            # 等待响应
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ 收到响应: {response_data}")
            
            # 等待可能的AI回复
            try:
                ai_reply = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                ai_data = json.loads(ai_reply)
                if ai_data.get("type") == "ai_reply":
                    print(f"🤖 收到AI回复: {ai_data['content'][:100]}...")
                else:
                    print(f"📨 收到其他消息: {ai_data}")
            except asyncio.TimeoutError:
                print("⏰ 等待AI回复超时")
            
    except Exception as e:
        print(f"❌ WebSocket测试失败: {e}")


async def run_full_test():
    """运行完整测试"""
    print("🚀 开始AI客户端集成测试...")
    print("=" * 50)
    
    # 测试1: AI客户端独立功能
    await test_ai_client_standalone()
    print()
    
    # 测试2: WebSocket连接（需要服务器运行）
    print("📝 注意: 请确保后端服务器正在运行 (python dianping-scraper/backend/server.py)")
    input("按回车键继续WebSocket测试...")
    
    await test_websocket_connection()
    
    print("=" * 50)
    print("🎉 集成测试完成!")


def create_demo_data():
    """创建演示数据"""
    demo_data = [
        {"content": "[客户] 您好，我需要女技师为我服务，预计18:30到店"},
        {"content": "[客户] 请问你们有什么特色服务吗？"},
        {"content": "[客户] 我想预约明天下午的时间"},
        {"content": "[商家] 好的，为您安排"},  # 这条不会触发AI回复
        {"content": "[客户] 价格是多少呢？"}
    ]
    
    print("📋 演示数据:")
    for i, item in enumerate(demo_data, 1):
        print(f"  {i}. {item['content']}")
    
    return demo_data


if __name__ == "__main__":
    print("🎯 AI客户端集成测试工具")
    print()
    
    # 显示演示数据
    demo_data = create_demo_data()
    print()
    
    # 运行测试
    try:
        asyncio.run(run_full_test())
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc() 