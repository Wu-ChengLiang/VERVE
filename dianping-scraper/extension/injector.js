/**
 * Injected Script - Verve
 * 
 * This script is injected into the main world of the web page
 * to interact with elements created by the page's own JavaScript.
 * It directly mirrors the logic of the user-provided quick_fix_test.js.
 */

(function() {
    console.log('[Injector] Script running in main world.');

    // --- Communication with Content Script ---
    function reportResult(status, message) {
        console.log(`[Injector] Reporting result: ${status}`, message || '');
        window.dispatchEvent(new CustomEvent('verveInjectorResult', { 
            detail: { status, message } 
        }));
    }

    // --- Task Execution ---
    function executeTask(task) {
        console.log('[Injector] Executing task:', task);
        if (task.action === 'testAndSend') {
            performSend(task.text);
        } else {
            reportResult('failed', `Unknown task action: ${task.action}`);
        }
    }

    function performSend(textToSend) {
        console.log(`[Injector] Attempting to send text: "${textToSend}"`);
        try {
            const iframes = document.querySelectorAll('iframe');
            if (iframes.length === 0) {
                reportResult('failed', 'No iframes found.');
                return;
            }

            let sent = false;
            for (let i = 0; i < iframes.length; i++) {
                if (sent) break;
                try {
                    const doc = iframes[i].contentDocument;
                    if (!doc) continue;

                    const inputBox = doc.querySelector('pre[data-placeholder="请输入你要回复顾客的内容"].dzim-chat-input-container');
                    if (!inputBox) continue;
                    
                    console.log(`[Injector] Found input box in iframe ${i + 1}`);

                    const sendButton = findSendButton(doc);
                    if (sendButton) {
                        console.log(`[Injector] Found send button in iframe ${i + 1}`);
                        
                        inputBox.focus();
                        inputBox.textContent = textToSend;
                        inputBox.dispatchEvent(new Event('input', { bubbles: true }));

                        setTimeout(() => { // Short delay to allow UI to update (e.g., enable button)
                            if (sendButton.disabled) {
                                reportResult('failed', 'Send button is disabled.');
                                return;
                            }
                            sendButton.click();
                            sent = true;
                            console.log('[Injector] Clicked send button.');
                            
                            // Final check
                            setTimeout(() => {
                                if (inputBox.textContent === '' || inputBox.textContent !== textToSend) {
                                    reportResult('success', 'Message sent successfully.');
                                } else {
                                    reportResult('success', 'Button clicked, but input did not clear.');
                                }
                            }, 500);

                        }, 100);
                    }
                } catch (e) { /* ignore */ }
            }

            if (!sent) {
                 setTimeout(() => reportResult('failed', 'Could not find the input/send button.'), 100);
            }
        } catch (error) {
            reportResult('failed', `A critical error occurred: ${error.message}`);
        }
    }

    function findSendButton(doc) {
        const allButtons = doc.querySelectorAll('button.dzim-button.dzim-button-primary');
        for (const btn of allButtons) {
            if (btn.textContent.trim() === '发送') {
                return btn;
            }
        }
        return null;
    }

    // --- Main ---
    // Listen for the task from the content script
    window.addEventListener('verveInjectorTask', function(evt) {
        if (evt.detail) {
            executeTask(evt.detail);
        }
    }, { once: true });

})(); 