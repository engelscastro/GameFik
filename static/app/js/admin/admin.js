// ==================== ADMIN CORE ====================

async function loadAdminData() {
    if (!state.user || state.user.role !== 'admin') return;

    try {
        await Promise.all([
            loadAdminUsers(),
            loadAdminMissions(),
            loadAdminAchievements(),
            loadAdminRewards(),
            loadAdminDisciplines()
        ]);
    } catch (error) {
        console.error('Admin load error:', error);
    }
}

// Funções de deleção
async function deleteUser(userId) {
    if (!confirm('Tem certeza que deseja excluir este usuário?')) return;
    await executeDelete(`${API_BASE_URL}/users/${userId}`, 'Usuário excluído!');
}

async function deleteMission(missionId) {
    if (!confirm('Tem certeza que deseja excluir esta missão?')) return;
    await executeDelete(`${API_BASE_URL}/missions/${missionId}`, 'Missão excluída!');
}

async function deleteAchievement(achievementId) {
    if (!confirm('Tem certeza que deseja excluir esta conquista?')) return;
    await executeDelete(`${API_BASE_URL}/achievements/${achievementId}`, 'Conquista excluída!');
}

async function deleteReward(rewardId) {
    if (!confirm('Tem certeza que deseja excluir esta recompensa?')) return;
    await executeDelete(`${API_BASE_URL}/rewards/${rewardId}`, 'Recompensa excluída!');
}

async function deleteDiscipline(disciplineId) {
    if (!confirm('Tem certeza que deseja excluir esta disciplina?')) return;
    await executeDelete(`${API_BASE_URL}/disciplines/${disciplineId}`, 'Disciplina excluída!');
}

async function executeDelete(url, successMessage) {
    try {
        const response = await fetch(url, { method: 'DELETE', credentials: 'include' });
        const data = await response.json();

        if (data.success) {
            showToast(successMessage, 'success');
            await loadAdminData();
        } else {
            showToast(data.error || 'Erro ao excluir', 'error');
        }
    } catch (error) {
        console.error('Delete error:', error);
        showToast('Erro ao excluir', 'error');
    }
}

// Funções de edição (placeholder)
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