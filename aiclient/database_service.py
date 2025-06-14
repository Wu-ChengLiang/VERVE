"""
数据库API服务
用于调用外部API获取门店、技师、预约等信息
"""

import logging
import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)


class DatabaseAPIService:
    """数据库API服务类"""
    
    def __init__(self, base_url: str = "http://emagen.323424.xyz/api"):
        self.base_url = base_url
        self.logger = logger.getChild(self.__class__.__name__)
    
    async def _make_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送HTTP请求到API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        self.logger.error(f"API错误 {response.status}: {error_text}")
                        raise Exception(f"API错误 {response.status}: {error_text}")
        except Exception as e:
            self.logger.error(f"请求失败 {url}: {e}")
            raise
    
    async def query_available_appointments(self, target_date: str, technician_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询可用预约时间
        
        Args:
            target_date: 目标日期 (YYYY-MM-DD)
            technician_id: 技师ID（可选）
            
        Returns:
            可用时间段列表
        """
        params = {
            "action": "query_available",
            "date": target_date
        }
        if technician_id:
            params["technician_id"] = technician_id
        
        try:
            result = await self._make_request("/appointments", params)
            return result.get("available_slots", [])
        except Exception as e:
            self.logger.error(f"查询可用预约失败: {e}")
            return []
    
    async def search_technicians(self, name: Optional[str] = None, skill: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        搜索技师
        
        Args:
            name: 技师姓名（支持模糊搜索）
            skill: 技师技能
            
        Returns:
            技师列表
        """
        params = {}
        if name:
            params["name"] = name
        if skill:
            params["skill"] = skill
        
        try:
            result = await self._make_request("/therapists", params)
            # 如果返回的是数组，直接返回；如果是对象包含therapists字段，则返回therapists
            if isinstance(result, list):
                return result
            return result.get("therapists", [])
        except Exception as e:
            self.logger.error(f"搜索技师失败: {e}")
            return []
    
    async def query_technician_schedule(self, technician_id: int, start_date: str, end_date: str) -> List[Dict[str, Any]]:
        """
        查询技师排班
        
        Args:
            technician_id: 技师ID
            start_date: 开始日期 (YYYY-MM-DD)
            end_date: 结束日期 (YYYY-MM-DD)
            
        Returns:
            排班记录列表
        """
        params = {
            "action": "query_schedule",
            "technician_id": technician_id,
            "start_date": start_date,
            "end_date": end_date
        }
        
        try:
            result = await self._make_request("/therapists", params)
            return result.get("schedules", [])
        except Exception as e:
            self.logger.error(f"查询技师排班失败: {e}")
            return []
    
    async def create_appointment(self, customer_name: str, customer_contact: str, 
                               technician_id: int, scheduled_time: str, 
                               additional_info: Optional[str] = None) -> Dict[str, Any]:
        """
        创建预约
        
        Args:
            customer_name: 客户姓名
            customer_contact: 客户联系方式
            technician_id: 技师ID
            scheduled_time: 预约时间 (YYYY-MM-DD HH:MM:SS)
            additional_info: 附加信息
            
        Returns:
            创建结果
        """
        # 注意：这里应该使用POST请求，但由于API限制，暂时使用GET
        params = {
            "action": "create",
            "customer_name": customer_name,
            "customer_contact": customer_contact,
            "technician_id": technician_id,
            "scheduled_time": scheduled_time
        }
        if additional_info:
            params["additional_info"] = additional_info
        
        try:
            result = await self._make_request("/appointments", params)
            return {
                "success": True,
                "data": result,
                "message": "预约创建成功"
            }
        except Exception as e:
            self.logger.error(f"创建预约失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "预约创建失败"
            }
    
    async def get_appointment_details(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        """
        获取预约详情
        
        Args:
            appointment_id: 预约ID
            
        Returns:
            预约详情
        """
        params = {
            "action": "get_details",
            "appointment_id": appointment_id
        }
        
        try:
            result = await self._make_request("/appointments", params)
            return result.get("appointment")
        except Exception as e:
            self.logger.error(f"获取预约详情失败: {e}")
            return None
    
    async def get_stores(self) -> List[Dict[str, Any]]:
        """
        获取门店列表
        
        Returns:
            门店列表
        """
        params = {}
        
        try:
            result = await self._make_request("/stores", params)
            # 如果返回的是数组，直接返回；如果是对象包含stores字段，则返回stores
            if isinstance(result, list):
                return result
            return result.get("stores", [])
        except Exception as e:
            self.logger.error(f"获取门店列表失败: {e}")
            return []