"""
Blueprint para gerenciamento de notas

Responsável por cadastro/atualização de notas, cálculo automático de média,
sistema de XP baseado em notas e listagem administrativa.
"""

from flask import Blueprint, request, jsonify, session

from src.models.academic import Grade, Student, Discipline
from src.models.user import db, User
from .utils import teacher_required, teacher_or_admin_required, login_required

# Criar blueprint
grade_bp = Blueprint('grade', __name__)

# ========== NOTAS - CRUD ==========

@grade_bp.route('/grades', methods=['POST'])
@teacher_required
def create_grade():
    """Cadastrar ou atualizar nota"""
    try:
        data = request.json

        # Validação de campos
        required_fields = ['student_id', 'discipline_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400

        # Verificar se estudante existe
        student = Student.query.get(data['student_id'])
        if not student:
            return jsonify({
                'success': False,
                'error': 'Estudante não encontrado'
            }), 404

        # Verificar se disciplina existe
        discipline = Discipline.query.get(data['discipline_id'])
        if not discipline:
            return jsonify({
                'success': False,
                'error': 'Disciplina não encontrada'
            }), 404

        # Verificar se já existe nota para esta combinação
        existing_grade = Grade.query.filter_by(
            student_id=data['student_id'],
            discipline_id=data['discipline_id']
        ).first()

        if existing_grade:
            # Atualizar nota existente
            if 'nota1' in data:
                existing_grade.nota1 = data['nota1']
            if 'nota2' in data:
                existing_grade.nota2 = data['nota2']
            existing_grade.calculate_media()
            grade = existing_grade
        else:
            # Criar nova nota
            grade = Grade(
                student_id=data['student_id'],
                discipline_id=data['discipline_id'],
                nota1=data.get('nota1'),
                nota2=data.get('nota2')
            )
            grade.calculate_media()
            db.session.add(grade)

        db.session.commit()

        # Calcular e atribuir XP
        xp_reward = grade.get_xp_reward()
        student_user = User.query.get(student.user_id)
        level_up = False

        if student_user and xp_reward > 0:
            level_up = student_user.add_xp(xp_reward)
            db.session.commit()

        action = "atualizada" if existing_grade else "cadastrada"

        return jsonify({
            'success': True,
            'message': f'Nota {action} com sucesso! +{xp_reward} XP',
            'grade': grade.to_dict(),
            'xp_reward': xp_reward,
            'level_up': level_up
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao cadastrar nota: {str(e)}'
        }), 500


# ========== LISTAGEM ADMINISTRATIVA ==========

@grade_bp.route('/admin/grades', methods=['GET'])
@teacher_or_admin_required
def get_all_grades():
    """Lista todas as notas (admin)"""
    try:
        grades = Grade.query.all()
        return jsonify({
            'success': True,
            'grades': [grade.to_dict() for grade in grades]
        })
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== NOVA ROTA: NOTAS DO ESTUDANTE LOGADO ==========

@grade_bp.route('/grades/me', methods=['GET'])
@login_required
def get_my_grades():
    """Lista notas do estudante logado."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Não autenticado'}), 401

        student = Student.query.filter_by(user_id=user_id).first()
        if not student:
            return jsonify({'success': False, 'error': 'Perfil de estudante não encontrado'}), 404

        grades = Grade.query.filter_by(student_id=student.id).all()

        grades_data = []
        for g in grades:
            discipline = Discipline.query.get(g.discipline_id)
            d = g.to_dict()
            d['discipline'] = {
                'id': discipline.id if discipline else None,
                'nome': discipline.nome if discipline else None,
                'codigo': discipline.codigo if discipline else None,
                'ano_turma': discipline.ano_turma if discipline else None,
            } if discipline else None
            grades_data.append(d)

        return jsonify({'success': True, 'grades': grades_data})

    except Exception as e:
        print(f'❌ Erro em /grades/me: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500
