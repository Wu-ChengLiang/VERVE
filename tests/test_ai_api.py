#!/usr/bin/env python3
"""
AI API实际调用测试
"""

import asyncio
import logging
from aiclient import AIClient, AIProvider

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def test_single_provider(client: AIClient, provider: AIProvider, test_message: str):
    """测试单个AI提供商"""
    print(f"\n🧪 测试 {provider.value} 提供商...")
    
    try:
        response = await client.generate_customer_service_reply(
            test_message, 
            preferred_provider=provider
        )
        
        print(f"✅ {provider.value} 成功响应:")
        print(f"   模型: {response.model}")
        print(f"   内容: {response.content[:200]}...")
        print(f"   用量: {response.usage}")
        
        return True
        
    except Exception as e:
        print(f"❌ {provider.value} 调用失败: {e}")
        return False


async def test_all_providers():
    """测试所有AI提供商"""
    print("🚀 开始测试所有AI提供商...")
    
    client = AIClient()
    status = client.get_status()
    print(f"📊 客户端状态: {status}")
    
    test_message = "您好，我需要女技师为我服务，预计18:30到店"
    
    results = {}
    
    # 测试每个可用的提供商
    for provider in client.adapters.keys():
        success = await test_single_provider(client, provider, test_message)
        results[provider.value] = success
    
    # 汇总结果
    print("\n" + "="*50)
    print("📋 测试结果汇总:")
    for provider, success in results.items():
        status = "✅ 成功" if success else "❌ 失败"
        print(f"   {provider}: {status}")
    
    successful_providers = sum(results.values())
    total_providers = len(results)
    print(f"\n🎯 总体结果: {successful_providers}/{total_providers} 个提供商可用")
    
    return results


async def test_message_processing():
    """测试消息处理流程"""
    print("\n🔄 测试完整的消息处理流程...")
    
    client = AIClient()
    
    # 测试数据
    test_cases = [
        [{"content": "[客户] 您好，我需要女技师为我服务，预计18:30到店"}],
        [{"content": "[客户] 请问你们有什么特色服务吗？"}],
        [{"content": "[商家] 好的，为您安排"}],  # 这个不应该触发AI回复
        []  # 空数据
    ]
    
    for i, test_data in enumerate(test_cases, 1):
        print(f"\n测试案例 {i}: {test_data}")
        
        try:
            response = await client.process_scraped_data(test_data)
            if response:
                print(f"✅ 生成AI回复: {response.content[:100]}...")
            else:
                print("ℹ️ 无需回复（正确行为）")
        except Exception as e:
            print(f"❌ 处理失败: {e}")


async def main():
    """主函数"""
    print("🎯 AI API实际调用测试")
    print("🔑 使用配置的API密钥进行真实API调用")
    print()
    
    try:
        # 测试所有提供商
        await test_all_providers()
        
        # 测试消息处理
        await test_message_processing()
        
        print("\n🎉 AI API测试完成!")
        
    except Exception as e:
        print(f"\n❌ 测试异常: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 