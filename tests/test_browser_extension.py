#!/usr/bin/env python3
"""
模拟浏览器扩展发送客户消息测试
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def send_customer_message(message_content: str):
    """模拟浏览器扩展发送客户消息"""
    uri = "ws://localhost:8767"
    
    try:
        async with websockets.connect(uri) as websocket:
            print(f"✅ 已连接到WebSocket服务器: {uri}")
            
            # 接收欢迎消息
            welcome = await websocket.recv()
            welcome_data = json.loads(welcome)
            print(f"📨 收到欢迎消息: {welcome_data['message']}")
            
            # 构造客户消息数据（模拟从大众点评页面抓取的数据）
            test_data = [
                {"content": f"[客户] {message_content}"}
            ]
            
            print(f"📤 发送客户消息: {message_content}")
            await websocket.send(json.dumps(test_data))
            
            # 等待服务器确认
            response = await websocket.recv()
            response_data = json.loads(response)
            print(f"✅ 服务器确认: {response_data.get('message', '未知响应')}")
            
            # 等待AI回复
            print("🤖 等待AI生成回复...")
            try:
                # 可能需要接收多个消息，直到收到AI回复
                for attempt in range(3):  # 最多尝试3次
                    ai_reply = await asyncio.wait_for(websocket.recv(), timeout=10.0)
                    ai_data = json.loads(ai_reply)
                    
                    if ai_data.get("type") == "ai_reply":
                        print("🎉 收到AI回复:")
                        print(f"   提供商: {ai_data.get('provider', '未知')}")
                        print(f"   模型: {ai_data.get('model', '未知')}")
                        print(f"   内容: {ai_data.get('content', '无内容')}")
                        print(f"   时间: {ai_data.get('timestamp', '未知')}")
                        return ai_data
                    else:
                        print(f"📨 收到其他消息: {ai_data.get('type', 'unknown')}")
                        # 继续等待下一个消息
                        
                print("⚠️ 没有收到AI回复消息")
                return None
                    
            except asyncio.TimeoutError:
                print("⏰ 等待AI回复超时（10秒）")
                return None
            
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        print("💡 请确保后端服务器正在运行: python dianping-scraper/backend/server.py")
        return None


async def test_multiple_scenarios():
    """测试多个场景"""
    test_cases = [
        "您好，我需要女技师为我服务，预计18:30到店",
        "请问你们有什么特色服务吗？",
        "我想预约明天下午的时间",
        "价格是多少呢？",
        "有优惠活动吗？"
    ]
    
    print("🚀 开始浏览器扩展消息测试...")
    print("=" * 60)
    
    for i, message in enumerate(test_cases, 1):
        print(f"\n【测试案例 {i}/5】")
        await send_customer_message(message)
        
        if i < len(test_cases):
            print("\n⏱️ 等待3秒后进行下一个测试...")
            await asyncio.sleep(3)
    
    print("\n" + "=" * 60)
    print("🎉 所有测试案例完成！")


async def test_non_customer_message():
    """测试非客户消息（应该不触发AI回复）"""
    print("\n🧪 测试非客户消息（不应触发AI回复）...")
    
    uri = "ws://localhost:8767"
    try:
        async with websockets.connect(uri) as websocket:
            # 接收欢迎消息
            await websocket.recv()
            
            # 发送商家消息
            test_data = [
                {"content": "[商家] 好的，为您安排"}
            ]
            
            print("📤 发送商家消息: [商家] 好的，为您安排")
            await websocket.send(json.dumps(test_data))
            
            # 等待确认
            response = await websocket.recv()
            print("✅ 服务器确认收到")
            
            # 等待可能的AI回复（应该没有）
            try:
                ai_reply = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                print("⚠️ 意外收到AI回复（这不应该发生）")
            except asyncio.TimeoutError:
                print("✅ 正确：没有触发AI回复")
                
    except Exception as e:
        print(f"❌ 测试失败: {e}")


async def main():
    """主函数"""
    print("🎯 浏览器扩展客户消息测试工具")
    print("🔧 使用新的模型优先级: 智谱AI → OpenAI → Deepseek")
    print()
    
    # 先测试单个消息
    print("📱 单个消息测试...")
    await send_customer_message("您好，我想了解一下你们的服务")
    
    print("\n" + "="*40)
    
    # 测试非客户消息
    await test_non_customer_message()
    
    print("\n" + "="*40)
    print("\n是否继续测试多个场景？(y/n): ", end="")
    
    # 简化版本，直接测试多个场景
    print("y")
    await test_multiple_scenarios()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 测试被用户中断")
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc() 