# 预约系统API接口同步更新

## 📋 更新概述

已将所有Function Call接口与最新的预约系统API规范完全同步，确保系统能够正确调用新的REST API端点。

## 🔄 主要变更

### 1. **API参数更新**

| 旧参数名 | 新参数名 | 说明 |
|---------|---------|------|
| `customer_contact` | `customer_phone` | 客户联系方式改为专门的电话字段 |
| `technician_id` | `therapist_id` | 统一使用therapist_id |
| `scheduled_time` | `appointment_date` + `appointment_time` | 分离日期和时间字段 |
| `additional_info` | `notes` | 备注字段重命名 |

### 2. **新增必填参数**

- **`username`**: 所有预约操作都需要用户名作为身份标识
- **`customer_phone`**: 客户电话号码（格式：13812345678）
- **`appointment_date`**: 预约日期（格式：YYYY-MM-DD）
- **`appointment_time`**: 预约时间（格式：HH:MM）

### 3. **HTTP方法更新**

| 功能 | 旧方式 | 新方式 |
|-----|-------|-------|
| 创建预约 | `GET /appointments?action=create` | `POST /appointments` |
| 查看预约 | `GET /appointments?action=get_details` | `GET /appointments/{id}` |
| 用户预约列表 | - | `GET /appointments/user/{username}` |
| 取消预约 | - | `DELETE /appointments/{id}?username={username}` |
| 技师可用时间 | - | `GET /appointments/availability/{therapist_id}?date={date}` |

## 🛠️ 更新的组件

### 1. **数据库服务层** (`aiclient/database_service.py`)

✅ **新增方法**:
- `create_appointment()` - 使用新的参数格式
- `get_user_appointments()` - 查询用户预约列表  
- `cancel_appointment()` - 取消预约
- `query_therapist_availability()` - 查询技师可用时间
- `search_therapists()` - 支持多种搜索方式

✅ **HTTP方法支持**:
- `_make_post_request()` - POST请求
- `_make_delete_request()` - DELETE请求
- `_make_get_request()` - GET请求（重命名）

### 2. **Function Call工具定义** (`aiclient/adapters/base.py`)

✅ **更新的工具**:
- `create_appointment` - 新增username等必填参数
- `get_user_appointments` - 查看用户预约列表
- `cancel_appointment` - 取消预约功能
- `query_therapist_availability` - 查询技师可用时间
- `search_therapists` - 支持按门店、技师名、服务类型搜索

✅ **系统提示词更新**:
- 更新了工具列表和说明
- 明确了username的重要性

### 3. **OpenAI适配器** (`aiclient/adapters/openai_adapter.py`)

✅ **Function Call执行逻辑**:
- 更新所有函数调用以匹配新API
- 正确传递新的参数格式
- 移除旧的兼容性方法

## 📊 支持的API操作

### ✅ 完整预约流程

1. **查询技师** 
   ```python
   search_therapists(store_name="莘庄店")
   search_therapists(therapist_name="陈老师") 
   search_therapists(service_type="艾灸")
   ```

2. **检查可用时间**
   ```python
   query_therapist_availability(therapist_id=1, date="2024-01-25")
   ```

3. **创建预约**
   ```python
   create_appointment(
       username="USER123",
       customer_name="张先生",
       customer_phone="13812345678",
       therapist_id=1,
       appointment_date="2024-01-25",
       appointment_time="14:00",
       service_type="经络疏通",
       notes="首次预约"
   )
   ```

4. **管理预约**
   ```python
   get_user_appointments(username="USER123")
   get_appointment_details(appointment_id=123)
   cancel_appointment(appointment_id=123, username="USER123")
   ```

## 🧪 测试验证

创建了 `test_new_appointment_api.py` 来验证：

- ✅ 所有新API端点的连通性
- ✅ Function Call参数映射正确性  
- ✅ AI集成和自动调用功能
- ✅ 错误处理和异常情况

## 🚀 使用示例

### 客户对话示例

**客户**: "我想预约明天下午2点的按摩"

**AI系统**:
1. 调用 `search_therapists()` 查找技师
2. 调用 `query_therapist_availability()` 检查可用时间
3. 收集客户信息（姓名、电话）
4. 调用 `create_appointment()` 创建预约

### 完整API调用示例

```bash
# 1. 查看莘庄店技师
curl "http://emagen.323424.xyz/api/therapists?action=query_schedule&store_name=莘庄店"

# 2. 创建预约  
curl -X POST http://emagen.323424.xyz/api/appointments \
  -H "Content-Type: application/json" \
  -d '{
    "username": "USER123",
    "customer_name": "张先生", 
    "customer_phone": "13812345678",
    "therapist_id": 1,
    "appointment_date": "2024-01-26",
    "appointment_time": "14:00",
    "service_type": "经络疏通"
  }'

# 3. 查看我的预约
curl http://emagen.323424.xyz/api/appointments/user/USER123
```

## ✅ 验证清单

- [x] 删除所有旧的兼容性方法
- [x] 更新所有参数名称和格式
- [x] 实现完整的REST API调用
- [x] 更新Function Call工具定义  
- [x] 更新系统提示词
- [x] 创建测试验证脚本
- [x] 确保username参数在所有操作中正确传递

## 🎯 关键改进

1. **完全REST化**: 使用标准HTTP方法（GET/POST/DELETE）
2. **参数标准化**: 统一参数命名和格式规范
3. **身份验证**: 所有操作都需要username身份标识
4. **类型安全**: 完备的类型注解和参数验证
5. **错误处理**: 改进的错误处理和日志记录

现在系统已完全与您的新预约API接口同步，所有Function Call都能正确工作！ 