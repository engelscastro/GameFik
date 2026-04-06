# src/routes/enrollment_routes.py
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.academic import Enrollment, Student, Discipline
from functools import wraps

enrollment_bp = Blueprint('enrollment', __name__)

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

@enrollment_bp.route('/enrollments/me', methods=['GET'])
@login_required
def get_my_enrollments():
    try:
        user = User.query.get(session['user_id'])
        student = Student.query.filter_by(user_id=user.id).first()
        if not student:
            return jsonify({'success': False, 'error': 'Perfil de estudante não encontrado'}), 404

        enrollments = Enrollment.query.filter_by(student_id=student.id, status='active').all()
        result = []
        for e in enrollments:
            discipline = Discipline.query.get(e.discipline_id)
            result.append({
                'id': e.id,
                'discipline_id': e.discipline_id,
                'discipline_nome': discipline.nome if discipline else None,
                'status': e.status,
                'enrollment_date': e.enrollment_date.isoformat() if e.enrollment_date else None
            })
        return jsonify({'success': True, 'enrollments': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@enrollment_bp.route('/admin/enrollments', methods=['GET'])
@admin_required
def get_all_enrollments():
    try:
        enrollments = Enrollment.query.all()
        result = []
        for e in enrollments:
            student = Student.query.get(e.student_id)
            discipline = Discipline.query.get(e.discipline_id)
            result.append({
                'id': e.id,
                'student_id': e.student_id,
                'student_nome': student.nome if student else None,
                'discipline_id': e.discipline_id,
                'discipline_nome': discipline.nome if discipline else None,
                'status': e.status,
                'enrollment_date': e.enrollment_date.isoformat() if e.enrollment_date else None
            })
        return jsonify({'success': True, 'enrollments': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500