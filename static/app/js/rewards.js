// ==================== RECOMPENSAS ====================

async function loadRewards() {
    if (!state.user) return;

    try {
        const [shopRes, userRes] = await Promise.all([
            fetch(`${API_BASE_URL}/rewards`, { credentials: 'include' }),
            fetch(`${API_BASE_URL}/users/${state.user.id}/rewards`, { credentials: 'include' })
        ]);

        if (shopRes.ok) {
            const data = await shopRes.json();
            renderShopRewards(data.rewards || []);
        }

        if (userRes.ok) {
            const data = await userRes.json();
            renderUserRewards(data.rewards || []);
        }

        document.getElementById('shop-coins').textContent = state.user?.coins || 0;
    } catch (error) {
        console.error('Rewards load error:', error);
    }
}

function renderShopRewards(rewards) {
    const container = document.getElementById('shop-rewards-grid');
    if (!rewards?.length) {
        container.innerHTML = '<p class="empty-state">Nenhuma recompensa disponível</p>';
        return;
    }

    container.innerHTML = rewards.map(reward => `
        <div class="reward-card">
            <div class="reward-header">
                <div class="reward-icon">${reward.icon || '🎁'}</div>
            </div>
            <h4 class="reward-title">${escapeHtml(reward.name)}</h4>
            <p class="reward-description">${escapeHtml(reward.description || '')}</p>
            <div class="reward-cost"><i class="fas fa-gem"></i> ${reward.coin_cost} cristais</div>
            <button class="btn btn-primary btn-full" onclick="purchaseReward(${reward.id})">Comprar</button>
        </div>
    `).join('');
}

function renderUserRewards(rewards) {
    const container = document.getElementById('my-rewards-grid');
    if (!rewards?.length) {
        container.innerHTML = '<p class="empty-state">Você não possui recompensas</p>';
        return;
    }

    container.innerHTML = rewards.map(reward => `
        <div class="reward-card">
            <div class="reward-header">
                <div class="reward-icon">${reward.reward?.icon || '🎁'}</div>
                ${reward.is_redeemed ? '<span class="reward-status redeemed">Resgatado</span>' : ''}
            </div>
            <h4 class="reward-title">${escapeHtml(reward.reward?.name || 'Recompensa')}</h4>
            <p class="reward-description">${escapeHtml(reward.reward?.description || '')}</p>
            <p class="reward-date">Comprado em: ${formatDate(reward.purchase_date)}</p>
            ${!reward.is_redeemed ? `
                <button class="btn btn-success btn-full" onclick="redeemReward(${reward.id})">Resgatar</button>
            ` : ''}
        </div>
    `).join('');
}

async function purchaseReward(rewardId) {
    try {
        const response = await fetch(`${API_BASE_URL}/purchase-reward/${rewardId}`, {
            method: 'POST',
            credentials: 'include'
        });

        const data = await response.json();
        if (data.success) {
            showToast('Recompensa comprada!', 'success');
            state.user.coins = data.remaining_coins;
            await updateUI();
            await loadRewards();
        } else {
            showToast(data.error || 'Erro ao comprar recompensa', 'error');
        }
    } catch (error) {
        console.error('Purchase reward error:', error);
        showToast('Erro ao comprar recompensa', 'error');
    }
}

async function redeemReward(userRewardId) {
    try {
        const response = await fetch(`${API_BASE_URL}/user_rewards/${userRewardId}/redeem`, {
            method: 'PUT',
            credentials: 'include'
        });

        const data = await response.json();
        if (data.success) {
            showToast('Recompensa resgatada!', 'success');
            await loadRewards();
        } else {
            showToast(data.error || 'Erro ao resgatar recompensa', 'error');
        }
    } catch (error) {
        console.error('Redeem reward error:', error);
        showToast('Erro ao resgatar recompensa', 'error');
    }
}