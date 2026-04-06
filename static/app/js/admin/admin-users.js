// ==================== ADMIN - USUÁRIOS (COMPLETO COM EDIÇÃO) ====================

// Inicializar GradeSelector quando o DOM carregar
document.addEventListener('DOMContentLoaded', () => {
    initStudentGradeSelector();

    const roleSelect = document.getElementById('user-role-select');
    if (roleSelect) {
        roleSelect.addEventListener('change', toggleUserFields);
    }
});

function initStudentGradeSelector() {
    const gradeContainer = document.getElementById('student-grade-container');
    if (!gradeContainer) return;

    // Criar seletor de série para estudantes
    if (typeof createGradeSelector !== 'undefined') {
        createGradeSelector('student-grade-container', {
            id: 'student-grade',
            label: 'Ano/Série do Estudante',
            placeholder: 'Selecione o ano/série',
            required: false,
            showInfo: true,
            onChange: (value) => {
                console.log('Série selecionada:', value);
                if (value && typeof getGradeLabel !== 'undefined') {
                    console.log('Série:', getGradeLabel(value));
                }
            }
        });
    }
}

async function loadAdminUsers() {
    try {
        const response = await fetch(`${API_BASE_URL}/users`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            // Buscar perfis adicionais para cada usuário
            const usersWithProfiles = await Promise.all((data.users || []).map(async (user) => {
                if (user.role === 'student') {
                    try {
                        const profileRes = await fetch(`${API_BASE_URL}/students`, { credentials: 'include' });
                        if (profileRes.ok) {
                            const profileData = await profileRes.json();
                            const studentProfile = profileData.students?.find(s => s.user_id === user.id);
                            if (studentProfile) {
                                user.profile = studentProfile;
                            }
                        }
                    } catch(e) { console.log('Erro ao buscar perfil do estudante'); }
                } else if (user.role === 'teacher') {
                    try {
                        const profileRes = await fetch(`${API_BASE_URL}/professors`, { credentials: 'include' });
                        if (profileRes.ok) {
                            const profileData = await profileRes.json();
                            const teacherProfile = profileData.professors?.find(p => p.user_id === user.id);
                            if (teacherProfile) {
                                user.profile = teacherProfile;
                            }
                        }
                    } catch(e) { console.log('Erro ao buscar perfil do professor'); }
                }
                return user;
            }));

            state.users = usersWithProfiles;
            renderAdminUsers(state.users);
        }
    } catch (error) {
        console.error('Load users error:', error);
    }
}

function renderAdminUsers(users) {
    const container = document.getElementById('admin-users-list');
    if (!users?.length) {
        container.innerHTML = '<p class="empty-state">Nenhum usuário cadastrado. <button class="btn btn-sm btn-primary" onclick="showAddUserModal()">Criar primeiro usuário</button></p>';
        return;
    }

    container.innerHTML = users.map(user => {
        // Determinar o nome a ser exibido
        let displayName = user.username; // fallback para username
        let displayRole = '';
        let additionalInfo = '';

        if (user.role === 'student') {
            displayRole = 'Estudante';
            // Tentar pegar o nome do perfil do estudante
            if (user.profile && user.profile.nome) {
                displayName = user.profile.nome;
                additionalInfo = `<small class="admin-item-detail">📚 ${user.profile.curso || 'Curso não definido'} | Matrícula: ${user.profile.matricula || 'N/A'}</small>`;
            } else {
                // Buscar dados do estudante via API se não estiver no profile
                displayName = user.username;
                additionalInfo = `<small class="admin-item-detail">⚠️ Perfil de estudante incompleto</small>`;
            }
        } else if (user.role === 'teacher') {
            displayRole = 'Professor';
            if (user.profile && user.profile.nome) {
                displayName = user.profile.nome;
                additionalInfo = `<small class="admin-item-detail">🏛️ ${user.profile.departamento || 'Departamento não definido'}</small>`;
            } else {
                displayName = user.username;
                additionalInfo = `<small class="admin-item-detail">⚠️ Perfil de professor incompleto</small>`;
            }
        } else if (user.role === 'admin') {
            displayRole = 'Administrador';
            if (user.profile && user.profile.nome) {
                displayName = user.profile.nome;
            } else {
                displayName = user.username;
            }
        }

        // Adicionar série para estudantes se disponível
        let gradeLabel = '';
        if (user.role === 'student' && user.profile?.ano_turma && typeof getGradeLabel !== 'undefined') {
            gradeLabel = `<small class="admin-item-desc">🎓 Série: ${getGradeLabel(user.profile.ano_turma)}</small>`;
        }

        return `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="user-avatar"><i class="fas ${user.role === 'student' ? 'fa-user-graduate' : user.role === 'teacher' ? 'fa-chalkboard-user' : 'fa-user-shield'}"></i></div>
                <div>
                    <div class="admin-item-name">
                        ${escapeHtml(displayName)}
                        <span class="admin-item-username">(${escapeHtml(user.username)})</span>
                    </div>
                    <div class="admin-item-role">${displayRole}</div>
                    ${additionalInfo}
                    ${gradeLabel}
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editUser(${user.id})" title="Editar usuário">
                    <i class="fas fa-edit"></i>
                </button>
                <button class="btn btn-icon btn-danger" onclick="deleteUser(${user.id})" title="Excluir usuário">
                    <i class="fas fa-trash"></i>
                </button>
            </div>
        </div>
    `}).join('');
}

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

    // Limpar e reinicializar o seletor de série
    const gradeContainer = document.getElementById('student-grade-container');
    if (gradeContainer) {
        gradeContainer.innerHTML = '';
        if (typeof createGradeSelector !== 'undefined') {
            createGradeSelector('student-grade-container', {
                id: 'student-grade',
                label: 'Ano/Série do Estudante',
                placeholder: 'Selecione o ano/série',
                required: false,
                showInfo: true
            });
        }
    }

    toggleUserFields();
    openModal('modal-user');
}

