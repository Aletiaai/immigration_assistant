class ChatInterface {
    constructor() {
        this.sessionId = 'default';
        this.isLoading = false;
<<<<<<< HEAD
        this.attachedFile = null;
=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
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
<<<<<<< HEAD
        this.adminBtn = document.getElementById('admin-btn');
        this.dropZone = document.getElementById('drop-zone');
        this.attachFileBtn = document.getElementById('attach-file-btn');
        this.fileInput = document.getElementById('file-input');
        this.fileNameSpan = document.getElementById('file-name');
    }

    attachEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.clearBtn.addEventListener('click', () => this.clearChat());
        this.adminBtn.addEventListener('click', () => {
            window.location.href = '/login';
        });
        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                if (e.shiftKey) {
                    return;
                } else {
=======
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
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
                    e.preventDefault();
                    this.sendMessage();
                }
            }
        });
<<<<<<< HEAD
=======

        // Auto-resize textarea
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });
<<<<<<< HEAD
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('dragover');
        });
        this.dropZone.addEventListener('dragleave', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
        });
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                this.handleFile(files[0]);
            }
        });
        this.attachFileBtn.addEventListener('click', () => {
            this.fileInput.click();
        });
        this.fileInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                this.handleFile(e.target.files[0]);
            }
        });
    }

    handleFile(file) {
        if (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.docx')) {
            this.attachedFile = file;
            this.fileNameSpan.textContent = `Attached: ${file.name}`;
        } else {
            alert('Only PDF and DOCX files are supported.');
            this.fileInput.value = '';
        }
=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        
        if (!message || this.isLoading) {
            return;
        }

        try {
            this.setLoading(true);
<<<<<<< HEAD
            this.addMessage(message, 'user', [], this.attachedFile ? this.attachedFile.name : null);
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';
            this.fileNameSpan.textContent = '';
            this.fileInput.value = '';

            let result;
            if (this.attachedFile) {
                const formData = new FormData();
                formData.append('file', this.attachedFile);
                formData.append('message', message);
                formData.append('session_id', this.sessionId);
                formData.append('instructions', '');
                const response = await fetch('/api/chat/document', {
                    method: 'POST',
                    body: formData
                });
                if (!response.ok) {
                    let errorData;
                    try {
                        errorData = await response.json();
                    } catch {
                        errorData = { detail: 'Failed to parse error response' };
                    }
                    console.error('API Error Response:', {
                        status: response.status,
                        statusText: response.statusText,
                        errorData,
                        responseText: await response.text()
                    });
                    throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
                }
                result = await response.json();
                console.log('Parsed API Response (Document):', result);
            } else {
                result = await this.callChatAPI(message);
                console.log('Parsed API Response (Text):', result);
            }

            // Validate response structure
            if (!result.response || !Array.isArray(result.sources) || !result.language || !result.timestamp) {
                console.error('Invalid Response Structure:', result);
                throw new Error('Invalid response structure from API');
            }

            this.addMessage(result.response, 'assistant', result.sources, this.attachedFile ? result.document_filename : null);

        } catch (error) {
            console.error('Chat error:', error.message, error.stack);
=======
            this.addMessage(message, 'user');
            this.messageInput.value = '';
            this.messageInput.style.height = 'auto';

            const response = await this.callChatAPI(message);
            this.addMessage(response.response, 'assistant', response.sources);

        } catch (error) {
            console.error('Chat error:', error);
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
            this.addMessage(
                'Sorry, there was an error processing your message. Please try again.',
                'assistant'
            );
            this.updateStatus('Error', 'error');
        } finally {
            this.setLoading(false);
<<<<<<< HEAD
            this.attachedFile = null;
=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
        }
    }

    async callChatAPI(message) {
<<<<<<< HEAD
        try {
            const requestBody = {
                message: message,
                session_id: this.sessionId,
                timestamp: new Date().toISOString()
            };
            console.log('Sending Request:', requestBody);

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            if (!response.ok) {
                let errorData;
                try {
                    errorData = await response.json();
                } catch {
                    errorData = { detail: 'Failed to parse error response' };
                }
                console.error('API Error Response:', {
                    status: response.status,
                    statusText: response.statusText,
                    errorData,
                    responseText: await response.text()
                });
                throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
            }

            let result;
            try {
                result = await response.json();
                console.log('Parsed API Response:', result);
            } catch (e) {
                console.error('Fetch Response Parsing Error:', e, 'Raw Response:', await response.text());
                throw new Error('Failed to parse API response JSON');
            }

            return result;
        } catch (error) {
            console.error('Fetch error in callChatAPI:', error.message, error.stack);
            throw error;
        }
    }

    addMessage(content, sender, sources = [], documentFilename = null) {
=======
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

        return await response.json();
    }

    addMessage(content, sender, sources = []) {
        // Remove welcome message if it exists
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) {
            welcomeMessage.remove();
        }

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
<<<<<<< HEAD
        
        if (sender === 'assistant') {
            messageContent.innerHTML = this.formatAssistantMessage(content);
            messageDiv.setAttribute('data-sources', JSON.stringify(sources));
            this.addCitationHandlers(messageContent, sources);
        } else {
            messageContent.textContent = content;
        }

        messageDiv.appendChild(messageContent);

        if (documentFilename) {
            const docInfo = document.createElement('div');
            docInfo.className = 'document-info';
            docInfo.textContent = `Based on: ${documentFilename}`;
            messageDiv.appendChild(docInfo);
        }

