# src/routes/student_routes.py
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.academic import Student, Enrollment, Discipline
from functools import wraps

student_bp = Blueprint('student', __name__)

# ========== DECORATORS ==========

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function

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

# ========== FUNÇÃO AUXILIAR ==========

def enroll_student_in_all_disciplines_of_year(student_id, ano_turma):
    """Auto-matrícula do estudante em todas as disciplinas do mesmo ano/turma"""
    if not ano_turma:
        return
    disciplines = Discipline.query.filter_by(ano_turma=ano_turma).all()
    for disc in disciplines:
        existing = Enrollment.query.filter_by(
            student_id=student_id,
            discipline_id=disc.id,
            status='active'
        ).first()
        if not existing:
            enrollment = Enrollment(
                student_id=student_id,
                discipline_id=disc.id,
                status='active'
            )
            db.session.add(enrollment)
    db.session.commit()

# ========== ROTAS PÚBLICAS (para o próprio usuário) ==========

@student_bp.route('/students/me', methods=['GET'])
@login_required
def get_my_student_profile():
    """Obter perfil do estudante logado"""
    try:
        user_id = session.get('user_id')
        student = Student.query.filter_by(user_id=user_id).first()

        if not student:
            return jsonify({
                'success': False,
                'error': 'Perfil de estudante não encontrado'
            }), 404

        return jsonify({
            'success': True,
            'student': student.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ========== ROTAS ADMIN ==========

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
                'nivel_ensino': s.nivel_ensino,
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
        if not data.get('nome') or not data.get('cpf') or not data.get('matricula') or not data.get('curso'):
            return jsonify({'success': False, 'error': 'Campos obrigatórios faltando'}), 400

        # Verificar duplicatas
        if Student.query.filter_by(matricula=data['matricula']).first():
            return jsonify({'success': False, 'error': 'Matrícula já existe'}), 400
        if Student.query.filter_by(cpf=data['cpf']).first():
            return jsonify({'success': False, 'error': 'CPF já existe'}), 400
        if User.query.filter_by(username=data['cpf']).first():
            return jsonify({'success': False, 'error': 'Usuário já existe'}), 400

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

        # Auto-matrícula
        enroll_student_in_all_disciplines_of_year(student.id, student.ano_turma)

        return jsonify({
            'success': True,
            'message': 'Aluno criado com sucesso',
            'student': {
                'id': student.id,
                'nome': student.nome,
                'matricula': student.matricula,
                'curso': student.curso,
                'cpf': student.cpf,
                'ano_turma': student.ano_turma,
                'nivel_ensino': student.nivel_ensino,
                'user_id': student.user_id,
                'username': user.username
            }
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@student_bp.route('/students/<int:student_id>', methods=['PUT'])
@admin_required
def update_student(student_id):
    """Atualizar dados de um estudante"""
    try:
        data = request.json
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Estudante não encontrado'}), 404

        # Atualizar campos
        if 'nome' in data:
            student.nome = data['nome']
        if 'matricula' in data:
            existing = Student.query.filter_by(matricula=data['matricula']).first()
            if existing and existing.id != student_id:
                return jsonify({'success': False, 'error': 'Matrícula já existe'}), 400
            student.matricula = data['matricula']
        if 'curso' in data:
            student.curso = data['curso']
        if 'ano_turma' in data:
            student.ano_turma = data['ano_turma']
        if 'nivel_ensino' in data:
            student.nivel_ensino = data['nivel_ensino']
        if 'cpf' in data:
            existing = Student.query.filter_by(cpf=data['cpf']).first()
            if existing and existing.id != student_id:
                return jsonify({'success': False, 'error': 'CPF já existe'}), 400
            student.cpf = data['cpf']
            # Atualizar username do usuário associado
            user = User.query.get(student.user_id)
            if user:
                user.username = data['cpf']

        db.session.commit()

        user = User.query.get(student.user_id)

        return jsonify({
            'success': True,
            'message': 'Estudante atualizado com sucesso',
            'student': {
                'id': student.id,
                'nome': student.nome,
                'matricula': student.matricula,
                'curso': student.curso,
                'cpf': student.cpf,
                'ano_turma': student.ano_turma,
                'nivel_ensino': student.nivel_ensino,
                'user_id': student.user_id,
                'username': user.username if user else None
            }
        })
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