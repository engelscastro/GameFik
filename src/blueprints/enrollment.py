# enrollment.py
"""
Blueprint para gerenciamento de matrículas
Responsável por matrícula individual, em lote, cancelamento,
listagem e rotas de debug/correção.
"""

from flask import Blueprint, request, jsonify, session

from src.models.academic import Student, Discipline, Enrollment
from src.models.user import db, User
from .utils import login_required, teacher_or_admin_required

# Criar blueprint
enrollment_bp = Blueprint('enrollment', __name__)


# ========== MATRÍCULAS - OPERAÇÕES PRINCIPAIS ==========

@enrollment_bp.route('/enrollments', methods=['POST'])
@login_required
def create_enrollment():
    """Matricular estudante em disciplina"""
    try:
        data = request.json
        print(f"🔍 DEBUG - Dados recebidos para matrícula: {data}")

        # Validação básica
        if not data or not data.get('student_id') or not data.get('discipline_id'):
            return jsonify({
                'success': False,
                'error': 'ID do estudante e da disciplina são obrigatórios'
            }), 400

        # Verificar se estudante existe (buscar pelo user_id)
        student = Student.query.filter_by(user_id=data['student_id']).first()
        if not student:
            return jsonify({
                'success': False,
                'error': 'Estudante não encontrado'
            }), 404

        # Verificar se a disciplina existe
        discipline = Discipline.query.get(data['discipline_id'])
        if not discipline:
            return jsonify({
                'success': False,
                'error': 'Disciplina não encontrada'
            }), 404

        print(f"🔍 DEBUG - Estudante encontrado: {student.nome}, Disciplina: {discipline.nome}")

        # Verificar se já está matriculado (ativo)
        existing_enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            discipline_id=data['discipline_id'],
            status='active'
        ).first()

        if existing_enrollment:
            return jsonify({
                'success': False,
                'error': f'Estudante já está matriculado na disciplina {discipline.nome}'
            }), 400

        # Verificar compatibilidade de turma
        if student.ano_turma and discipline.ano_turma and student.ano_turma != discipline.ano_turma:
            return jsonify({
                'success': False,
                'error': f'Estudante da turma {student.ano_turma} não pode se matricular em disciplina da turma {discipline.ano_turma}'
            }), 400

        # Criar matrícula
        enrollment = Enrollment(
            student_id=student.id,
            discipline_id=data['discipline_id'],
            status='active'
        )

        db.session.add(enrollment)
        db.session.commit()

        # Adicionar XP para o estudante
        student_user = User.query.get(student.user_id)
        xp_reward = 10
        level_up = False
        if student_user:
            level_up = student_user.add_xp(xp_reward)
            db.session.commit()

        # Preparar resposta
        enrollment_data = {
            'id': enrollment.id,
            'student_id': enrollment.student_id,
            'discipline_id': enrollment.discipline_id,
            'status': enrollment.status,
            'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
            'student_nome': student.nome,
            'student_matricula': student.matricula,
            'student_ano_turma': student.ano_turma,
            'discipline_nome': discipline.nome,
            'discipline_codigo': discipline.codigo,
            'discipline_ano_turma': discipline.ano_turma
        }

        return jsonify({
            'success': True,
            'message': f'Matrícula de {student.nome} em {discipline.nome} realizada com sucesso! +{xp_reward} XP',
            'enrollment': enrollment_data,
            'xp_reward': xp_reward,
            'level_up': level_up
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro na matrícula: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erro ao realizar matrícula: {str(e)}'
        }), 500


@enrollment_bp.route('/enrollments/<int:enrollment_id>', methods=['DELETE'])
@login_required
def cancel_enrollment(enrollment_id):
    """Cancelar matrícula"""
    try:
        enrollment = Enrollment.query.get_or_404(enrollment_id)
        current_user = User.query.get(session['user_id'])

        # Verificar permissão: estudante só pode cancelar própria matrícula
        student = Student.query.filter_by(user_id=session['user_id']).first()
        if student and enrollment.student_id != student.id:
            return jsonify({
                'success': False,
                'error': 'Você só pode cancelar suas próprias matrículas'
            }), 403

        # Admin/professor pode cancelar qualquer matrícula
        if current_user.role not in ['teacher', 'admin'] and (not student or enrollment.student_id != student.id):
            return jsonify({
                'success': False,
                'error': 'Acesso não autorizado'
            }), 403

        # Verificar se já tem notas (impedir cancelamento)
        from src.models.academic import Grade
        grade = Grade.query.filter_by(
            student_id=enrollment.student_id,
            discipline_id=enrollment.discipline_id
        ).first()

        if grade and (grade.nota1 is not None or grade.nota2 is not None):
            return jsonify({
                'success': False,
                'error': 'Não é possível cancelar matrícula com notas lançadas'
            }), 400

        # 🔥 Deletar definitivamente a matrícula
        db.session.delete(enrollment)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Matrícula deletada com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao cancelar matrícula: {str(e)}'
        }), 500


