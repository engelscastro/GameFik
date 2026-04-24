// ==================== CHAT COMPLETO COM TODAS AS MELHORIAS ====================

let currentChatDisciplineId = null;
let currentChatDisciplineName = '';
let chatAutoRefresh = null;
let typingTimeout = null;
let isTyping = false;
let currentPage = 1;
let hasMoreMessages = true;
let isLoadingMessages = false;
let lastMessageId = null;
let unreadCount = 0;
let originalTitle = document.title;
let searchTerm = '';
let currentReplyTo = null;
let notificationSound = null;

// Inicializar som (opcional)
function initNotificationSound() {
    notificationSound = new Audio('/static/sounds/notification.mp3');
    notificationSound.volume = 0.3;
}

function playNotificationSound() {
    if (notificationSound) notificationSound.play().catch(e => console.log);
}

// Badge de não lidas
function updateUnreadBadge(count) {
    const badge = document.getElementById('chat-unread-badge');
    if (badge) {
        badge.textContent = count > 9 ? '9+' : count;
        badge.style.display = count ? 'inline-block' : 'none';
    }
    if (count && document.hidden) {
        document.title = `(${count}) ${originalTitle}`;
    } else {
        document.title = originalTitle;
    }
}

// Notificação do navegador
function showBrowserNotification(title, body) {
    if (Notification.permission === 'granted') {
        new Notification(title, { body, icon: '/static/favicon.ico' });
    } else if (Notification.permission !== 'denied') {
        Notification.requestPermission();
    }
}

// Abrir chat
async function openDisciplineChat(disciplineId, disciplineName) {
    currentChatDisciplineId = disciplineId;
    currentChatDisciplineName = disciplineName;
    currentPage = 1;
    hasMoreMessages = true;
    isLoadingMessages = false;
    searchTerm = '';
    currentReplyTo = null;

    const chatReady = await ensureChatExists(disciplineId);
    if (!chatReady) {
        showToast('❌ Não foi possível acessar o chat', 'error');
        return;
    }

    document.getElementById('chatDisciplineName').textContent = `Chat - ${disciplineName}`;
    const modal = document.getElementById('disciplineChatModal');
    modal.classList.remove('hidden');

    unreadCount = 0;
    updateUnreadBadge(0);

    await loadChatMessages(true);
    startChatAutoRefresh();
    document.getElementById('chat-message-input').focus();
}

async function ensureChatExists(disciplineId) {
    try {
        const res = await fetch(`/api/disciplines/${disciplineId}/chat/ensure`, { method: 'POST', credentials: 'include' });
        const data = await res.json();
        return data.success;
    } catch(e) { return false; }
}

// Carregar mensagens (com paginação e busca)
async function loadChatMessages(reset = false) {
    if (!currentChatDisciplineId) return;
    if (reset) {
        currentPage = 1;
        hasMoreMessages = true;
        document.getElementById('chat-messages').innerHTML = '';
    }
    if (isLoadingMessages || (!hasMoreMessages && !reset)) return;
    isLoadingMessages = true;

    try {
        let url = `/api/disciplines/${currentChatDisciplineId}/chat?page=${currentPage}&per_page=20`;
        if (searchTerm) url += `&search=${encodeURIComponent(searchTerm)}`;
        const res = await fetch(url, { credentials: 'include' });
        const data = await res.json();
        if (data.success) {
            if (reset) {
                renderMessages(data.messages);
            } else {
                prependMessages(data.messages);
                const container = document.getElementById('chat-messages');
                const oldScrollHeight = container.scrollHeight;
                if (container.scrollTop === 0) {
                    container.scrollTop = container.scrollHeight - oldScrollHeight;
                }
            }
            hasMoreMessages = data.has_more;
            currentPage++;
        }
    } catch(e) { console.error(e); }
    finally { isLoadingMessages = false; }
}

