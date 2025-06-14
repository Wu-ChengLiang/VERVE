#!/usr/bin/env python3
"""
WebSocket测试客户端
用于测试大众点评WebSocket服务器的连接和消息处理功能
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TestClient:
    """WebSocket测试客户端"""
    
    def __init__(self, uri: str = "ws://localhost:8765"):
        self.uri = uri
        self.websocket = None
        
    async def connect(self):
        """连接到WebSocket服务器"""
        try:
            logger.info(f"🔌 连接到服务器: {self.uri}")
            self.websocket = await websockets.connect(self.uri)
            logger.info("✅ 连接成功!")
            return True
        except Exception as e:
            logger.error(f"❌ 连接失败: {e}")
            return False
    
    async def send_message(self, message: dict):
        """发送消息到服务器"""
        if not self.websocket:
            logger.error("❌ 未连接到服务器")
            return
            
        try:
            message_str = json.dumps(message, ensure_ascii=False)
            await self.websocket.send(message_str)
            logger.info(f"📤 发送消息: {message.get('type', 'unknown')}")
            
            # 等待响应
            response = await self.websocket.recv()
            response_data = json.loads(response)
            logger.info(f"📨 收到响应: {response_data.get('type', 'unknown')}")
            logger.info(f"   消息: {response_data.get('message', 'N/A')}")
            
            return response_data
            
        except Exception as e:
            logger.error(f"❌ 发送消息失败: {e}")
            return None
    
    async def test_ping(self):
        """测试ping/pong"""
        logger.info("🏓 测试 ping/pong...")
        ping_msg = {
            "type": "ping",
            "timestamp": datetime.now().isoformat()
        }
        return await self.send_message(ping_msg)
    
    async def test_dianping_data(self):
        """测试大众点评数据发送"""
        logger.info("🏪 测试大众点评数据发送...")
        dianping_data = {
            "type": "dianping_data",
            "url": "https://g.dianping.com/dzim-main-pc/index.html#/",
            "content": {
                "restaurants": [
                    {
                        "name": "测试餐厅1",
                        "rating": 4.5,
                        "address": "测试地址1",
                        "price": "人均100元"
                    },
                    {
                        "name": "测试餐厅2", 
                        "rating": 4.2,
                        "address": "测试地址2",
                        "price": "人均80元"
                    }
                ]
            },
            "timestamp": datetime.now().isoformat()
        }
        return await self.send_message(dianping_data)
    
    async def test_page_info(self):
        """测试页面信息发送"""
        logger.info("📄 测试页面信息发送...")
        page_info = {
            "type": "page_info",
            "page_info": {
                "title": "大众点评 - 测试页面",
                "url": "https://g.dianping.com/dzim-main-pc/index.html#/",
                "element_count": 25,
                "page_type": "restaurant_list"
            },
            "timestamp": datetime.now().isoformat()
        }
        return await self.send_message(page_info)
    
    async def run_tests(self):
        """运行所有测试"""
        logger.info("🧪 开始WebSocket服务器测试...")
        
        # 连接服务器
        if not await self.connect():
            return False
        
        try:
            # 等待欢迎消息
            welcome_msg = await self.websocket.recv()
            welcome_data = json.loads(welcome_msg)
            logger.info(f"👋 收到欢迎消息: {welcome_data.get('message', 'N/A')}")
            
            # 运行测试
            await self.test_ping()
            await asyncio.sleep(1)
            
            await self.test_page_info()
            await asyncio.sleep(1)
            
            await self.test_dianping_data()
            await asyncio.sleep(1)
            
            logger.info("✅ 所有测试完成!")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试过程中发生错误: {e}")
            return False
        finally:
            if self.websocket:
                await self.websocket.close()
                logger.info("🔌 连接已关闭")

async def main():
    """主函数"""
    client = TestClient()
    success = await client.run_tests()
    
    if success:
        logger.info("🎉 WebSocket服务器测试成功!")
    else:
        logger.error("❌ WebSocket服务器测试失败!")
        return 1
    
    return 0

if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        exit(exit_code)
    except KeyboardInterrupt:
        logger.info("👋 测试被用户中断")
    except Exception as e:
        logger.error(f"❌ 测试程序异常: {e}")
        exit(1) 