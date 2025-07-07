// Path: app/static/js/login.js

document.addEventListener('DOMContentLoaded', () => {
    const loginForm = document.getElementById('login-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const loginBtn = document.getElementById('login-btn');
    const loginStatus = document.getElementById('login-status');

    if (usernameInput) {
        usernameInput.focus();
    }

    if (loginForm) {
        loginForm.addEventListener('submit', async (e) => {
            e.preventDefault();
            setLoading(true);
            
            const username = usernameInput.value;
            const password = passwordInput.value;

            if (!username || !password) {
                showStatus('Username and password are required.', 'error');
                setLoading(false);
                return;
            }

            // OAuth2 requires form data, not JSON
            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/api/auth/token', {
                    method: 'POST',
                    body: formData, // Send as form data
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'Login failed.');
                }

                // IMPORTANT: Use a consistent token name. Let's use 'user_token'.
                localStorage.setItem('user_token', data.access_token);
                showStatus('Login successful! Redirecting...', 'success');
                
                // Check if the user is an admin to decide where to redirect
                if (username.toLowerCase().includes('admin')) {
                    window.location.href = '/documents'; // Redirect admins to the document page
                } else {
                    window.location.href = '/'; // Redirect regular users to the chat page
                }

            } catch (error) {
                showStatus(error.message, 'error');
            } finally {
                setLoading(false);
            }
        });
    }

    function showStatus(message, type) {
        if (loginStatus) {
            loginStatus.textContent = message;
            loginStatus.className = `status-message ${type}`;
        }
    }

    function setLoading(loading) {
        loginBtn.disabled = loading;
        loginBtn.textContent = loading ? 'Logging in...' : 'Login';
    }
});