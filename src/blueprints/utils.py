"""
Módulo com utilitários compartilhados para os blueprints acadêmicos
Contém decorators de autenticação e autorização
"""

from functools import wraps
from flask import jsonify, session
from src.models.user import User


def login_required(f):
    """Decorator para verificar se o usuário está autenticado"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """Decorator para verificar se o usuário é estudante"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401

        user = User.query.get(session['user_id'])
        if not user or user.role != 'student':
            return jsonify({'error': 'Acesso restrito a estudantes'}), 403

        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """Decorator para verificar se o usuário é professor"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401

        user = User.query.get(session['user_id'])
        if not user or user.role != 'teacher':
            return jsonify({'error': 'Acesso restrito a professores'}), 403

        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """Decorator para verificar se o usuário é administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401

        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Acesso restrito a administradores'}), 403

        return f(*args, **kwargs)
    return decorated_function


def master_admin_required(f):
    """
    Decorator para verificar se o usuário é administrador MASTER (nível 1)
    Apenas admins com nivel_acesso = 1 têm acesso total ao sistema
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401

        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Acesso restrito a administradores'}), 403

        # Importar aqui para evitar circular import
        from src.models.academic import Admin
        admin = Admin.query.filter_by(user_id=user.id).first()

        if not admin:
            return jsonify({'error': 'Perfil de administrador não encontrado'}), 403

        if admin.nivel_acesso != 1:
            return jsonify({'error': 'Acesso restrito a administradores master'}), 403

        return f(*args, **kwargs)
    return decorated_function


def teacher_or_admin_required(f):
    """Decorator para verificar se o usuário é professor ou administrador"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401

        user = User.query.get(session['user_id'])
        if not user or user.role not in ['teacher', 'admin']:
            return jsonify({'error': 'Acesso restrito a professores e administradores'}), 403

        return f(*args, **kwargs)
    return decorated_function


def student_or_teacher_required(f):
    """Decorator para verificar se o usuário é estudante ou professor"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401

        user = User.query.get(session['user_id'])
        if not user or user.role not in ['student', 'teacher']:
            return jsonify({'error': 'Acesso restrito a estudantes e professores'}), 403

        return f(*args, **kwargs)
    return decorated_function


def any_user_required(f):
    """Decorator para qualquer usuário logado (student, teacher ou admin)"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401

        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': 'Usuário não encontrado'}), 401

        return f(*args, **kwargs)
    return decorated_function