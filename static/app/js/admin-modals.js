// ==================== ADMIN MODAL FUNCTIONS ====================

// MISSIONS
function showAddMissionModal() {
    document.getElementById('mission-id').value = '';
    document.getElementById('mission-name').value = '';
    document.getElementById('mission-description').value = '';
    document.getElementById('mission-xp').value = '50';
    document.getElementById('mission-coins').value = '10';
    document.getElementById('mission-modal-title').textContent = 'Nova Missão';
    loadDisciplinesForSelect();
    openModalById('modal-mission');
}

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
        const response = await fetch(`${API_BASE_URL}/missions`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            showToast('Missão criada com sucesso!', 'success');
            closeModal('modal-mission');
            await loadAdminData();
        } else {
            showToast(result.error || 'Erro ao criar missão', 'error');
        }
    } catch (error) {
        showToast('Erro ao criar missão', 'error');
    }
}

// ACHIEVEMENTS
function showAddAchievementModal() {
    document.getElementById('achievement-id').value = '';
    document.getElementById('achievement-name').value = '';
    document.getElementById('achievement-description').value = '';
    document.getElementById('achievement-icon').value = '🏆';
    document.getElementById('achievement-points').value = '100';
    document.getElementById('achievement-modal-title').textContent = 'Nova Conquista';
    openModalById('modal-achievement');
}

async function saveAchievement() {
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
        const response = await fetch(`${API_BASE_URL}/achievements`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            showToast('Conquista criada com sucesso!', 'success');
            closeModal('modal-achievement');
            await loadAdminData();
        } else {
            showToast(result.error || 'Erro ao criar conquista', 'error');
        }
    } catch (error) {
        showToast('Erro ao criar conquista', 'error');
    }
}

// REWARDS
function showAddRewardModal() {
    document.getElementById('reward-id').value = '';
    document.getElementById('reward-name').value = '';
    document.getElementById('reward-description').value = '';
    document.getElementById('reward-icon').value = '🎁';
    document.getElementById('reward-cost').value = '50';
    document.getElementById('reward-type').value = 'item';
    document.getElementById('reward-modal-title').textContent = 'Nova Recompensa';
    openModalById('modal-reward');
}

async function saveReward() {
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
        const response = await fetch(`${API_BASE_URL}/rewards`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            showToast('Recompensa criada com sucesso!', 'success');
            closeModal('modal-reward');
            await loadAdminData();
        } else {
            showToast(result.error || 'Erro ao criar recompensa', 'error');
        }
    } catch (error) {
        showToast('Erro ao criar recompensa', 'error');
    }
}

// DISCIPLINES
function showAddDisciplineModal() {
    document.getElementById('discipline-id').value = '';
    document.getElementById('discipline-code').value = '';
    document.getElementById('discipline-name').value = '';
    document.getElementById('discipline-hours').value = '60';
    document.getElementById('discipline-year').value = '';
    document.getElementById('discipline-modal-title').textContent = 'Nova Disciplina';
    loadProfessorsForSelect();
    openModalById('modal-discipline');
}

