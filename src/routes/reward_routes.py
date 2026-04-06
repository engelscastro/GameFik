# src/routes/reward_routes.py
"""
Routes para Recompensas - Controllers HTTP
Usa reward_service.py para toda lógica de negócio
Desacoplado, limpo e profissional
"""

from functools import wraps
from flask import Blueprint, jsonify, request, session
from src.services.reward_service import (
    RewardService,
    RewardNotFound,
    InsufficientCoins,
    RewardAlreadyRedeemed,
    InvalidRewardData
)

reward_bp = Blueprint('reward', __name__)


# ============================================================================
# DECORATORS (integrados)
# ============================================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário', 'success': False}), 401
        return f(*args, **kwargs)
    return decorated_function


def teacher_or_admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário', 'success': False}), 401
        
        from src.models.user import User
        user = User.query.get(session['user_id'])
        
        if not user or (user.role != 'teacher' and user.role != 'admin'):
            return jsonify({
                'error': 'Acesso restrito a professores e administradores',
                'success': False
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# LISTAR RECOMPENSAS
# ============================================================================

@reward_bp.route('/rewards', methods=['GET'])
@login_required
def get_rewards():
    """Listar todas as recompensas disponíveis"""
    try:
        rewards = RewardService.get_all_rewards()
        return jsonify({'success': True, 'rewards': rewards}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@reward_bp.route('/rewards/all', methods=['GET'])
@teacher_or_admin_required
def get_all_rewards_admin():
    """Listar TODAS as recompensas (admin/professor)"""
    try:
        rewards = RewardService.get_all_rewards_admin()
        return jsonify({'success': True, 'rewards': rewards}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@reward_bp.route('/rewards/<int:reward_id>', methods=['GET'])
@login_required
def get_reward(reward_id):
    """Obter detalhes de uma recompensa"""
    try:
        reward = RewardService.get_reward_details(reward_id)
        return jsonify({'success': True, 'reward': reward}), 200
    except RewardNotFound as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@reward_bp.route('/users/<int:user_id>/rewards', methods=['GET'])
@login_required
def get_user_rewards(user_id):
    """Listar todas as recompensas de um usuário"""
    try:
        rewards = RewardService.get_user_rewards(user_id)
        return jsonify({'success': True, 'rewards': rewards}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@reward_bp.route('/users/<int:user_id>/rewards/pending', methods=['GET'])
@login_required
def get_pending_rewards(user_id):
    """Listar recompensas PENDENTES de um usuário"""
    try:
        rewards = RewardService.get_user_pending_rewards(user_id)
        return jsonify({'success': True, 'rewards': rewards}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@reward_bp.route('/users/<int:user_id>/rewards/redeemed', methods=['GET'])
@login_required
def get_redeemed_rewards(user_id):
    """Listar recompensas JÁ RESGATADAS de um usuário"""
    try:
        rewards = RewardService.get_user_redeemed_rewards(user_id)
        return jsonify({'success': True, 'rewards': rewards}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# CRIAR/ATUALIZAR/DELETAR RECOMPENSAS (ADMIN)
# ============================================================================

@reward_bp.route('/rewards', methods=['POST'])
@teacher_or_admin_required
def create_reward():
    """Criar nova recompensa (admin/professor)"""
    try:
        data = request.json
        reward = RewardService.create_reward(data)
        return jsonify({'success': True, 'reward': reward}), 201
    except InvalidRewardData as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@reward_bp.route('/rewards/<int:reward_id>', methods=['PUT'])
@teacher_or_admin_required
def update_reward(reward_id):
    """Atualizar recompensa (admin/professor)"""
    try:
        data = request.json
        reward = RewardService.update_reward(reward_id, data)
        return jsonify({'success': True, 'reward': reward}), 200
    except RewardNotFound as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@reward_bp.route('/rewards/<int:reward_id>', methods=['DELETE'])
@teacher_or_admin_required
def delete_reward(reward_id):
    """Deletar recompensa (admin/professor)"""
    try:
        result = RewardService.delete_reward(reward_id)
        return jsonify(result), 200
    except RewardNotFound as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except ValueError as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# COMPRA E RESGATE
# ============================================================================

@reward_bp.route('/purchase-reward/<int:reward_id>', methods=['POST'])
@login_required
def purchase_reward(reward_id):
    """Comprar recompensa com coins"""
    try:
        user_id = session['user_id']
        result = RewardService.purchase_reward(user_id, reward_id)
        return jsonify(result), 200
    except (RewardNotFound, InsufficientCoins) as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except ValueError as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@reward_bp.route('/user_rewards/<int:user_reward_id>/redeem', methods=['PUT'])
@login_required
def redeem_reward(user_reward_id):
    """Marcar recompensa como resgatada"""
    try:
        user_id = session['user_id']
        result = RewardService.redeem_reward(user_reward_id, user_id)
        return jsonify(result), 200
    except (RewardNotFound, RewardAlreadyRedeemed) as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# VERIFICACAO - Recompensas (chamada automática)
# ============================================================================

@reward_bp.route('/rewards/check/<int:user_id>', methods=['POST'])
@teacher_or_admin_required
def check_rewards(user_id):
    """Verificar novas recompensas disponíveis para usuário"""
    try:
        new_available = RewardService.check_rewards(user_id)
        return jsonify({
            'success': True,
            'new_available_rewards': new_available
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