# ========== NOVA ROTA: MATRÍCULAS DO ESTUDANTE LOGADO ==========

@enrollment_bp.route('/enrollments/me', methods=['GET'])
@login_required
def get_my_enrollments():
    """Lista matrículas do estudante logado."""
    try:
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'success': False, 'error': 'Não autenticado'}), 401

        student = Student.query.filter_by(user_id=user_id).first()
        if not student:
            return jsonify({'success': False, 'error': 'Perfil de estudante não encontrado'}), 404

        enrollments = Enrollment.query.filter_by(
            student_id=student.id,
            status='active'
        ).all()

        enrollments_data = []
        for e in enrollments:
            discipline = Discipline.query.get(e.discipline_id)

            enrollments_data.append({
                'id': e.id,
                'student_id': e.student_id,
                'discipline_id': e.discipline_id,
                'status': e.status,
                'enrollment_date': e.enrollment_date.isoformat() if e.enrollment_date else None,
                # usa o to_dict() da Discipline, que já inclui professor_nome com segurança
                'discipline': discipline.to_dict() if discipline else None
            })

        return jsonify({'success': True, 'enrollments': enrollments_data})

    except Exception as e:
        print(f'❌ Erro em /enrollments/me: {e}')
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== MATRÍCULA EM LOTE ==========

