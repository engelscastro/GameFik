# src/routes/user_routes.py
"""
Routes para Usuários - Controllers HTTP
Usa user_service.py para toda lógica de negócio
Desacoplado, limpo e profissional
"""

from functools import wraps
from flask import Blueprint, jsonify, request, session
from src.services.user_service import (
    UserService,
    UserNotFound,
    UserAlreadyExists,
    InvalidCredentials,
    InvalidUserData
)
from src.models.academic import Professor

user_bp = Blueprint('user', __name__)


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
# AUTENTICACAO
# ============================================================================

@user_bp.route('/register', methods=['POST'])
def register():
    """Registrar novo usuário"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        email = data.get('email')
        role = data.get('role', 'student')
        
        user = UserService.register_user(username, password, email, role)
        return jsonify({'success': True, 'user': user}), 201
    except (UserAlreadyExists, InvalidUserData) as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@user_bp.route('/login', methods=['POST'])
def login():
    """Autenticar usuário e criar sessão"""
    try:
        data = request.json
        username = data.get('username')
        password = data.get('password')
        
        user = UserService.authenticate_user(username, password)
        
        # Criar sessão Flask
        session['user_id'] = user['id']
        session['username'] = user['username']
        session['role'] = user['role']
        
        return jsonify({'success': True, 'user': user}), 200
    except InvalidCredentials as e:
        return jsonify({'error': str(e), 'success': False}), 401
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@user_bp.route('/auth/logout', methods=['POST'])
@login_required
def logout():
    """Fazer logout do usuário"""
    try:
        session.clear()
        return jsonify({'success': True, 'message': 'Logout realizado com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@user_bp.route('/auth/me', methods=['GET'])
@login_required
def get_current_user():
    """Obter dados do usuário logado"""
    try:
        user_id = session['user_id']
        user = UserService.get_user(user_id)  # retorna um dict

        # Se for professor, anexar perfil com nome
        if user.get('role') == 'teacher':
            professor = Professor.query.filter_by(user_id=user_id).first()
            if professor:
                user['professor_profile'] = {
                    'id': professor.id,
                    'nome': professor.nome,
                    'cpf': professor.cpf,
                    'departamento': professor.departamento,
                    'anos_turmas': professor.anos_turmas,
                    'niveis_ensino': professor.niveis_ensino,
                }

        return jsonify({'success': True, 'user': user}), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# LEITURA - Usuários
# ============================================================================

@user_bp.route('/users/<int:user_id>', methods=['GET'])
@login_required
def get_user(user_id):
    """Obter dados de um usuário"""
    try:
        user = UserService.get_user(user_id)
        return jsonify({'success': True, 'user': user}), 200
    except UserNotFound as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# src/routes/user_routes.py

@user_bp.route('/users', methods=['GET'])
@login_required  # Mantém apenas login_required, remove teacher_or_admin_required
def get_users():
    """Listar todos os usuários (qualquer usuário logado pode ver para ranking)"""
    try:
        role = request.args.get('role')
        users = UserService.get_all_users(role=role)
        return jsonify({'success': True, 'users': users}), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# ATUALIZACAO - Usuários
# ============================================================================

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@login_required
def update_user(user_id):
    """Atualizar dados do usuário"""
    try:
        # Só pode atualizar a si próprio (ou admin)
        current_user_id = session['user_id']
        if user_id != current_user_id:
            from src.models.user import User
            current_user = User.query.get(current_user_id)
            if not current_user or current_user.role != 'admin':
                return jsonify({
                    'error': 'Você só pode atualizar sua própria conta',
                    'success': False
                }), 403
        
        data = request.json
        user = UserService.update_user(user_id, data)
        return jsonify({'success': True, 'user': user}), 200
    except (UserNotFound, UserAlreadyExists) as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except InvalidUserData as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# SENHA - Usuários
# ============================================================================

@user_bp.route('/users/<int:user_id>/change-password', methods=['POST'])
@login_required
def change_password(user_id):
    """Alterar senha do usuário"""
    try:
        # Só pode alterar sua própria senha
        current_user_id = session['user_id']
        if user_id != current_user_id:
            return jsonify({
                'error': 'Você só pode alterar sua própria senha',
                'success': False
            }), 403
        
        data = request.json
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        
        result = UserService.change_password(user_id, old_password, new_password)
        return jsonify(result), 200
    except (UserNotFound, InvalidCredentials, InvalidUserData) as e:
        return jsonify({'error': str(e), 'success': False}), 400
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# DELECAO - Usuários (ADMIN)
# ============================================================================

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@teacher_or_admin_required
def delete_user(user_id):
    """Deletar usuário (admin/professor)"""
    try:
        result = UserService.delete_user(user_id)
        return jsonify(result), 200
    except UserNotFound as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


# ============================================================================
# ESTATISTICAS - Usuários
# ============================================================================

@user_bp.route('/users/<int:user_id>/stats', methods=['GET'])
@login_required
def get_user_stats(user_id):
    """Obter estatísticas do usuário"""
    try:
        stats = UserService.get_user_stats(user_id)
        return jsonify({'success': True, 'stats': stats}), 200
    except UserNotFound as e:
        return jsonify({'error': str(e), 'success': False}), 404
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500
