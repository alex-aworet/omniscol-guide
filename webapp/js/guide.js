/**
 * Guide Chat Module
 * Integrates the GuideAgent with the web interface
 */

const GuideChat = (function() {
    const state = {
        isLoading: false,
        messages: [],
        container: null,
        input: null,
        messagesDiv: null
    };

    function init() {
        // Create chat UI if it doesn't exist
        createChatUI();
        attachEventListeners();
    }

    function createChatUI() {
        // Create container
        const container = document.createElement('div');
        container.id = 'guide-chat-container';
        container.className = 'guide-chat-container';
        
        const html = `
            <div class="guide-chat">
                <div class="guide-chat-header">
                    <h3>Guide Assistant</h3>
                    <button class="guide-chat-close" id="guide-close">✕</button>
                </div>
                <div class="guide-chat-messages" id="guide-messages"></div>
                <div class="guide-chat-input-area">
                    <input 
                        type="text" 
                        id="guide-input" 
                        class="guide-chat-input" 
                        placeholder="Ask me anything..."
                        autocomplete="off"
                    />
                    <button id="guide-send" class="guide-chat-send">Send</button>
                </div>
            </div>
        `;
        
        container.innerHTML = html;
        document.body.appendChild(container);
        
        state.container = container;
        state.input = document.getElementById('guide-input');
        state.messagesDiv = document.getElementById('guide-messages');
    }

    function attachEventListeners() {
        const sendBtn = document.getElementById('guide-send');
        const closeBtn = document.getElementById('guide-close');
        
        sendBtn.addEventListener('click', handleSendMessage);
        state.input.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') handleSendMessage();
        });
        
        closeBtn.addEventListener('click', toggleChat);
        
        // Automatically send page summary when page loads
        generateAutoSummary();
    }

    async function getPageContext() {
        // Get current route from window location
        const route = window.location.pathname;
        
        // Try to determine active tab from page elements
        let activeTab = null;
        const tabElements = document.querySelectorAll('[data-tab-id], [role="tab"][aria-selected="true"]');
        if (tabElements.length > 0) {
            activeTab = tabElements[0].getAttribute('data-tab-id') || tabElements[0].getAttribute('aria-label');
        }
        
        // Get visible sections from DOM
        const visibleSections = [];
        document.querySelectorAll('[data-section-id][style*="display"], [data-section-id]:not([style*="display:none"])').forEach(section => {
            const sectionId = section.getAttribute('data-section-id');
            if (sectionId) {
                visibleSections.push(sectionId);
            }
        });
        
        return {
            route,
            active_tab: activeTab,
            visible_sections: visibleSections
        };
    }

    async function handleSendMessage() {
        const message = state.input.value.trim();
        if (!message || state.isLoading) return;
        
        // Add user message to UI
        addMessageToUI('user', message);
        state.input.value = '';
        state.isLoading = true;
        
        try {
            // Get page context
            const pageContext = await getPageContext();
            
            // Call the API
            const response = await fetch('/api/guide/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    route: pageContext.route,
                    active_tab: pageContext.active_tab,
                    visible_sections: pageContext.visible_sections
                })
            });
            
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                const errorDetail = errorData.detail || `HTTP ${response.status}`;
                
                // Provide helpful error messages
                let errorMessage = `Error: ${errorDetail}`;
                
                if (response.status === 500 && errorDetail.includes('Agent error')) {
                    if (errorDetail.includes('does not support tools')) {
                        errorMessage = '⚠️ Model does not support tools. Check GUIDE_SETUP.md for compatible models.';
                    } else if (errorDetail.includes('Could not connect')) {
                        errorMessage = '⚠️ Could not connect to Ollama. Make sure Ollama is running on localhost:11434. See GUIDE_SETUP.md';
                    } else if (errorDetail.includes('not found')) {
                        errorMessage = '⚠️ Model not found. Run: ollama pull mistral. See GUIDE_SETUP.md';
                    }
                }
                
                throw new Error(errorMessage);
            }
            
            const data = await response.json();
            const agentResponse = data.answer || data.response || data.message || 'No response';
            
            // Add agent response to UI
            addMessageToUI('agent', agentResponse);
            
        } catch (error) {
            console.error('Error calling guide chat:', error);
            addMessageToUI('error', error.message || 'An error occurred');
        } finally {
            state.isLoading = false;
        }
    }

    function addMessageToUI(role, content) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `guide-chat-message guide-chat-${role}`;
        messageDiv.textContent = content;
        state.messagesDiv.appendChild(messageDiv);
        
        // Scroll to bottom
        state.messagesDiv.scrollTop = state.messagesDiv.scrollHeight;
        
        state.messages.push({ role, content });
    }

    function toggleChat() {
        state.container?.classList.toggle('hidden');
    }

    function show() {
        state.container?.classList.remove('hidden');
    }

    function hide() {
        state.container?.classList.add('hidden');
    }

    async function generateAutoSummary() {
        try {
            // Get page context
            const pageContext = await getPageContext();
            
            // Call the auto-summary API with a timeout
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 second timeout
            
            const response = await fetch('/api/guide/auto-summary', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    route: pageContext.route,
                    active_tab: pageContext.active_tab,
                    visible_sections: pageContext.visible_sections
                }),
                signal: controller.signal
            });
            
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                console.warn('Auto-summary API returned error:', response.status);
                return;
            }
            
            const data = await response.json();
            const summary = data.summary;
            
            if (summary && summary.trim()) {
                // Add agent response to UI with a "Page Summary" prefix
                addMessageToUI('agent', `📄 Page Summary: ${summary}`);
                // Automatically show the chat when summary is received
                show();
            }
        } catch (error) {
            if (error.name === 'AbortError') {
                console.warn('Auto-summary request timed out');
            } else {
                console.warn('Could not generate auto-summary:', error.message);
            }
            // Silently fail - don't show error to user
        }
    }

    // --- Auto-summary on route change ---
    (function() {
        let lastRoute = window.location.pathname;
        function onRouteChange() {
            if (window.location.pathname !== lastRoute) {
                lastRoute = window.location.pathname;
                if (GuideChat && typeof GuideChat.init === 'function') {
                    // Remove previous summary messages
                    const messagesDiv = document.getElementById('guide-messages');
                    if (messagesDiv) {
                        Array.from(messagesDiv.querySelectorAll('.guide-chat-agent')).forEach(el => el.remove());
                    }
                    // Generate new summary
                    if (typeof GuideChat.generateAutoSummary === 'function') {
                        GuideChat.generateAutoSummary();
                    } else if (window.generateAutoSummary) {
                        window.generateAutoSummary();
                    }
                }
            }
        }
        // Patch pushState/replaceState
        const origPush = history.pushState;
        const origReplace = history.replaceState;
        history.pushState = function() { origPush.apply(this, arguments); window.dispatchEvent(new Event('locationchange')); };
        history.replaceState = function() { origReplace.apply(this, arguments); window.dispatchEvent(new Event('locationchange')); };
        window.addEventListener('popstate', () => window.dispatchEvent(new Event('locationchange')));
        window.addEventListener('locationchange', onRouteChange);
    })();

    return {
        init,
        show,
        hide,
        toggle: toggleChat,
        addMessage: addMessageToUI,
        generateAutoSummary
    };
})();

// Initialize when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => GuideChat.init());
} else {
    GuideChat.init();
}
