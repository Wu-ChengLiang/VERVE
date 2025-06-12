/**
 * WebSocket通信管理器
 * 负责与Python后端服务器的连接和数据传输
 */

class WebSocketManager {
    constructor() {
        this.ws = null;
        this.serverUrl = 'ws://localhost:8765';
        this.isConnected = false;
        this.reconnectInterval = 5000; // 5秒重连间隔
        this.maxReconnectAttempts = 10;
        this.reconnectAttempts = 0;
        this.messageQueue = []; // 消息队列，连接断开时暂存消息
        
        // 绑定方法上下文
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.sendMessage = this.sendMessage.bind(this);
        this.handleMessage = this.handleMessage.bind(this);
        this.handleError = this.handleError.bind(this);
        this.handleClose = this.handleClose.bind(this);
        
        this.init();
    }
    
    /**
     * 初始化WebSocket连接
     */
    init() {
        console.log('[WebSocket] 初始化WebSocket管理器...');
        this.connect();
    }
    
    /**
     * 连接到WebSocket服务器
     */
    connect() {
        if (this.isConnected || (this.ws && this.ws.readyState === WebSocket.CONNECTING)) {
            console.log('[WebSocket] 已连接或正在连接中...');
            return;
        }
        
        try {
            console.log(`[WebSocket] 尝试连接到: ${this.serverUrl}`);
            this.ws = new WebSocket(this.serverUrl);
            
            this.ws.onopen = () => {
                console.log('[WebSocket] 连接成功!');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                
                // 发送欢迎消息
                // this.sendPageInfo(); // 在连接时发送页面信息
                
                // 处理消息队列
                this.processMessageQueue();
                
                // 通知content script连接成功
                this.notifyConnectionStatus(true);
            };
            
            this.ws.onmessage = this.handleMessage;
            this.ws.onerror = this.handleError;
            this.ws.onclose = this.handleClose;
            
        } catch (error) {
            console.error('[WebSocket] 连接创建失败:', error);
            this.scheduleReconnect();
        }
    }
    
    /**
     * 处理接收到的消息
     */
    handleMessage(event) {
        try {
            const data = JSON.parse(event.data);
            console.log('[WebSocket] 收到服务器消息:', data);
            
            // 根据消息类型处理
            switch (data.type) {
                case 'welcome':
                    console.log('[WebSocket] 收到欢迎消息:', data.message);
                    break;
                case 'pong':
                    console.log('[WebSocket] 收到pong响应');
                    break;
                case 'data_received':
                    console.log('[WebSocket] 数据已被服务器接收:', data.data_id);
                    break;
                case 'page_info_received':
                    console.log('[WebSocket] 页面信息已被服务器接收');
                    break;
                case 'error':
                    console.error('[WebSocket] 服务器错误:', data.message);
                    break;
                default:
                    console.log('[WebSocket] 未知消息类型:', data.type);
            }
            
        } catch (error) {
            console.error('[WebSocket] 消息解析失败:', error);
        }
    }
    
    /**
     * 处理WebSocket错误
     */
    handleError(error) {
        console.error('[WebSocket] 连接错误:', error);
        this.isConnected = false;
        this.notifyConnectionStatus(false);
    }
    
    /**
     * 处理WebSocket连接关闭
     */
    handleClose(event) {
        console.log('[WebSocket] 连接关闭:', event.code, event.reason);
        this.isConnected = false;
        this.notifyConnectionStatus(false);
        
        // 如果不是主动关闭，则尝试重连
        if (event.code !== 1000) {
            this.scheduleReconnect();
        }
    }
    
    /**
     * 安排重连
     */
    scheduleReconnect() {
        if (this.reconnectAttempts >= this.maxReconnectAttempts) {
            console.error('[WebSocket] 达到最大重连次数，停止重连');
            return;
        }
        
        this.reconnectAttempts++;
        console.log(`[WebSocket] ${this.reconnectInterval/1000}秒后尝试第${this.reconnectAttempts}次重连...`);
        
        setTimeout(() => {
            this.connect();
        }, this.reconnectInterval);
    }
    
