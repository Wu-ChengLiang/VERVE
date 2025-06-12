/**
 * 大众点评数据提取器 - Background Script
 * 处理扩展的后台逻辑、消息传递和事件管理
 */

console.log('[Background] 大众点评数据提取器后台脚本启动');

class ExtensionBackgroundManager {
    constructor() {
        this.activeConnections = new Map();
        this.extensionState = {
            isActive: true,
            lastActivity: Date.now(),
            dataCollected: 0,
            errors: 0
        };
        
        this.init();
    }
    
    /**
     * 初始化后台管理器
     */
    init() {
        console.log('[Background] 初始化后台管理器...');
        
        // 监听扩展安装事件
        chrome.runtime.onInstalled.addListener(this.handleInstalled.bind(this));
        
        // 监听标签页更新事件
        chrome.tabs.onUpdated.addListener(this.handleTabUpdated.bind(this));
        
        // 监听来自content script的消息
        chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
        
        // 监听扩展图标点击
        chrome.action.onClicked.addListener(this.handleActionClicked.bind(this));
        
        // 定期检查状态
        this.startStatusCheck();
    }
    
    /**
     * 处理扩展安装
     */
    handleInstalled(details) {
        console.log('[Background] 扩展安装/更新:', details.reason);
        
        if (details.reason === 'install') {
            console.log('[Background] 首次安装，设置默认配置');
            this.setDefaultSettings();
            this.showWelcomeNotification();
        } else if (details.reason === 'update') {
            console.log('[Background] 扩展更新完成');
        }
    }
    
    /**
     * 设置默认配置
     */
    setDefaultSettings() {
        const defaultSettings = {
            autoExtract: true,
            websocketUrl: 'ws://localhost:8765',
            extractionDelay: 2000,
            maxRetries: 3,
            debugMode: false
        };
        
        chrome.storage.sync.set(defaultSettings, () => {
            console.log('[Background] 默认设置已保存');
        });
    }
    
    /**
     * 显示欢迎通知
     */
    showWelcomeNotification() {
        // 检查notifications API是否可用
        if (chrome.notifications && chrome.notifications.create) {
            chrome.notifications.create({
                type: 'basic',
                iconUrl: 'icons/icon48.png',
                title: '大众点评数据提取器',
                message: '扩展安装成功！请访问大众点评网站开始数据提取。'
            }, (notificationId) => {
                if (chrome.runtime.lastError) {
                    console.warn('[Background] 通知创建失败:', chrome.runtime.lastError.message);
                } else {
                    console.log('[Background] 欢迎通知已显示:', notificationId);
                }
            });
        } else {
            console.warn('[Background] 通知API不可用，跳过欢迎通知');
        }
    }
    
    /**
     * 处理标签页更新
     */
    handleTabUpdated(tabId, changeInfo, tab) {
        // 只处理大众点评网站的标签页
        if (changeInfo.status === 'complete' && tab.url && this.isDianpingUrl(tab.url)) {
            console.log('[Background] 检测到大众点评页面:', tab.url);
            
            // 更新扩展图标状态
            this.updateBadge(tabId, 'active');
            
            // 向content script发送激活消息
            this.sendMessageToTab(tabId, {
                type: 'activate_extraction',
                url: tab.url,
                timestamp: new Date().toISOString()
            });
        }
    }
    
    /**
     * 检查是否是大众点评URL
     */
    isDianpingUrl(url) {
        return url.includes('dianping.com');
    }
    
    /**
     * 处理来自content script的消息
     */
    handleMessage(message, sender, sendResponse) {
        console.log('[Background] 收到消息:', message.type, 'from tab:', sender.tab?.id);
        
        switch (message.type) {
            case 'data_extracted':
                this.handleDataExtracted(message.data, sender);
                break;
                
            case 'extraction_error':
                this.handleExtractionError(message.error, sender);
                break;
                
            case 'websocket_status':
                this.handleWebSocketStatus(message.status, sender);
                break;
                
            case 'get_settings':
                this.getSettings(sendResponse);
                return true; // 保持消息通道开放
                
            case 'update_settings':
                this.updateSettings(message.settings, sendResponse);
                return true;
                
            default:
                console.warn('[Background] 未知消息类型:', message.type);
        }
    }
    
    /**
     * 处理数据提取完成
     */
    handleDataExtracted(data, sender) {
        this.extensionState.dataCollected++;
        this.extensionState.lastActivity = Date.now();
        
        console.log('[Background] 数据提取完成:', data);
        
        // 更新徽章显示数据收集数量
        if (sender.tab) {
            this.updateBadge(sender.tab.id, this.extensionState.dataCollected.toString());
        }
        
        // 保存到本地存储
        this.saveExtractedData(data, sender.tab?.url);
    }
    