=======
        messageContent.textContent = content;

        messageDiv.appendChild(messageContent);

        // Add sources if available (for assistant messages)
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
        if (sender === 'assistant' && sources && sources.length > 0) {
            const sourcesDiv = document.createElement('div');
            sourcesDiv.className = 'message-sources';
            sourcesDiv.innerHTML = `<strong>Sources:</strong> ${sources.length} document(s) referenced`;
            messageDiv.appendChild(sourcesDiv);
        }

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

<<<<<<< HEAD
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
        const existingPopup = document.querySelector('.citation-popup');
        if (existingPopup) {
            existingPopup.remove();
        }

        const popup = document.createElement('div');
        popup.className = 'citation-popup';
        popup.innerHTML = `
            <div class="citation-content">
                <button class="citation-close">×</button>
                <h4>${source.header || 'Source Reference'}</h4>
                <div class="citation-text">${source.original_content || source.content || source.text || 'Source content not available'}</div>
            </div>
        `;

        document.body.appendChild(popup);

        const rect = citationElement.getBoundingClientRect();
        popup.style.top = (rect.bottom + window.scrollY + 10) + 'px';
        popup.style.left = Math.max(10, rect.left + window.scrollX - 150) + 'px';

        popup.querySelector('.citation-close').addEventListener('click', () => popup.remove());
        popup.addEventListener('click', (e) => {
            if (e.target === popup) popup.remove();
        });
    }

    formatAssistantMessage(content) {
        let formattedContent = content.replace(/\[(\d+)\]/g, '<span class="citation" data-source="$1">[$1]</span>');
        const paragraphs = formattedContent.split('\n').filter(p => p.trim());
        
        return paragraphs.map(paragraph => {
            paragraph = paragraph.trim();
            paragraph = paragraph.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
            return `<p>${paragraph}</p>`;
        }).join('');
    }

=======
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
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
<<<<<<< HEAD
        this.statusElement.className = '';
        
=======
        
        // Remove existing status classes
        this.statusElement.className = '';
        
        // Add appropriate status class
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
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
<<<<<<< HEAD
=======
                // Clear chat messages
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
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

<<<<<<< HEAD
document.addEventListener('DOMContentLoaded', () => {
    const chat = new ChatInterface();
    chat.checkSystemHealth();
=======
// Initialize chat interface when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    const chat = new ChatInterface();
    
    // Check system health on startup
    chat.checkSystemHealth();
    
    // Focus on input field
>>>>>>> 4499d3e (The initial version of the RAG is running smoothly)
    chat.messageInput.focus();
});