    /**
     * 发送消息到服务器
     */
    sendMessage(message) {
        if (!this.isConnected || !this.ws || this.ws.readyState !== WebSocket.OPEN) {
            console.log('[WebSocket] 连接未就绪，消息加入队列:', message);
            this.messageQueue.push(message);
            return false;
        }
        
        try {
            const messageStr = JSON.stringify(message);
            this.ws.send(messageStr);
            console.log('[WebSocket] 消息发送成功:', message.type);
            return true;
        } catch (error) {
            console.error('[WebSocket] 消息发送失败:', error);
            this.messageQueue.push(message);
            return false;
        }
    }
    
    /**
     * 处理消息队列
     */
    processMessageQueue() {
        while (this.messageQueue.length > 0 && this.isConnected) {
            const message = this.messageQueue.shift();
            this.sendMessage(message);
        }
    }
    
    /**
     * 发送页面信息
     */
    sendPageInfo() {
        // 收集所有元素的详细信息
        const allElements = document.querySelectorAll('*');
        const elementsInfo = [];
        
        allElements.forEach((element, index) => {
            try {
                const elementInfo = {
                    index: index,
                    tagName: element.tagName.toLowerCase(),
                    id: element.id || '',
                    className: element.className || '',
                    textContent: element.textContent ? element.textContent.trim().substring(0, 100) : '', // 限制文本长度
                    attributes: {},
                    position: {
                        offsetTop: element.offsetTop,
                        offsetLeft: element.offsetLeft,
                        offsetWidth: element.offsetWidth,
                        offsetHeight: element.offsetHeight
                    }
                };
                
                // 收集主要属性
                if (element.attributes) {
                    for (let attr of element.attributes) {
                        if (['id', 'class', 'src', 'href', 'alt', 'title', 'data-*'].some(key => 
                            attr.name === key || attr.name.startsWith('data-'))) {
                            elementInfo.attributes[attr.name] = attr.value;
                        }
                    }
                }
                
                elementsInfo.push(elementInfo);
            } catch (error) {
                console.warn(`[WebSocket] 处理元素 ${index} 时出错:`, error);
            }
        });
        
        const pageInfo = {
            type: 'page_info',
            page_info: {
                title: document.title,
                url: window.location.href,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent,
                element_count: allElements.length,
                elements: elementsInfo // 添加所有元素的详细信息
            }
        };
        
        this.sendMessage(pageInfo);
    }
    
    /**
     * 发送大众点评数据
     */
    sendDianpingData(data) {
        const message = {
            type: 'dianping_data',
            url: window.location.href,
            content: data,
            timestamp: new Date().toISOString()
        };
        
        this.sendMessage(message);
    }
    
    /**
     * 发送ping消息
     */
    ping() {
        const pingMessage = {
            type: 'ping',
            timestamp: new Date().toISOString()
        };
        
        this.sendMessage(pingMessage);
    }
    
    /**
     * 通知连接状态
     */
    notifyConnectionStatus(connected) {
        // 向content script发送连接状态
        const event = new CustomEvent('websocket-status', {
            detail: { connected, timestamp: new Date().toISOString() }
        });
        document.dispatchEvent(event);
    }
    
    /**
     * 断开连接
     */
    disconnect() {
        console.log('[WebSocket] 主动断开连接');
        if (this.ws) {
            this.ws.close(1000, '主动断开');
            this.ws = null;
        }
        this.isConnected = false;
    }
    
    /**
     * 获取连接状态
     */
    getStatus() {
        return {
            connected: this.isConnected,
            readyState: this.ws ? this.ws.readyState : -1,
            serverUrl: this.serverUrl,
            reconnectAttempts: this.reconnectAttempts,
            messageQueueLength: this.messageQueue.length
        };
    }
}

// 创建全局WebSocket管理器实例
window.DianpingWebSocketManager = new WebSocketManager();

// 导出给其他脚本使用
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WebSocketManager;
} 