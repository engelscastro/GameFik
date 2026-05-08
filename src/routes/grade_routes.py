"""
Blueprint para gerenciamento de Notas Bimestrais
Sistema completo de lançamento, cálculo de médias e boletim
"""

from flask import Blueprint, request, jsonify, session
from sqlalchemy import func, and_

from src.models.academic import (
    Grade, Assessment, GradeSummary, Student, Professor,
    Discipline, Enrollment
)
from src.models.user import db, User
from .utils import login_required, teacher_required, teacher_or_admin_required

grade_bp = Blueprint('grade', __name__)


# ========== FUNÇÕES AUXILIARES ==========

def calcular_media_bimestre(student_id, discipline_id, bimestre):
    """Calcula a média ponderada do bimestre baseado nas avaliações"""
    assessments = Assessment.query.filter_by(
        discipline_id=discipline_id,
        bimestre=bimestre,
        is_active=True
    ).all()

    if not assessments:
        return None

    total_peso = 0
    total_score = 0

    for assessment in assessments:
        grade = Grade.query.filter_by(
            student_id=student_id,
            assessment_id=assessment.id
        ).first()

        if grade and grade.score is not None:
            total_score += grade.score * assessment.peso
            total_peso += assessment.peso

    if total_peso == 0:
        return None

    return round(total_score / total_peso, 2)


def atualizar_grade_summary(student_id, discipline_id):
    """Atualiza ou cria o resumo de notas do aluno na disciplina"""
    summary = GradeSummary.query.filter_by(
        student_id=student_id,
        discipline_id=discipline_id
    ).first()

    if not summary:
        summary = GradeSummary(
            student_id=student_id,
            discipline_id=discipline_id
        )
        db.session.add(summary)

    # Calcular médias de cada bimestre
    summary.b1_media = calcular_media_bimestre(student_id, discipline_id, 1)
    summary.b2_media = calcular_media_bimestre(student_id, discipline_id, 2)
    summary.b3_media = calcular_media_bimestre(student_id, discipline_id, 3)
    summary.b4_media = calcular_media_bimestre(student_id, discipline_id, 4)

    # Calcular média final
    summary.media_final = summary.calcular_media_final()

    # Atualizar situação
    summary.atualizar_situacao()

    db.session.commit()
    return summary


def get_or_create_grade(student_id, assessment_id):
    """Obtém ou cria uma nota para o aluno na avaliação"""
    grade = Grade.query.filter_by(
        student_id=student_id,
        assessment_id=assessment_id
    ).first()

    if not grade:
        grade = Grade(
            student_id=student_id,
            assessment_id=assessment_id
        )
        db.session.add(grade)

    return grade


# ========== LANÇAR NOTA (Professor) ==========

