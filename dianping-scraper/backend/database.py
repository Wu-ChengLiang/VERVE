import sqlite3
import hashlib
import json
import logging
import threading
import os
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class DatabaseManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path='dianping_history.db'):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(DatabaseManager, cls).__new__(cls)
                    cls._instance.db_path = db_path
                    cls._instance.conn = None
                    cls._instance._init_db()
        return cls._instance

    def _init_db(self):
        """初始化数据库和表"""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row
            cursor = self.conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    chat_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    timestamp TEXT,
                    raw_data TEXT NOT NULL,
                    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_chat_id ON messages (chat_id)')
            self.conn.commit()
            logger.info(f"[数据库] 数据库 '{self.db_path}' 初始化成功")
        except sqlite3.Error as e:
            logger.error(f"[数据库] 数据库初始化失败: {e}")
            raise

    def _generate_message_id(self, message: Dict[str, Any]) -> str:
        """
        为消息生成一个确定性的唯一ID。
        只使用稳定的字段：chatId, role, content。
        排除不稳定的timestamp和messageId。
        """
        keys_to_hash = [
            str(message.get('chatId', '')),
            str(message.get('role', '')),
            str(message.get('content', '')),
        ]
        
        message_string = "".join(keys_to_hash)
        return hashlib.md5(message_string.encode('utf-8')).hexdigest()

    def is_message_processed(self, message_id: str) -> bool:
        """检查消息ID是否已在数据库中"""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT 1 FROM messages WHERE id = ?", (message_id,))
            return cursor.fetchone() is not None
        except sqlite3.Error as e:
            logger.error(f"[数据库] 查询消息失败 (ID: {message_id}): {e}")
            return False # 出错时保守地认为未处理

    def add_message(self, message: Dict[str, Any]):
        """将一条消息添加到数据库"""
        message_id = self._generate_message_id(message)
        if self.is_message_processed(message_id):
            return

        chat_id = message.get('chatId', 'unknown_chat')
        role = message.get('role', 'unknown')
        content = message.get('content', '')
        timestamp = message.get('timestamp')
        raw_data = json.dumps(message, ensure_ascii=False)

        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "INSERT INTO messages (id, chat_id, role, content, timestamp, raw_data) VALUES (?, ?, ?, ?, ?, ?)",
                (message_id, chat_id, role, content, timestamp, raw_data)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
             # 并发情况下可能重复插入，可以安全忽略
            pass
        except sqlite3.Error as e:
            logger.error(f"[数据库] 添加消息失败 (ID: {message_id}): {e}")

    def get_chat_history(self, chat_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """获取指定聊天的历史记录"""
        history = []
        try:
            cursor = self.conn.cursor()
            # 按时间戳和ID排序，确保顺序
            cursor.execute(
                "SELECT raw_data FROM messages WHERE chat_id = ? ORDER BY timestamp, id LIMIT ?",
                (chat_id, limit)
            )
            rows = cursor.fetchall()
            for row in rows:
                history.append(json.loads(row['raw_data']))
        except sqlite3.Error as e:
            logger.error(f"[数据库] 获取聊天历史失败 (ChatID: {chat_id}): {e}")
        return history

    def close(self):
        """关闭数据库连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logger.info("[数据库] 数据库连接已关闭")

# 单例模式，方便在应用中各处调用
db_manager = DatabaseManager() 