// ==================== EDUQUEST - APP.JS ====================

const API_BASE_URL = '/api';

// ==================== STATE ====================
const state = {
    user: null,
    missions: [],
    achievements: [],
    rewards: [],
    disciplines: [],
    users: [],
    currentPage: 'dashboard'
};

// ==================== DOM ELEMENTS ====================
const elements = {
    loadingScreen: document.getElementById('loading-screen'),
    loginScreen: document.getElementById('login-screen'),
    app: document.getElementById('app'),
    loginForm: document.getElementById('login-form'),
    logoutBtn: document.getElementById('logout-btn'),
    sidebarToggle: document.getElementById('sidebar-toggle'),
    sidebar: document.getElementById('sidebar'),
    modalOverlay: document.getElementById('modal-overlay'),
    modal: document.getElementById('modal'),
    modalTitle: document.getElementById('modal-title'),
    modalBody: document.getElementById('modal-body'),
    modalFooter: document.getElementById('modal-footer'),
    modalClose: document.getElementById('modal-close'),
    toastContainer: document.getElementById('toast-container'),
    particlesContainer: document.getElementById('particles-container')
};

// ==================== INITIALIZATION ====================
document.addEventListener('DOMContentLoaded', () => {
    initParticles();
    checkAuth();
    setupEventListeners();
    
    // Hide loading screen after initialization
    setTimeout(() => {
        elements.loadingScreen.classList.add('hidden');
    }, 1500);
});

// ==================== PARTICLES ====================
function initParticles() {
    const container = elements.particlesContainer;
    const particleCount = 50;
    
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.className = 'particle';
        particle.style.left = `${Math.random() * 100}%`;
        particle.style.top = `${Math.random() * 100}%`;
        particle.style.animationDelay = `${Math.random() * 6}s`;
        particle.style.animationDuration = `${4 + Math.random() * 4}s`;
        
        const colors = ['#00ffff', '#ff00ff', '#ffff00', '#00ff00'];
        particle.style.background = colors[Math.floor(Math.random() * colors.length)];
        
        container.appendChild(particle);
    }
}

