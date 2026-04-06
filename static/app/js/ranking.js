// ==================== RANKING ====================

async function loadRanking() {
    try {
        const response = await fetch(`${API_BASE_URL}/users`, {
            credentials: 'include'
        });

        if (response.ok) {
            const data = await response.json();
            const users = (data.users || []).sort((a, b) => b.current_xp - a.current_xp);
            renderRanking(users);
        }
    } catch (error) {
        console.error('Ranking load error:', error);
    }
}

function renderRanking(users) {
    const container = document.getElementById('ranking-list');
    if (!users?.length) {
        container.innerHTML = '<p class="empty-state">Nenhum usuário no ranking</p>';
        return;
    }

    container.innerHTML = users.map((user, index) => {
        let positionClass = 'normal';
        if (index === 0) positionClass = 'gold';
        else if (index === 1) positionClass = 'silver';
        else if (index === 2) positionClass = 'bronze';

        return `
            <div class="ranking-item">
                <div class="ranking-position ${positionClass}">${index + 1}</div>
                <div class="ranking-avatar"><i class="fas fa-user"></i></div>
                <div class="ranking-info">
                    <div class="ranking-name">${escapeHtml(user.username)}</div>
                    <div class="ranking-level">Nível ${user.current_level}</div>
                </div>
                <div class="ranking-xp">${user.current_xp} XP</div>
            </div>
        `;
    }).join('');
}