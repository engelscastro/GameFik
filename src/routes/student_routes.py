# src/routes/student_routes.py
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.academic import Student
from functools import wraps

student_bp = Blueprint('student', __name__)

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

@student_bp.route('/students', methods=['GET'])
@admin_required
def get_all_students():
    try:
        students = Student.query.all()
        result = []
        for s in students:
            user = User.query.get(s.user_id)
            result.append({
                'id': s.id,
                'nome': s.nome,
                'matricula': s.matricula,
                'curso': s.curso,
                'cpf': s.cpf,
                'ano_turma': s.ano_turma,
                'user_id': s.user_id,
                'username': user.username if user else None
            })
        return jsonify({'success': True, 'students': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@student_bp.route('/students', methods=['POST'])
@admin_required
def create_student():
    try:
        data = request.json
        # Validações básicas
        if not data.get('nome') or not data.get('cpf') or not data.get('matricula') or not data.get('curso'):
            return jsonify({'success': False, 'error': 'Campos obrigatórios faltando'}), 400

        # Criar usuário
        user = User(username=data['cpf'], role='student')
        user.set_password(data.get('password', 'aluno123'))
        db.session.add(user)
        db.session.flush()

        # Criar estudante
        student = Student(
            user_id=user.id,
            matricula=data['matricula'],
            nome=data['nome'],
            curso=data['curso'],
            cpf=data['cpf'],
            ano_turma=data.get('ano_turma'),
            nivel_ensino=data.get('nivel_ensino', 'Superior')
        )
        db.session.add(student)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Aluno criado com sucesso',
            'student': {'id': student.id, 'nome': student.nome, 'matricula': student.matricula}
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@student_bp.route('/students/<int:student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Aluno não encontrado'}), 404

        user = User.query.get(student.user_id)
        db.session.delete(student)
        if user:
            db.session.delete(user)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Aluno excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500