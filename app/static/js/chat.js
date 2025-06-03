class ChatInterface {
    constructor() {
        this.sessionId = 'default';
        this.isLoading = false;
        this.initializeElements();
        this.attachEventListeners();
        this.updateStatus();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.clearBtn = document.getElementById('clear-chat');
        this.statusElement = document.getElementById('status');
    }

    attachEventListeners() {
        // Send button click
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        
        // Clear chat button
        this.clearBtn.addEventListener('click', () => this.clearChat());
        
        // Enter key handling
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.shiftKey) {
                    // Allow new line with Shift+Enter
                    return;
                } else {
                    // Send message with Enter
                    e.preventDefault();
                    this.sendMessage();
                }
            }
        });

        // Auto-resize textarea
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isLoading) {
            return;
        }

        try {
            this.setLoading(true);
            this.addMessage(message, 'user');
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';

            const response = await this.callChatAPI(message);
            this.addMessage(response.response, 'assistant', response.sources);

        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage(
                'Sorry, there was an error processing your message. Please try again.',
                'assistant'
            );
            this.updateStatus('Error', 'error');
        } finally {
            this.setLoading(false);
        }
    }

    async callChatAPI(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                message: message,
                timestamp: new Date().toISOString()
            })
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || `HTTP ${response.status}`);
        }

        const result = await response.json();
        console.log('API Response:', result); // Debug line
        return result;
    }

    addMessage(content, sender, sources = []) {
    // Remove welcome message if it exists
    const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
    if (welcomeMessage) {
        welcomeMessage.remove();
    }

    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${sender}`;

    const messageContent = document.createElement('div');
    messageContent.className = 'message-content';
    
    // Format the content for better readability
    if (sender === 'assistant') {
        messageContent.innerHTML = this.formatAssistantMessage(content);
        // Store sources data for citation popups
        messageDiv.setAttribute('data-sources', JSON.stringify(sources));
        // Add click handlers for citations
        this.addCitationHandlers(messageContent, sources);
    } else {
        messageContent.textContent = content;
    }

    messageDiv.appendChild(messageContent);

    // Add sources if available (for assistant messages)
    if (sender === 'assistant' && sources && sources.length > 0) {
        const sourcesDiv = document.createElement('div');
        sourcesDiv.className = 'message-sources';
        sourcesDiv.innerHTML = `<strong>Sources:</strong> ${sources.length} document(s) referenced`;
        messageDiv.appendChild(sourcesDiv);
    }

    this.chatMessages.appendChild(messageDiv);
    this.scrollToBottom();
}

addCitationHandlers(messageContent, sources) {
    const citations = messageContent.querySelectorAll('.citation');
    citations.forEach(citation => {
        citation.addEventListener('click', (e) => {
            e.preventDefault();
            const sourceIndex = parseInt(citation.getAttribute('data-source')) - 1;
            if (sources && sources[sourceIndex]) {
                this.showCitationPopup(sources[sourceIndex], citation);
            }
        });
    });
}

showCitationPopup(source, citationElement) {
    // Remove existing popup
    const existingPopup = document.querySelector('.citation-popup');
    if (existingPopup) {
        existingPopup.remove();
    }

    // Create popup
    const popup = document.createElement('div');
    popup.className = 'citation-popup';
    popup.innerHTML = `
        <div class="citation-content">
            <button class="citation-close">&times;</button>
            <h4>${source.header || 'Source Reference'}</h4>
            <div class="citation-text">${source.original_content || source.content || source.text || 'Source content not available'}</div>
        </div>
    `;

    document.body.appendChild(popup);

    // Position popup near citation
    const rect = citationElement.getBoundingClientRect();
    popup.style.top = (rect.bottom + window.scrollY + 10) + 'px';
    popup.style.left = Math.max(10, rect.left + window.scrollX - 150) + 'px';

    // Close handlers
    popup.querySelector('.citation-close').addEventListener('click', () => popup.remove());
    popup.addEventListener('click', (e) => {
        if (e.target === popup) popup.remove();
    });
}

formatAssistantMessage(content) {
    // Replace citation patterns [1], [2], etc. with clickable spans
    let formattedContent = content.replace(/\[(\d+)\]/g, '<span class="citation" data-source="$1">[$1]</span>');
    
    // Split on single line breaks and filter empty lines
    const paragraphs = formattedContent.split('\n').filter(p => p.trim());
    
    return paragraphs.map(paragraph => {
        paragraph = paragraph.trim();
        
        // Handle bold text (**text**)
        paragraph = paragraph.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        
        // Return as paragraph with proper spacing
        return `<p>${paragraph}</p>`;
    }).join('');
}



    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.sendBtn.disabled = loading;
        this.messageInput.disabled = loading;

        if (loading) {
            this.sendBtn.innerHTML = '<div class="loading"></div>';
            this.updateStatus('Processing...', 'processing');
        } else {
            this.sendBtn.textContent = 'Send';
            this.updateStatus('Ready', 'ready');
        }
    }

    updateStatus(text = 'Ready', type = 'ready') {
        this.statusElement.textContent = text;
        
        // Remove existing status classes
        this.statusElement.className = '';
        
        // Add appropriate status class
        switch (type) {
            case 'ready':
                this.statusElement.style.background = '#48bb78';
                break;
            case 'processing':
                this.statusElement.style.background = '#ed8936';
                break;
            case 'error':
                this.statusElement.style.background = '#f56565';
                break;
            default:
                this.statusElement.style.background = '#48bb78';
        }
    }

    async clearChat() {
        try {
            const response = await fetch(`/api/chat/history/${this.sessionId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                // Clear chat messages
                this.chatMessages.innerHTML = `
                    <div class="welcome-message">
                        <h2>Immigration Law Assistant</h2>
                        <p>Ask me any questions about immigration processes and laws.</p>
                        <p>You can ask questions in English or Spanish - I'll respond in the same language.</p>
                        <div class="example-questions">
                            <p><strong>Example questions:</strong></p>
                            <ul>
                                <li>"What documents do I need for permanent residency?"</li>
                                <li>"¿Cuáles son los requisitos para la ciudadanía?"</li>
                                <li>"How long does the visa process take?"</li>
                            </ul>
                        </div>
                    </div>
                `;
                this.updateStatus('Chat cleared', 'ready');
            } else {
                throw new Error('Failed to clear chat');
            }
        } catch (error) {
            console.error('Clear chat error:', error);
            this.updateStatus('Clear failed', 'error');
        }
    }

    async checkSystemHealth() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                this.updateStatus('Ready', 'ready');
            } else {
                this.updateStatus('System issues', 'error');
            }
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateStatus('Connection error', 'error');
        }
    }
}

// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const chat = new ChatInterface();
    
    // Check system health on startup
    chat.checkSystemHealth();
    
    // Focus on input field
    chat.messageInput.focus();
});