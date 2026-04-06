// ==================== MISSÕES ====================

async function loadMissions() {
    if (!state.user) return;

    try {
        const [availableRes, pendingRes, completedRes] = await Promise.all([
            fetch(`${API_BASE_URL}/missions/available`, { credentials: 'include' }),
            fetch(`${API_BASE_URL}/users/${state.user.id}/missions/pending`, { credentials: 'include' }),
            fetch(`${API_BASE_URL}/users/${state.user.id}/missions/completed`, { credentials: 'include' })
        ]);

        if (availableRes.ok) {
            const data = await availableRes.json();
            renderAvailableMissions(data.missions || []);
        }

        if (pendingRes.ok) {
            const data = await pendingRes.json();
            renderPendingMissionsGrid(data.missions || []);
        }

        if (completedRes.ok) {
            const data = await completedRes.json();
            renderCompletedMissions(data.missions || []);
        }
    } catch (error) {
        console.error('Missions load error:', error);
    }
}

function renderAvailableMissions(missions) {
    const container = document.getElementById('available-missions-grid');
    if (!missions?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão disponível</p>';
        return;
    }

    container.innerHTML = missions.map(mission => `
        <div class="mission-card">
            <div class="mission-header">
                <div class="mission-icon"><i class="fas fa-tasks"></i></div>
            </div>
            <h4 class="mission-title">${escapeHtml(mission.name)}</h4>
            <p class="mission-description">${escapeHtml(mission.description || '')}</p>
            <div class="mission-rewards">
                <span class="mission-reward"><i class="fas fa-bolt"></i> ${mission.xp_reward} XP</span>
                <span class="mission-reward coins"><i class="fas fa-gem"></i> ${mission.coin_reward}</span>
            </div>
            <button class="btn btn-primary btn-full" onclick="acceptMission(${mission.id})">Aceitar Missão</button>
        </div>
    `).join('');
}

function renderPendingMissionsGrid(missions) {
    const container = document.getElementById('pending-missions-grid');
    if (!missions?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão pendente</p>';
        return;
    }

    container.innerHTML = missions.map(mission => `
        <div class="mission-card">
            <div class="mission-header">
                <div class="mission-icon"><i class="fas fa-tasks"></i></div>
                <span class="mission-status pending">Pendente</span>
            </div>
            <h4 class="mission-title">${escapeHtml(mission.mission?.name || 'Missão')}</h4>
            <p class="mission-description">${escapeHtml(mission.mission?.description || '')}</p>
            <div class="mission-rewards">
                <span class="mission-reward"><i class="fas fa-bolt"></i> ${mission.mission?.xp_reward || 0} XP</span>
                <span class="mission-reward coins"><i class="fas fa-gem"></i> ${mission.mission?.coin_reward || 0}</span>
            </div>
            <button class="btn btn-success btn-full" onclick="completeMission(${mission.id})">Completar</button>
        </div>
    `).join('');
}

function renderCompletedMissions(missions) {
    const container = document.getElementById('completed-missions-grid');
    if (!missions?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão completada</p>';
        return;
    }

    container.innerHTML = missions.map(mission => `
        <div class="mission-card">
            <div class="mission-header">
                <div class="mission-icon"><i class="fas fa-check"></i></div>
                <span class="mission-status completed">Completada</span>
            </div>
            <h4 class="mission-title">${escapeHtml(mission.mission?.name || 'Missão')}</h4>
            <p class="mission-description">${escapeHtml(mission.mission?.description || '')}</p>
            <p class="mission-date">Completada em: ${formatDate(mission.completion_date)}</p>
        </div>
    `).join('');
}

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
            await loadMissions();
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

            // Atualizar estado do usuário
            state.user.current_xp = data.total_xp;
            state.user.coins = data.total_coins;
            state.user.current_level = data.new_level;

            // Atualizar UI
            await updateUI();

            // Recarregar listas
            await loadMissions();
            await loadDashboard();

            // 🔥 FORÇAR ATUALIZAÇÃO DO DASHBOARD
            await refreshStudentDashboard();

        } else {
            showToast(data.error || 'Erro ao completar missão', 'error');
        }
    } catch (error) {
        console.error('Complete mission error:', error);
        showToast('Erro ao completar missão', 'error');
    }
}
