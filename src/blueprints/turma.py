# src/blueprints/turma.py
from datetime import datetime
from flask import Blueprint, request, jsonify, session
from src.models.user import db, User
from src.models.academic import Student, Professor, Discipline, Enrollment, TurmaFeedPost, TurmaAssignmentSubmission
from .utils import login_required, teacher_required, teacher_or_admin_required, student_required

turma_bp = Blueprint('turma', __name__)

# ========== DADOS DA TURMA ==========
@turma_bp.route('/turma/<string:ano_turma>', methods=['GET'])
@login_required
def get_turma_data(ano_turma):
    user = User.query.get(session['user_id'])
    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id, ano_turma=ano_turma).first()
        if not student:
            return jsonify({'success': False, 'error': 'Você não pertence a esta turma'}), 403
    elif user.role == 'teacher':
        professor = Professor.query.filter_by(user_id=user.id).first()
        if not professor:
            return jsonify({'success': False, 'error': 'Perfil de professor não encontrado'}), 404
        disciplines = Discipline.query.filter_by(professor_id=professor.id, ano_turma=ano_turma).first()
        if not disciplines:
            return jsonify({'success': False, 'error': 'Você não leciona nesta turma'}), 403
    elif user.role != 'admin':
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403

    disciplines = Discipline.query.filter_by(ano_turma=ano_turma).all()
    students = Student.query.filter_by(ano_turma=ano_turma).all()
    posts = TurmaFeedPost.query.filter_by(ano_turma=ano_turma).order_by(TurmaFeedPost.created_at.desc()).all()

    return jsonify({
        'success': True,
        'turma': ano_turma,
        'disciplines': [d.to_dict() for d in disciplines],
        'students': [s.to_dict() for s in students],
        'feed': [p.to_dict() for p in posts],
        'user_role': user.role
    })

# ========== CRIAR POST NO FEED ==========
@turma_bp.route('/turma/<string:ano_turma>/post', methods=['POST'])
@teacher_or_admin_required
def create_feed_post(ano_turma):
    data = request.json
    user_id = session['user_id']
    due_date = None
    if data.get('due_date'):
        try:
            due_date = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        except:
            due_date = datetime.strptime(data['due_date'], '%Y-%m-%dT%H:%M')
    post = TurmaFeedPost(
        ano_turma=ano_turma,
        user_id=user_id,
        title=data.get('title'),
        content=data.get('content'),
        post_type=data.get('post_type', 'announcement'),
        file_url=data.get('file_url'),
        due_date=due_date,
        points=data.get('points', 0)
    )
    db.session.add(post)
    db.session.commit()
    return jsonify({'success': True, 'post': post.to_dict()}), 201

# ========== LISTAR POSTS DO FEED ==========
@turma_bp.route('/turma/<string:ano_turma>/feed', methods=['GET'])
@login_required
def get_feed(ano_turma):
    posts = TurmaFeedPost.query.filter_by(ano_turma=ano_turma).order_by(TurmaFeedPost.created_at.desc()).all()
    return jsonify({'success': True, 'posts': [p.to_dict() for p in posts]})

# ========== LISTAR ATIVIDADES (tipo assignment) ==========
@turma_bp.route('/turma/<string:ano_turma>/assignments', methods=['GET'])
@login_required
def get_assignments(ano_turma):
    assignments = TurmaFeedPost.query.filter_by(ano_turma=ano_turma, post_type='assignment').order_by(TurmaFeedPost.due_date.asc()).all()
    return jsonify({'success': True, 'assignments': [a.to_dict() for a in assignments]})

