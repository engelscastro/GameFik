// ==================== DASHBOARD ====================
async function loadDashboard() {
    if (!state.user) return;

    try {
        const [missionsRes, achievementsRes] = await Promise.all([
            fetch(`${API_BASE_URL}/users/${state.user.id}/missions/pending`, { credentials: 'include' }),
            fetch(`${API_BASE_URL}/user-achievements`, { credentials: 'include' })
        ]);

        if (missionsRes.ok) {
            const data = await missionsRes.json();
            renderPendingMissions(data.missions || []);
        }

        if (achievementsRes.ok) {
            const data = await achievementsRes.json();
            renderRecentAchievements(data.achievements || []);
        }

        updateDashboardStats();
    } catch (error) {
        console.error('Dashboard load error:', error);
    }
}

function updateDashboardStats() {
    if (!state.user) return;

    document.getElementById('welcome-name').textContent = state.user.username;
    document.getElementById('current-xp').textContent = state.user.current_xp || 0;
    document.getElementById('next-level-xp').textContent = ((state.user.current_level || 1) + 1) * 100;

    const xpProgress = ((state.user.current_xp || 0) % 100) / 100 * 100;
    document.getElementById('xp-progress').style.width = `${xpProgress}%`;
}

function renderPendingMissions(missions) {
    const container = document.getElementById('pending-missions-list');
    if (!missions?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão pendente</p>';
        return;
    }

    container.innerHTML = missions.slice(0, 5).map(mission => `
        <div class="mission-item">
            <div class="mission-item-info">
                <i class="fas fa-tasks"></i>
                <span>${mission.mission?.name || 'Missão'}</span>
            </div>
            <button class="btn btn-sm btn-primary" onclick="completeMission(${mission.id})">Completar</button>
        </div>
    `).join('');
}

function renderRecentAchievements(achievements) {
    const container = document.getElementById('recent-achievements-list');
    if (!achievements?.length) {
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

// ==================== ATUALIZAR DASHBOARD DO ALUNO ====================

async function refreshStudentDashboard() {
    if (!state.user) return;

    console.log('🔄 Atualizando dashboard do aluno...');

    try {
        // Buscar dados atualizados do usuário
        const userResponse = await fetch(`${API_BASE_URL}/auth/me`, {
            credentials: 'include'
        });

        if (userResponse.ok) {
            const data = await userResponse.json();
            if (data.success && data.user) {
                // Atualizar estado do usuário
                state.user = data.user;

                console.log('📊 Novos dados do usuário:', {
                    xp: state.user.current_xp,
                    level: state.user.current_level,
                    coins: state.user.coins
                });

                // Atualizar elementos da UI
                document.getElementById('user-level').textContent = `Nível ${state.user.current_level || 1}`;
                document.getElementById('user-xp').textContent = `${state.user.current_xp || 0} XP`;
                document.getElementById('user-coins').textContent = state.user.coins || 0;

                // Atualizar dashboard stats
                updateDashboardStats();
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

        // 🔥 ATUALIZAR RECOMPENSAS DO USUÁRIO
        const rewardsResponse = await fetch(`${API_BASE_URL}/users/${state.user.id}/rewards`, {
            credentials: 'include'
        });

        if (rewardsResponse.ok) {
            const rewardsData = await rewardsResponse.json();
            const rewardsCount = rewardsData.rewards?.length || 0;
            const statRewards = document.getElementById('stat-rewards');
            if (statRewards) statRewards.textContent = rewardsCount;
            console.log('🎁 Recompensas:', rewardsCount);
        }

        // 🔥 ATUALIZAR DISCIPLINAS
        const disciplinesResponse = await fetch(`${API_BASE_URL}/disciplines`, {
            credentials: 'include'
        });

        if (disciplinesResponse.ok) {
            const disciplinesData = await disciplinesResponse.json();
            const disciplinesCount = disciplinesData.disciplines?.length || 0;
            const statDisciplines = document.getElementById('stat-disciplines');
            if (statDisciplines) statDisciplines.textContent = disciplinesCount;
            console.log('📚 Disciplinas:', disciplinesCount);
        }

        console.log('✅ Dashboard atualizado com sucesso!');

    } catch (error) {
        console.error('Erro ao atualizar dashboard:', error);
    }
}