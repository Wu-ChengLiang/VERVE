#!/usr/bin/env python3
"""测试所有API函数调用功能"""

import asyncio
import sys
import os
from datetime import datetime, timedelta

# 添加项目根目录到path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'aiclient'))

from aiclient.adapters.openai_adapter import OpenAIAdapter
from aiclient.config import ModelConfig

async def test_all_functions():
    """测试所有API函数调用"""
    
    # 创建配置
    config = ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        api_key="test-key",  # 测试用，不需要真实的key
        base_url="https://api.openai.com/v1"
    )
    
    # 创建适配器
    adapter = OpenAIAdapter(config)
    
    print("🚀 开始测试所有API函数调用...")
    print("=" * 50)
    
    # 1. 测试获取门店列表
    print("\n1️⃣  测试获取门店列表 (get_stores)")
    try:
        result = await adapter.execute_function_call("get_stores", {})
        if result["success"]:
            print(f"✅ 成功: {result['message']}")
            print(f"门店示例: {result['data'][:2] if result['data'] else '无数据'}")
        else:
            print(f"❌ 失败: {result['message']}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 2. 测试搜索技师
    print("\n2️⃣  测试搜索技师 (search_technicians)")
    try:
        result = await adapter.execute_function_call("search_technicians", {})
        if result["success"]:
            print(f"✅ 成功: {result['message']}")
            print(f"技师示例: {result['data'][:2] if result['data'] else '无数据'}")
        else:
            print(f"❌ 失败: {result['message']}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 3. 测试搜索特定技师
    print("\n3️⃣  测试搜索特定技师 (搜索'老师')")
    try:
        result = await adapter.execute_function_call("search_technicians", {"name": "老师"})
        if result["success"]:
            print(f"✅ 成功: {result['message']}")
            if result['data']:
                for tech in result['data'][:3]:
                    print(f"   - {tech.get('name', '未知')} (ID: {tech.get('id', '?')}, 门店ID: {tech.get('store_id', '?')})")
        else:
            print(f"❌ 失败: {result['message']}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 4. 测试查询可用预约时间
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"\n4️⃣  测试查询可用预约时间 ({tomorrow})")
    try:
        result = await adapter.execute_function_call("query_available_appointments", {"target_date": tomorrow})
        if result["success"]:
            print(f"✅ 成功: {result['message']}")
        else:
            print(f"❌ 失败: {result['message']}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    # 5. 测试查询技师排班
    print(f"\n5️⃣  测试查询技师排班 (技师ID: 1)")
    try:
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        result = await adapter.execute_function_call("query_technician_schedule", {
            "technician_id": 1,
            "start_date": start_date,
            "end_date": end_date
        })
        if result["success"]:
            print(f"✅ 成功: {result['message']}")
        else:
            print(f"❌ 失败: {result['message']}")
    except Exception as e:
        print(f"❌ 异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 API函数调用测试完成!")

if __name__ == "__main__":
    asyncio.run(test_all_functions()) 