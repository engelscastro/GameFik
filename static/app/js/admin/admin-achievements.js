// ==================== ADMIN - CONQUISTAS (COMPLETO) ====================

async function loadAdminAchievements() {
    try {
        const response = await fetch(`${API_BASE_URL}/achievements`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderAdminAchievements(data.achievements || []);
        }
    } catch (error) {
        console.error('Load achievements error:', error);
    }
}

function renderAdminAchievements(achievements) {
    const container = document.getElementById('admin-achievements-list');
    if (!achievements?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma conquista cadastrada. <button class="btn btn-sm btn-primary" onclick="showAddAchievementModal()">Criar primeira conquista</button></p>';
        return;
    }

    container.innerHTML = achievements.map(achievement => `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="achievement-icon">${achievement.icon || '🏆'}</div>
                <div>
                    <div class="admin-item-name">${escapeHtml(achievement.name)}</div>
                    <div class="admin-item-meta">${achievement.points || 0} pontos</div>
                    <small class="admin-item-desc">${escapeHtml(achievement.description || 'Sem descrição')}</small>
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editAchievement(${achievement.id})"><i class="fas fa-edit"></i></button>
                <button class="btn btn-icon btn-danger" onclick="deleteAchievement(${achievement.id})"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `).join('');
}

function showAddAchievementModal() {
    document.getElementById('achievement-id').value = '';
    document.getElementById('achievement-name').value = '';
    document.getElementById('achievement-description').value = '';
    document.getElementById('achievement-icon').value = '🏆';
    document.getElementById('achievement-points').value = '100';
    document.getElementById('achievement-modal-title').textContent = 'Nova Conquista';
    openModal('modal-achievement');
}

// ========== FUNÇÃO DE EDIÇÃO ==========
async function editAchievement(achievementId) {
    try {
        const response = await fetch(`${API_BASE_URL}/achievements/${achievementId}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.achievement) {
            document.getElementById('achievement-id').value = achievementId;
            document.getElementById('achievement-name').value = data.achievement.name || '';
            document.getElementById('achievement-description').value = data.achievement.description || '';
            document.getElementById('achievement-icon').value = data.achievement.icon || '🏆';
            document.getElementById('achievement-points').value = data.achievement.points || 100;
            document.getElementById('achievement-modal-title').textContent = 'Editar Conquista';

            openModal('modal-achievement');
        } else {
            showToast(data.error || 'Erro ao carregar conquista', 'error');
        }
    } catch (error) {
        console.error('Erro ao carregar conquista:', error);
        showToast('Erro ao carregar dados da conquista', 'error');
    }
}

// ========== FUNÇÃO DE SALVAR (CRIAR/ATUALIZAR) ==========
async function saveAchievement() {
    const achievementId = document.getElementById('achievement-id').value;
    const data = {
        name: document.getElementById('achievement-name').value,
        description: document.getElementById('achievement-description').value,
        icon: document.getElementById('achievement-icon').value,
        points: parseInt(document.getElementById('achievement-points').value)
    };

    if (!data.name) {
        showToast('Preencha o nome da conquista', 'error');
        return;
    }

    try {
        const url = `${API_BASE_URL}/achievements${achievementId ? `/${achievementId}` : ''}`;
        const method = achievementId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast(achievementId ? 'Conquista atualizada!' : 'Conquista criada!', 'success');
            closeModal('modal-achievement');
            await loadAdminAchievements();
            if (state.currentPage === 'achievements') await loadAchievements();
        } else {
            showToast(result.error || 'Erro ao salvar conquista', 'error');
        }
    } catch (error) {
        console.error('Save achievement error:', error);
        showToast('Erro ao salvar conquista', 'error');
    }
}

// ========== FUNÇÃO DE DELETAR ==========
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
            await loadAdminAchievements();
            if (state.currentPage === 'achievements') await loadAchievements();
        } else {
            showToast(data.error || 'Erro ao excluir conquista', 'error');
        }
    } catch (error) {
        console.error('Delete achievement error:', error);
        showToast('Erro ao excluir conquista', 'error');
    }
}