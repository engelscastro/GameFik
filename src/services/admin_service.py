# src/services/admin_service.py
"""
Service Layer para Administradores - Lógica de Negócio
Responsável por gerenciar administradores e operações de sistema.
Desacoplado do Flask HTTP - reutilizável em qualquer contexto.

Métodos:
  - create_admin(): Criar novo admin (master only)
  - get_all_admins(): Listar admins
  - get_admin_details(): Detalhes de um admin
  - update_admin(): Atualizar admin
  - delete_admin(): Deletar admin
  - get_system_stats(): Estatísticas do sistema
  - get_all_users_with_profiles(): Listar todos usuários com perfis
  - get_dashboard_data(): Dados do dashboard admin
"""

from datetime import datetime
from src.models.user import User, db
from src.models.academic import Student, Professor, Admin, Discipline, Enrollment, Grade


# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class AdminNotFound(Exception):
    """Exceção quando administrador não é encontrado"""
    pass


class AdminAlreadyExists(Exception):
    """Exceção quando admin já existe"""
    pass


class MasterAdminRequired(Exception):
    """Exceção quando operação requer admin master"""
    pass


class InvalidAdminData(Exception):
    """Exceção quando dados são inválidos"""
    pass


# ============================================================================
# ADMIN SERVICE
# ============================================================================

