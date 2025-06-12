## 项目网页元素读取机制分析

### 核心架构

这个项目使用 浏览器扩展 + WebSocket通信 的架构来读取网页元素：

网页平台 ←→ 浏览器扩展(Content Script) ←→ WebSocket ←→ app后端 ←→ AI模型

```javascript
// 核心监听机制
class PlatformIntegration {
  observeMessages() {
    // 使用MutationObserver监听DOM变化
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        mutation.addedNodes.forEach((node) => {
          if (this.isNewMessage(node)) {
            this.handleNewMessage(node); // 处理新消息
          }
        });
      });
    });
    
    // 监听消息容器
    observer.observe(messageContainer, {
      childList: true,
      subtree: true
    });
  }
  
  extractMessageData(messageElement) {
    // 提取消息内容
    const content = messageElement.querySelector('.message-content')?.textContent;
    const senderId = messageElement.getAttribute('data-user-id');
    return { content, senderId, timestamp: Date.now() };
  }
}
```