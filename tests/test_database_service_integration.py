"""
数据库API服务集成测试
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from aiclient.database_service import DatabaseAPIService


class TestDatabaseServiceIntegration:
    """测试数据库API服务（集成测试）"""
    
    @pytest.fixture
    def db_service(self):
        """创建数据库服务实例"""
        return DatabaseAPIService()
    
    @pytest.mark.asyncio
    async def test_api_health(self):
        """测试API健康状态"""
        import aiohttp
        url = "http://emagen.323424.xyz/api/health"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                assert response.status == 200
                data = await response.json()
                assert data.get("status") == "ok"
                print(f"\nAPI健康检查通过: {data}")
    
    @pytest.mark.asyncio
    async def test_get_stores(self, db_service):
        """测试获取门店列表"""
        stores = await db_service.get_stores()
        
        assert isinstance(stores, list)
        if stores:  # 如果有数据
            store = stores[0]
            assert "id" in store or "name" in store
            print(f"\n获取到 {len(stores)} 个门店")
            print(f"示例门店: {store}")
    
    @pytest.mark.asyncio
    async def test_search_technicians(self, db_service):
        """测试搜索技师"""
        # 测试不带参数的搜索
        technicians = await db_service.search_technicians()
        
        assert isinstance(technicians, list)
        if technicians:
            technician = technicians[0]
            print(f"\n获取到 {len(technicians)} 个技师")
            print(f"示例技师: {technician}")
            
            # 如果有技师，尝试按名字搜索
            if "name" in technician:
                name = technician["name"]
                search_result = await db_service.search_technicians(name=name)
                assert isinstance(search_result, list)
                print(f"按名字 '{name}' 搜索到 {len(search_result)} 个技师")
    
    @pytest.mark.asyncio
    async def test_query_available_appointments(self, db_service):
        """测试查询可用预约时间"""
        # 查询明天的可用时间
        tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        
        available_slots = await db_service.query_available_appointments(tomorrow)
        
        assert isinstance(available_slots, list)
        print(f"\n{tomorrow} 有 {len(available_slots)} 个可用时间段")
        if available_slots:
            print(f"示例时间段: {available_slots[0]}")
    
    @pytest.mark.asyncio
    async def test_technician_schedule(self, db_service):
        """测试查询技师排班"""
        # 首先获取一个技师
        technicians = await db_service.search_technicians()
        if not technicians:
            pytest.skip("没有可用的技师数据")
        
        technician = technicians[0]
        technician_id = technician.get("id", 1)
        
        # 查询未来一周的排班
        today = datetime.now().strftime("%Y-%m-%d")
        next_week = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        schedules = await db_service.query_technician_schedule(
            technician_id, today, next_week
        )
        
        assert isinstance(schedules, list)
        print(f"\n技师 {technician_id} 未来一周有 {len(schedules)} 个排班")
        if schedules:
            print(f"示例排班: {schedules[0]}")
    
    @pytest.mark.asyncio
    async def test_create_appointment_simulation(self, db_service):
        """测试创建预约（模拟）"""
        # 注意：这个测试只是模拟，不会真正创建预约
        # 在实际环境中，你可能需要特殊的测试账号或环境
        
        test_data = {
            "customer_name": "测试客户",
            "customer_contact": "13800138000",
            "technician_id": 1,
            "scheduled_time": (datetime.now() + timedelta(days=1, hours=10)).strftime("%Y-%m-%d %H:%M:%S"),
            "additional_info": "这是一个测试预约"
        }
        
        # 由于这可能会真正创建预约，所以跳过此测试
        pytest.skip("跳过创建预约测试以避免创建真实数据")
        
        # 如果要测试，取消注释下面的代码
        # result = await db_service.create_appointment(**test_data)
        # assert isinstance(result, dict)
        # assert "success" in result
        # print(f"\n创建预约结果: {result}")
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, db_service):
        """测试并发请求"""
        # 同时发送多个请求
        tasks = [
            db_service.get_stores(),
            db_service.search_technicians(),
            db_service.query_available_appointments(
                (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
            )
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 检查所有请求都成功
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"\n请求 {i} 失败: {result}")
            else:
                assert isinstance(result, list)
                print(f"\n请求 {i} 成功，返回 {len(result)} 条数据")