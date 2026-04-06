# discipline.py
"""
Blueprint para gerenciamento de disciplinas
Responsável por operações CRUD de disciplinas, atribuição de professores,
listagem de disciplinas disponíveis e verificação de exclusão.
"""

from datetime import datetime
from flask import Blueprint, request, jsonify, session
from sqlalchemy import func

from src.models.academic import Discipline, Professor, Enrollment, AcademicMission
from src.models.user import db, User
from .utils import login_required, teacher_or_admin_required

# Criar blueprint
discipline_bp = Blueprint('discipline', __name__)


# ========== DISCIPLINAS - CRUD ==========

@discipline_bp.route('/disciplines', methods=['GET'])
@login_required
def get_disciplines():
    """Listar todas as disciplinas"""
    try:
        disciplines = Discipline.query.all()
        
        # Debug: verificar se os professores estão sendo carregados
        for discipline in disciplines:
            print(f"🔍 Disciplina: {discipline.nome}, Professor ID: {discipline.professor_id}")
            if discipline.professor:
                print(f"  ✅ Professor encontrado: {discipline.professor.nome}")
            else:
                print(f"  ❌ Professor NÃO encontrado para ID: {discipline.professor_id}")
        
        return jsonify({
            'success': True,
            'disciplines': [discipline.to_dict() for discipline in disciplines]
        })
    except Exception as e:
        print(f"❌ Erro ao carregar disciplinas: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discipline_bp.route('/disciplines', methods=['POST'])
@teacher_or_admin_required
def create_discipline():
    """Criar nova disciplina"""
    try:
        current_user = User.query.get(session['user_id'])
        data = request.json
        
        # Validação dos campos obrigatórios
        required_fields = ['codigo', 'nome', 'carga_horaria']
        for field in required_fields:
            if not data.get(field):
                return jsonify({
                    'success': False,
                    'error': f'Campo {field} é obrigatório'
                }), 400
        
        # Verificar se código já existe
        existing_discipline = Discipline.query.filter_by(codigo=data['codigo']).first()
        if existing_discipline:
            return jsonify({
                'success': False,
                'error': 'Já existe uma disciplina com este código'
            }), 400
        
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
            'discipline': discipline.to_dict()
        }), 201
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao criar disciplina: {str(e)}'
        }), 500


@discipline_bp.route('/disciplines/<int:discipline_id>', methods=['DELETE'])
@teacher_or_admin_required
def delete_discipline(discipline_id):
    """Excluir disciplina com tratamento de dependências"""
    try:
        current_user = User.query.get(session['user_id'])
        discipline = Discipline.query.get(discipline_id)
        
        if not discipline:
            return jsonify({
                'success': False,
                'error': 'Disciplina não encontrada'
            }), 404
        
        # Verificar se há matrículas ativas
        active_enrollments = Enrollment.query.filter_by(
            discipline_id=discipline_id,
            status='active'
        ).count()
        
        if active_enrollments > 0:
            return jsonify({
                'success': False,
                'error': f'Não é possível excluir disciplina com {active_enrollments} matrícula(s) ativa(s)'
            }), 400
        
        # Excluir missões acadêmicas vinculadas
        academic_missions = AcademicMission.query.filter_by(discipline_id=discipline_id).all()
        if academic_missions:
            for mission in academic_missions:
                db.session.delete(mission)
            print(f"🗑️ Excluídas {len(academic_missions)} missões acadêmicas vinculadas")
        
        # Excluir a disciplina
        db.session.delete(discipline)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Disciplina excluída com sucesso'
        })
    
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erro ao excluir disciplina {discipline_id}: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Erro ao excluir disciplina: {str(e)}'
        }), 500


# ========== ATRIBUIÇÃO DE PROFESSORES ==========

@discipline_bp.route('/disciplines/<int:discipline_id>/assign-professor', methods=['POST'])
@teacher_or_admin_required
def assign_professor_to_discipline(discipline_id):
    """Atribuir ou remover professor de uma disciplina"""
    try:
        data = request.json
        professor_id = data.get('professor_id')
        
        # Verificar se disciplina existe
        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({
                'success': False,
                'error': 'Disciplina não encontrada'
            }), 404
        
        # Se professor_id for fornecido, verificar se existe
        if professor_id:
            professor = Professor.query.get(professor_id)
            if not professor:
                return jsonify({
                    'success': False,
                    'error': 'Professor não encontrado'
                }), 404
        
        # Atribuir professor (pode ser None para remover atribuição)
        discipline.professor_id = professor_id
        db.session.commit()
        
        # Recarregar dados atualizados
        db.session.refresh(discipline)
        
        action = "atribuído" if professor_id else "removido"
        return jsonify({
            'success': True,
            'message': f'Professor {action} com sucesso',
            'discipline': discipline.to_dict()
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'error': f'Erro ao atribuir professor: {str(e)}'
        }), 500


# ========== CONSULTAS ESPECIALIZADAS ==========

