/**
 * WebSocket通信管理器 - 后台脚本
 * 负责与Python后端服务器的全局连接和数据传输
 */
let websocket = null;
const wsUrl = 'ws://localhost:8765';
let tabExtractionStatus = {}; // { tabId: boolean }

function connectWebSocket() {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        console.log('[Background] WebSocket is already connected.');
        return;
    }
    
    if (websocket && websocket.readyState === WebSocket.CONNECTING) {
        console.log('[Background] WebSocket is connecting.');
        return;
    }

    console.log('[Background] Connecting to WebSocket...');
    websocket = new WebSocket(wsUrl);

    websocket.onopen = () => {
        console.log('[Background] WebSocket connection established.');
    };

    websocket.onmessage = (event) => {
        console.log('[Background] Message from server:', event.data);
    };

    websocket.onclose = () => {
        console.log('[Background] WebSocket connection closed.');
        websocket = null;
        // Optional: attempt to reconnect
        setTimeout(connectWebSocket, 5000);
    };

    websocket.onerror = (error) => {
        console.error('[Background] WebSocket error:', error);
        websocket = null;
    };
}

function sendMessageToServer(data) {
    if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify(data));
    } else {
        console.error('[Background] WebSocket not connected. Cannot send data.');
        // ToDo: Queueing could be implemented here if needed
    }
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    const tabId = message.tabId || (sender.tab ? sender.tab.id : null);

    switch (message.type) {
        case 'connect':
            console.log('[Background] Received connect request.');
            connectWebSocket();
            // Give it a moment to establish connection for the UI update
            setTimeout(() => {
                sendResponse({ status: (websocket && websocket.readyState === WebSocket.OPEN) ? 'connected' : 'connecting' });
            }, 500);
            return true; // Async response

        case 'startExtraction':
            if (!tabId) {
                 sendResponse({ status: 'error', message: 'No tabId provided.' });
                 return true;
            }
            console.log(`[Background] Received startExtraction for tab ${tabId}`);
            // Ensure connection exists before starting
            if (!websocket || websocket.readyState !== WebSocket.OPEN) {
                connectWebSocket();
            }
            chrome.tabs.sendMessage(tabId, { type: 'startExtraction' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('[Background] Error starting extraction:', chrome.runtime.lastError.message);
                    sendResponse({ status: 'error', message: chrome.runtime.lastError.message });
                } else {
                    tabExtractionStatus[tabId] = true;
                    console.log(`[Background] Extraction started for tab ${tabId}`);
                    sendResponse({ status: 'started' });
                }
            });
            return true; // Keep message channel open for async response

        case 'stopExtraction':
             if (!tabId) {
                 sendResponse({ status: 'error', message: 'No tabId provided.' });
                 return true;
            }
            console.log(`[Background] Received stopExtraction for tab ${tabId}`);
            chrome.tabs.sendMessage(tabId, { type: 'stopExtraction' }, (response) => {
                if (chrome.runtime.lastError) {
                    console.error('[Background] Error stopping extraction:', chrome.runtime.lastError.message);
                    sendResponse({ status: 'error', message: chrome.runtime.lastError.message });
                } else {
                    tabExtractionStatus[tabId] = false;
                    console.log(`[Background] Extraction stopped for tab ${tabId}`);
                    sendResponse({ status: 'stopped' });
                }
            });
            return true; // Keep message channel open for async response

        case 'extractedData':
            console.log('[Background] Received extractedData, sending to server.');
            sendMessageToServer(message.data);
            // No response needed for this message type
            break;

        case 'getStatus':
             if (!tabId) {
                 sendResponse({ isExtracting: false, isConnected: false });
                 return true;
            }
            console.log(`[Background] Received getStatus for tab ${tabId}`);
            const isConnected = websocket && websocket.readyState === WebSocket.OPEN;
            const isExtracting = !!tabExtractionStatus[tabId];
            sendResponse({ isExtracting: isExtracting, isConnected: isConnected });
            break;
            
        default:
            console.warn(`[Background] Received unknown message type: ${message.type}`);
            sendResponse({ status: 'error', message: 'Unknown message type' });
            return false;
    }
    return true; // Default to keeping channel open for async responses
});

// Initial connection attempt when the extension starts
connectWebSocket();

console.log('[BG] 后台脚本已完全加载。');
