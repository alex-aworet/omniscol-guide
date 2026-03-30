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
    }

    async function handleSendMessage() {
        const message = state.input.value.trim();
        if (!message || state.isLoading) return;
        
        // Add user message to UI
        addMessageToUI('user', message);
        state.input.value = '';
        state.isLoading = true;
        
        try {
            // Get current tab info if available
            const currentTab = window.location.pathname;
            
            // Call the API
            const response = await fetch('/api/guide/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    message: message,
                    current_tab: currentTab
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

    return {
        init,
        show,
        hide,
        toggle: toggleChat,
        addMessage: addMessageToUI
    };
})();

// Initialize when document is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => GuideChat.init());
} else {
    GuideChat.init();
}