function prependMessages(messages) {
    const container = document.getElementById('chat-messages');
    const fragment = document.createDocumentFragment();
    messages.reverse().forEach(msg => fragment.appendChild(createMessageElement(msg)));
    if (container.firstChild) container.insertBefore(fragment, container.firstChild);
    else container.appendChild(fragment);
}

function renderMessages(messages) {
    const container = document.getElementById('chat-messages');
    container.innerHTML = '';
    messages.forEach(msg => container.appendChild(createMessageElement(msg)));
    attachReactionEvents();
    attachScrollListener();
    scrollToBottom();
}

function createMessageElement(msg) {
    const div = document.createElement('div');
    div.className = `chat-message ${msg.user_id === state.user?.id ? 'own-message' : ''} ${msg.message_type === 'announcement' ? 'announcement' : ''}`;
    div.dataset.id = msg.id;

    let replyHtml = '';
    if (msg.reply_to && msg.parent_message) {
        replyHtml = `<div class="message-reply">↪️ <strong>${escapeHtml(msg.parent_message.user_name)}</strong>: ${escapeHtml(msg.parent_message.content)}</div>`;
    }

    let reactionsHtml = '';
    if (msg.reactions) {
        const emojis = ['👍', '❤️', '😂', '😮', '😢', '🙏'];
        reactionsHtml = `<div class="message-reactions">`;
        for (const emoji of emojis) {
            const count = msg.reactions[emoji]?.length || 0;
            reactionsHtml += `<button class="reaction-btn" data-emoji="${emoji}" data-id="${msg.id}">${emoji} ${count ? count : ''}</button>`;
        }
        reactionsHtml += `</div>`;
    }

    div.innerHTML = `
        <div class="message-header">
            <strong>${escapeHtml(msg.user_name)}</strong>
            <small>${formatChatTime(msg.created_at)}</small>
            ${msg.is_pinned ? '<span class="badge">📌 Fixada</span>' : ''}
            ${msg.message_type === 'announcement' ? '<span class="badge announcement">📢 Anúncio</span>' : ''}
        </div>
        ${replyHtml}
        <div class="message-content">${formatMessageText(msg.content)}</div>
        ${reactionsHtml}
        <div class="message-actions">
            <button class="btn-icon-small" onclick="replyToMessage(${msg.id}, '${escapeHtml(msg.user_name)}', '${escapeHtml(msg.content)}')" title="Responder">↩️</button>
            <button class="btn-icon-small" onclick="copyMessage(${msg.id})" title="Copiar">📋</button>
            ${msg.user_id === state.user?.id ? `<button class="btn-icon-small" onclick="deleteChatMessage(${msg.id})" title="Excluir">🗑️</button>` : ''}
            ${(state.user?.role === 'teacher' || state.user?.role === 'admin') ? `<button class="btn-icon-small" onclick="togglePinMessage(${msg.id})" title="${msg.is_pinned ? 'Desafixar' : 'Fixar'}">📌</button>` : ''}
        </div>
    `;
    return div;
}

// 🔧 CORREÇÃO PRINCIPAL: formatação de Markdown e imagens
function formatMessageText(text) {
    let html = escapeHtml(text);
    // Negrito
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Itálico
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    // Código inline
    html = html.replace(/`(.*?)`/g, '<code>$1</code>');
    // Links
    html = html.replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank">$1</a>');
    // Imagens ![](url) ou ![alt](url) - com classe para CSS
    html = html.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" class="chat-image" loading="lazy">');
    return html;
}

function attachReactionEvents() {
    document.querySelectorAll('.reaction-btn').forEach(btn => {
        btn.removeEventListener('click', reactionHandler);
        btn.addEventListener('click', reactionHandler);
    });
}

async function reactionHandler(e) {
    const btn = e.currentTarget;
    const messageId = btn.dataset.id;
    const emoji = btn.dataset.emoji;
    await addReaction(messageId, emoji);
}

async function addReaction(messageId, emoji) {
    try {
        const res = await fetch(`/api/chat/messages/${messageId}/react`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({ reaction: emoji })
        });
        if (res.ok) await loadChatMessages(true);
    } catch(e) { console.error(e); }
}

