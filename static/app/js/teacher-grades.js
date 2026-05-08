// ==================== SISTEMA DE NOTAS - PROFESSOR ====================

// Variáveis globais para controle de modais de notas
let currentGradeDisciplineId = null;
let currentGradeDisciplineName = '';
let currentAssessmentId = null;

// ============================================================================
// MODAL: CRIAR AVALIAÇÃO
// ============================================================================

function showCreateAssessmentModal(disciplineId, disciplineName) {
    currentGradeDisciplineId = disciplineId;
    currentGradeDisciplineName = disciplineName;

    // Criar modal dinamicamente se não existir
    let modal = document.getElementById('modal-create-assessment');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-create-assessment';
        modal.className = 'modal-overlay hidden';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>📝 Criar Avaliação</h3>
                    <button class="btn btn-close" onclick="closeModal('modal-create-assessment')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <form id="assessment-form" onsubmit="event.preventDefault(); saveAssessment();">
                        <input type="hidden" id="assessment-discipline-id">
                        <div class="form-group">
                            <label>Título da Avaliação *</label>
                            <input type="text" id="assessment-title" class="form-control" placeholder="Ex: Prova B1 - Matemática" required>
                        </div>
                        <div class="form-group">
                            <label>Descrição</label>
                            <textarea id="assessment-description" class="form-control" rows="2" placeholder="Conteúdo da avaliação..."></textarea>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Tipo *</label>
                                <select id="assessment-type" class="form-control" required>
                                    <option value="prova">📝 Prova</option>
                                    <option value="trabalho">📄 Trabalho</option>
                                    <option value="participacao">💬 Participação</option>
                                    <option value="projeto">🚀 Projeto</option>
                                </select>
                            </div>
                            <div class="form-group">
                                <label>Bimestre *</label>
                                <select id="assessment-bimestre" class="form-control" required>
                                    <option value="1">1º Bimestre</option>
                                    <option value="2">2º Bimestre</option>
                                    <option value="3">3º Bimestre</option>
                                    <option value="4">4º Bimestre</option>
                                </select>
                            </div>
                        </div>
                        <div class="form-row">
                            <div class="form-group">
                                <label>Peso *</label>
                                <input type="number" id="assessment-peso" class="form-control" value="1.0" step="0.1" min="0.1" max="10" required>
                                <small style="color: var(--text-muted);">Peso na média do bimestre</small>
                            </div>
                            <div class="form-group">
                                <label>Nota Máxima *</label>
                                <input type="number" id="assessment-max-score" class="form-control" value="10.0" step="0.5" min="1" max="100" required>
                            </div>
                        </div>
                        <div class="form-group">
                            <label>Data de Entrega</label>
                            <input type="datetime-local" id="assessment-due-date" class="form-control">
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('modal-create-assessment')">Cancelar</button>
                    <button class="btn btn-primary" onclick="saveAssessment()">
                        <i class="fas fa-save"></i> Criar Avaliação
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    document.getElementById('assessment-discipline-id').value = disciplineId;
    document.getElementById('assessment-title').value = '';
    document.getElementById('assessment-description').value = '';
    document.getElementById('assessment-type').value = 'prova';
    document.getElementById('assessment-bimestre').value = '1';
    document.getElementById('assessment-peso').value = '1.0';
    document.getElementById('assessment-max-score').value = '10.0';
    document.getElementById('assessment-due-date').value = '';

    openModal('modal-create-assessment');
}

