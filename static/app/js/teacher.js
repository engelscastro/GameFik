// ==================== DASHBOARD DO PROFESSOR ====================

async function loadTeacherDashboard() {
    if (!state.user || state.user.role !== 'teacher') return;

    console.log('👨‍🏫 Carregando dashboard do professor...');

    try {
        await loadTeacherStats();
        await loadTeacherDisciplines();
        await loadTeacherRecentActivities();
    } catch (error) {
        console.error('Erro ao carregar dashboard do professor:', error);
    }
}

async function loadTeacherStats() {
    try {
        const response = await fetch(`${API_BASE_URL}/teacher/stats`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();

            const elements = {
                'teacher-total-disciplines': data.total_disciplines || 0,
                'teacher-total-students': data.total_students || 0,
                'teacher-total-missions': data.total_missions || 0,
                'teacher-total-xp': data.total_xp_awarded || 0
            };

            for (const [id, value] of Object.entries(elements)) {
                const el = document.getElementById(id);
                if (el) el.textContent = value;
            }
        }
    } catch (error) {
        console.error('Erro ao carregar estatísticas:', error);
    }
}

async function loadTeacherDisciplines() {
    if (!state.user || state.user.role !== 'teacher') return;

    console.log('👨‍🏫 Carregando disciplinas do professor...');

    const normalGrid = document.getElementById('disciplines-grid');
    const teacherContainer = document.getElementById('teacher-disciplines-container');

    if (normalGrid) normalGrid.classList.add('hidden');
    if (teacherContainer) teacherContainer.classList.remove('hidden');

    try {
        const response = await fetch(`${API_BASE_URL}/teacher/disciplines`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            renderTeacherDisciplines(data.disciplines || []);
        } else {
            const error = await response.json();
            console.error('Erro:', error);
            showToast(error.error || 'Erro ao carregar disciplinas', 'error');
        }
    } catch (error) {
        console.error('Erro ao carregar disciplinas do professor:', error);
        showToast('Erro ao carregar disciplinas', 'error');
    }
}