function attachScrollListener() {
    const container = document.getElementById('chat-messages');
    container.removeEventListener('scroll', scrollHandler);
    container.addEventListener('scroll', scrollHandler);
}

function scrollHandler() {
    const container = document.getElementById('chat-messages');
    if (container.scrollTop === 0 && hasMoreMessages && !isLoadingMessages) {
        loadChatMessages(false);
    }
}

function replyToMessage(messageId, userName, content) {
    currentReplyTo = { id: messageId, user: userName, content: content };
    const input = document.getElementById('chat-message-input');
    input.value = `@${userName} `;
    input.focus();
    showToast(`Respondendo a ${userName}`, 'info');
}

async function sendChatMessage() {
    const input = document.getElementById('chat-message-input');
    let content = input.value.trim();
    if (!content) return;

    let replyToId = null;
    if (currentReplyTo) {
        replyToId = currentReplyTo.id;
        currentReplyTo = null;
    }

    const button = document.getElementById('send-chat-btn');
    button.disabled = true;
    button.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Enviando...';

    try {
        const body = { content, message_type: 'text' };
        if (replyToId) body.reply_to = replyToId;
        const res = await fetch(`/api/disciplines/${currentChatDisciplineId}/chat/messages`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify(body)
        });
        const data = await res.json();
        if (data.success) {
            input.value = '';
            await loadChatMessages(true);
            input.focus();
            if (data.message) showToast(data.message, 'success');
        } else {
            showToast(data.error || 'Erro ao enviar', 'error');
        }
    } catch(e) {
        showToast('Erro ao enviar mensagem', 'error');
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fas fa-paper-plane"></i> Enviar';
    }
}

// 🔧 CORREÇÃO NO UPLOAD: envia como texto com markdown
async function uploadChatImage(file) {
    const formData = new FormData();
    formData.append('image', file);
    try {
        const res = await fetch(`/api/disciplines/${currentChatDisciplineId}/chat/upload`, {
            method: 'POST',
            credentials: 'include',
            body: formData
        });
        const data = await res.json();
        if (data.success) {
            const content = `![imagem](${data.url})`;
            const msgRes = await fetch(`/api/disciplines/${currentChatDisciplineId}/chat/messages`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ content, message_type: 'text' })  // 'text' para formatar
            });
            if (msgRes.ok) await loadChatMessages(true);
        } else {
            showToast(data.error, 'error');
        }
    } catch(e) { showToast('Erro ao enviar imagem', 'error'); }
}

function searchMessages() {
    searchTerm = document.getElementById('chat-search-input').value;
    loadChatMessages(true);
}

function handleChatKeyPress(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
        event.preventDefault();
        sendChatMessage();
    } else {
        if (!isTyping) {
            isTyping = true;
            fetch(`/api/disciplines/${currentChatDisciplineId}/chat/typing`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ typing: true })
            }).catch(e=>console.log);
        }
        clearTimeout(typingTimeout);
        typingTimeout = setTimeout(() => {
            isTyping = false;
            fetch(`/api/disciplines/${currentChatDisciplineId}/chat/typing`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({ typing: false })
            }).catch(e=>console.log);
        }, 1000);
    }
}

async function checkNewMessages() {
    if (!currentChatDisciplineId) return;
    const res = await fetch(`/api/disciplines/${currentChatDisciplineId}/chat/latest`, { credentials: 'include' });
    const data = await res.json();
    if (data.last_message_id && data.last_message_id !== lastMessageId) {
        if (!document.getElementById('disciplineChatModal').classList.contains('hidden')) {
            await loadChatMessages(true);
        } else {
            unreadCount++;
            updateUnreadBadge(unreadCount);
            playNotificationSound();
            showBrowserNotification(`Nova mensagem em ${currentChatDisciplineName}`, data.last_message_preview);
        }
        lastMessageId = data.last_message_id;
    }
}

