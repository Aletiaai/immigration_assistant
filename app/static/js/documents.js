// Path: app/static/js/document.js

document.addEventListener('DOMContentLoaded', async () => {
    // This script requires an admin token to function.
    const token = localStorage.getItem('admin_token');

    // If no token is found, redirect to the login page immediately.
    if (!token) {
        window.location.href = '/login';
        return;
    }

    // Verify the token with the backend to ensure it's still valid.
    try {
        const response = await fetch('/api/auth/verify', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        // If the token is invalid (e.g., expired), clear it and redirect to login.
        if (!response.ok) {
            localStorage.removeItem('admin_token');
            window.location.href = '/login';
            return;
        }

        // If the token is valid, initialize the page's functionality.
        initializeDocumentManagement();
    } catch (error) {
        console.error('Authentication check failed:', error);
        localStorage.removeItem('admin_token');
        window.location.href = '/login';
    }
});

// This function sets up the entire document management page.
function initializeDocumentManagement() {
    const fileInput = document.getElementById('file-input');
    const uploadBtn = document.getElementById('upload-btn');
    const uploadStatusEl = document.getElementById('upload-status');
    const documentListEl = document.getElementById('document-list');
    const listStatusEl = document.getElementById('list-status');
    const refreshDocsBtn = document.getElementById('refresh-docs-btn');
    const kbChunksEl = document.getElementById('kb-chunks');
    const kbReadyStatusEl = document.getElementById('kb-ready-status');
    const kbStatusMessageEl = document.getElementById('kb-status-message');
    const refreshKbStatusBtn = document.getElementById('refresh-kb-status-btn');

    const API_BASE_URL = '/api/documents';
    const AUTH_HEADER = { 'Authorization': `Bearer ${localStorage.getItem('admin_token')}` };

    // --- Utility Functions ---
    const showStatusMessage = (element, message, type = 'info') => {
        element.textContent = message;
        element.className = `status-message ${type}`;
        element.style.display = 'block';
    };

    const clearStatusMessage = (element) => {
        element.textContent = '';
        element.style.display = 'none';
    };

    const setLoading = (button, isLoading) => {
        button.disabled = isLoading;
        if (isLoading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<div class="spinner-small"></div> Loading...';
        } else {
            button.innerHTML = button.dataset.originalText || button.innerHTML;
        }
    };

    // Add a smaller spinner style for buttons
    const styleSheet = document.createElement("style");
    styleSheet.innerText = `.spinner-small { border: 2px solid rgba(0,0,0,0.1); width: 16px; height: 16px; border-radius: 50%; border-left-color: #667eea; animation: spin 0.8s ease infinite; display: inline-block; vertical-align: middle; margin-right: 5px; } @keyframes spin { to { transform: rotate(360deg); } }`;
    document.head.appendChild(styleSheet);

    // --- Core API Functions ---

    async function uploadDocument() {
        if (!fileInput.files.length) {
            showStatusMessage(uploadStatusEl, 'Please select a PDF file.', 'error');
            return;
        }
        const file = fileInput.files[0];
        if (file.type !== 'application/pdf') {
            showStatusMessage(uploadStatusEl, 'Only PDF files are allowed.', 'error');
            return;
        }

        const formData = new FormData();
        formData.append('file', file);
        setLoading(uploadBtn, true);
        clearStatusMessage(uploadStatusEl);

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: formData, headers: AUTH_HEADER });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Upload failed');

            showStatusMessage(uploadStatusEl, `Success: ${result.message}`, 'success');
            fileInput.value = '';
            fetchDocumentList();
            fetchKbStatus();
        } catch (error) {
            showStatusMessage(uploadStatusEl, `Error: ${error.message}`, 'error');
        } finally {
            setLoading(uploadBtn, false);
        }
    }

    async function fetchDocumentList() {
        setLoading(refreshDocsBtn, true);
        listStatusEl.textContent = 'Loading documents...';
        documentListEl.innerHTML = '';

        try {
            const response = await fetch(`${API_BASE_URL}/list`, { headers: AUTH_HEADER });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();

            if (data.documents && data.documents.length > 0) {
                clearStatusMessage(listStatusEl);
                data.documents.forEach(doc => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <span class="doc-name">${doc.filename}</span>
                        <span class="doc-size">${(doc.size / 1024 / 1024).toFixed(2)} MB</span>
                        <div class="doc-actions">
                            <button class="btn btn-danger btn-sm delete-doc-btn" data-filename="${doc.filename}">Delete</button>
                        </div>`;
                    documentListEl.appendChild(li);
                });
                document.querySelectorAll('.delete-doc-btn').forEach(btn => btn.addEventListener('click', handleDeleteClick));
            } else {
                showStatusMessage(listStatusEl, 'No documents found.', 'info');
            }
        } catch (error) {
            showStatusMessage(listStatusEl, `Error loading documents: ${error.message}`, 'error');
        } finally {
            setLoading(refreshDocsBtn, false);
        }
    }
    
    async function handleDeleteClick(event) {
        const btn = event.target;
        const filename = btn.dataset.filename;
        if (confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
            setLoading(btn, true);
            try {
                const response = await fetch(`${API_BASE_URL}/${encodeURIComponent(filename)}`, { method: 'DELETE', headers: AUTH_HEADER });
                const result = await response.json();
                if (!response.ok) throw new Error(result.detail || 'Delete failed');
                
                showStatusMessage(listStatusEl, `"${filename}" deleted successfully.`, 'success');
                fetchDocumentList();
                fetchKbStatus();
            } catch (error) {
                showStatusMessage(listStatusEl, `Error deleting "${filename}": ${error.message}`, 'error');
                setLoading(btn, false);
            }
        }
    }

    async function fetchKbStatus() {
        setLoading(refreshKbStatusBtn, true);
        clearStatusMessage(kbStatusMessageEl);

        try {
            const response = await fetch(`${API_BASE_URL}/status`, { headers: AUTH_HEADER });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();

            kbChunksEl.textContent = data.total_chunks;
            kbReadyStatusEl.textContent = data.status.charAt(0).toUpperCase() + data.status.slice(1);
            kbReadyStatusEl.style.color = data.status === 'ready' ? 'green' : (data.status === 'empty' ? 'orange' : 'red');
            showStatusMessage(kbStatusMessageEl, `Status as of ${new Date(data.timestamp).toLocaleString()}`, 'info');
        } catch (error) {
            showStatusMessage(kbStatusMessageEl, `Error loading KB status: ${error.message}`, 'error');
        } finally {
            setLoading(refreshKbStatusBtn, false);
        }
    }

    // --- Initial Load and Event Listeners ---
    uploadBtn.addEventListener('click', uploadDocument);
    refreshDocsBtn.addEventListener('click', fetchDocumentList);
    refreshKbStatusBtn.addEventListener('click', fetchKbStatus);
    
    fetchDocumentList();
    fetchKbStatus();
}