# AI客户端API函数调用功能

## 概述

AI客户端现在支持通过函数调用（Function Calling）来访问外部API，获取实时的门店、技师和预约信息。这使得AI能够回答客户关于预约、技师查询等实时问题。

## API端点

- **基础URL**: `http://emagen.323424.xyz/api/`
- **健康检查**: `http://emagen.323424.xyz/api/health`

### 可用端点

1. **门店列表**: `/functions/stores`
2. **技师列表**: `/functions/therapists`  
3. **预约管理**: `/functions/appointments`

## 支持的函数

### 1. 查询可用预约时间 (query_available_appointments)

查询指定日期的可用预约时间段。

**参数**:
- `target_date` (必需): 查询日期，格式 YYYY-MM-DD
- `technician_id` (可选): 技师ID，如果指定则只查询该技师的可用时间

### 2. 搜索技师 (search_technicians)

搜索技师信息，支持按姓名或技能搜索。

**参数**:
- `name` (可选): 技师姓名，支持模糊搜索
- `skill` (可选): 技师技能或专长

### 3. 查询技师排班 (query_technician_schedule)

查询指定技师在某个时间段内的排班情况。

**参数**:
- `technician_id` (必需): 技师ID
- `start_date` (必需): 开始日期，格式 YYYY-MM-DD
- `end_date` (必需): 结束日期，格式 YYYY-MM-DD

### 4. 创建预约 (create_appointment)

创建新的预约记录。

**参数**:
- `customer_name` (必需): 客户姓名
- `customer_contact` (必需): 客户联系方式
- `technician_id` (必需): 技师ID
- `scheduled_time` (必需): 预约时间，格式 YYYY-MM-DD HH:MM:SS
- `additional_info` (可选): 附加信息或备注

### 5. 获取预约详情 (get_appointment_details)

获取预约详情信息。

**参数**:
- `appointment_id` (必需): 预约ID

### 6. 获取门店列表 (get_stores)

获取所有门店信息（在DatabaseAPIService中实现，但未在base.py中定义）。

## 实现架构

```
┌─────────────────┐
│   AI Client     │
└────────┬────────┘
         │
┌────────▼────────┐
│  OpenAI Adapter │ (支持函数调用)
└────────┬────────┘
         │
┌────────▼────────┐
│DatabaseAPIService│
└────────┬────────┘
         │
┌────────▼────────┐
│  External API   │
│ (emagen.323424) │
└─────────────────┘
```

## 使用示例

### 1. 基础使用

```python
from aiclient.client import AIClient
from aiclient.config import AIConfig

# 初始化客户端
config = AIConfig()
client = AIClient(config)

# 询问预约信息
response = await client.generate_customer_service_reply("明天有什么可用的预约时间？")
print(response.content)
```

### 2. 直接使用DatabaseAPIService

```python
from aiclient.database_service import DatabaseAPIService

db_service = DatabaseAPIService()

# 获取门店列表
stores = await db_service.get_stores()

# 搜索技师
technicians = await db_service.search_technicians(name="张三")

# 查询可用预约
appointments = await db_service.query_available_appointments("2025-06-15")
```

## 测试

项目包含了完整的测试套件：

1. **单元测试** (`tests/test_api_function_calls.py`): 测试API调用的基本功能
2. **集成测试** (`tests/test_database_service_integration.py`): 测试与真实API的集成
3. **适配器测试** (`tests/test_openai_adapter_functions.py`): 测试OpenAI适配器的函数调用功能

运行测试：

```bash
# 运行所有函数调用相关测试
python -m pytest tests/test_api_function_calls.py tests/test_openai_adapter_functions.py -v

# 运行集成测试
python -m pytest tests/test_database_service_integration.py -v
```

## 注意事项

1. **API限制**: 当前API仅支持GET请求，创建预约等操作在实际环境中应使用POST请求
2. **错误处理**: 所有API调用都包含了错误处理，失败时会返回空列表或错误信息
3. **超时设置**: 默认超时时间为30秒，可在配置中调整
4. **并发支持**: DatabaseAPIService支持并发请求，可同时发送多个API调用

## 配置要求

确保在`.env`文件中配置了OpenAI API密钥：

```env
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-4o-mini
```

只有OpenAI适配器支持函数调用功能，其他适配器（如Zhipu、DeepSeek）暂不支持。