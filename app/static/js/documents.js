// Path: app/static/js/documents.js

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Look for the standard user token.
    const token = localStorage.getItem('user_token');

    if (!token) {
        window.location.href = '/login'; // If no token, they must log in.
        return;
    }

    // 2. Verify the token is valid AND belongs to an admin.
    try {
        const response = await fetch('/api/auth/verify', {
            method: 'GET',
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) {
            // This happens if the token is expired or invalid.
            throw new Error('Invalid or expired token.');
        }

        const userData = await response.json();
        
        // This is the crucial admin check on the frontend.
        if (!userData.username || !userData.username.toLowerCase().includes('admin')) {
            // If the user is valid but not an admin, send them to the chat page.
            alert('Access denied. This page is for administrators only.');
            window.location.href = '/';
            return;
        }

        // 3. If the user is a verified admin, initialize the page.
        initializeDocumentManagement(token);

    } catch (error) {
        console.error('Admin verification failed:', error);
        localStorage.removeItem('user_token'); // Clear bad token
        window.location.href = '/login';
    }
});

// This function sets up the entire document management page.
function initializeDocumentManagement(token) {
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
    const logoutBtn = document.getElementById('logout-btn');
    const createUserBtn = document.getElementById('create-user-btn');

    const API_BASE_URL = '/api/documents';
    // Use the verified token for all API calls on this page.
    const AUTH_HEADER = { 'Authorization': `Bearer ${token}` };

    // --- Utility Functions ---
    const showStatusMessage = (element, message, type = 'info') => {
        element.textContent = message;
        element.className = `status-message ${type}`;
        element.style.display = 'block';
    };

    const setLoading = (button, isLoading) => {
        button.disabled = isLoading;
        if (isLoading) {
            button.dataset.originalText = button.innerHTML;
            button.innerHTML = '<div class="spinner-small"></div>';
        } else {
            button.innerHTML = button.dataset.originalText;
        }
    };
    
    const styleSheet = document.createElement("style");
    styleSheet.innerText = `.spinner-small { border: 2px solid rgba(0,0,0,0.1); width: 16px; height: 16px; border-radius: 50%; border-left-color: #667eea; animation: spin 0.8s ease infinite; display: inline-block; vertical-align: middle; } @keyframes spin { to { transform: rotate(360deg); } }`;
    document.head.appendChild(styleSheet);


    // --- API Functions ---
    async function uploadDocument() {
        if (!fileInput.files.length) return showStatusMessage(uploadStatusEl, 'Please select a PDF file.', 'error');
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        setLoading(uploadBtn, true);

        try {
            const response = await fetch(`${API_BASE_URL}/upload`, { method: 'POST', body: formData, headers: AUTH_HEADER });
            const result = await response.json();
            if (!response.ok) throw new Error(result.detail || 'Upload failed');
            showStatusMessage(uploadStatusEl, result.message, 'success');
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
        try {
            const response = await fetch(`${API_BASE_URL}/list`, { headers: AUTH_HEADER });
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            const data = await response.json();
            
            documentListEl.innerHTML = '';
            if (data.documents && data.documents.length > 0) {
                listStatusEl.style.display = 'none';
                data.documents.forEach(doc => {
                    const li = document.createElement('li');
                    li.innerHTML = `
                        <span class="doc-name">${doc.filename}</span>
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
        if (confirm(`Are you sure you want to delete "${filename}"?`)) {
            setLoading(btn, true);
            try {
                const response = await fetch(`${API_BASE_URL}/${encodeURIComponent(filename)}`, { method: 'DELETE', headers: AUTH_HEADER });
                const result = await response.json();
                if (!response.ok) throw new Error(result.detail || 'Delete failed');
                fetchDocumentList();
                fetchKbStatus();
            } catch (error) {
                alert(`Error: ${error.message}`);
                setLoading(btn, false);
            }
        }
    }

    async function fetchKbStatus() {
        setLoading(refreshKbStatusBtn, true);
        try {
            const response = await fetch(`${API_BASE_URL}/status`, { headers: AUTH_HEADER });
            if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
            const data = await response.json();
            kbChunksEl.textContent = data.total_chunks;
            kbReadyStatusEl.textContent = data.status;
        } catch (error) {
            kbReadyStatusEl.textContent = 'Error';
        } finally {
            setLoading(refreshKbStatusBtn, false);
        }
    }

    // Initial load and event listeners
    uploadBtn.addEventListener('click', uploadDocument);
    refreshDocsBtn.addEventListener('click', fetchDocumentList);
    refreshKbStatusBtn.addEventListener('click', fetchKbStatus);
    
    fetchDocumentList();
    fetchKbStatus();

    if (logoutBtn) {
        logoutBtn.addEventListener('click', async () => {
            try {
                // Call the logout endpoint to clear server session
                await fetch('/api/auth/logout', { 
                    method: 'POST',
                    headers: { 'Authorization': `Bearer ${token}` }
                });
            } catch (error) {
                console.log('Logout API call failed, but clearing local storage anyway');
            }
            
            localStorage.removeItem('user_token'); // Clear the token
            window.location.href = '/login'; // Redirect to login
        });
    }

    if (createUserBtn) {
        createUserBtn.addEventListener('click', async () => {
            // Now we simply navigate to the page - session authentication handles the rest
            window.location.href = '/create-user';
        });
    }
}