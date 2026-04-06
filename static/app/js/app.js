// ==================== EDUQUEST - APP.JS (PRINCIPAL) ====================

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    checkAuth();
    setupEventListeners();

    setTimeout(() => {
        elements.loadingScreen.classList.add('hidden');
    }, 1500);
});

// Event Listeners
function setupEventListeners() {
    elements.loginForm.addEventListener('submit', handleLogin);
    elements.logoutBtn.addEventListener('click', handleLogout);
    elements.sidebarToggle.addEventListener('click', () => elements.sidebar.classList.toggle('collapsed'));
    elements.modalClose.addEventListener('click', () => closeModal());
    elements.modalOverlay.addEventListener('click', (e) => {
        if (e.target === elements.modalOverlay) closeModal();
    });

    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navigateTo(item.dataset.page);
        });
    });

    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchTab(btn.dataset.tab));
    });

    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => switchAdminTab(btn.dataset.adminTab));
    });
}

// Update principal
async function updateUI() {
    if (!state.user) return;

    // Atualizar informações do usuário na sidebar
    document.getElementById('user-name').textContent = state.user.username;
    document.getElementById('user-role').textContent = state.user.role === 'student' ? 'Estudante' :
                                                         state.user.role === 'teacher' ? 'Professor' : 'Administrador';

    // Atualizar top bar
    document.getElementById('user-level').textContent = `Nível ${state.user.current_level || 1}`;
    document.getElementById('user-xp').textContent = `${state.user.current_xp || 0} XP`;
    document.getElementById('user-coins').textContent = state.user.coins || 0;

    // Atualizar dashboard stats se estiver na página
    if (typeof updateDashboardStats === 'function') {
        updateDashboardStats();
    }

    // Atualizar estatísticas do dashboard (missões, conquistas)
    if (document.getElementById('stat-missions')) {
        try {
            const missionsRes = await fetch(`${API_BASE_URL}/users/${state.user.id}/missions/pending`, {
                credentials: 'include'
            });
            if (missionsRes.ok) {
                const data = await missionsRes.json();
                document.getElementById('stat-missions').textContent = data.missions?.length || 0;
            }
        } catch(e) { console.log('Erro ao atualizar stat missions'); }
    }

    if (document.getElementById('stat-achievements')) {
        try {
            const achievementsRes = await fetch(`${API_BASE_URL}/user-achievements`, {
                credentials: 'include'
            });
            if (achievementsRes.ok) {
                const data = await achievementsRes.json();
                document.getElementById('stat-achievements').textContent = data.achievements?.length || 0;
            }
        } catch(e) { console.log('Erro ao atualizar stat achievements'); }
    }

    // Mostrar/esconder elementos admin
    const adminItems = document.querySelectorAll('.admin-only');
    const isAdmin = state.user.role === 'admin';
    adminItems.forEach(item => {
        if (isAdmin) {
            item.classList.remove('hidden');
        } else {
            item.classList.add('hidden');
        }
    });
}

// ==================== ATUALIZAR DASHBOARD DO ALUNO ====================

async function refreshStudentDashboard() {
    if (!state.user) return;

    console.log('🔄 Atualizando dashboard do aluno...');

    try {
        // Atualizar estatísticas do usuário
        const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
            credentials: 'include'
        });

        if (userResponse.ok) {
            const data = await userResponse.json();
            if (data.success && data.user) {
                // Atualizar estado do usuário
                state.user = data.user;

                // Atualizar UI com novos dados
                document.getElementById('user-level').textContent = `Nível ${state.user.current_level || 1}`;
                document.getElementById('user-xp').textContent = `${state.user.current_xp || 0} XP`;
                document.getElementById('user-coins').textContent = state.user.coins || 0;
                document.getElementById('current-xp').textContent = state.user.current_xp || 0;

                // Atualizar barra de XP
                const xpProgress = ((state.user.current_xp || 0) % 100) / 100 * 100;
                document.getElementById('xp-progress').style.width = `${xpProgress}%`;
            }
        }

        // Recarregar missões pendentes
        const missionsResponse = await fetch(`${API_BASE_URL}/users/${state.user.id}/missions/pending`, {
            credentials: 'include'
        });

        if (missionsResponse.ok) {
            const missionsData = await missionsResponse.json();
            renderPendingMissions(missionsData.missions || []);

            // Atualizar contador de missões no dashboard
            const missionCount = missionsData.missions?.length || 0;
            const statMissions = document.getElementById('stat-missions');
            if (statMissions) statMissions.textContent = missionCount;
        }

        // Recarregar conquistas recentes
        const achievementsResponse = await fetch(`${API_BASE_URL}/user-achievements`, {
            credentials: 'include'
        });

        if (achievementsResponse.ok) {
            const achievementsData = await achievementsResponse.json();
            renderRecentAchievements(achievementsData.achievements || []);

            // Atualizar contador de conquistas
            const achievementCount = achievementsData.achievements?.length || 0;
            const statAchievements = document.getElementById('stat-achievements');
            if (statAchievements) statAchievements.textContent = achievementCount;
        }

        console.log('✅ Dashboard atualizado com sucesso!');

    } catch (error) {
        console.error('Erro ao atualizar dashboard:', error);
    }
}