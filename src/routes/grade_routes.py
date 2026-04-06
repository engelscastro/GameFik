# src/routes/grade_routes.py
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.academic import Grade, Student, Discipline
from functools import wraps

grade_bp = Blueprint('grade', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': 'Login necessário'}), 401
        return f(*args, **kwargs)
    return decorated_function

@grade_bp.route('/grades', methods=['POST'])
@login_required
def create_grade():
    try:
        data = request.json
        user = User.query.get(session['user_id'])

        # Verificar se é professor ou admin
        if user.role not in ['teacher', 'admin']:
            return jsonify({'success': False, 'error': 'Apenas professores podem lançar notas'}), 403

        # Buscar ou criar nota
        grade = Grade.query.filter_by(
            student_id=data['student_id'],
            discipline_id=data['discipline_id']
        ).first()

        if not grade:
            grade = Grade(
                student_id=data['student_id'],
                discipline_id=data['discipline_id']
            )
            db.session.add(grade)

        if 'nota1' in data:
            grade.nota1 = data['nota1']
        if 'nota2' in data:
            grade.nota2 = data['nota2']

        grade.calculate_media()
        db.session.commit()

        return jsonify({'success': True, 'grade': grade.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@grade_bp.route('/grades/me', methods=['GET'])
@login_required
def get_my_grades():
    try:
        user = User.query.get(session['user_id'])
        student = Student.query.filter_by(user_id=user.id).first()
        if not student:
            return jsonify({'success': False, 'error': 'Perfil de estudante não encontrado'}), 404

        grades = Grade.query.filter_by(student_id=student.id).all()
        result = []
        for g in grades:
            discipline = Discipline.query.get(g.discipline_id)
            result.append({
                'id': g.id,
                'discipline_id': g.discipline_id,
                'discipline_nome': discipline.nome if discipline else None,
                'nota1': g.nota1,
                'nota2': g.nota2,
                'media': g.media
            })
        return jsonify({'success': True, 'grades': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500