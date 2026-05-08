// ==================== SISTEMA DE NOTAS - ALUNO ====================

// ============================================================================
// MODAL: VER NOTAS E BOLETIM
// ============================================================================

async function showStudentGradesModal(disciplineId, disciplineName) {
    let modal = document.getElementById('modal-student-grades');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'modal-student-grades';
        modal.className = 'modal-overlay hidden';
        modal.innerHTML = `
            <div class="modal modal-large">
                <div class="modal-header">
                    <h3>📊 Minhas Notas - <span id="student-grade-discipline-name"></span></h3>
                    <button class="btn btn-close" onclick="closeModal('modal-student-grades')">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="tabs" style="margin-bottom: 1rem;">
                        <button class="tab-btn active" data-tab="notas" onclick="switchStudentGradeTab('notas')">Notas por Avaliação</button>
                        <button class="tab-btn" data-tab="boletim" onclick="switchStudentGradeTab('boletim')">Boletim Completo</button>
                    </div>
                    <div class="tab-content active" id="student-tab-notas">
                        <div id="student-notas-container">
                            <p class="empty-state">Carregando notas...</p>
                        </div>
                    </div>
                    <div class="tab-content" id="student-tab-boletim">
                        <div id="student-boletim-container">
                            <p class="empty-state">Carregando boletim...</p>
                        </div>
                    </div>
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="closeModal('modal-student-grades')">Fechar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    document.getElementById('student-grade-discipline-name').textContent = disciplineName;
    openModal('modal-student-grades');

    // Resetar tabs
    document.querySelectorAll('#modal-student-grades .tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.dataset.tab === 'notas') btn.classList.add('active');
    });
    document.querySelectorAll('#modal-student-grades .tab-content').forEach(content => {
        content.classList.remove('active');
        if (content.id === 'student-tab-notas') content.classList.add('active');
    });

    // Carregar dados
    await loadStudentNotas(disciplineId);
    await loadStudentBoletim();
}

function switchStudentGradeTab(tab) {
    document.querySelectorAll('#modal-student-grades .tab-btn').forEach(btn => {
        btn.classList.toggle('active', btn.dataset.tab === tab);
    });
    document.querySelectorAll('#modal-student-grades .tab-content').forEach(content => {
        content.classList.toggle('active', content.id === `student-tab-${tab}`);
    });
}

async function loadStudentNotas(disciplineId) {
    const container = document.getElementById('student-notas-container');
    container.innerHTML = '<p class="empty-state"><i class="fas fa-spinner fa-spin"></i> Carregando notas...</p>';

    try {
        const res = await fetch(`${API_BASE_URL}/grades/me?discipline_id=${disciplineId}`, {
            credentials: 'include'
        });
        const data = await res.json();

        if (!data.success) {
            container.innerHTML = `<p class="empty-state">${data.error}</p>`;
            return;
        }

        const grades = data.grades || [];
        if (grades.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhuma nota lançada ainda nesta disciplina.</p>';
            return;
        }

        // Agrupar por bimestre
        const porBimestre = { 1: [], 2: [], 3: [], 4: [] };
        grades.forEach(g => {
            if (g.bimestre && porBimestre[g.bimestre]) {
                porBimestre[g.bimestre].push(g);
            }
        });

        let html = '';
        [1, 2, 3, 4].forEach(bimestre => {
            const notas = porBimestre[bimestre];
            if (notas.length === 0) return;

            html += `
                <div class="bimestre-section" style="margin-bottom: 1.5rem;">
                    <h4 style="color: var(--primary-neon); margin-bottom: 0.75rem; border-bottom: 1px solid var(--border-color); padding-bottom: 0.5rem;">
                        ${bimestre}º Bimestre
                    </h4>
                    <div class="grades-list">
            `;

            notas.forEach(g => {
                const tipoIcon = {
                    'prova': '📝',
                    'trabalho': '📄',
                    'participacao': '💬',
                    'projeto': '🚀'
                }[g.assessment_type] || '📝';

                const scorePercent = g.score !== null ? (g.score / g.max_score * 100) : 0;
                let scoreColor = 'var(--danger-neon)';
                if (scorePercent >= 70) scoreColor = 'var(--success-neon)';
                else if (scorePercent >= 50) scoreColor = 'var(--warning-neon)';

                html += `
                    <div class="grade-item" style="background: var(--bg-card); padding: 1rem; border-radius: 0.5rem; margin-bottom: 0.75rem; border-left: 3px solid ${scoreColor};">
                        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
                            <div>
                                <div style="font-weight: 600;">${tipoIcon} ${escapeHtml(g.assessment_title)}</div>
                                <small style="color: var(--text-muted);">${escapeHtml(g.discipline_nome)}</small>
                            </div>
                            <div style="text-align: right;">
                                <div style="font-size: 1.5rem; font-weight: 700; color: ${scoreColor};">
                                    ${g.score !== null ? g.score.toFixed(1) : '-'}
                                    <span style="font-size: 0.9rem; color: var(--text-muted);">/ ${g.max_score}</span>
                                </div>
                                <small style="color: var(--text-muted);">${scorePercent.toFixed(0)}%</small>
                            </div>
                        </div>
                        ${g.feedback ? `<div style="margin-top: 0.5rem; padding-top: 0.5rem; border-top: 1px solid var(--border-color); color: var(--text-muted); font-size: 0.9rem;"><i class="fas fa-comment"></i> ${escapeHtml(g.feedback)}</div>` : ''}
                    </div>
                `;
            });

            html += `</div></div>`;
        });

        container.innerHTML = html;

    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="empty-state">Erro ao carregar notas</p>';
    }
}

async function loadStudentBoletim() {
    const container = document.getElementById('student-boletim-container');
    container.innerHTML = '<p class="empty-state"><i class="fas fa-spinner fa-spin"></i> Carregando boletim...</p>';

    try {
        const res = await fetch(`${API_BASE_URL}/grades/me/boletim`, {
            credentials: 'include'
        });
        const data = await res.json();

        if (!data.success) {
            container.innerHTML = `<p class="empty-state">${data.error}</p>`;
            return;
        }

        const boletim = data.boletim || [];
        if (boletim.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhuma disciplina matriculada.</p>';
            return;
        }

        const situacaoBadge = (situacao) => {
            if (situacao === 'aprovado') return '<span style="background: rgba(0,255,0,0.15); color: var(--success-neon); padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.85rem; font-weight: 600;">✅ Aprovado</span>';
            if (situacao === 'recuperacao') return '<span style="background: rgba(255,128,0,0.15); color: var(--warning-neon); padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.85rem; font-weight: 600;">⚠️ Recuperação</span>';
            if (situacao === 'reprovado') return '<span style="background: rgba(255,0,64,0.15); color: var(--danger-neon); padding: 0.25rem 0.75rem; border-radius: 1rem; font-size: 0.85rem; font-weight: 600;">❌ Reprovado</span>';
            return '<span style="color: var(--text-muted);">-</span>';
        };

        let html = `
            <div style="margin-bottom: 1rem;">
                <h4 style="margin-bottom: 0.5rem;">👤 ${escapeHtml(data.student?.nome || 'Aluno')}</h4>
                <p style="color: var(--text-muted);">Matrícula: ${escapeHtml(data.student?.matricula || '-')}</p>
            </div>
            <div class="grades-table-container" style="overflow-x: auto;">
                <table class="students-table" style="width: 100%; min-width: 600px;">
                    <thead>
                        <tr>
                            <th style="text-align: left;">Disciplina</th>
                            <th style="text-align: center;">1º Bim</th>
                            <th style="text-align: center;">2º Bim</th>
                            <th style="text-align: center;">3º Bim</th>
                            <th style="text-align: center;">4º Bim</th>
                            <th style="text-align: center;">Média Final</th>
                            <th style="text-align: center;">Situação</th>
                        </tr>
                    </thead>
                    <tbody>
        `;

        boletim.forEach(b => {
            html += `
                <tr>
                    <td>
                        <strong>${escapeHtml(b.discipline_nome)}</strong>
                        <br><small style="color: var(--text-muted);">${escapeHtml(b.discipline_codigo || '')}</small>
                    </td>
                    <td style="text-align: center; font-weight: 600;">${b.medias?.b1 !== null ? b.medias.b1.toFixed(1) : '-'}</td>
                    <td style="text-align: center; font-weight: 600;">${b.medias?.b2 !== null ? b.medias.b2.toFixed(1) : '-'}</td>
                    <td style="text-align: center; font-weight: 600;">${b.medias?.b3 !== null ? b.medias.b3.toFixed(1) : '-'}</td>
                    <td style="text-align: center; font-weight: 600;">${b.medias?.b4 !== null ? b.medias.b4.toFixed(1) : '-'}</td>
                    <td style="text-align: center; font-weight: 700; font-size: 1.1rem; color: var(--primary-neon);">
                        ${b.media_final !== null ? b.media_final.toFixed(2) : '-'}
                    </td>
                    <td style="text-align: center;">${situacaoBadge(b.situacao)}</td>
                </tr>
            `;
        });

        html += `
                    </tbody>
                </table>
            </div>
        `;

        container.innerHTML = html;

    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="empty-state">Erro ao carregar boletim</p>';
    }
}


// ============================================================================
// ATUALIZAR RENDER DOS CARDS DO ALUNO (adicionar botão de notas)
// ============================================================================

function renderDisciplinesWithGrades(disciplines) {
    const container = document.getElementById('disciplines-grid');
    const teacherContainer = document.getElementById('teacher-disciplines-container');

    if (teacherContainer) teacherContainer.classList.add('hidden');
    if (container) container.classList.remove('hidden');

    if (!disciplines?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma disciplina disponível</p>';
        return;
    }

    container.innerHTML = disciplines.map(discipline => `
        <div class="discipline-card">
            <div class="discipline-header">
                <div class="discipline-icon"><i class="fas fa-book"></i></div>
            </div>
            <h4 class="discipline-title">${escapeHtml(discipline.nome)}</h4>
            <p class="discipline-code">${escapeHtml(discipline.codigo)}</p>
            <p class="discipline-info"><i class="fas fa-clock"></i> ${discipline.carga_horaria}h</p>
            ${discipline.professor_nome ? `
                <p class="discipline-professor"><i class="fas fa-user"></i> ${escapeHtml(discipline.professor_nome)}</p>
            ` : ''}
            <div class="discipline-actions" style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem;">
                <button class="btn btn-sm btn-info" onclick="openDisciplineChat(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                    <i class="fas fa-comment"></i> Chat
                </button>
                <button class="btn btn-sm btn-primary" onclick="showStudentGradesModal(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                    <i class="fas fa-chart-line"></i> Notas
                </button>
            </div>
        </div>
    `).join('');
}

// Sobrescrever a função original quando este script for carregado
if (typeof renderDisciplines === 'function') {
    window.renderDisciplines = renderDisciplinesWithGrades;
}

console.log('✅ student-grades.js carregado com sucesso!');
