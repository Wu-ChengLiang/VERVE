"""
配置文件 - 大众点评网页元素读取器
"""

import os
from typing import Dict, Any

class Config:
    """服务器配置类"""
    
    # WebSocket服务器配置
    WEBSOCKET_HOST = os.getenv("WEBSOCKET_HOST", "localhost")
    WEBSOCKET_PORT = int(os.getenv("WEBSOCKET_PORT", 8767))
    
    # 日志配置
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "dianping_scraper.log")
    
    # 数据存储配置
    DATA_STORE_PATH = os.getenv("DATA_STORE_PATH", "./data")
    MAX_DATA_ENTRIES = int(os.getenv("MAX_DATA_ENTRIES", 1000))
    
    # WebSocket连接配置
    PING_INTERVAL = int(os.getenv("PING_INTERVAL", 20))
    PING_TIMEOUT = int(os.getenv("PING_TIMEOUT", 10))
    MAX_CONNECTIONS = int(os.getenv("MAX_CONNECTIONS", 10))
    
    # 大众点评特定配置
    DIANPING_DOMAIN = "dianping.com"
    ALLOWED_ORIGINS = [
        "https://g.dianping.com",
        "https://www.dianping.com",
        "chrome-extension://*"
    ]
    
    @classmethod
    def get_config_dict(cls) -> Dict[str, Any]:
        """获取配置字典"""
        return {
            "websocket": {
                "host": cls.WEBSOCKET_HOST,
                "port": cls.WEBSOCKET_PORT,
                "ping_interval": cls.PING_INTERVAL,
                "ping_timeout": cls.PING_TIMEOUT,
                "max_connections": cls.MAX_CONNECTIONS
            },
            "logging": {
                "level": cls.LOG_LEVEL,
                "file": cls.LOG_FILE
            },
            "data": {
                "store_path": cls.DATA_STORE_PATH,
                "max_entries": cls.MAX_DATA_ENTRIES
            },
            "dianping": {
                "domain": cls.DIANPING_DOMAIN,
                "allowed_origins": cls.ALLOWED_ORIGINS
            }
        }
    
    @classmethod
    def print_config(cls):
        """打印当前配置"""
        config = cls.get_config_dict()
        print("📋 当前服务器配置:")
        for section, settings in config.items():
            print(f"  {section.upper()}:")
            for key, value in settings.items():
                print(f"    {key}: {value}")
        print()

# 创建全局配置实例
config = Config() 