@discipline_bp.route('/disciplines-with-professors', methods=['GET'])
@login_required
def get_disciplines_with_professors():
    """Listar disciplinas com informações detalhadas dos professores"""
    try:
        disciplines = Discipline.query.all()
        result = []
        
        for discipline in disciplines:
            discipline_dict = discipline.to_dict()
            
            # Enriquecer com dados do professor se não estiver presente
            if discipline.professor_id and not discipline_dict.get('professor_nome'):
                professor = Professor.query.get(discipline.professor_id)
                if professor:
                    discipline_dict['professor_nome'] = professor.nome
                    discipline_dict['professor_departamento'] = professor.departamento
            
            result.append(discipline_dict)
        
        return jsonify({
            'success': True,
            'disciplines': result
        })
    
    except Exception as e:
        print(f"❌ Erro ao carregar disciplinas com professores: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discipline_bp.route('/disciplines/available', methods=['GET'])
@login_required
def get_available_disciplines():
    """Listar disciplinas disponíveis para matrícula do estudante logado"""
    try:
        from src.models.academic import Student
        
        # Verificar se é estudante
        student = Student.query.filter_by(user_id=session['user_id']).first()
        if not student:
            return jsonify({
                'success': False,
                'error': 'Perfil de estudante não encontrado'
            }), 404
        
        # Buscar disciplinas do mesmo ano/turma do estudante
        available_disciplines = Discipline.query.filter(
            Discipline.ano_turma == student.ano_turma
        ).all()
        
        # Buscar matrículas atuais do estudante
        current_enrollments = Enrollment.query.filter_by(
            student_id=student.id,
            status='active'
        ).all()
        
        enrolled_discipline_ids = [e.discipline_id for e in current_enrollments]
        
        # Filtrar disciplinas não matriculadas
        filtered_disciplines = [
            discipline for discipline in available_disciplines
            if discipline.id not in enrolled_discipline_ids
        ]
        
        return jsonify({
            'success': True,
            'disciplines': [discipline.to_dict() for discipline in filtered_disciplines],
            'student_ano_turma': student.ano_turma,
            'total_available': len(filtered_disciplines)
        })
    
    except Exception as e:
        print(f"❌ Erro ao carregar disciplinas disponíveis: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@discipline_bp.route('/disciplines/<int:discipline_id>/can-delete', methods=['GET'])
@teacher_or_admin_required
def can_delete_discipline(discipline_id):
    """Verificar se a disciplina pode ser excluída"""
    try:
        discipline = Discipline.query.get(discipline_id)
        
        if not discipline:
            return jsonify({
                'success': True,
                'can_delete': False,
                'reason': 'Disciplina não encontrada'
            })
        
        # Verificar matrículas ativas
        active_enrollments = Enrollment.query.filter_by(
            discipline_id=discipline_id,
            status='active'
        ).count()
        
        # Verificar missões acadêmicas
        academic_missions = AcademicMission.query.filter_by(
            discipline_id=discipline_id
        ).count()
        
        can_delete = active_enrollments == 0
        reasons = []
        
        if active_enrollments > 0:
            reasons.append(f'{active_enrollments} matrícula(s) ativa(s)')
        if academic_missions > 0:
            reasons.append(f'{academic_missions} missão(ões) acadêmica(s) vinculada(s)')
        
        return jsonify({
            'success': True,
            'can_delete': can_delete,
            'reasons': reasons,
            'details': {
                'active_enrollments': active_enrollments,
                'academic_missions': academic_missions
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@discipline_bp.route('/disciplines/<int:discipline_id>/reload', methods=['GET'])
@login_required
def reload_discipline(discipline_id):
    """Recarregar disciplina com relacionamentos"""
    try:
        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            return jsonify({
                'success': False,
                'error': 'Disciplina não encontrada'
            }), 404
        
        professor_name = None
        if discipline.professor_id:
            professor = Professor.query.get(discipline.professor_id)
            professor_name = professor.nome if professor else None
        
        return jsonify({
            'success': True,
            'discipline': {
                'id': discipline.id,
                'nome': discipline.nome,
                'professor_id': discipline.professor_id,
                'professor_nome': professor_name,
                'carregado_via_query': True
            }
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ========== ROTAS DE DEBUG ==========

@discipline_bp.route('/debug/disciplines-with-professors', methods=['GET'])
@login_required
def debug_disciplines_with_professors():
    """Rota de debug para verificar disciplinas e professores"""
    try:
        disciplines = Discipline.query.all()
        result = []
        
        for discipline in disciplines:
            professor_info = None
            if discipline.professor_id:
                professor = Professor.query.get(discipline.professor_id)
                if professor:
                    professor_info = {
                        'id': professor.id,
                        'nome': professor.nome,
                        'departamento': professor.departamento
                    }
            
            result.append({
                'disciplina_id': discipline.id,
                'disciplina_nome': discipline.nome,
                'professor_id': discipline.professor_id,
                'professor_info': professor_info,
                'tem_professor': bool(discipline.professor_id and professor_info)
            })
        
        return jsonify({
            'success': True,
            'disciplines': result,
            'total': len(result),
            'com_professor': len([d for d in result if d['tem_professor']])
        })
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
