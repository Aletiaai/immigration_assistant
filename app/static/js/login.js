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

            const formData = new FormData();
            formData.append('username', username);
            formData.append('password', password);

            try {
                const response = await fetch('/api/auth/token', {
                    method: 'POST',
                    body: formData,
                });

                const data = await response.json();

                if (!response.ok) {
                    throw new Error(data.detail || 'Login failed.');
                }

                console.log("Login successful. Token received:", data.access_token);
                
                // On successful login, save the token and redirect
                localStorage.setItem('user_token', data.access_token);
                console.log("Token saved to localStorage.");

                showStatus('Login successful! Redirecting...', 'success');
                
                // Redirect based on whether the user is an admin
                if (username.toLowerCase().includes('admin')) {
                    window.location.href = '/documents';
                } else {
                    window.location.href = '/';
                }

            } catch (error) {
                console.error('An error occurred during login:', error);
                showStatus(error.message, 'error');
            }finally {
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