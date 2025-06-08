// Script for app/static/js/documents.js
document.addEventListener('DOMContentLoaded', async () => {
    const token = localStorage.getItem('admin_token');

    // Redirect to login if no token is found
    if (!token) {
        window.location.href = '/login';
        return;
    }

    try {
        // Verify token with the backend
        const response = await fetch('/api/auth/verify', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });

        if (!response.ok) {
            localStorage.removeItem('admin_token');
            window.location.href = '/login';
            return;
        }

        // Token is valid; initialize document management
        initializeDocumentManagement();
    } catch (error) {
        console.error('Authentication check failed:', error);
        localStorage.removeItem('admin_token');
        window.location.href = '/login';
    }
});

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

    // --- Utility Functions ---
    function showStatusMessage(element, message, type = 'info') {
        if (!element) return;
        element.textContent = message;
        element.className = `status-message ${type}`;
        element.style.display = 'block';
    }

    function clearStatusMessage(element) {
        if (!element) return;
        element.textContent = '';
        element.style.display = 'none';
        element.className = 'status-message';
    }

    function setLoading(button, isLoading) {
        if (!button) return;
        button.disabled = isLoading;
        button.innerHTML = isLoading ? '<div class="spinner-small"></div> Loading...' : button.dataset.originalText || button.textContent;
        if (!isLoading && button.dataset.originalText) {
            delete button.dataset.originalText;
        } else if (isLoading && !button.dataset.originalText) {
            button.dataset.originalText = button.textContent;
        }
    }

    const styleSheet = document.createElement("style");
    styleSheet.innerText = `.spinner-small { border: 2px solid rgba(0,0,0,0.1); width: 16px; height: 16px; border-radius: 50%; border-left-color: #667eea; animation: spin 0.8s ease infinite; display: inline-block; vertical-align: middle; margin-right: 5px; }`;
    document.head.appendChild(styleSheet);

    // --- Document Upload ---
    async function uploadDocument() {
        if (!fileInput.files || fileInput.files.length === 0) {
            showStatusMessage(uploadStatusEl, 'Please select a PDF file to upload.', 'error');
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
            const response = await fetch(`${API_BASE_URL}/upload`, {
                method: 'POST',
                body: formData,
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                }
            });

            if (response.status === 401) {
                localStorage.removeItem('admin_token');
                window.location.href = '/login';
                return;
            }

            const result = await response.json();

            if (response.ok && result.status === 'processed') {
                showStatusMessage(uploadStatusEl, `Success: ${result.message || 'Document uploaded and processed.'}`, 'success');
                fileInput.value = '';
                fetchDocumentList();
                fetchKbStatus();
            } else {
                showStatusMessage(uploadStatusEl, `Error: ${result.message || 'Upload failed.'} (Status: ${result.status})`, 'error');
            }
        } catch (error) {
            console.error('Upload error:', error);
            showStatusMessage(uploadStatusEl, `Network or server error: ${error.message}`, 'error');
        } finally {
            setLoading(uploadBtn, false);
        }
    }

    // --- Document List ---
    async function fetchDocumentList() {
        setLoading(refreshDocsBtn, true);
        listStatusEl.textContent = 'Loading documents...';
        listStatusEl.className = 'status-message info';
        documentListEl.innerHTML = '';

        try {
            const response = await fetch(`${API_BASE_URL}/list`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                }
            });

            if (response.status === 401) {
                localStorage.removeItem('admin_token');
                window.location.href = '/login';
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            if (data.documents && data.documents.length > 0) {
                listStatusEl.style.display = 'none';
                data.documents.forEach(doc => {
                    const li = document.createElement('li');
                    const sizeMB = (doc.size / (1024 * 1024)).toFixed(2);
                    li.innerHTML = `
                        <span class="doc-name">${doc.filename}</span>
                        <span class="doc-size">${sizeMB} MB</span>
                        <div class="doc-actions">
                            <button class="btn btn-danger btn-sm delete-doc-btn" data-filename="${doc.filename}">Delete</button>
                        </div>
                    `;
                    documentListEl.appendChild(li);
                });
                attachDeleteListeners();
            } else {
                listStatusEl.textContent = 'No documents found. Upload one to get started.';
                listStatusEl.className = 'status-message info';
            }
        } catch (error) {
            console.error('Error fetching document list:', error);
            listStatusEl.textContent = `Error loading documents: ${error.message}`;
            listStatusEl.className = 'status-message error';
        } finally {
            setLoading(refreshDocsBtn, false);
        }
    }

    function attachDeleteListeners() {
        document.querySelectorAll('.delete-doc-btn').forEach(button => {
            button.addEventListener('click', async (event) => {
                const filename = event.target.dataset.filename;
                if (confirm(`Are you sure you want to delete "${filename}"? This action cannot be undone.`)) {
                    await deleteDocument(filename, event.target);
                }
            });
        });
    }

    async function deleteDocument(filename, buttonElement) {
        setLoading(buttonElement, true);
        clearStatusMessage(listStatusEl);

        try {
            const response = await fetch(`${API_BASE_URL}/${encodeURIComponent(filename)}`, {
                method: 'DELETE',
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                }
            });

            if (response.status === 401) {
                localStorage.removeItem('admin_token');
                window.location.href = '/login';
                return;
            }

            const result = await response.json();

            if (response.ok) {
                showStatusMessage(listStatusEl, `"${filename}" deleted successfully.`, 'success');
                fetchDocumentList();
                fetchKbStatus();
            } else {
                showStatusMessage(listStatusEl, `Error deleting "${filename}": ${result.detail || 'Unknown error'}`, 'error');
            }
        } catch (error) {
            console.error('Delete error:', error);
            showStatusMessage(listStatusEl, `Network or server error during deletion: ${error.message}`, 'error');
        } finally {
            // No need to reset loading state here as the list will refresh
        }
    }

    // --- Knowledge Base Status ---
    async function fetchKbStatus() {
        setLoading(refreshKbStatusBtn, true);
        clearStatusMessage(kbStatusMessageEl);
        kbChunksEl.textContent = 'Loading...';
        kbReadyStatusEl.textContent = 'Loading...';

        try {
            const response = await fetch(`${API_BASE_URL}/status`, {
                headers: {
                    'Authorization': `Bearer ${localStorage.getItem('admin_token')}`
                }
            });

            if (response.status === 401) {
                localStorage.removeItem('admin_token');
                window.location.href = '/login';
                return;
            }

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            const data = await response.json();

            kbChunksEl.textContent = data.total_chunks !== undefined ? data.total_chunks : 'N/A';
            kbReadyStatusEl.textContent = data.status ? data.status.charAt(0).toUpperCase() + data.status.slice(1) : 'N/A';
            if (data.status === 'empty') {
                kbReadyStatusEl.style.color = 'orange';
            } else if (data.status === 'ready') {
                kbReadyStatusEl.style.color = 'green';
            } else {
                kbReadyStatusEl.style.color = 'red';
            }
            showStatusMessage(kbStatusMessageEl, `Status as of ${new Date(data.timestamp).toLocaleString()}`, 'info');
        } catch (error) {
            console.error('Error fetching KB status:', error);
            kbChunksEl.textContent = 'Error';
            kbReadyStatusEl.textContent = 'Error';
            showStatusMessage(kbStatusMessageEl, `Error loading KB status: ${error.message}`, 'error');
        } finally {
            setLoading(refreshKbStatusBtn, false);
        }
    }

    // --- Event Listeners ---
    if (uploadBtn) uploadBtn.addEventListener('click', uploadDocument);
    if (refreshDocsBtn) refreshDocsBtn.addEventListener('click', fetchDocumentList);
    if (refreshKbStatusBtn) refreshKbStatusBtn.addEventListener('click', fetchKbStatus);

    // --- Initial Load ---
    fetchDocumentList();
    fetchKbStatus();
}