// ========== FUNÇÃO DE EDIÇÃO DE USUÁRIO ==========
async function editUser(userId) {
    try {
        const response = await fetch(`${API_BASE_URL}/users/${userId}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.user) {
            const user = data.user;

            document.getElementById('user-id').value = user.id;
            document.getElementById('user-fullname').value = user.profile?.nome || user.username || '';
            document.getElementById('user-cpf').value = user.profile?.cpf || user.username || '';
            document.getElementById('user-role-select').value = user.role;
            document.getElementById('user-password').value = '';
            document.getElementById('user-password').placeholder = 'Deixe em branco para manter a mesma senha';
            document.getElementById('user-modal-title').textContent = 'Editar Usuário';

            // Limpar e recriar seletor de série
            const gradeContainer = document.getElementById('student-grade-container');
            if (gradeContainer && typeof createGradeSelector !== 'undefined') {
                gradeContainer.innerHTML = '';
                createGradeSelector('student-grade-container', {
                    id: 'student-grade',
                    label: 'Ano/Série do Estudante',
                    placeholder: 'Selecione o ano/série',
                    required: false,
                    showInfo: true
                });
            }

            // Preencher campos específicos
            if (user.role === 'student' && user.profile) {
                document.getElementById('user-matricula').value = user.profile.matricula || '';
                document.getElementById('user-curso').value = user.profile.curso || '';
                if (user.profile.ano_turma && typeof setGradeValue !== 'undefined') {
                    setTimeout(() => {
                        try {
                            setGradeValue('student-grade', user.profile.ano_turma);
                        } catch(e) {
                            console.log('Erro ao setar série:', e);
                        }
                    }, 100);
                }
            } else if (user.role === 'teacher' && user.profile) {
                document.getElementById('user-departamento').value = user.profile.departamento || '';
            }

            toggleUserFields();
            openModal('modal-user');
        } else {
            showToast(data.error || 'Erro ao carregar usuário', 'error');
        }
    } catch (error) {
        console.error('Erro ao carregar usuário:', error);
        showToast('Erro ao carregar dados do usuário', 'error');
    }
}

function toggleUserFields() {
    const role = document.getElementById('user-role-select')?.value;
    const studentFields = document.querySelectorAll('.student-fields');
    const teacherFields = document.querySelectorAll('.teacher-fields');
    const gradeContainer = document.getElementById('student-grade-container');

    if (role === 'student') {
        studentFields.forEach(f => f.classList.remove('hidden'));
        teacherFields.forEach(f => f.classList.add('hidden'));
        if (gradeContainer) gradeContainer.style.display = 'block';
    } else if (role === 'teacher') {
        studentFields.forEach(f => f.classList.add('hidden'));
        teacherFields.forEach(f => f.classList.remove('hidden'));
        if (gradeContainer) gradeContainer.style.display = 'none';
    } else {
        studentFields.forEach(f => f.classList.add('hidden'));
        teacherFields.forEach(f => f.classList.add('hidden'));
        if (gradeContainer) gradeContainer.style.display = 'none';
    }
}

// ========== FUNÇÃO DE SALVAR (CRIAR/ATUALIZAR) ==========
async function saveUser() {
    const userId = document.getElementById('user-id').value;
    const isEditing = userId && userId !== '';

    const role = document.getElementById('user-role-select').value;
    const password = document.getElementById('user-password').value;

    const data = {
        nome: document.getElementById('user-fullname').value,
        cpf: document.getElementById('user-cpf').value,
        role: role
    };

    // Só incluir senha se foi preenchida (para edição) ou se for criação
    if (password || !isEditing) {
        data.password = password || (role === 'student' ? 'aluno123' : role === 'teacher' ? 'prof123' : 'admin123');
    }

    if (!data.nome || !data.cpf) {
        showToast('Preencha nome e CPF', 'error');
        return;
    }

    if (role === 'student') {
        data.matricula = document.getElementById('user-matricula').value;
        data.curso = document.getElementById('user-curso').value;

        if (typeof getGradeValue !== 'undefined') {
            const gradeValue = getGradeValue('student-grade');
            if (gradeValue) {
                data.ano_turma = gradeValue;
            }
        }

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
        let url, method;

        if (isEditing) {
            // PUT para edição
            method = 'PUT';
            if (role === 'student') {
                url = `${API_BASE_URL}/students/${userId}`;
            } else if (role === 'teacher') {
                url = `${API_BASE_URL}/professors/${userId}`;
            } else {
                url = `${API_BASE_URL}/users/${userId}`;
            }
        } else {
            // POST para criação
            method = 'POST';
            if (role === 'student') {
                url = `${API_BASE_URL}/students`;
            } else if (role === 'teacher') {
                url = `${API_BASE_URL}/professors`;
            } else {
                url = `${API_BASE_URL}/users`;
                data.username = data.cpf;
            }
        }

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            let gradeMessage = '';
            if (data.ano_turma && typeof getGradeLabel !== 'undefined') {
                gradeMessage = ` (Série: ${getGradeLabel(data.ano_turma)})`;
            }

            if (isEditing) {
                showToast(`Usuário ${data.nome} atualizado com sucesso!${gradeMessage}`, 'success');
            } else {
                const finalPassword = data.password;
                showToast(`Usuário ${data.nome} criado! Senha: ${finalPassword}${gradeMessage}`, 'success');
            }

            closeModal('modal-user');
            await loadAdminUsers();
        } else {
            showToast(result.error || 'Erro ao salvar usuário', 'error');
        }
    } catch (error) {
        console.error('Save user error:', error);
        showToast('Erro ao salvar usuário', 'error');
    }
}

// ========== FUNÇÃO DE DELETAR ==========
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
            await loadAdminUsers();
        } else {
            showToast(data.error || 'Erro ao excluir usuário', 'error');
        }
    } catch (error) {
        console.error('Delete user error:', error);
        showToast('Erro ao excluir usuário', 'error');
    }
}

// ========== FUNÇÃO PARA GARANTIR PERFIS DE PROFESSORES ==========

async function ensureAllTeachersHaveProfiles() {
    console.log('🔧 Verificando e corrigindo perfis de professores...');

    try {
        // Buscar todos os usuários
        const usersRes = await fetch(`${API_BASE_URL}/users`, { credentials: 'include' });
        const usersData = await usersRes.json();

        // Filtrar apenas professores
        const teachers = usersData.users.filter(u => u.role === 'teacher');
        console.log(`📊 Encontrados ${teachers.length} professores no sistema`);

        let fixedCount = 0;

        for (const teacher of teachers) {
            // Verificar se tem perfil
            const hasProfile = teacher.profile !== undefined && teacher.profile !== null;

            if (!hasProfile) {
                console.log(`⚠️ Professor ${teacher.username} (ID: ${teacher.id}) sem perfil. Criando...`);

                // Criar perfil
                const profileData = {
                    user_id: teacher.id,
                    nome: `Professor ${teacher.username}`,
                    cpf: teacher.username,
                    departamento: "Departamento Geral"
                };

                const createRes = await fetch(`${API_BASE_URL}/professors`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    credentials: 'include',
                    body: JSON.stringify(profileData)
                });

                const result = await createRes.json();
                if (result.success) {
                    console.log(`   ✅ Perfil criado para ${teacher.username}`);
                    fixedCount++;
                } else {
                    console.log(`   ❌ Erro ao criar perfil: ${result.error}`);
                }
            } else {
                console.log(`✅ Professor ${teacher.username} já tem perfil`);
            }
        }

        if (fixedCount > 0) {
            console.log(`🎉 ${fixedCount} perfis criados! Recarregando lista...`);
            await loadAdminUsers();
        } else {
            console.log('✅ Todos os professores já têm perfis!');
        }

        showToast(`Verificação concluída: ${fixedCount} perfis criados`, 'success');

    } catch (error) {
        console.error('Erro ao verificar perfis:', error);
        showToast('Erro ao verificar perfis de professores', 'error');
    }
}

// Botão para executar a verificação (opcional)
function addFixTeacherButton() {
    const adminSection = document.querySelector('#admin-tab-users .admin-section');
    if (adminSection && !document.getElementById('fix-teacher-btn')) {
        const fixBtn = document.createElement('button');
        fixBtn.id = 'fix-teacher-btn';
        fixBtn.className = 'btn btn-warning';
        fixBtn.style.marginLeft = '1rem';
        fixBtn.innerHTML = '<i class="fas fa-tools"></i> Corrigir Perfis';
        fixBtn.onclick = ensureAllTeachersHaveProfiles;

        const header = adminSection.querySelector('.admin-section-header');
        if (header) {
            header.appendChild(fixBtn);
        }
    }
}

// Chamar a verificação quando carregar a página admin
const originalLoadAdminUsers = loadAdminUsers;
window.loadAdminUsers = async function() {
    await originalLoadAdminUsers();
    setTimeout(addFixTeacherButton, 100);
};