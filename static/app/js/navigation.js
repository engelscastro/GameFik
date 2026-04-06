// ==================== NAVEGAÇÃO ====================
async function navigateTo(page) {
    state.currentPage = page;

    document.querySelectorAll('.nav-item').forEach(item => {
        item.classList.toggle('active', item.dataset.page === page);
    });

    document.querySelectorAll('.page').forEach(p => {
        p.classList.toggle('active', p.id === `page-${page}`);
    });

    await loadPageData(page);
}

async function loadPageData(page) {
    const pageLoaders = {
        dashboard: () => loadDashboard(),
        missions: () => loadMissions(),
        achievements: () => loadAchievements(),
        rewards: () => loadRewards(),
        disciplines: () => loadDisciplines(),
        ranking: () => loadRanking(),
        admin: () => loadAdminData()
    };

    const loader = pageLoaders[page];
    if (loader) await loader();
}