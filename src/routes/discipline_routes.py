# src/routes/discipline_routes.py
"""
Routes para Disciplinas - Controllers HTTP
"""

from functools import wraps
from flask import Blueprint, jsonify, request, session
from src.models.user import db, User
from src.models.academic import Discipline, Professor, Enrollment, AcademicMission, Student

discipline_bp = Blueprint('discipline', __name__)


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
# LISTAR DISCIPLINAS
# ============================================================================

@discipline_bp.route('/disciplines', methods=['GET'])
@login_required
def get_disciplines():
    """Listar disciplinas - admin vê todas, aluno vê apenas as da sua turma"""
    try:
        user = User.query.get(session['user_id'])

        # Se for admin, retorna todas as disciplinas
        if user.role == 'admin':
            disciplines = Discipline.query.all()
        # Se for aluno, filtra por ano_turma
        elif user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if not student or not student.ano_turma:
                # Aluno sem turma definida não vê nenhuma disciplina
                return jsonify({'success': True, 'disciplines': []}), 200
            disciplines = Discipline.query.filter_by(ano_turma=student.ano_turma).all()
        else:
            # Para professores (ou outros), retorna todas (professor tem rota específica)
            disciplines = Discipline.query.all()

        result = []
        for d in disciplines:
            professor_nome = None
            if d.professor_id:
                professor = Professor.query.get(d.professor_id)
                if professor:
                    professor_nome = professor.nome
            result.append({
                'id': d.id,
                'codigo': d.codigo,
                'nome': d.nome,
                'carga_horaria': d.carga_horaria,
                'professor_id': d.professor_id,
                'professor_nome': professor_nome,
                'ano_turma': d.ano_turma,
                'nivel_ensino': d.nivel_ensino,
                'created_at': d.created_at.isoformat() if d.created_at else None
            })

        return jsonify({'success': True, 'disciplines': result}), 200
    except Exception as e:
        print(f"❌ Erro em get_disciplines: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@discipline_bp.route('/disciplines-with-professors', methods=['GET'])
@login_required
def get_disciplines_with_professors():
    """Listar disciplinas com informações dos professores"""
    try:
        disciplines = Discipline.query.all()
        result = []

        for d in disciplines:
            professor_nome = None
            if d.professor_id:
                professor = Professor.query.get(d.professor_id)
                if professor:
                    professor_nome = professor.nome

            result.append({
                'id': d.id,
                'codigo': d.codigo,
                'nome': d.nome,
                'carga_horaria': d.carga_horaria,
                'professor_id': d.professor_id,
                'professor_nome': professor_nome,
                'ano_turma': getattr(d, 'ano_turma', None),
                'nivel_ensino': getattr(d, 'nivel_ensino', None),
                'created_at': d.created_at.isoformat() if d.created_at else None
            })

        return jsonify({'success': True, 'disciplines': result}), 200
    except Exception as e:
        print(f"❌ Erro em get_disciplines_with_professors: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@discipline_bp.route('/disciplines/available', methods=['GET'])
@login_required
def get_available_disciplines():
    """Listar disciplinas disponíveis para aluno"""
    try:
        from src.models.academic import Student

        student = Student.query.filter_by(user_id=session['user_id']).first()
        if not student:
            return jsonify({'success': False, 'error': 'Perfil de estudante não encontrado'}), 404

        available_disciplines = Discipline.query.filter(
            Discipline.ano_turma == student.ano_turma
        ).all()

        current_enrollments = Enrollment.query.filter_by(
            student_id=student.id, status='active'
        ).all()

        enrolled_ids = [e.discipline_id for e in current_enrollments]

        filtered = [d for d in available_disciplines if d.id not in enrolled_ids]

        result = []
        for d in filtered:
            professor_nome = None
            if d.professor_id:
                professor = Professor.query.get(d.professor_id)
                if professor:
                    professor_nome = professor.nome

            result.append({
                'id': d.id,
                'codigo': d.codigo,
                'nome': d.nome,
                'carga_horaria': d.carga_horaria,
                'professor_id': d.professor_id,
                'professor_nome': professor_nome,
                'ano_turma': d.ano_turma,
                'nivel_ensino': d.nivel_ensino
            })

        return jsonify({'success': True, 'disciplines': result}), 200
    except Exception as e:
        print(f"❌ Erro em get_available_disciplines: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@discipline_bp.route('/disciplines/<int:discipline_id>', methods=['GET'])
@login_required
def get_discipline_details(discipline_id):
    """Obter detalhes de uma disciplina"""
    try:
        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({'error': 'Disciplina não encontrada', 'success': False}), 404

        professor_nome = None
        if discipline.professor_id:
            professor = Professor.query.get(discipline.professor_id)
            if professor:
                professor_nome = professor.nome

        return jsonify({
            'success': True,
            'discipline': {
                'id': discipline.id,
                'codigo': discipline.codigo,
                'nome': discipline.nome,
                'carga_horaria': discipline.carga_horaria,
                'professor_id': discipline.professor_id,
                'professor_nome': professor_nome,
                'ano_turma': discipline.ano_turma,
                'nivel_ensino': discipline.nivel_ensino,
                'created_at': discipline.created_at.isoformat() if discipline.created_at else None
            }
        }), 200
    except Exception as e:
        print(f"❌ Erro em get_discipline_details: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@discipline_bp.route('/disciplines/<int:discipline_id>/can-delete', methods=['GET'])
@login_required
def can_delete_discipline(discipline_id):
    """Verificar se disciplina pode ser deletada"""
    try:
        enrollment_count = Enrollment.query.filter_by(
            discipline_id=discipline_id
        ).count()

        can_delete = enrollment_count == 0
        return jsonify({
            'success': True,
            'can_delete': can_delete,
            'enrollment_count': enrollment_count
        }), 200
    except Exception as e:
        return jsonify({'error': str(e), 'success': False}), 500


@discipline_bp.route('/teacher/disciplines', methods=['GET'])
@login_required
def get_teacher_disciplines():
    user_id = session.get('user_id')
    print(f"🔍 [teacher/disciplines] user_id = {user_id}")

    professor = Professor.query.filter_by(user_id=user_id).first()
    if not professor:
        print("❌ Perfil não encontrado")
        return jsonify({'success': False, 'error': 'Perfil de professor não encontrado'}), 404

    print(f"✅ Perfil ID = {professor.id}")

    disciplinas = Discipline.query.filter_by(professor_id=professor.id).all()
    print(f"📚 Disciplinas encontradas: {[d.nome for d in disciplinas]}")

    result = []
    for d in disciplinas:
        result.append({
            'id': d.id,
            'codigo': d.codigo,
            'nome': d.nome,
            'carga_horaria': d.carga_horaria,
            'ano_turma': d.ano_turma,
            'nivel_ensino': d.nivel_ensino,
            'student_count': Enrollment.query.filter_by(discipline_id=d.id, status='active').count()
        })

    print(f"📤 Resultado JSON: {result}")
    return jsonify({'success': True, 'disciplines': result})


# ============================================================================
# CRIAR DISCIPLINA
# ============================================================================

@discipline_bp.route('/disciplines', methods=['POST'])
@teacher_or_admin_required
def create_discipline():
    """Criar nova disciplina"""
    try:
        data = request.json
        print(f"📥 Dados recebidos: {data}")

        # Validação
        if not data.get('codigo'):
            return jsonify({'success': False, 'error': 'Código da disciplina é obrigatório'}), 400

        if not data.get('nome'):
            return jsonify({'success': False, 'error': 'Nome da disciplina é obrigatório'}), 400

        if not data.get('carga_horaria'):
            return jsonify({'success': False, 'error': 'Carga horária é obrigatória'}), 400

        # Verificar se código já existe
        existing = Discipline.query.filter_by(codigo=data['codigo']).first()
        if existing:
            return jsonify({'success': False, 'error': 'Já existe uma disciplina com este código'}), 400

        # Criar disciplina
        discipline = Discipline(
            codigo=data['codigo'],
            nome=data['nome'],
            carga_horaria=data['carga_horaria'],
            professor_id=data.get('professor_id'),
            ano_turma=data.get('ano_turma'),
            nivel_ensino=data.get('nivel_ensino')
        )

        db.session.add(discipline)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Disciplina criada com sucesso!',
            'discipline': {
                'id': discipline.id,
                'codigo': discipline.codigo,
                'nome': discipline.nome,
                'carga_horaria': discipline.carga_horaria,
                'professor_id': discipline.professor_id,
                'ano_turma': discipline.ano_turma,
                'nivel_ensino': discipline.nivel_ensino
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar disciplina: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ATUALIZAR DISCIPLINA
# ============================================================================

@discipline_bp.route('/disciplines/<int:discipline_id>', methods=['PUT'])
@teacher_or_admin_required
def update_discipline(discipline_id):
    """Atualizar disciplina"""
    try:
        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({'success': False, 'error': 'Disciplina não encontrada'}), 404

        data = request.json

        if 'codigo' in data:
            # Verificar se novo código já existe
            existing = Discipline.query.filter_by(codigo=data['codigo']).first()
            if existing and existing.id != discipline_id:
                return jsonify({'success': False, 'error': 'Já existe uma disciplina com este código'}), 400
            discipline.codigo = data['codigo']

        if 'nome' in data:
            discipline.nome = data['nome']

        if 'carga_horaria' in data:
            discipline.carga_horaria = data['carga_horaria']

        if 'professor_id' in data:
            discipline.professor_id = data['professor_id']

        if 'ano_turma' in data:
            discipline.ano_turma = data['ano_turma']

        if 'nivel_ensino' in data:
            discipline.nivel_ensino = data['nivel_ensino']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Disciplina atualizada com sucesso!',
            'discipline': {
                'id': discipline.id,
                'codigo': discipline.codigo,
                'nome': discipline.nome,
                'carga_horaria': discipline.carga_horaria,
                'professor_id': discipline.professor_id,
                'ano_turma': discipline.ano_turma,
                'nivel_ensino': discipline.nivel_ensino
            }
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao atualizar disciplina: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# DELETAR DISCIPLINA
# ============================================================================

@discipline_bp.route('/disciplines/<int:discipline_id>', methods=['DELETE'])
@teacher_or_admin_required
def delete_discipline(discipline_id):
    """Deletar disciplina"""
    try:
        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({'success': False, 'error': 'Disciplina não encontrada'}), 404

        # Verificar se há matrículas ativas
        active_enrollments = Enrollment.query.filter_by(
            discipline_id=discipline_id, status='active'
        ).count()

        if active_enrollments > 0:
            return jsonify({
                'success': False,
                'error': f'Não é possível excluir disciplina com {active_enrollments} matrícula(s) ativa(s)'
            }), 400

        # Verificar se há missões acadêmicas
        academic_missions = AcademicMission.query.filter_by(discipline_id=discipline_id).count()
        if academic_missions > 0:
            # Excluir missões acadêmicas vinculadas
            AcademicMission.query.filter_by(discipline_id=discipline_id).delete()

        db.session.delete(discipline)
        db.session.commit()

        return jsonify({'success': True, 'message': 'Disciplina excluída com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao excluir disciplina: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# PROFESSOR - Atribuição
# ============================================================================

@discipline_bp.route('/disciplines/<int:discipline_id>/assign-professor', methods=['POST'])
@teacher_or_admin_required
def assign_professor_to_discipline(discipline_id):
    """Atribuir professor a uma disciplina"""
    try:
        data = request.json
        professor_id = data.get('professor_id')

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({'success': False, 'error': 'Disciplina não encontrada'}), 404

        if professor_id:
            professor = Professor.query.get(professor_id)
            if not professor:
                return jsonify({'success': False, 'error': 'Professor não encontrado'}), 404

        discipline.professor_id = professor_id
        db.session.commit()

        action = "atribuído" if professor_id else "removido"
        return jsonify({'success': True, 'message': f'Professor {action} com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ALUNO - Matrícula
# ============================================================================

@discipline_bp.route('/enrollments', methods=['POST'])
@login_required
def create_enrollment():
    """Matricular aluno em disciplina"""
    try:
        from src.models.academic import Student

        data = request.json
        discipline_id = data.get('discipline_id')

        if not discipline_id:
            return jsonify({'error': 'discipline_id é obrigatório', 'success': False}), 400

        student = Student.query.filter_by(user_id=session['user_id']).first()
        if not student:
            return jsonify({'error': 'Perfil de estudante não encontrado', 'success': False}), 404

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({'error': 'Disciplina não encontrada', 'success': False}), 404

        # Verificar se já está matriculado
        existing = Enrollment.query.filter_by(
            student_id=student.id, discipline_id=discipline_id, status='active'
        ).first()

        if existing:
            return jsonify({'error': 'Aluno já matriculado nesta disciplina', 'success': False}), 400

        # Criar matrícula
        enrollment = Enrollment(
            student_id=student.id,
            discipline_id=discipline_id,
            status='active'
        )

        db.session.add(enrollment)
        db.session.commit()

        # Adicionar XP
        student_user = User.query.get(student.user_id)
        xp_reward = 10
        if student_user:
            student_user.add_xp(xp_reward)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Matrícula realizada com sucesso! +{xp_reward} XP',
            'enrollment': {
                'id': enrollment.id,
                'student_id': enrollment.student_id,
                'discipline_id': enrollment.discipline_id,
                'status': enrollment.status,
                'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao criar matrícula: {e}")
        return jsonify({'error': str(e), 'success': False}), 500


@discipline_bp.route('/enrollments/<int:enrollment_id>', methods=['DELETE'])
@login_required
def cancel_enrollment(enrollment_id):
    """Cancelar matrícula de aluno"""
    try:
        enrollment = Enrollment.query.get(enrollment_id)
        if not enrollment:
            return jsonify({'error': 'Matrícula não encontrada', 'success': False}), 404

        enrollment.status = 'cancelled'
        db.session.commit()

        return jsonify({'success': True, 'message': 'Matrícula cancelada com sucesso'}), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500


@discipline_bp.route('/enrollments/bulk', methods=['POST'])
@teacher_or_admin_required
def bulk_enrollment():
    """Matricular múltiplos alunos em uma disciplina"""
    try:
        from src.models.academic import Student

        data = request.json
        discipline_id = data.get('discipline_id')
        student_ids = data.get('student_ids', [])

        if not discipline_id:
            return jsonify({'error': 'discipline_id é obrigatório', 'success': False}), 400

        if not student_ids:
            return jsonify({'error': 'student_ids é obrigatório', 'success': False}), 400

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({'error': 'Disciplina não encontrada', 'success': False}), 404

        success_count = 0
        error_count = 0

        for student_id in student_ids:
            try:
                existing = Enrollment.query.filter_by(
                    student_id=student_id, discipline_id=discipline_id, status='active'
                ).first()

                if not existing:
                    enrollment = Enrollment(
                        student_id=student_id,
                        discipline_id=discipline_id,
                        status='active'
                    )
                    db.session.add(enrollment)
                    success_count += 1
            except Exception as e:
                error_count += 1
                print(f"Erro ao matricular estudante {student_id}: {e}")

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Matrícula em lote concluída: {success_count} sucesso(s), {error_count} erro(s)',
            'success_count': success_count,
            'error_count': error_count
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e), 'success': False}), 500

# ============================================================================
# PROFESSOR - VER ALUNOS DA DISCIPLINA
# ============================================================================

@discipline_bp.route('/teacher/my-disciplines/<int:discipline_id>/students', methods=['GET'])
@teacher_or_admin_required
def get_teacher_discipline_students(discipline_id):
    """Listar alunos de uma disciplina específica do professor"""
    try:
        from src.models.academic import Student, Enrollment

        user_id = session['user_id']

        # Verificar se o professor é o responsável pela disciplina
        professor = Professor.query.filter_by(user_id=user_id).first()
        if not professor:
            return jsonify({'success': False, 'error': 'Perfil de professor não encontrado'}), 404

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({'success': False, 'error': 'Disciplina não encontrada'}), 404

        # Verificar se a disciplina pertence ao professor
        if discipline.professor_id != professor.id:
            return jsonify({'success': False, 'error': 'Esta disciplina não pertence a você'}), 403

        # Buscar alunos matriculados
        enrollments = Enrollment.query.filter_by(
            discipline_id=discipline_id, status='active'
        ).all()

        students = []
        for e in enrollments:
            student = Student.query.get(e.student_id)
            if student:
                user = User.query.get(student.user_id)
                students.append({
                    'id': student.id,
                    'nome': student.nome,
                    'matricula': student.matricula,
                    'curso': student.curso,
                    'ano_turma': student.ano_turma,
                    'username': user.username if user else None,
                    'xp': user.current_xp if user else 0,
                    'level': user.current_level if user else 1
                })

        return jsonify({
            'success': True,
            'students': students,
            'discipline': discipline.nome,
            'discipline_name': discipline.nome,
            'total_students': len(students)
        }), 200

    except Exception as e:
        print(f"❌ Erro em get_teacher_discipline_students: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

    # ============================================================================
# PROFESSOR - ESTATÍSTICAS
# ============================================================================

@discipline_bp.route('/teacher/stats', methods=['GET'])
@teacher_or_admin_required
def get_teacher_stats():
    """Obter estatísticas do professor"""
    try:
        user_id = session['user_id']

        professor = Professor.query.filter_by(user_id=user_id).first()
        if not professor:
            return jsonify({'success': False, 'error': 'Perfil de professor não encontrado'}), 404

        # Buscar disciplinas do professor
        disciplines = Discipline.query.filter_by(professor_id=professor.id).all()

        total_disciplines = len(disciplines)
        total_students = 0
        total_missions = 0
        total_xp_awarded = 0

        for d in disciplines:
            # Contar alunos
            student_count = Enrollment.query.filter_by(
                discipline_id=d.id, status='active'
            ).count()
            total_students += student_count

            # Contar missões (usando AcademicMission se existir)
            try:
                from src.models.academic import AcademicMission
                mission_count = AcademicMission.query.filter_by(
                    discipline_id=d.id
                ).count()
                total_missions += mission_count
            except:
                pass

        return jsonify({
            'success': True,
            'total_disciplines': total_disciplines,
            'total_students': total_students,
            'total_missions': total_missions,
            'total_xp_awarded': total_xp_awarded
        }), 200

    except Exception as e:
        print(f"❌ Erro em get_teacher_stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

    # src/routes/discipline_routes.py
from src.models.academic import Student, Enrollment

def enroll_all_students_of_year(discipline_id, ano_turma):
    if not ano_turma:
        return
    students = Student.query.filter_by(ano_turma=ano_turma).all()
    for student in students:
        existing = Enrollment.query.filter_by(
            student_id=student.id,
            discipline_id=discipline_id,
            status='active'
        ).first()
        if not existing:
            enrollment = Enrollment(
                student_id=student.id,
                discipline_id=discipline_id,
                status='active'
            )
            db.session.add(enrollment)
    db.session.commit()

    # Dentro de create_discipline, após salvar a disciplina:
    db.session.add(discipline)
    db.session.commit()
    enroll_all_students_of_year(discipline.id, discipline.ano_turma)

    # Dentro de update_discipline, se ano_turma for alterado:
    old_ano = discipline.ano_turma
    if 'ano_turma' in data:
        discipline.ano_turma = data['ano_turma']
        # Você pode optar por remover matrículas antigas? (complexo, mas pode manter)
        # Apenas adiciona novos alunos:
        enroll_all_students_of_year(discipline.id, discipline.ano_turma)