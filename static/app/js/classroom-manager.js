// ==================== CLASSROOM MANAGER - SALA DE AULA VIRTUAL ====================

let currentTurma = null;           // armazena o ano_turma (ex: '7_ano_final')
let currentDisciplineId = null;    // opcional: se quiser vincular a uma disciplina

// Função principal chamada pelo teacher.js
function openVirtualClassroom(disciplineId, disciplineName) {
    console.log(`🎓 Abrindo sala de aula virtual: ${disciplineName}`);
    fetch(`/api/disciplines/${disciplineId}`, { credentials: 'include' })
        .then(res => res.json())
        .then(data => {
            if (data.success && data.discipline.ano_turma) {
                currentDisciplineId = disciplineId;   // <-- guarda o ID
                openTurmaClassroom(data.discipline.ano_turma);
            } else {
                showToast('Não foi possível identificar a turma desta disciplina', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            showToast('Erro ao carregar dados da turma', 'error');
        });
}

// Função principal para abrir a sala a partir do ano_turma
async function openTurmaClassroom(anoTurma) {
    console.log(`🏫 Abrindo sala da turma: ${anoTurma}`);
    currentTurma = anoTurma;
    currentDisciplineId = null;

    // Criar ou obter o modal
    let classroomModal = document.getElementById('classroom-modal');
    if (!classroomModal) {
        classroomModal = createClassroomModal();
        document.body.appendChild(classroomModal);
    }

    // Carregar cabeçalho com o nome da turma (opcional)
    document.getElementById('classroom-title').innerHTML = `📚 Sala de Aula - Turma ${formatarTurma(anoTurma)}`;

    // Mostrar modal
    classroomModal.classList.remove('hidden');

    // Carregar a aba ativa (Mural por padrão)
    await switchClassroomTab('feed');
}

// Formata o ano_turma para exibição amigável
function formatarTurma(anoTurma) {
    const mapa = {
        '1_ano_inicial': '1º Ano - Fundamental Inicial',
        '2_ano_inicial': '2º Ano - Fundamental Inicial',
        '3_ano_inicial': '3º Ano - Fundamental Inicial',
        '4_ano_inicial': '4º Ano - Fundamental Inicial',
        '5_ano_inicial': '5º Ano - Fundamental Inicial',
        '6_ano_final': '6º Ano - Fundamental Final',
        '7_ano_final': '7º Ano - Fundamental Final',
        '8_ano_final': '8º Ano - Fundamental Final',
        '9_ano_final': '9º Ano - Fundamental Final',
        '1_ano_medio': '1º Ano - Ensino Médio',
        '2_ano_medio': '2º Ano - Ensino Médio',
        '3_ano_medio': '3º Ano - Ensino Médio'
    };
    return mapa[anoTurma] || anoTurma;
}

// Cria a estrutura do modal (abas e botão de vídeo)
function createClassroomModal() {
    const modal = document.createElement('div');
    modal.id = 'classroom-modal';
    modal.className = 'modal-overlay hidden';
    modal.innerHTML = `
        <div class="modal modal-large">
            <div class="modal-header">
                <h3 id="classroom-title">Sala de Aula</h3>
                <button class="btn btn-close" onclick="closeClassroomModal()">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <div class="modal-body" style="padding: 0;">
                <!-- Botão de videochamada -->
                <div style="padding: 0.75rem 1rem; background: var(--bg-card); border-bottom: 1px solid var(--border-color); text-align: right;">
                    <button id="start-video-call-btn" class="btn btn-danger" onclick="startVideoCall()">
                        <i class="fas fa-video"></i> Iniciar Chamada de Vídeo
                    </button>
                </div>
                <!-- Abas -->
                <div class="classroom-tabs" style="display: flex; border-bottom: 1px solid var(--border-color); padding: 0 1rem;">
                    <button class="tab-btn active" data-tab="feed" onclick="switchClassroomTab('feed')">
                        <i class="fas fa-newspaper"></i> Mural
                    </button>
                    <button class="tab-btn" data-tab="activities" onclick="switchClassroomTab('activities')">
                        <i class="fas fa-tasks"></i> Atividades
                    </button>
                    <button class="tab-btn" data-tab="people" onclick="switchClassroomTab('people')">
                        <i class="fas fa-users"></i> Pessoas
                    </button>
                </div>
                <!-- Conteúdo dinâmico -->
                <div id="classroom-content" style="min-height: 400px; padding: 1rem;">
                    <div class="loading-state">
                        <i class="fas fa-spinner fa-spin"></i>
                        <p>Carregando...</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    return modal;
}

// Fechar modal
function closeClassroomModal() {
    const modal = document.getElementById('classroom-modal');
    if (modal) modal.classList.add('hidden');
    currentTurma = null;
}

// Alternar entre abas
async function switchClassroomTab(tabName) {
    // Atualizar classe ativa nos botões
    document.querySelectorAll('#classroom-modal .tab-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.getAttribute('data-tab') === tabName) {
            btn.classList.add('active');
        }
    });
    // Carregar conteúdo da aba
    await loadTabContent(tabName);
}

// Carregar conteúdo de cada aba
async function loadTabContent(tabName) {
    const container = document.getElementById('classroom-content');
    if (!container || !currentTurma) return;

    if (tabName === 'feed') {
        await loadFeed(container);
    } else if (tabName === 'activities') {
        await loadActivities(container);
    } else if (tabName === 'people') {
        await loadPeople(container);
    }
}

// ========== ABA MURAL (FEED) ==========
async function loadFeed(container) {
    container.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i><p>Carregando mural...</p></div>';
    try {
        const res = await fetch(`/api/turma/${currentTurma}/feed`, { credentials: 'include' });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);

        const posts = data.posts || [];
        const isTeacher = (state.user?.role === 'teacher' || state.user?.role === 'admin');

        let html = '';
        if (isTeacher) {
            html += `
                <div class="feed-post-form" style="background: var(--bg-card); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1.5rem;">
                    <h4>✏️ Criar novo post</h4>
                    <input type="text" id="post-title" class="form-control" placeholder="Título" style="margin-bottom: 0.5rem;">
                    <textarea id="post-content" class="form-control" rows="3" placeholder="Conteúdo..."></textarea>
                    <select id="post-type" class="form-control" style="margin: 0.5rem 0;">
                        <option value="announcement">📢 Anúncio</option>
                        <option value="material">📚 Material</option>
                        <option value="assignment">📝 Atividade</option>
                    </select>
                    <div id="assignment-fields" style="display: none;">
                        <input type="datetime-local" id="post-due" class="form-control" placeholder="Data de entrega">
                        <input type="number" id="post-points" class="form-control" placeholder="Pontuação máxima" value="100">
                    </div>
                    <button class="btn btn-primary" onclick="createFeedPost()">Publicar</button>
                </div>
            `;
            // Mostrar/esconder campos de atividade conforme o tipo selecionado
            setTimeout(() => {
                const typeSelect = document.getElementById('post-type');
                const assignmentDiv = document.getElementById('assignment-fields');
                if (typeSelect) {
                    typeSelect.addEventListener('change', () => {
                        assignmentDiv.style.display = typeSelect.value === 'assignment' ? 'block' : 'none';
                    });
                }
            }, 100);
        }

        if (posts.length === 0) {
            html += '<p class="empty-state">Nenhum post no mural ainda.</p>';
        } else {
            html += `<div id="feed-list">`;
            posts.forEach(post => {
                html += `
                    <div class="feed-post" style="background: var(--bg-card); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                            <strong>${escapeHtml(post.title)}</strong>
                            <small>${formatDate(post.created_at)}</small>
                        </div>
                        <div>${escapeHtml(post.content)}</div>
                        ${post.post_type === 'assignment' ? `<div style="margin-top: 0.5rem; color: var(--primary-neon);">📅 Entrega: ${formatDate(post.due_date)} | 🎯 Pontos: ${post.points}</div>` : ''}
                        ${post.file_url ? `<div><a href="${post.file_url}" target="_blank">📎 Anexo</a></div>` : ''}
                    </div>
                `;
            });
            html += `</div>`;
        }
        container.innerHTML = html;
    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="empty-state">Erro ao carregar o mural. Tente novamente.</p>';
    }
}

// Criar um novo post no feed
async function createFeedPost() {
    const title = document.getElementById('post-title').value;
    const content = document.getElementById('post-content').value;
    const post_type = document.getElementById('post-type').value;
    let due_date = null;
    let points = 0;
    if (post_type === 'assignment') {
        due_date = document.getElementById('post-due').value;
        points = parseInt(document.getElementById('post-points').value) || 0;
    }
    if (!title || !content) {
        showToast('Preencha título e conteúdo', 'error');
        return;
    }
    const payload = { title, content, post_type, due_date, points };
    try {
        const res = await fetch(`/api/turma/${currentTurma}/post`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            showToast('Post publicado!', 'success');
            // Limpar formulário e recarregar feed
            document.getElementById('post-title').value = '';
            document.getElementById('post-content').value = '';
            await loadFeed(document.getElementById('classroom-content'));
        } else {
            showToast(data.error || 'Erro ao publicar', 'error');
        }
    } catch (error) {
        console.error(error);
        showToast('Erro ao publicar post', 'error');
    }
}

// ========== ABA ATIVIDADES ==========
async function loadActivities(container) {
    container.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i><p>Carregando atividades...</p></div>';
    try {
        const res = await fetch(`/api/turma/${currentTurma}/feed`, { credentials: 'include' });
        const data = await res.json();
        if (!data.success) throw new Error(data.error);
        const assignments = data.posts.filter(p => p.post_type === 'assignment');
        if (assignments.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhuma atividade criada ainda.</p>';
            return;
        }
        let html = `<div class="assignments-list">`;
        for (const act of assignments) {
            html += `
                <div class="assignment-card" style="background: var(--bg-card); padding: 1rem; border-radius: 0.5rem; margin-bottom: 1rem;">
                    <h4>${escapeHtml(act.title)}</h4>
                    <p>${escapeHtml(act.content)}</p>
                    <div>📅 Entrega: ${formatDate(act.due_date)} | 🎯 Pontos: ${act.points}</div>
            `;
            // Se for aluno, mostrar botão de entregar ou status
            if (state.user?.role === 'student') {
                // Verificar se já entregou (precisa de uma rota para consultar entrega)
                // Por simplicidade, vamos apenas mostrar um botão genérico
                html += `<button class="btn btn-sm btn-primary" onclick="submitAssignment(${act.id})">Entregar Atividade</button>`;
            } else if (state.user?.role === 'teacher' || state.user?.role === 'admin') {
                html += `<button class="btn btn-sm btn-secondary" onclick="viewSubmissions(${act.id})">Ver Entregas</button>`;
            }
            html += `</div>`;
        }
        html += `</div>`;
        container.innerHTML = html;
    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="empty-state">Erro ao carregar atividades.</p>';
    }
}

// Função para aluno entregar atividade (pode ser aprimorada)
async function submitAssignment(postId) {
    const content = prompt('Digite sua resposta (ou link para arquivo):');
    if (!content) return;
    try {
        const res = await fetch(`/api/turma/${currentTurma}/post/${postId}/submit`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ content })
        });
        const data = await res.json();
        if (data.success) {
            showToast('Atividade entregue!', 'success');
            await loadActivities(document.getElementById('classroom-content'));
        } else {
            showToast(data.error || 'Erro ao entregar', 'error');
        }
    } catch (error) {
        showToast('Erro ao enviar', 'error');
    }
}

// ========== ABA PESSOAS ==========
async function loadPeople(container) {
    container.innerHTML = '<div class="loading-state"><i class="fas fa-spinner fa-spin"></i><p>Carregando lista de pessoas...</p></div>';
    try {
        let students = [];
        // Monta a URL com o discipline_id, se disponível
        let url = `/api/turma/${currentTurma}/students`;
        if (currentDisciplineId) {
            url += `?discipline_id=${currentDisciplineId}`;
        }
        const res = await fetch(url, { credentials: 'include' });
        if (res.ok) {
            const data = await res.json();
            students = data.students || [];
        } else {
            // Fallback: usar dados da rota geral /turma/<ano> (caso a rota específica não exista)
            const fallbackRes = await fetch(`/api/turma/${currentTurma}`, { credentials: 'include' });
            const fallbackData = await fallbackRes.json();
            students = fallbackData.students || [];
        }

        if (students.length === 0) {
            container.innerHTML = '<p class="empty-state">Nenhum aluno encontrado nesta turma/disciplina.</p>';
            return;
        }

        let html = `<div class="people-list" style="display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 1rem;">`;
        students.forEach(s => {
            html += `
                <div class="person-card" style="background: var(--bg-card); padding: 1rem; border-radius: 0.5rem; display: flex; align-items: center; gap: 1rem;">
                    <div class="person-avatar" style="font-size: 2rem;">${s.avatar || '👨‍🎓'}</div>
                    <div>
                        <div><strong>${escapeHtml(s.nome)}</strong></div>
                        <div><small>${escapeHtml(s.matricula)}</small></div>
                        <div><small>${escapeHtml(s.curso || '')}</small></div>
                    </div>
                </div>
            `;
        });
        html += `</div>`;
        container.innerHTML = html;
    } catch (error) {
        console.error(error);
        container.innerHTML = '<p class="empty-state">Erro ao carregar lista de pessoas.</p>';
    }
}

// ========== VIDEOCHAMADA ==========
async function startVideoCall() {
    if (!currentTurma) return;
    try {
        const res = await fetch(`/api/turma/${currentTurma}/videocall`, { credentials: 'include' });
        const data = await res.json();
        if (data.success && data.link) {
            // Abrir modal com iframe
            let videoModal = document.getElementById('video-modal');
            if (!videoModal) {
                videoModal = document.createElement('div');
                videoModal.id = 'video-modal';
                videoModal.className = 'modal-overlay hidden';
                videoModal.innerHTML = `
                    <div class="modal modal-large">
                        <div class="modal-header">
                            <h3>Videochamada</h3>
                            <button class="btn btn-close" onclick="closeVideoModal()">✖</button>
                        </div>
                        <div class="modal-body" style="padding: 0;">
                            <iframe id="video-iframe" width="100%" height="500" allow="camera; microphone" style="border: none;"></iframe>
                        </div>
                    </div>
                `;
                document.body.appendChild(videoModal);
            }
            document.getElementById('video-iframe').src = data.link;
            videoModal.classList.remove('hidden');
        } else {
            showToast('Erro ao obter link da videochamada', 'error');
        }
    } catch (error) {
        console.error(error);
        showToast('Erro ao iniciar videochamada', 'error');
    }
}

function closeVideoModal() {
    const modal = document.getElementById('video-modal');
    if (modal) {
        modal.classList.add('hidden');
        const iframe = document.getElementById('video-iframe');
        if (iframe) iframe.src = '';
    }
}

// ========== FUNÇÕES AUXILIARES ==========
function formatDate(dateString) {
    if (!dateString) return 'Sem data';
    const date = new Date(dateString);
    return date.toLocaleDateString('pt-BR');
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// Exportar funções para o escopo global (necessário para chamadas inline onclick)
window.openVirtualClassroom = openVirtualClassroom;
window.openTurmaClassroom = openTurmaClassroom;
window.closeClassroomModal = closeClassroomModal;
window.switchClassroomTab = switchClassroomTab;
window.createFeedPost = createFeedPost;
window.submitAssignment = submitAssignment;
window.startVideoCall = startVideoCall;
window.closeVideoModal = closeVideoModal;

console.log('✅ classroom-manager.js caArregado com sucesso!');