"""
Blueprint para gerenciamento de Avaliações Bimestrais
Professor cria provas, trabalhos, participações e projetos
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, session

from src.models.academic import Assessment, Professor, Discipline, Enrollment, Student
from src.models.user import db, User
from src.blueprints.utils import login_required, teacher_required

assessment_bp = Blueprint('assessment', __name__)


# ========== AVALIAÇÕES - CRUD ==========

@assessment_bp.route('/assessments', methods=['POST'])
@teacher_required
def create_assessment():
    """Professor cria uma nova avaliação (prova, trabalho, etc.)"""
    try:
        data = request.json
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if not professor:
            return jsonify({'success': False, 'error': 'Perfil de professor não encontrado'}), 404

        # Validações
        required = ['discipline_id', 'title', 'assessment_type', 'bimestre']
        for field in required:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'Campo {field} é obrigatório'}), 400

        # Validar bimestre
        bimestre = int(data['bimestre'])
        if bimestre not in [1, 2, 3, 4]:
            return jsonify({'success': False, 'error': 'Bimestre deve ser 1, 2, 3 ou 4'}), 400

        # Validar tipo
        if data['assessment_type'] not in ['prova', 'trabalho', 'participacao', 'projeto']:
            return jsonify({'success': False, 'error': 'Tipo deve ser: prova, trabalho, participacao ou projeto'}), 400

        # Verificar se disciplina existe e pertence ao professor
        discipline = Discipline.query.get(data['discipline_id'])
        if not discipline:
            return jsonify({'success': False, 'error': 'Disciplina não encontrada'}), 404

        if discipline.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Você não é o professor desta disciplina'}), 403

        # Criar avaliação
        assessment = Assessment(
            discipline_id=data['discipline_id'],
            professor_id=professor.id,
            title=data['title'],
            description=data.get('description', ''),
            assessment_type=data['assessment_type'],
            bimestre=bimestre,
            peso=float(data.get('peso', 1.0)),
            max_score=float(data.get('max_score', 10.0)),
            due_date=datetime.fromisoformat(data['due_date']) if data.get('due_date') else None,
            is_active=data.get('is_active', True)
        )

        db.session.add(assessment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Avaliação criada com sucesso!',
            'assessment': assessment.to_dict()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@assessment_bp.route('/assessments', methods=['GET'])
@login_required
def get_assessments():
    """Listar avaliações com filtros opcionais"""
    try:
        current_user = User.query.get(session['user_id'])

        # Filtros
        discipline_id = request.args.get('discipline_id', type=int)
        bimestre = request.args.get('bimestre', type=int)
        assessment_type = request.args.get('type')

        query = Assessment.query

        # Se for professor, mostrar apenas suas avaliações
        if current_user.role == 'teacher':
            professor = Professor.query.filter_by(user_id=current_user.id).first()
            if professor:
                query = query.filter_by(professor_id=professor.id)

        # Se for aluno, mostrar avaliações das disciplinas matriculadas
        elif current_user.role == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            if student:
                enrolled_disciplines = db.session.query(Enrollment.discipline_id).filter_by(
                    student_id=student.id, status='active'
                ).all()
                discipline_ids = [d[0] for d in enrolled_disciplines]
                query = query.filter(Assessment.discipline_id.in_(discipline_ids))

        if discipline_id:
            query = query.filter_by(discipline_id=discipline_id)
        if bimestre:
            query = query.filter_by(bimestre=bimestre)
        if assessment_type:
            query = query.filter_by(assessment_type=assessment_type)

        assessments = query.order_by(Assessment.bimestre, Assessment.created_at.desc()).all()

        return jsonify({
            'success': True,
            'assessments': [a.to_dict() for a in assessments]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@assessment_bp.route('/assessments/<int:assessment_id>', methods=['GET'])
@login_required
def get_assessment(assessment_id):
    """Obter detalhes de uma avaliação"""
    try:
        assessment = Assessment.query.get_or_404(assessment_id)

        # Verificar permissão
        current_user = User.query.get(session['user_id'])
        if current_user.role == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            enrollment = Enrollment.query.filter_by(
                student_id=student.id,
                discipline_id=assessment.discipline_id,
                status='active'
            ).first()
            if not enrollment:
                return jsonify({'success': False, 'error': 'Acesso negado'}), 403

        return jsonify({
            'success': True,
            'assessment': assessment.to_dict()
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@assessment_bp.route('/assessments/<int:assessment_id>', methods=['PUT'])
@teacher_required
def update_assessment(assessment_id):
    """Professor atualiza uma avaliação"""
    try:
        assessment = Assessment.query.get_or_404(assessment_id)
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if assessment.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Você não pode editar esta avaliação'}), 403

        data = request.json

        if 'title' in data:
            assessment.title = data['title']
        if 'description' in data:
            assessment.description = data['description']
        if 'assessment_type' in data:
            assessment.assessment_type = data['assessment_type']
        if 'bimestre' in data:
            assessment.bimestre = int(data['bimestre'])
        if 'peso' in data:
            assessment.peso = float(data['peso'])
        if 'max_score' in data:
            assessment.max_score = float(data['max_score'])
        if 'due_date' in data:
            assessment.due_date = datetime.fromisoformat(data['due_date']) if data['due_date'] else None
        if 'is_active' in data:
            assessment.is_active = data['is_active']

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Avaliação atualizada com sucesso',
            'assessment': assessment.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@assessment_bp.route('/assessments/<int:assessment_id>', methods=['DELETE'])
@teacher_required
def delete_assessment(assessment_id):
    """Professor exclui uma avaliação"""
    try:
        assessment = Assessment.query.get_or_404(assessment_id)
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if assessment.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Você não pode excluir esta avaliação'}), 403

        db.session.delete(assessment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Avaliação excluída com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== AVALIAÇÕES POR DISCIPLINA ==========

@assessment_bp.route('/disciplines/<int:discipline_id>/assessments', methods=['GET'])
@login_required
def get_discipline_assessments(discipline_id):
    """Listar avaliações de uma disciplina específica"""
    try:
        current_user = User.query.get(session['user_id'])

        # Verificar acesso
        if current_user.role == 'student':
            student = Student.query.filter_by(user_id=current_user.id).first()
            enrollment = Enrollment.query.filter_by(
                student_id=student.id,
                discipline_id=discipline_id,
                status='active'
            ).first()
            if not enrollment:
                return jsonify({'success': False, 'error': 'Você não está matriculado nesta disciplina'}), 403

        bimestre = request.args.get('bimestre', type=int)

        query = Assessment.query.filter_by(discipline_id=discipline_id, is_active=True)
        if bimestre:
            query = query.filter_by(bimestre=bimestre)

        assessments = query.order_by(Assessment.bimestre, Assessment.created_at.desc()).all()

        return jsonify({
            'success': True,
            'discipline_id': discipline_id,
            'bimestre': bimestre,
            'assessments': [a.to_dict() for a in assessments]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== TIPOS DE AVALIAÇÃO ==========

@assessment_bp.route('/assessment-types', methods=['GET'])
@login_required
def get_assessment_types():
    """Retorna os tipos de avaliação disponíveis"""
    return jsonify({
        'success': True,
        'types': [
            {'value': 'prova', 'label': 'Prova', 'icon': '📝'},
            {'value': 'trabalho', 'label': 'Trabalho', 'icon': '📄'},
            {'value': 'participacao', 'label': 'Participação', 'icon': '💬'},
            {'value': 'projeto', 'label': 'Projeto', 'icon': '🚀'}
        ]
    })