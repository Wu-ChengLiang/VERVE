"""
数据库API服务
用于调用外部API获取门店、技师、预约等信息
"""

import logging
import aiohttp
from typing import Optional, List, Dict, Any
from datetime import datetime, date, time

logger = logging.getLogger(__name__)


class DatabaseAPIService:
    """数据库API服务类"""
    
    def __init__(self, base_url: str = "http://emagen.323424.xyz/api"):
        self.base_url = base_url
        self.logger = logger.getChild(self.__class__.__name__)
    
    async def _make_get_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送HTTP GET请求到API"""
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
            self.logger.error(f"GET请求失败 {url}: {e}")
            raise
    
    async def _make_post_request(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """发送HTTP POST请求到API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data) as response:
                    if response.status in [200, 201]:
                        result = await response.json()
                        return result
                    else:
                        error_text = await response.text()
                        self.logger.error(f"API错误 {response.status}: {error_text}")
                        raise Exception(f"API错误 {response.status}: {error_text}")
        except Exception as e:
            self.logger.error(f"POST请求失败 {url}: {e}")
            raise
    
    async def _make_delete_request(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """发送HTTP DELETE请求到API"""
        url = f"{self.base_url}{endpoint}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.delete(url, params=params) as response:
                    if response.status in [200, 204]:
                        if response.content_length and response.content_length > 0:
                            result = await response.json()
                            return result
                        else:
                            return {"success": True, "message": "删除成功"}
                    else:
                        error_text = await response.text()
                        self.logger.error(f"API错误 {response.status}: {error_text}")
                        raise Exception(f"API错误 {response.status}: {error_text}")
        except Exception as e:
            self.logger.error(f"DELETE请求失败 {url}: {e}")
            raise
    
    async def create_appointment(self, username: str, customer_name: str, customer_phone: str, 
                               therapist_id: int, appointment_date: str, appointment_time: str,
                               service_type: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        """
        创建预约
        
        Args:
            username: 用户名（必填）
            customer_name: 客户姓名
            customer_phone: 客户电话
            therapist_id: 技师ID
            appointment_date: 预约日期 (YYYY-MM-DD)
            appointment_time: 预约时间 (HH:MM)
            service_type: 服务类型（可选）
            notes: 备注信息（可选）
            
        Returns:
            创建结果
        """
        data = {
            "username": username,
            "customer_name": customer_name,
            "customer_phone": customer_phone,
            "therapist_id": therapist_id,
            "appointment_date": appointment_date,
            "appointment_time": appointment_time
        }
        
        if service_type:
            data["service_type"] = service_type
        if notes:
            data["notes"] = notes
        
        try:
            result = await self._make_post_request("/appointments", data)
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
    
    async def get_user_appointments(self, username: str) -> List[Dict[str, Any]]:
        """
        查看用户的预约列表
        
        Args:
            username: 用户名
            
        Returns:
            预约列表
        """
        try:
            result = await self._make_get_request(f"/appointments/user/{username}")
            if isinstance(result, list):
                return result
            return result.get("appointments", [])
        except Exception as e:
            self.logger.error(f"获取用户预约失败: {e}")
            return []
    
    async def get_appointment_details(self, appointment_id: int) -> Optional[Dict[str, Any]]:
        """
        获取预约详情
        
        Args:
            appointment_id: 预约ID
            
        Returns:
            预约详情
        """
        try:
            result = await self._make_get_request(f"/appointments/{appointment_id}")
            return result
        except Exception as e:
            self.logger.error(f"获取预约详情失败: {e}")
            return None
    
    async def cancel_appointment(self, appointment_id: int, username: str) -> Dict[str, Any]:
        """
        取消预约
        
        Args:
            appointment_id: 预约ID
            username: 用户名
            
        Returns:
            取消结果
        """
        params = {"username": username}
        
        try:
            result = await self._make_delete_request(f"/appointments/{appointment_id}", params)
            return {
                "success": True,
                "data": result,
                "message": "预约取消成功"
            }
        except Exception as e:
            self.logger.error(f"取消预约失败: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "预约取消失败"
            }
    
    async def query_therapist_availability(self, therapist_id: int, date: str) -> List[Dict[str, Any]]:
        """
        查询技师可用时间
        
        Args:
            therapist_id: 技师ID
            date: 日期 (YYYY-MM-DD)
            
        Returns:
            可用时间段列表
        """
        params = {"date": date}
        
        try:
            result = await self._make_get_request(f"/appointments/availability/{therapist_id}", params)
            if isinstance(result, list):
                return result
            return result.get("available_slots", [])
        except Exception as e:
            self.logger.error(f"查询技师可用时间失败: {e}")
            return []
    
    async def search_therapists(self, therapist_name: Optional[str] = None, 
                               store_name: Optional[str] = None,
                               service_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        查询技师（多种方式）
        
        Args:
            therapist_name: 技师名称（可选）
            store_name: 门店名称（可选）
            service_type: 服务类型（可选）
            
        Returns:
            技师列表
        """
        params = {"action": "query_schedule"}
        
        if therapist_name:
            params["therapist_name"] = therapist_name
        if store_name:
            params["store_name"] = store_name
        if service_type:
            params["service_type"] = service_type
        
        try:
            result = await self._make_get_request("/therapists", params)
            
            # 处理新的响应格式
            if isinstance(result, dict) and "therapists" in result:
                return result["therapists"]
            elif isinstance(result, list):
                return result
            return []
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
            result = await self._make_get_request("/therapists", params)
            return result.get("schedules", [])
        except Exception as e:
            self.logger.error(f"查询技师排班失败: {e}")
            return []
    
    async def get_stores(self) -> List[Dict[str, Any]]:
        """
        获取门店列表
        
        Returns:
            门店列表
        """
        try:
            result = await self._make_get_request("/stores")
            if isinstance(result, list):
                return result
            return result.get("stores", [])
        except Exception as e:
            self.logger.error(f"获取门店列表失败: {e}")
            return []