@enrollment_bp.route('/enrollments/bulk', methods=['POST'])
@teacher_or_admin_required
def bulk_enrollment():
    """Matrícula em lote para uma turma"""
    try:
        data = request.json

        if not data.get('target_year') or not data.get('discipline_id'):
            return jsonify({
                'success': False,
                'error': 'Turma e disciplina são obrigatórios'
            }), 400

        # Buscar estudantes da turma
        students_in_year = Student.query.filter_by(ano_turma=data['target_year']).all()
        if not students_in_year:
            return jsonify({
                'success': False,
                'error': 'Nenhum estudante encontrado na turma selecionada'
            }), 404

        # Verificar se disciplina existe
        discipline = Discipline.query.get(data['discipline_id'])
        if not discipline:
            return jsonify({
                'success': False,
                'error': 'Disciplina não encontrada'
            }), 404

        success_count = 0
        error_count = 0
        results = []

        for student in students_in_year:
            try:
                # Verificar se já está matriculado
                existing = Enrollment.query.filter_by(
                    student_id=student.id,
                    discipline_id=data['discipline_id'],
                    status='active'
                ).first()

                if not existing:
                    enrollment = Enrollment(
                        student_id=student.id,
                        discipline_id=data['discipline_id'],
                        status='active'
                    )

                    db.session.add(enrollment)

                    # Adicionar XP
                    student_user = User.query.get(student.user_id)
                    if student_user:
                        student_user.add_xp(10)

                    success_count += 1
                    results.append({'student': student.nome, 'status': 'success'})
                else:
                    error_count += 1
                    results.append({'student': student.nome, 'status': 'already_enrolled'})

            except Exception as e:
                error_count += 1
                results.append({'student': student.nome, 'status': 'error', 'error': str(e)})

        db.session.commit()

        return jsonify({
            'success': True,
            'message': f'Matrícula em lote concluída: {success_count} sucesso(s), {error_count} erro(s)',
            'results': results,
            'success_count': success_count,
            'error_count': error_count
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ROTA ADMIN PARA MATRÍCULAS ==========

@enrollment_bp.route('/admin/enrollments', methods=['POST'])
@teacher_or_admin_required
def create_enrollment_admin():
    """Matricular estudante em disciplina (admin/professor)"""
    try:
        current_user = User.query.get(session['user_id'])
        data = request.json
        print(f"🔍 DEBUG - Dados recebidos para matrícula admin: {data}")

        # Validação de campos obrigatórios
        required_fields = ['student_id', 'discipline_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400

        # Verificar se estudante existe (buscar pelo user_id)
        student = Student.query.filter_by(user_id=data['student_id']).first()
        if not student:
            return jsonify({
                'success': False,
                'error': 'Estudante não encontrado'
            }), 404

        # Verificar se a disciplina existe
        discipline = Discipline.query.get(data['discipline_id'])
        if not discipline:
            return jsonify({
                'success': False,
                'error': 'Disciplina não encontrada'
            }), 404

        print(f"🔍 DEBUG - Estudante: {student.nome}, Disciplina: {discipline.nome}")

        # Para professores, verificar se é o professor da disciplina
        from src.models.academic import Professor
        if current_user.role == 'teacher':
            professor = Professor.query.filter_by(user_id=current_user.id).first()
            if discipline.professor_id != professor.id:
                return jsonify({
                    'success': False,
                    'error': 'Você não é o professor desta disciplina'
                }), 403

        # Verificar compatibilidade de ano/turma
        if student.ano_turma != discipline.ano_turma:
            return jsonify({
                'success': False,
                'error': f'Estudante do ano/turma {student.ano_turma} não pode se matricular em disciplina do ano/turma {discipline.ano_turma}'
            }), 400

        # Verificar se já está matriculado (ativo)
        existing_enrollment = Enrollment.query.filter_by(
            student_id=student.id,
            discipline_id=data['discipline_id'],
            status='active'
        ).first()

        if existing_enrollment:
            return jsonify({
                'success': False,
                'error': f'Estudante já está matriculado na disciplina {discipline.nome}'
            }), 400

        # Verificar limite de matrículas do estudante
        current_enrollments = Enrollment.query.filter_by(
            student_id=student.id,
            status='active'
        ).count()

        MAX_ENROLLMENTS = 8
        if current_enrollments >= MAX_ENROLLMENTS:
            return jsonify({
                'success': False,
                'error': f'Estudante atingiu o limite de {MAX_ENROLLMENTS} matrículas ativas'
            }), 400

        # Criar matrícula
        enrollment = Enrollment(
            student_id=student.id,
            discipline_id=data['discipline_id'],
            status='active'
        )

        db.session.add(enrollment)
        db.session.commit()

        # Adicionar XP para o estudante
        student_user = User.query.get(student.user_id)
        xp_reward = 10
        level_up = False
        if student_user:
            level_up = student_user.add_xp(xp_reward)
            db.session.commit()

        # Preparar resposta
        enrollment_data = {
            'id': enrollment.id,
            'student_id': enrollment.student_id,
            'discipline_id': enrollment.discipline_id,
            'status': enrollment.status,
            'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
            'student_nome': student.nome,
            'student_matricula': student.matricula,
            'student_ano_turma': student.ano_turma,
            'discipline_nome': discipline.nome,
            'discipline_codigo': discipline.codigo,
            'discipline_ano_turma': discipline.ano_turma
        }

        return jsonify({
            'success': True,
            'message': f'Matrícula de {student.nome} em {discipline.nome} realizada com sucesso! +{xp_reward} XP',
            'enrollment': enrollment_data,
            'xp_reward': xp_reward,
            'level_up': level_up,
            'matriculado_por': current_user.username
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro na matrícula admin: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erro ao realizar matrícula: {str(e)}'
        }), 500


@enrollment_bp.route('/admin/enrollments', methods=['GET'])
@teacher_or_admin_required
def get_all_enrollments():
    """Lista todas as matrículas para o painel admin"""
    try:
        enrollments = Enrollment.query.all()

        # Enriquecer dados das matrículas
        enrollments_data = []
        for enrollment in enrollments:
            enrollment_dict = {
                'id': enrollment.id,
                'student_id': enrollment.student_id,
                'discipline_id': enrollment.discipline_id,
                'enrollment_date': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None,
                'status': enrollment.status
            }

            # Buscar dados do estudante
            student = Student.query.get(enrollment.student_id)
            if student:
                enrollment_dict['student_nome'] = student.nome
                enrollment_dict['student_matricula'] = student.matricula
                enrollment_dict['student_ano_turma'] = student.ano_turma
            else:
                enrollment_dict['student_nome'] = 'N/A'
                enrollment_dict['student_matricula'] = 'N/A'
                enrollment_dict['student_ano_turma'] = None

            # Buscar dados da disciplina
            discipline = Discipline.query.get(enrollment.discipline_id)
            if discipline:
                enrollment_dict['discipline_nome'] = discipline.nome
                enrollment_dict['discipline_codigo'] = discipline.codigo
                enrollment_dict['discipline_ano_turma'] = discipline.ano_turma
            else:
                enrollment_dict['discipline_nome'] = 'N/A'
                enrollment_dict['discipline_codigo'] = 'N/A'
                enrollment_dict['discipline_ano_turma'] = None

            enrollments_data.append(enrollment_dict)

        print(f"🔍 DEBUG - Matrículas carregadas: {len(enrollments_data)}")

        return jsonify({
            'success': True,
            'enrollments': enrollments_data
        })

    except Exception as e:
        print(f"❌ Erro ao carregar matrículas: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ========== ROTAS DE DEBUG ==========

@enrollment_bp.route('/debug/enrollments-routes', methods=['GET'])
@login_required
def debug_enrollments_routes():
    """Debug para verificar rotas de matrículas"""
    try:
        current_user = User.query.get(session['user_id'])

        # Testar diferentes consultas
        total_enrollments = Enrollment.query.count()
        active_enrollments = Enrollment.query.filter_by(status='active').count()

        # Testar se há estudantes
        total_students = Student.query.count()

        # Testar se há disciplinas
        total_disciplines = Discipline.query.count()

        return jsonify({
            'success': True,
            'debug_info': {
                'total_enrollments': total_enrollments,
                'active_enrollments': active_enrollments,
                'total_students': total_students,
                'total_disciplines': total_disciplines,
                'user_role': current_user.role,
                'available_routes': [
                    '/api/enrollments (POST) - Criar matrícula',
                    '/api/enrollments/<id> (DELETE) - Cancelar matrícula',
                    '/api/enrollments/me (GET) - Matrículas do aluno logado',
                    '/api/enrollments/bulk (POST) - Matrícula em lote',
                    '/api/admin/enrollments (GET) - Todas as matrículas (admin)',
                    '/api/admin/enrollments (POST) - Criar matrícula (admin)'
                ]
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@enrollment_bp.route('/debug/enrollments', methods=['GET'])
@login_required
def debug_enrollments():
    """Rota de debug para verificar matrículas"""
    try:
        enrollments = Enrollment.query.all()
        result = []

        for enrollment in enrollments:
            student_info = None
            discipline_info = None

            if enrollment.student_id:
                student = Student.query.get(enrollment.student_id)
                if student:
                    student_info = {
                        'id': student.id,
                        'nome': student.nome,
                        'matricula': student.matricula
                    }

            if enrollment.discipline_id:
                discipline = Discipline.query.get(enrollment.discipline_id)
                if discipline:
                    discipline_info = {
                        'id': discipline.id,
                        'nome': discipline.nome,
                        'codigo': discipline.codigo,
                        'ano_turma': discipline.ano_turma
                    }

            result.append({
                'matricula_id': enrollment.id,
                'student_id': enrollment.student_id,
                'student_info': student_info,
                'discipline_id': enrollment.discipline_id,
                'discipline_info': discipline_info,
                'status': enrollment.status,
                'data': enrollment.enrollment_date.isoformat() if enrollment.enrollment_date else None
            })

        return jsonify({
            'success': True,
            'enrollments': result,
            'total': len(result),
            'com_estudante': len([e for e in result if e['student_info']]),
            'com_disciplina': len([e for e in result if e['discipline_info']])
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@enrollment_bp.route('/fix-enrollments', methods=['POST'])
@teacher_or_admin_required
def fix_enrollments():
    """Corrigir matrículas problemáticas"""
    try:
        enrollments = Enrollment.query.all()
        fixed_count = 0

        for enrollment in enrollments:
            student = Student.query.get(enrollment.student_id)
            if not student:
                print(f"❌ Matrícula {enrollment.id}: Estudante {enrollment.student_id} não existe")
                continue

            discipline = Discipline.query.get(enrollment.discipline_id)
            if not discipline:
                print(f"❌ Matrícula {enrollment.id}: Disciplina {enrollment.discipline_id} não existe")
                continue

            fixed_count += 1

        return jsonify({
            'success': True,
            'message': f'Verificadas {len(enrollments)} matrículas. {fixed_count} estão OK.',
            'total_enrollments': len(enrollments),
            'fixed_count': fixed_count
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


#visão agrupada e usar isso só na tela admin.
@enrollment_bp.route('/admin/enrollments/grouped-by-student', methods=['GET'])
@teacher_or_admin_required
def get_enrollments_grouped_by_student():
    """Lista matrículas agrupadas por estudante para o painel admin."""
    try:
        enrollments = Enrollment.query.all()

        grouped = {}
        for e in enrollments:
            student = e.student
            discipline = e.discipline

            if not student:
                continue

            sid = student.id
            if sid not in grouped:
                grouped[sid] = {
                    'student_id': student.id,
                    'student_nome': student.nome,
                    'student_matricula': student.matricula,
                    'student_ano_turma': student.ano_turma,
                    'enrollments': []
                }

            grouped[sid]['enrollments'].append({
                'id': e.id,
                'discipline_id': e.discipline_id,
                'status': e.status,
                'enrollment_date': e.enrollment_date.isoformat() if e.enrollment_date else None,
                'discipline_nome': discipline.nome if discipline else None,
                'discipline_codigo': discipline.codigo if discipline else None,
                'discipline_ano_turma': discipline.ano_turma if discipline else None,
            })

        return jsonify({
            'success': True,
            'students': list(grouped.values())
        })
    except Exception as e:
        print(f"❌ Erro ao agrupar matrículas por estudante: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


