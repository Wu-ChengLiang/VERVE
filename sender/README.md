# AI邮件发送测试

这个目录包含了调用 `aiclient` 模块生成邮件内容并发送给指定邮箱的测试代码。

## 文件说明

- `config.toml` - 邮件发送配置文件
- `email_sender.py` - 原始的邮件发送器（依赖app模块）
- `test_ai_email.py` - 完整的AI邮件发送测试脚本
- `simple_test.py` - 简化版测试脚本，专门给 19357509506@163.com 发送一封邮件
- `requirements.txt` - Python依赖包列表

## 使用方法

### 1. 安装依赖

```bash
pip install toml
```

### 2. 配置邮箱设置

确保 `config.toml` 文件中的邮箱配置正确：

```toml
[email]
sender_email = "your_email@163.com"     # 发件邮箱
smtp_password = "your_smtp_password"    # SMTP密码/授权码
smtp_server = "smtp.163.com"            # SMTP服务器
server_port = 25                        # 端口号 (25/465/587)
```

### 3. 运行测试

#### 简单测试（推荐）
```bash
cd sender
python simple_test.py
```

这会给 `19357509506@163.com` 发送一封AI生成的测试邮件。

#### 完整测试
```bash
cd sender
python test_ai_email.py
```

这会发送多封不同主题的AI生成邮件进行全面测试。

## 功能特点

✅ **AI内容生成**: 使用 `aiclient` 模块调用AI服务生成专业的邮件内容
✅ **自动解析**: 智能解析AI回复，提取邮件主题和正文
✅ **完整类型注解**: 所有函数都有完备的类型注解
✅ **错误处理**: 包含完善的异常处理和日志输出
✅ **多端口支持**: 支持25/465/587端口的SMTP连接
✅ **中文友好**: 完全支持中文邮件内容

## 注意事项

1. 确保 `aiclient` 模块的配置正确，AI服务可正常调用
2. 确保发件邮箱已开启SMTP服务并获取了正确的授权码
3. 测试时请注意邮件发送频率，避免被服务商限制
4. 建议先使用 `simple_test.py` 进行单次测试，确认功能正常后再运行完整测试

## TODO

- [x] 创建基础的AI邮件发送功能
- [x] 添加完整的类型注解
- [x] 实现错误处理和日志
- [x] 支持多种SMTP端口
- [ ] 添加邮件模板功能
- [ ] 支持HTML格式邮件
- [ ] 添加邮件发送历史记录 