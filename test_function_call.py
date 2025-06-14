#!/usr/bin/env python3
"""
测试OpenAI Function Call与数据库查询集成
"""

import asyncio
import logging
import sys
import os

# 添加项目路径到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from aiclient.client import AIClient
from aiclient.config import AIProvider

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


async def test_function_call():
    """测试Function Call功能"""
    
    try:
        # 初始化AI客户端
        logger.info("初始化AI客户端...")
        client = AIClient()
        
        # 检查状态
        status = client.get_status()
        logger.info(f"客户端状态: {status}")
        
        if not status["function_call_enabled"]:
            logger.error("Function Call功能未启用")
            return
        
        # 测试用例
        test_cases = [
            {
                "message": "我想预约明天的理疗服务",
                "description": "测试预约查询（应该触发查询可用时间段）"
            },
            {
                "message": "你们有哪些技师？",
                "description": "测试技师查询"
            },
            {
                "message": "张师傅这周的排班怎么样？",
                "description": "测试技师排班查询"
            },
            {
                "message": "我要预约张师傅明天下午2点的服务，我叫李小明，手机13800138000",
                "description": "测试创建预约"
            }
        ]
        
        # 执行测试用例
        for i, test_case in enumerate(test_cases, 1):
            logger.info(f"\n=== 测试用例 {i}: {test_case['description']} ===")
            logger.info(f"客户消息: {test_case['message']}")
            
            try:
                # 生成客服回复
                response = await client.generate_customer_service_reply(
                    customer_message=test_case['message'],
                    preferred_provider=AIProvider.OPENAI
                )
                
                logger.info(f"AI回复: {response.content}")
                
                if response.tool_calls:
                    logger.info(f"触发了 {len(response.tool_calls)} 个函数调用:")
                    for tool_call in response.tool_calls:
                        logger.info(f"  - {tool_call['function']['name']}: {tool_call['function']['arguments']}")
                else:
                    logger.info("未触发函数调用")
                
                # 添加到记忆中
                client.add_to_memory("user", test_case['message'])
                client.add_to_memory("assistant", response.content)
                
                logger.info("=" * 50)
                
            except Exception as e:
                logger.error(f"测试用例 {i} 失败: {e}")
                continue
    
    except Exception as e:
        logger.error(f"测试失败: {e}")
        raise


async def test_database_service():
    """测试数据库服务"""
    
    logger.info("\n=== 测试数据库服务 ===")
    
    try:
        from aiclient.database_service import DatabaseAPIService
        
        # 初始化数据库服务
        db_service = DatabaseAPIService()
        
        # 测试查询技师
        logger.info("测试查询技师...")
        technicians = await db_service.search_technicians()
        logger.info(f"查询到 {len(technicians)} 个技师")
        
        if technicians:
            logger.info(f"技师列表: {technicians}")
            
            # 使用第一个技师测试排班查询
            first_technician = technicians[0]
            technician_id = first_technician['id']
            
            logger.info(f"测试查询技师 {technician_id} 的排班...")
            schedule = await db_service.query_technician_schedule(
                technician_id=technician_id,
                start_date="2024-12-01",
                end_date="2024-12-31"
            )
            logger.info(f"查询到 {len(schedule)} 个排班记录")
            
            # 测试查询可用预约时间
            logger.info("测试查询可用预约时间...")
            available_times = await db_service.query_available_appointments("2024-12-20")
            logger.info(f"查询到 {len(available_times)} 个可用时间段")
        
        logger.info("数据库服务测试完成")
        
    except Exception as e:
        logger.error(f"数据库服务测试失败: {e}")


if __name__ == "__main__":
    print("🚀 开始测试OpenAI Function Call功能")
    
    # 运行数据库服务测试
    asyncio.run(test_database_service())
    
    # 运行Function Call测试
    asyncio.run(test_function_call())
    
    print("✅ 测试完成") 