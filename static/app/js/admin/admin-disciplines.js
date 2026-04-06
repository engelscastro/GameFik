// ==================== ADMIN - DISCIPLINAS (COMPLETO) ====================

async function loadAdminDisciplines() {
    try {
        const response = await fetch(`${API_BASE_URL}/disciplines`, { credentials: 'include' });
        if (response.ok) {
            const data = await response.json();
            renderAdminDisciplines(data.disciplines || []);
        }
    } catch (error) {
        console.error('Load disciplines error:', error);
    }
}

function renderAdminDisciplines(disciplines) {
    const container = document.getElementById('admin-disciplines-list');
    if (!disciplines?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma disciplina cadastrada. <button class="btn btn-sm btn-primary" onclick="showAddDisciplineModal()">Criar primeira disciplina</button></p>';
        return;
    }

    container.innerHTML = disciplines.map(discipline => {
        let gradeLabel = '';
        if (discipline.ano_turma && typeof getGradeLabel !== 'undefined') {
            gradeLabel = `<small class="admin-item-desc">Série: ${getGradeLabel(discipline.ano_turma)}</small>`;
        }

        return `
        <div class="admin-item">
            <div class="admin-item-info">
                <div class="discipline-icon"><i class="fas fa-book"></i></div>
                <div>
                    <div class="admin-item-name">${escapeHtml(discipline.nome)}</div>
                    <div class="admin-item-meta">${discipline.codigo} | ${discipline.carga_horaria}h</div>
                    <small class="admin-item-desc">Professor: ${escapeHtml(discipline.professor_nome || 'Não atribuído')}</small>
                    ${gradeLabel}
                </div>
            </div>
            <div class="admin-item-actions">
                <button class="btn btn-icon" onclick="editDiscipline(${discipline.id})"><i class="fas fa-edit"></i></button>
                <button class="btn btn-icon btn-danger" onclick="deleteDiscipline(${discipline.id})"><i class="fas fa-trash"></i></button>
            </div>
        </div>
    `}).join('');
}

function showAddDisciplineModal() {
    document.getElementById('discipline-id').value = '';
    document.getElementById('discipline-code').value = '';
    document.getElementById('discipline-name').value = '';
    document.getElementById('discipline-hours').value = '60';
    document.getElementById('discipline-year').value = '';
    document.getElementById('discipline-modal-title').textContent = 'Nova Disciplina';

    // Inicializar seletor de série para disciplina
    const gradeContainer = document.getElementById('discipline-grade-container');
    if (gradeContainer) {
        gradeContainer.innerHTML = '';
        if (typeof createGradeSelector !== 'undefined') {
            createGradeSelector('discipline-grade-container', {
                id: 'discipline-grade',
                label: 'Série da Disciplina',
                placeholder: 'Selecione a série',
                required: false,
                showInfo: true,
                onChange: (value) => {
                    if (value) {
                        document.getElementById('discipline-year').value = value;
                    }
                }
            });
        }
    }

    loadProfessorsForSelect();
    openModal('modal-discipline');
}

// ========== FUNÇÃO DE EDIÇÃO ==========
async function editDiscipline(disciplineId) {
    try {
        const response = await fetch(`${API_BASE_URL}/disciplines/${disciplineId}`, {
            credentials: 'include'
        });

        if (!response.ok) {
            throw new Error(`HTTP ${response.status}`);
        }

        const data = await response.json();

        if (data.success && data.discipline) {
            document.getElementById('discipline-id').value = disciplineId;
            document.getElementById('discipline-code').value = data.discipline.codigo || '';
            document.getElementById('discipline-name').value = data.discipline.nome || '';
            document.getElementById('discipline-hours').value = data.discipline.carga_horaria || 60;
            document.getElementById('discipline-year').value = data.discipline.ano_turma || '';
            document.getElementById('discipline-modal-title').textContent = 'Editar Disciplina';

            await loadProfessorsForSelect();
            if (data.discipline.professor_id) {
                document.getElementById('discipline-professor').value = data.discipline.professor_id;
            }

            // Atualizar seletor de série se existir
            if (data.discipline.ano_turma && typeof setGradeValue !== 'undefined') {
                try {
                    setGradeValue('discipline-grade', data.discipline.ano_turma);
                } catch(e) {
                    console.log('Erro ao setar grade:', e);
                }
            }

            openModal('modal-discipline');
        } else {
            showToast(data.error || 'Erro ao carregar disciplina', 'error');
        }
    } catch (error) {
        console.error('Erro ao carregar disciplina:', error);
        showToast('Erro ao carregar dados da disciplina', 'error');
    }
}

