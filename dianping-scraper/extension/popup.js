/**
 * 大众点评数据提取器 - 弹出窗口脚本
 * 处理用户界面交互和状态管理
 */

class PopupManager {
    constructor() {
        this.isActive = false;
        this.currentTab = null;
        this.stats = {
            extracted: 0,
            errors: 0,
            uptime: 0
        };
        
        this.init();
    }
    
    /**
     * 初始化弹出窗口
     */
    init() {
        console.log('[Popup] 初始化弹出窗口...');
        
        // 绑定事件监听器
        this.bindEventListeners();
        
        // 获取当前标签页
        this.getCurrentTab();
        
        // 加载状态
        this.loadStatus();
        
        // 定期更新状态
        this.startStatusUpdate();
    }
    
    /**
     * 绑定事件监听器
     */
    bindEventListeners() {
        // 控制按钮
        document.getElementById('toggleExtraction').addEventListener('click', () => {
            this.toggleExtraction();
        });
        
        document.getElementById('testConnection').addEventListener('click', () => {
            this.testConnection();
        });
        
        document.getElementById('clearData').addEventListener('click', () => {
            this.clearData();
        });
        
        // 快速操作
        document.getElementById('openDianping').addEventListener('click', () => {
            this.openDianping();
        });
        
        document.getElementById('viewData').addEventListener('click', () => {
            this.viewData();
        });
        
        document.getElementById('openSettings').addEventListener('click', () => {
            this.openSettings();
        });
    }
    
    /**
     * 获取当前标签页
     */
    async getCurrentTab() {
        try {
            const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
            this.currentTab = tab;
            
            // 更新当前页面显示
            const pageElement = document.getElementById('currentPage');
            if (tab.url && tab.url.includes('dianping.com')) {
                pageElement.textContent = '大众点评';
                pageElement.className = 'value connected';
            } else {
                pageElement.textContent = '非大众点评页面';
                pageElement.className = 'value warning';
            }
            
            // 检查是否在大众点评页面
            this.checkDianpingPage();
            
        } catch (error) {
            console.error('[Popup] 获取当前标签页失败:', error);
        }
    }
    
    /**
     * 检查是否在大众点评页面
     */
    checkDianpingPage() {
        if (this.currentTab && this.currentTab.url && this.currentTab.url.includes('dianping.com')) {
            // 在大众点评页面，启用相关功能
            document.getElementById('toggleExtraction').disabled = false;
            document.getElementById('testConnection').disabled = false;
        } else {
            // 不在大众点评页面，禁用部分功能
            document.getElementById('toggleExtraction').disabled = true;
            this.updateExtractionStatus('未在大众点评页面', 'warning');
        }
    }
    
    /**
     * 加载状态
     */
    async loadStatus() {
        try {
            // 获取扩展状态
            const response = await this.sendMessageToBackground({
                type: 'get_extension_state'
            });
            
            if (response && response.state) {
                this.updateUIFromState(response.state);
            }
            
            // 获取存储的数据统计
            this.loadDataStats();
            
            // 检查WebSocket连接状态
            this.checkWebSocketStatus();
            
        } catch (error) {
            console.error('[Popup] 加载状态失败:', error);
            this.showMessage('加载状态失败', 'error');
        }
    }
    
    /**
     * 加载数据统计
     */
    async loadDataStats() {
        try {
            const result = await chrome.storage.local.get(['extractedData']);
            const extractedData = result.extractedData || [];
            
            // 更新统计显示
            document.getElementById('extractedCount').textContent = extractedData.length;
            
            // 计算错误数（假设有错误记录）
            // 这里可以根据实际需求添加错误统计逻辑
            
        } catch (error) {
            console.error('[Popup] 加载数据统计失败:', error);
        }
    }
    
    /**
     * 检查WebSocket连接状态
     */
    async checkWebSocketStatus() {
        if (!this.currentTab || !this.currentTab.url.includes('dianping.com')) {
            this.updateWebSocketStatus('未连接', 'error');
            return;
        }
        
        try {
            // 向content script请求WebSocket状态
            const response = await chrome.tabs.sendMessage(this.currentTab.id, {
                type: 'get_websocket_status'
            });
            
            if (response && response.status) {
                const { connected } = response.status;
                this.updateWebSocketStatus(
                    connected ? '已连接' : '未连接',
                    connected ? 'connected' : 'error'
                );
            } else {
                this.updateWebSocketStatus('检查中...', 'warning');
            }
            
        } catch (error) {
            console.warn('[Popup] 检查WebSocket状态失败:', error);
            this.updateWebSocketStatus('无法检查', 'error');
        }
    }
    
    /**
     * 更新WebSocket状态显示
     */
    updateWebSocketStatus(text, className) {
        const statusElement = document.getElementById('websocketStatus');
        const dotElement = document.getElementById('statusDot');
        const textElement = document.getElementById('statusText');
        
        statusElement.textContent = text;
        statusElement.className = `value ${className}`;
        
        dotElement.className = `status-dot ${className}`;
        textElement.textContent = text;
    }
    
    /**
     * 更新提取状态显示
     */
    updateExtractionStatus(text, className) {
        const statusElement = document.getElementById('extractionStatus');
        statusElement.textContent = text;
        statusElement.className = `value ${className}`;
    }
    