@grade_bp.route('/grades', methods=['POST'])
@teacher_required
def create_grade():
    """Professor lança nota para um aluno em uma avaliação"""
    try:
        data = request.json
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if not professor:
            return jsonify({'success': False, 'error': 'Perfil de professor não encontrado'}), 404

        # Validações
        required = ['student_id', 'assessment_id', 'score']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Campo {field} é obrigatório'}), 400

        # Verificar se avaliação existe
        assessment = Assessment.query.get(data['assessment_id'])
        if not assessment:
            return jsonify({'success': False, 'error': 'Avaliação não encontrada'}), 404

        # Verificar se professor é o dono da avaliação
        if assessment.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Você não pode lançar notas nesta avaliação'}), 403

        # Verificar se aluno existe e está matriculado
        student = Student.query.get(data['student_id'])
        if not student:
            return jsonify({'success': False, 'error': 'Aluno não encontrado'}), 404

        enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            discipline_id=assessment.discipline_id,
            status='active'
        ).first()

        if not enrollment:
            return jsonify({'success': False, 'error': 'Aluno não está matriculado nesta disciplina'}), 400

        # Validar nota
        score = float(data['score'])
        if score < 0 or score > assessment.max_score:
            return jsonify({
                'success': False,
                'error': f'Nota deve estar entre 0 e {assessment.max_score}'
            }), 400

        # Criar ou atualizar nota
        grade = get_or_create_grade(student.id, assessment.id)
        grade.score = score
        grade.feedback = data.get('feedback', '')

        db.session.commit()

        # Atualizar resumo do aluno
        summary = atualizar_grade_summary(student.id, assessment.discipline_id)

        # XP baseado na nota
        xp_reward = 0
        if score >= 9:
            xp_reward = 50
        elif score >= 7:
            xp_reward = 30
        elif score >= 5:
            xp_reward = 15

        student_user = User.query.get(student.user_id)
        level_up = False
        if student_user and xp_reward > 0:
            level_up = student_user.add_xp(xp_reward)
            db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Nota lançada com sucesso! +{xp_reward} XP',
            'grade': grade.to_dict(),
            'summary': summary.to_dict(),
            'xp_reward': xp_reward,
            'level_up': level_up
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@grade_bp.route('/grades/bulk', methods=['POST'])
@teacher_required
def create_grades_bulk():
    """Professor lança notas em lote para uma avaliação"""
    try:
        data = request.json
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if not professor:
            return jsonify({'success': False, 'error': 'Perfil de professor não encontrado'}), 404

        assessment_id = data.get('assessment_id')
        grades_data = data.get('grades', [])  # [{student_id, score, feedback}, ...]

        if not assessment_id or not grades_data:
            return jsonify({'success': False, 'error': 'assessment_id e grades são obrigatórios'}), 400

        assessment = Assessment.query.get(assessment_id)
        if not assessment:
            return jsonify({'success': False, 'error': 'Avaliação não encontrada'}), 404

        if assessment.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Acesso negado'}), 403

        success_count = 0
        error_count = 0
        results = []

        for item in grades_data:
            try:
                student_id = item.get('student_id')
                score = float(item.get('score'))

                # Validar nota
                if score < 0 or score > assessment.max_score:
                    results.append({
                        'student_id': student_id,
                        'status': 'error',
                        'message': f'Nota fora do intervalo (0-{assessment.max_score})'
                    })
                    error_count += 1
                    continue

                grade = get_or_create_grade(student_id, assessment_id)
                grade.score = score
                grade.feedback = item.get('feedback', '')

                # Atualizar resumo
                student = Student.query.get(student_id)
                if student:
                    atualizar_grade_summary(student.id, assessment.discipline_id)

                success_count += 1
                results.append({
                    'student_id': student_id,
                    'status': 'success',
                    'score': score
                })

            except Exception as e:
                error_count += 1
                results.append({
                    'student_id': item.get('student_id'),
                    'status': 'error',
                    'message': str(e)
                })

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Notas lançadas: {success_count} sucesso(s), {error_count} erro(s)',
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ATUALIZAR NOTA ==========