// ==================== AUTH ====================
async function checkAuth() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/me`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            if (data.success) {
                state.user = data.user;
                showApp();
                updateUI();
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
}

function showApp() {
    elements.loginScreen.classList.add('hidden');
    elements.app.classList.remove('hidden');
}

// ==================== EVENT LISTENERS ====================
function setupEventListeners() {
    // Login form
    elements.loginForm.addEventListener('submit', handleLogin);
    
    // Logout
    elements.logoutBtn.addEventListener('click', handleLogout);
    
    // Sidebar toggle
    elements.sidebarToggle.addEventListener('click', () => {
        elements.sidebar.classList.toggle('collapsed');
    });
    
    // Navigation
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const page = item.dataset.page;
            navigateTo(page);
        });
    });
    
    // Modal close
    elements.modalClose.addEventListener('click', closeModal);
    elements.modalOverlay.addEventListener('click', (e) => {
        if (e.target === elements.modalOverlay) {
            closeModal();
        }
    });
    
    // Tabs
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const tab = btn.dataset.tab;
            switchTab(tab);
        });
    });
    
    // Admin tabs
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const adminTab = btn.dataset.adminTab;
            switchAdminTab(adminTab);
        });
    });
}

// ==================== LOGIN/LOGOUT ====================
async function handleLogin(e) {
    e.preventDefault();
    
    const username = document.getElementById('username').value;
    const password = document.getElementById('password').value;
    
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
            updateUI();
            showToast('Login realizado com sucesso!', 'success');
        } else {
            showToast(data.error || 'Erro ao fazer login', 'error');
        }
    } catch (error) {
        console.error('Login error:', error);
        showToast('Erro ao conectar com o servidor', 'error');
    }
}

async function handleLogout() {
    try {
        const response = await fetch(`${API_BASE_URL}/auth/logout`, {
            method: 'POST',
            credentials: 'include'
        });
        
        state.user = null;
        showLogin();
        showToast('Logout realizado com sucesso!', 'success');
    } catch (error) {
        console.error('Logout error:', error);
    }
}

// ==================== NAVIGATION ====================
function navigateTo(page) {
    state.currentPage = page;
    
    // Update nav items
    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.remove('active');
        if (item.dataset.page === page) {
            item.classList.add('active');
        }
    });
    
    // Update pages
    document.querySelectorAll('.page').forEach(p => {
        p.classList.remove('active');
    });
    
    const targetPage = document.getElementById(`page-${page}`);
    if (targetPage) {
        targetPage.classList.add('active');
    }
    
    // Load page data
    loadPageData(page);
}

async function loadPageData(page) {
    switch (page) {
        case 'dashboard':
            await loadDashboard();
            break;
        case 'missions':
            await loadMissions();
            break;
        case 'achievements':
            await loadAchievements();
            break;
        case 'rewards':
            await loadRewards();
            break;
        case 'disciplines':
            await loadDisciplines();
            break;
        case 'ranking':
            await loadRanking();
            break;
        case 'admin':
            await loadAdminData();
            break;
    }
}

// ==================== DASHBOARD ====================
async function loadDashboard() {
    try {
        // Load pending missions
        const missionsResponse = await fetch(`${API_BASE_URL}/users/${state.user.id}/missions/pending`, {
            credentials: 'include'
        });
        
        if (missionsResponse.ok) {
            const missionsData = await missionsResponse.json();
            renderPendingMissions(missionsData.missions || []);
        }
        
        // Load achievements
        const achievementsResponse = await fetch(`${API_BASE_URL}/user-achievements`, {
            credentials: 'include'
        });
        
        if (achievementsResponse.ok) {
            const achievementsData = await achievementsResponse.json();
            renderRecentAchievements(achievementsData.achievements || []);
        }
        
        // Update stats
        updateDashboardStats();
        
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

function updateDashboardStats() {
    if (!state.user) return;
    
    document.getElementById('welcome-name').textContent = state.user.username;
    document.getElementById('current-xp').textContent = state.user.current_xp;
    document.getElementById('next-level-xp').textContent = (state.user.current_level + 1) * 100;
    
    const xpProgress = ((state.user.current_xp % 100) / 100) * 100;
    document.getElementById('xp-progress').style.width = `${xpProgress}%`;
}

function renderPendingMissions(missions) {
    const container = document.getElementById('pending-missions-list');
    
    if (missions.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão pendente</p>';
        return;
    }
    
    container.innerHTML = missions.slice(0, 5).map(mission => `
        <div class="mission-item">
            <div class="mission-item-info">
                <i class="fas fa-tasks"></i>
                <span>${mission.mission?.name || 'Missão'}</span>
            </div>
            <button class="btn btn-sm btn-primary" onclick="completeMission(${mission.id})">
                Completar
            </button>
        </div>
    `).join('');
}

function renderRecentAchievements(achievements) {
    const container = document.getElementById('recent-achievements-list');
    
    if (achievements.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma conquista ainda</p>';
        return;
    }
    
    container.innerHTML = achievements.slice(0, 5).map(achievement => `
        <div class="achievement-item">
            <div class="achievement-item-icon">${achievement.achievement?.icon || '🏆'}</div>
            <div class="achievement-item-info">
                <span class="achievement-item-name">${achievement.achievement?.name || 'Conquista'}</span>
                <span class="achievement-item-date">${formatDate(achievement.date_achieved)}</span>
            </div>
        </div>
    `).join('');
}

// ==================== MISSIONS ====================
async function loadMissions() {
    try {
        // Available missions
        const availableResponse = await fetch(`${API_BASE_URL}/missions/available`, {
            credentials: 'include'
        });
        
        if (availableResponse.ok) {
            const data = await availableResponse.json();
            renderAvailableMissions(data.missions || []);
        }
        
        // Pending missions
        const pendingResponse = await fetch(`${API_BASE_URL}/users/${state.user.id}/missions/pending`, {
            credentials: 'include'
        });
        
        if (pendingResponse.ok) {
            const data = await pendingResponse.json();
            renderPendingMissionsGrid(data.missions || []);
        }
        
        // Completed missions
        const completedResponse = await fetch(`${API_BASE_URL}/users/${state.user.id}/missions/completed`, {
            credentials: 'include'
        });
        
        if (completedResponse.ok) {
            const data = await completedResponse.json();
            renderCompletedMissions(data.missions || []);
        }
        
    } catch (error) {
        console.error('Missions load error:', error);
    }
}

function renderAvailableMissions(missions) {
    const container = document.getElementById('available-missions-grid');
    
    if (missions.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão disponível</p>';
        return;
    }
    
    container.innerHTML = missions.map(mission => `
        <div class="mission-card">
            <div class="mission-header">
                <div class="mission-icon">
                    <i class="fas fa-tasks"></i>
                </div>
            </div>
            <h4 class="mission-title">${mission.name}</h4>
            <p class="mission-description">${mission.description || ''}</p>
            <div class="mission-rewards">
                <span class="mission-reward">
                    <i class="fas fa-bolt"></i> ${mission.xp_reward} XP
                </span>
                <span class="mission-reward coins">
                    <i class="fas fa-gem"></i> ${mission.coin_reward}
                </span>
            </div>
            <button class="btn btn-primary btn-full" onclick="acceptMission(${mission.id})">
                Aceitar Missão
            </button>
        </div>
    `).join('');
}

function renderPendingMissionsGrid(missions) {
    const container = document.getElementById('pending-missions-grid');
    
    if (missions.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão pendente</p>';
        return;
    }
    
    container.innerHTML = missions.map(mission => `
        <div class="mission-card">
            <div class="mission-header">
                <div class="mission-icon">
                    <i class="fas fa-tasks"></i>
                </div>
                <span class="mission-status pending">Pendente</span>
            </div>
            <h4 class="mission-title">${mission.mission?.name || 'Missão'}</h4>
            <p class="mission-description">${mission.mission?.description || ''}</p>
            <div class="mission-rewards">
                <span class="mission-reward">
                    <i class="fas fa-bolt"></i> ${mission.mission?.xp_reward || 0} XP
                </span>
                <span class="mission-reward coins">
                    <i class="fas fa-gem"></i> ${mission.mission?.coin_reward || 0}
                </span>
            </div>
            <button class="btn btn-success btn-full" onclick="completeMission(${mission.id})">
                Completar
            </button>
        </div>
    `).join('');
}

function renderCompletedMissions(missions) {
    const container = document.getElementById('completed-missions-grid');
    
    if (missions.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão completada</p>';
        return;
    }
    
    container.innerHTML = missions.map(mission => `
        <div class="mission-card">
            <div class="mission-header">
                <div class="mission-icon">
                    <i class="fas fa-check"></i>
                </div>
                <span class="mission-status completed">Completada</span>
            </div>
            <h4 class="mission-title">${mission.mission?.name || 'Missão'}</h4>
            <p class="mission-description">${mission.mission?.description || ''}</p>
            <p class="mission-date">Completada em: ${formatDate(mission.completion_date)}</p>
        </div>
    `).join('');
}

// ==================== ACHIEVEMENTS ====================
async function loadAchievements() {
    try {
        const response = await fetch(`${API_BASE_URL}/user-achievements/progress`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            renderAchievements(data.progress || []);
        }
        
    } catch (error) {
        console.error('Achievements load error:', error);
    }
}

function renderAchievements(achievements) {
    const container = document.getElementById('achievements-grid');
    
    if (achievements.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma conquista disponível</p>';
        return;
    }
    
    container.innerHTML = achievements.map(achievement => `
        <div class="achievement-card ${achievement.earned ? 'earned' : ''}">
            <div class="achievement-header">
                <div class="achievement-icon">
                    ${achievement.icon || '🏆'}
                </div>
                ${achievement.earned ? '<i class="fas fa-check-circle earned-icon"></i>' : ''}
            </div>
            <h4 class="achievement-title">${achievement.name}</h4>
            <p class="achievement-description">${achievement.description || ''}</p>
            ${!achievement.earned && achievement.progress !== undefined ? `
                <div class="achievement-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${achievement.progress}%"></div>
                    </div>
                    <span class="progress-text">${Math.round(achievement.progress)}%</span>
                </div>
            ` : ''}
        </div>
    `).join('');
}

// ==================== REWARDS ====================
async function loadRewards() {
    try {
        // Shop rewards
        const shopResponse = await fetch(`${API_BASE_URL}/rewards`, {
            credentials: 'include'
        });
        
        if (shopResponse.ok) {
            const data = await shopResponse.json();
            renderShopRewards(data.rewards || []);
        }
        
        // User rewards
        const userResponse = await fetch(`${API_BASE_URL}/users/${state.user.id}/rewards`, {
            credentials: 'include'
        });
        
        if (userResponse.ok) {
            const data = await userResponse.json();
            renderUserRewards(data.rewards || []);
        }
        
        // Update coins display
        document.getElementById('shop-coins').textContent = state.user?.coins || 0;
        
    } catch (error) {
        console.error('Rewards load error:', error);
    }
}

function renderShopRewards(rewards) {
    const container = document.getElementById('shop-rewards-grid');
    
    if (rewards.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma recompensa disponível</p>';
        return;
    }
    
    container.innerHTML = rewards.map(reward => `
        <div class="reward-card">
            <div class="reward-header">
                <div class="reward-icon">
                    ${reward.icon || '🎁'}
                </div>
            </div>
            <h4 class="reward-title">${reward.name}</h4>
            <p class="reward-description">${reward.description || ''}</p>
            <div class="reward-cost">
                <i class="fas fa-gem"></i> ${reward.coin_cost} cristais
            </div>
            <button class="btn btn-primary btn-full" onclick="purchaseReward(${reward.id})">
                Comprar
            </button>
        </div>
    `).join('');
}

function renderUserRewards(rewards) {
    const container = document.getElementById('my-rewards-grid');
    
    if (rewards.length === 0) {
        container.innerHTML = '<p class="empty-state">Você não possui recompensas</p>';
        return;
    }
    
    container.innerHTML = rewards.map(reward => `
        <div class="reward-card">
            <div class="reward-header">
                <div class="reward-icon">
                    ${reward.reward?.icon || '🎁'}
                </div>
                ${reward.is_redeemed ? '<span class="reward-status redeemed">Resgatado</span>' : ''}
            </div>
            <h4 class="reward-title">${reward.reward?.name || 'Recompensa'}</h4>
            <p class="reward-description">${reward.reward?.description || ''}</p>
            <p class="reward-date">Comprado em: ${formatDate(reward.purchase_date)}</p>
            ${!reward.is_redeemed ? `
                <button class="btn btn-success btn-full" onclick="redeemReward(${reward.id})">
                    Resgatar
                </button>
            ` : ''}
        </div>
    `).join('');
}

// ==================== DISCIPLINES ====================
async function loadDisciplines() {
    try {
        const response = await fetch(`${API_BASE_URL}/disciplines`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            renderDisciplines(data.disciplines || []);
        }
        
    } catch (error) {
        console.error('Disciplines load error:', error);
    }
}

function renderDisciplines(disciplines) {
    const container = document.getElementById('disciplines-grid');
    
    if (disciplines.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma disciplina disponível</p>';
        return;
    }
    
    container.innerHTML = disciplines.map(discipline => `
        <div class="discipline-card">
            <div class="discipline-header">
                <div class="discipline-icon">
                    <i class="fas fa-book"></i>
                </div>
            </div>
            <h4 class="discipline-title">${discipline.nome}</h4>
            <p class="discipline-code">${discipline.codigo}</p>
            <p class="discipline-info">
                <i class="fas fa-clock"></i> ${discipline.carga_horaria}h
            </p>
            ${discipline.professor_nome ? `
                <p class="discipline-professor">
                    <i class="fas fa-user"></i> ${discipline.professor_nome}
                </p>
            ` : ''}
        </div>
    `).join('');
}

// ==================== RANKING ====================
async function loadRanking() {
    try {
        const response = await fetch(`${API_BASE_URL}/users`, {
            credentials: 'include'
        });
        
        if (response.ok) {
            const data = await response.json();
            const users = (data.users || []).sort((a, b) => b.current_xp - a.current_xp);
            renderRanking(users);
        }
        
    } catch (error) {
        console.error('Ranking load error:', error);
    }
}

function renderRanking(users) {
    const container = document.getElementById('ranking-list');
    
    if (users.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhum usuário no ranking</p>';
        return;
    }
    
    container.innerHTML = users.map((user, index) => {
        let positionClass = 'normal';
        if (index === 0) positionClass = 'gold';
        else if (index === 1) positionClass = 'silver';
        else if (index === 2) positionClass = 'bronze';
        
        return `
            <div class="ranking-item">
                <div class="ranking-position ${positionClass}">${index + 1}</div>
                <div class="ranking-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div class="ranking-info">
                    <div class="ranking-name">${user.username}</div>
                    <div class="ranking-level">Nível ${user.current_level}</div>
                </div>
                <div class="ranking-xp">${user.current_xp} XP</div>
            </div>
        `;
    }).join('');
}

// ==================== ADMIN ====================
async function loadAdminData() {
    if (!state.user || state.user.role !== 'admin') return;
    
    try {
        // Load users
        const usersResponse = await fetch(`${API_BASE_URL}/users`, {
            credentials: 'include'
        });
        
        if (usersResponse.ok) {
            const data = await usersResponse.json();
            state.users = data.users || [];
            renderAdminUsers(state.users);
        }
        
        // Load missions
        const missionsResponse = await fetch(`${API_BASE_URL}/missions-all`, {
            credentials: 'include'
        });
        
        if (missionsResponse.ok) {
            const data = await missionsResponse.json();
            renderAdminMissions(data.missions || []);
        }
        
        // Load achievements
        const achievementsResponse = await fetch(`${API_BASE_URL}/achievements`, {
            credentials: 'include'
        });
        
        if (achievementsResponse.ok) {
            const data = await achievementsResponse.json();
            renderAdminAchievements(data.achievements || []);
        }
        
        // Load rewards
        const rewardsResponse = await fetch(`${API_BASE_URL}/rewards/all`, {
            credentials: 'include'
        });
        
        if (rewardsResponse.ok) {
            const data = await rewardsResponse.json();
            renderAdminRewards(data.rewards || []);
        }
        
        // Load disciplines
        const disciplinesResponse = await fetch(`${API_BASE_URL}/disciplines`, {
            credentials: 'include'
        });
        
        if (disciplinesResponse.ok) {
            const data = await disciplinesResponse.json();
            renderAdminDisciplines(data.disciplines || []);
        }
        
    } catch (error) {
        console.error('Admin load error:', error);
    }
}

function renderAdminUsers(users) {
    const container = document.getElementById('admin-users-list');
    
    container.innerHTML = users.map(user => `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="user-avatar">
                    <i class="fas fa-user"></i>
                </div>
                <div>
                    <div class="admin-item-name">${user.username}</div>
                    <div class="admin-item-role">${user.role}</div>
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editUser(${user.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-icon btn-danger" onclick="deleteUser(${user.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function renderAdminMissions(missions) {
    const container = document.getElementById('admin-missions-list');
    
    container.innerHTML = missions.map(mission => `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="mission-icon">
                    <i class="fas fa-tasks"></i>
                </div>
                <div>
                    <div class="admin-item-name">${mission.name}</div>
                    <div class="admin-item-meta">${mission.xp_reward} XP | ${mission.coin_reward} cristais</div>
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editMission(${mission.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-icon btn-danger" onclick="deleteMission(${mission.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function renderAdminAchievements(achievements) {
    const container = document.getElementById('admin-achievements-list');
    
    container.innerHTML = achievements.map(achievement => `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="achievement-icon">
                    ${achievement.icon || '🏆'}
                </div>
                <div>
                    <div class="admin-item-name">${achievement.name}</div>
                    <div class="admin-item-meta">${achievement.description || ''}</div>
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editAchievement(${achievement.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-icon btn-danger" onclick="deleteAchievement(${achievement.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function renderAdminRewards(rewards) {
    const container = document.getElementById('admin-rewards-list');
    
    container.innerHTML = rewards.map(reward => `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="reward-icon">
                    ${reward.icon || '🎁'}
                </div>
                <div>
                    <div class="admin-item-name">${reward.name}</div>
                    <div class="admin-item-meta">${reward.coin_cost} cristais</div>
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editReward(${reward.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-icon btn-danger" onclick="deleteReward(${reward.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function renderAdminDisciplines(disciplines) {
    const container = document.getElementById('admin-disciplines-list');
    
    container.innerHTML = disciplines.map(discipline => `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="discipline-icon">
                    <i class="fas fa-book"></i>
                </div>
                <div>
                    <div class="admin-item-name">${discipline.nome}</div>
                    <div class="admin-item-meta">${discipline.codigo} | ${discipline.carga_horaria}h</div>
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editDiscipline(${discipline.id})">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-icon btn-danger" onclick="deleteDiscipline(${discipline.id})">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `).join('');
}

// ==================== UI UPDATES ====================
function updateUI() {
    if (!state.user) return;
    
    // Update user info
    document.getElementById('user-name').textContent = state.user.username;
    document.getElementById('user-role').textContent = state.user.role === 'student' ? 'Estudante' : 
                                                         state.user.role === 'teacher' ? 'Professor' : 'Administrador';
    
    // Update stats bar
    document.getElementById('user-level').textContent = `Nível ${state.user.current_level}`;
    document.getElementById('user-xp').textContent = `${state.user.current_xp} XP`;
    document.getElementById('user-coins').textContent = state.user.coins;
    
    // Show/hide admin menu
    const adminItems = document.querySelectorAll('.admin-only');
    adminItems.forEach(item => {
        if (state.user.role === 'admin') {
            item.classList.remove('hidden');
            item.classList.add('visible');
        } else {
            item.classList.add('hidden');
            item.classList.remove('visible');
        }
    });
    
    // Update dashboard stats
    updateDashboardStats();
}

// ==================== TABS ====================
function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === tab) {
            btn.classList.add('active');
        }
    });
    
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const targetContent = document.getElementById(`tab-${tab}`);
    if (targetContent) {
        targetContent.classList.add('active');
    }
}

function switchAdminTab(tab) {
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.adminTab === tab) {
            btn.classList.add('active');
        }
    });
    
    document.querySelectorAll('.admin-tab-content').forEach(content => {
        content.classList.remove('active');
    });
    
    const targetContent = document.getElementById(`admin-tab-${tab}`);
    if (targetContent) {
        targetContent.classList.add('active');
    }
}

// ==================== MODAL ====================
function openModal(title, content, footer = '') {
    elements.modalTitle.textContent = title;
    elements.modalBody.innerHTML = content;
    elements.modalFooter.innerHTML = footer;
    elements.modalOverlay.classList.remove('hidden');
}

function closeModal() {
    elements.modalOverlay.classList.add('hidden');
}

// ==================== TOAST ====================
function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        info: 'fa-info-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
    `;
    
    elements.toastContainer.appendChild(toast);
    
    setTimeout(() => {
        toast.remove();
    }, 3000);
}

// ==================== ACTIONS ====================
async function acceptMission(missionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/missions/${missionId}/assign`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ user_id: state.user.id })
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Missão aceita!', 'success');
            loadMissions();
        } else {
            showToast(data.error || 'Erro ao aceitar missão', 'error');
        }
    } catch (error) {
        console.error('Accept mission error:', error);
        showToast('Erro ao aceitar missão', 'error');
    }
}

async function completeMission(userMissionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/missions/${userMissionId}/complete`, {
            method: 'POST',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast(`Missão completada! +${data.xp_earned} XP`, 'success');
            
            if (data.level_up) {
                showToast(`🎉 Level Up! Você alcançou o nível ${data.new_level}!`, 'success');
            }
            
            // Update user data
            state.user.current_xp = data.total_xp;
            state.user.coins = data.total_coins;
            state.user.current_level = data.new_level;
            updateUI();
            
            loadMissions();
        } else {
            showToast(data.error || 'Erro ao completar missão', 'error');
        }
    } catch (error) {
        console.error('Complete mission error:', error);
        showToast('Erro ao completar missão', 'error');
    }
}

async function purchaseReward(rewardId) {
    try {
        const response = await fetch(`${API_BASE_URL}/purchase-reward/${rewardId}`, {
            method: 'POST',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Recompensa comprada!', 'success');
            state.user.coins = data.remaining_coins;
            updateUI();
            loadRewards();
        } else {
            showToast(data.error || 'Erro ao comprar recompensa', 'error');
        }
    } catch (error) {
        console.error('Purchase reward error:', error);
        showToast('Erro ao comprar recompensa', 'error');
    }
}

async function redeemReward(userRewardId) {
    try {
        const response = await fetch(`${API_BASE_URL}/user_rewards/${userRewardId}/redeem`, {
            method: 'PUT',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Recompensa resgatada!', 'success');
            loadRewards();
        } else {
            showToast(data.error || 'Erro ao resgatar recompensa', 'error');
        }
    } catch (error) {
        console.error('Redeem reward error:', error);
        showToast('Erro ao resgatar recompensa', 'error');
    }
}

// ==================== UTILS ====================
function formatDate(dateString) {
    if (!dateString) return 'N/A';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

// ==================== ADMIN ACTIONS ====================
async function deleteUser(userId) {
    if (!confirm('Tem certeza que deseja excluir este usuário?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Usuário excluído!', 'success');
            loadAdminData();
        } else {
            showToast(data.error || 'Erro ao excluir usuário', 'error');
        }
    } catch (error) {
        console.error('Delete user error:', error);
        showToast('Erro ao excluir usuário', 'error');
    }
}

async function deleteMission(missionId) {
    if (!confirm('Tem certeza que deseja excluir esta missão?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/missions/${missionId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Missão excluída!', 'success');
            loadAdminData();
        } else {
            showToast(data.error || 'Erro ao excluir missão', 'error');
        }
    } catch (error) {
        console.error('Delete mission error:', error);
        showToast('Erro ao excluir missão', 'error');
    }
}

async function deleteAchievement(achievementId) {
    if (!confirm('Tem certeza que deseja excluir esta conquista?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/achievements/${achievementId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Conquista excluída!', 'success');
            loadAdminData();
        } else {
            showToast(data.error || 'Erro ao excluir conquista', 'error');
        }
    } catch (error) {
        console.error('Delete achievement error:', error);
        showToast('Erro ao excluir conquista', 'error');
    }
}

async function deleteReward(rewardId) {
    if (!confirm('Tem certeza que deseja excluir esta recompensa?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/rewards/${rewardId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Recompensa excluída!', 'success');
            loadAdminData();
        } else {
            showToast(data.error || 'Erro ao excluir recompensa', 'error');
        }
    } catch (error) {
        console.error('Delete reward error:', error);
        showToast('Erro ao excluir recompensa', 'error');
    }
}

async function deleteDiscipline(disciplineId) {
    if (!confirm('Tem certeza que deseja excluir esta disciplina?')) return;
    
    try {
        const response = await fetch(`${API_BASE_URL}/disciplines/${disciplineId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        
        const data = await response.json();
        
        if (data.success) {
            showToast('Disciplina excluída!', 'success');
            loadAdminData();
        } else {
            showToast(data.error || 'Erro ao excluir disciplina', 'error');
        }
    } catch (error) {
        console.error('Delete discipline error:', error);
        showToast('Erro ao excluir disciplina', 'error');
    }
}

// Placeholder functions for edit actions
function editUser(userId) {
    showToast('Função de edição em desenvolvimento', 'info');
}

function editMission(missionId) {
    showToast('Função de edição em desenvolvimento', 'info');
}

function editAchievement(achievementId) {
    showToast('Função de edição em desenvolvimento', 'info');
}

function editReward(rewardId) {
    showToast('Função de edição em desenvolvimento', 'info');
}

function editDiscipline(disciplineId) {
    showToast('Função de edição em desenvolvimento', 'info');
}
