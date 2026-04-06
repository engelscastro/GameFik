# src/services/user_service.py
"""
Service Layer para Usuários - Lógica de Negócio
Responsável por autenticação, autorização e gerenciamento de usuários.
Desacoplado do Flask HTTP - reutilizável em qualquer contexto.

Métodos:
  - register_user(): Registrar novo usuário
  - authenticate_user(): Validar credenciais
  - get_user(): Obter dados de um usuário
  - get_all_users(): Listar todos os usuários (admin)
  - update_user(): Atualizar dados do usuário
  - delete_user(): Deletar usuário (admin)
  - change_password(): Alterar senha
  - get_user_stats(): Obter estatísticas do usuário (XP, Level, etc)
"""

from datetime import datetime
from src.models.user import User, db
from src.models.academic import Student, Professor, Admin


# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class UserNotFound(Exception):
    """Exceção quando usuário não é encontrado"""
    pass


class UserAlreadyExists(Exception):
    """Exceção quando username/email já existem"""
    pass


class InvalidCredentials(Exception):
    """Exceção quando credenciais são inválidas"""
    pass


class InvalidUserData(Exception):
    """Exceção quando dados do usuário são inválidos"""
    pass


# ============================================================================
# USER SERVICE
# ============================================================================

class UserService:
    """Service para gerenciar usuários do sistema"""

    # ========================================================================
    # AUTENTICAÇÃO
    # ========================================================================

    @staticmethod
    def register_user(username, password, email, role='student'):
        """
        Registrar novo usuário

        Args:
            username: Nome de usuário único
            password: Senha (será hash)
            email: Email do usuário
            role: 'student', 'teacher', ou 'admin'

        Returns:
            dict: Dados do usuário criado

        Raises:
            UserAlreadyExists: Se username/email já estão cadastrados
            InvalidUserData: Se dados inválidos
        """
        if not username or len(username) < 3:
            raise InvalidUserData('Username deve ter pelo menos 3 caracteres')

        if not password or len(password) < 6:
            raise InvalidUserData('Senha deve ter pelo menos 6 caracteres')

        if not email or '@' not in email:
            raise InvalidUserData('Email inválido')

        existing = User.query.filter_by(username=username).first()
        if existing:
            raise UserAlreadyExists(f'Username "{username}" já existe')

        existing_email = User.query.filter_by(email=email).first()
        if existing_email:
            raise UserAlreadyExists(f'Email "{email}" já cadastrado')

        user = User(
            username=username,
            email=email,
            role=role,
            current_xp=0,
            current_level=1,
            coins=0  # CORRIGIDO: era 'current_coins'
        )
        user.set_password(password)

        db.session.add(user)
        db.session.commit()

        return user.to_dict()

    @staticmethod
    def authenticate_user(username, password):
        """
        Autenticar usuário

        Args:
            username: Nome de usuário
            password: Senha

        Returns:
            dict: Dados do usuário autenticado

        Raises:
            InvalidCredentials: Se credenciais incorretas
        """
        user = User.query.filter_by(username=username).first()

        if not user or not user.check_password(password):
            raise InvalidCredentials('Username ou senha inválidos')

        return user.to_dict()

    # ========================================================================
    # LEITURA - Usuários
    # ========================================================================

    @staticmethod
    def get_user(user_id):
        """Obter dados de um usuário, incluindo perfis acadêmicos."""
        user = User.query.get(user_id)
        if not user:
            raise UserNotFound(f"Usuário {user_id} não encontrado")

        user_data = user.to_dict()

        # Anexar perfil de estudante, se existir
        student = Student.query.filter_by(user_id=user.id).first()
        if student:
            user_data['student_profile'] = student.to_dict()

        # Anexar perfil de professor, se existir
        professor = Professor.query.filter_by(user_id=user.id).first()
        if professor:
            user_data['professor_profile'] = professor.to_dict()

        # NOVO: Anexar perfil de admin, se existir
        admin = Admin.query.filter_by(user_id=user.id).first()
        if admin:
            user_data['admin_profile'] = admin.to_dict()

        return user_data

    @staticmethod
    def get_all_users(role=None):
        """
        Listar todos os usuários (admin)

        Args:
            role: Filtrar por role ('student', 'teacher', 'admin')

        Returns:
            list: Lista de usuários
        """
        query = User.query

        if role:
            query = query.filter_by(role=role)

        users = query.all()
        return [user.to_dict() for user in users]

    @staticmethod
    def get_user_stats(user_id):
        """
        Obter estatísticas completas do usuário

        Args:
            user_id: ID do usuário

        Returns:
            dict: Estatísticas e progressão
        """
        user = User.query.get(user_id)
        if not user:
            raise UserNotFound(f"Usuário {user_id} não encontrado")

        # CORRIGIDO: 'coins' em vez de 'current_coins'
        return {
            'user_id': user.id,
            'username': user.username,
            'role': user.role,
            'level': user.current_level,
            'xp': user.current_xp,
            'xp_to_next_level': ((user.current_level + 1) * 100) - user.current_xp,
            'coins': user.coins,  # CORRIGIDO
            'created_at': user.created_at.isoformat() if user.created_at else None,
            'xp_progress': {
                'current': user.current_xp,
                'total_for_level': user.current_level * 100,
                'percentage': min(
                    100,
                    (user.current_xp / (user.current_level * 100)) * 100
                ) if user.current_level > 0 else 0
            }
        }

    # ========================================================================
    # ATUALIZAÇÃO - Usuários
    # ========================================================================

    @staticmethod
    def update_user(user_id, data):
        """
        Atualizar dados do usuário

        Args:
            user_id: ID do usuário
            data: Dict com dados a atualizar

        Returns:
            dict: Usuário atualizado

        Raises:
            UserNotFound: Se usuário não existe
            InvalidUserData: Se dados inválidos
        """
        user = User.query.get(user_id)
        if not user:
            raise UserNotFound(f"Usuário {user_id} não encontrado")

        # Só admin pode mudar role (regra de negócio simples aqui)
        if 'role' in data:
            raise InvalidUserData('Role pode ser alterado apenas por admin')

        if 'email' in data:
            existing = User.query.filter_by(email=data['email']).first()
            if existing and existing.id != user_id:
                raise UserAlreadyExists('Email já cadastrado')
            user.email = data['email']

        if 'username' in data:
            existing = User.query.filter_by(username=data['username']).first()
            if existing and existing.id != user_id:
                raise UserAlreadyExists('Username já existe')
            user.username = data['username']

        db.session.commit()

        return user.to_dict()

    @staticmethod
    def change_password(user_id, old_password, new_password):
        """
        Alterar senha do usuário

        Args:
            user_id: ID do usuário
            old_password: Senha atual
            new_password: Nova senha

        Returns:
            dict: Status da alteração

        Raises:
            UserNotFound: Se usuário não existe
            InvalidCredentials: Se senha atual incorreta
            InvalidUserData: Se nova senha inválida
        """
        user = User.query.get(user_id)
        if not user:
            raise UserNotFound(f"Usuário {user_id} não encontrado")

        if not user.check_password(old_password):
            raise InvalidCredentials('Senha atual incorreta')

        if not new_password or len(new_password) < 6:
            raise InvalidUserData('Nova senha deve ter pelo menos 6 caracteres')

        user.set_password(new_password)
        db.session.commit()

        return {
            'success': True,
            'message': 'Senha alterada com sucesso'
        }

    # ========================================================================
    # DELEÇÃO - Usuários
    # ========================================================================

    @staticmethod
    def delete_user(user_id):
        """
        Deletar usuário (admin)
        Será deletado em cascata com todos seus dados

        Args:
            user_id: ID do usuário

        Returns:
            dict: Status da deleção

        Raises:
            UserNotFound: Se usuário não existe
        """
        user = User.query.get(user_id)
        if not user:
            raise UserNotFound(f"Usuário {user_id} não encontrado")

        # Deletar perfis associados
        if user.role == 'student':
            student = Student.query.filter_by(user_id=user.id).first()
            if student:
                db.session.delete(student)
        elif user.role == 'teacher':
            professor = Professor.query.filter_by(user_id=user.id).first()
            if professor:
                db.session.delete(professor)
        elif user.role == 'admin':
            admin = Admin.query.filter_by(user_id=user.id).first()
            if admin:
                db.session.delete(admin)

        db.session.delete(user)
        db.session.commit()

        return {
            'success': True,
            'message': f'Usuário {user.username} deletado com sucesso'
        }

    # ========================================================================
    # PROGRESSÃO - Usuários
    # ========================================================================

    @staticmethod
    def add_xp(user_id, xp_amount):
        """
        Adicionar XP ao usuário

        Args:
            user_id: ID do usuário
            xp_amount: Quantidade de XP a adicionar

        Returns:
            dict: Nova progressão do usuário
        """
        user = User.query.get(user_id)
        if not user:
            raise UserNotFound(f"Usuário {user_id} não encontrado")

        old_level = user.current_level

        user.current_xp += xp_amount
        user.current_level = (user.current_xp // 100) + 1

        db.session.commit()

        level_up = user.current_level > old_level

        return {
            'success': True,
            'xp_added': xp_amount,
            'total_xp': user.current_xp,
            'current_level': user.current_level,
            'level_up': level_up,
            'old_level': old_level,
            'new_level': user.current_level
        }

    @staticmethod
    def add_coins(user_id, coin_amount):
        """
        Adicionar coins ao usuário

        Args:
            user_id: ID do usuário
            coin_amount: Quantidade de coins a adicionar

        Returns:
            dict: Nova progressão do usuário
        """
        user = User.query.get(user_id)
        if not user:
            raise UserNotFound(f"Usuário {user_id} não encontrado")

        user.coins += coin_amount  # CORRIGIDO: era 'current_coins'
        db.session.commit()

        return {
            'success': True,
            'coins_added': coin_amount,
            'total_coins': user.coins  # CORRIGIDO
        }

    @staticmethod
    def get_user_by_username(username):
        """
        Buscar usuário por username

        Args:
            username: Nome de usuário

        Returns:
            dict: Dados do usuário ou None
        """
        user = User.query.filter_by(username=username).first()
        if not user:
            return None
        return UserService.get_user(user.id)

    @staticmethod
    def get_user_by_email(email):
        """
        Buscar usuário por email

        Args:
            email: Email do usuário

        Returns:
            dict: Dados do usuário ou None
        """
        user = User.query.filter_by(email=email).first()
        if not user:
            return None
        return UserService.get_user(user.id)