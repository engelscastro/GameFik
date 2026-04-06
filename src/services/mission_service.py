# src/services/mission_service.py
"""
Service Layer para Missões - Lógica de Negócio
Responsável por toda a lógica de gamificação de missões.
Desacoplado do Flask HTTP - reutilizável em qualquer contexto.

Métodos:
  - get_all_missions(): Listar todas as missões ativas
  - get_all_missions_admin(): Listar TODAS as missões (admin)
  - get_available_missions(): Missões disponíveis para usuário
  - create_mission(): Criar nova missão (admin)
  - update_mission(): Atualizar missão (admin)
  - delete_mission(): Deletar missão (admin)
  - get_mission_details(): Obter detalhes de uma missão
  - complete_mission(): Completar uma missão (lógica complexa)
  - assign_mission_bulk(): Atribuir a múltiplos alunos
  - assign_mission(): Atribuir a um aluno
  - get_user_missions(): Missões de um usuário
  - get_user_pending_missions(): Missões pendentes
  - get_user_completed_missions(): Missões completadas
"""

from datetime import datetime
from src.models.user import User, UserMission, Mission, Achievement, UserAchievement, db
from src.models.academic import Student, Discipline, Enrollment


# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class MissionNotFound(Exception):
    """Exceção quando missão não é encontrada"""
    pass


class MissionAlreadyCompleted(Exception):
    """Exceção quando missão já foi completada"""
    pass


class MissionAlreadyAssigned(Exception):
    """Exceção quando missão já foi atribuída"""
    pass


class InvalidUser(Exception):
    """Exceção quando usuário não é válido"""
    pass


class UnauthorizedAccess(Exception):
    """Exceção quando acesso não é autorizado"""
    pass


# ============================================================================
# MISSION SERVICE
# ============================================================================

