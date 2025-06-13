// 快速修复测试 - 使用正确的按钮选择器
console.log('🔧 快速修复测试开始...');

function quickFixTest() {
    console.log('\n🎯 运行快速修复测试...');
    
    // 获取iframe中的元素
    const iframes = document.querySelectorAll('iframe');
    console.log('🔍 找到iframe数量:', iframes.length);
    
    for (let i = 0; i < iframes.length; i++) {
        try {
            const doc = iframes[i].contentDocument;
            if (!doc) continue;
            
            console.log(`\n📄 检查iframe ${i + 1}:`, doc.URL);
            
            // 查找输入框
            const inputBox = doc.querySelector('pre[data-placeholder="请输入你要回复顾客的内容"].dzim-chat-input-container[contenteditable="plaintext-only"]');
            console.log('📝 输入框:', inputBox);
            
            if (inputBox) {
                // 使用修复后的按钮选择器
                console.log('\n🔘 查找发送按钮（使用正确选择器）...');
                
                // 方法1: 直接查找dzim-button-primary
                let sendButton = doc.querySelector('button.dzim-button.dzim-button-primary');
                console.log('  - 第一个primary按钮:', sendButton);
                
                // 方法2: 查找所有primary按钮，选择文本为"发送"的
                const allPrimaryButtons = doc.querySelectorAll('button.dzim-button.dzim-button-primary');
                console.log('  - 所有primary按钮数量:', allPrimaryButtons.length);
                
                for (let j = 0; j < allPrimaryButtons.length; j++) {
                    const btn = allPrimaryButtons[j];
                    const text = btn.textContent.trim();
                    console.log(`    [${j}] 按钮文本: "${text}", 类名: "${btn.className}"`);
                    
                    if (text === '发送') {
                        sendButton = btn;
                        console.log(`✅ 找到正确的发送按钮: 第${j}个`);
                        break;
                    }
                }
                
                if (sendButton) {
                    console.log('\n🧪 开始测试注入...');
                    const testText = `修复测试消息 - ${new Date().toLocaleTimeString()}`;
                    
                    // 设置文本
                    inputBox.focus();
                    inputBox.textContent = testText;
                    
                    // 触发事件
                    const inputEvent = new Event('input', { bubbles: true });
                    inputBox.dispatchEvent(inputEvent);
                    
                    console.log('✅ 文本设置完成:', inputBox.textContent);
                    console.log('🔘 发送按钮状态:');
                    console.log('  - disabled:', sendButton.disabled);
                    console.log('  - 可见:', getComputedStyle(sendButton).display !== 'none');
                    
                    // 询问是否点击发送
                    if (confirm(`修复测试完成！\n\n输入框内容: ${testText}\n\n是否点击发送按钮测试？`)) {
                        console.log('🚀 点击发送按钮...');
                        
                        // 多种点击方式
                        sendButton.focus();
                        sendButton.click();
                        
                        // 也触发鼠标事件
                        const clickEvent = new MouseEvent('click', {
                            bubbles: true,
                            cancelable: true,
                            view: window
                        });
                        sendButton.dispatchEvent(clickEvent);
                        
                        console.log('✅ 发送按钮已点击！');
                        
                        // 检查是否有新消息
                        setTimeout(() => {
                            console.log('\n📜 检查是否发送成功...');
                            const currentContent = inputBox.textContent;
                            console.log('输入框当前内容:', currentContent);
                            
                            if (currentContent === '' || currentContent !== testText) {
                                console.log('🎉 可能发送成功！输入框已清空或内容改变');
                            } else {
                                console.log('⚠️ 输入框内容未变，可能需要其他触发方式');
                            }
                        }, 1000);
                        
                    } else {
                        console.log('⏸️ 用户取消发送测试');
                    }
                    
                    return true; // 测试完成
                } else {
                    console.log('❌ 未找到发送按钮');
                }
            }
        } catch (e) {
            console.log(`❌ 无法访问iframe ${i + 1}:`, e.message);
        }
    }
    
    console.log('❌ 未找到可用的输入框和发送按钮');
    return false;
}

// 暴露函数
window.quickFixTest = quickFixTest;

console.log('\n📋 快速修复测试命令:');
console.log('  - quickFixTest() - 运行快速修复测试');

console.log('\n🔧 运行 quickFixTest() 开始测试！'); 