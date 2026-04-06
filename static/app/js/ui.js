// ==================== UI COMPONENTS ====================
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
        particle.style.background = PARTICLE_COLORS[Math.floor(Math.random() * PARTICLE_COLORS.length)];
        container.appendChild(particle);
    }
}

function switchTab(tab) {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });

    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `tab-${tab}`);
    });
}

function switchAdminTab(tab) {
    document.querySelectorAll('.admin-tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.adminTab === tab);
    });

    document.querySelectorAll('.admin-tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `admin-tab-${tab}`);
    });
}

function updateUserUI() {
    if (!state.user) return;

    document.getElementById('user-name').textContent = state.user.username;
    document.getElementById('user-role').textContent =
        state.user.role === 'student' ? 'Estudante' :
        state.user.role === 'teacher' ? 'Professor' : 'Administrador';

    document.getElementById('user-level').textContent = `Nível ${state.user.current_level || 1}`;
    document.getElementById('user-xp').textContent = `${state.user.current_xp || 0} XP`;
    document.getElementById('user-coins').textContent = state.user.coins || 0;

    // Mostrar/esconder elementos admin
    const adminElements = document.querySelectorAll('.admin-only');
    const isAdmin = state.user.role === 'admin';
    adminElements.forEach(el => {
        if (isAdmin) el.classList.remove('hidden');
        else el.classList.add('hidden');
    });
}