class MissionService:
    """Service para gerenciar missões e gamificação"""
    
    # ========================================================================
    # LEITURA - Missões
    # ========================================================================
    
    @staticmethod
    def get_all_missions():
        """
        Obter todas as missões ATIVAS
        
        Returns:
            list: Lista de missões ativas em formato dict
        """
        missions = Mission.query.filter_by(is_active=True).all()
        return [mission.to_dict() for mission in missions]
    
    @staticmethod
    def get_all_missions_admin():
        """
        Obter TODAS as missões (admin)
        
        Returns:
            list: Lista de todas as missões
        """
        missions = Mission.query.all()
        return [mission.to_dict() for mission in missions]
    
    @staticmethod
    def get_available_missions(user_id):
        """
        Obter missões DISPONÍVEIS para um usuário
        (missões que ele ainda não tem)
        
        Args:
            user_id: ID do usuário
            
        Returns:
            list: Missões disponíveis
        """
        # Missões que o usuário já tem
        user_mission_ids = [
            um.mission_id for um in UserMission.query.filter_by(
                user_id=user_id
            ).all()
        ]
        
        # Missões ativas que não estão na lista do usuário
        available_missions = Mission.query.filter(
            Mission.is_active == True,
            (Mission.id.notin_(user_mission_ids) 
             if user_mission_ids 
             else True)
        ).all()
        
        return [mission.to_dict() for mission in available_missions]
    
    @staticmethod
    def get_mission_details(mission_id):
        """
        Obter detalhes completos de uma missão
        
        Args:
            mission_id: ID da missão
            
        Returns:
            dict: Detalhes da missão
            
        Raises:
            MissionNotFound: Se missão não existe
        """
        mission = Mission.query.get(mission_id)
        if not mission:
            raise MissionNotFound(f"Missão {mission_id} não encontrada")
        return mission.to_dict()
    
    @staticmethod
    def get_user_missions(user_id):
        """
        Obter TODAS as missões de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            list: Missões do usuário
        """
        user_missions = UserMission.query.filter_by(user_id=user_id).all()
        return [um.to_dict() for um in user_missions]
    
    @staticmethod
    def get_user_pending_missions(user_id):
        """
        Obter MISSÕES PENDENTES de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            list: Missões pendentes (status='pending')
        """
        pending_missions = UserMission.query.filter_by(
            user_id=user_id,
            status='pending'
        ).all()
        return [um.to_dict() for um in pending_missions]
    
    @staticmethod
    def get_user_completed_missions(user_id):
        """
        Obter MISSÕES COMPLETADAS de um usuário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            list: Missões completadas (status='completed')
        """
        completed_missions = UserMission.query.filter_by(
            user_id=user_id,
            status='completed'
        ).all()
        return [um.to_dict() for um in completed_missions]
    
    # ========================================================================
    # CRIACAO/ATUALIZACAO/DELECAO - Missões
    # ========================================================================
    
    @staticmethod
    def create_mission(data, created_by_user_id):
        """
        Criar NOVA missão (admin/professor)
        
        Args:
            data: Dict com:
                - name: Nome (obrigatório)
                - description: Descrição
                - xp_reward: XP a ganhar (default: 0)
                - coin_reward: Coins a ganhar (default: 0)
            created_by_user_id: ID do criador
            
        Returns:
            dict: Missão criada
            
        Raises:
            ValueError: Se dados inválidos
        """
        if not data.get('name'):
            raise ValueError('Nome da missão é obrigatório')
        
        mission = Mission(
            name=data.get('name'),
            description=data.get('description', ''),
            xp_reward=data.get('xp_reward', 0),
            coin_reward=data.get('coin_reward', 0),
            created_by=created_by_user_id,
            is_active=True
        )
        
        db.session.add(mission)
        db.session.commit()
        
        return mission.to_dict()
    
    @staticmethod
    def update_mission(mission_id, data):
        """
        Atualizar missão existente (admin)
        
        Args:
            mission_id: ID da missão
            data: Dict com dados a atualizar
                - name
                - description
                - xp_reward
                - coin_reward
                - is_active
            
        Returns:
            dict: Missão atualizada
            
        Raises:
            MissionNotFound: Se missão não existe
        """
        mission = Mission.query.get(mission_id)
        if not mission:
            raise MissionNotFound(f"Missão {mission_id} não encontrada")
        
        if 'name' in data:
            mission.name = data['name']
        if 'description' in data:
            mission.description = data['description']
        if 'xp_reward' in data:
            mission.xp_reward = data['xp_reward']
        if 'coin_reward' in data:
            mission.coin_reward = data['coin_reward']
        if 'is_active' in data:
            mission.is_active = data['is_active']
        
        db.session.commit()
        
        return mission.to_dict()
    
    @staticmethod
    def delete_mission(mission_id):
        """
        Deletar missão (admin)
        Só pode deletar se nenhum usuário tem essa missão
        
        Args:
            mission_id: ID da missão
            
        Returns:
            dict: Status
            
        Raises:
            MissionNotFound: Se missão não existe
            ValueError: Se usuários têm essa missão
        """
        mission = Mission.query.get(mission_id)
        if not mission:
            raise MissionNotFound(f"Missão {mission_id} não encontrada")
        
        # Verificar se há usuários com essa missão
        user_count = UserMission.query.filter_by(mission_id=mission_id).count()
        if user_count > 0:
            raise ValueError(
                f'Não é possível excluir missão com {user_count} usuários atribuídos'
            )
        
        db.session.delete(mission)
        db.session.commit()
        
        return {'success': True, 'message': 'Missão deletada com sucesso'}
    
    # ========================================================================
    # ATRIBUICAO - Missões
    # ========================================================================
    
    @staticmethod
    def assign_mission(user_id, mission_id):
        """
        Atribuir MISSÃO A UM USUÁRIO
        
        Args:
            user_id: ID do usuário
            mission_id: ID da missão
            
        Returns:
            dict: UserMission criado
            
        Raises:
            InvalidUser: Se usuário não é estudante
            MissionNotFound: Se missão não existe
            MissionAlreadyAssigned: Se já tem essa missão
        """
        # Validar usuário
        user = User.query.get(user_id)
        if not user or user.role != 'student':
            raise InvalidUser('Só é possível atribuir missões a estudantes')
        
        # Validar missão
        mission = Mission.query.get(mission_id)
        if not mission:
            raise MissionNotFound(f"Missão {mission_id} não encontrada")
        
        # Verificar se já existe
        existing = UserMission.query.filter_by(
            user_id=user_id,
            mission_id=mission_id
        ).first()
        if existing:
            raise MissionAlreadyAssigned(
                'Missão já atribuída a este estudante'
            )
        
        # Criar atribuição
        user_mission = UserMission(
            user_id=user_id,
            mission_id=mission_id,
            status='pending'
        )
        
        db.session.add(user_mission)
        db.session.commit()
        
        return user_mission.to_dict()
    
    @staticmethod
    def assign_mission_bulk(mission_id, student_ids, current_user_id):
        """
        Atribuir MISSÃO A MÚLTIPLOS ESTUDANTES de uma vez
        Com validação de permissões e integridade
        
        Args:
            mission_id: ID da missão
            student_ids: Lista de IDs de estudantes
            current_user_id: ID do professor/admin fazendo atribuição
            
        Returns:
            dict: {
                'success': True,
                'success_count': int,
                'error_count': int,
                'results': [
                    {'student_id': int, 'status': 'success' or 'error', 'message': str}
                ]
            }
        """
        mission = Mission.query.get(mission_id)
        if not mission:
            raise MissionNotFound(f"Missão {mission_id} não encontrada")
        
        current_user = User.query.get(current_user_id)
        
        success_count = 0
        error_count = 0
        results = []
        
        for student_id in student_ids:
            try:
                # Validar estudante
                student_user = User.query.get(student_id)
                if not student_user or student_user.role != 'student':
                    results.append({
                        'student_id': student_id,
                        'status': 'error',
                        'message': 'Usuário não é estudante'
                    })
                    error_count += 1
                    continue
                
                # Se professor: validar permissão
                if current_user.role == 'teacher':
                    teacher_disciplines = Discipline.query.filter_by(
                        professor_id=current_user_id
                    ).all()
                    
                    if not teacher_disciplines:
                        results.append({
                            'student_id': student_id,
                            'status': 'error',
                            'message': 'Professor sem disciplinas atribuídas'
                        })
                        error_count += 1
                        continue
                    
                    # Validar se estudante está numa disciplina do professor
                    student_profile = Student.query.filter_by(
                        user_id=student_id
                    ).first()
                    
                    if not student_profile:
                        results.append({
                            'student_id': student_id,
                            'status': 'error',
                            'message': 'Perfil de estudante não encontrado'
                        })
                        error_count += 1
                        continue
                    
                    discipline_ids = [d.id for d in teacher_disciplines]
                    enrollment = Enrollment.query.filter(
                        Enrollment.student_id == student_profile.id,
                        Enrollment.discipline_id.in_(discipline_ids),
                        Enrollment.status == 'active'
                    ).first()
                    
                    if not enrollment:
                        results.append({
                            'student_id': student_id,
                            'status': 'error',
                            'message': 'Estudante não está em nenhuma disciplina do professor'
                        })
                        error_count += 1
                        continue
                
                # Verificar se já tem
                existing = UserMission.query.filter_by(
                    user_id=student_id,
                    mission_id=mission_id
                ).first()
                
                if existing:
                    results.append({
                        'student_id': student_id,
                        'status': 'error',
                        'message': 'Missão já atribuída'
                    })
                    error_count += 1
                    continue
                
                # Atribuir
                user_mission = UserMission(
                    user_id=student_id,
                    mission_id=mission_id,
                    status='pending'
                )
                
                db.session.add(user_mission)
                success_count += 1
                
                results.append({
                    'student_id': student_id,
                    'status': 'success',
                    'message': 'Missão atribuída'
                })
                
            except Exception as e:
                error_count += 1
                results.append({
                    'student_id': student_id,
                    'status': 'error',
                    'message': str(e)
                })
        
        db.session.commit()
        
        return {
            'success': True,
            'message': f'Missão atribuída a {success_count} estudantes! ({error_count} erros)',
            'success_count': success_count,
            'error_count': error_count,
            'results': results
        }
    
    # ========================================================================
    # COMPLETACAO - Missões (LOGICA COMPLEXA)
    # ========================================================================
    
    @staticmethod
    def complete_mission(user_mission_id, user_id):
        """
        COMPLETAR UMA MISSÃO - LÓGICA COMPLEXA
        
        Handles:
        - Marcar como completa
        - Ganhar XP
        - Ganhar Coins
        - Verificar level up
        - Verificar novas conquistas
        - Verificar novas recompensas
        
        Args:
            user_mission_id: ID da atribuição de missão (UserMission)
            user_id: ID do usuário (para validação)
            
        Returns:
            dict: {
                'success': True,
                'level_up': bool,
                'xp_earned': int,
                'coins_earned': int,
                'new_achievements': [...],
                'new_rewards': [...]
            }
            
        Raises:
            MissionNotFound: Se UserMission não existe
            MissionAlreadyCompleted: Se já foi completada
        """
        # Buscar atribuição de missão
        user_mission = UserMission.query.filter_by(
            id=user_mission_id,
            user_id=user_id
        ).first()
        
        if not user_mission:
            raise MissionNotFound('Missão do usuário não encontrada')
        
        # Validar se já foi completada
        if user_mission.status == 'completed':
            raise MissionAlreadyCompleted('Missão já foi completada')
        
        # Obter usuário e missão
        user = User.query.get(user_id)
        mission = user_mission.mission
        
        # ====================================================================
        # ETAPA 1: Marcar como completa
        # ====================================================================
        user_mission.status = 'completed'
        user_mission.completion_date = datetime.utcnow()
        db.session.commit()
        
        # ====================================================================
        # ETAPA 2: Ganhar XP e Coins
        # ====================================================================
        xp_earned = mission.xp_reward
        coins_earned = mission.coin_reward
        
        old_level = user.level
        
        user.current_xp += xp_earned
        user.current_coins += coins_earned
        
        # Calcular novo level (a cada 100 XP = 1 level)
        user.current_level = user.current_xp // 100
        
        db.session.commit()
        
        level_up = user.current_level > old_level
        
        # ====================================================================
        # ETAPA 3: Verificar conquistas desbloqueadas
        # ====================================================================
        from src.services.achievement_service import AchievementService
        new_achievements = AchievementService.check_achievements(user_id)
        
        # ====================================================================
        # ETAPA 4: Verificar recompensas desbloqueadas
        # ====================================================================
        from src.services.reward_service import RewardService
        new_rewards = RewardService.check_rewards(user_id)
        
        # ====================================================================
        # RETORNO
        # ====================================================================
        return {
            'success': True,
            'message': 'Missão completada com sucesso!',
            'level_up': level_up,
            'old_level': old_level,
            'new_level': user.current_level,
            'xp_earned': xp_earned,
            'total_xp': user.current_xp,
            'coins_earned': coins_earned,
            'total_coins': user.current_coins,
            'new_achievements': new_achievements,
            'new_rewards': new_rewards
        }


