# 大众点评AI记忆功能实现项目

## 背景和动机

用户希望为大众点评爬虫系统添加AI记忆功能，使AI能够基于历史对话上下文生成更智能的客服回复，而不是每次都独立回复。

## 关键挑战和分析

### 核心问题
1. **无持久记忆**：当前AI回复系统每次都是独立的，没有对话历史
2. **聊天对象混淆**：不同聊天对象的消息会混在一起
3. **无聊天对象识别**：系统无法区分当前在与哪个客户对话
4. **临时数据存储**：只有server.py中的临时data_store，没有持久化

### 技术架构分析
- **前端**：Chrome扩展 (content.js) 负责消息提取
- **后端**：WebSocket服务器 (server.py) 处理数据和AI调用  
- **AI客户端**：统一的AI接口 (client.py + adapters/)

## 高层任务拆分

### Phase 1: 前端记忆基础设施 ✅
- [x] 添加记忆管理属性到DianpingDataExtractor
- [x] 实现联系人切换检测机制
- [x] 实现消息自动添加到记忆功能
- [x] 添加记忆清空和切换逻辑
- [x] 实现自动保存机制

### Phase 2: WebSocket协议扩展 ✅  
- [x] 定义chat_context_switch消息类型
- [x] 定义memory_update消息类型
- [x] 定义memory_save消息类型
- [x] 实现前端到后端的记忆同步

### Phase 3: 后端记忆处理 ✅
- [x] 扩展server.py添加memory_store
- [x] 实现handle_chat_context_switch方法
- [x] 实现handle_memory_update方法  
- [x] 实现handle_memory_save方法
- [x] 修改AI调用传递conversation_history

### Phase 4: AI客户端记忆集成 ✅
- [x] 修改client.py支持conversation_history参数
- [x] 扩展base.py适配器支持历史对话
- [x] 实现create_customer_service_prompt_with_history方法
- [x] 添加记忆管理方法到AIClient

## 项目状态看板

### 已完成 ✅
- [x] 前端记忆管理基础设施
- [x] WebSocket协议扩展
- [x] 后端记忆存储和处理
- [x] AI客户端记忆集成
- [x] 自动联系人检测机制
- [x] 消息重复发送问题修复
- [x] 记忆存储逻辑修复（处理None chatId）
- [x] AI提示词优化（更好利用对话历史）

### 当前状态 🔄
- [x] 核心记忆功能已实现并测试通过
- [x] 消息重复发送问题已解决
- [x] 记忆存储和检索功能正常工作
- [x] AI能接收到完整对话历史（20条记录）
- [x] 提示词已优化，强调上下文理解

### 待验证 🧪
- [ ] AI回复的上下文连贯性测试
- [ ] 多轮对话场景测试
- [ ] 联系人切换场景测试
- [ ] 长期使用稳定性测试

## 执行者反馈或请求帮助

### 最新修复 (2025-06-14 00:30)

**问题1: 消息重复发送** ✅ 已解决
- 原因：存在两个AI处理路径（handle_data_list + handle_memory_update）
- 解决：移除handle_data_list中的重复AI处理逻辑
- 结果：消息现在只通过memory_update路径处理一次

**问题2: 记忆存储失败** ✅ 已解决  
- 原因：chatId为None时，条件`if action == "add_message" and chat_id:`不满足
- 解决：使用默认值"default_chat"，移除chat_id检查条件
- 结果：记忆能正确存储到memory_store中

**问题3: AI上下文理解优化** ✅ 已完成
- 优化了create_customer_service_prompt_with_history的提示词
- 增加了对话历史使用量（10条→15条）
- 强调了上下文连贯性和意图理解
- 调整了temperature参数提高回复自然度

### 当前技术状态

**记忆系统架构**：
```
前端(content.js) → WebSocket → 后端(server.py) → AI客户端(client.py)
     ↓                ↓              ↓                    ↓
conversationMemory → memory_update → memory_store → conversation_history
```

**数据流**：
1. 前端提取消息 → addToMemory() → conversationMemory数组
2. 发送memory_update → 后端handle_memory_update() → memory_store[chatId]
3. 客户消息触发AI → 传递conversation_history → AI生成回复
4. AI回复 → 前端接收 → 添加到记忆 → 循环

**关键修复点**：
- ✅ 自动联系人检测：autoDetectCurrentContact()
- ✅ 默认chatId处理：chatId || "default_chat"  
- ✅ 重复处理消除：移除handle_data_list的AI调用
- ✅ 提示词优化：强调上下文理解和连贯性

### 测试建议

建议进行以下测试验证修复效果：
1. **基础对话测试**：发送几条消息，验证AI回复的上下文连贯性
2. **多轮对话测试**：进行复杂对话，检查AI是否能记住之前的内容
3. **简短消息测试**：发送"啊"、"好的"等简短消息，看AI是否能结合历史理解意图
4. **联系人切换测试**：切换不同联系人，验证记忆隔离是否正常

## 经验教训

### 调试技巧
1. **日志分层**：前端console.log + 后端logger.info + AI客户端调试日志
2. **数据流跟踪**：通过messageId和timestamp跟踪消息流转
3. **并行处理识别**：注意识别重复的处理路径
4. **默认值处理**：对于可能为None/null的关键字段要有默认值

### 架构设计
1. **最小改动原则**：在现有架构基础上扩展，避免大规模重构
2. **数据一致性**：确保前后端的数据结构和字段命名一致
3. **错误处理**：对于关键流程要有完善的错误处理和降级机制
4. **调试友好**：添加充分的调试日志，便于问题定位

### 技术要点
1. **WebSocket消息类型**：使用明确的消息类型区分不同功能
2. **记忆管理**：前端本地记忆 + 后端持久化存储的双重机制
3. **AI提示词**：针对对话历史场景优化提示词，强调上下文理解
4. **性能优化**：限制记忆长度，避免过长的历史记录影响性能
