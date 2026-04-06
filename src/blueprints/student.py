"""
Blueprint para gerenciamento de estudantes
Responsável por operações CRUD de estudantes, sincronização de estudantes
e listagem administrativa.
"""

from flask import Blueprint, request, jsonify, session
from sqlalchemy import and_
import random

from src.models.academic import Student, Enrollment
from src.models.user import db, User
from .utils import login_required, admin_required, teacher_or_admin_required

# Criar blueprint
student_bp = Blueprint('student', __name__)


# ========== ESTUDANTES - CRUD ==========

@student_bp.route('/students', methods=['POST'])
@admin_required
def create_student():
    """Criar estudante com conta de usuário"""
    try:
        data = request.json

        # Validação de campos obrigatórios
        required_fields = ['matricula', 'nome', 'curso', 'cpf']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400

        # Verificar matrícula única
        if Student.query.filter_by(matricula=data['matricula']).first():
            return jsonify({
                'success': False,
                'error': 'Já existe um estudante com esta matrícula'
            }), 400

        # Verificar CPF único
        if Student.query.filter_by(cpf=data['cpf']).first():
            return jsonify({
                'success': False,
                'error': 'Já existe um estudante com este CPF'
            }), 400

        # Verificar se usuário já existe
        if User.query.filter_by(username=data['cpf']).first():
            return jsonify({
                'success': False,
                'error': 'Já existe um usuário com este CPF'
            }), 400

        # Criar usuário
        user = User(username=data['cpf'], role='student')
        user.set_password('aluno123')  # Senha padrão
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
            nivel_ensino=data.get('nivel_ensino')
        )

        db.session.add(student)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Estudante cadastrado com sucesso!',
            'student': student.to_dict(),
            'login_info': {
                'username': data['cpf'],
                'password': 'aluno123',
                'role': 'student'
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao criar estudante: {str(e)}'
        }), 500


@student_bp.route('/students/<int:student_id>', methods=['DELETE'])
@admin_required
def delete_student(student_id):
    """Excluir estudante"""
    try:
        student = Student.query.get(student_id)
        if not student:
            return jsonify({
                'success': False,
                'error': 'Estudante não encontrado'
            }), 404

        # Verificar se tem matrículas ativas
        active_enrollments = Enrollment.query.filter_by(
            student_id=student_id,
            status='active'
        ).count()

        if active_enrollments > 0:
            return jsonify({
                'success': False,
                'error': f'Não é possível excluir estudante com {active_enrollments} matrícula(s) ativa(s)'
            }), 400

        user = student.user

        # Excluir estudante e usuário
        db.session.delete(student)
        db.session.delete(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Estudante excluído com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir estudante: {str(e)}'
        }), 500


# ========== LISTAGEM ADMINISTRATIVA ==========

@student_bp.route('/admin/students', methods=['GET'])
@teacher_or_admin_required
def get_all_students():
    """Lista todos os estudantes (admin)"""
    try:
        print("🔍 DEBUG: Iniciando get_all_students")

        students = Student.query.all()
        print(f"🔍 DEBUG: Encontrados {len(students)} estudantes")

        students_data = []
        for student in students:
            try:
                print(f"🔍 DEBUG: Processando estudante {student.id} - {student.nome}")

                # USAR to_dict() para garantir todos os campos
                student_dict = student.to_dict()

                # Adicionar informações extras se necessário
                student_dict['username'] = student_dict.get('cpf', 'N/A')  # CPF é o username

                students_data.append(student_dict)
                print(f"✅ DEBUG: Estudante {student.id} processado: {student.nome} - Mat: {student.matricula}")

            except Exception as e:
                print(f"❌ DEBUG: Erro ao processar estudante {student.id}: {e}")
                import traceback
                traceback.print_exc()

                # Fallback manual
                students_data.append({
                    'id': student.id,
                    'nome': getattr(student, 'nome', 'Erro'),
                    'matricula': getattr(student, 'matricula', 'N/A'),
                    'curso': getattr(student, 'curso', 'Erro'),
                    'ano_turma': getattr(student, 'ano_turma', None),
                    'cpf': getattr(student, 'cpf', 'Erro'),
                    'user_id': student.user_id,
                    'error': str(e)
                })

        print(f"🔍 DEBUG: Retornando {len(students_data)} estudantes")

        return jsonify({
            'success': True,
            'students': students_data
        })

    except Exception as e:
        print(f"❌ DEBUG: Erro geral em get_all_students: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500


# ========== SINCRONIZAÇÃO ==========

@student_bp.route('/sync-students', methods=['POST'])
def sync_students():
    """Sincroniza usuários estudantes que não têm perfil de Student"""
    try:
        students_without_profile = db.session.query(User).filter(
            and_(
                User.role == 'student',
                ~User.id.in_(db.session.query(Student.user_id))
            )
        ).all()

        synced = 0
        for user in students_without_profile:
            # Gerar matrícula única
            matricula = f"SYNC{user.id:06d}{random.randint(100,999)}"
            while Student.query.filter_by(matricula=matricula).first():
                matricula = f"SYNC{user.id:06d}{random.randint(100,999)}"

            cpf_ficticio = f"SYNCP{user.id:08d}"

            student = Student(
                user_id=user.id,
                matricula=matricula,
                nome=user.username,
                curso='Curso a definir - Sincronizado',
                ano_turma='Sincronizado',
                cpf=cpf_ficticio
            )

            db.session.add(student)
            synced += 1

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'{synced} estudantes sincronizados com sucesso!'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== ROTAS DE DEBUG ==========

@student_bp.route('/debug/students', methods=['GET'])
def debug_students():
    """Rota de debug para verificar estudantes"""
    try:
        students = Student.query.all()
        result = []

        for student in students:
            result.append({
                'id': student.id,
                'nome': student.nome,
                'matricula': student.matricula,
                'curso': student.curso,
                'ano_turma': student.ano_turma if hasattr(student, 'ano_turma') else None,
                'cpf': student.cpf,
                'user_id': student.user_id,
                'has_user': bool(User.query.get(student.user_id))
            })

        return jsonify({
            'success': True,
            'count': len(result),
            'students': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