function renderTeacherDisciplines(disciplines) {
    const container = document.getElementById('teacher-disciplines-container');
    if (!container) return;

    if (!disciplines || disciplines.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chalkboard-teacher" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <h3>Nenhuma disciplina atribuída</h3>
                <p>Você ainda não está ministrando nenhuma disciplina.</p>
                <small>Entre em contato com o administrador para atribuir disciplinas a você.</small>
            </div>
        `;
        return;
    }

    const totalStudents = disciplines.reduce((sum, d) => sum + (d.student_count || 0), 0);

    container.innerHTML = `
        <div class="teacher-stats">
            <div class="teacher-stat-card">
                <i class="fas fa-book"></i>
                <div class="stat-value">${disciplines.length}</div>
                <div class="stat-label">Disciplinas Ministradas</div>
            </div>
            <div class="teacher-stat-card">
                <i class="fas fa-users"></i>
                <div class="stat-value">${totalStudents}</div>
                <div class="stat-label">Total de Alunos</div>
            </div>
            <div class="teacher-stat-card">
                <i class="fas fa-tasks"></i>
                <div class="stat-value">0</div>
                <div class="stat-label">Missões Ativas</div>
            </div>
        </div>

        <div class="teacher-disciplines-grid">
            ${disciplines.map(discipline => `
                <div class="teacher-discipline-card">
                    <div class="discipline-header">
                        <div class="discipline-code">${escapeHtml(discipline.codigo)}</div>
                        <div class="discipline-students-badge">
                            <i class="fas fa-users"></i> ${discipline.student_count || 0} alunos
                        </div>
                    </div>
                    <h3 class="discipline-name">${escapeHtml(discipline.nome)}</h3>
                    <div class="discipline-info">
                        <span><i class="fas fa-clock"></i> ${discipline.carga_horaria}h</span>
                        <span><i class="fas fa-graduation-cap"></i> ${discipline.ano_turma || 'Turma não definida'}</span>
                    </div>
                    <div class="discipline-actions">
                        <button class="btn btn-sm btn-primary" onclick="showDisciplineStudents(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-users"></i> Ver Alunos
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="createMissionForDiscipline(${discipline.id})">
                            <i class="fas fa-plus"></i> Nova Missão
                        </button>
                        <button class="btn btn-sm btn-info" onclick="openDisciplineChat(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-comment"></i> Chat
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>

        <div id="discipline-students-modal" class="modal-overlay hidden">
            <div class="modal modal-large">
                <div class="modal-header">
                    <h3 id="discipline-students-title">Alunos da Disciplina</h3>
                    <button class="btn btn-close" onclick="closeModalById('discipline-students-modal')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div id="discipline-students-list"></div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModalById('discipline-students-modal')">Fechar</button>
                </div>
            </div>
        </div>
    `;
}

async function showDisciplineStudents(disciplineId, disciplineName) {
    console.log(`📚 Buscando alunos da disciplina: ${disciplineName}`);
    showToast('Carregando alunos...', 'info');

    try {
        const response = await fetch(`${API_BASE_URL}/teacher/my-disciplines/${disciplineId}/students`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();

            const title = document.getElementById('discipline-students-title');
            if (title) title.textContent = `${data.discipline || disciplineName} - Alunos Matriculados`;

            const container = document.getElementById('discipline-students-list');

            if (!data.students || data.students.length === 0) {
                container.innerHTML = '<p class="empty-state">Nenhum aluno matriculado nesta disciplina.</p>';
            } else {
                container.innerHTML = `
                    <div class="students-table-container">
                        <table class="students-table">
                            <thead>
                                <tr>
                                    <th>Matrícula</th>
                                    <th>Nome</th>
                                    <th>Curso</th>
                                    <th>Turma</th>
                                    <th>Nível</th>
                                    <th>XP</th>
                                    <th>Ações</th>
                                </tr>
                            </thead>
                            <tbody>
                                ${data.students.map(student => `
                                    <tr>
                                        <td>${escapeHtml(student.matricula)}</td>
                                        <td><strong>${escapeHtml(student.nome)}</strong></td>
                                        <td>${escapeHtml(student.curso)}</td>
                                        <td>${escapeHtml(student.ano_turma || 'N/A')}</td>
                                        <td>${student.level}</td>
                                        <td>${student.xp} XP</td>
                                        <td>
                                            <button class="btn btn-icon btn-sm" onclick="viewStudentDetails(${student.id})" title="Ver detalhes">
                                                <i class="fas fa-eye"></i>
                                            </button>
                                            <button class="btn btn-icon btn-sm" onclick="assignMissionToStudent(${student.id}, ${disciplineId})" title="Atribuir missão">
                                                <i class="fas fa-tasks"></i>
                                            </button>
                                        </td>
                                    </tr>
                                `).join('')}
                            </tbody>
                        </table>
                    </div>
                `;
            }

            openModalById('discipline-students-modal');
        } else {
            const error = await response.json();
            showToast(error.error || 'Erro ao carregar alunos', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao carregar alunos', 'error');
    }
}

async function loadTeacherRecentActivities() {
    try {
        const response = await fetch(`${API_BASE_URL}/teacher/recent-activities`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            renderTeacherRecentActivities(data.activities || []);
        }
    } catch (error) {
        console.error('Erro ao carregar atividades recentes:', error);
    }
}

function renderTeacherRecentActivities(activities) {
    const container = document.getElementById('teacher-recent-activities');
    if (!container) return;

    if (!activities || activities.length === 0) {
        container.innerHTML = '<p class="empty-state">Nenhuma atividade recente.</p>';
        return;
    }

    container.innerHTML = activities.map(activity => `
        <div class="activity-item">
            <div class="activity-icon">
                <i class="fas ${activity.icon || 'fa-bell'}"></i>
            </div>
            <div class="activity-content">
                <p>${escapeHtml(activity.description)}</p>
                <small>${formatDate(activity.created_at)}</small>
            </div>
        </div>
    `).join('');
}

// Funções auxiliares
function createMissionForDiscipline(disciplineId) {
    showToast('Função em desenvolvimento - Criar missão para disciplina', 'info');
}

function viewStudentDetails(studentId) {
    showToast('Função em desenvolvimento - Detalhes do aluno', 'info');
}

function assignMissionToStudent(studentId, disciplineId) {
    showToast('Função em desenvolvimento - Atribuir missão', 'info');
}

function openModalById(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.remove('hidden');
}

function closeModalById(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) modal.classList.add('hidden');
}

// ==================== SALA DE AULA VIRTUAL ====================

// Função para abrir a sala de aula virtual a partir da disciplina
// Em teacher.js
function openVirtualClassroom(disciplineId, disciplineName) {
    console.log(`🎓 Abrindo sala de aula virtual: ${disciplineName}`);
    if (typeof window.openVirtualClassroom === 'function') {
        window.openVirtualClassroom(disciplineId, disciplineName);
    } else {
        console.warn('classroom-manager.js não carregado, usando chat padrão');
        // Fallback: abrir chat da disciplina
        if (typeof openDisciplineChat === 'function') {
            openDisciplineChat(disciplineId, disciplineName);
        } else {
            showToast('Sala de aula não disponível', 'error');
        }
    }
}

// Modificar o botão "Ver Alunos" para abrir a sala de aula
// Substitua o botão "Ver Alunos" no renderTeacherDisciplines
function renderTeacherDisciplinesWithClassroom(disciplines) {
    const container = document.getElementById('teacher-disciplines-container');
    if (!container) return;

    if (!disciplines || disciplines.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chalkboard-teacher" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <h3>Nenhuma disciplina atribuída</h3>
                <p>Você ainda não está ministrando nenhuma disciplina.</p>
                <small>Entre em contato com o administrador para atribuir disciplinas a você.</small>
            </div>
        `;
        return;
    }

    const totalStudents = disciplines.reduce((sum, d) => sum + (d.student_count || 0), 0);

    container.innerHTML = `
        <div class="teacher-stats">
            <div class="teacher-stat-card">
                <i class="fas fa-book"></i>
                <div class="stat-value">${disciplines.length}</div>
                <div class="stat-label">Disciplinas Ministradas</div>
            </div>
            <div class="teacher-stat-card">
                <i class="fas fa-users"></i>
                <div class="stat-value">${totalStudents}</div>
                <div class="stat-label">Total de Alunos</div>
            </div>
            <div class="teacher-stat-card">
                <i class="fas fa-chalkboard"></i>
                <div class="stat-value">Sala Virtual</div>
                <div class="stat-label">Clique para acessar</div>
            </div>
        </div>

        <div class="teacher-disciplines-grid">
            ${disciplines.map(discipline => `
                <div class="teacher-discipline-card" onclick="openVirtualClassroom(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                    <div class="discipline-header">
                        <div class="discipline-code">${escapeHtml(discipline.codigo)}</div>
                        <div class="discipline-students-badge">
                            <i class="fas fa-users"></i> ${discipline.student_count || 0} alunos
                        </div>
                    </div>
                    <h3 class="discipline-name">${escapeHtml(discipline.nome)}</h3>
                    <div class="discipline-info">
                        <span><i class="fas fa-clock"></i> ${discipline.carga_horaria}h</span>
                        <span><i class="fas fa-graduation-cap"></i> ${discipline.ano_turma || 'Turma não definida'}</span>
                    </div>
                    <div class="discipline-actions">
                        <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); openVirtualClassroom(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-door-open"></i> Entrar na Sala
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); createMissionForDiscipline(${discipline.id})">
                            <i class="fas fa-plus"></i> Nova Missão
                        </button>
                        <button class="btn btn-sm btn-info" onclick="event.stopPropagation(); openDisciplineChat(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-comment"></i> Chat Rápido
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Substituir a função renderTeacherDisciplines existente
window.renderTeacherDisciplines = renderTeacherDisciplinesWithClassroom;