async function saveDiscipline() {
    const data = {
        codigo: document.getElementById('discipline-code').value,
        nome: document.getElementById('discipline-name').value,
        carga_horaria: parseInt(document.getElementById('discipline-hours').value),
        professor_id: document.getElementById('discipline-professor').value || null,
        ano_turma: document.getElementById('discipline-year').value
    };

    if (!data.codigo || !data.nome || !data.carga_horaria) {
        showToast('Preencha todos os campos obrigatórios', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/disciplines`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });
        const result = await response.json();

        if (result.success) {
            showToast('Disciplina criada com sucesso!', 'success');
            closeModal('modal-discipline');
            await loadAdminData();
        } else {
            showToast(result.error || 'Erro ao criar disciplina', 'error');
        }
    } catch (error) {
        showToast('Erro ao criar disciplina', 'error');
    }
}

// USERS
function showAddUserModal() {
    document.getElementById('user-id').value = '';
    document.getElementById('user-fullname').value = '';
    document.getElementById('user-cpf').value = '';
    document.getElementById('user-password').value = '';
    document.getElementById('user-role-select').value = 'student';
    document.getElementById('user-matricula').value = '';
    document.getElementById('user-curso').value = '';
    document.getElementById('user-departamento').value = '';
    document.getElementById('user-modal-title').textContent = 'Novo Usuário';
    toggleUserFields();
    openModalById('modal-user');
}

function toggleUserFields() {
    const role = document.getElementById('user-role-select')?.value;
    const studentFields = document.querySelectorAll('.student-fields');
    const teacherFields = document.querySelectorAll('.teacher-fields');

    if (role === 'student') {
        studentFields.forEach(f => f.classList.remove('hidden'));
        teacherFields.forEach(f => f.classList.add('hidden'));
    } else if (role === 'teacher') {
        studentFields.forEach(f => f.classList.add('hidden'));
        teacherFields.forEach(f => f.classList.remove('hidden'));
    } else {
        studentFields.forEach(f => f.classList.add('hidden'));
        teacherFields.forEach(f => f.classList.add('hidden'));
    }
}

async function saveUser() {
    const role = document.getElementById('user-role-select').value;
    const password = document.getElementById('user-password').value;
    const finalPassword = password || (role === 'student' ? 'aluno123' : role === 'teacher' ? 'prof123' : 'admin123');

    const data = {
        nome: document.getElementById('user-fullname').value,
        cpf: document.getElementById('user-cpf').value,
        role: role,
        password: finalPassword
    };

    if (!data.nome || !data.cpf) {
        showToast('Preencha nome e CPF', 'error');
        return;
    }

    if (role === 'student') {
        data.matricula = document.getElementById('user-matricula').value;
        data.curso = document.getElementById('user-curso').value;
        if (!data.matricula || !data.curso) {
            showToast('Matrícula e curso são obrigatórios', 'error');
            return;
        }
    } else if (role === 'teacher') {
        data.departamento = document.getElementById('user-departamento').value;
        if (!data.departamento) {
            showToast('Departamento é obrigatório', 'error');
            return;
        }
    }

    try {
        let url, response;

        if (role === 'student') {
            url = `${API_BASE_URL}/students`;
        } else if (role === 'teacher') {
            url = `${API_BASE_URL}/professors`;
        } else {
            url = `${API_BASE_URL}/users`;
            data.username = data.cpf;
        }

        response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast(`Usuário criado! Senha: ${finalPassword}`, 'success');
            closeModal('modal-user');
            await loadAdminData();
        } else {
            showToast(result.error || 'Erro ao criar usuário', 'error');
        }
    } catch (error) {
        showToast('Erro ao criar usuário', 'error');
    }
}

// HELPER FUNCTIONS
async function loadDisciplinesForSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/disciplines`, { credentials: 'include' });
        const data = await response.json();
        if (data.success && data.disciplines) {
            const select = document.getElementById('mission-discipline');
            select.innerHTML = '<option value="">Todas as disciplinas</option>';
            data.disciplines.forEach(d => {
                const option = document.createElement('option');
                option.value = d.id;
                option.textContent = `${d.codigo} - ${d.nome}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar disciplinas:', error);
    }
}

async function loadProfessorsForSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/professors`, { credentials: 'include' });
        const data = await response.json();
        if (data.success && data.professors) {
            const select = document.getElementById('discipline-professor');
            select.innerHTML = '<option value="">Selecione um professor</option>';
            data.professors.forEach(p => {
                const option = document.createElement('option');
                option.value = p.id;
                option.textContent = p.nome;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erro ao carregar professores:', error);
    }
}

function openModalById(modalId) {
    document.getElementById(modalId).classList.remove('hidden');
}

function closeModal(modalId) {
    document.getElementById(modalId).classList.add('hidden');
}

// Event listener para o select de role
document.addEventListener('DOMContentLoaded', () => {
    const roleSelect = document.getElementById('user-role-select');
    if (roleSelect) {
        roleSelect.addEventListener('change', toggleUserFields);
    }
});