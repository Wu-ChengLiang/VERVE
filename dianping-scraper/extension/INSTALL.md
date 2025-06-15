# 大众点评数据提取器 - 浏览器扩展安装指南

## 📋 系统要求

- Chrome 浏览器 88+ 或 Edge 浏览器 88+
- 支持Manifest V3的现代浏览器
- Python WebSocket服务器运行在 localhost:8767

## 🚀 安装步骤

### 1. 准备扩展文件

确保所有扩展文件在 `extension` 目录中：

```
extension/
├── manifest.json       # 扩展配置文件
├── background.js       # 后台脚本
├── content.js          # 内容脚本
├── websocket.js        # WebSocket通信模块
├── popup.html          # 弹出窗口HTML
├── popup.css           # 弹出窗口样式
├── popup.js            # 弹出窗口脚本
├── test_extension.js   # 扩展测试脚本
├── icons/              # 图标目录
│   └── icon.svg        # 扩展图标
└── INSTALL.md          # 本安装指南
```

### 2. 启动WebSocket服务器

在开始使用扩展前，必须先启动Python WebSocket服务器：

```bash
# 进入后端目录
cd ../backend

# 启动服务器
python server.py
```

服务器启动后会显示：
```
[START] 启动大众点评WebSocket服务器...
[SERVER] 监听地址: localhost:8767
[SUCCESS] 服务器启动成功! 等待连接...
[WEBSOCKET] 浏览器扩展可以连接到: ws://localhost:8767
```

### 3. 在Chrome中加载扩展

1. **打开扩展管理页面**
   - 在Chrome地址栏输入: `chrome://extensions/`
   - 或者: 菜单 → 更多工具 → 扩展程序

2. **启用开发者模式**
   - 点击页面右上角的"开发者模式"开关

3. **加载扩展**
   - 点击"加载已解压的扩展程序"按钮
   - 选择 `extension` 目录
   - 点击"选择文件夹"

4. **验证安装**
   - 扩展应该出现在扩展列表中
   - 扩展名称: "大众点评数据提取器"
   - 版本: 1.0.0
   - 状态: 已启用

## 🧪 功能测试

### 1. 基础功能测试

1. **打开大众点评网站**
   ```
   https://g.dianping.com/dzim-main-pc/index.html#/
   ```

2. **检查扩展状态**
   - 点击浏览器工具栏中的扩展图标
   - 弹出窗口应显示连接状态
   - WebSocket状态应为"已连接"

3. **测试数据提取**
   - 在弹出窗口中点击"启动提取"
   - 浏览大众点评页面（餐厅列表、详情页等）
   - 观察控制台日志和服务器日志

### 2. 开发者工具测试

1. **打开开发者工具**
   - 按 F12 或右键 → 检查

2. **查看控制台日志**
   ```javascript
   // 应该看到类似的日志
   [DianpingExtractor] Content Script 加载完成
   [WebSocket] 初始化WebSocket管理器...
   [WebSocket] 连接成功!
   [DianpingExtractor] WebSocket管理器已就绪
   ```

3. **测试扩展API**
   ```javascript
   // 在控制台中运行
   console.log(window.DianpingDataExtractor);
   console.log(window.DianpingWebSocketManager);
   ```

### 3. 自动化测试

运行内置的测试脚本：

```javascript
// 在大众点评页面的控制台中运行
const script = document.createElement('script');
script.src = chrome.runtime.getURL('test_extension.js');
document.head.appendChild(script);
```

## 🔧 故障排除

### 常见问题

1. **扩展无法加载**
   - 检查manifest.json语法是否正确
   - 确保所有必需文件都存在
   - 查看Chrome扩展页面的错误信息

2. **WebSocket连接失败**
   - 确认Python服务器正在运行
   - 检查防火墙设置
   - 验证端口8767是否被占用

3. **数据提取不工作**
   - 确认在正确的大众点评页面
   - 检查页面元素选择器是否有效
   - 查看控制台错误日志

4. **弹出窗口不显示**
   - 检查popup.html和相关CSS/JS文件
   - 确认图标文件存在
   - 重新加载扩展

### 调试技巧

1. **启用详细日志**
   ```javascript
   // 在控制台中设置
   localStorage.setItem('debug', 'true');
   ```

2. **检查存储数据**
   ```javascript
   // 查看提取的数据
   chrome.storage.local.get(['extractedData'], console.log);
   ```

3. **手动测试WebSocket**
   ```javascript
   // 发送测试消息
   window.DianpingWebSocketManager.ping();
   ```

## 📊 性能监控

### 监控指标

- **连接状态**: WebSocket连接是否稳定
- **数据提取量**: 成功提取的数据条目数
- **错误率**: 提取过程中的错误次数
- **内存使用**: 扩展的内存占用情况

### 日志分析

服务器端日志位置: `../backend/dianping_scraper.log`

客户端日志: 浏览器开发者工具控制台

## 🔄 更新扩展

1. 修改扩展文件后
2. 在扩展管理页面点击"重新加载"按钮
3. 或者完全移除后重新加载

## ⚠️ 注意事项

1. **隐私保护**: 扩展只在大众点评网站运行
2. **数据安全**: 提取的数据仅存储在本地
3. **使用限制**: 请遵守大众点评网站的使用条款
4. **性能影响**: 大量数据提取可能影响页面性能

## 📞 技术支持

如遇到问题，请检查：

1. 控制台错误日志
2. 扩展错误页面
3. WebSocket服务器日志
4. 网络连接状态

---

**版本**: 1.0.0  
**更新日期**: 2025-06-12  
**兼容性**: Chrome 88+, Edge 88+ 