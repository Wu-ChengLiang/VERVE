#!/usr/bin/env python3
"""
大众点评网页元素读取器 - WebSocket服务器
负责接收来自浏览器扩展的数据并进行处理
"""

import asyncio
import websockets
import json
import logging
from datetime import datetime
from typing import Set, Dict, Any
import signal
import sys

# 配置日志 - 修复Windows编码问题
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
    """大众点评WebSocket服务器"""
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.clients: Set[websockets.WebSocketServerProtocol] = set()
        self.data_store: Dict[str, Any] = {}
        
    async def register_client(self, websocket: websockets.WebSocketServerProtocol):
        """注册新客户端连接"""
        self.clients.add(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"[SUCCESS] 客户端连接: {client_info}")
        logger.info(f"[INFO] 当前连接数: {len(self.clients)}")
        
        # 发送欢迎消息
        welcome_msg = {
            "type": "welcome",
            "message": "连接成功! 大众点评数据提取服务已就绪",
            "timestamp": datetime.now().isoformat(),
            "server_info": {
                "host": self.host,
                "port": self.port,
                "version": "1.0.0"
            }
        }
        await websocket.send(json.dumps(welcome_msg, ensure_ascii=False))

    async def unregister_client(self, websocket: websockets.WebSocketServerProtocol):
        """注销客户端连接"""
        self.clients.discard(websocket)
        client_info = f"{websocket.remote_address[0]}:{websocket.remote_address[1]}"
        logger.info(f"[DISCONNECT] 客户端断开: {client_info}")
        logger.info(f"[INFO] 当前连接数: {len(self.clients)}")

    async def handle_message(self, websocket: websockets.WebSocketServerProtocol, message: str):
        """处理来自客户端的消息"""
        try:
            data = json.loads(message)
            timestamp = datetime.now().isoformat()
            
            response = None
            if isinstance(data, list):
                logger.info(f"[MESSAGE] 收到消息数组 (共 {len(data)} 条)")
                response = await self.handle_dianping_data_list(data, timestamp)
            elif isinstance(data, dict):
                msg_type = data.get("type", "unknown")
                logger.info(f"[MESSAGE] 收到消息类型: {msg_type}")
                logger.debug(f"[MESSAGE] 消息内容: {json.dumps(data, ensure_ascii=False, indent=2)}")
                response = await self.process_message_by_type(data, timestamp)
            else:
                logger.warning(f"⚠️ 收到了未知的数据类型: {type(data)}")
                response = {
                    "type": "error",
                    "message": "不支持的数据类型",
                    "timestamp": timestamp
                }
            
            if response:
                await websocket.send(json.dumps(response, ensure_ascii=False))
                logger.info(f"[RESPONSE] 发送响应: {response.get('type', 'unknown')}")
                
        except json.JSONDecodeError as e:
            logger.error(f"[ERROR] JSON解析错误: {e}")
            await websocket.send(json.dumps({
                "type": "error", "message": "JSON格式错误", "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False))
        except Exception as e:
            logger.error(f"[ERROR] 消息处理错误: {e}")
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
            # 处理大众点评数据
            return await self.handle_dianping_data(data, timestamp)
            
        elif msg_type == "page_info":
            # 处理页面信息
            return await self.handle_page_info(data, timestamp)
            
        else:
            logger.warning(f"⚠️ 未知消息类型: {msg_type}")
            return {
                "type": "error",
                "message": f"未知的消息类型: {msg_type}",
                "timestamp": timestamp
            }

    async def handle_dianping_data_list(self, data_list: list, timestamp: str) -> Dict[str, Any]:
        """专门处理聊天消息列表"""
        logger.info(f"[CHAT] 提取到 {len(data_list)} 条聊天消息:")
        for msg in data_list:
            content = msg.get('content', '无内容')
            logger.info(f"  - {content}")
        
        data_id = f"dianping_chat_{timestamp}"
        self.data_store[data_id] = {
            "content": data_list,
            "url": "N/A (来自列表)",
            "timestamp": timestamp,
            "type": "dianping_chat_list"
        }
        
        return {
            "type": "data_received",
            "message": f"聊天数据列表已接收 ({len(data_list)}条)",
            "data_id": data_id,
            "timestamp": timestamp
        }

    async def handle_dianping_data(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """处理大众点评数据(旧格式)"""
        content = data.get("payload", {}) # Adjusted to match client structure
        page_url = content.get("pageUrl", "N/A")
        
        data_id = f"dianping_{timestamp}"
        self.data_store[data_id] = {
            "content": content,
            "url": page_url,
            "timestamp": timestamp,
            "type": "dianping_data_object"
        }
        
        logger.info(f"[DATA] 存储大众点评数据对象: {data_id}")
        logger.info(f"[URL] 页面URL: {page_url}")
        
        if content.get("pageType") == "chat_page":
            messages = content.get("data", {}).get("messages", [])
            logger.info(f"[CHAT] 提取到 {len(messages)} 条聊天消息:")
            for msg in messages:
                logger.info(f"  - {msg.get('content')}")
        
        return {
            "type": "data_received",
            "message": "大众点评数据对象已接收",
            "data_id": data_id,
            "timestamp": timestamp
        }

    async def handle_page_info(self, data: Dict[str, Any], timestamp: str) -> Dict[str, Any]:
        """处理页面信息"""
        page_info = data.get("page_info", {})
        
        logger.info(f"[PAGE_INFO] 收到页面信息:")
        logger.info(f"   - 标题: {page_info.get('title', 'N/A')}")
        logger.info(f"   - URL: {page_info.get('url', 'N/A')}")
        logger.info(f"   - 元素数量: {page_info.get('element_count', 0)}")
        
        # 打印所有元素的详细信息
        elements = page_info.get('elements', [])
        if elements:
            logger.info(f"[ELEMENTS] 开始打印所有 {len(elements)} 个元素的详细信息:")
            logger.info("=" * 80)
            
            for element in elements:
                try:
                    logger.info(f"元素 #{element.get('index', 'N/A')}:")
                    logger.info(f"  标签: <{element.get('tagName', 'unknown')}>")
                    
                    if element.get('id'):
                        logger.info(f"  ID: {element.get('id')}")
                    
                    if element.get('className'):
                        logger.info(f"  Class: {element.get('className')}")
                    
                    if element.get('textContent'):
                        logger.info(f"  文本内容: {element.get('textContent')[:50]}...")
                    
                    # 打印位置信息
                    position = element.get('position', {})
                    if position:
                        logger.info(f"  位置: top={position.get('offsetTop', 0)}, left={position.get('offsetLeft', 0)}")
                        logger.info(f"  尺寸: width={position.get('offsetWidth', 0)}, height={position.get('offsetHeight', 0)}")
                    
                    # 打印重要属性
                    attributes = element.get('attributes', {})
                    if attributes:
                        attr_str = ", ".join([f"{k}='{v}'" for k, v in attributes.items() if v])
                        if attr_str:
                            logger.info(f"  属性: {attr_str}")
                    
                    logger.info("-" * 40)
                    
                except Exception as e:
                    logger.error(f"  打印元素信息时出错: {e}")
            
            logger.info("=" * 80)
            logger.info(f"[ELEMENTS] 完成打印所有 {len(elements)} 个元素")
        else:
            logger.warning("[ELEMENTS] 未收到元素详细信息，可能是旧版本扩展")
        
        return {
            "type": "page_info_received",
            "message": "页面信息已接收",
            "timestamp": timestamp
        }

    async def handle_client(self, websocket: websockets.WebSocketServerProtocol, path: str):
        """处理客户端连接"""
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
        logger.info(f"[START] 启动大众点评WebSocket服务器...")
        logger.info(f"[SERVER] 监听地址: {self.host}:{self.port}")
        
        # 启动WebSocket服务器
        start_server = websockets.serve(
            self.handle_client,
            self.host,
            self.port,
            ping_interval=20,
            ping_timeout=10
        )
        
        logger.info(f"[SUCCESS] 服务器启动成功! 等待连接...")
        logger.info(f"[WEBSOCKET] 浏览器扩展可以连接到: ws://{self.host}:{self.port}")
        
        return start_server

    def get_stats(self) -> Dict[str, Any]:
        """获取服务器统计信息"""
        return {
            "connected_clients": len(self.clients),
            "stored_data_count": len(self.data_store),
            "server_host": self.host,
            "server_port": self.port,
            "uptime": datetime.now().isoformat()
        }

async def main():
    """主函数"""
    # 创建服务器实例
    server = DianpingWebSocketServer()
    
    # 处理优雅关闭
    def signal_handler(signum, frame):
        logger.info("🛑 收到停止信号，正在关闭服务器...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动服务器
        start_server = await server.start_server()
        
        # 运行服务器
        await start_server
        
        # 保持运行
        await asyncio.Future()  # 永远运行
        
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