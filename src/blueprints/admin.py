"""
Blueprint para gerenciamento de administradores
Admin Master tem controle total do sistema: usuários, professores, estudantes, disciplinas, matrículas, notas
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, session
from sqlalchemy import func, and_

from src.models.academic import (
    Student, Professor, Admin, Discipline, Enrollment, Grade,
    AcademicMission, DisciplineChat, ChatMessage, ClassActivity
)
from src.models.user import db, User, Mission, Achievement, Reward, UserMission, UserAchievement, UserReward
from .utils import login_required, admin_required, master_admin_required

# Criar blueprint
admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ========== GESTÃO DE ADMINISTRADORES ==========

@admin_bp.route('/admins', methods=['POST'])
@master_admin_required
def create_admin():
    """Criar novo administrador (apenas Master)"""
    try:
        data = request.json

        required_fields = ['nome', 'cpf', 'cargo']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Campo {field} é obrigatório'}), 400

        # Verificar CPF único
        if Admin.query.filter_by(cpf=data['cpf']).first():
            return jsonify({'success': False, 'error': 'CPF já cadastrado'}), 400

        # Verificar se usuário já existe
        if User.query.filter_by(username=data['cpf']).first():
            return jsonify({'success': False, 'error': 'Usuário já existe'}), 400

        # Criar usuário
        user = User(username=data['cpf'], role='admin')
        user.set_password(data.get('password', 'admin123'))
        db.session.add(user)
        db.session.flush()

        # Criar perfil admin
        admin = Admin(
            user_id=user.id,
            nome=data['nome'],
            cpf=data['cpf'],
            cargo=data['cargo'],
            setor=data.get('setor'),
            permissoes=','.join(data.get('permissoes', [])),
            nivel_acesso=data.get('nivel_acesso', 2)
        )

        db.session.add(admin)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Administrador criado com sucesso!',
            'admin': admin.to_dict(),
            'login_info': {'username': data['cpf'], 'password': data.get('password', 'admin123'), 'role': 'admin'}
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/admins', methods=['GET'])
@admin_required
def get_all_admins():
    """Listar todos os administradores"""
    try:
        admins = Admin.query.all()
        return jsonify({'success': True, 'admins': [a.to_dict() for a in admins]})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/admins/<int:admin_id>', methods=['DELETE'])
@master_admin_required
def delete_admin(admin_id):
    """Excluir administrador (apenas Master)"""
    try:
        admin = Admin.query.get(admin_id)
        if not admin:
            return jsonify({'success': False, 'error': 'Admin não encontrado'}), 404

        # Não permitir excluir o próprio admin master
        current_user = User.query.get(session['user_id'])
        current_admin = Admin.query.filter_by(user_id=current_user.id).first()

        if current_admin and current_admin.id == admin_id:
            return jsonify({'success': False, 'error': 'Não é possível excluir seu próprio usuário'}), 400

        user = admin.user
        db.session.delete(admin)
        db.session.delete(user)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Administrador excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== DASHBOARD DO ADMIN ==========

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_admin_dashboard():
    """Dashboard completo do administrador com estatísticas do sistema"""
    try:
        # Estatísticas de usuários
        total_users = User.query.count()
        total_students = Student.query.count()
        total_professors = Professor.query.count()
        total_admins = Admin.query.count()

        # Estatísticas acadêmicas
        total_disciplines = Discipline.query.count()
        total_enrollments = Enrollment.query.count()
        active_enrollments = Enrollment.query.filter_by(status='active').count()
        total_grades = Grade.query.count()

        # Estatísticas de gamificação
        total_xp_all = db.session.query(func.sum(User.current_xp)).scalar() or 0
        total_coins_all = db.session.query(func.sum(User.coins)).scalar() or 0
        avg_level = db.session.query(func.avg(User.current_level)).scalar() or 0

        # Top estudantes por XP
        top_students = db.session.query(
            User.id, User.username, User.current_xp, User.current_level, Student.nome
        ).join(Student, User.id == Student.user_id).order_by(User.current_xp.desc()).limit(5).all()

        top_students_data = [
            {'id': s[0], 'username': s[1], 'xp': s[2], 'level': s[3], 'nome': s[4]}
            for s in top_students
        ]

        # Atividades recentes (últimas 10 matrículas)
        recent_enrollments = Enrollment.query.order_by(Enrollment.enrollment_date.desc()).limit(10).all()
        recent_activities = []
        for e in recent_enrollments:
            student = Student.query.get(e.student_id)
            discipline = Discipline.query.get(e.discipline_id)
            recent_activities.append({
                'type': 'enrollment',
                'student': student.nome if student else 'N/A',
                'discipline': discipline.nome if discipline else 'N/A',
                'date': e.enrollment_date.isoformat() if e.enrollment_date else None
            })

        return jsonify({
            'success': True,
            'dashboard': {
                'users': {
                    'total': total_users,
                    'students': total_students,
                    'professors': total_professors,
                    'admins': total_admins
                },
                'academic': {
                    'disciplines': total_disciplines,
                    'enrollments': total_enrollments,
                    'active_enrollments': active_enrollments,
                    'grades': total_grades
                },
                'gamification': {
                    'total_xp': total_xp_all,
                    'total_coins': total_coins_all,
                    'avg_level': round(float(avg_level), 1)
                },
                'top_students': top_students_data,
                'recent_activities': recent_activities
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== GESTÃO COMPLETA DE USUÁRIOS ==========

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_all_users():
    """Listar todos os usuários do sistema com seus perfis"""
    try:
        users = User.query.all()
        users_data = []

        for user in users:
            user_dict = user.to_dict()

            # Adicionar perfil específico
            if user.role == 'student':
                student = Student.query.filter_by(user_id=user.id).first()
                if student:
                    user_dict['profile'] = student.to_dict()
            elif user.role == 'teacher':
                professor = Professor.query.filter_by(user_id=user.id).first()
                if professor:
                    user_dict['profile'] = professor.to_dict()
            elif user.role == 'admin':
                admin = Admin.query.filter_by(user_id=user.id).first()
                if admin:
                    user_dict['profile'] = admin.to_dict()

            users_data.append(user_dict)

        return jsonify({'success': True, 'users': users_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def reset_user_password(user_id):
    """Resetar senha de qualquer usuário"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404

        data = request.json
        new_password = data.get('password', 'nova_senha123')
        user.set_password(new_password)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Senha do usuário {user.username} redefinida com sucesso',
            'new_password': new_password
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>/change-role', methods=['PUT'])
@master_admin_required
def change_user_role(user_id):
    """Alterar role do usuário (apenas Master)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404

        data = request.json
        new_role = data.get('role')

        if new_role not in ['student', 'teacher', 'admin']:
            return jsonify({'success': False, 'error': 'Role inválida'}), 400

        # Não permitir alterar o próprio role se for o último master
        current_user = User.query.get(session['user_id'])
        if current_user.id == user_id and new_role != 'admin':
            return jsonify({'success': False, 'error': 'Não pode remover seu próprio acesso de admin'}), 400

        user.role = new_role
        db.session.commit()

        return jsonify({'success': True, 'message': f'Role alterado para {new_role}', 'user': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/users/<int:user_id>', methods=['DELETE'])
@master_admin_required
def delete_any_user(user_id):
    """Excluir qualquer usuário do sistema (apenas Master)"""
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'error': 'Usuário não encontrado'}), 404

        # Não permitir excluir o próprio usuário master
        current_user = User.query.get(session['user_id'])
        if current_user.id == user_id:
            return jsonify({'success': False, 'error': 'Não é possível excluir seu próprio usuário'}), 400

        # Excluir perfil específico
        if user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                db.session.delete(student)
        elif user.role == 'teacher':
            professor = Professor.query.filter_by(user_id=user.id).first()
            if professor:
                db.session.delete(professor)
        elif user.role == 'admin':
            admin = Admin.query.filter_by(user_id=user.id).first()
            if admin:
                db.session.delete(admin)

        db.session.delete(user)
        db.session.commit()

        return jsonify({'success': True, 'message': f'Usuário {user.username} excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== GESTÃO DE SISTEMA (BACKUP, LOGS, CONFIG) ==========

@admin_bp.route('/system/stats', methods=['GET'])
@admin_required
def get_system_stats():
    """Estatísticas detalhadas do sistema"""
    try:
        # Contagem por tabelas
        stats = {
            'users': {
                'total': User.query.count(),
                'by_role': {
                    'student': User.query.filter_by(role='student').count(),
                    'teacher': User.query.filter_by(role='teacher').count(),
                    'admin': User.query.filter_by(role='admin').count()
                }
            },
            'academic': {
                'students': Student.query.count(),
                'professors': Professor.query.count(),
                'disciplines': Discipline.query.count(),
                'enrollments': Enrollment.query.count(),
                'grades': Grade.query.count(),
                'missions': AcademicMission.query.count()
            },
            'gamification': {
                'missions': Mission.query.count(),
                'achievements': Achievement.query.count(),
                'rewards': Reward.query.count(),
                'completed_missions': UserMission.query.filter_by(status='completed').count()
            },
            'chat': {
                'chats': DisciplineChat.query.count(),
                'messages': ChatMessage.query.count()
            }
        }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ATUALIZAÇÃO DO utils.py (adicionar master_admin_required) ==========
# Adicione este decorator no arquivo utils.py

def master_admin_required(f):
    """Decorator para verificar se o usuário é admin master (nível 1)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401

        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Acesso restrito a administradores'}), 403

        # Verificar se é admin master
        from src.models.academic import Admin
        admin = Admin.query.filter_by(user_id=user.id).first()
        if not admin or admin.nivel_acesso != 1:
            return jsonify({'error': 'Acesso restrito a administradores master'}), 403

        return f(*args, **kwargs)
    return decorated_function