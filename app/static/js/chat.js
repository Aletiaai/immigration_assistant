// Path: app/static/js/chat.js

class ChatInterface {
    constructor() {
        // This is the first thing we do: check for a login token
        this.token = localStorage.getItem('user_token');
        if (!this.token) {
            // If no token, redirect to login immediately
            window.location.href = '/login';
            return; // Stop execution
        }

        this.sessionId = 'session-' + Date.now(); // Start a new session for this user
        this.isLoading = false;
        this.attachedFile = null;

        this.initializeElements();
        this.attachEventListeners();
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
        this.logoutBtn = document.getElementById('logout-btn');
    }

    attachEventListeners() {
        this.sendBtn.addEventListener('click', () => this.sendMessage());
        this.clearBtn.addEventListener('click', () => this.clearChat());
        
        if (this.adminBtn) {
            this.adminBtn.addEventListener('click', () => { window.location.href = '/documents'; });
        }

        this.messageInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

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
        this.attachFileBtn.addEventListener('click', () => this.fileInput.click());
        this.fileInput.addEventListener('change', () => {
            if (this.fileInput.files.length > 0) {
                this.handleFile(this.fileInput.files[0]);
            }
        });

        if (this.logoutBtn) {
            this.logoutBtn.addEventListener('click', () => this.handleLogout());
        }
    }
    
    handleFile(file) {
        if (file && (file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.docx'))) {
            this.attachedFile = file;
            this.fileNameSpan.textContent = `Attached: ${file.name}`;
        } else {
            alert('Only PDF and DOCX files are supported.');
            this.attachedFile = null;
            this.fileNameSpan.textContent = '';
            this.fileInput.value = '';
        }
    }


    async sendMessage() {
        const message = this.messageInput.value.trim();
        if ((!message && !this.attachedFile) || this.isLoading) return;

        this.setLoading(true);
        const userMessage = message || `File attached: ${this.attachedFile.name}`;
        this.addMessage(userMessage, 'user');

        const fileToSend = this.attachedFile;
        this.messageInput.value = '';
        this.fileNameSpan.textContent = '';
        this.fileInput.value = '';
        this.attachedFile = null;

        try {
            let result;
            const headers = { 'Authorization': `Bearer ${this.token}` };

            if (fileToSend) {
                const formData = new FormData();
                formData.append('file', fileToSend);
                formData.append('message', message);
                formData.append('session_id', this.sessionId);
                
                const response = await fetch('/api/chat/document', { method: 'POST', body: formData, headers: headers });
                if (!response.ok) {
                    const errorData = await response.json();
                    throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
                }
                result = await response.json();
            } else {
                result = await this.callChatAPI(message, headers);
            }
            this.addMessage(result.response, 'assistant', result.sources, result.document_filename);
        } catch (error) {
            console.error('Chat error:', error);
            this.addMessage(`Sorry, there was an error: ${error.message}`, 'assistant');
        } finally {
            this.setLoading(false);
        }
    }

    async callChatAPI(message, headers) {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { ...headers, 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message, session_id: this.sessionId })
        });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.detail || `HTTP error! Status: ${response.status}`);
        }
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
        // Convert markdown-style citations [1] to clickable HTML spans
        let formattedContent = content.replace(/\[(\d+)\]/g, '<span class="citation" data-source="$1">[$1]</span>');
        // Split by newlines to create paragraphs
        const paragraphs = formattedContent.split('\n').filter(p => p.trim());
        // Wrap each line in a <p> tag and handle bolding
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
        document.querySelector('.citation-popup')?.remove();

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
            const headers = { 'Authorization': `Bearer ${this.token}` };
            await fetch(`/api/chat/history/${this.sessionId}`, { method: 'DELETE', headers: headers });
            this.chatMessages.innerHTML = `
                <div class="welcome-message">
                    <h2>Immigration Law Assistant</h2>
                    <p>Ask a question or upload a document to begin.</p>
                </div>`;
        } catch (error) {
            console.error('Clear chat error:', error);
        }
    }

    handleLogout() {
        localStorage.removeItem('user_token'); // Remove the user's token
        window.location.href = '/login'; // Redirect to the login page
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new ChatInterface();
});