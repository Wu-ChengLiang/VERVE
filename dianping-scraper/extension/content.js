/**
 * 大众点评数据提取器 - Content Script
 * 精简版 - 只保留核心监听和数据提取功能
 */

(function() {
    'use strict';
    
    console.log('[DianpingExtractor] Content Script 加载完成');
    
    class DianpingDataExtractor {
        constructor() {
            this.isActive = false;
            this.observer = null;
            this.pollingInterval = null;
            this.extractedData = new Set(); // 防止重复提取

            // 联系人点击相关属性
            this.isClickingContacts = false;
            this.clickTimeout = null;
            this.clickCount = 0;
            this.totalClicks = 0;
            this.clickInterval = 2000;

            this.selectors = {
                chatMessageList: '.text-message.normal-text, .rich-message, .text-message.shop-text',
                tuanInfo: '.tuan',
                contactItems: '.chat-list-item', // 联系人元素选择器
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
                }
                return true;
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
                
                // 根据className判断消息类型并添加前缀
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
        
        // 开始点击联系人
        startClickContacts(count = 10, interval = 2000) {
            if (this.isClickingContacts) {
                console.log('[DianpingExtractor] 联系人点击已在进行中');
                return;
            }
            
            this.isClickingContacts = true;
            this.clickCount = 0;
            this.totalClicks = count;
            this.clickInterval = interval;
            
            console.log(`[DianpingExtractor] 开始点击联系人，总数: ${count}, 间隔: ${interval}ms`);
            this.sendProgressUpdate();
            this.clickNextContact();
        }
        
        // 停止点击联系人
        stopClickContacts() {
            if (!this.isClickingContacts) return;
            
            this.isClickingContacts = false;
            if (this.clickTimeout) {
                clearTimeout(this.clickTimeout);
                this.clickTimeout = null;
            }
            
            console.log('[DianpingExtractor] 联系人点击已停止');
            this.sendErrorMessage('用户手动停止');
        }
        
        // 点击下一个联系人
        clickNextContact() {
            if (!this.isClickingContacts || this.clickCount >= this.totalClicks) {
                this.isClickingContacts = false;
                console.log('[DianpingExtractor] 联系人点击完成');
                this.sendProgressUpdate();
                return;
            }
            
            try {
                // 查找所有联系人元素
                const contactElements = this.findAllElements(this.selectors.contactItems, document);
                
                if (contactElements.length === 0) {
                    this.sendErrorMessage('未找到联系人元素');
                    return;
                }
                
                // 获取当前要点击的联系人
                const targetContact = contactElements[this.clickCount];
                if (!targetContact) {
                    this.sendErrorMessage(`联系人 ${this.clickCount + 1} 不存在`);
                    return;
                }
                
                // 点击联系人
                console.log(`[DianpingExtractor] 点击第 ${this.clickCount + 1} 个联系人`);
                targetContact.click();
                
                // 更新计数
                this.clickCount++;
                this.sendProgressUpdate();
                
                // 设置下一次点击
                if (this.isClickingContacts && this.clickCount < this.totalClicks) {
                    this.clickTimeout = setTimeout(() => {
                        this.clickNextContact();
                    }, this.clickInterval);
                } else {
                    this.isClickingContacts = false;
                    console.log('[DianpingExtractor] 所有联系人点击完成');
                }
                
            } catch (error) {
                console.error('[DianpingExtractor] 点击联系人错误:', error);
                this.sendErrorMessage(`点击错误: ${error.message}`);
            }
        }
        
        // 发送进度更新
        sendProgressUpdate() {
            try {
                chrome.runtime.sendMessage({
                    type: 'clickProgress',
                    current: this.clickCount,
                    total: this.totalClicks
                });
            } catch (error) {
                console.error('[DianpingExtractor] 发送进度更新错误:', error);
            }
        }
        
        // 发送错误消息
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
    
    // 实例化提取器
    if (!window.dianpingExtractor) {
        window.dianpingExtractor = new DianpingDataExtractor();
    }
    
})();