// ========== FUNÇÃO DE SALVAR (CRIAR/ATUALIZAR) ==========
async function saveDiscipline() {
    const disciplineId = document.getElementById('discipline-id').value;

    const codigo = document.getElementById('discipline-code').value.trim();
    const nome = document.getElementById('discipline-name').value.trim();
    const cargaHoraria = parseInt(document.getElementById('discipline-hours').value);
    const professorId = document.getElementById('discipline-professor').value;
    let anoTurma = document.getElementById('discipline-year').value.trim();

    if (typeof getGradeValue !== 'undefined') {
        const gradeValue = getGradeValue('discipline-grade');
        if (gradeValue) anoTurma = gradeValue;
    }

    if (!codigo) {
        showToast('Código da disciplina é obrigatório', 'error');
        return;
    }

    if (!nome) {
        showToast('Nome da disciplina é obrigatório', 'error');
        return;
    }

    if (!cargaHoraria || cargaHoraria <= 0) {
        showToast('Carga horária deve ser maior que zero', 'error');
        return;
    }

    const data = {
        codigo: codigo,
        nome: nome,
        carga_horaria: cargaHoraria,
        professor_id: professorId || null,
        ano_turma: anoTurma || null
    };

    console.log('Enviando para API:', data);

    try {
        const url = `${API_BASE_URL}/disciplines${disciplineId ? `/${disciplineId}` : ''}`;
        const method = disciplineId ? 'PUT' : 'POST';

        const response = await fetch(url, {
            method: method,
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(data)
        });

        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            const result = await response.json();
            console.log('Resposta:', result);

            if (result.success) {
                let gradeMessage = '';
                if (data.ano_turma && typeof getGradeLabel !== 'undefined') {
                    gradeMessage = ` (Série: ${getGradeLabel(data.ano_turma)})`;
                }
                showToast(disciplineId ? 'Disciplina atualizada!' : `Disciplina criada!${gradeMessage}`, 'success');
                closeModal('modal-discipline');
                await loadAdminDisciplines();
                if (state.currentPage === 'disciplines') await loadDisciplines();
            } else {
                showToast(result.error || 'Erro ao salvar disciplina', 'error');
            }
        } else {
            const text = await response.text();
            console.error('Resposta não é JSON:', text.substring(0, 200));
            showToast('Erro no servidor. Verifique o console.', 'error');
        }
    } catch (error) {
        console.error('Save discipline error:', error);
        showToast('Erro ao salvar disciplina', 'error');
    }
}

// ========== FUNÇÃO DE DELETAR ==========
async function deleteDiscipline(disciplineId) {
    if (!confirm('Tem certeza que deseja excluir esta disciplina?\n\nATENÇÃO: Isso pode afetar matrículas e notas associadas.')) return;

    try {
        const response = await fetch(`${API_BASE_URL}/disciplines/${disciplineId}`, {
            method: 'DELETE',
            credentials: 'include'
        });

        const data = await response.json();

        if (data.success) {
            showToast('Disciplina excluída!', 'success');
            await loadAdminDisciplines();
            if (state.currentPage === 'disciplines') await loadDisciplines();
        } else {
            showToast(data.error || 'Erro ao excluir disciplina', 'error');
        }
    } catch (error) {
        console.error('Delete discipline error:', error);
        showToast('Erro ao excluir disciplina', 'error');
    }
}

// ========== FUNÇÕES AUXILIARES ==========
async function loadProfessorsForSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/professors`, { credentials: 'include' });
        const data = await response.json();

        if (data.success && data.professors) {
            const select = document.getElementById('discipline-professor');
            if (select) {
                select.innerHTML = '<option value="">Selecione um professor</option>';
                data.professors.forEach(professor => {
                    const option = document.createElement('option');
                    option.value = professor.id;
                    option.textContent = professor.nome;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Erro ao carregar professores:', error);
    }
}

async function loadDisciplinesForSelect() {
    try {
        const response = await fetch(`${API_BASE_URL}/disciplines`, { credentials: 'include' });
        const data = await response.json();

        if (data.success && data.disciplines) {
            const select = document.getElementById('mission-discipline');
            if (select) {
                select.innerHTML = '<option value="">Todas as disciplinas</option>';
                data.disciplines.forEach(discipline => {
                    const option = document.createElement('option');
                    option.value = discipline.id;
                    option.textContent = `${discipline.codigo} - ${discipline.nome}`;
                    select.appendChild(option);
                });
            }
        }
    } catch (error) {
        console.error('Erro ao carregar disciplinas:', error);
    }
}