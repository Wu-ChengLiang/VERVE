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
    
    def __init__(self, host: str = "localhost", port: int = 8767):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.data_store: Dict[str, Any] = {}
        self.ai_client = AIClient()
        
        # 记忆管理相关属性
        self.memory_store: Dict[str, List[Dict[str, Any]]] = {}  # {chatId: [memory_items]}
        self.current_chat_contexts: Dict[str, str] = {}  # {client_id: current_chatId}
        
        logger.info(f"[AI] AI客户端初始化成功，可用提供商: {len(self.ai_client.adapters)}")
        logger.info(f"[记忆] 记忆管理系统初始化完成")
        
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
            
        elif msg_type == "chat_context_switch":
            return await self.handle_chat_context_switch(data, timestamp)
            
        elif msg_type == "memory_update":
            return await self.handle_memory_update(data, timestamp)
            
        elif msg_type == "memory_save":
            return await self.handle_memory_save(data, timestamp)
            
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
        
        # 注释掉AI处理，避免与memory_update重复处理
        # 现在AI回复完全由memory_update系统处理
        # try:
        #     await self._process_data_with_memory(data_list)
        # except Exception as e:
        #     logger.error(f"[AI错误] AI处理失败: {e}")
        
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

    async def handle_chat_context_switch(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """处理聊天对象切换"""
        payload = data.get("payload", {})
        action = payload.get("action")
        old_chat_id = payload.get("oldChatId")
        new_chat_id = payload.get("newChatId")
        old_contact_name = payload.get("oldContactName")
        new_contact_name = payload.get("newContactName")
        conversation_memory = payload.get("conversationMemory", [])
        
        logger.info(f"[记忆] 聊天对象切换: {old_contact_name} -> {new_contact_name}")
        
        # 保存旧的记忆
        if old_chat_id and conversation_memory:
            self.memory_store[old_chat_id] = conversation_memory.copy()
            logger.info(f"[记忆] 保存 {old_contact_name} 的记忆 ({len(conversation_memory)}条)")
        
        # 清空当前上下文并加载新的记忆
        if new_chat_id:
            existing_memory = self.memory_store.get(new_chat_id, [])
            logger.info(f"[记忆] 加载 {new_contact_name} 的记忆 ({len(existing_memory)}条)")
            
            # 更新AI客户端的记忆上下文
            if hasattr(self.ai_client, 'set_conversation_memory'):
                self.ai_client.set_conversation_memory(existing_memory)
        
        return {
            "type": "chat_context_switched",
            "message": f"聊天对象已切换: {old_contact_name} -> {new_contact_name}",
            "old_chat_id": old_chat_id,
            "new_chat_id": new_chat_id,
            "loaded_memory_count": len(existing_memory) if new_chat_id else 0,
            "timestamp": timestamp
        }

    async def handle_memory_update(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """处理记忆更新"""
        payload = data.get("payload", {})
        action = payload.get("action")
        chat_id = payload.get("chatId") or "default_chat"  # 使用默认ID如果为None
        contact_name = payload.get("contactName") or "unknown"
        message = payload.get("message", {})
        conversation_memory = payload.get("conversationMemory", [])
        
        # 调试日志
        logger.info(f"[Memory Update调试] action: {action}, chatId: {chat_id}, contactName: {contact_name}")
        logger.info(f"[Memory Update调试] 消息类型: {message.get('messageType')}, 记忆长度: {len(conversation_memory)}")
        if conversation_memory:
            logger.info(f"[Memory Update调试] 记忆内容预览: {conversation_memory[-1] if conversation_memory else 'None'}")
        
        if action == "add_message":  # 移除chat_id检查，因为已经有默认值
            # 更新存储的记忆
            self.memory_store[chat_id] = conversation_memory.copy()
            logger.info(f"[记忆存储] 已存储到key: {chat_id}, 记忆条数: {len(conversation_memory)}")
            
            # 检查是否需要AI回复
            if message.get("messageType") == "customer":
                try:
                    customer_msg = message.get("originalContent", "")
                    logger.info(f"[记忆调试] 客户消息: {customer_msg}")
                    logger.info(f"[记忆调试] 对话历史长度: {len(conversation_memory)}")
                    
                    # 打印最近几条对话历史用于调试
                    if conversation_memory:
                        logger.info(f"[记忆调试] 最近对话历史:")
                        for i, mem in enumerate(conversation_memory[-5:], 1):
                            role = mem.get("role", "unknown")
                            content = mem.get("content", "")[:50]
                            logger.info(f"  {i}. {role}: {content}...")
                    
                    # 传递完整的对话历史给AI
                    ai_response = await self.ai_client.generate_customer_service_reply(
                        customer_msg,
                        conversation_history=conversation_memory
                    )
                    if ai_response:
                        logger.info(f"[AI回复] 为 {contact_name} 生成回复: {ai_response.content[:50]}...")
                        await self._broadcast_ai_reply(ai_response)
                except Exception as e:
                    logger.error(f"[AI错误] 处理客户消息失败: {e}")
            
            logger.info(f"[记忆] 更新 {contact_name} 的记忆 ({len(conversation_memory)}条)")
        
        return {
            "type": "memory_updated",
            "message": f"记忆已更新: {contact_name}",
            "chat_id": chat_id,
            "memory_count": len(conversation_memory),
            "timestamp": timestamp
        }

    async def handle_memory_save(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """处理记忆保存"""
        payload = data.get("payload", {})
        chat_id = payload.get("chatId") or "default_chat"  # 使用默认ID如果为None
        contact_name = payload.get("contactName") or "unknown"
        conversation_memory = payload.get("conversationMemory", [])
        
        if conversation_memory:  # 只要有记忆就保存，不需要检查chat_id
            self.memory_store[chat_id] = conversation_memory.copy()
            logger.info(f"[记忆] 自动保存 {contact_name} 的记忆 ({len(conversation_memory)}条)")
            
            # TODO: 这里可以添加持久化到文件的逻辑
            # await self._persist_memory_to_file(chat_id, contact_name, conversation_memory)
        
        return {
            "type": "memory_saved",
            "message": f"记忆已保存: {contact_name}",
            "chat_id": chat_id,
            "memory_count": len(conversation_memory),
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

    async def _process_data_with_memory(self, data_list: list):
        """使用记忆系统处理数据并生成AI回复"""
        if not data_list:
            return
            
        # 查找最后一条客户消息（非商家消息）
        last_customer_message = None
        chat_id = None
        contact_name = None
        
        for item in reversed(data_list):
            content = item.get('content', '')
            if isinstance(content, str):
                # 检查是否为客户消息（非商家消息）
                if content.startswith('[客户]'):
                    last_customer_message = content[4:].strip()  # 去掉[客户]前缀
                    chat_id = item.get('chatId') or 'default_chat'  # 使用默认ID如果没有chatId
                    contact_name = item.get('contactName') or 'unknown'
                    break
                elif not content.startswith('[商家]') and not content.startswith('[未知]'):
                    # 如果没有前缀，可能也是客户消息
                    last_customer_message = content.strip()
                    chat_id = item.get('chatId') or 'default_chat'
                    contact_name = item.get('contactName') or 'unknown'
                    break
        
        if not last_customer_message:
            logger.debug("[记忆处理] 没有找到客户消息")
            return
            
        logger.info(f"[记忆处理] 检测到客户消息: {last_customer_message}")
        logger.info(f"[记忆处理] ChatID: {chat_id}, 联系人: {contact_name}")
        
        # 获取对应的记忆
        conversation_memory = self.memory_store.get(chat_id, [])
        
        logger.info(f"[记忆处理] 客户消息: {last_customer_message}")
        logger.info(f"[记忆处理] 对话历史长度: {len(conversation_memory)}")
        logger.info(f"[记忆处理] 当前memory_store keys: {list(self.memory_store.keys())}")
        logger.info(f"[记忆处理] 查找的chatId: {chat_id}")
        
        # 打印最近几条对话历史用于调试
        if conversation_memory:
            logger.info(f"[记忆处理] 最近对话历史:")
            for i, mem in enumerate(conversation_memory[-5:], 1):
                role = mem.get("role", "unknown")
                content = mem.get("content", "")[:50]
                logger.info(f"  {i}. {role}: {content}...")
        
        # 使用对话历史生成AI回复
        try:
            ai_response = await self.ai_client.generate_customer_service_reply(
                last_customer_message,
                conversation_history=conversation_memory
            )
            if ai_response:
                logger.info(f"[AI回复] 为 {contact_name} 生成回复: {ai_response.content[:50]}...")
                await self._broadcast_ai_reply(ai_response)
        except Exception as e:
            logger.error(f"[AI错误] 使用记忆生成回复失败: {e}")

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