function startChatAutoRefresh() {
    if (chatAutoRefresh) clearInterval(chatAutoRefresh);
    chatAutoRefresh = setInterval(() => {
        if (currentChatDisciplineId && document.getElementById('disciplineChatModal') &&
            !document.getElementById('disciplineChatModal').classList.contains('hidden')) {
            checkNewMessages();
        }
    }, 3000);
}

function stopChatAutoRefresh() {
    if (chatAutoRefresh) clearInterval(chatAutoRefresh);
    chatAutoRefresh = null;
}

function closeDisciplineChat() {
    stopChatAutoRefresh();
    currentChatDisciplineId = null;
    currentReplyTo = null;
    const modal = document.getElementById('disciplineChatModal');
    if (modal) modal.classList.add('hidden');
    document.title = originalTitle;
}

async function deleteChatMessage(messageId) {
    if (!confirm('Excluir esta mensagem?')) return;
    const res = await fetch(`/api/chat/messages/${messageId}`, { method: 'DELETE', credentials: 'include' });
    const data = await res.json();
    if (data.success) {
        showToast('Mensagem excluída', 'success');
        await loadChatMessages(true);
    } else {
        showToast(data.error, 'error');
    }
}

async function togglePinMessage(messageId) {
    const res = await fetch(`/api/chat/messages/${messageId}/pin`, { method: 'PUT', credentials: 'include' });
    const data = await res.json();
    if (data.success) {
        showToast(data.message, 'success');
        await loadChatMessages(true);
    } else {
        showToast(data.error, 'error');
    }
}

function copyMessage(messageId) {
    const msgDiv = document.querySelector(`.chat-message[data-id="${messageId}"] .message-content`);
    if (msgDiv) {
        navigator.clipboard.writeText(msgDiv.innerText);
        showToast('Mensagem copiada!', 'success');
    }
}

function formatChatTime(timestamp) {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = Math.floor((now - date) / 1000);
    if (diff < 60) return 'agora';
    if (diff < 3600) return `${Math.floor(diff / 60)} min`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} h`;
    return date.toLocaleDateString('pt-BR');
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function scrollToBottom() {
    const container = document.getElementById('chat-messages');
    if (container) container.scrollTop = container.scrollHeight;
}

function startTypingPolling() {
    setInterval(async () => {
        if (!currentChatDisciplineId) return;
        const res = await fetch(`/api/disciplines/${currentChatDisciplineId}/chat/typing-status`, { credentials: 'include' });
        const data = await res.json();
        const typingDiv = document.getElementById('chat-typing-indicator');
        if (data.typing_users && data.typing_users.length) {
            typingDiv.textContent = `${data.typing_users.join(', ')} está digitando...`;
            typingDiv.style.display = 'block';
        } else {
            typingDiv.style.display = 'none';
        }
    }, 2000);
}

function debounce(fn, delay) {
    let timer;
    return function() {
        clearTimeout(timer);
        timer = setTimeout(fn, delay);
    };
}

// Inicialização
document.addEventListener('DOMContentLoaded', () => {
    initNotificationSound();
    startTypingPolling();

    const searchInput = document.getElementById('chat-search-input');
    if (searchInput) searchInput.addEventListener('input', debounce(() => searchMessages(), 500));

    const uploadBtn = document.getElementById('upload-image-btn');
    if (uploadBtn) {
        uploadBtn.addEventListener('click', () => {
            const input = document.createElement('input');
            input.type = 'file';
            input.accept = 'image/*';
            input.onchange = (e) => {
                if (e.target.files[0]) uploadChatImage(e.target.files[0]);
            };
            input.click();
        });
    }

    // Observador para scroll quando modal abrir
    const observer = new MutationObserver(() => {
        const modal = document.getElementById('disciplineChatModal');
        if (modal && !modal.classList.contains('hidden')) {
            scrollToBottom();
        }
    });
    observer.observe(document.body, { attributes: true, subtree: true, attributeFilter: ['class'] });
});