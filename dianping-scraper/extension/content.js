/**
 * 大众点评数据提取器 - Content Script
 * 精简版 - 只保留核心监听和数据提取功能
 */

(function() {
    'use strict';
    
    console.log('[DianpingExtractor] Content Script 加载完成 (V4)');
    
    class DianpingDataExtractor {
        constructor() {
            this.isActive = false;
            this.observer = null;
            this.pollingInterval = null;
            this.extractedData = new Set();
            this.isClickingContacts = false;
            this.clickTimeout = null;
            this.clickCount = 0;
            this.totalClicks = 0;

            this.selectors = {
                chatMessageList: '.text-message.normal-text, .rich-message, .text-message.shop-text',
                tuanInfo: '.tuan',
                contactItems: '.chat-list-item',
            };
            
            this.init();
        }

        init() {
            this.listenForCommands();
        }

        listenForCommands() {
            chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
                console.log(`[DianpingExtractor] 收到命令: ${request.type}`);
                switch (request.type) {
                    case 'startExtraction':
                        this.start();
                        sendResponse({ status: 'started' });
                        break;
                    case 'stopExtraction':
                        this.stop();
                        sendResponse({ status: 'stopped' });
                        break;
                    case 'startClickContacts':
                        this.startClickContacts(request.count, request.interval);
                        sendResponse({ status: 'started' });
                        break;
                    case 'stopClickContacts':
                        this.stopClickContacts();
                        sendResponse({ status: 'stopped' });
                        break;
                    case 'testSendMessage':
                        this.executeTestSend()
                            .then(result => sendResponse(result))
                            .catch(error => sendResponse({ status: 'failed', message: error.message }));
                        break;
                    case 'sendAIReply':
                        this.sendAIReply(request.text)
                             .then(result => sendResponse(result))
                             .catch(error => sendResponse({ status: 'failed', message: error.message }));
                        break;
                }
                return true;
            });
        }
        
        // --- Injected Script Logic ---
        
        // This is the main function to communicate with the injected script.
        // It injects the script and sends it a task to perform.
        _executeInjectedScript(task) {
            console.log(`[ContentScript] Injecting script to perform task:`, task);
            
            return new Promise((resolve, reject) => {
                const scriptId = 'verve-injector-script';
                const taskEventName = 'verveInjectorTask';
                const resultEventName = 'verveInjectorResult';

                // Cleanup previous script if it exists
                document.getElementById(scriptId)?.remove();

                // 1. Define the listener for the response event from the injected script
                const resultListener = (event) => {
                    console.log(`[ContentScript] Received result:`, event.detail);
                    if (event.detail.status === 'success') {
                        resolve({ status: 'success', message: event.detail.message });
                    } else {
                        reject(new Error(event.detail.message || 'Injected script failed.'));
                    }
                    // Auto-cleanup
                    window.removeEventListener(resultEventName, resultListener);
                    document.getElementById(scriptId)?.remove();
                };

                // 2. Add the result listener
                window.addEventListener(resultEventName, resultListener, { once: true });

                // 3. Create and inject the script element
                const script = document.createElement('script');
                script.id = scriptId;
                script.src = chrome.runtime.getURL('injector.js');
                
                // 4. Once the script is loaded, dispatch the task to it
                script.onload = () => {
                    console.log('[ContentScript] Injected script loaded. Sending task...');
                    window.dispatchEvent(new CustomEvent(taskEventName, { detail: task }));
                };
                
                script.onerror = (e) => {
                    console.error('[ContentScript] Failed to load injector script:', e);
                    window.removeEventListener(resultEventName, resultListener); // Cleanup on error
                    reject(new Error('Failed to load injector script.'));
                };
                
                (document.head || document.documentElement).appendChild(script);
            });
        }

        // The original test function, now simplified
        executeTestSend() {
            return this._executeInjectedScript({
                action: 'testAndSend',
                text: '这是一个自动发送的测试消息'
            });
        }

        // New function to handle sending AI replies
        sendAIReply(replyText) {
            console.log(`[ContentScript] Received request to send AI reply: "${replyText}"`);
            return this._executeInjectedScript({
                action: 'testAndSend',
                text: replyText
            });
        }
        
        start() {
            if (this.isActive) {
                console.log('[DianpingExtractor] 提取器已激活');
                return;
            }
            this.isActive = true;
            console.log('[DianpingExtractor] 开始数据提取');

            this.extractedData.clear();

            if (this.detectPageType() === 'chat_page') {
                console.log('[DianpingExtractor] 聊天页面 - 启动轮询模式');
                if (this.pollingInterval) clearInterval(this.pollingInterval);
                this.pollingInterval = setInterval(() => this.extractData(), 2000);
            } else {
                console.log('[DianpingExtractor] 普通页面 - 启动DOM监听模式');
                this.startObserving();
            }
        }

        stop() {
            if (!this.isActive) return;
            this.isActive = false;

            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
            }

            if (this.observer) {
                this.observer.disconnect();
                this.observer = null;
            }
            console.log('[DianpingExtractor] 数据提取已停止');
        }

        sendDataToBackground(data) {
            try {
                chrome.runtime.sendMessage({
                    type: 'extractedData',
                    data: data.payload.data
                });
            } catch (error) {
                console.error('[DianpingExtractor] 发送消息错误:', error);
            }
        }
        
        startObserving() {
            this.observer = new MutationObserver(() => {
                this.extractData();
            });
            this.observer.observe(document.body, { childList: true, subtree: true });
        }

        extractData() {
            if (!this.isActive) return;
            
            const pageType = this.detectPageType();
            
            if (pageType === 'chat_page') {
                const allExtractedData = [];

                const { messages } = this.extractChatMessages();
                if (messages.length > 0) {
                    allExtractedData.push(...messages);
                }

                const { tuanInfo } = this.extractTuanInfo();
                if (tuanInfo.length > 0) {
                    allExtractedData.push(...tuanInfo);
                }

                if (allExtractedData.length > 0) {
                    this.sendDataToBackground({
                        type: 'dianping_data',
                        payload: {
                            pageType,
                            data: allExtractedData
                        }
                    });
                }
            }
        }
        
        detectPageType() {
            const url = window.location.href;
            if (url.includes('dzim-main-pc') || document.querySelector('wujie-app')) {
                return 'chat_page';
            }
            if (document.querySelector('.message-list') || document.querySelector('.text-message')) {
                return 'chat_page';
            }
            return 'unknown';
        }

        findAllElements(selector, root) {
            let elements = [];
            try {
                Array.prototype.push.apply(elements, root.querySelectorAll(selector));
                const descendants = root.querySelectorAll('*');
                for (const el of descendants) {
                    if (el.shadowRoot) {
                        const nestedElements = this.findAllElements(selector, el.shadowRoot);
                        Array.prototype.push.apply(elements, nestedElements);
                    }
                }
            } catch (e) {
                // 忽略错误
            }
            return elements;
        }

        extractChatMessages() {
            const messages = [];
            const messageNodes = this.findAllElements(this.selectors.chatMessageList, document);

            messageNodes.forEach((node, index) => {
                const content = (node.innerText || node.textContent).trim();
                
                let messageType = '';
                let prefix = '';
                if (node.className.includes('shop-text')) {
                    messageType = 'shop';
                    prefix = '[商家] ';
                } else if (node.className.includes('normal-text')) {
                    messageType = 'customer';
                    prefix = '[客户] ';
                } else {
                    messageType = 'unknown';
                    prefix = '[未知] ';
                }
                
                const prefixedContent = prefix + content;
                const uniqueKey = `${node.tagName}_${prefixedContent.slice(0, 50)}`;

                if (content && !this.extractedData.has(uniqueKey)) {
                    messages.push({
                        id: `msg_${Date.now()}_${index}`,
                        type: 'chat_message',
                        messageType: messageType,
                        content: prefixedContent,
                        originalContent: content,
                    });
                    this.extractedData.add(uniqueKey);
                }
            });
            
            if(messages.length > 0) {
                console.log(`[DianpingExtractor] 提取 ${messages.length} 条新消息`);
            }

            return { messages, count: messages.length };
        }

        extractTuanInfo() {
            const tuanInfoList = [];
            const tuanNodes = this.findAllElements(this.selectors.tuanInfo, document);

            tuanNodes.forEach((node, index) => {
                try {
                    const nameNode = node.querySelector('.tuan-name');
                    const salePriceNode = node.querySelector('.sale-price');
                    const originalPriceNode = node.querySelector('.tuan-price .gray-price > span, .tuan-price > .gray > .gray-price:not(.left-dis)');
                    const imageNode = node.querySelector('.tuan-img img');

                    const name = nameNode ? nameNode.innerText.trim() : '';
                    const salePrice = salePriceNode ? salePriceNode.innerText.trim() : '';
                    
                    const uniqueKey = `tuan_${name}_${salePrice}`;

                    if (name && salePrice && !this.extractedData.has(uniqueKey)) {
                        const originalPrice = originalPriceNode ? originalPriceNode.innerText.trim() : '';
                        const image = imageNode ? imageNode.src : '';

                        tuanInfoList.push({
                            id: `tuan_${Date.now()}_${index}`,
                            type: 'tuan_info',
                            content: {
                                name,
                                salePrice,
                                originalPrice,
                                image,
                            }
                        });
                        this.extractedData.add(uniqueKey);
                    }
                } catch (error) {
                    console.error('[DianpingExtractor] 提取团购信息错误:', error);
                }
            });
            
            if(tuanInfoList.length > 0) {
                console.log(`[DianpingExtractor] 提取 ${tuanInfoList.length} 条团购信息`);
            }

            return { tuanInfo: tuanInfoList, count: tuanInfoList.length };
        }
        
        startClickContacts(count = 10, interval = 2000) {
            if (this.isClickingContacts) {
                console.log('[DianpingExtractor] 批量提取已在进行中');
                return;
            }
            
            this.isClickingContacts = true;
            this.clickCount = 0;
            this.totalClicks = count;
            this.clickInterval = interval;

            // 动态调整内部延迟时间
            this.pageLoadWaitTime = Math.min(1500, interval * 0.6);
            this.extractionWaitTime = Math.min(2500, interval * 0.8);
            
            console.log(`[DianpingExtractor] 开始批量提取，总数: ${count}, 间隔: ${interval}ms`);
            this.sendProgressUpdate();
            this.clickNextContact();
        }
        
        stopClickContacts() {
            if (!this.isClickingContacts) return;
            
            this.isClickingContacts = false;
            if (this.clickTimeout) {
                clearTimeout(this.clickTimeout);
                this.clickTimeout = null;
            }
            
            console.log('[DianpingExtractor] 批量提取已停止');
        }
        
        clickNextContact() {
            if (!this.isClickingContacts || this.clickCount >= this.totalClicks) {
                this.isClickingContacts = false;
                console.log('[DianpingExtractor] 批量提取完成');
                this.sendProgressUpdate();
                return;
            }
            
            try {
                const contactElements = this.findAllElements(this.selectors.contactItems, document);
                
                if (contactElements.length === 0) {
                    this.sendErrorMessage('未找到联系人元素');
                    return;
                }
                
                const targetContact = contactElements[this.clickCount];
                if (!targetContact) {
                    this.sendErrorMessage(`联系人 ${this.clickCount + 1} 不存在`);
                    return;
                }
                
                const contactInfo = this.getContactInfo(targetContact);
                console.log(`[DianpingExtractor] 点击第 ${this.clickCount + 1} 个联系人: ${contactInfo.name}`);
                
                targetContact.click();
                
                this.clickCount++;
                this.sendProgressUpdate(`正在处理联系人: ${contactInfo.name}`);
                
                setTimeout(() => {
                    this.extractCurrentContactData(contactInfo);
                }, this.pageLoadWaitTime);
                
            } catch (error) {
                console.error('[DianpingExtractor] 点击联系人错误:', error);
                this.sendErrorMessage(`点击错误: ${error.message}`);
            }
        }
        
        getContactInfo(contactElement) {
            let name = '未知联系人';
            try {
                const nameElement = contactElement.querySelector('.userinfo-username');
                if (nameElement) {
                    name = nameElement.textContent.trim();
                }
            } catch (error) {
                console.error('[DianpingExtractor] 获取联系人信息错误:', error);
            }
            
            return {
                name: name,
                chatId: contactElement.getAttribute('data-chatid') || contactElement.id || '',
                timestamp: Date.now()
            };
        }
        
        extractCurrentContactData(contactInfo) {
            if (!this.isClickingContacts) return;
            
            console.log(`[DianpingExtractor] 开始提取联系人 ${contactInfo.name} 的数据`);
            
            try {
                const allExtractedData = [];
                
                const { messages } = this.extractChatMessages();
                if (messages.length > 0) {
                    const messagesWithContact = messages.map(msg => ({
                        ...msg,
                        contactInfo: contactInfo,
                        contactName: contactInfo.name,
                        contactChatId: contactInfo.chatId
                    }));
                    allExtractedData.push(...messagesWithContact);
                }
                
                const { tuanInfo } = this.extractTuanInfo();
                if (tuanInfo.length > 0) {
                    const tuanWithContact = tuanInfo.map(tuan => ({
                        ...tuan,
                        contactInfo: contactInfo,
                        contactName: contactInfo.name,
                        contactChatId: contactInfo.chatId
                    }));
                    allExtractedData.push(...tuanWithContact);
                }
                
                if (allExtractedData.length > 0) {
                    this.sendDataToBackground({
                        type: 'dianping_contact_data',
                        payload: {
                            pageType: 'chat_page',
                            contactInfo: contactInfo,
                            data: allExtractedData
                        }
                    });
                    console.log(`[DianpingExtractor] 已提取联系人 ${contactInfo.name} 的 ${allExtractedData.length} 条数据`);
                } else {
                    console.log(`[DianpingExtractor] 联系人 ${contactInfo.name} 暂无新数据`);
                }
                
            } catch (error) {
                console.error('[DianpingExtractor] 提取联系人数据错误:', error);
            }
            
            setTimeout(() => {
                this.proceedToNextContact();
            }, this.extractionWaitTime);
        }
        
        proceedToNextContact() {
            if (!this.isClickingContacts) return;
            
            if (this.clickCount < this.totalClicks) {
                this.clickTimeout = setTimeout(() => this.clickNextContact(), this.clickInterval);
            } else {
                this.isClickingContacts = false;
                this.sendProgressUpdate('所有联系人处理完成');
            }
        }
        
        sendProgressUpdate(status = '') {
            try {
                chrome.runtime.sendMessage({
                    type: 'clickProgress',
                    current: this.clickCount,
                    total: this.totalClicks,
                    status: status
                });
            } catch (error) {
                console.error('[DianpingExtractor] 发送进度更新错误:', error);
            }
        }
        
        sendErrorMessage(message) {
            this.isClickingContacts = false;
            if (this.clickTimeout) {
                clearTimeout(this.clickTimeout);
                this.clickTimeout = null;
            }
            
            try {
                chrome.runtime.sendMessage({
                    type: 'clickError',
                    message: message
                });
            } catch (error) {
                console.error('[DianpingExtractor] 发送错误消息错误:', error);
            }
        }
    }
    
    if (!window.dianpingExtractor) {
        window.dianpingExtractor = new DianpingDataExtractor();
    }
})();