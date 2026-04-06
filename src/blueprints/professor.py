"""
Blueprint para gerenciamento de professores
Responsável por operações CRUD de professores, dashboard do professor
e listagem administrativa.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, session
from sqlalchemy import func

from src.models.academic import Professor, Discipline, Enrollment, AcademicMission
from src.models.user import db, User
from .utils import login_required, teacher_required, admin_required, teacher_or_admin_required

# Criar blueprint
professor_bp = Blueprint('professor', __name__)


# ========== PROFESSORES - CRUD ==========

@professor_bp.route('/professors', methods=['POST'])
@admin_required
def create_professor():
    """Criar professor com conta de usuário"""
    try:
        data = request.json
        print(f"📝 Dados recebidos: {data}")

        # Validação de campos obrigatórios
        required_fields = ['nome', 'cpf', 'departamento']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400

        # Verificar CPF único
        existing_professor = Professor.query.filter_by(cpf=data['cpf']).first()
        if existing_professor:
            return jsonify({
                'success': False,
                'error': 'Já existe um professor com este CPF'
            }), 400

        # Verificar se usuário já existe com este CPF
        existing_user = User.query.filter_by(username=data['cpf']).first()
        if existing_user:
            return jsonify({
                'success': False,
                'error': 'Já existe um usuário com este CPF'
            }), 400

        # Criar usuário
        user = User(username=data['cpf'], role='teacher')
        user.set_password('prof123')  # Senha padrão
        db.session.add(user)
        db.session.flush()  # Obter ID sem commit
        print(f"✅ Usuário criado: ID {user.id}")

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
        print(f"✅ Professor criado: {professor.nome}")

        return jsonify({
            'success': True,
            'message': 'Professor cadastrado com sucesso!',
            'professor': professor.to_dict(),
            'login_info': {
                'username': data['cpf'],
                'password': 'prof123',
                'role': 'teacher'
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"❌ ERRO CRÍTICO ao criar professor: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erro ao criar professor: {str(e)}'
        }), 500


@professor_bp.route('/professors/<int:professor_id>', methods=['DELETE'])
@admin_required
def delete_professor(professor_id):
    """Excluir professor"""
    try:
        professor = Professor.query.get(professor_id)
        if not professor:
            return jsonify({
                'success': False,
                'error': 'Professor não encontrado'
            }), 404

        # Verificar se tem disciplinas atribuídas
        disciplines_count = Discipline.query.filter_by(professor_id=professor_id).count()
        if disciplines_count > 0:
            return jsonify({
                'success': False,
                'error': f'Não é possível excluir professor com {disciplines_count} disciplina(s) atribuída(s)'
            }), 400

        user = professor.user

        # Excluir professor e usuário
        db.session.delete(professor)
        db.session.delete(user)
        db.session.commit()

        return jsonify({
            'success': True,
            'message': 'Professor excluído com sucesso'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir professor: {str(e)}'
        }), 500


# ========== LISTAGEM ADMINISTRATIVA ==========

@professor_bp.route('/admin/professors', methods=['GET'])
@teacher_or_admin_required
def get_all_professors():
    """Lista todos os professores (admin)"""
    try:
        print("🔍 DEBUG: Iniciando get_all_professors")

        professors = Professor.query.all()
        print(f"🔍 DEBUG: Encontrados {len(professors)} professores")

        professors_data = []
        for professor in professors:
            try:
                print(f"🔍 DEBUG: Processando professor {professor.id} - {professor.nome}")

                # USAR to_dict() para garantir todos os campos
                professor_dict = professor.to_dict()

                # Adicionar informações extras se necessário
                professor_dict['username'] = professor_dict.get('cpf', 'N/A')  # CPF é o username

                professors_data.append(professor_dict)
                print(f"✅ DEBUG: Professor {professor.id} processado: {professor.nome} - CPF: {professor.cpf}")

            except Exception as e:
                print(f"❌ DEBUG: Erro ao processar professor {professor.id}: {e}")
                import traceback
                traceback.print_exc()

                # Fallback manual
                professors_data.append({
                    'id': professor.id,
                    'nome': getattr(professor, 'nome', 'Erro'),
                    'cpf': getattr(professor, 'cpf', 'N/A'),
                    'departamento': getattr(professor, 'departamento', 'Erro'),
                    'anos_turmas': getattr(professor, 'anos_turmas', None),
                    'niveis_ensino': getattr(professor, 'niveis_ensino', None),
                    'user_id': professor.user_id,
                    'error': str(e)
                })

        print(f"🔍 DEBUG: Retornando {len(professors_data)} professores")

        return jsonify({
            'success': True,
            'professors': professors_data
        })

    except Exception as e:
        print(f"❌ DEBUG: Erro geral em get_all_professors: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'Erro interno: {str(e)}'}), 500


# ========== DASHBOARD DO PROFESSOR ==========

@professor_bp.route('/teacher/dashboard', methods=['GET'])
@teacher_required
def get_teacher_dashboard():
    """Carregar dados do dashboard do professor"""
    try:
        current_user = User.query.get(session['user_id'])
        professor = Professor.query.filter_by(user_id=current_user.id).first()

        if not professor:
            return jsonify({
                'success': False,
                'error': 'Perfil de professor não encontrado'
            }), 404

        print(f"🔍 Carregando dashboard para professor: {professor.nome}")

        # Buscar disciplinas do professor
        disciplines = Discipline.query.filter_by(professor_id=professor.id).all()
        print(f"📚 Disciplinas encontradas: {len(disciplines)}")

        # Preparar dados das disciplinas
        disciplines_data = []
        total_students = 0
        total_xp_distributed = 0

        for discipline in disciplines:
            try:
                # Contar alunos matriculados ativos
                student_count = Enrollment.query.filter_by(
                    discipline_id=discipline.id,
                    status='active'
                ).count()

                # Contar atividades
                activities_count = 0
                try:
                    activities_count = db.session.query(func.count(AcademicMission.id)) \
                        .filter(AcademicMission.discipline_id == discipline.id) \
                        .scalar() or 0
                except Exception as e:
                    print(f"⚠️ Erro ao contar atividades da disciplina {discipline.id}: {e}")
                    activities_count = 0

                # Calcular XP
                total_discipline_xp = 0
                try:
                    xp_result = db.session.query(func.sum(AcademicMission.xp_reward)) \
                        .filter(AcademicMission.discipline_id == discipline.id) \
                        .scalar()
                    total_discipline_xp = xp_result if xp_result else 0
                except Exception as e:
                    print(f"⚠️ Erro ao calcular XP da disciplina {discipline.id}: {e}")
                    total_discipline_xp = 0

                average_xp = total_discipline_xp // max(student_count, 1) if student_count > 0 else 0

                disciplines_data.append({
                    'id': discipline.id,
                    'nome': discipline.nome,
                    'codigo': discipline.codigo,
                    'carga_horaria': discipline.carga_horaria,
                    'ano_turma': discipline.ano_turma,
                    'studentCount': student_count,
                    'activitiesCount': activities_count,
                    'average_xp': average_xp
                })

                total_students += student_count
                total_xp_distributed += total_discipline_xp

            except Exception as e:
                print(f"❌ Erro ao processar disciplina {discipline.id}: {e}")
                continue

        # Atividades recentes
        recent_activities = []
        try:
            discipline_ids = [d.id for d in disciplines]
            if discipline_ids:
                recent_missions = db.session.query(
                    AcademicMission.id,
                    AcademicMission.mission_type,
                    AcademicMission.discipline_id,
                    AcademicMission.xp_reward,
                    AcademicMission.created_at,
                    AcademicMission.due_date
                ).filter(
                    AcademicMission.discipline_id.in_(discipline_ids)
                ).order_by(
                    AcademicMission.created_at.desc()
                ).limit(5).all()

                for mission in recent_missions:
                    discipline = Discipline.query.get(mission.discipline_id)
                    discipline_name = discipline.nome if discipline else "Sem disciplina"
                    titulo = f"{mission.mission_type.capitalize()} - {discipline_name}"

                    status = 'publicada'
                    if mission.due_date:
                        if datetime.now().date() > mission.due_date:
                            status = 'corrigindo'

                    recent_activities.append({
                        'id': mission.id,
                        'titulo': titulo,
                        'disciplina': discipline_name,
                        'tipo': mission.mission_type,
                        'xp': mission.xp_reward,
                        'status': status
                    })

        except Exception as e:
            print(f"⚠️ Erro ao carregar atividades recentes: {e}")
            import traceback
            traceback.print_exc()
            recent_activities = []

        # Calcular estatísticas
        statistics = {
            'total_students': total_students,
            'total_xp_distributed': total_xp_distributed,
            'pending_corrections': 0  # TODO: implementar contagem real
        }

        # Dados completos do professor
        teacher_data = {
            'teacher': {
                'nome': professor.nome,
                'cpf': professor.cpf,
                'departamento': professor.departamento,
                'disciplinas_count': len(disciplines)
            },
            'disciplines': disciplines_data,
            'recent_activities': recent_activities,
            'statistics': statistics
        }

        print(f"✅ Dashboard carregado com sucesso!")

        return jsonify({
            'success': True,
            'data': teacher_data
        })

    except Exception as e:
        print(f"❌ Erro crítico ao carregar dashboard: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': f'Erro interno do servidor: {str(e)}'
        }), 500


# ========== ROTAS DE DEBUG ==========

@professor_bp.route('/debug/professors', methods=['GET'])
def debug_professors():
    """Rota de debug para verificar professores"""
    try:
        professors = Professor.query.all()
        result = []

        for professor in professors:
            result.append({
                'id': professor.id,
                'nome': professor.nome,
                'cpf': professor.cpf,
                'departamento': professor.departamento,
                'anos_turmas': professor.anos_turmas if hasattr(professor, 'anos_turmas') else None,
                'user_id': professor.user_id,
                'has_user': bool(User.query.get(professor.user_id))
            })

        return jsonify({
            'success': True,
            'count': len(result),
            'professors': result
        })

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
