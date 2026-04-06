// ==================== CONQUISTAS ====================

async function loadAchievements() {
    if (!state.user) return;

    try {
        const response = await fetch(`${API_BASE_URL}/user-achievements/progress`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            renderAchievements(data.progress || []);
        }
    } catch (error) {
        console.error('Achievements load error:', error);
    }
}

function renderAchievements(achievements) {
    const container = document.getElementById('achievements-grid');
    if (!achievements?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma conquista disponível</p>';
        return;
    }

    container.innerHTML = achievements.map(achievement => {
        // Determinar classe de progresso
        let progressClass = '';
        let progressText = '';

        if (achievement.earned) {
            progressClass = 'earned';
            progressText = '<span class="achievement-badge">✅ Desbloqueada!</span>';
        } else if (achievement.progress >= 100) {
            progressClass = 'ready';
            progressText = '<span class="achievement-badge ready">🎯 Pronta para desbloquear!</span>';
        } else {
            progressText = `<span class="achievement-badge locked">🔒 ${Math.round(achievement.progress)}% completo</span>`;
        }

        // Criar HTML dos requisitos
        let requirementsHtml = '';
        if (achievement.requirements && achievement.requirements.length > 0) {
            requirementsHtml = `
                <div class="achievement-requirements">
                    <strong>Requisitos:</strong>
                    <ul>
                        ${achievement.requirements.map(req => `<li>${req}</li>`).join('')}
                    </ul>
                </div>
            `;
        }

        return `
        <div class="achievement-card ${achievement.earned ? 'earned' : ''}" data-progress="${achievement.progress}">
            <div class="achievement-header">
                <div class="achievement-icon">
                    ${achievement.icon || '🏆'}
                </div>
                ${progressText}
            </div>
            <h4 class="achievement-title">${escapeHtml(achievement.name)}</h4>
            <p class="achievement-description">${escapeHtml(achievement.description || 'Complete os requisitos para desbloquear esta conquista.')}</p>
            ${requirementsHtml}
            ${!achievement.earned ? `
                <div class="achievement-progress">
                    <div class="progress-bar">
                        <div class="progress-fill" style="width: ${achievement.progress}%"></div>
                    </div>
                    <span class="progress-text">${Math.round(achievement.progress)}% completo</span>
                </div>
            ` : ''}
            <div class="achievement-points">
                <i class="fas fa-star"></i> ${achievement.points} pontos
            </div>
        </div>
    `}).join('');
}