# src/routes/achievement_routes.py
"""
Routes para Conquistas - Controllers HTTP
Usa achievement_service.py para toda lógica de negócio
Desacoplado, limpo e profissional
"""

from functools import wraps
from flask import Blueprint, jsonify, request, session
from src.services.achievement_service import (
    AchievementService,
    AchievementNotFound,
    AchievementAlreadyAwarded,
    InvalidAchievementData
)

achievement_bp = Blueprint('achievement', __name__)


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
# LISTAR CONQUISTAS
# ============================================================================

@achievement_bp.route('/achievements', methods=['GET'])
@login_required
def get_achievements():
    """Listar todas as conquistas"""
    try:
        achievements = AchievementService.get_all_achievements()
        return jsonify({'success': True, 'achievements': achievements}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@achievement_bp.route('/user-achievements', methods=['GET'])
@login_required
def get_user_achievements():
    """Listar conquistas desbloqueadas do usuário"""
    try:
        user_id = session['user_id']
        achievements = AchievementService.get_user_achievements(user_id)
        return jsonify({'success': True, 'achievements': achievements}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@achievement_bp.route('/user-achievements/progress', methods=['GET'])
@login_required
def get_user_achievement_progress():
    """Obter progresso do usuário para TODAS as conquistas"""
    try:
        from src.models.user import Achievement, UserAchievement, User, UserMission

        user_id = session['user_id']
        user = User.query.get(user_id)

        if not user:
            return jsonify({'success': True, 'progress': []}), 200

        # Buscar todas as conquistas
        all_achievements = Achievement.query.all()

        if not all_achievements:
            return jsonify({'success': True, 'progress': []}), 200

        # Buscar conquistas já desbloqueadas pelo usuário
        unlocked = UserAchievement.query.filter_by(user_id=user_id).all()
        unlocked_ids = [ua.achievement_id for ua in unlocked]

        # Calcular estatísticas do usuário
        completed_missions_count = UserMission.query.filter_by(
            user_id=user_id, status='completed'
        ).count()

        progress = []

        for ach in all_achievements:
            earned = ach.id in unlocked_ids
            progress_percent = 100 if earned else 0

            # Calcular progresso baseado nos requisitos
            requirements = []

            if not earned:
                if ach.mission_count_threshold and ach.mission_count_threshold > 0:
                    progress_percent = (completed_missions_count / ach.mission_count_threshold) * 100
                    if progress_percent > 100:
                        progress_percent = 100
                    requirements.append(f"{completed_missions_count}/{ach.mission_count_threshold} missões")

                elif ach.xp_threshold and ach.xp_threshold > 0:
                    progress_percent = (user.current_xp / ach.xp_threshold) * 100
                    if progress_percent > 100:
                        progress_percent = 100
                    requirements.append(f"{user.current_xp}/{ach.xp_threshold} XP")

                elif ach.level_threshold and ach.level_threshold > 0:
                    progress_percent = (user.current_level / ach.level_threshold) * 100
                    if progress_percent > 100:
                        progress_percent = 100
                    requirements.append(f"Nível {user.current_level}/{ach.level_threshold}")

                elif ach.coin_threshold and ach.coin_threshold > 0:
                    progress_percent = (user.coins / ach.coin_threshold) * 100
                    if progress_percent > 100:
                        progress_percent = 100
                    requirements.append(f"{user.coins}/{ach.coin_threshold} cristais")

            # Se for conquista de Primeiro Passo (missões completadas >= 1)
            if ach.name == 'Primeiro Passo' and completed_missions_count >= 1:
                earned = True
                progress_percent = 100
                requirements = ["✅ Conquista desbloqueada!"]

            progress.append({
                'id': ach.id,
                'name': ach.name,
                'description': ach.description or f"Complete os requisitos para desbloquear {ach.name}",
                'icon': getattr(ach, 'icon', '🏆'),
                'points': getattr(ach, 'points', 100),
                'earned': earned,
                'progress': round(progress_percent, 1),
                'requirements': requirements if requirements else ["Complete os requisitos"]
            })

        return jsonify({'success': True, 'progress': progress}), 200

    except Exception as e:
        print(f"❌ Erro em user-achievements/progress: {e}")
        import traceback
        traceback.print_exc()
        # Em caso de erro, retornar lista vazia
        return jsonify({'success': True, 'progress': []}), 200

@achievement_bp.route('/achievements/<int:achievement_id>', methods=['GET'])
@login_required
def get_achievement_details(achievement_id):
    """Obter detalhes de uma conquista específica"""
    try:
        achievement = AchievementService.get_all_achievements()
        for ach in achievement:
            if ach['id'] == achievement_id:
                return jsonify({'success': True, 'achievement': ach}), 200
        return jsonify({'error': 'Conquista não encontrada', 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# CRIAR/ATUALIZAR/DELETAR CONQUISTAS (ADMIN)
# ============================================================================

@achievement_bp.route('/achievements', methods=['POST'])
@teacher_or_admin_required
def create_achievement():
    """Criar nova conquista (admin/professor)"""
    try:
        data = request.json
        achievement = AchievementService.create_achievement(data)
        return jsonify({'success': True, 'achievement': achievement}), 201
    except InvalidAchievementData as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@achievement_bp.route('/achievements/<int:achievement_id>', methods=['PUT'])
@teacher_or_admin_required
def update_achievement(achievement_id):
    """Atualizar conquista (admin/professor)"""
    try:
        data = request.json
        achievement = AchievementService.update_achievement(achievement_id, data)
        return jsonify({'success': True, 'achievement': achievement}), 200
    except AchievementNotFound as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@achievement_bp.route('/achievements/<int:achievement_id>', methods=['DELETE'])
@teacher_or_admin_required
def delete_achievement(achievement_id):
    """Deletar conquista (admin/professor)"""
    try:
        result = AchievementService.delete_achievement(achievement_id)
        return jsonify(result), 200
    except AchievementNotFound as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except ValueError as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# ATRIBUICAO DE CONQUISTAS (ADMIN)
# ============================================================================

@achievement_bp.route('/achievements/<int:achievement_id>/award', methods=['POST'])
@teacher_or_admin_required
def award_achievement(achievement_id):
    """Atribuir conquista a um usuário (admin/professor)"""
    try:
        data = request.json
        user_id = data.get('user_id')
        
        if not user_id:
            return jsonify({'error': 'user_id é obrigatório', 'success': False}), 400
        
        result = AchievementService.award_achievement(user_id, achievement_id)
        return jsonify(result), 200
    except (AchievementNotFound, AchievementAlreadyAwarded, ValueError) as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# VERIFICACAO - Conquistas (chamada automática)
# ============================================================================

@achievement_bp.route('/achievements/check/<int:user_id>', methods=['POST'])
@teacher_or_admin_required
def check_achievements(user_id):
    """Verificar e desbloquear novas conquistas do usuário"""
    try:
        new_achievements = AchievementService.check_achievements(user_id)
        return jsonify({
            'success': True,
            'new_achievements': new_achievements
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
