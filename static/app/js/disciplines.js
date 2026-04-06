// ==================== DISCIPLINAS ====================

async function loadDisciplines() {
    try {
        // Se for professor, usar a função definida em teacher.js
        if (state.user && state.user.role === 'teacher') {
            if (typeof loadTeacherDisciplines === 'function') {
                await loadTeacherDisciplines();
            } else {
                console.error('loadTeacherDisciplines não definida. Verifique se teacher.js foi carregado antes.');
                showToast('Erro ao carregar disciplinas do professor. Recarregue a página.', 'error');
            }
            return;
        }

        // Para alunos e admin, mostrar todas as disciplinas
        const response = await fetch(`${API_BASE_URL}/disciplines`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            renderDisciplines(data.disciplines || []);
        }
    } catch (error) {
        console.error('Disciplines load error:', error);
    }
}

function renderDisciplines(disciplines) {
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
            <div class="discipline-actions" style="margin-top: 1rem;">
                <button class="btn btn-sm btn-info" onclick="openDisciplineChat(${discipline.id}, '${escapeHtml(discipline.nome)}')">
                    <i class="fas fa-comment"></i> Chat
                </button>
            </div>
        </div>
    `).join('');
}