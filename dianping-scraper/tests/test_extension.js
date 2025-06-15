/**
 * 浏览器扩展测试脚本
 * 用于验证扩展的基本功能是否正常
 */

class ExtensionTester {
    constructor() {
        this.testResults = [];
        this.passed = 0;
        this.failed = 0;
    }
    
    /**
     * 运行所有测试
     */
    async runAllTests() {
        console.log('🧪 开始扩展功能测试...');
        
        // 测试manifest文件
        await this.testManifest();
        
        // 测试WebSocket管理器
        await this.testWebSocketManager();
        
        // 测试Content Script
        await this.testContentScript();
        
        // 测试Background Script
        await this.testBackgroundScript();
        
        // 测试存储功能
        await this.testStorage();
        
        // 显示测试结果
        this.showResults();
    }
    
    /**
     * 测试Manifest文件
     */
    async testManifest() {
        const testName = 'Manifest 配置';
        
        try {
            // 检查manifest是否可访问
            const manifest = chrome.runtime.getManifest();
            
            this.assert(manifest, 'Manifest 文件存在');
            this.assert(manifest.name === '大众点评数据提取器', '扩展名称正确');
            this.assert(manifest.version === '1.0.0', '版本号正确');
            this.assert(manifest.manifest_version === 3, 'Manifest版本正确');
            this.assert(manifest.permissions.includes('activeTab'), '包含必要权限');
            this.assert(manifest.content_scripts.length > 0, '配置了Content Scripts');
            
            this.pass(testName);
            
        } catch (error) {
            this.fail(testName, error.message);
        }
    }
    
    /**
     * 测试WebSocket管理器
     */
    async testWebSocketManager() {
        const testName = 'WebSocket 管理器';
        
        try {
            // 检查WebSocket管理器是否存在
            this.assert(typeof WebSocketManager === 'function', 'WebSocketManager 类存在');
            
            // 创建实例
            const wsManager = new WebSocketManager();
            this.assert(wsManager, 'WebSocket管理器实例创建成功');
            this.assert(typeof wsManager.connect === 'function', '包含connect方法');
            this.assert(typeof wsManager.sendMessage === 'function', '包含sendMessage方法');
            this.assert(typeof wsManager.disconnect === 'function', '包含disconnect方法');
            
            // 测试配置
            this.assert(wsManager.serverUrl === 'ws://localhost:8767', '服务器URL配置正确');
            this.assert(wsManager.reconnectInterval === 5000, '重连间隔配置正确');
            
            this.pass(testName);
            
        } catch (error) {
            this.fail(testName, error.message);
        }
    }
    
    /**
     * 测试Content Script
     */
    async testContentScript() {
        const testName = 'Content Script';
        
        try {
            // 检查DOM监听器
            this.assert(typeof MutationObserver !== 'undefined', 'MutationObserver 可用');
            
            // 检查选择器配置
            if (typeof DianpingDataExtractor !== 'undefined') {
                const extractor = new DianpingDataExtractor();
                this.assert(extractor.selectors, '选择器配置存在');
                this.assert(extractor.selectors.restaurantList, '餐厅列表选择器存在');
                this.assert(extractor.selectors.restaurantItem, '餐厅项目选择器存在');
            } else {
                console.warn('DianpingDataExtractor 在测试环境中不可用');
            }
            
            this.pass(testName);
            
        } catch (error) {
            this.fail(testName, error.message);
        }
    }
    
    /**
     * 测试Background Script
     */
    async testBackgroundScript() {
        const testName = 'Background Script';
        
        try {
            // 检查Chrome API
            this.assert(typeof chrome !== 'undefined', 'Chrome API 可用');
            this.assert(typeof chrome.runtime !== 'undefined', 'Runtime API 可用');
            this.assert(typeof chrome.tabs !== 'undefined', 'Tabs API 可用');
            this.assert(typeof chrome.storage !== 'undefined', 'Storage API 可用');
            
            // 检查事件监听器
            this.assert(typeof chrome.runtime.onInstalled !== 'undefined', '安装事件监听器可用');
            this.assert(typeof chrome.tabs.onUpdated !== 'undefined', '标签页更新监听器可用');
            
            this.pass(testName);
            
        } catch (error) {
            this.fail(testName, error.message);
        }
    }
    
    /**
     * 测试存储功能
     */
    async testStorage() {
        const testName = '存储功能';
        
        try {
            // 测试本地存储
            const testData = { test: 'value', timestamp: Date.now() };
            
            await new Promise((resolve, reject) => {
                chrome.storage.local.set({ testData }, () => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError);
                    } else {
                        resolve();
                    }
                });
            });
            
            const result = await new Promise((resolve, reject) => {
                chrome.storage.local.get(['testData'], (result) => {
                    if (chrome.runtime.lastError) {
                        reject(chrome.runtime.lastError);
                    } else {
                        resolve(result);
                    }
                });
            });
            
            this.assert(result.testData, '数据写入成功');
            this.assert(result.testData.test === 'value', '数据读取正确');
            
            // 清理测试数据
            await new Promise((resolve) => {
                chrome.storage.local.remove(['testData'], resolve);
            });
            
            this.pass(testName);
            
        } catch (error) {
            this.fail(testName, error.message);
        }
    }
    
    /**
     * 断言函数
     */
    assert(condition, message) {
        if (!condition) {
            throw new Error(message);
        }
    }
    
    /**
     * 标记测试通过
     */
    pass(testName) {
        this.testResults.push({ name: testName, status: 'PASS' });
        this.passed++;
        console.log(`✅ ${testName}: 通过`);
    }
    
    /**
     * 标记测试失败
     */
    fail(testName, error) {
        this.testResults.push({ name: testName, status: 'FAIL', error });
        this.failed++;
        console.error(`❌ ${testName}: 失败 - ${error}`);
    }
    
    /**
     * 显示测试结果
     */
    showResults() {
        console.log('\n📊 测试结果汇总:');
        console.log(`总计: ${this.testResults.length} 项测试`);
        console.log(`通过: ${this.passed} 项`);
        console.log(`失败: ${this.failed} 项`);
        
        if (this.failed === 0) {
            console.log('🎉 所有测试通过！扩展功能正常');
        } else {
            console.log('⚠️ 部分测试失败，请检查扩展配置');
        }
        
        return {
            total: this.testResults.length,
            passed: this.passed,
            failed: this.failed,
            success: this.failed === 0
        };
    }
}

// 在扩展环境中运行测试
if (typeof chrome !== 'undefined' && chrome.runtime) {
    const tester = new ExtensionTester();
    
    // 等待DOM加载完成后运行测试
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => {
            tester.runAllTests();
        });
    } else {
        tester.runAllTests();
    }
} else {
    console.warn('测试脚本需要在Chrome扩展环境中运行');
}

// 导出测试器类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ExtensionTester;
} 