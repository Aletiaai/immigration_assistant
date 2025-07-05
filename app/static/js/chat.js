// Path: app/static/js/chat.js

class ChatInterface {
    constructor() {
        this.sessionId = 'default-' + Date.now(); // Create a unique session ID
        this.isLoading = false;
        this.attachedFile = null;
        this.initializeElements();
        this.attachEventListeners();
        this.checkSystemHealth();
    }

    initializeElements() {
        this.chatMessages = document.getElementById('chat-messages');
        this.messageInput = document.getElementById('message-input');
        this.sendBtn = document.getElementById('send-btn');
        this.clearBtn = document.getElementById('clear-chat');
        this.adminBtn = document.getElementById('admin-btn');
        this.dropZone = document.getElementById('drop-zone');
        this.attachFileBtn = document.getElementById('attach-file-btn');
        this.fileInput = document.getElementById('file-input');
        this.fileNameSpan = document.getElementById('file-name');
    }

    attachEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.clearBtn.addEventListener('click', () => this.clearChat());
        this.adminBtn.addEventListener('click', () => { window.location.href = '/login'; });

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        this.messageInput.addEventListener('input', () => {
            this.messageInput.style.height = 'auto';
            this.messageInput.style.height = this.messageInput.scrollHeight + 'px';
        });

        // Drag and Drop Listeners
        this.dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            this.dropZone.classList.add('dragover');
        });
        this.dropZone.addEventListener('dragleave', () => this.dropZone.classList.remove('dragover'));
        this.dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            this.dropZone.classList.remove('dragover');
            if (e.dataTransfer.files.length > 0) {
                this.handleFile(e.dataTransfer.files[0]);
            }
        });

        // Attach Button and File Input Listeners
        this.attachFileBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', () => {
            if (this.fileInput.files.length > 0) {
                this.handleFile(this.fileInput.files[0]);
            }
        });
    }

    handleFile(file) {
        // Corrected JavaScript method name: endsWith (with a capital W)
        if (file && (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.docx'))) {
            this.attachedFile = file;
            this.fileNameSpan.textContent = `Attached: ${file.name}`;
        } else {
            alert('Only PDF and DOCX files are supported.');
            this.attachedFile = null;
            this.fileNameSpan.textContent = '';
            this.fileInput.value = ''; // Clear the file input
        }
    }

    async sendMessage() {
        const message = this.messageInput.value.trim();
        if ((!message && !this.attachedFile) || this.isLoading) {
            return;
        }

        this.setLoading(true);
        const userMessage = message || `File attached: ${this.attachedFile.name}`;
        this.addMessage(userMessage, 'user', [], this.attachedFile ? this.attachedFile.name : null);

        // Store file to send, then clear UI state immediately
        const fileToSend = this.attachedFile;
        this.messageInput.value = '';
        this.messageInput.style.height = 'auto';
        this.fileNameSpan.textContent = '';
        this.fileInput.value = '';
        this.attachedFile = null;

        try {
            let result;
            if (fileToSend) {
                const formData = new FormData();
                formData.append('file', fileToSend);
                formData.append('message', message); // Send message even if empty, API handles it
                formData.append('session_id', this.sessionId);
                
                const response = await fetch('/api/chat/document', { method: 'POST', body: formData });
                if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
                result = await response.json();
            } else {
                result = await this.callChatAPI(message);
            }
            this.addMessage(result.response, 'assistant', result.sources, result.document_filename);
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage('Sorry, there was an error. Please check the console and try again.', 'assistant');
        } finally {
            this.setLoading(false);
        }
    }

    async callChatAPI(message) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, session_id: this.sessionId })
        });
        if (!response.ok) throw new Error(`HTTP error! Status: ${response.status}`);
        return await response.json();
    }

    addMessage(content, sender, sources = [], documentFilename = null) {
        const welcomeMessage = this.chatMessages.querySelector('.welcome-message');
        if (welcomeMessage) welcomeMessage.remove();

        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}`;

        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        if (sender === 'assistant') {
            messageContent.innerHTML = this.formatAssistantMessage(content);
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

        this.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();
    }

    formatAssistantMessage(content) {
        let formattedContent = content.replace(/\[(\d+)\]/g, '<span class="citation" data-source="$1">[$1]</span>');
        const paragraphs = formattedContent.split('\n').filter(p => p.trim());
        return paragraphs.map(p => `<p>${p.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')}</p>`).join('');
    }

    addCitationHandlers(messageContent, sources) {
        messageContent.querySelectorAll('.citation').forEach(citation => {
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
        document.querySelector('.citation-popup')?.remove(); // Close any existing popup

        const popup = document.createElement('div');
        popup.className = 'citation-popup';
        popup.innerHTML = `
            <div class="citation-content">
                <button class="citation-close">×</button>
                <h4>${source.header || 'Source Reference'}</h4>
                <div class="citation-text">${source.original_content || 'Content not available.'}</div>
            </div>
        `;
        document.body.appendChild(popup);

        const rect = citationElement.getBoundingClientRect();
        popup.style.top = `${rect.bottom + window.scrollY + 5}px`;
        popup.style.left = `${rect.left + window.scrollX}px`;

        popup.querySelector('.citation-close').addEventListener('click', () => popup.remove());
        document.addEventListener('click', (e) => {
            if (!popup.contains(e.target) && e.target !== citationElement) {
                popup.remove();
            }
        }, { once: true });
    }

    scrollToBottom() {
        this.chatMessages.scrollTop = this.chatMessages.scrollHeight;
    }

    setLoading(loading) {
        this.isLoading = loading;
        this.sendBtn.disabled = loading;
        this.messageInput.disabled = loading;
        this.sendBtn.innerHTML = loading ? '<div class="loading"></div>' : 'Send';
    }

    async clearChat() {
        try {
            await fetch(`/api/chat/history/${this.sessionId}`, { method: 'DELETE' });
            this.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h2>Immigration Law Assistant</h2>
                    <p>Ask me questions about immigration law or upload a document to discuss.</p>
                </div>`;
        } catch (error) {
            console.error('Clear chat error:', error);
        }
    }

    async checkSystemHealth() {
        // Placeholder for a system health check if needed
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});