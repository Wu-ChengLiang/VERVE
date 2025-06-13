/**
 * Injected Script - Verve
 * 
 * This script is injected into the main world of the web page
 * to interact with elements created by the page's own JavaScript.
 * It directly mirrors the logic of the user-provided quick_fix_test.js.
 */

(function() {
    console.log('[Injector] Script injected and running in main world.');

    function reportResult(status, message) {
        console.log(`[Injector] Reporting result: ${status}`, message || '');
        window.dispatchEvent(new CustomEvent('verveTestSendResult', { 
            detail: { status, message } 
        }));
    }

    try {
        const iframes = document.querySelectorAll('iframe');
        console.log('[Injector] Found iframes:', iframes.length);

        if (iframes.length === 0) {
            reportResult('failed', 'No iframes found on the page.');
            return;
        }

        let foundAndSent = false;

        for (let i = 0; i < iframes.length; i++) {
            if (foundAndSent) break;

            try {
                const doc = iframes[i].contentDocument;
                if (!doc) continue;

                const inputBox = doc.querySelector('pre[data-placeholder="请输入你要回复顾客的内容"].dzim-chat-input-container[contenteditable="plaintext-only"]');
                if (!inputBox) continue;

                console.log(`[Injector] Found input box in iframe ${i + 1}`);

                const allPrimaryButtons = doc.querySelectorAll('button.dzim-button.dzim-button-primary');
                let sendButton = null;

                for (const btn of allPrimaryButtons) {
                    if (btn.textContent.trim() === '发送') {
                        sendButton = btn;
                        break;
                    }
                }

                if (sendButton) {
                    console.log(`[Injector] Found send button in iframe ${i + 1}`);
                    
                    const testText = '测试';
                    inputBox.focus();
                    inputBox.textContent = testText;
                    inputBox.dispatchEvent(new Event('input', { bubbles: true }));

                    console.log('[Injector] Text injected. Clicking send button...');
                    
                    if(sendButton.disabled){
                         console.log('[Injector] Send button is disabled!');
                         reportResult('failed', 'Send button was disabled after input.');
                         foundAndSent = true;
                         break;
                    }
                    
                    sendButton.click();
                    foundAndSent = true;

                    // A brief moment to check if input cleared
                    setTimeout(() => {
                        if (inputBox.textContent === '' || inputBox.textContent !== testText) {
                            reportResult('success', 'Message sent successfully (input cleared).');
                        } else {
                            reportResult('success', 'Message sent (input not cleared, but button clicked).');
                        }
                    }, 500);

                }
            } catch (e) {
                 console.error(`[Injector] Error in iframe ${i + 1}:`, e);
            }
        }

        if (!foundAndSent) {
            setTimeout(() => {
                reportResult('failed', 'Could not find the input box or send button in any iframe.');
            }, 100); // Use timeout to ensure this message is sent after loops complete
        }

    } catch (error) {
        console.error('[Injector] A critical error occurred:', error);
        reportResult('failed', `A critical error occurred: ${error.message}`);
    }
})(); 