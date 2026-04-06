# src/routes/mission_routes.py
"""
Routes para Missões - Controllers HTTP
"""

from functools import wraps
from flask import Blueprint, jsonify, request, session
from src.models.user import db, User, Mission, UserMission
from src.services.mission_service import (
    MissionService,
    MissionNotFound,
    MissionAlreadyCompleted,
    MissionAlreadyAssigned,
    InvalidUser,
    get_teacher_students,
    get_teacher_disciplines
)

mission_bp = Blueprint('mission', __name__)


# ============================================================================
# DECORATORS
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

        user = User.query.get(session['user_id'])

        if not user or (user.role != 'teacher' and user.role != 'admin'):
            return jsonify({
                'error': 'Acesso restrito a professores e administradores',
                'success': False
            }), 403

        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# LISTAR MISSOES
# ============================================================================

@mission_bp.route('/missions', methods=['GET'])
@login_required
def get_all_missions():
    """Listar todas as missões ATIVAS"""
    try:
        missions = MissionService.get_all_missions()
        return jsonify({'success': True, 'missions': missions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/missions-all', methods=['GET'])
@teacher_or_admin_required
def get_all_missions_admin():
    """Listar TODAS as missões (admin/professor)"""
    try:
        missions = MissionService.get_all_missions_admin()
        return jsonify({'success': True, 'missions': missions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/missions/available', methods=['GET'])
@login_required
def get_available_missions():
    """Listar missões DISPONÍVEIS para o usuário"""
    try:
        user_id = session['user_id']
        missions = MissionService.get_available_missions(user_id)
        return jsonify({'success': True, 'missions': missions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/missions/<int:mission_id>', methods=['GET'])
@login_required
def get_mission_details(mission_id):
    """Obter detalhes de uma missão específica"""
    try:
        mission = MissionService.get_mission_details(mission_id)
        return jsonify({'success': True, 'mission': mission}), 200
    except MissionNotFound as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/user/missions', methods=['GET'])
@login_required
def get_user_missions():
    """Listar missões do usuário atual"""
    try:
        user_id = session['user_id']
        missions = MissionService.get_user_missions(user_id)
        return jsonify({'success': True, 'missions': missions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/users/<int:user_id>/missions', methods=['GET'])
@login_required
def get_user_missions_by_id(user_id):
    """Listar missões de um usuário específico"""
    try:
        missions = MissionService.get_user_missions(user_id)
        return jsonify({'success': True, 'missions': missions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/users/<int:user_id>/missions/pending', methods=['GET'])
@login_required
def get_user_pending_missions(user_id):
    """Listar missões PENDENTES de um usuário"""
    try:
        missions = MissionService.get_user_pending_missions(user_id)
        return jsonify({'success': True, 'missions': missions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/users/<int:user_id>/missions/completed', methods=['GET'])
@login_required
def get_user_completed_missions(user_id):
    """Listar missões COMPLETADAS de um usuário"""
    try:
        missions = MissionService.get_user_completed_missions(user_id)
        return jsonify({'success': True, 'missions': missions}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# CRIAR/ATUALIZAR/DELETAR MISSOES
# ============================================================================

@mission_bp.route('/missions', methods=['POST'])
@teacher_or_admin_required
def create_mission():
    """Criar nova missão (admin/professor)"""
    try:
        data = request.json
        user_id = session['user_id']
        mission = MissionService.create_mission(data, user_id)
        return jsonify({'success': True, 'mission': mission}), 201
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/missions/<int:mission_id>', methods=['PUT'])
@teacher_or_admin_required
def update_mission(mission_id):
    """Atualizar missão (admin/professor)"""
    try:
        data = request.json
        mission = MissionService.update_mission(mission_id, data)
        return jsonify({'success': True, 'mission': mission}), 200
    except MissionNotFound as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@mission_bp.route('/missions/<int:mission_id>', methods=['DELETE'])
@teacher_or_admin_required
def delete_mission(mission_id):
    """Deletar missão (admin/professor)"""
    try:
        result = MissionService.delete_mission(mission_id)
        return jsonify(result), 200
    except MissionNotFound as e:
        return jsonify({'error': str(e)}), 404
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# ATRIBUICAO DE MISSOES
# ============================================================================

@mission_bp.route('/missions/<int:mission_id>/assign', methods=['POST'])
@login_required
def assign_mission(mission_id):
    """Atribuir missão a um estudante"""
    try:
        data = request.json
        user_id = data.get('user_id') or session['user_id']

        if not user_id:
            user_id = session['user_id']

        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Usuário não encontrado', 'success': False}), 404

        # Alunos só podem aceitar missões para si mesmos
        if user.role == 'student' and user_id != session['user_id']:
            return jsonify({'error': 'Você só pode aceitar missões para si mesmo', 'success': False}), 403

        result = MissionService.assign_mission(user_id, mission_id)
        return jsonify({'success': True, 'mission': result}), 201
    except (MissionNotFound, InvalidUser, MissionAlreadyAssigned) as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@mission_bp.route('/missions/<int:mission_id>/assign-bulk', methods=['POST'])
@teacher_or_admin_required
def assign_mission_bulk(mission_id):
    """Atribuir missão a MÚLTIPLOS estudantes"""
    try:
        data = request.json
        student_ids = data.get('student_ids', [])
        user_id = session['user_id']

        if not student_ids:
            return jsonify({'error': 'student_ids é obrigatório'}), 400

        result = MissionService.assign_mission_bulk(
            mission_id,
            student_ids,
            user_id
        )
        return jsonify(result), 200
    except MissionNotFound as e:
        return jsonify({'error': str(e)}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ============================================================================
# COMPLETAR MISSOES
# ============================================================================

@mission_bp.route('/missions/<int:user_mission_id>/complete', methods=['POST'])
@login_required
def complete_mission(user_mission_id):
    """Completar uma MISSÃO"""
    try:
        from datetime import datetime

        user_id = session['user_id']

        print(f"🔍 Completando missão {user_mission_id} para usuário {user_id}")

        # Buscar a missão do usuário
        user_mission = UserMission.query.get(user_mission_id)

        if not user_mission:
            return jsonify({'error': 'Missão não encontrada', 'success': False}), 404

        # Verificar se pertence ao usuário
        if user_mission.user_id != user_id:
            return jsonify({'error': 'Esta missão não pertence a você', 'success': False}), 403

        # Verificar se já foi completada
        if user_mission.status == 'completed':
            return jsonify({'error': 'Missão já completada', 'success': False}), 400

        # Buscar a missão original
        mission = Mission.query.get(user_mission.mission_id)
        if not mission:
            return jsonify({'error': 'Missão não encontrada', 'success': False}), 404

        # Completar a missão
        user_mission.status = 'completed'
        user_mission.completion_date = datetime.utcnow()

        # Adicionar XP e coins ao usuário
        user = User.query.get(user_id)
        old_level = user.current_level

        user.current_xp += mission.xp_reward
        user.coins += mission.coin_reward

        # Verificar level up (a cada 100 XP)
        new_level = old_level
        while user.current_xp >= new_level * 100:
            user.current_xp -= new_level * 100
            new_level += 1

        level_up = new_level > old_level
        if level_up:
            user.current_level = new_level

        db.session.commit()

        print(f"✅ Missão completada! XP ganho: {mission.xp_reward}, Level up: {level_up}")

        return jsonify({
            'success': True,
            'message': 'Missão completada com sucesso!',
            'xp_earned': mission.xp_reward,
            'coins_earned': mission.coin_reward,
            'total_xp': user.current_xp,
            'total_coins': user.coins,
            'new_level': user.current_level,
            'level_up': level_up
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao completar missão: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# ROTAS DO PROFESSOR
# ============================================================================

@mission_bp.route('/teacher/students', methods=['GET'])
@teacher_or_admin_required
def get_teacher_students_route():
    """Listar TODOS OS ESTUDANTES das disciplinas do professor"""
    try:
        user_id = session['user_id']
        result = get_teacher_students(user_id)
        return jsonify({'success': True, **result}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


