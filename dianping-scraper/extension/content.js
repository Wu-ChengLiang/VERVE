/**
 * 大众点评数据提取器 - Content Script
 * 在大众点评网页中运行，负责DOM监听和数据提取
 */

(function() {
    'use strict';
    
    console.log('[DianpingExtractor] Content Script 加载完成');
    
    class DianpingDataExtractor {
        constructor() {
            this.isActive = false;
            this.observer = null;
            this.pollingInterval = null; // For polling on chat pages
            this.extractedData = new Set(); // Prevent duplicate extraction
            this.pageInfoSent = false;

            this.selectors = {
                chatMessageList: '.text-message.normal-text, .rich-message',
                // Other selectors can be kept for different page types
            };
            
            this.init();
        }

        /**
         * Initialize the extractor by listening for commands.
         */
        init() {
            this.listenForCommands();
        }

        /**
         * Listen for commands from the background script (e.g., from the popup).
         */
        listenForCommands() {
            chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
                console.log(`[DianpingExtractor] Received command: ${request.type}`);
                switch (request.type) {
                    case 'startExtraction':
                        this.start();
                        sendResponse({ status: 'started' });
                        break;
                    case 'stopExtraction':
                        this.stop();
                        sendResponse({ status: 'stopped' });
                        break;
                }
                return true; // Indicate asynchronous response.
            });
        }
        
        /**
         * Start the extraction process.
         */
        start() {
            if (this.isActive) {
                console.log('[DianpingExtractor] Extractor is already active.');
                return;
            }
            this.isActive = true;
            console.log('[DianpingExtractor] Extractor has been started.');

            this.extractedData.clear();
            this.pageInfoSent = false;

            // Use polling for chat pages, as it's more reliable for dynamic content.
            if (this.detectPageType() === 'chat_page') {
                console.log('[DianpingExtractor] Chat page detected. Starting polling mode.');
                if (this.pollingInterval) clearInterval(this.pollingInterval);
                this.pollingInterval = setInterval(() => this.extractData(), 2000);
            } else {
                console.log('[DianpingExtractor] Non-chat page. Starting MutationObserver mode.');
                this.startObserving();
            }
        }

        /**
         * Stop the extraction process.
         */
        stop() {
            if (!this.isActive) {
                console.log('[DianpingExtractor] Extractor is not active.');
                return;
            }
            this.isActive = false;

            if (this.pollingInterval) {
                clearInterval(this.pollingInterval);
                this.pollingInterval = null;
                console.log('[DianpingExtractor] Polling stopped.');
            }

            if (this.observer) {
                this.observer.disconnect();
                this.observer = null;
                console.log('[DianpingExtractor] MutationObserver stopped.');
            }
            console.log('[DianpingExtractor] Extractor has been stopped.');
        }

        /**
         * Send extracted data to the background script.
         */
        sendDataToBackground(data) {
            try {
                chrome.runtime.sendMessage({
                    type: 'extractedData',
                    data: data.payload.data // Send the array of messages
                });
            } catch (error) {
                console.error('[DianpingExtractor] Error sending message:', error);
            }
        }
        
        /**
         * Start the MutationObserver to watch for DOM changes on non-chat pages.
         */
        startObserving() {
            this.observer = new MutationObserver(() => {
                this.extractData();
            });
            this.observer.observe(document.body, { childList: true, subtree: true });
            console.log('[DianpingExtractor] DOM observer started.');
        }

        /**
         * Main data extraction router.
         */
        extractData() {
            if (!this.isActive) return;
            
            const pageType = this.detectPageType();
            
            if (pageType === 'chat_page') {
                const { messages, count } = this.extractChatMessages();
                if (count > 0) {
                    this.sendDataToBackground({ 
                        type: 'dianping_data', 
                        payload: { 
                            pageType, 
                            data: messages
                        }
                    });
                }
            }
            // Logic for other page types can be added here.
        }
        
        /**
         * Detects the current page type (e.g., list page, detail page, chat page).
         */
        detectPageType() {
            const url = window.location.href;
            if (url.includes('dzim-main-pc') || document.querySelector('wujie-app')) {
                return 'chat_page';
            }
            // Heuristic for in-frame detection
            if (document.querySelector('.message-list') || document.querySelector('.text-message')) {
                return 'chat_page';
            }
            return 'unknown';
        }

        /**
         * Recursively finds all elements matching a selector, searching within shadow DOMs.
         */
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
                // Ignore errors
            }
            return elements;
        }

        /**
         * Extracts chat messages from the page.
         */
        extractChatMessages() {
            const messages = [];
            const messageNodes = this.findAllElements(this.selectors.chatMessageList, document);

            console.log(`[DianpingExtractor] Found ${messageNodes.length} potential chat elements.`);

            messageNodes.forEach((node, index) => {
                const content = (node.innerText || node.textContent).trim();
                const uniqueKey = `${node.tagName}_${content.slice(0, 50)}`;

                if (content && !this.extractedData.has(uniqueKey)) {
                    messages.push({
                        id: `msg_${Date.now()}_${index}`,
                        content: content,
                    });
                    this.extractedData.add(uniqueKey);
                }
            });
            
            if(messages.length > 0) {
                console.log(`[DianpingExtractor] Extracted ${messages.length} new messages.`);
            }

            return { messages, count: messages.length };
        }
    }
    
    // Instantiate the extractor.
    if (!window.dianpingExtractor) {
        window.dianpingExtractor = new DianpingDataExtractor();
    }
    
})();