# ============================================================================
# UTILS HELPER FUNCTIONS
# ============================================================================

def get_teacher_students(teacher_id):
    """
    Obter TODOS OS ESTUDANTES das disciplinas de um professor
    
    Args:
        teacher_id: ID do professor
        
    Returns:
        dict: {
            'students': [...],
            'total_students': int,
            'total_disciplines': int
        }
    """
    # Buscar disciplinas do professor
    teacher_disciplines = Discipline.query.filter_by(professor_id=teacher_id).all()
    
    if not teacher_disciplines:
        return {
            'students': [],
            'total_disciplines': 0,
            'total_students': 0
        }
    
    discipline_ids = [d.id for d in teacher_disciplines]
    
    # Buscar matrículas ativas nessas disciplinas
    enrollments = Enrollment.query.filter(
        Enrollment.discipline_id.in_(discipline_ids),
        Enrollment.status == 'active'
    ).all()
    
    # Montar lista de estudantes
    students_data = []
    student_ids = set()
    
    for enrollment in enrollments:
        if enrollment.student_id not in student_ids:
            student = Student.query.get(enrollment.student_id)
            if student and hasattr(student, 'user') and student.user:
                student_ids.add(enrollment.student_id)
                
                # Disciplinas deste estudante
                student_disciplines = []
                for disc in teacher_disciplines:
                    student_enrollment = Enrollment.query.filter_by(
                        student_id=student.id,
                        discipline_id=disc.id,
                        status='active'
                    ).first()
                    
                    if student_enrollment:
                        student_disciplines.append({
                            'id': disc.id,
                            'nome': disc.nome,
                            'codigo': disc.codigo
                        })
                
                students_data.append({
                    'user_id': student.user_id,
                    'student_id': student.id,
                    'nome': student.nome,
                    'matricula': student.matricula,
                    'cpf': student.cpf,
                    'curso': student.curso,
                    'ano_turma': student.ano_turma,
                    'disciplines': student_disciplines
                })
    
    return {
        'students': students_data,
        'total_students': len(students_data),
        'total_disciplines': len(teacher_disciplines),
        'teacher_disciplines': [
            {'id': d.id, 'nome': d.nome}
            for d in teacher_disciplines
        ]
    }


def get_teacher_disciplines(teacher_id):
    """
    Obter TODAS AS DISCIPLINAS de um professor com estatísticas
    
    Args:
        teacher_id: ID do professor
        
    Returns:
        dict: {
            'disciplines': [...],
            'total_disciplines': int,
            'total_enrolled_students': int
        }
    """
    teacher_disciplines = Discipline.query.filter_by(professor_id=teacher_id).all()
    
    disciplines_data = []
    total_students = 0
    
    for discipline in teacher_disciplines:
        enrolled_count = Enrollment.query.filter_by(
            discipline_id=discipline.id,
            status='active'
        ).count()
        
        discipline_dict = discipline.to_dict()
        discipline_dict['enrolled_students'] = enrolled_count
        
        disciplines_data.append(discipline_dict)
        total_students += enrolled_count
    
    return {
        'disciplines': disciplines_data,
        'total_disciplines': len(disciplines_data),
        'total_enrolled_students': total_students
    }