async function saveAssessment() {
    const data = {
        discipline_id: parseInt(document.getElementById('assessment-discipline-id').value),
        title: document.getElementById('assessment-title').value.trim(),
        description: document.getElementById('assessment-description').value.trim(),
        assessment_type: document.getElementById('assessment-type').value,
        bimestre: parseInt(document.getElementById('assessment-bimestre').value),
        peso: parseFloat(document.getElementById('assessment-peso').value),
        max_score: parseFloat(document.getElementById('assessment-max-score').value),
        due_date: document.getElementById('assessment-due-date').value || null
    };

    if (!data.title) {
        showToast('Título é obrigatório', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/assessments`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Avaliação criada com sucesso!', 'success');
            closeModal('modal-create-assessment');
        } else {
            showToast(result.error || 'Erro ao criar avaliação', 'error');
        }
    } catch (error) {
        console.error('Erro:', error);
        showToast('Erro ao criar avaliação', 'error');
    }
}


// ============================================================================
// MODAL: LANÇAR NOTAS EM LOTE
// ============================================================================

async function showLaunchGradesModal(disciplineId, disciplineName) {
    currentGradeDisciplineId = disciplineId;
    currentGradeDisciplineName = disciplineName;

    // Buscar avaliações da disciplina
    let assessments = [];
    try {
        const res = await fetch(`${API_BASE_URL}/disciplines/${disciplineId}/assessments`, {
            credentials: 'include'
        });
        const data = await res.json();
        if (data.success) assessments = data.assessments || [];
    } catch (e) {
        console.error(e);
    }

    if (assessments.length === 0) {
        showToast('Crie uma avaliação primeiro antes de lançar notas', 'warning');
        showCreateAssessmentModal(disciplineId, disciplineName);
        return;
    }

    // Criar modal se não existir
    let modal = document.getElementById('modal-launch-grades');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-launch-grades';
        modal.className = 'modal-overlay hidden';
        modal.innerHTML = `
            <div class="modal modal-large">
                <div class="modal-header">
                    <h3>📊 Lançar Notas - <span id="launch-grade-discipline-name"></span></h3>
                    <button class="btn btn-close" onclick="closeModal('modal-launch-grades')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="form-group">
                        <label>Selecionar Avaliação *</label>
                        <select id="launch-grade-assessment" class="form-control" onchange="loadStudentsForGrading()">
                            <option value="">Selecione uma avaliação...</option>
                        </select>
                    </div>
                    <div id="launch-grades-container" style="margin-top: 1rem;">
                        <p class="empty-state">Selecione uma avaliação para ver os alunos</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('modal-launch-grades')">Cancelar</button>
                    <button class="btn btn-primary" id="btn-save-grades-bulk" onclick="saveGradesBulk()" disabled>
                        <i class="fas fa-save"></i> Salvar Notas
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    document.getElementById('launch-grade-discipline-name').textContent = disciplineName;

    // Preencher select de avaliações
    const select = document.getElementById('launch-grade-assessment');
    select.innerHTML = '<option value="">Selecione uma avaliação...</option>';
    assessments.forEach(a => {
        const option = document.createElement('option');
        option.value = a.id;
        option.textContent = `${a.title} (${a.assessment_type}, ${a.bimestre}º Bim)`;
        select.appendChild(option);
    });

    document.getElementById('launch-grades-container').innerHTML = '<p class="empty-state">Selecione uma avaliação para ver os alunos</p>';
    document.getElementById('btn-save-grades-bulk').disabled = true;

    openModal('modal-launch-grades');
}

async function loadStudentsForGrading() {
    const assessmentId = document.getElementById('launch-grade-assessment').value;
    const container = document.getElementById('launch-grades-container');

    if (!assessmentId) {
        container.innerHTML = '<p class="empty-state">Selecione uma avaliação para ver os alunos</p>';
        document.getElementById('btn-save-grades-bulk').disabled = true;
        return;
    }

    currentAssessmentId = parseInt(assessmentId);

    container.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i><p>Carregando alunos...</p></div>';

    try {
        const res = await fetch(`${API_BASE_URL}/assessments/${assessmentId}/grades`, {
            credentials: 'include'
        });
        const data = await res.json();

        if (!data.success) {
            container.innerHTML = `<p class="empty-state">Erro: ${data.error}</p>`;
            return;
        }

        const maxScore = data.assessment?.max_score || 10;

        let html = `
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem;">
                <span><strong>${data.total_students}</strong> alunos | Nota máxima: <strong>${maxScore}</strong></span>
                <span style="color: var(--text-muted);">${data.graded_count} notas já lançadas</span>
            </div>
            <div class="grades-table-container" style="max-height: 400px; overflow-y: auto;">
                <table class="students-table" style="width: 100%;">
                    <thead>
                        <tr>
                            <th>Aluno</th>
                            <th>Matrícula</th>
                            <th style="width: 120px;">Nota (0-${maxScore})</th>
                            <th>Feedback</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.grades.forEach(g => {
            html += `
                <tr data-student-id="${g.student_id}">
                    <td><strong>${escapeHtml(g.student_nome)}</strong></td>
                    <td>${escapeHtml(g.student_matricula)}</td>
                    <td>
                        <input type="number" 
                               class="form-control grade-input" 
                               data-student-id="${g.student_id}"
                               value="${g.score !== null ? g.score : ''}" 
                               min="0" 
                               max="${maxScore}" 
                               step="0.1"
                               placeholder="-"
                               style="width: 80px; text-align: center;">
                    </td>
                    <td>
                        <input type="text" 
                               class="form-control feedback-input" 
                               data-student-id="${g.student_id}"
                               value="${g.feedback ? escapeHtml(g.feedback) : ''}" 
                               placeholder="Feedback opcional"
                               style="width: 100%;">
                    </td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;
        document.getElementById('btn-save-grades-bulk').disabled = false;

    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="empty-state">Erro ao carregar alunos</p>';
    }
}

async function saveGradesBulk() {
    const assessmentId = currentAssessmentId;
    if (!assessmentId) {
        showToast('Selecione uma avaliação', 'error');
        return;
    }

    const gradeInputs = document.querySelectorAll('.grade-input');
    const grades = [];

    gradeInputs.forEach(input => {
        const studentId = parseInt(input.dataset.studentId);
        const score = input.value.trim();
        const feedbackInput = document.querySelector(`.feedback-input[data-student-id="${studentId}"]`);
        const feedback = feedbackInput ? feedbackInput.value.trim() : '';

        if (score !== '') {
            grades.push({
                student_id: studentId,
                score: parseFloat(score),
                feedback: feedback
            });
        }
    });

    if (grades.length === 0) {
        showToast('Preencha pelo menos uma nota', 'error');
        return;
    }

    const btn = document.getElementById('btn-save-grades-bulk');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Salvando...';

    try {
        const response = await fetch(`${API_BASE_URL}/grades/bulk`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
                assessment_id: assessmentId,
                grades: grades
            })
        });

        const result = await response.json();

        if (result.success) {
            showToast(`Notas salvas! ${result.success_count} sucesso(s), ${result.error_count} erro(s)`, 'success');
            if (result.error_count > 0) {
                console.log('Erros:', result.results.filter(r => r.status === 'error'));
            }
            closeModal('modal-launch-grades');
        } else {
            showToast(result.error || 'Erro ao salvar notas', 'error');
        }
    } catch (error) {
        console.error(error);
        showToast('Erro ao salvar notas', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-save"></i> Salvar Notas';
    }
}