    /**
     * 处理提取错误
     */
    handleExtractionError(error, sender) {
        this.extensionState.errors++;
        console.error('[Background] 提取错误:', error);
        
        // 更新徽章显示错误状态
        if (sender.tab) {
            this.updateBadge(sender.tab.id, '!', '#ff0000');
        }
    }
    
    /**
     * 处理WebSocket状态变化
     */
    handleWebSocketStatus(status, sender) {
        console.log('[Background] WebSocket状态:', status);
        
        if (sender.tab) {
            const badgeColor = status.connected ? '#00ff00' : '#ff9900';
            const badgeText = status.connected ? '●' : '○';
            this.updateBadge(sender.tab.id, badgeText, badgeColor);
        }
    }
    
    /**
     * 获取设置
     */
    getSettings(sendResponse) {
        chrome.storage.sync.get(null, (settings) => {
            sendResponse(settings);
        });
    }
    
    /**
     * 更新设置
     */
    updateSettings(newSettings, sendResponse) {
        chrome.storage.sync.set(newSettings, () => {
            console.log('[Background] 设置已更新:', newSettings);
            sendResponse({ success: true });
        });
    }
    
    /**
     * 保存提取的数据
     */
    saveExtractedData(data, url) {
        const dataEntry = {
            data: data,
            url: url,
            timestamp: new Date().toISOString(),
            id: `data_${Date.now()}`
        };
        
        // 获取现有数据
        chrome.storage.local.get(['extractedData'], (result) => {
            const existingData = result.extractedData || [];
            existingData.push(dataEntry);
            
            // 限制存储的数据条目数量（最多保留1000条）
            if (existingData.length > 1000) {
                existingData.splice(0, existingData.length - 1000);
            }
            
            // 保存到本地存储
            chrome.storage.local.set({ extractedData: existingData }, () => {
                console.log('[Background] 数据已保存到本地存储');
            });
        });
    }
    
    /**
     * 更新徽章
     */
    updateBadge(tabId, text, color = '#4CAF50') {
        chrome.action.setBadgeText({
            text: text,
            tabId: tabId
        });
        
        chrome.action.setBadgeBackgroundColor({
            color: color,
            tabId: tabId
        });
    }
    
    /**
     * 向指定标签页发送消息
     */
    sendMessageToTab(tabId, message) {
        chrome.tabs.sendMessage(tabId, message, (response) => {
            if (chrome.runtime.lastError) {
                console.warn('[Background] 发送消息失败:', chrome.runtime.lastError.message);
            }
        });
    }
    
    /**
     * 处理扩展图标点击
     */
    handleActionClicked(tab) {
        console.log('[Background] 扩展图标被点击, 标签页:', tab.url);
        
        if (this.isDianpingUrl(tab.url)) {
            // 在大众点评页面，切换提取状态
            this.toggleExtraction(tab.id);
        } else {
            // 在其他页面，打开大众点评
            chrome.tabs.create({
                url: 'https://g.dianping.com/dzim-main-pc/index.html#/'
            });
        }
    }
    
    /**
     * 切换数据提取状态
     */
    toggleExtraction(tabId) {
        this.extensionState.isActive = !this.extensionState.isActive;
        
        this.sendMessageToTab(tabId, {
            type: 'toggle_extraction',
            active: this.extensionState.isActive,
            timestamp: new Date().toISOString()
        });
        
        // 更新徽章
        const badgeText = this.extensionState.isActive ? '●' : '○';
        const badgeColor = this.extensionState.isActive ? '#4CAF50' : '#9E9E9E';
        this.updateBadge(tabId, badgeText, badgeColor);
    }
    
    /**
     * 开始状态检查
     */
    startStatusCheck() {
        setInterval(() => {
            console.log('[Background] 扩展状态:', this.extensionState);
        }, 60000); // 每分钟检查一次
    }
    
    /**
     * 获取扩展状态
     */
    getExtensionState() {
        return {
            ...this.extensionState,
            activeConnections: this.activeConnections.size,
            uptime: Date.now() - this.extensionState.lastActivity
        };
    }
}

// 创建后台管理器实例
const backgroundManager = new ExtensionBackgroundManager();

// 导出到全局作用域供调试使用
if (typeof globalThis !== 'undefined') {
    globalThis.backgroundManager = backgroundManager;
} 