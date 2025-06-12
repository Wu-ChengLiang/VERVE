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
            this.websocketManager = null;
            this.extractedData = new Set(); // 防止重复提取
            this.lastExtractTime = 0;
            this.extractCooldown = 2000; // 2秒冷却期
            
            // 大众点评特定选择器
            this.selectors = {
                // 餐厅列表页面
                restaurantList: '.shop-list .shop-item',
                restaurantItem: {
                    name: '.shop-name, .shop-title, h3, h4',
                    rating: '.rating-num, .score, .point',
                    address: '.shop-addr, .address',
                    price: '.price, .avg-price, .per-price',
                    category: '.shop-type, .category',
                    distance: '.distance',
                    image: 'img'
                },
                
                // 餐厅详情页面
                restaurantDetail: {
                    name: '.shop-name, .shop-title, h1',
                    rating: '.rating-num, .score',
                    address: '.shop-addr, .address',
                    phone: '.shop-phone, .phone',
                    hours: '.hours, .business-hours',
                    tags: '.shop-tags .tag, .tags .tag'
                },
                
                // 评论列表
                reviewList: '.reviews .review-item, .comment-list .comment-item',
                reviewItem: {
                    user: '.user-name, .reviewer-name',
                    rating: '.rating, .score',
                    content: '.review-content, .comment-content',
                    date: '.review-date, .comment-date',
                    useful: '.useful-count'
                }
            };
            
            this.init();
        }
        
        /**
         * 初始化提取器
         */
        init() {
            console.log('[DianpingExtractor] 初始化数据提取器...');
            
            // 等待WebSocket管理器加载
            this.waitForWebSocket();
            
            // 监听页面变化
            this.startObserving();
            
            // 监听WebSocket状态
            this.listenWebSocketStatus();
            
            // 初始数据提取
            this.scheduleExtraction();
        }
        
        /**
         * 等待WebSocket管理器加载
         */
        waitForWebSocket() {
            const checkWebSocket = () => {
                if (window.DianpingWebSocketManager) {
                    console.log('[DianpingExtractor] WebSocket管理器已就绪');
                    this.websocketManager = window.DianpingWebSocketManager;
                    this.isActive = true;
                } else {
                    // 加载WebSocket脚本
                    this.loadWebSocketScript();
                    setTimeout(checkWebSocket, 1000);
                }
            };
            checkWebSocket();
        }
        
        /**
         * 加载WebSocket脚本
         */
        loadWebSocketScript() {
            if (document.querySelector('script[src*="websocket.js"]')) {
                return; // 已加载
            }
            
            const script = document.createElement('script');
            script.src = chrome.runtime.getURL('websocket.js');
            script.onload = () => {
                console.log('[DianpingExtractor] WebSocket脚本加载完成');
            };
            script.onerror = (error) => {
                console.error('[DianpingExtractor] WebSocket脚本加载失败:', error);
            };
            
            (document.head || document.documentElement).appendChild(script);
        }
        
        /**
         * 监听WebSocket连接状态
         */
        listenWebSocketStatus() {
            document.addEventListener('websocket-status', (event) => {
                const { connected } = event.detail;
                console.log('[DianpingExtractor] WebSocket状态变更:', connected ? '已连接' : '已断开');
                
                if (connected && this.isActive) {
                    // 连接成功后立即提取一次数据
                    this.scheduleExtraction();
                }
            });
        }
        
        /**
         * 开始监听DOM变化
         */
        startObserving() {
            // 创建MutationObserver监听页面变化
            this.observer = new MutationObserver((mutations) => {
                let shouldExtract = false;
                
                mutations.forEach((mutation) => {
                    // 检查是否有新节点添加
                    if (mutation.type === 'childList' && mutation.addedNodes.length > 0) {
                        mutation.addedNodes.forEach((node) => {
                            if (node.nodeType === Node.ELEMENT_NODE) {
                                // 检查是否是我们关心的元素
                                if (this.isRelevantElement(node)) {
                                    shouldExtract = true;
                                }
                            }
                        });
                    }
                });
                
                if (shouldExtract) {
                    this.scheduleExtraction();
                }
            });
            
            // 开始观察
            this.observer.observe(document.body, {
                childList: true,
                subtree: true
            });
            
            console.log('[DianpingExtractor] DOM监听已启动');
        }
        
        /**
         * 检查元素是否相关
         */
        isRelevantElement(element) {
            const relevantClasses = [
                'shop-item', 'shop-list', 'restaurant-item',
                'review-item', 'comment-item',
                'shop-detail', 'restaurant-detail'
            ];
            
            return relevantClasses.some(className => 
                element.classList?.contains(className) ||
                element.querySelector(`.${className}`)
            );
        }
        
        /**
         * 安排数据提取（防抖）
         */
        scheduleExtraction() {
            const now = Date.now();
            if (now - this.lastExtractTime < this.extractCooldown) {
                return; // 冷却期内，跳过
            }
            
            this.lastExtractTime = now;
            
            // 延迟执行，等待DOM稳定
            setTimeout(() => {
                this.extractData();
            }, 500);
        }
        
        /**
         * 提取数据
         */
        extractData() {
            if (!this.isActive || !this.websocketManager) {
                console.log('[DianpingExtractor] 提取器未激活或WebSocket未就绪');
                return;
            }
            
            console.log('[DianpingExtractor] 开始提取数据...');
            
            const extractedData = {
                url: window.location.href,
                pageType: this.detectPageType(),
                timestamp: new Date().toISOString(),
                data: {}
            };
            
            try {
                // 根据页面类型提取不同数据
                switch (extractedData.pageType) {
                    case 'restaurant_list':
                        extractedData.data = this.extractRestaurantList();
                        break;
                    case 'restaurant_detail':
                        extractedData.data = this.extractRestaurantDetail();
                        break;
                    case 'reviews':
                        extractedData.data = this.extractReviews();
                        break;
                    default:
                        extractedData.data = this.extractGenericData();
                }
                
                // 检查是否有新数据
                const dataHash = this.hashData(extractedData.data);
                if (!this.extractedData.has(dataHash)) {
                    this.extractedData.add(dataHash);
                    
                    // 发送数据到后端
                    this.websocketManager.sendDianpingData(extractedData);
                    
                    console.log('[DianpingExtractor] 数据提取完成:', extractedData);
                } else {
                    console.log('[DianpingExtractor] 数据未变化，跳过发送');
                }
                
            } catch (error) {
                console.error('[DianpingExtractor] 数据提取失败:', error);
            }
        }
        
        /**
         * 检测页面类型
         */
        detectPageType() {
            const url = window.location.href;
            const pathname = window.location.pathname;
            
            if (url.includes('shop') && url.includes('list')) {
                return 'restaurant_list';
            } else if (pathname.includes('/shop/')) {
                return 'restaurant_detail';
            } else if (url.includes('review') || url.includes('comment')) {
                return 'reviews';
            } else {
                return 'unknown';
            }
        }
        
        /**
         * 提取餐厅列表数据
         */
        extractRestaurantList() {
            const restaurants = [];
            const restaurantElements = document.querySelectorAll(this.selectors.restaurantList);
            
            restaurantElements.forEach((element, index) => {
                try {
                    const restaurant = {
                        id: `restaurant_${index}`,
                        name: this.extractText(element, this.selectors.restaurantItem.name),
                        rating: this.extractText(element, this.selectors.restaurantItem.rating),
                        address: this.extractText(element, this.selectors.restaurantItem.address),
                        price: this.extractText(element, this.selectors.restaurantItem.price),
                        category: this.extractText(element, this.selectors.restaurantItem.category),
                        distance: this.extractText(element, this.selectors.restaurantItem.distance),
                        image: this.extractImage(element, this.selectors.restaurantItem.image),
                        link: this.extractLink(element)
                    };
                    
                    // 只添加有名称的餐厅
                    if (restaurant.name) {
                        restaurants.push(restaurant);
                    }
                } catch (error) {
                    console.warn('[DianpingExtractor] 餐厅数据提取失败:', error);
                }
            });
            
            return { restaurants, count: restaurants.length };
        }
        
        /**
         * 提取餐厅详情数据
         */
        extractRestaurantDetail() {
            const detail = {
                name: this.extractText(document, this.selectors.restaurantDetail.name),
                rating: this.extractText(document, this.selectors.restaurantDetail.rating),
                address: this.extractText(document, this.selectors.restaurantDetail.address),
                phone: this.extractText(document, this.selectors.restaurantDetail.phone),
                hours: this.extractText(document, this.selectors.restaurantDetail.hours),
                tags: this.extractTextArray(document, this.selectors.restaurantDetail.tags)
            };
            
            return { restaurant_detail: detail };
        }
        
        /**
         * 提取评论数据
         */
        extractReviews() {
            const reviews = [];
            const reviewElements = document.querySelectorAll(this.selectors.reviewList);
            
            reviewElements.forEach((element, index) => {
                try {
                    const review = {
                        id: `review_${index}`,
                        user: this.extractText(element, this.selectors.reviewItem.user),
                        rating: this.extractText(element, this.selectors.reviewItem.rating),
                        content: this.extractText(element, this.selectors.reviewItem.content),
                        date: this.extractText(element, this.selectors.reviewItem.date),
                        useful: this.extractText(element, this.selectors.reviewItem.useful)
                    };
                    
                    if (review.content) {
                        reviews.push(review);
                    }
                } catch (error) {
                    console.warn('[DianpingExtractor] 评论数据提取失败:', error);
                }
            });
            
            return { reviews, count: reviews.length };
        }
        
        /**
         * 提取通用数据
         */
        extractGenericData() {
            return {
                title: document.title,
                meta: {
                    description: document.querySelector('meta[name="description"]')?.content,
                    keywords: document.querySelector('meta[name="keywords"]')?.content
                },
                elementCount: document.querySelectorAll('*').length,
                textLength: document.body.innerText.length
            };
        }
        
        /**
         * 从元素中提取文本
         */
        extractText(parent, selector) {
            try {
                const element = parent.querySelector(selector);
                return element ? element.textContent.trim() : '';
            } catch (error) {
                return '';
            }
        }
        
        /**
         * 从元素中提取文本数组
         */
        extractTextArray(parent, selector) {
            try {
                const elements = parent.querySelectorAll(selector);
                return Array.from(elements).map(el => el.textContent.trim()).filter(text => text);
            } catch (error) {
                return [];
            }
        }
        
        /**
         * 提取图片URL
         */
        extractImage(parent, selector) {
            try {
                const img = parent.querySelector(selector);
                return img ? (img.src || img.dataset.src || '') : '';
            } catch (error) {
                return '';
            }
        }
        
        /**
         * 提取链接
         */
        extractLink(element) {
            try {
                const link = element.querySelector('a') || element.closest('a');
                return link ? link.href : '';
            } catch (error) {
                return '';
            }
        }
        
        /**
         * 计算数据哈希值
         */
        hashData(data) {
            return JSON.stringify(data).length + '_' + Object.keys(data).join('_');
        }
        
        /**
         * 停止监听
         */
        stop() {
            if (this.observer) {
                this.observer.disconnect();
                this.observer = null;
            }
            this.isActive = false;
            console.log('[DianpingExtractor] 数据提取器已停止');
        }
    }
    
    // 创建数据提取器实例
    const extractor = new DianpingDataExtractor();
    
    // 页面卸载时清理
    window.addEventListener('beforeunload', () => {
        extractor.stop();
    });
    
    // 导出到全局作用域
    window.DianpingDataExtractor = extractor;
    
})();