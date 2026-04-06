# src/routes/admin_routes.py
"""
Routes para Administração de Usuários - Controllers HTTP
Gerencia alunos e professores no painel administrativo
"""

from functools import wraps
from flask import Blueprint, jsonify, request, session
from src.models.user import db, User
from src.models.academic import Student, Professor, Enrollment, Discipline

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


# ============================================================================
# DECORATORS
# ============================================================================

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário', 'success': False}), 401

        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': 'Acesso restrito a administradores', 'success': False}), 403

        return f(*args, **kwargs)
    return decorated_function


# ============================================================================
# FUNÇÕES AUXILIARES PARA MATRÍCULAS AUTOMÁTICAS
# ============================================================================

def enroll_student_in_all_disciplines_of_year(student_id, ano_turma):
    """Matricula o aluno em todas as disciplinas do mesmo ano/turma"""
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


def sync_student_enrollments(student_id, old_ano_turma, new_ano_turma):
    """Sincroniza matrículas do aluno conforme mudança de ano/turma"""
    if old_ano_turma == new_ano_turma:
        return

    # Remove matrículas em disciplinas do antigo ano/turma
    if old_ano_turma:
        old_disciplines = Discipline.query.filter_by(ano_turma=old_ano_turma).all()
        for disc in old_disciplines:
            Enrollment.query.filter_by(
                student_id=student_id,
                discipline_id=disc.id
            ).delete()

    # Adiciona matrículas nas disciplinas do novo ano/turma
    if new_ano_turma:
        new_disciplines = Discipline.query.filter_by(ano_turma=new_ano_turma).all()
        for disc in new_disciplines:
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


# ============================================================================
# GESTÃO DE ALUNOS
# ============================================================================