    /**
     * 从状态更新UI
     */
    updateUIFromState(state) {
        this.isActive = state.isActive;
        
        // 更新切换按钮
        const toggleBtn = document.getElementById('toggleExtraction');
        const toggleText = document.getElementById('toggleText');
        
        if (this.isActive) {
            toggleBtn.className = 'btn btn-secondary';
            toggleText.textContent = '停止提取';
            this.updateExtractionStatus('运行中', 'connected');
        } else {
            toggleBtn.className = 'btn btn-primary';
            toggleText.textContent = '启动提取';
            this.updateExtractionStatus('未激活', 'warning');
        }
        
        // 更新统计信息
        if (state.dataCollected !== undefined) {
            document.getElementById('extractedCount').textContent = state.dataCollected;
        }
        
        if (state.errors !== undefined) {
            document.getElementById('errorCount').textContent = state.errors;
        }
        
        // 更新运行时间
        if (state.lastActivity) {
            const uptime = Date.now() - state.lastActivity;
            this.updateUptimeDisplay(uptime);
        }
    }
    
    /**
     * 更新运行时间显示
     */
    updateUptimeDisplay(uptime) {
        const uptimeElement = document.getElementById('uptimeDisplay');
        
        if (uptime < 60000) {
            uptimeElement.textContent = '< 1分钟';
        } else if (uptime < 3600000) {
            const minutes = Math.floor(uptime / 60000);
            uptimeElement.textContent = `${minutes}分钟`;
        } else {
            const hours = Math.floor(uptime / 3600000);
            const minutes = Math.floor((uptime % 3600000) / 60000);
            uptimeElement.textContent = `${hours}小时${minutes}分钟`;
        }
    }
    
    /**
     * 切换数据提取状态
     */
    async toggleExtraction() {
        if (!this.currentTab || !this.currentTab.url.includes('dianping.com')) {
            this.showMessage('请在大众点评页面使用此功能', 'warning');
            return;
        }
        
        try {
            const response = await chrome.tabs.sendMessage(this.currentTab.id, {
                type: 'toggle_extraction',
                active: !this.isActive
            });
            
            if (response && response.success) {
                this.isActive = !this.isActive;
                this.updateUIFromState({ isActive: this.isActive });
                this.showMessage(
                    this.isActive ? '数据提取已启动' : '数据提取已停止',
                    'success'
                );
            } else {
                this.showMessage('操作失败，请重试', 'error');
            }
            
        } catch (error) {
            console.error('[Popup] 切换提取状态失败:', error);
            this.showMessage('操作失败', 'error');
        }
    }
    
    /**
     * 测试连接
     */
    async testConnection() {
        if (!this.currentTab || !this.currentTab.url.includes('dianping.com')) {
            this.showMessage('请在大众点评页面测试连接', 'warning');
            return;
        }
        
        try {
            this.showMessage('正在测试连接...', 'warning');
            
            const response = await chrome.tabs.sendMessage(this.currentTab.id, {
                type: 'test_websocket_connection'
            });
            
            if (response && response.success) {
                this.showMessage('连接测试成功！', 'success');
                this.updateWebSocketStatus('已连接', 'connected');
            } else {
                this.showMessage('连接测试失败', 'error');
                this.updateWebSocketStatus('连接失败', 'error');
            }
            
        } catch (error) {
            console.error('[Popup] 测试连接失败:', error);
            this.showMessage('连接测试失败', 'error');
        }
    }
    
    /**
     * 清除数据
     */
    async clearData() {
        if (!confirm('确定要清除所有提取的数据吗？此操作不可撤销。')) {
            return;
        }
        
        try {
            await chrome.storage.local.remove(['extractedData']);
            document.getElementById('extractedCount').textContent = '0';
            this.showMessage('数据已清除', 'success');
            
        } catch (error) {
            console.error('[Popup] 清除数据失败:', error);
            this.showMessage('清除数据失败', 'error');
        }
    }
    
    /**
     * 打开大众点评
     */
    openDianping() {
        chrome.tabs.create({
            url: 'https://g.dianping.com/dzim-main-pc/index.html#/'
        });
        window.close();
    }
    
    /**
     * 查看数据
     */
    async viewData() {
        try {
            const result = await chrome.storage.local.get(['extractedData']);
            const extractedData = result.extractedData || [];
            
            if (extractedData.length === 0) {
                this.showMessage('暂无数据', 'warning');
                return;
            }
            
            // 创建数据查看页面
            const dataUrl = chrome.runtime.getURL('data.html');
            chrome.tabs.create({ url: dataUrl });
            window.close();
            
        } catch (error) {
            console.error('[Popup] 查看数据失败:', error);
            this.showMessage('查看数据失败', 'error');
        }
    }
    
    /**
     * 打开设置
     */
    openSettings() {
        const settingsUrl = chrome.runtime.getURL('settings.html');
        chrome.tabs.create({ url: settingsUrl });
        window.close();
    }
    
    /**
     * 发送消息到后台脚本
     */
    async sendMessageToBackground(message) {
        return new Promise((resolve, reject) => {
            chrome.runtime.sendMessage(message, (response) => {
                if (chrome.runtime.lastError) {
                    reject(chrome.runtime.lastError);
                } else {
                    resolve(response);
                }
            });
        });
    }
    
    /**
     * 显示消息
     */
    showMessage(text, type = 'success') {
        const messageElement = document.getElementById('message');
        const messageTextElement = document.getElementById('messageText');
        
        messageTextElement.textContent = text;
        messageElement.className = `message ${type}`;
        messageElement.style.display = 'block';
        
        // 3秒后自动隐藏
        setTimeout(() => {
            messageElement.style.display = 'none';
        }, 3000);
    }
    
    /**
     * 开始状态更新
     */
    startStatusUpdate() {
        // 每5秒更新一次状态
        setInterval(() => {
            this.loadStatus();
        }, 5000);
        
        // 更新最后更新时间
        setInterval(() => {
            document.getElementById('lastUpdate').textContent = 
                new Date().toLocaleTimeString();
        }, 1000);
    }
}

// 等待DOM加载完成后初始化
document.addEventListener('DOMContentLoaded', () => {
    new PopupManager();
}); 