class AdminService:
    """Service para gerenciar administradores e operações de sistema"""

    # ========================================================================
    # LEITURA - Administradores
    # ========================================================================

    @staticmethod
    def get_all_admins():
        """Obter todos os administradores"""
        try:
            admins = Admin.query.all()
            return [admin.to_dict() for admin in admins]
        except Exception as e:
            raise Exception(f"Erro ao buscar administradores: {str(e)}")

    @staticmethod
    def get_admin_details(admin_id):
        """Obter detalhes de um administrador"""
        try:
            admin = Admin.query.get(admin_id)
            if not admin:
                raise AdminNotFound(f"Admin {admin_id} não encontrado")
            return admin.to_dict()
        except AdminNotFound:
            raise
        except Exception as e:
            raise Exception(f"Erro ao buscar admin: {str(e)}")

    @staticmethod
    def get_admin_by_user_id(user_id):
        """Obter admin pelo user_id"""
        try:
            admin = Admin.query.filter_by(user_id=user_id).first()
            if not admin:
                return None
            return admin.to_dict()
        except Exception as e:
            raise Exception(f"Erro ao buscar admin: {str(e)}")

    @staticmethod
    def is_master_admin(user_id):
        """Verificar se um usuário é admin master"""
        try:
            admin = Admin.query.filter_by(user_id=user_id).first()
            return admin is not None and admin.nivel_acesso == 1
        except Exception:
            return False

    # ========================================================================
    # CRIAÇÃO/ATUALIZAÇÃO/DELECÃO - Administradores
    # ========================================================================

    @staticmethod
    def create_admin(data, created_by_user_id=None):
        """
        Criar novo administrador

        Args:
            data: Dict com dados do admin
                - nome (obrigatório)
                - cpf (obrigatório)
                - cargo (obrigatório)
                - setor (opcional)
                - permissoes (opcional, lista)
                - nivel_acesso (opcional, 1=master, 2=supervisor, 3=suporte)
                - password (opcional, padrão 'admin123')
            created_by_user_id: ID do admin master que está criando

        Returns:
            dict: Admin criado

        Raises:
            InvalidAdminData: Se dados inválidos
            AdminAlreadyExists: Se CPF já cadastrado
            MasterAdminRequired: Se criador não é master
        """
        # Validar permissão (apenas master pode criar admin)
        if created_by_user_id:
            if not AdminService.is_master_admin(created_by_user_id):
                raise MasterAdminRequired("Apenas administradores master podem criar novos admins")

        required_fields = ['nome', 'cpf', 'cargo']
        for field in required_fields:
            if not data.get(field):
                raise InvalidAdminData(f'Campo {field} é obrigatório')

        # Verificar CPF único
        existing_admin = Admin.query.filter_by(cpf=data['cpf']).first()
        if existing_admin:
            raise AdminAlreadyExists(f'CPF {data["cpf"]} já cadastrado')

        # Verificar se usuário já existe
        existing_user = User.query.filter_by(username=data['cpf']).first()
        if existing_user:
            raise AdminAlreadyExists(f'Usuário com CPF {data["cpf"]} já existe')

        # Criar usuário
        user = User(
            username=data['cpf'],
            role='admin',
            current_xp=0,
            current_level=1,
            coins=0
        )
        password = data.get('password', 'admin123')
        user.set_password(password)

        db.session.add(user)
        db.session.flush()  # Obter ID

        # Criar perfil admin
        admin = Admin(
            user_id=user.id,
            nome=data['nome'],
            cpf=data['cpf'],
            cargo=data['cargo'],
            setor=data.get('setor'),
            permissoes=','.join(data.get('permissoes', [])),
            nivel_acesso=data.get('nivel_acesso', 2)  # Padrão: supervisor
        )

        db.session.add(admin)
        db.session.commit()

        return {
            'success': True,
            'admin': admin.to_dict(),
            'login_info': {
                'username': data['cpf'],
                'password': password,
                'role': 'admin'
            }
        }

    @staticmethod
    def update_admin(admin_id, data, current_user_id):
        """
        Atualizar administrador

        Args:
            admin_id: ID do admin
            data: Dict com dados a atualizar
            current_user_id: ID do usuário fazendo a atualização

        Returns:
            dict: Admin atualizado

        Raises:
            AdminNotFound: Se admin não existe
            MasterAdminRequired: Se não tem permissão
        """
        admin = Admin.query.get(admin_id)
        if not admin:
            raise AdminNotFound(f"Admin {admin_id} não encontrado")

        # Verificar permissão: apenas master pode alterar outro admin
        if not AdminService.is_master_admin(current_user_id):
            # Verificar se está alterando o próprio perfil
            current_admin = Admin.query.filter_by(user_id=current_user_id).first()
            if not current_admin or current_admin.id != admin_id:
                raise MasterAdminRequired("Apenas administradores master podem alterar outros admins")

        if 'nome' in data:
            admin.nome = data['nome']
        if 'cargo' in data:
            admin.cargo = data['cargo']
        if 'setor' in data:
            admin.setor = data['setor']
        if 'permissoes' in data:
            admin.permissoes = ','.join(data['permissoes'])
        if 'nivel_acesso' in data:
            # Apenas master pode alterar nível de acesso
            if not AdminService.is_master_admin(current_user_id):
                raise MasterAdminRequired("Apenas administradores master podem alterar nível de acesso")
            admin.nivel_acesso = data['nivel_acesso']

        db.session.commit()

        return admin.to_dict()

    @staticmethod
    def delete_admin(admin_id, current_user_id):
        """
        Deletar administrador

        Args:
            admin_id: ID do admin
            current_user_id: ID do usuário fazendo a deleção

        Returns:
            dict: Status

        Raises:
            AdminNotFound: Se admin não existe
            MasterAdminRequired: Se não tem permissão
            ValueError: Se tentar deletar o próprio admin master
        """
        admin = Admin.query.get(admin_id)
        if not admin:
            raise AdminNotFound(f"Admin {admin_id} não encontrado")

        # Verificar permissão: apenas master pode deletar admin
        if not AdminService.is_master_admin(current_user_id):
            raise MasterAdminRequired("Apenas administradores master podem deletar admins")

        # Não permitir deletar o próprio admin master
        current_admin = Admin.query.filter_by(user_id=current_user_id).first()
        if current_admin and current_admin.id == admin_id:
            raise ValueError("Não é possível deletar seu próprio usuário")

        user = admin.user

        db.session.delete(admin)
        db.session.delete(user)
        db.session.commit()

        return {'success': True, 'message': 'Administrador deletado com sucesso'}

    # ========================================================================
    # SISTEMA - Estatísticas e Dashboard
    # ========================================================================

    @staticmethod
    def get_system_stats():
        """Obter estatísticas completas do sistema"""
        try:
            stats = {
                'users': {
                    'total': User.query.count(),
                    'students': User.query.filter_by(role='student').count(),
                    'teachers': User.query.filter_by(role='teacher').count(),
                    'admins': User.query.filter_by(role='admin').count()
                },
                'academic': {
                    'students_profiles': Student.query.count(),
                    'professors_profiles': Professor.query.count(),
                    'disciplines': Discipline.query.count(),
                    'enrollments': Enrollment.query.count(),
                    'active_enrollments': Enrollment.query.filter_by(status='active').count(),
                    'grades': Grade.query.count()
                },
                'gamification': {
                    'total_xp': db.session.query(db.func.sum(User.current_xp)).scalar() or 0,
                    'total_coins': db.session.query(db.func.sum(User.coins)).scalar() or 0,
                    'avg_level': db.session.query(db.func.avg(User.current_level)).scalar() or 0
                }
            }
            return stats
        except Exception as e:
            raise Exception(f"Erro ao buscar estatísticas: {str(e)}")

    @staticmethod
    def get_all_users_with_profiles():
        """Listar todos os usuários com seus perfis acadêmicos"""
        try:
            users = User.query.all()
            users_data = []

            for user in users:
                user_dict = user.to_dict()

                if user.role == 'student':
                    student = Student.query.filter_by(user_id=user.id).first()
                    if student:
                        user_dict['profile'] = student.to_dict()
                elif user.role == 'teacher':
                    professor = Professor.query.filter_by(user_id=user.id).first()
                    if professor:
                        user_dict['profile'] = professor.to_dict()
                elif user.role == 'admin':
                    admin = Admin.query.filter_by(user_id=user.id).first()
                    if admin:
                        user_dict['profile'] = admin.to_dict()

                users_data.append(user_dict)

            return users_data
        except Exception as e:
            raise Exception(f"Erro ao buscar usuários: {str(e)}")

    @staticmethod
    def get_dashboard_data():
        """Obter dados completos para dashboard do admin"""
        try:
            # Top estudantes por XP
            top_students = db.session.query(
                User.id, User.username, User.current_xp, User.current_level, Student.nome
            ).join(Student, User.id == Student.user_id).order_by(
                User.current_xp.desc()
            ).limit(5).all()

            top_students_data = [
                {'id': s[0], 'username': s[1], 'xp': s[2], 'level': s[3], 'nome': s[4]}
                for s in top_students
            ]

            # Atividades recentes (últimas matrículas)
            recent_enrollments = Enrollment.query.order_by(
                Enrollment.enrollment_date.desc()
            ).limit(10).all()

            recent_activities = []
            for e in recent_enrollments:
                student = Student.query.get(e.student_id)
                discipline = Discipline.query.get(e.discipline_id)
                recent_activities.append({
                    'type': 'enrollment',
                    'student': student.nome if student else 'N/A',
                    'discipline': discipline.nome if discipline else 'N/A',
                    'date': e.enrollment_date.isoformat() if e.enrollment_date else None
                })

            # Estatísticas do sistema
            stats = AdminService.get_system_stats()

            return {
                'statistics': stats,
                'top_students': top_students_data,
                'recent_activities': recent_activities
            }
        except Exception as e:
            raise Exception(f"Erro ao buscar dashboard: {str(e)}")