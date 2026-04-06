// ==================== ADMIN - MISSÕES (COMPLETO) ====================

async function loadAdminMissions() {
    try {
        const response = await fetch(`${API_BASE_URL}/missions-all`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderAdminMissions(data.missions || []);
        }
    } catch (error) {
        console.error('Load missions error:', error);
    }
}

function renderAdminMissions(missions) {
    const container = document.getElementById('admin-missions-list');
    if (!missions?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma missão cadastrada. <button class="btn btn-sm btn-primary" onclick="showAddMissionModal()">Criar primeira missão</button></p>';
        return;
    }

    container.innerHTML = missions.map(mission => `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="mission-icon"><i class="fas fa-tasks"></i></div>
                <div>
                    <div class="admin-item-name">${escapeHtml(mission.name)}</div>
                    <div class="admin-item-meta">${mission.xp_reward} XP | ${mission.coin_reward} cristais</div>
                    <small class="admin-item-desc">${escapeHtml(mission.description || 'Sem descrição')}</small>
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editMission(${mission.id})"><i class="fas fa-edit"></i></button>
                <button class="btn btn-icon btn-danger" onclick="deleteMission(${mission.id})"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `).join('');
}

function showAddMissionModal() {
    document.getElementById('mission-id').value = '';
    document.getElementById('mission-name').value = '';
    document.getElementById('mission-description').value = '';
    document.getElementById('mission-xp').value = '50';
    document.getElementById('mission-coins').value = '10';
    document.getElementById('mission-modal-title').textContent = 'Nova Missão';
    loadDisciplinesForSelect();
    openModal('modal-mission');
}

// ========== FUNÇÃO DE EDIÇÃO ==========
async function editMission(missionId) {
    try {
        const response = await fetch(`${API_BASE_URL}/missions/${missionId}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.mission) {
            document.getElementById('mission-id').value = missionId;
            document.getElementById('mission-name').value = data.mission.name || '';
            document.getElementById('mission-description').value = data.mission.description || '';
            document.getElementById('mission-xp').value = data.mission.xp_reward || 0;
            document.getElementById('mission-coins').value = data.mission.coin_reward || 0;
            document.getElementById('mission-modal-title').textContent = 'Editar Missão';

            // Carregar disciplinas e selecionar a atual
            await loadDisciplinesForSelect();
            if (data.mission.discipline_id) {
                document.getElementById('mission-discipline').value = data.mission.discipline_id;
            }

            openModal('modal-mission');
        } else {
            showToast(data.error || 'Erro ao carregar missão', 'error');
        }
    } catch (error) {
        console.error('Erro ao carregar missão:', error);
        showToast('Erro ao carregar dados da missão', 'error');
    }
}

// ========== FUNÇÃO DE SALVAR (CRIAR/ATUALIZAR) ==========
async function saveMission() {
    const missionId = document.getElementById('mission-id').value;
    const data = {
        name: document.getElementById('mission-name').value,
        description: document.getElementById('mission-description').value,
        xp_reward: parseInt(document.getElementById('mission-xp').value),
        coin_reward: parseInt(document.getElementById('mission-coins').value),
        discipline_id: document.getElementById('mission-discipline').value || null
    };

    if (!data.name) {
        showToast('Preencha o nome da missão', 'error');
        return;
    }

    try {
        const url = `${API_BASE_URL}/missions${missionId ? `/${missionId}` : ''}`;
        const method = missionId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast(missionId ? 'Missão atualizada!' : 'Missão criada!', 'success');
            closeModal('modal-mission');
            await loadAdminMissions();
            if (state.currentPage === 'missions') await loadMissions();
        } else {
            showToast(result.error || 'Erro ao salvar missão', 'error');
        }
    } catch (error) {
        console.error('Save mission error:', error);
        showToast('Erro ao salvar missão', 'error');
    }
}

// ========== FUNÇÃO DE DELETAR ==========
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
            await loadAdminMissions();
            if (state.currentPage === 'missions') await loadMissions();
        } else {
            showToast(data.error || 'Erro ao excluir missão', 'error');
        }
    } catch (error) {
        console.error('Delete mission error:', error);
        showToast('Erro ao excluir missão', 'error');
    }
}