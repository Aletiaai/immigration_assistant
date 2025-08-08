// Path: app/static/js/create_user.js

document.addEventListener('DOMContentLoaded', () => {
    const token = localStorage.getItem('user_token');
    // If the user isn't logged in with a token, redirect them.
    if (!token) {
        window.location.href = '/login';
        return;
    }

    const createUserForm = document.getElementById('create-user-form');
    const usernameInput = document.getElementById('username');
    const passwordInput = document.getElementById('password');
    const isAdminCheckbox = document.getElementById('is-admin');
    const createUserBtn = document.getElementById('create-user-btn');
    const statusMessageEl = document.getElementById('status-message');

    if (createUserForm) {
        createUserForm.addEventListener('submit', async (e) => {
            e.preventDefault();

            const username = usernameInput.value;
            const password = passwordInput.value;
            const isAdmin = isAdminCheckbox.checked;

            if (!username || !password) {
                showStatusMessage('Username and password are required.', 'error');
                return;
            }

            setLoading(true);

            try {
                const response = await fetch('/api/users/create', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': `Bearer ${token}`
                    },
                    body: JSON.stringify({
                        username: username,
                        password: password,
                        is_admin: isAdmin
                    })
                });

                const result = await response.json();

                if (!response.ok) {
                    throw new Error(result.detail || 'Failed to create user.');
                }

                showStatusMessage(`User '${username}' created successfully!`, 'success');
                createUserForm.reset(); // Clear the form for the next entry

            } catch (error) {
                showStatusMessage(`Error: ${error.message}`, 'error');
            } finally {
                setLoading(false);
            }
        });
    }

    function showStatusMessage(message, type) {
        statusMessageEl.textContent = message;
        statusMessageEl.className = `status-message ${type}`;
        statusMessageEl.style.display = 'block';
    }

    function setLoading(loading) {
        createUserBtn.disabled = loading;
        createUserBtn.textContent = loading ? 'Creating...' : 'Create User';
    }
});