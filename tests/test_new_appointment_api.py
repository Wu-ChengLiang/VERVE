#!/usr/bin/env python3
"""
测试生产环境API - 修复后版本
"""

import requests
import json
from urllib.parse import quote

# API基础URL
BASE_URL = "http://emagen.323424.xyz/api"

def test_therapist_queries():
    """测试技师查询API"""
    print("=== 测试技师查询API ===\n")
    
    # 1. 按技师名查询
    print("1. 按技师名查询（陈老师）：")
    response = requests.get(f"{BASE_URL}/therapists", params={
        "action": "query_schedule",
        "therapist_name": "陈老师"
    })
    if response.status_code == 200:
        data = response.json()
        print(f"   找到 {len(data.get('therapists', []))} 个技师")
        if data.get('therapists'):
            therapist = data['therapists'][0]
            print(f"   技师: {therapist['name']} - {therapist['title']}")
            print(f"   门店: {therapist['store_name']}")
            print(f"   专长: {', '.join(therapist['specialties'])}")
    else:
        print(f"   错误: {response.status_code}")
    
    # 2. 按门店查询
    print("\n2. 按门店查询（莘庄店）：")
    response = requests.get(f"{BASE_URL}/therapists", params={
        "action": "query_schedule",
        "store_name": "莘庄店"
    })
    if response.status_code == 200:
        data = response.json()
        print(f"   找到 {len(data.get('therapists', []))} 个技师")
        for therapist in data.get('therapists', [])[:3]:  # 显示前3个
            print(f"   - {therapist['name']} ({therapist['title']})")
    
    # 3. 按服务类型查询
    print("\n3. 按服务类型查询（艾灸）：")
    response = requests.get(f"{BASE_URL}/therapists", params={
        "action": "query_schedule",
        "service_type": "艾灸"
    })
    if response.status_code == 200:
        data = response.json()
        print(f"   找到 {len(data.get('therapists', []))} 个技师")
        for therapist in data.get('therapists', [])[:3]:  # 显示前3个
            print(f"   - {therapist['name']} ({therapist.get('store_name', 'N/A')})")

def test_appointment_flow():
    """测试预约流程"""
    print("\n\n=== 测试预约流程 ===\n")
    
    # 1. 查询技师可用时间
    print("1. 查询技师可用时间：")
    response = requests.get(f"{BASE_URL}/appointments/availability/1", params={
        "date": "2025-06-16"
    })
    if response.status_code == 200:
        data = response.json()
        print(f"   可用时段: {', '.join(data.get('available_times', [])[:5])}...")
    
    # 2. 创建预约
    print("\n2. 创建预约：")
    appointment_data = {
        "username": "TEST_PYTHON_USER",
        "customer_name": "测试客户",
        "customer_phone": "13800138000",
        "therapist_id": 1,
        "appointment_date": "2025-06-16",
        "appointment_time": "14:00",
        "service_type": "经络疏通",
        "notes": "Python测试预约"
    }
    
    response = requests.post(f"{BASE_URL}/appointments", json=appointment_data)
    if response.status_code in [200, 201]:
        data = response.json()
        print(f"   预约成功！ID: {data.get('appointment', {}).get('id')}")
        appointment_id = data.get('appointment', {}).get('id')
        
        # 3. 查看用户预约
        print("\n3. 查看用户预约：")
        response = requests.get(f"{BASE_URL}/appointments/user/TEST_PYTHON_USER")
        if response.status_code == 200:
            data = response.json()
            appointments = data.get('appointments', [])
            print(f"   用户共有 {len(appointments)} 个预约")
        
        # 4. 取消预约
        if appointment_id:
            print(f"\n4. 取消预约 (ID: {appointment_id})：")
            response = requests.delete(
                f"{BASE_URL}/appointments/{appointment_id}",
                params={"username": "TEST_PYTHON_USER"}
            )
            if response.status_code in [200, 204]:
                print("   预约已取消")
    else:
        print(f"   预约失败: {response.status_code} - {response.text}")

if __name__ == "__main__":
    print("🚀 开始测试生产环境API (http://emagen.323424.xyz/api)\n")
    print("=" * 60)
    
    # 测试技师查询
    test_therapist_queries()
    
    # 测试预约流程
    test_appointment_flow()
    
    print("\n" + "=" * 60)
    print("✅ 测试完成！")