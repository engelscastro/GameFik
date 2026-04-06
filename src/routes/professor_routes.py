# src/routes/professor_routes.py
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.academic import Professor, Discipline
from functools import wraps

professor_bp = Blueprint('professor', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Acesso restrito a administradores'}), 403
        return f(*args, **kwargs)
    return decorated_function

@professor_bp.route('/professors', methods=['GET'])
@admin_required
def get_all_professors():
    try:
        professors = Professor.query.all()
        result = []
        for p in professors:
            user = User.query.get(p.user_id)
            result.append({
                'id': p.id,
                'nome': p.nome,
                'cpf': p.cpf,
                'departamento': p.departamento,
                'user_id': p.user_id,
                'username': user.username if user else None
            })
        return jsonify({'success': True, 'professors': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@professor_bp.route('/professors', methods=['POST'])
@admin_required
def create_professor():
    try:
        data = request.json
        # Validações básicas
        if not data.get('nome') or not data.get('cpf') or not data.get('departamento'):
            return jsonify({'success': False, 'error': 'Campos obrigatórios faltando'}), 400

        # Criar usuário
        user = User(username=data['cpf'], role='teacher')
        user.set_password(data.get('password', 'prof123'))
        db.session.add(user)
        db.session.flush()

        # Criar professor
        professor = Professor(
            user_id=user.id,
            nome=data['nome'],
            cpf=data['cpf'],
            departamento=data['departamento'],
            anos_turmas=data.get('anos_turmas'),
            niveis_ensino=data.get('niveis_ensino')
        )
        db.session.add(professor)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Professor criado com sucesso',
            'professor': {'id': professor.id, 'nome': professor.nome}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@professor_bp.route('/professors/<int:professor_id>', methods=['DELETE'])
@admin_required
def delete_professor(professor_id):
    try:
        professor = Professor.query.get(professor_id)
        if not professor:
            return jsonify({'success': False, 'error': 'Professor não encontrado'}), 404

        user = User.query.get(professor.user_id)
        db.session.delete(professor)
        if user:
            db.session.delete(user)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Professor excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500