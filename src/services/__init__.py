# src/services/__init__.py
"""
Service Layer - Lógica de Negócio Centralizada

Esta camada contém toda a lógica de negócio do sistema,
desacoplada das camadas de apresentação (HTTP, CLI, etc).

Services disponíveis:
  - UserService: Autenticação e gestão de usuários
  - AdminService: Gestão de administradores e sistema
  - DisciplineService: Gestão de disciplinas
  - MissionService: Gestão de missões e gamificação
  - AchievementService: Gestão de conquistas
  - RewardService: Gestão de recompensas
"""

from .user_service import UserService, UserNotFound, UserAlreadyExists, InvalidCredentials, InvalidUserData
from .admin_service import AdminService, AdminNotFound, AdminAlreadyExists, MasterAdminRequired, InvalidAdminData
from .discipline_service import DisciplineService, DisciplineNotFound, DisciplineAlreadyExists
from .mission_service import MissionService, MissionNotFound, MissionAlreadyCompleted, MissionAlreadyAssigned
from .achievement_service import AchievementService, AchievementNotFound, AchievementAlreadyAwarded
from .reward_service import RewardService, RewardNotFound, InsufficientCoins, RewardAlreadyRedeemed

__all__ = [
    # Services
    'UserService',
    'AdminService',
    'DisciplineService',
    'MissionService',
    'AchievementService',
    'RewardService',
    # Exceptions - User
    'UserNotFound',
    'UserAlreadyExists',
    'InvalidCredentials',
    'InvalidUserData',
    # Exceptions - Admin
    'AdminNotFound',
    'AdminAlreadyExists',
    'MasterAdminRequired',
    'InvalidAdminData',
    # Exceptions - Discipline
    'DisciplineNotFound',
    'DisciplineAlreadyExists',
    # Exceptions - Mission
    'MissionNotFound',
    'MissionAlreadyCompleted',
    'MissionAlreadyAssigned',
    # Exceptions - Achievement
    'AchievementNotFound',
    'AchievementAlreadyAwarded',
    # Exceptions - Reward
    'RewardNotFound',
    'InsufficientCoins',
    'RewardAlreadyRedeemed'
]