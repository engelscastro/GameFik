# src/services/achievement_service.py
"""
Service Layer para Conquistas - Lógica de Negócio
Responsável por toda a lógica de gamificação de conquistas.
Desacoplado do Flask HTTP - reutilizável em qualquer contexto.

Métodos:
  - get_all_achievements(): Listar todas as conquistas
  - create_achievement(): Criar nova conquista (admin)
  - update_achievement(): Atualizar conquista (admin)
  - delete_achievement(): Deletar conquista (admin)
  - get_user_achievements(): Obter conquistas do usuário
  - get_user_achievement_progress(): Progresso para próxima conquista
  - check_achievements(): Verificar novas conquistas desbloqueadas
  - award_achievement(): Atribuir conquista a usuário
"""

from datetime import datetime
from src.models.user import User, Achievement, UserAchievement, db


# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class AchievementNotFound(Exception):
    """Exceção quando conquista não é encontrada"""
    pass


class AchievementAlreadyAwarded(Exception):
    """Exceção quando conquista já foi atribuída"""
    pass


class InvalidAchievementData(Exception):
    """Exceção quando dados são inválidos"""
    pass


# ============================================================================
# ACHIEVEMENT SERVICE
# ============================================================================

class AchievementService:
    """Service para gerenciar conquistas e progressão do usuário"""
    
    # ========================================================================
    # LEITURA - Conquistas
    # ========================================================================
    
    @staticmethod
    def get_all_achievements():
        """Obter todas as conquistas disponíveis"""
        achievements = Achievement.query.all()
        return [achievement.to_dict() for achievement in achievements]
    
    @staticmethod
    def get_user_achievements(user_id):
        """Obter conquistas que o usuário já desbloqueou"""
        user_achievements = UserAchievement.query.filter_by(
            user_id=user_id
        ).all()
        return [ua.to_dict() for ua in user_achievements]
    
    @staticmethod
    def get_user_achievement_progress(user_id):
        """Obter progresso do usuário para próximas conquistas"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        # Obter todas as conquistas
        all_achievements = Achievement.query.all()
        
        # Obter conquistas já ganhas
        earned_achievement_ids = [
            ua.achievement_id 
            for ua in UserAchievement.query.filter_by(user_id=user_id).all()
        ]
        
        progress = []
        
        for achievement in all_achievements:
            is_earned = achievement.id in earned_achievement_ids
            progress_data = achievement.to_dict()
            progress_data['earned'] = is_earned
            
            if not is_earned:
                # Calcular progresso para conquistas não ganhas
                if achievement.xp_threshold:
                    progress_pct = min(100, (user.current_xp / achievement.xp_threshold) * 100)
                    progress_data['progress'] = progress_pct
                    progress_data['target'] = achievement.xp_threshold
                    progress_data['current'] = user.current_xp
                
                if achievement.level_threshold:
                    progress_pct = min(100, (user.current_level / achievement.level_threshold) * 100)
                    progress_data['progress'] = progress_pct
                    progress_data['target'] = achievement.level_threshold
                    progress_data['current'] = user.current_level
                
                if achievement.mission_count_threshold:
                    completed_missions = db.session.query(
                        db.func.count(db.distinct('UserMission.id'))
                    ).filter(
                        db.UserMission.user_id == user_id,
                        db.UserMission.status == 'completed'
                    ).scalar()
                    
                    progress_pct = min(100, (completed_missions / achievement.mission_count_threshold) * 100)
                    progress_data['progress'] = progress_pct
                    progress_data['target'] = achievement.mission_count_threshold
                    progress_data['current'] = completed_missions
            
            progress.append(progress_data)
        
        return progress
    
    # ========================================================================
    # CRIACAO/ATUALIZACAO/DELECAO - Conquistas
    # ========================================================================
    
    @staticmethod
    def create_achievement(data):
        """Criar nova conquista (admin)"""
        if not data.get('name'):
            raise InvalidAchievementData('Nome da conquista é obrigatório')
        
        achievement = Achievement(
            name=data.get('name'),
            description=data.get('description', ''),
            icon=data.get('icon', '🏆'),
            xp_threshold=data.get('xp_threshold'),
            level_threshold=data.get('level_threshold'),
            mission_count_threshold=data.get('mission_count_threshold')
        )
        
        db.session.add(achievement)
        db.session.commit()
        
        return achievement.to_dict()
    
    @staticmethod
    def update_achievement(achievement_id, data):
        """Atualizar conquista (admin)"""
        achievement = Achievement.query.get(achievement_id)
        if not achievement:
            raise AchievementNotFound(f"Conquista {achievement_id} não encontrada")
        
        if 'name' in data:
            achievement.name = data['name']
        if 'description' in data:
            achievement.description = data['description']
        if 'icon' in data:
            achievement.icon = data['icon']
        if 'xp_threshold' in data:
            achievement.xp_threshold = data['xp_threshold']
        if 'level_threshold' in data:
            achievement.level_threshold = data['level_threshold']
        if 'mission_count_threshold' in data:
            achievement.mission_count_threshold = data['mission_count_threshold']
        
        db.session.commit()
        
        return achievement.to_dict()
    
    @staticmethod
    def delete_achievement(achievement_id):
        """Deletar conquista (admin)"""
        achievement = Achievement.query.get(achievement_id)
        if not achievement:
            raise AchievementNotFound(f"Conquista {achievement_id} não encontrada")
        
        # Verificar se há usuários com essa conquista
        user_count = UserAchievement.query.filter_by(
            achievement_id=achievement_id
        ).count()
        
        if user_count > 0:
            raise ValueError(
                f'Não é possível deletar conquista com {user_count} usuários'
            )
        
        db.session.delete(achievement)
        db.session.commit()
        
        return {'success': True, 'message': 'Conquista deletada com sucesso'}
    
    # ========================================================================
    # VERIFICACAO - Conquistas (LOGICA COMPLEXA)
    # ========================================================================
    
    @staticmethod
    def check_achievements(user_id):
        """
        VERIFICAR E DESBLOQUEAR novas conquistas
        Função chamada quando usuário ganha XP, sobe nível ou completa missão
        
        Returns:
            list: Novas conquistas desbloqueadas
        """
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        new_achievements = []
        all_achievements = Achievement.query.all()
        
        for achievement in all_achievements:
            # Verificar se usuário já tem essa conquista
            existing = UserAchievement.query.filter_by(
                user_id=user_id,
                achievement_id=achievement.id
            ).first()
            
            if existing:
                continue  # Já ganhou essa conquista
            
            # Verificar se alcançou os critérios
            criteria_met = False
            
            # Critério: XP acumulado
            if achievement.xp_threshold:
                if user.current_xp >= achievement.xp_threshold:
                    criteria_met = True
            
            # Critério: Level
            if achievement.level_threshold:
                if user.current_level >= achievement.level_threshold:
                    criteria_met = True
            
            # Critério: Missões completadas
            if achievement.mission_count_threshold:
                completed_count = db.session.query(
                    db.func.count(db.UserMission.id)
                ).filter(
                    db.UserMission.user_id == user_id,
                    db.UserMission.status == 'completed'
                ).scalar()
                
                if completed_count >= achievement.mission_count_threshold:
                    criteria_met = True
            
            # Se atendeu aos critérios, desbloquear conquista
            if criteria_met:
                user_achievement = UserAchievement(
                    user_id=user_id,
                    achievement_id=achievement.id,
                    unlocked_date=datetime.utcnow()
                )
                db.session.add(user_achievement)
                new_achievements.append(achievement.to_dict())
        
        db.session.commit()
        
        return new_achievements
    
    @staticmethod
    def award_achievement(user_id, achievement_id):
        """Atribuir conquista manualmente a um usuário (admin)"""
        user = User.query.get(user_id)
        if not user:
            raise ValueError("Usuário não encontrado")
        
        achievement = Achievement.query.get(achievement_id)
        if not achievement:
            raise AchievementNotFound("Conquista não encontrada")
        
        # Verificar se já tem
        existing = UserAchievement.query.filter_by(
            user_id=user_id,
            achievement_id=achievement_id
        ).first()
        
        if existing:
            raise AchievementAlreadyAwarded("Usuário já possui essa conquista")
        
        user_achievement = UserAchievement(
            user_id=user_id,
            achievement_id=achievement_id,
            unlocked_date=datetime.utcnow()
        )
        
        db.session.add(user_achievement)
        db.session.commit()
        
        return {
            'success': True,
            'message': 'Conquista atribuída com sucesso',
            'achievement': achievement.to_dict()
        }
