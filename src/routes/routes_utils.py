# src/routes/utils.py
"""
Utilitários para rotas - Decorators e funções auxiliares
Decorators para autenticação e autorização usados por todos os blueprints
"""

from functools import wraps
from flask import session, jsonify


# ============================================================================
# DECORATORS DE AUTENTICAÇÃO
# ============================================================================

def login_required(f):
    """
    Decorator que valida se o usuário está logado
    Verifica se 'user_id' existe na sessão
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário', 'success': False}), 401
        return f(*args, **kwargs)
    return decorated_function


def teacher_or_admin_required(f):
    """
    Decorator que valida se o usuário é professor ou admin
    Requer login + role == 'teacher' ou 'admin'
    """
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


def admin_required(f):
    """
    Decorator que valida se o usuário é admin
    Requer login + role == 'admin'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário', 'success': False}), 401
        
        from src.models.user import User
        user = User.query.get(session['user_id'])
        
        if not user or user.role != 'admin':
            return jsonify({
                'error': 'Acesso restrito a administradores',
                'success': False
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def teacher_required(f):
    """
    Decorator que valida se o usuário é professor
    Requer login + role == 'teacher'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário', 'success': False}), 401
        
        from src.models.user import User
        user = User.query.get(session['user_id'])
        
        if not user or user.role != 'teacher':
            return jsonify({
                'error': 'Acesso restrito a professores',
                'success': False
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function


def student_required(f):
    """
    Decorator que valida se o usuário é estudante
    Requer login + role == 'student'
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário', 'success': False}), 401
        
        from src.models.user import User
        user = User.query.get(session['user_id'])
        
        if not user or user.role != 'student':
            return jsonify({
                'error': 'Acesso restrito a estudantes',
                'success': False
            }), 403
        
        return f(*args, **kwargs)
    return decorated_function
