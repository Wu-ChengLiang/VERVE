/**
 * WebSocket通信管理器 - 后台脚本
 * 精简版 - 负责与Python后端的核心连接和数据传输
 */
let websocket = null;
const wsUrl = 'ws://localhost:8767';
let tabExtractionStatus = {}; // { tabId: boolean }

function connectWebSocket() {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        console.log('[Background] WebSocket已连接');
        return;
    }
    
    if (websocket && websocket.readyState === WebSocket.CONNECTING) {
        console.log('[Background] WebSocket连接中');
        return;
    }

    console.log('[Background] 正在连接WebSocket...');
    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log('[Background] WebSocket连接已建立');
    };

    websocket.onmessage = (event) => {
        console.log('[Background] 收到服务器消息:', event.data);
        try {
            const command = JSON.parse(event.data);
            if (command.type === 'sendAIReply' && command.text) {
                console.log(`[Background] 收到AI回复指令，准备发送: "${command.text}"`);
                // Find the active Dianping tab and send the message to it
                chrome.tabs.query({ active: true, url: "*://*.dianping.com/*" }, (tabs) => {
                    if (tabs.length > 0) {
                        const targetTabId = tabs[0].id;
                        console.log(`[Background] 找到目标Tab ${targetTabId}，正在发送...`);
                        chrome.tabs.sendMessage(targetTabId, {
                            type: 'sendAIReply',
                            text: command.text
                        }, (response) => {
                            if (chrome.runtime.lastError) {
                                console.error('[Background] 发送AI回复失败:', chrome.runtime.lastError.message);
                            } else {
                                console.log('[Background] AI回复指令发送成功，前端响应:', response);
                            }
                        });
                    } else {
                        console.warn('[Background] 未找到活跃的大众点评Tab来发送AI回复。');
                    }
                });
            }
        } catch (error) {
            console.warn('[Background]收到的服务器消息不是一个有效的JSON指令。', error);
        }
    };

    websocket.onclose = () => {
        console.log('[Background] WebSocket连接已关闭');
        websocket = null;
        setTimeout(connectWebSocket, 5000);
    };

    websocket.onerror = (error) => {
        console.error('[Background] WebSocket错误:', error);
        websocket = null;
    };
}

function sendMessageToServer(data) {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify(data));
    } else {
        console.error('[Background] WebSocket未连接，无法发送数据');
    }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    const tabId = message.tabId || (sender.tab ? sender.tab.id : null);

    switch (message.type) {
        case 'startExtraction':
            if (!tabId) {
                 sendResponse({ status: 'error', message: '无tabId' });
                 return true;
            }
            console.log(`[Background] 开始提取 tab ${tabId}`);
            if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                connectWebSocket();
            }
            chrome.tabs.sendMessage(tabId, { type: 'startExtraction' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('[Background] 启动提取错误:', chrome.runtime.lastError.message);
                    sendResponse({ status: 'error', message: chrome.runtime.lastError.message });
                } else {
                    tabExtractionStatus[tabId] = true;
                    sendResponse({ status: 'started' });
                }
            });
            return true;

        case 'stopExtraction':
             if (!tabId) {
                 sendResponse({ status: 'error', message: '无tabId' });
                 return true;
            }
            console.log(`[Background] 停止提取 tab ${tabId}`);
            chrome.tabs.sendMessage(tabId, { type: 'stopExtraction' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('[Background] 停止提取错误:', chrome.runtime.lastError.message);
                    sendResponse({ status: 'error', message: chrome.runtime.lastError.message });
                } else {
                    tabExtractionStatus[tabId] = false;
                    sendResponse({ status: 'stopped' });
                }
            });
            return true;

        case 'extractedData':
            console.log('[Background] 收到提取数据，发送到服务器');
            sendMessageToServer(message.data);
            break;

        case 'startClickContacts':
            if (!tabId) {
                sendResponse({ status: 'error', message: '无tabId' });
                return true;
            }
            console.log(`[Background] 开始批量提取 tab ${tabId}, 数量: ${message.count}`);
            chrome.tabs.sendMessage(tabId, { 
                type: 'startClickContacts', 
                count: message.count, 
                interval: message.interval 
            }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('[Background] 启动批量提取错误:', chrome.runtime.lastError.message);
                    sendResponse({ status: 'error', message: chrome.runtime.lastError.message });
                } else {
                    sendResponse({ status: 'started' });
                }
            });
            return true;

        case 'stopClickContacts':
            if (!tabId) {
                sendResponse({ status: 'error', message: '无tabId' });
                return true;
            }
            console.log(`[Background] 停止批量提取 tab ${tabId}`);
            chrome.tabs.sendMessage(tabId, { type: 'stopClickContacts' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('[Background] 停止批量提取错误:', chrome.runtime.lastError.message);
                    sendResponse({ status: 'error', message: chrome.runtime.lastError.message });
                } else {
                    sendResponse({ status: 'stopped' });
                }
            });
            return true;

        case 'testSendMessage':
            if (!tabId) {
                sendResponse({ status: 'failed', message: '无tabId' });
                return true;
            }
            console.log(`[Background] 测试发送消息 tab ${tabId}`);
            chrome.tabs.sendMessage(tabId, { type: 'testSendMessage' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('[Background] 测试发送错误:', chrome.runtime.lastError.message);
                    sendResponse({ status: 'failed', message: chrome.runtime.lastError.message });
                } else if (response && response.status === 'success') {
                    sendResponse({ status: 'success' });
                } else {
                    sendResponse({ status: 'failed', message: response?.message || '未知错误' });
                }
            });
            return true;

        case 'clickProgress':
        case 'clickError':
            // 转发进度和错误消息到popup
            chrome.runtime.sendMessage(message);
            break;

        case 'getStatus':
             if (!tabId) {
                 sendResponse({ isExtracting: false, isConnected: false });
                 return true;
            }
            const isConnected = websocket && websocket.readyState === WebSocket.OPEN;
            const isExtracting = !!tabExtractionStatus[tabId];
            sendResponse({ isExtracting: isExtracting, isConnected: isConnected });
            break;
            
        default:
            console.warn(`[Background] 未知消息类型: ${message.type}`);
            sendResponse({ status: 'error', message: '未知消息类型' });
            return false;
    }
    return true;
});

// 扩展启动时初始化连接
connectWebSocket();

console.log('[Background] 后台脚本已加载');
