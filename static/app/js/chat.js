// ==================== SISTEMA DE CHAT POR DISCIPLINA ====================

let currentChatDisciplineId = null;
let chatAutoRefresh = null;

// Abrir chat da disciplina
async function openDisciplineChat(disciplineId, disciplineName) {
    console.log(`🎯 Abrindo chat da disciplina ${disciplineId}: ${disciplineName}`);

    // Verificar/criar chat
    const chatReady = await ensureChatExists(disciplineId);
    if (!chatReady) {
        showToast('❌ Não foi possível acessar o chat desta disciplina', 'error');
        return;
    }

    currentChatDisciplineId = disciplineId;
    document.getElementById('chatDisciplineName').textContent = `Chat - ${disciplineName}`;

    // Abrir modal
    const modal = document.getElementById('disciplineChatModal');
    modal.classList.remove('hidden');

    // Inicializar chat
    setTimeout(() => {
        loadChatMessages();
        startChatAutoRefresh();
        // Focar no input
        document.getElementById('chat-message-input').focus();
    }, 100);
}

// Garantir que o chat existe no backend
async function ensureChatExists(disciplineId) {
    try {
        const response = await fetch(`/api/disciplines/${disciplineId}/chat/ensure`, {
            method: 'POST',
            credentials: 'include'
        });
        const data = await response.json();
        return data.success;
    } catch (error) {
        console.error('Erro ao verificar chat:', error);
        return false;
    }
}

// Carregar mensagens do chat
async function loadChatMessages() {
    if (!currentChatDisciplineId) return;

    try {
        const response = await fetch(`/api/disciplines/${currentChatDisciplineId}/chat`, {
            credentials: 'include'
        });
        const data = await response.json();

        if (data.success) {
            displayChatMessages(data.messages);
            updateChatStatus(`${data.total_messages} mensagens`);
        } else {
            updateChatStatus('Erro ao carregar');
        }
    } catch (error) {
        console.error('Erro ao carregar mensagens:', error);
        updateChatStatus('Erro de conexão');
    }
}

// Exibir mensagens
function displayChatMessages(messages) {
    const container = document.getElementById('chat-messages');
    if (!container) return;

    if (!messages || messages.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-comment-dots"></i>
                <p>Nenhuma mensagem ainda</p>
                <small>Seja o primeiro a enviar uma mensagem!</small>
            </div>
        `;
        return;
    }

    container.innerHTML = messages.map(message => {
        const isOwn = message.user_id === state.user?.id;
        const isAnnouncement = message.message_type === 'announcement';
        return `
            <div class="chat-message ${isOwn ? 'own-message' : ''} ${isAnnouncement ? 'announcement' : ''}">
                <div class="message-header">
                    <strong>${escapeHtml(message.user_name || 'Usuário')}</strong>
                    <small>${formatChatTime(message.created_at)}</small>
                    ${message.is_pinned ? '<span class="badge">📌 Fixada</span>' : ''}
                    ${isAnnouncement ? '<span class="badge announcement">📢 Anúncio</span>' : ''}
                </div>
                <div class="message-content">${escapeHtml(message.content)}</div>
                ${(isOwn || state.user?.role !== 'student') ? `
                    <div class="message-actions">
                        ${isOwn ? `<button class="btn-icon-small" onclick="deleteChatMessage(${message.id})" title="Excluir"><i class="fas fa-trash"></i></button>` : ''}
                        ${(state.user?.role === 'teacher' || state.user?.role === 'admin') ? `
                            <button class="btn-icon-small" onclick="togglePinMessage(${message.id})" title="${message.is_pinned ? 'Desafixar' : 'Fixar'}">
                                <i class="fas ${message.is_pinned ? 'fa-thumbtack' : 'fa-thumbtack'}"></i>
                            </button>
                        ` : ''}
                    </div>
                ` : ''}
            </div>
        `;
    }).join('');

    // Scroll para o final
    setTimeout(() => {
        container.scrollTop = container.scrollHeight;
    }, 50);
}

// Enviar mensagem
async function sendChatMessage() {
    const input = document.getElementById('chat-message-input');
    const content = input.value.trim();
    const button = document.getElementById('send-chat-btn');

    if (!content || !currentChatDisciplineId) return;

    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';

    try {
        const response = await fetch(`/api/disciplines/${currentChatDisciplineId}/chat/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ content, message_type: 'text' })
        });

        const data = await response.json();

        if (data.success) {
            input.value = '';
            await loadChatMessages();
            input.focus();
            if (data.message) showToast(data.message, 'success');
        } else {
            showToast(data.error || 'Erro ao enviar mensagem', 'error');
        }
    } catch (error) {
        console.error('Erro ao enviar mensagem:', error);
        showToast('Erro ao enviar mensagem', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar';
    }
}

// Excluir mensagem
async function deleteChatMessage(messageId) {
    if (!confirm('Tem certeza que deseja excluir esta mensagem?')) return;

    try {
        const response = await fetch(`/api/chat/messages/${messageId}`, {
            method: 'DELETE',
            credentials: 'include'
        });
        const data = await response.json();

        if (data.success) {
            showToast('Mensagem excluída', 'success');
            await loadChatMessages();
        } else {
            showToast(data.error || 'Erro ao excluir', 'error');
        }
    } catch (error) {
        console.error('Erro ao excluir mensagem:', error);
        showToast('Erro ao excluir mensagem', 'error');
    }
}

// Fixar/desafixar mensagem (apenas professor/admin)
async function togglePinMessage(messageId) {
    try {
        const response = await fetch(`/api/chat/messages/${messageId}/pin`, {
            method: 'PUT',
            credentials: 'include'
        });
        const data = await response.json();

        if (data.success) {
            showToast(data.message, 'success');
            await loadChatMessages();
        } else {
            showToast(data.error || 'Erro ao fixar mensagem', 'error');
        }
    } catch (error) {
        console.error('Erro ao fixar mensagem:', error);
        showToast('Erro ao fixar mensagem', 'error');
    }
}

// Auto-refresh
function startChatAutoRefresh() {
    if (chatAutoRefresh) clearInterval(chatAutoRefresh);
    chatAutoRefresh = setInterval(() => {
        if (currentChatDisciplineId && document.getElementById('disciplineChatModal') &&
            !document.getElementById('disciplineChatModal').classList.contains('hidden')) {
            loadChatMessages();
        }
    }, 5000);
}

function stopChatAutoRefresh() {
    if (chatAutoRefresh) {
        clearInterval(chatAutoRefresh);
        chatAutoRefresh = null;
    }
}

// Fechar chat
function closeDisciplineChat() {
    stopChatAutoRefresh();
    currentChatDisciplineId = null;
    const modal = document.getElementById('disciplineChatModal');
    if (modal) modal.classList.add('hidden');
}

// Atualizar status
function updateChatStatus(status) {
    const el = document.getElementById('chat-status');
    if (el) el.textContent = status;
}

// Formatar hora
function formatChatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);

    if (diff < 60) return 'agora';
    if (diff < 3600) return `${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} h`;
    return date.toLocaleDateString('pt-BR');
}

// Evento Enter
function handleChatKeyPress(event) {
    if (event.key === 'Enter') {
        sendChatMessage();
    }
}