#!/usr/bin/env python3
"""
大众点评网页元素读取器 - WebSocket服务器
精简版 - 负责接收和处理来自浏览器扩展的核心数据
集成AI客户端，自动回复客户消息
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any
import signal
import sys
import os

# 添加AI客户端路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))
from aiclient import AIClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('dianping_scraper.log', encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# 设置控制台编码为UTF-8 (Windows)
if sys.platform.startswith('win'):
    import locale
    try:
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except locale.Error:
        pass
logger = logging.getLogger(__name__)

class DianpingWebSocketServer:
    """大众点评WebSocket服务器 - 精简版"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.data_store: Dict[str, Any] = {}
        self.ai_client = AIClient()
        logger.info(f"[AI] AI客户端初始化成功，可用提供商: {len(self.ai_client.adapters)}")
        
    async def register_client(self, websocket):
        """注册新客户端连接"""
        self.clients.add(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"[连接] 客户端: {client_info}")
        logger.info(f"[状态] 当前连接数: {len(self.clients)}")
        
        welcome_msg = {
            "type": "welcome",
            "message": "连接成功! 大众点评数据提取服务已就绪",
            "timestamp": datetime.now().isoformat()
        }
        await websocket.send(json.dumps(welcome_msg, ensure_ascii=False))

    async def unregister_client(self, websocket):
        """注销客户端连接"""
        self.clients.discard(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"[断开] 客户端: {client_info}")
        logger.info(f"[状态] 当前连接数: {len(self.clients)}")

    async def handle_message(self, websocket, message: str):
        """处理来自客户端的消息"""
        try:
            data = json.loads(message)
            timestamp = datetime.now().isoformat()
            
            response = None
            if isinstance(data, list):
                logger.info(f"[消息] 收到数据数组 (共 {len(data)} 条)")
                response = await self.handle_data_list(data, timestamp)
            elif isinstance(data, dict):
                msg_type = data.get("type", "unknown")
                logger.info(f"[消息] 类型: {msg_type}")
                response = await self.process_message_by_type(data, timestamp)
            else:
                logger.warning(f"⚠️ 未知数据类型: {type(data)}")
                response = {
                    "type": "error",
                    "message": "不支持的数据类型",
                    "timestamp": timestamp
                }
            
            if response:
                await websocket.send(json.dumps(response, ensure_ascii=False))
                
        except json.JSONDecodeError as e:
            logger.error(f"[错误] JSON解析错误: {e}")
            await websocket.send(json.dumps({
                "type": "error", "message": "JSON格式错误", "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False))
        except Exception as e:
            logger.error(f"[错误] 消息处理错误: {e}")
            await websocket.send(json.dumps({
                "type": "error", "message": "服务器内部错误", "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False))

    async def process_message_by_type(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """根据消息类型处理数据"""
        msg_type = data.get("type")
        
        if msg_type == "ping":
            return {
                "type": "pong",
                "timestamp": timestamp,
                "message": "服务器正常运行"
            }
            
        elif msg_type == "dianping_data":
            return await self.handle_dianping_data(data, timestamp)
            
        else:
            logger.warning(f"⚠️ 未知消息类型: {msg_type}")
            return {
                "type": "error",
                "message": f"未知的消息类型: {msg_type}",
                "timestamp": timestamp
            }

    async def handle_data_list(self, data_list: list, timestamp: str) -> Dict[str, Any]:
        """处理数据列表"""
        logger.info(f"[数据] 提取到 {len(data_list)} 条数据:")
        for item in data_list:
            content = item.get('content', '无内容')
            if isinstance(content, dict):
                content = content.get('name', str(content)[:50])
            logger.info(f"  - {str(content)[:100]}")
        
        # 检查是否需要AI回复
        try:
            ai_response = await self.ai_client.process_scraped_data(data_list)
            if ai_response:
                logger.info(f"[AI回复] 生成回复: {ai_response.content[:100]}...")
                # 发送AI回复到所有连接的客户端
                await self._broadcast_ai_reply(ai_response)
        except Exception as e:
            logger.error(f"[AI错误] AI处理失败: {e}")
        
        data_id = f"dianping_list_{timestamp}"
        self.data_store[data_id] = {
            "content": data_list,
            "timestamp": timestamp,
            "type": "dianping_data_list"
        }
        
        return {
            "type": "data_received",
            "message": f"数据列表已接收 ({len(data_list)}条)",
            "data_id": data_id,
            "timestamp": timestamp
        }

    async def handle_dianping_data(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """处理大众点评数据"""
        content = data.get("payload", {})
        
        data_id = f"dianping_{timestamp}"
        self.data_store[data_id] = {
            "content": content,
            "timestamp": timestamp,
            "type": "dianping_data_object"
        }
        
        logger.info(f"[数据] 存储数据对象: {data_id}")
        
        if content.get("pageType") == "chat_page":
            data_items = content.get("data", [])
            if data_items:
                logger.info(f"[聊天] 提取到 {len(data_items)} 条数据")
        
        return {
            "type": "data_received",
            "message": "大众点评数据已接收",
            "data_id": data_id,
            "timestamp": timestamp
        }

    async def handle_client(self, websocket):
        """处理客户端连接 - 移除废弃的 path 参数"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed:
            pass
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """启动WebSocket服务器"""
        logger.info(f"[启动] 大众点评WebSocket服务器")
        logger.info(f"[服务器] 监听地址: {self.host}:{self.port}")
        
        start_server = websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info(f"[成功] 服务器启动成功! 等待连接...")
        
        return start_server
    
    async def _broadcast_ai_reply(self, ai_response):
        """广播AI回复到所有客户端"""
        if not self.clients:
            logger.warning("[广播] 没有连接的客户端，无法发送AI回复")
            return
        
        # 发送AI回复指令，让前端自动发送
        message = {
            "type": "sendAIReply",
            "text": ai_response.content
        }
        
        # 发送到所有连接的客户端
        disconnected = []
        for client in self.clients:
            try:
                await client.send(json.dumps(message, ensure_ascii=False))
                logger.info(f"[广播] AI回复指令已发送: {ai_response.content[:50]}...")
            except websockets.exceptions.ConnectionClosed:
                disconnected.append(client)
            except Exception as e:
                logger.error(f"[广播错误] 发送AI回复失败: {e}")
                disconnected.append(client)
        
        # 清理断开的连接
        for client in disconnected:
            self.clients.discard(client)

async def main():
    """主函数"""
    server = DianpingWebSocketServer()
    
    def signal_handler(signum, frame):
        logger.info("🛑 收到停止信号，正在关闭服务器...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        start_server = await server.start_server()
        await start_server
        await asyncio.Future()  # 保持运行
        
    except Exception as e:
        logger.error(f"❌ 服务器启动失败: {e}")
        sys.exit(1)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 服务器已停止")
    except Exception as e:
        logger.error(f"❌ 程序异常退出: {e}")
        sys.exit(1) 