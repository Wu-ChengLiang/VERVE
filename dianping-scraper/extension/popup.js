/**
 * 大众点评数据提取器 - 弹出窗口脚本
 * 处理用户界面交互和状态管理
 */
document.addEventListener('DOMContentLoaded', () => {
    const toggleButton = document.getElementById('toggleExtraction');
    const toggleText = document.getElementById('toggleText');
    const extractionStatus = document.getElementById('extractionStatus');
    const websocketStatus = document.getElementById('websocketStatus');
    const statusDot = document.getElementById('statusDot');
    const statusText = document.getElementById('statusText');

    let currentTabId = null;
    let isExtracting = false;

    function updateUI(extracting) {
        isExtracting = extracting;
        if (isExtracting) {
            toggleButton.className = 'btn btn-secondary';
            toggleText.textContent = '停止提取';
            extractionStatus.textContent = '运行中';
            extractionStatus.className = 'value connected';
        } else {
            toggleButton.className = 'btn btn-primary';
            toggleText.textContent = '启动提取';
            extractionStatus.textContent = '未激活';
            extractionStatus.className = 'value warning';
        }
    }
    
    function updateWebsocketStatusUI(connected) {
         if (connected) {
            websocketStatus.textContent = '已连接';
            websocketStatus.className = 'value connected';
            statusDot.className = 'status-dot connected';
            statusText.textContent = '已连接';
        } else {
            websocketStatus.textContent = '未连接';
            websocketStatus.className = 'value error';
            statusDot.className = 'status-dot error';
            statusText.textContent = '未连接';
        }
    }


    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        const tab = tabs[0];
        if (!tab) return;
        currentTabId = tab.id;
        
        const pageElement = document.getElementById('currentPage');
        if (!tab.url || !tab.url.includes('dianping.com')) {
            toggleButton.disabled = true;
            extractionStatus.textContent = '非大众点评页';
            pageElement.textContent = '非大众点评页面';
            pageElement.className = 'value warning';
            updateUI(false);
        } else {
            pageElement.textContent = '大众点评';
            pageElement.className = 'value connected';
        }

        // Get initial status from background script
        chrome.runtime.sendMessage({ type: 'getStatus', tabId: currentTabId }, (response) => {
            if (chrome.runtime.lastError) {
                console.error("GetStatus Error:", chrome.runtime.lastError.message);
                updateUI(false);
                updateWebsocketStatusUI(false);
            } else if (response) {
                updateUI(response.isExtracting);
                updateWebsocketStatusUI(response.isConnected);
            } else {
                updateUI(false);
                updateWebsocketStatusUI(false);
            }
        });
    });

    toggleButton.addEventListener('click', () => {
        if (!currentTabId || toggleButton.disabled) return;

        const messageType = isExtracting ? 'stopExtraction' : 'startExtraction';
        chrome.runtime.sendMessage({ type: messageType, tabId: currentTabId }, (response) => {
            if (chrome.runtime.lastError) {
                console.error(messageType + " Error:", chrome.runtime.lastError.message);
            } else if (response && (response.status === 'started' || response.status === 'stopped')) {
                updateUI(!isExtracting);
            }
        });
    });
    
    // Minimalistic handlers for other buttons to prevent errors
    document.getElementById('testConnection').addEventListener('click', () => {
        chrome.runtime.sendMessage({ type: 'connect' }, (response) => {
            if(response && response.status === 'connected') {
                 updateWebsocketStatusUI(true);
            } else {
                 updateWebsocketStatusUI(false);
            }
        });
    });
    document.getElementById('clearData').addEventListener('click', () => console.log('Clear data clicked'));
    document.getElementById('openDianping').addEventListener('click', () => chrome.tabs.create({ url: 'https://www.dianping.com/' }));
    document.getElementById('viewData').addEventListener('click', () => console.log('View data clicked'));
    document.getElementById('openSettings').addEventListener('click', () => console.log('Settings clicked'));
}); 