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

            // 记忆管理相关属性
            this.currentChatId = null;
            this.currentContactName = null;
            this.conversationMemory = []; // 当前对话记忆
            this.isMemoryEnabled = true;

            this.selectors = {
                chatMessageList: '.text-message.normal-text, .rich-message, .text-message.shop-text',
                tuanInfo: '.tuan',
                contactItems: '.chat-list-item',
            };
            
            this.init();
        }

        init() {
            this.listenForCommands();
            this.setupAutoSave();
        }

        setupAutoSave() {
            // 页面卸载时自动保存记忆
            window.addEventListener('beforeunload', () => {
                if (this.conversationMemory.length > 0 && this.currentChatId) {
                    this.saveCurrentMemory();
                }
            });
            
            // 页面隐藏时也保存记忆
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'hidden' && this.conversationMemory.length > 0 && this.currentChatId) {
                    this.saveCurrentMemory();
                }
            });
        }

        saveCurrentMemory() {
            try {
                chrome.runtime.sendMessage({
                    type: 'extractedData',
                    data: {
                        type: 'memory_save',
                        payload: {
                            action: 'save',
                            chatId: this.currentChatId,
                            contactName: this.currentContactName,
                            conversationMemory: this.conversationMemory.slice(),
                            timestamp: Date.now()
                        }
                    }
                });
                console.log(`[记忆] 自动保存记忆 (${this.conversationMemory.length}条): ${this.currentContactName}`);
            } catch (error) {
                console.error('[记忆] 自动保存记忆错误:', error);
            }
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
            
            // 将AI回复添加到记忆中
            const aiReplyData = {
                id: `ai_reply_${Date.now()}`,
                type: 'chat_message',
                messageType: 'shop', // AI回复算作商家回复
                content: `[商家] ${replyText}`,
                originalContent: replyText,
                timestamp: Date.now(),
                chatId: this.currentChatId,
                contactName: this.currentContactName
            };
            
            this.addToMemory(aiReplyData);
            
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
            // 自动检测当前联系人（如果尚未设置）
            if (!this.currentChatId) {
                this.autoDetectCurrentContact();
            }
            
            try {
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
                            pageType: this.detectPageType(),
                            data: allExtractedData
                        }
                    });
                }
            } catch (error) {
                console.error('[DianpingExtractor] 数据提取错误:', error);
            }
        }
        
        autoDetectCurrentContact() {
            try {
                // 初始化默认值
                let contactName = '默认联系人';
                let chatId = 'default_chat';
                
                console.log('[联系人检测] 开始自动检测当前联系人...');
                
                // 方法1: 优先从 userinfo-username 元素获取（包含 data-chatid）
                const userinfoElement = document.querySelector('.userinfo-username[data-chatid]');
                if (userinfoElement) {
                    const name = userinfoElement.textContent.trim();
                    const dataChatId = userinfoElement.getAttribute('data-chatid');
                    if (name && dataChatId) {
                        contactName = name;
                        chatId = dataChatId;
                        console.log(`[联系人检测] 从 userinfo-username 提取到: ${contactName} (chatId: ${chatId})`);
                    }
                } else {
                    // 方法2: 从 userinfo-name-show 元素获取联系人名称
                    const nameShowElement = document.querySelector('.userinfo-name-show');
                    if (nameShowElement) {
                        const name = nameShowElement.textContent.trim();
                        if (name) {
                            contactName = name;
                            // 如果没有 data-chatid，生成一个基于名称的 chatId
                            chatId = `chat_${name}_${Date.now()}`;
                            console.log(`[联系人检测] 从 userinfo-name-show 提取到: ${contactName} (生成 chatId: ${chatId})`);
                        }
                    } else {
                        // 方法3: 尝试其他可能的选择器
                        const fallbackSelectors = [
                            '.userinfo-username',
                            '.chat-title', 
                            '.contact-name',
                            '.shop-name',
                            '.merchant-name'
                        ];
                        
                        for (const selector of fallbackSelectors) {
                            const element = document.querySelector(selector);
                            if (element && element.textContent.trim()) {
                                const name = element.textContent.trim();
                                contactName = name;
                                chatId = `chat_${name}_${Date.now()}`;
                                console.log(`[联系人检测] 从备用选择器 ${selector} 提取到: ${contactName}`);
                                break;
                            }
                        }
                        
                        // 方法4: 如果都没找到，使用时间戳生成唯一标识
                        if (contactName === '默认联系人') {
                            const timestamp = Date.now();
                            contactName = `用户_${timestamp}`;
                            chatId = `chat_${timestamp}`;
                            console.log(`[联系人检测] 未找到联系人信息，生成临时标识: ${contactName}`);
                        }
                    }
                }
                
                // 设置当前联系人信息
                this.currentChatId = chatId;
                this.currentContactName = contactName;
                
                console.log(`[联系人检测] 最终确定联系人: ${contactName} (ID: ${chatId})`);
                
                // 调试：输出页面中找到的相关元素
                console.log('[联系人检测] 页面中的联系人相关元素:');
                const debugElements = [
                    { selector: '.userinfo-username[data-chatid]', desc: '带chatId的用户名' },
                    { selector: '.userinfo-name-show', desc: '用户名显示' },
                    { selector: '.userinfo-username', desc: '用户名' }
                ];
                
                debugElements.forEach(({ selector, desc }) => {
                    const el = document.querySelector(selector);
                    if (el) {
                        const chatIdAttr = el.getAttribute('data-chatid');
                        console.log(`  ${desc}: "${el.textContent.trim()}"${chatIdAttr ? ` (chatId: ${chatIdAttr})` : ''}`);
                    }
                });
                
            } catch (error) {
                console.error('[联系人检测] 自动检测联系人错误:', error);
                // 错误恢复：使用时间戳生成唯一标识
                const timestamp = Date.now();
                this.currentChatId = `error_${timestamp}`;
                this.currentContactName = `错误恢复_${timestamp}`;
                console.log(`[联系人检测] 错误恢复，使用: ${this.currentContactName}`);
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
                
                // ✅ 改进去重机制：使用DOM元素的完整路径和内容组合
                const elementPath = this.getElementPath(node);
                const uniqueKey = `${elementPath}_${content.slice(0, 100)}_${messageType}`;

                if (content && !this.extractedData.has(uniqueKey)) {
                    const messageData = {
                        id: `msg_${Date.now()}_${index}`,
                        type: 'chat_message',
                        messageType: messageType,
                        content: prefixedContent,
                        originalContent: content,
                        timestamp: Date.now(), // ✅ 使用当前时间戳，确保时间准确性
                        chatId: this.currentChatId,
                        contactName: this.currentContactName
                    };
                    
                    messages.push(messageData);
                    this.extractedData.add(uniqueKey);
                    
                    // ✅ 只对客户消息添加到记忆并可能触发AI回复
                    if (messageType === 'customer') {
                        this.addToMemory(messageData);
                    } else {
                        // 商家消息只添加到记忆，不触发AI回复逻辑
                        this.addToMemoryWithoutTrigger(messageData);
                    }
                }
            });
            
            if(messages.length > 0) {
                console.log(`[DianpingExtractor] 提取 ${messages.length} 条新消息`);
            }

            return { messages, count: messages.length };
        }

        // ✅ 获取元素的完整DOM路径，用于更准确的去重
        getElementPath(element) {
            const path = [];
            let current = element;
            
            while (current && current !== document.body) {
                let selector = current.tagName.toLowerCase();
                
                if (current.id) {
                    selector += `#${current.id}`;
                } else if (current.className) {
                    selector += `.${current.className.split(' ').join('.')}`;
                }
                
                // 添加同级元素的索引
                const siblings = Array.from(current.parentNode?.children || [])
                    .filter(sibling => sibling.tagName === current.tagName);
                if (siblings.length > 1) {
                    const index = siblings.indexOf(current);
                    selector += `:nth-child(${index + 1})`;
                }
                
                path.unshift(selector);
                current = current.parentNode;
            }
            
            return path.join(' > ');
        }

        // ✅ 添加消息到记忆但不触发AI回复的方法
        addToMemoryWithoutTrigger(messageData) {
            if (!this.isMemoryEnabled || !messageData) return;
            
            // 添加到本地记忆
            this.conversationMemory.push({
                role: messageData.messageType === 'customer' ? 'user' : 'assistant',
                content: messageData.originalContent,
                timestamp: messageData.timestamp,
                messageId: messageData.id
            });
            
            // 限制记忆长度，保留最近的20条消息
            if (this.conversationMemory.length > 20) {
                this.conversationMemory = this.conversationMemory.slice(-20);
            }
            
            console.log(`[记忆-无触发] 添加消息到记忆 (${this.conversationMemory.length}/20): ${messageData.originalContent.slice(0, 50)}...`);
            
            // 不发送memory_update，避免触发AI回复
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
                
                // 检测联系人切换并处理记忆
                this.handleContactSwitch(contactInfo);
                
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
            let chatId = '';
            
            try {
                // 优先从带有 data-chatid 属性的 userinfo-username 元素获取
                const nameElementWithChatId = contactElement.querySelector('.userinfo-username[data-chatid]');
                if (nameElementWithChatId) {
                    name = nameElementWithChatId.textContent.trim();
                    chatId = nameElementWithChatId.getAttribute('data-chatid');
                    console.log(`[联系人信息] 从 userinfo-username 提取: ${name} (chatId: ${chatId})`);
                } else {
                    // 备用方案：从 userinfo-name-show 或其他元素获取
                    const selectors = ['.userinfo-name-show', '.userinfo-username', '.contact-name'];
                    for (const selector of selectors) {
                        const nameElement = contactElement.querySelector(selector);
                        if (nameElement && nameElement.textContent.trim()) {
                            name = nameElement.textContent.trim();
                            console.log(`[联系人信息] 从 ${selector} 提取: ${name}`);
                            break;
                        }
                    }
                    
                    // 尝试从元素本身获取 data-chatid
                    chatId = contactElement.getAttribute('data-chatid') || contactElement.id || '';
                }
                
                // 如果没有找到 chatId，生成一个基于名称的 ID
                if (!chatId && name !== '未知联系人') {
                    chatId = `chat_${name}_${Date.now()}`;
                    console.log(`[联系人信息] 生成 chatId: ${chatId}`);
                }
                
            } catch (error) {
                console.error('[联系人信息] 获取联系人信息错误:', error);
            }
            
            return {
                name: name,
                chatId: chatId,
                timestamp: Date.now()
            };
        }

        handleContactSwitch(contactInfo) {
            if (!this.isMemoryEnabled) return;
            
            const newChatId = contactInfo.chatId || contactInfo.name;
            const newContactName = contactInfo.name;
            
            // 检测是否切换了联系人
            if (this.currentChatId && this.currentChatId !== newChatId) {
                console.log(`[记忆] 检测到联系人切换: ${this.currentContactName} -> ${newContactName}`);
                
                // 发送记忆清空请求
                this.sendMemoryClearRequest(this.currentChatId, this.currentContactName);
                
                // 清空当前记忆
                this.conversationMemory = [];
            }
            
            // 更新当前联系人信息
            this.currentChatId = newChatId;
            this.currentContactName = newContactName;
            
            console.log(`[记忆] 当前聊天对象: ${newContactName} (ID: ${newChatId})`);
        }

        sendMemoryClearRequest(oldChatId, oldContactName) {
            try {
                chrome.runtime.sendMessage({
                    type: 'extractedData',
                    data: {
                        type: 'chat_context_switch',
                        payload: {
                            action: 'switch',
                            oldChatId: oldChatId,
                            oldContactName: oldContactName,
                            newChatId: this.currentChatId,
                            newContactName: this.currentContactName,
                            conversationMemory: this.conversationMemory.slice(), // 发送当前记忆的副本
                            timestamp: Date.now()
                        }
                    }
                });
                console.log(`[记忆] 已发送记忆切换请求: ${oldContactName} -> ${this.currentContactName}`);
            } catch (error) {
                console.error('[记忆] 发送记忆切换请求错误:', error);
            }
        }

        addToMemory(messageData) {
            if (!this.isMemoryEnabled || !messageData) return;
            
            // 添加到本地记忆
            this.conversationMemory.push({
                role: messageData.messageType === 'customer' ? 'user' : 'assistant',
                content: messageData.originalContent,
                timestamp: messageData.timestamp,
                messageId: messageData.id
            });
            
            // 限制记忆长度，保留最近的20条消息
            if (this.conversationMemory.length > 20) {
                this.conversationMemory = this.conversationMemory.slice(-20);
            }
            
            console.log(`[记忆] 添加消息到记忆 (${this.conversationMemory.length}/20): ${messageData.originalContent.slice(0, 50)}...`);
            
            // 发送记忆更新到后端
            this.sendMemoryUpdate(messageData);
        }

        sendMemoryUpdate(messageData) {
            try {
                chrome.runtime.sendMessage({
                    type: 'extractedData',
                    data: {
                        type: 'memory_update',
                        payload: {
                            action: 'add_message',
                            chatId: this.currentChatId,
                            contactName: this.currentContactName,
                            message: messageData,
                            conversationMemory: this.conversationMemory.slice(), // 发送当前记忆的副本
                            timestamp: Date.now()
                        }
                    }
                });
            } catch (error) {
                console.error('[记忆] 发送记忆更新错误:', error);
            }
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