@admin_bp.route('/students', methods=['GET'])
@admin_required
def get_all_students():
    """Listar todos os alunos com seus dados"""
    try:
        students = Student.query.all()
        result = []

        for student in students:
            user = User.query.get(student.user_id)
            result.append({
                'id': student.id,
                'user_id': student.user_id,
                'matricula': student.matricula,
                'nome': student.nome,
                'curso': student.curso,
                'cpf': student.cpf,
                'ano_turma': student.ano_turma,
                'nivel_ensino': student.nivel_ensino,
                'username': user.username if user else None,
                'xp': user.current_xp if user else 0,
                'level': user.current_level if user else 1,
                'coins': user.coins if user else 0,
                'created_at': student.created_at.isoformat() if student.created_at else None
            })

        return jsonify({'success': True, 'students': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/students', methods=['POST'])
@admin_required
def create_student():
    """Criar novo aluno com conta de usuário"""
    try:
        data = request.json

        # Validações
        if not data.get('nome'):
            return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
        if not data.get('cpf'):
            return jsonify({'success': False, 'error': 'CPF é obrigatório'}), 400
        if not data.get('matricula'):
            return jsonify({'success': False, 'error': 'Matrícula é obrigatória'}), 400
        if not data.get('curso'):
            return jsonify({'success': False, 'error': 'Curso é obrigatório'}), 400

        # Verificar CPF duplicado
        if Student.query.filter_by(cpf=data['cpf']).first():
            return jsonify({'success': False, 'error': 'CPF já cadastrado'}), 400

        # Verificar matrícula duplicada
        if Student.query.filter_by(matricula=data['matricula']).first():
            return jsonify({'success': False, 'error': 'Matrícula já cadastrada'}), 400

        # Verificar username duplicado
        if User.query.filter_by(username=data['cpf']).first():
            return jsonify({'success': False, 'error': 'Usuário já existe'}), 400

        # Criar usuário
        user = User(
            username=data['cpf'],
            role='student',
            current_xp=0,
            current_level=1,
            coins=100
        )
        user.set_password(data.get('password', 'aluno123'))
        db.session.add(user)
        db.session.flush()

        # Criar perfil de estudante
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

        # Auto‑matrícula nas disciplinas do ano/turma
        enroll_student_in_all_disciplines_of_year(student.id, student.ano_turma)

        return jsonify({
            'success': True,
            'message': 'Aluno criado com sucesso!',
            'student': {
                'id': student.id,
                'nome': student.nome,
                'matricula': student.matricula,
                'username': user.username,
                'password': data.get('password', 'aluno123')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/students/<int:student_id>', methods=['PUT'])
@admin_required
def update_student(student_id):
    """Atualizar dados do aluno e sincronizar matrículas se o ano/turma mudar"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Aluno não encontrado'}), 404

        data = request.json
        old_ano = student.ano_turma  # guardar antes da alteração

        if 'nome' in data:
            student.nome = data['nome']
        if 'curso' in data:
            student.curso = data['curso']
        if 'ano_turma' in data:
            student.ano_turma = data['ano_turma']
        if 'nivel_ensino' in data:
            student.nivel_ensino = data['nivel_ensino']

        db.session.commit()

        # Sincronizar matrículas se o ano/turma foi alterado
        if 'ano_turma' in data:
            sync_student_enrollments(student.id, old_ano, student.ano_turma)

        return jsonify({'success': True, 'message': 'Aluno atualizado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/students/<int:student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    """Excluir aluno"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({'success': False, 'error': 'Aluno não encontrado'}), 404

        user = User.query.get(student.user_id)

        # Excluir matrículas primeiro
        Enrollment.query.filter_by(student_id=student.id).delete()

        db.session.delete(student)
        if user:
            db.session.delete(user)

        db.session.commit()

        return jsonify({'success': True, 'message': 'Aluno excluído com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# GESTÃO DE PROFESSORES
# ============================================================================

@admin_bp.route('/professors', methods=['GET'])
@admin_required
def get_all_professors():
    """Listar todos os professores"""
    try:
        professors = Professor.query.all()
        result = []

        for professor in professors:
            user = User.query.get(professor.user_id)
            result.append({
                'id': professor.id,
                'user_id': professor.user_id,
                'nome': professor.nome,
                'cpf': professor.cpf,
                'departamento': professor.departamento,
                'anos_turmas': professor.anos_turmas,
                'niveis_ensino': professor.niveis_ensino,
                'username': user.username if user else None,
                'xp': user.current_xp if user else 0,
                'level': user.current_level if user else 1,
                'coins': user.coins if user else 0,
                'created_at': professor.created_at.isoformat() if professor.created_at else None
            })

        return jsonify({'success': True, 'professors': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/professors', methods=['POST'])
@admin_required
def create_professor():
    """Criar novo professor com conta de usuário"""
    try:
        data = request.json

        # Validações
        if not data.get('nome'):
            return jsonify({'success': False, 'error': 'Nome é obrigatório'}), 400
        if not data.get('cpf'):
            return jsonify({'success': False, 'error': 'CPF é obrigatório'}), 400
        if not data.get('departamento'):
            return jsonify({'success': False, 'error': 'Departamento é obrigatório'}), 400

        # Verificar CPF duplicado
        if Professor.query.filter_by(cpf=data['cpf']).first():
            return jsonify({'success': False, 'error': 'CPF já cadastrado'}), 400

        # Verificar username duplicado
        if User.query.filter_by(username=data['cpf']).first():
            return jsonify({'success': False, 'error': 'Usuário já existe'}), 400

        # Criar usuário
        user = User(
            username=data['cpf'],
            role='teacher',
            current_xp=0,
            current_level=1,
            coins=500
        )
        user.set_password(data.get('password', 'prof123'))
        db.session.add(user)
        db.session.flush()

        # Criar perfil de professor
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
            'message': 'Professor criado com sucesso!',
            'professor': {
                'id': professor.id,
                'nome': professor.nome,
                'username': user.username,
                'password': data.get('password', 'prof123')
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/professors/<int:professor_id>', methods=['PUT'])
@admin_required
def update_professor(professor_id):
    """Atualizar dados do professor"""
    try:
        professor = Professor.query.get(professor_id)
        if not professor:
            return jsonify({'success': False, 'error': 'Professor não encontrado'}), 404

        data = request.json

        if 'nome' in data:
            professor.nome = data['nome']
        if 'departamento' in data:
            professor.departamento = data['departamento']
        if 'anos_turmas' in data:
            professor.anos_turmas = data['anos_turmas']
        if 'niveis_ensino' in data:
            professor.niveis_ensino = data['niveis_ensino']

        db.session.commit()

        return jsonify({'success': True, 'message': 'Professor atualizado com sucesso'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/professors/<int:professor_id>', methods=['DELETE'])
@admin_required
def delete_professor(professor_id):
    """Excluir professor"""
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


# ============================================================================
# LISTAR DISCIPLINAS PARA FORMULÁRIOS
# ============================================================================

@admin_bp.route('/disciplines/list', methods=['GET'])
@admin_required
def get_disciplines_list():
    """Listar disciplinas para uso em selects"""
    try:
        disciplines = Discipline.query.all()
        result = [{'id': d.id, 'nome': d.nome, 'codigo': d.codigo} for d in disciplines]
        return jsonify({'success': True, 'disciplines': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@admin_bp.route('/students/<int:student_id>/enrollments', methods=['GET'])
@admin_required
def get_student_enrollments(student_id):
    """Listar matrículas de um aluno"""
    try:
        enrollments = Enrollment.query.filter_by(student_id=student_id).all()
        result = []

        for e in enrollments:
            discipline = Discipline.query.get(e.discipline_id)
            result.append({
                'id': e.id,
                'discipline_id': e.discipline_id,
                'discipline_nome': discipline.nome if discipline else 'N/A',
                'status': e.status,
                'enrollment_date': e.enrollment_date.isoformat() if e.enrollment_date else None
            })

        return jsonify({'success': True, 'enrollments': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500