@grade_bp.route('/grades/<int:grade_id>', methods=['PUT'])
@teacher_required
def update_grade(grade_id):
    """Professor atualiza uma nota já lançada"""
    try:
        grade = Grade.query.get_or_404(grade_id)
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if grade.assessment.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Você não pode editar esta nota'}), 403

        data = request.json

        if 'score' in data:
            score = float(data['score'])
            if score < 0 or score > grade.assessment.max_score:
                return jsonify({
                    'success': False,
                    'error': f'Nota deve estar entre 0 e {grade.assessment.max_score}'
                }), 400
            grade.score = score

        if 'feedback' in data:
            grade.feedback = data['feedback']

        db.session.commit()

        # Atualizar resumo
        summary = atualizar_grade_summary(grade.student_id, grade.assessment.discipline_id)

        return jsonify({
            'success': True,
            'message': 'Nota atualizada com sucesso',
            'grade': grade.to_dict(),
            'summary': summary.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


@grade_bp.route('/grades/<int:grade_id>', methods=['DELETE'])
@teacher_required
def delete_grade(grade_id):
    """Professor remove uma nota"""
    try:
        grade = Grade.query.get_or_404(grade_id)
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if grade.assessment.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Você não pode excluir esta nota'}), 403

        student_id = grade.student_id
        discipline_id = grade.assessment.discipline_id

        db.session.delete(grade)
        db.session.commit()

        # Atualizar resumo
        atualizar_grade_summary(student_id, discipline_id)

        return jsonify({
            'success': True,
            'message': 'Nota removida com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== NOTAS DO ALUNO LOGADO ==========

@grade_bp.route('/grades/me', methods=['GET'])
@login_required
def get_my_grades():
    """Aluno visualiza suas notas"""
    try:
        user_id = session.get('user_id')
        student = Student.query.filter_by(user_id=user_id).first()

        if not student:
            return jsonify({'success': False, 'error': 'Perfil de estudante não encontrado'}), 404

        # Filtros opcionais
        discipline_id = request.args.get('discipline_id', type=int)
        bimestre = request.args.get('bimestre', type=int)

        query = Grade.query.filter_by(student_id=student.id)

        if discipline_id:
            query = query.join(Assessment).filter(Assessment.discipline_id == discipline_id)
        if bimestre:
            query = query.join(Assessment).filter(Assessment.bimestre == bimestre)

        grades = query.order_by(Assessment.bimestre, Assessment.created_at).all()

        return jsonify({
            'success': True,
            'student_id': student.id,
            'student_nome': student.nome,
            'grades': [g.to_dict() for g in grades]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== BOLETIM DO ALUNO ==========

@grade_bp.route('/grades/me/boletim', methods=['GET'])
@login_required
def get_my_boletim():
    """Aluno visualiza boletim completo com médias bimestrais"""
    try:
        user_id = session.get('user_id')
        student = Student.query.filter_by(user_id=user_id).first()

        if not student:
            return jsonify({'success': False, 'error': 'Perfil de estudante não encontrado'}), 404

        # Buscar todas as disciplinas matriculadas
        enrollments = Enrollment.query.filter_by(
            student_id=student.id,
            status='active'
        ).all()

        boletim = []

        for enrollment in enrollments:
            discipline = Discipline.query.get(enrollment.discipline_id)
            if not discipline:
                continue

            # Buscar ou criar resumo
            summary = GradeSummary.query.filter_by(
                student_id=student.id,
                discipline_id=discipline.id
            ).first()

            if not summary:
                summary = atualizar_grade_summary(student.id, discipline.id)

            # Buscar notas detalhadas por bimestre
            notas_por_bimestre = {1: [], 2: [], 3: [], 4: []}

            assessments = Assessment.query.filter_by(
                discipline_id=discipline.id,
                is_active=True
            ).all()

            for assessment in assessments:
                grade = Grade.query.filter_by(
                    student_id=student.id,
                    assessment_id=assessment.id
                ).first()

                if grade:
                    notas_por_bimestre[assessment.bimestre].append({
                        'assessment_id': assessment.id,
                        'title': assessment.title,
                        'type': assessment.assessment_type,
                        'score': grade.score,
                        'max_score': assessment.max_score,
                        'peso': assessment.peso,
                        'feedback': grade.feedback
                    })

            boletim.append({
                'discipline_id': discipline.id,
                'discipline_nome': discipline.nome,
                'discipline_codigo': discipline.codigo,
                'professor_nome': discipline.professor.nome if discipline.professor else None,
                'medias': {
                    'b1': summary.b1_media,
                    'b2': summary.b2_media,
                    'b3': summary.b3_media,
                    'b4': summary.b4_media
                },
                'media_final': summary.media_final,
                'situacao': summary.situacao,
                'nota_recuperacao': summary.nota_recuperacao,
                'notas_detalhadas': notas_por_bimestre
            })

        return jsonify({
            'success': True,
            'student': {
                'id': student.id,
                'nome': student.nome,
                'matricula': student.matricula,
                'ano_turma': student.ano_turma
            },
            'boletim': boletim
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== NOTAS POR AVALIAÇÃO (Professor) ==========

@grade_bp.route('/assessments/<int:assessment_id>/grades', methods=['GET'])
@teacher_required
def get_assessment_grades(assessment_id):
    """Professor visualiza todas as notas de uma avaliação"""
    try:
        assessment = Assessment.query.get_or_404(assessment_id)
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if assessment.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Acesso negado'}), 403

        # Buscar alunos matriculados na disciplina
        enrollments = Enrollment.query.filter_by(
            discipline_id=assessment.discipline_id,
            status='active'
        ).all()

        result = []
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if not student:
                continue

            grade = Grade.query.filter_by(
                student_id=student.id,
                assessment_id=assessment_id
            ).first()

            result.append({
                'student_id': student.id,
                'student_nome': student.nome,
                'student_matricula': student.matricula,
                'grade_id': grade.id if grade else None,
                'score': grade.score if grade else None,
                'max_score': assessment.max_score,
                'feedback': grade.feedback if grade else None,
                'status': 'lancada' if grade and grade.score is not None else 'pendente'
            })

        return jsonify({
            'success': True,
            'assessment': assessment.to_dict(),
            'total_students': len(result),
            'graded_count': len([r for r in result if r['score'] is not None]),
            'grades': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== NOTAS POR DISCIPLINA (Professor) ==========

@grade_bp.route('/disciplines/<int:discipline_id>/grades', methods=['GET'])
@teacher_required
def get_discipline_grades(discipline_id):
    """Professor visualiza notas de todos os alunos na disciplina"""
    try:
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()
        discipline = Discipline.query.get_or_404(discipline_id)

        if discipline.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Acesso negado'}), 403

        bimestre = request.args.get('bimestre', type=int)

        # Buscar alunos matriculados
        enrollments = Enrollment.query.filter_by(
            discipline_id=discipline_id,
            status='active'
        ).all()

        result = []
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if not student:
                continue

            # Buscar resumo
            summary = GradeSummary.query.filter_by(
                student_id=student.id,
                discipline_id=discipline_id
            ).first()

            # Buscar notas detalhadas
            query = Grade.query.join(Assessment).filter(
                Grade.student_id == student.id,
                Assessment.discipline_id == discipline_id
            )

            if bimestre:
                query = query.filter(Assessment.bimestre == bimestre)

            grades = query.all()

            result.append({
                'student_id': student.id,
                'student_nome': student.nome,
                'student_matricula': student.matricula,
                'medias': {
                    'b1': summary.b1_media if summary else None,
                    'b2': summary.b2_media if summary else None,
                    'b3': summary.b3_media if summary else None,
                    'b4': summary.b4_media if summary else None,
                    'final': summary.media_final if summary else None,
                    'situacao': summary.situacao if summary else None
                },
                'notas': [g.to_dict() for g in grades]
            })

        return jsonify({
            'success': True,
            'discipline': discipline.to_dict(),
            'bimestre': bimestre,
            'total_students': len(result),
            'students': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== MÉDIAS BIMESTRAIS (Professor) ==========

@grade_bp.route('/disciplines/<int:discipline_id>/medias', methods=['GET'])
@teacher_required
def get_discipline_medias(discipline_id):
    """Professor visualiza médias bimestrais de todos os alunos"""
    try:
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()
        discipline = Discipline.query.get_or_404(discipline_id)

        if discipline.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Acesso negado'}), 403

        enrollments = Enrollment.query.filter_by(
            discipline_id=discipline_id,
            status='active'
        ).all()

        result = []
        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if not student:
                continue

            # Atualizar resumo antes de retornar
            summary = atualizar_grade_summary(student.id, discipline_id)

            result.append({
                'student_id': student.id,
                'student_nome': student.nome,
                'student_matricula': student.matricula,
                'b1_media': summary.b1_media,
                'b2_media': summary.b2_media,
                'b3_media': summary.b3_media,
                'b4_media': summary.b4_media,
                'media_final': summary.media_final,
                'situacao': summary.situacao,
                'nota_recuperacao': summary.nota_recuperacao
            })

        return jsonify({
            'success': True,
            'discipline': discipline.to_dict(),
            'total_students': len(result),
            'aprovados': len([r for r in result if r['situacao'] == 'aprovado']),
            'recuperacao': len([r for r in result if r['situacao'] == 'recuperacao']),
            'reprovados': len([r for r in result if r['situacao'] == 'reprovado']),
            'students': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== LANÇAR NOTA DE RECUPERAÇÃO ==========

@grade_bp.route('/grades/recuperacao', methods=['POST'])
@teacher_required
def lancar_recuperacao():
    """Professor lança nota de recuperação/final para um aluno"""
    try:
        data = request.json
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        required = ['student_id', 'discipline_id', 'nota_recuperacao']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Campo {field} é obrigatório'}), 400

        discipline = Discipline.query.get(data['discipline_id'])
        if not discipline:
            return jsonify({'success': False, 'error': 'Disciplina não encontrada'}), 404

        if discipline.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Acesso negado'}), 403

        nota_rec = float(data['nota_recuperacao'])
        if nota_rec < 0 or nota_rec > 10:
            return jsonify({'success': False, 'error': 'Nota deve estar entre 0 e 10'}), 400

        summary = GradeSummary.query.filter_by(
            student_id=data['student_id'],
            discipline_id=data['discipline_id']
        ).first()

        if not summary:
            return jsonify({'success': False, 'error': 'Resumo de notas não encontrado'}), 404

        summary.nota_recuperacao = nota_rec

        # Se aluno está em recuperação, recalcular situação
        if summary.situacao == 'recuperacao':
            # Média entre a média final e a nota de recuperação
            if summary.media_final:
                nova_media = (summary.media_final + nota_rec) / 2
                if nova_media >= 5:
                    summary.situacao = 'aprovado'
                else:
                    summary.situacao = 'reprovado'

        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Nota de recuperação lançada com sucesso',
            'summary': summary.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ESTATÍSTICAS DA DISCIPLINA ==========

@grade_bp.route('/disciplines/<int:discipline_id>/stats', methods=['GET'])
@teacher_required
def get_discipline_stats(discipline_id):
    """Estatísticas de notas da disciplina"""
    try:
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()
        discipline = Discipline.query.get_or_404(discipline_id)

        if discipline.professor_id != professor.id and current_user.role != 'admin':
            return jsonify({'success': False, 'error': 'Acesso negado'}), 403

        bimestre = request.args.get('bimestre', type=int)

        # Buscar todas as notas da disciplina
        query = db.session.query(Grade.score).join(Assessment).filter(
            Assessment.discipline_id == discipline_id
        )

        if bimestre:
            query = query.filter(Assessment.bimestre == bimestre)

        scores = [s[0] for s in query.all() if s[0] is not None]

        if not scores:
            return jsonify({
                'success': True,
                'discipline': discipline.to_dict(),
                'stats': {
                    'total_grades': 0,
                    'media': None,
                    'maior_nota': None,
                    'menor_nota': None,
                    'aprovados': 0,
                    'reprovados': 0
                }
            })

        # Contar aprovados/reprovados por bimestre
        summaries = GradeSummary.query.filter_by(discipline_id=discipline_id).all()
        aprovados = len([s for s in summaries if s.situacao == 'aprovado'])
        reprovados = len([s for s in summaries if s.situacao == 'reprovado'])
        recuperacao = len([s for s in summaries if s.situacao == 'recuperacao'])

        return jsonify({
            'success': True,
            'discipline': discipline.to_dict(),
            'bimestre': bimestre,
            'stats': {
                'total_grades': len(scores),
                'media': round(sum(scores) / len(scores), 2),
                'maior_nota': max(scores),
                'menor_nota': min(scores),
                'aprovados': aprovados,
                'reprovados': reprovados,
                'recuperacao': recuperacao
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ADMIN - TODAS AS NOTAS ==========

@grade_bp.route('/admin/grades', methods=['GET'])
@teacher_or_admin_required
def get_all_grades():
    """Admin visualiza todas as notas do sistema"""
    try:
        student_id = request.args.get('student_id', type=int)
        discipline_id = request.args.get('discipline_id', type=int)

        query = Grade.query

        if student_id:
            query = query.filter_by(student_id=student_id)
        if discipline_id:
            query = query.join(Assessment).filter(Assessment.discipline_id == discipline_id)

        grades = query.order_by(Grade.created_at.desc()).limit(500).all()

        return jsonify({
            'success': True,
            'total': len(grades),
            'grades': [g.to_dict() for g in grades]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@grade_bp.route('/admin/summaries', methods=['GET'])
@teacher_or_admin_required
def get_all_summaries():
    """Admin visualiza todos os resumos de notas"""
    try:
        student_id = request.args.get('student_id', type=int)
        discipline_id = request.args.get('discipline_id', type=int)

        query = GradeSummary.query

        if student_id:
            query = query.filter_by(student_id=student_id)
        if discipline_id:
            query = query.filter_by(discipline_id=discipline_id)

        summaries = query.all()

        return jsonify({
            'success': True,
            'total': len(summaries),
            'summaries': [s.to_dict() for s in summaries]
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500