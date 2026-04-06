// ==================== AUTENTICAÇÃO ====================
async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            if (data.success && data.user) {
                state.user = data.user;
                showApp();
                await updateUI();
                await loadDashboard();
                return;
            }
        }
        showLogin();
    } catch (error) {
        console.error('Auth check error:', error);
        showLogin();
    }
}

function showLogin() {
    elements.loginScreen.classList.remove('hidden');
    elements.app.classList.add('hidden');
    document.getElementById('username').value = '';
    document.getElementById('password').value = '';
}

function showApp() {
    elements.loginScreen.classList.add('hidden');
    elements.app.classList.remove('hidden');
}

async function handleLogin(e) {
    e.preventDefault();

    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    const submitBtn = elements.loginForm.querySelector('button[type="submit"]');
    const originalText = submitBtn.innerHTML;

    submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Entrando...';
    submitBtn.disabled = true;

    try {
        const response = await fetch(`${API_BASE_URL}/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ username, password })
        });

        const data = await response.json();

        if (data.success) {
            state.user = data.user;
            showApp();
            await updateUI();
            await loadDashboard();
            showToast('Login realizado com sucesso!', 'success');
        } else {
            showToast(data.error || 'Usuário ou senha inválidos', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Erro ao conectar com o servidor', 'error');
    } finally {
        submitBtn.innerHTML = originalText;
        submitBtn.disabled = false;
    }
}

async function handleLogout() {
    try {
        await fetch(`${API_BASE_URL}/auth/logout`, { method: 'POST', credentials: 'include' });
        state.user = null;
        showLogin();
        showToast('Logout realizado com sucesso!', 'success');
    } catch (error) {
        console.error('Logout error:', error);
    }
}