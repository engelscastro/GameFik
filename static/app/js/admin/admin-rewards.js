// ==================== ADMIN - RECOMPENSAS (COMPLETO) ====================

async function loadAdminRewards() {
    try {
        const response = await fetch(`${API_BASE_URL}/rewards/all`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderAdminRewards(data.rewards || []);
        }
    } catch (error) {
        console.error('Load rewards error:', error);
    }
}

function renderAdminRewards(rewards) {
    const container = document.getElementById('admin-rewards-list');
    if (!rewards?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma recompensa cadastrada. <button class="btn btn-sm btn-primary" onclick="showAddRewardModal()">Criar primeira recompensa</button></p>';
        return;
    }

    container.innerHTML = rewards.map(reward => `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="reward-icon">${reward.icon || '🎁'}</div>
                <div>
                    <div class="admin-item-name">${escapeHtml(reward.name)}</div>
                    <div class="admin-item-meta">${reward.coin_cost} cristais</div>
                    <small class="admin-item-desc">${escapeHtml(reward.description || 'Sem descrição')}</small>
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editReward(${reward.id})"><i class="fas fa-edit"></i></button>
                <button class="btn btn-icon btn-danger" onclick="deleteReward(${reward.id})"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `).join('');
}

function showAddRewardModal() {
    document.getElementById('reward-id').value = '';
    document.getElementById('reward-name').value = '';
    document.getElementById('reward-description').value = '';
    document.getElementById('reward-icon').value = '🎁';
    document.getElementById('reward-cost').value = '50';
    document.getElementById('reward-type').value = 'item';
    document.getElementById('reward-modal-title').textContent = 'Nova Recompensa';
    openModal('modal-reward');
}

// ========== FUNÇÃO DE EDIÇÃO ==========
async function editReward(rewardId) {
    try {
        const response = await fetch(`${API_BASE_URL}/rewards/${rewardId}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.reward) {
            document.getElementById('reward-id').value = rewardId;
            document.getElementById('reward-name').value = data.reward.name || '';
            document.getElementById('reward-description').value = data.reward.description || '';
            document.getElementById('reward-icon').value = data.reward.icon || '🎁';
            document.getElementById('reward-cost').value = data.reward.coin_cost || 50;
            document.getElementById('reward-type').value = data.reward.type || 'item';
            document.getElementById('reward-modal-title').textContent = 'Editar Recompensa';

            openModal('modal-reward');
        } else {
            showToast(data.error || 'Erro ao carregar recompensa', 'error');
        }
    } catch (error) {
        console.error('Erro ao carregar recompensa:', error);
        showToast('Erro ao carregar dados da recompensa', 'error');
    }
}

// ========== FUNÇÃO DE SALVAR (CRIAR/ATUALIZAR) ==========
async function saveReward() {
    const rewardId = document.getElementById('reward-id').value;
    const data = {
        name: document.getElementById('reward-name').value,
        description: document.getElementById('reward-description').value,
        icon: document.getElementById('reward-icon').value,
        coin_cost: parseInt(document.getElementById('reward-cost').value),
        type: document.getElementById('reward-type').value
    };

    if (!data.name || !data.coin_cost) {
        showToast('Preencha todos os campos obrigatórios', 'error');
        return;
    }

    try {
        const url = `${API_BASE_URL}/rewards${rewardId ? `/${rewardId}` : ''}`;
        const method = rewardId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast(rewardId ? 'Recompensa atualizada!' : 'Recompensa criada!', 'success');
            closeModal('modal-reward');
            await loadAdminRewards();
            if (state.currentPage === 'rewards') await loadRewards();
        } else {
            showToast(result.error || 'Erro ao salvar recompensa', 'error');
        }
    } catch (error) {
        console.error('Save reward error:', error);
        showToast('Erro ao salvar recompensa', 'error');
    }
}

// ========== FUNÇÃO DE DELETAR ==========
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
            await loadAdminRewards();
            if (state.currentPage === 'rewards') await loadRewards();
        } else {
            showToast(data.error || 'Erro ao excluir recompensa', 'error');
        }
    } catch (error) {
        console.error('Delete reward error:', error);
        showToast('Erro ao excluir recompensa', 'error');
    }
}