# ========== LISTAR ALUNOS DA TURMA (com filtro opcional por disciplina) ==========
@turma_bp.route('/turma/<string:ano_turma>/students', methods=['GET'])
@login_required
def get_turma_students(ano_turma):
    discipline_id = request.args.get('discipline_id', type=int)
    user = User.query.get(session['user_id'])

    # Validação de permissão (aluno ou professor da turma)
    if user.role == 'student':
        student = Student.query.filter_by(user_id=user.id, ano_turma=ano_turma).first()
        if not student:
            return jsonify({'success': False, 'error': 'Acesso negado'}), 403
    elif user.role == 'teacher':
        professor = Professor.query.filter_by(user_id=user.id).first()
        if not professor:
            return jsonify({'success': False, 'error': 'Perfil de professor não encontrado'}), 404
        # Se discipline_id foi informado, verifica se a disciplina pertence ao professor
        if discipline_id:
            discipline = Discipline.query.get(discipline_id)
            if not discipline or discipline.professor_id != professor.id:
                return jsonify({'success': False, 'error': 'Disciplina não pertence a você'}), 403
        else:
            # Fallback: verifica se professor leciona alguma disciplina na turma
            disciplines = Discipline.query.filter_by(professor_id=professor.id, ano_turma=ano_turma).first()
            if not disciplines:
                return jsonify({'success': False, 'error': 'Você não leciona nesta turma'}), 403
    elif user.role != 'admin':
        return jsonify({'success': False, 'error': 'Acesso negado'}), 403

    # Query base: alunos da turma
    query = Student.query.filter_by(ano_turma=ano_turma)

    # Se discipline_id foi informado, filtra apenas alunos matriculados na disciplina
    if discipline_id:
        # Subconsulta: alunos com matrícula ativa na disciplina
        subquery = db.session.query(Enrollment.student_id).filter(
            Enrollment.discipline_id == discipline_id,
            Enrollment.status == 'active'
        ).subquery()
        query = query.filter(Student.id.in_(subquery))

    students = query.all()
    result = []
    for s in students:
        result.append({
            'id': s.id,
            'nome': s.nome,
            'matricula': s.matricula,
            'curso': s.curso,
            'ano_turma': s.ano_turma,
            'avatar': '👨‍🎓'
        })
    return jsonify({'success': True, 'students': result})

# ========== ENTREGAR ATIVIDADE ==========
@turma_bp.route('/turma/<string:ano_turma>/post/<int:post_id>/submit', methods=['POST'])
@student_required
def submit_assignment(ano_turma, post_id):
    user_id = session['user_id']
    student = Student.query.filter_by(user_id=user_id, ano_turma=ano_turma).first()
    if not student:
        return jsonify({'success': False, 'error': 'Aluno não pertence a esta turma'}), 403

    post = TurmaFeedPost.query.get_or_404(post_id)
    if post.post_type != 'assignment':
        return jsonify({'success': False, 'error': 'Esta postagem não é uma atividade'}), 400

    data = request.json
    submission = TurmaAssignmentSubmission.query.filter_by(post_id=post_id, student_id=student.id).first()
    if not submission:
        submission = TurmaAssignmentSubmission(post_id=post_id, student_id=student.id)

    submission.content = data.get('content')
    submission.file_url = data.get('file_url')
    submission.status = 'submitted'
    db.session.commit()

    return jsonify({'success': True, 'submission': submission.to_dict()})

# ========== CORRIGIR ATIVIDADE ==========
@turma_bp.route('/turma/<string:ano_turma>/post/<int:post_id>/grade/<int:student_id>', methods=['POST'])
@teacher_or_admin_required
def grade_assignment(ano_turma, post_id, student_id):
    data = request.json
    submission = TurmaAssignmentSubmission.query.filter_by(post_id=post_id, student_id=student_id).first_or_404()
    submission.grade = data.get('grade')
    submission.feedback = data.get('feedback')
    submission.status = 'graded'
    db.session.commit()

    # Conceder XP baseado na nota (opcional)
    student = Student.query.get(student_id)
    if student and submission.grade:
        user = User.query.get(student.user_id)
        if user:
            xp = int(submission.grade)  # 0-100
            user.add_xp(xp)
            db.session.commit()

    return jsonify({'success': True, 'submission': submission.to_dict()})

# ========== VIDEOCHAMADA ==========
# Dicionário simples para armazenar links personalizados (em produção usar banco)
_videocall_links = {}

@turma_bp.route('/turma/<string:ano_turma>/videocall', methods=['GET', 'POST'])
@login_required
def videocall_link(ano_turma):
    if request.method == 'POST':
        if request.json and request.json.get('link'):
            _videocall_links[ano_turma] = request.json['link']
        else:
            # Gerar link padrão Jitsi
            _videocall_links[ano_turma] = f"https://meet.jit.si/EduQuest-{ano_turma.replace('_', '-')}"
        return jsonify({'success': True, 'link': _videocall_links[ano_turma]})
    else:
        link = _videocall_links.get(ano_turma)
        if not link:
            link = f"https://meet.jit.si/EduQuest-{ano_turma.replace('_', '-')}"
        return jsonify({'success': True, 'link': link})
