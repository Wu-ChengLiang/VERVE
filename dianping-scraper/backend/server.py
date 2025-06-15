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
from typing import Set, Dict, Any, List
import signal
import sys
import os

# 导入新的数据库管理器
from database import db_manager

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
    
    def __init__(self, host: str = "localhost", port: int = 8767):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.data_store: Dict[str, Any] = {}
        self.ai_client = AIClient()
        self.server = None
        self.is_stopping = False
        
        logger.info(f"[AI] AI客户端初始化成功，可用提供商: {len(self.ai_client.adapters)}")
        logger.info(f"[数据库] 数据库管理器已初始化")
    
    def _safe_get_value(self, value: Any, default: str) -> str:
        """安全获取值，只有None时才使用默认值，保留空字符串"""
        return value if value is not None else default
        
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
                response = {"type": "error", "message": "不支持的数据类型"}
            
            if response:
                response["timestamp"] = datetime.now().isoformat()
                await websocket.send(json.dumps(response, ensure_ascii=False))
                
        except json.JSONDecodeError as e:
            logger.error(f"[错误] JSON解析错误: {e}")
            await websocket.send(json.dumps({"type": "error", "message": "JSON格式错误"}, ensure_ascii=False))
        except Exception as e:
            logger.error(f"[错误] 消息处理错误: {e}", exc_info=True)
            await websocket.send(json.dumps({"type": "error", "message": "服务器内部错误"}, ensure_ascii=False))

    async def process_message_by_type(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """根据消息类型处理数据"""
        msg_type = data.get("type")
        
        if msg_type == "ping":
            return {"type": "pong", "message": "服务器正常运行"}
        elif msg_type == "dianping_data":
            return await self.handle_dianping_data(data, timestamp)
        elif msg_type == "chat_context_switch":
            return await self.handle_chat_context_switch(data, timestamp)
        elif msg_type == "memory_update":
            return await self.handle_memory_update(data, timestamp)
        else:
            logger.warning(f"⚠️ 未知消息类型: {msg_type}")
            return {"type": "error", "message": f"未知的消息类型: {msg_type}"}

    async def handle_data_list(self, data_list: list, timestamp: str) -> Dict[str, Any]:
        """处理数据列表 (通常是历史消息)，现在主要用于记录"""
        logger.info(f"[数据] 提取到 {len(data_list)} 条数据 (此路径不再触发AI)")
        data_id = f"dianping_list_{timestamp}"
        self.data_store[data_id] = {
            "content": data_list, "timestamp": timestamp, "type": "dianping_data_list"
        }
        return {"type": "data_received", "message": f"数据列表已接收 ({len(data_list)}条)", "data_id": data_id}

    async def handle_dianping_data(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """处理通用的大众点评数据对象"""
        content = data.get("payload", {})
        data_id = f"dianping_{timestamp}"
        self.data_store[data_id] = {"content": content, "timestamp": timestamp, "type": "dianping_data_object"}
        logger.info(f"[数据] 存储数据对象: {data_id}")
        return {"type": "data_received", "message": "大众点评数据已接收", "data_id": data_id}

    async def handle_chat_context_switch(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """处理聊天对象切换 - 简化版，仅记录日志"""
        payload = data.get("payload", {})
        new_chat_id = payload.get("newChatId")
        new_contact_name = payload.get("newContactName", "未知用户")
        logger.info(f"[上下文切换] 切换到: {new_contact_name} ({new_chat_id})")
        return {"type": "chat_context_switched", "message": f"聊天对象已切换: {new_contact_name}", "new_chat_id": new_chat_id}

    async def handle_memory_update(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """
        使用数据库处理记忆更新，识别新消息并触发AI。
        这是目前系统的核心AI触发器。
        """
        payload = data.get("payload", {})
        chat_id = self._safe_get_value(payload.get("chatId"), "default_chat")
        contact_name = self._safe_get_value(payload.get("contactName"), "未知用户")
        conversation_memory = payload.get("conversationMemory", [])

        if not conversation_memory:
            return { "type": "memory_ack", "message": "空记忆，无需更新" }

        logger.info(f"[记忆处理] 收到 {contact_name} ({chat_id}) 的 {len(conversation_memory)} 条记忆")

        new_messages = []
        for message in conversation_memory:
            message['chatId'] = message.get('chatId', chat_id)
            message['contactName'] = message.get('contactName', contact_name)
            
            message_id = db_manager._generate_message_id(message)
            
            if not db_manager.is_message_processed(message_id):
                new_messages.append(message)

        if not new_messages:
            logger.info(f"[记忆处理] {contact_name}: 无新消息")
            return { "type": "memory_ack", "message": "无新消息" }

        logger.info(f"[记忆处理] {contact_name}: 检测到 {len(new_messages)} 条新消息，将存入数据库")
        for msg in new_messages:
            db_manager.add_message(msg)
            logger.info(f"  -> [新消息] Role: {msg.get('role', 'N/A')}, Content: '{str(msg.get('content', ''))[:50]}...'")

        new_customer_messages = [m for m in new_messages if m.get("role") == "user"]

        if not new_customer_messages:
            logger.info(f"[AI触发] {contact_name}: 新消息中无客户消息，不触发AI")
            return { "type": "memory_updated", "new_messages_count": len(new_messages) }

        latest_customer_message = new_customer_messages[-1]
        message_content = latest_customer_message.get("content", "")
        
        logger.info(f"[AI触发] {contact_name}: 基于新消息 '{message_content[:50]}...' 触发AI")

        full_history = db_manager.get_chat_history(chat_id, limit=50)
        logger.info(f"[AI触发] 为AI加载了 {len(full_history)} 条来自数据库的历史记录")

        try:
            ai_response = await self.ai_client.generate_customer_service_reply(
                customer_message=message_content,
                conversation_history=full_history
            )

            if ai_response and ai_response.content:
                ai_response_text = ai_response.content
                logger.info(f"[AI回复] {contact_name}: {ai_response_text[:100]}...")
                ai_reply_message = {
                    "type": "ai_reply", "chatId": chat_id, "contactName": contact_name,
                    "reply": ai_response_text, "timestamp": datetime.now().isoformat()
                }
                await self._broadcast_ai_reply(ai_reply_message)
                
                db_message = {
                    "chatId": chat_id, "contactName": contact_name, "role": "assistant",
                    "content": ai_response_text, "timestamp": ai_reply_message["timestamp"]
                }
                db_manager.add_message(db_message)
                logger.info(f"[数据库] 已存储AI对 {contact_name} 的回复")
            else:
                logger.warning(f"[AI回复] {contact_name}: AI未返回有效回复")

        except Exception as e:
            logger.error(f"[AI触发] 调用AI时发生错误 for {contact_name}: {e}", exc_info=True)

        return { "type": "memory_updated_and_ai_triggered", "new_messages_count": len(new_messages) }

    async def handle_client(self, websocket):
        """主循环，处理单个客户端的所有通信"""
        await self.register_client(websocket)
        try:
            async for message in websocket:
                await self.handle_message(websocket, message)
        except websockets.exceptions.ConnectionClosed as e:
            logger.warning(f"[断开] 连接异常关闭: {e}")
        finally:
            await self.unregister_client(websocket)

    async def start_server(self):
        """启动WebSocket服务器"""
        self.server = await websockets.serve(self.handle_client, self.host, self.port)
        logger.info(f"🚀 服务器已启动，监听于 ws://{self.host}:{self.port}")
        await self.server.wait_closed()

    async def _broadcast_ai_reply(self, ai_response: Dict[str, Any]):
        """向所有客户端广播AI回复"""
        message_to_send = {
            "type": "sendAIReply",
            "text": ai_response.get("reply", "")
        }
        logger.info(f"[广播] AI回复指令已发送: {message_to_send['text'][:50]}...")
        
        disconnected_clients = []
        for client in self.clients:
            try:
                await client.send(json.dumps(message_to_send, ensure_ascii=False))
            except websockets.exceptions.ConnectionClosed:
                disconnected_clients.append(client)
        
        for client in disconnected_clients:
            await self.unregister_client(client)
            
    async def stop(self):
        """优雅地停止服务器"""
        if self.is_stopping:
            return
        self.is_stopping = True
        logger.info("服务器正在停止...")
        if self.server:
            self.server.close()
            await self.server.wait_closed()
        db_manager.close()
        logger.info("服务器已成功关闭")

async def main():
    server = DianpingWebSocketServer()
    
    loop = asyncio.get_running_loop()
    
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}, 正在优雅地关闭...")
        asyncio.create_task(server.stop())

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        await server.start_server()
    except Exception as e:
        logger.critical(f"服务器主程序出现致命错误: {e}", exc_info=True)
    finally:
        if not server.is_stopping:
             await server.stop()
        logger.info("服务器主程序退出")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("程序被用户中断")

    except Exception as e:
        logger.error(f"❌ 程序异常退出: {e}")
        sys.exit(1) 