// ============================================================================
// MODAL: VER MÉDIAS BIMESTRAIS DA TURMA
// ============================================================================

async function showClassMediasModal(disciplineId, disciplineName) {
    let modal = document.getElementById('modal-class-medias');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-class-medias';
        modal.className = 'modal-overlay hidden';
        modal.innerHTML = `
            <div class="modal modal-large">
                <div class="modal-header">
                    <h3>📊 Médias Bimestrais - <span id="medias-discipline-name"></span></h3>
                    <button class="btn btn-close" onclick="closeModal('modal-class-medias')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div id="class-medias-container">
                        <p class="empty-state">Carregando...</p>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('modal-class-medias')">Fechar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    document.getElementById('medias-discipline-name').textContent = disciplineName;
    document.getElementById('class-medias-container').innerHTML = '<p class="empty-state"><i class="fas fa-spinner fa-spin"></i> Carregando médias...</p>';
    openModal('modal-class-medias');

    try {
        const res = await fetch(`${API_BASE_URL}/disciplines/${disciplineId}/medias`, {
            credentials: 'include'
        });
        const data = await res.json();

        if (!data.success) {
            document.getElementById('class-medias-container').innerHTML = `<p class="empty-state">${data.error}</p>`;
            return;
        }

        const situacaoBadge = (situacao) => {
            if (situacao === 'aprovado') return '<span style="color: var(--success-neon);">✅ Aprovado</span>';
            if (situacao === 'recuperacao') return '<span style="color: var(--warning-neon);">⚠️ Recuperação</span>';
            if (situacao === 'reprovado') return '<span style="color: var(--danger-neon);">❌ Reprovado</span>';
            return '<span style="color: var(--text-muted);">-</span>';
        };

        let html = `
            <div style="display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap;">
                <div class="stat-box" style="flex: 1; min-width: 120px;">
                    <div class="stat-value" style="color: var(--success-neon);">${data.aprovados || 0}</div>
                    <div class="stat-label">Aprovados</div>
                </div>
                <div class="stat-box" style="flex: 1; min-width: 120px;">
                    <div class="stat-value" style="color: var(--warning-neon);">${data.recuperacao || 0}</div>
                    <div class="stat-label">Recuperação</div>
                </div>
                <div class="stat-box" style="flex: 1; min-width: 120px;">
                    <div class="stat-value" style="color: var(--danger-neon);">${data.reprovados || 0}</div>
                    <div class="stat-label">Reprovados</div>
                </div>
                <div class="stat-box" style="flex: 1; min-width: 120px;">
                    <div class="stat-value">${data.total_students || 0}</div>
                    <div class="stat-label">Total</div>
                </div>
            </div>
            <div class="grades-table-container" style="max-height: 500px; overflow-y: auto;">
                <table class="students-table" style="width: 100%;">
                    <thead>
                        <tr>
                            <th>Aluno</th>
                            <th>Matrícula</th>
                            <th>1º Bim</th>
                            <th>2º Bim</th>
                            <th>3º Bim</th>
                            <th>4º Bim</th>
                            <th>Média Final</th>
                            <th>Situação</th>
                            <th>Rec.</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        data.students.forEach(s => {
            html += `
                <tr>
                    <td><strong>${escapeHtml(s.student_nome)}</strong></td>
                    <td>${escapeHtml(s.student_matricula)}</td>
                    <td style="text-align: center;">${s.b1_media !== null ? s.b1_media.toFixed(1) : '-'}</td>
                    <td style="text-align: center;">${s.b2_media !== null ? s.b2_media.toFixed(1) : '-'}</td>
                    <td style="text-align: center;">${s.b3_media !== null ? s.b3_media.toFixed(1) : '-'}</td>
                    <td style="text-align: center;">${s.b4_media !== null ? s.b4_media.toFixed(1) : '-'}</td>
                    <td style="text-align: center; font-weight: bold;">${s.media_final !== null ? s.media_final.toFixed(2) : '-'}</td>
                    <td style="text-align: center;">${situacaoBadge(s.situacao)}</td>
                    <td style="text-align: center;">${s.nota_recuperacao !== null ? s.nota_recuperacao.toFixed(1) : '-'}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        document.getElementById('class-medias-container').innerHTML = html;

    } catch (error) {
        console.error(error);
        document.getElementById('class-medias-container').innerHTML = '<p class="empty-state">Erro ao carregar médias</p>';
    }
}


// ============================================================================
// MODAL: LANÇAR NOTA DE RECUPERAÇÃO
// ============================================================================

async function showRecuperacaoModal(disciplineId, disciplineName) {
    let modal = document.getElementById('modal-recuperacao');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-recuperacao';
        modal.className = 'modal-overlay hidden';
        modal.innerHTML = `
            <div class="modal">
                <div class="modal-header">
                    <h3>📝 Nota de Recuperação</h3>
                    <button class="btn btn-close" onclick="closeModal('modal-recuperacao')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <form id="recuperacao-form">
                        <div class="form-group">
                            <label>Disciplina</label>
                            <input type="text" id="recuperacao-discipline-name" class="form-control" readonly>
                            <input type="hidden" id="recuperacao-discipline-id">
                        </div>
                        <div class="form-group">
                            <label>Aluno *</label>
                            <select id="recuperacao-student" class="form-control" required>
                                <option value="">Selecione o aluno...</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Nota de Recuperação (0-10) *</label>
                            <input type="number" id="recuperacao-nota" class="form-control" min="0" max="10" step="0.1" required>
                        </div>
                    </form>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('modal-recuperacao')">Cancelar</button>
                    <button class="btn btn-primary" onclick="saveRecuperacao()">
                        <i class="fas fa-save"></i> Lançar Recuperação
                    </button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    document.getElementById('recuperacao-discipline-name').value = disciplineName;
    document.getElementById('recuperacao-discipline-id').value = disciplineId;
    document.getElementById('recuperacao-nota').value = '';

    // Carregar alunos da disciplina
    const select = document.getElementById('recuperacao-student');
    select.innerHTML = '<option value="">Carregando alunos...</option>';

    try {
        const res = await fetch(`${API_BASE_URL}/disciplines/${disciplineId}/medias`, { credentials: 'include' });
        const data = await res.json();

        if (data.success && data.students) {
            // Filtrar apenas alunos em recuperação
            const emRecuperacao = data.students.filter(s => s.situacao === 'recuperacao');

            if (emRecuperacao.length === 0) {
                select.innerHTML = '<option value="">Nenhum aluno em recuperação</option>';
            } else {
                select.innerHTML = '<option value="">Selecione o aluno...</option>';
                emRecuperacao.forEach(s => {
                    const option = document.createElement('option');
                    option.value = s.student_id;
                    option.textContent = `${s.student_nome} (Média: ${s.media_final?.toFixed(2) || '-'})`;
                    select.appendChild(option);
                });
            }
        }
    } catch (e) {
        select.innerHTML = '<option value="">Erro ao carregar</option>';
    }

    openModal('modal-recuperacao');
}

async function saveRecuperacao() {
    const data = {
        student_id: parseInt(document.getElementById('recuperacao-student').value),
        discipline_id: parseInt(document.getElementById('recuperacao-discipline-id').value),
        nota_recuperacao: parseFloat(document.getElementById('recuperacao-nota').value)
    };

    if (!data.student_id || isNaN(data.nota_recuperacao)) {
        showToast('Preencha todos os campos', 'error');
        return;
    }

    try {
        const response = await fetch(`${API_BASE_URL}/grades/recuperacao`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const result = await response.json();

        if (result.success) {
            showToast('Nota de recuperação lançada!', 'success');
            closeModal('modal-recuperacao');
        } else {
            showToast(result.error || 'Erro ao lançar recuperação', 'error');
        }
    } catch (error) {
        showToast('Erro ao lançar recuperação', 'error');
    }
}


// ============================================================================
// ATUALIZAR RENDER DOS CARDS DO PROFESSOR (adicionar botões de notas + sala)
// ============================================================================

// Esta função substitui o renderTeacherDisciplines original para incluir botões de notas E sala de aula
function renderTeacherDisciplinesWithGrades(disciplines) {
    const container = document.getElementById('teacher-disciplines-container');
    if (!container) return;

    if (!disciplines || disciplines.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chalkboard-teacher" style="font-size: 3rem; margin-bottom: 1rem;"></i>
                <h3>Nenhuma disciplina atribuída</h3>
                <p>Você ainda não está ministrando nenhuma disciplina.</p>
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
                <div class="stat-label">Disciplinas</div>
            </div>
            <div class="teacher-stat-card">
                <i class="fas fa-users"></i>
                <div class="stat-value">${totalStudents}</div>
                <div class="stat-label">Total de Alunos</div>
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
                    <div class="discipline-actions" style="display: flex; flex-wrap: wrap; gap: 0.5rem;">
                        <button class="btn btn-sm btn-primary" onclick="event.stopPropagation(); openVirtualClassroom(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-door-open"></i> Entrar na Sala
                        </button>
                        <button class="btn btn-sm btn-info" onclick="event.stopPropagation(); showDisciplineStudents(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-users"></i> Alunos
                        </button>
                        <button class="btn btn-sm btn-warning" onclick="event.stopPropagation(); showCreateAssessmentModal(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-plus"></i> Avaliação
                        </button>
                        <button class="btn btn-sm btn-success" onclick="event.stopPropagation(); showLaunchGradesModal(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-pen"></i> Lançar Notas
                        </button>
                        <button class="btn btn-sm btn-info" onclick="event.stopPropagation(); showClassMediasModal(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-chart-bar"></i> Médias
                        </button>
                        <button class="btn btn-sm btn-secondary" onclick="event.stopPropagation(); showRecuperacaoModal(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-redo"></i> Recuperação
                        </button>
                        <button class="btn btn-sm btn-info" onclick="event.stopPropagation(); openDisciplineChat(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                            <i class="fas fa-comment"></i> Chat
                        </button>
                    </div>
                </div>
            `).join('')}
        </div>
    `;
}

// Sobrescrever a função original quando este script for carregado
if (typeof renderTeacherDisciplines === 'function') {
    window.renderTeacherDisciplines = renderTeacherDisciplinesWithGrades;
}

console.log('✅ teacher-grades.js carregado com sucesso!');