# src/services/discipline_service.py
"""
Service Layer para Disciplinas - Lógica de Negócio
Responsável por gerenciar disciplinas, professores, alunos e relacionamentos.
Desacoplado do Flask HTTP - reutilizável em qualquer contexto.

Métodos:
  - get_all_disciplines(): Listar todas as disciplinas
  - create_discipline(): Criar nova disciplina (admin)
  - update_discipline(): Atualizar disciplina (admin)
  - delete_discipline(): Deletar disciplina (admin)
  - get_discipline_details(): Obter detalhes de disciplina
  - assign_professor_to_discipline(): Atribuir professor
  - get_teacher_disciplines(): Listar disciplinas do professor
  - get_available_disciplines(): Disciplinas disponíveis para aluno
  - enroll_student(): Matricular estudante em disciplina
  - get_discipline_students(): Listar alunos de uma disciplina
"""

from datetime import datetime
from src.models.user import User, db

# Importar modelos acadêmicos (pode estar em academic.py)
try:
    from src.models.academic import Discipline, Enrollment, Professor, Student
except ImportError:
    # Se não encontrar, tentar importar de user.py
    try:
        from src.models.user import Discipline, Enrollment, Professor, Student
    except ImportError:
        print("⚠️ Aviso: Modelos acadêmicos (Discipline, Enrollment, etc) não encontrados")
        Discipline = None
        Enrollment = None
        Professor = None
        Student = None


# ============================================================================
# EXCEÇÕES CUSTOMIZADAS
# ============================================================================

class DisciplineNotFound(Exception):
    """Exceção quando disciplina não é encontrada"""
    pass


class DisciplineAlreadyExists(Exception):
    """Exceção quando disciplina já existe"""
    pass


class ProfessorNotFound(Exception):
    """Exceção quando professor não é encontrado"""
    pass


class StudentNotFound(Exception):
    """Exceção quando aluno não é encontrado"""
    pass


class StudentAlreadyEnrolled(Exception):
    """Exceção quando aluno já está matriculado"""
    pass


class InvalidDisciplineData(Exception):
    """Exceção quando dados são inválidos"""
    pass


# ============================================================================
# DISCIPLINE SERVICE
# ============================================================================

class DisciplineService:
    """Service para gerenciar disciplinas e matrículas"""

    # ========================================================================
    # LEITURA - Disciplinas
    # ========================================================================

    @staticmethod
    def get_all_disciplines():
        """Obter todas as disciplinas ativas"""
        if Discipline is None:
            raise ImportError("Modelo Discipline não disponível")

        disciplines = Discipline.query.filter_by(is_active=True).all()
        return [discipline.to_dict() for discipline in disciplines]

    @staticmethod
    def get_all_disciplines_admin():
        """Obter TODAS as disciplinas (admin)"""
        if Discipline is None:
            raise ImportError("Modelo Discipline não disponível")

        disciplines = Discipline.query.all()
        return [discipline.to_dict() for discipline in disciplines]

    @staticmethod
    def get_discipline_details(discipline_id):
        """Obter detalhes completos de uma disciplina"""
        if Discipline is None:
            raise ImportError("Modelo Discipline não disponível")

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            raise DisciplineNotFound(f"Disciplina {discipline_id} não encontrada")

        details = discipline.to_dict()

        # Adicionar professor
        if discipline.professor_id:
            professor = User.query.get(discipline.professor_id)
            details['professor'] = professor.to_dict() if professor else None

        # Contar alunos
        if Enrollment is not None:
            student_count = Enrollment.query.filter_by(
                discipline_id=discipline_id
            ).count()
            details['student_count'] = student_count

        return details

    @staticmethod
    def get_teacher_disciplines(user_id):
        """
        Listar todas as disciplinas de um professor
        CORRIGIDO: agora busca o perfil do professor antes de filtrar.
        """
        if Discipline is None:
            raise ImportError("Modelo Discipline não disponível")
        if Professor is None:
            raise ImportError("Modelo Professor não disponível")

        user = User.query.get(user_id)
        if not user or user.role != 'teacher':
            raise ValueError("Usuário não é professor")

        # 1. Buscar o perfil do professor (tabela professor)
        professor = Professor.query.filter_by(user_id=user_id).first()
        if not professor:
            # Professor não tem perfil cadastrado -> retorna lista vazia
            return []

        # 2. Filtrar disciplinas pelo ID do perfil (professor.id)
        disciplines = Discipline.query.filter_by(professor_id=professor.id).all()

        result = []
        for discipline in disciplines:
            disc_data = discipline.to_dict()

            # Contar alunos matriculados (opcional)
            if Enrollment is not None:
                student_count = Enrollment.query.filter_by(
                    discipline_id=discipline.id
                ).count()
                disc_data['student_count'] = student_count

            result.append(disc_data)

        return result

    @staticmethod
    def get_available_disciplines(user_id):
        """Listar disciplinas disponíveis para um aluno"""
        if Discipline is None or Enrollment is None:
            raise ImportError("Modelos acadêmicos não disponíveis")

        user = User.query.get(user_id)
        if not user or user.role != 'student':
            raise ValueError("Usuário não é aluno")

        # Obter disciplinas já matriculadas
        enrolled_ids = db.session.query(Enrollment.discipline_id).filter_by(
            student_id=user_id
        ).all()
        enrolled_ids = [e[0] for e in enrolled_ids]

        # Obter disciplinas disponíveis (não matriculadas)
        available = Discipline.query.filter(
            Discipline.is_active == True,
            Discipline.id.notin_(enrolled_ids)
        ).all()

        return [discipline.to_dict() for discipline in available]

    @staticmethod
    def get_discipline_students(discipline_id):
        """Listar alunos de uma disciplina"""
        if Discipline is None or Enrollment is None:
            raise ImportError("Modelos acadêmicos não disponíveis")

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            raise DisciplineNotFound(f"Disciplina {discipline_id} não encontrada")

        enrollments = Enrollment.query.filter_by(
            discipline_id=discipline_id
        ).all()

        students = []
        for enrollment in enrollments:
            student = User.query.get(enrollment.student_id)
            if student:
                student_data = student.to_dict()
                student_data['enrollment_date'] = enrollment.enrollment_date
                students.append(student_data)

        return students

    # ========================================================================
    # CRIACAO/ATUALIZACAO/DELECAO - Disciplinas
    # ========================================================================

    @staticmethod
    def create_discipline(data):
        """Criar nova disciplina (admin)"""
        if Discipline is None:
            raise ImportError("Modelo Discipline não disponível")

        if not data.get('name'):
            raise InvalidDisciplineData('Nome da disciplina é obrigatório')

        # Verificar se já existe
        existing = Discipline.query.filter_by(name=data.get('name')).first()
        if existing:
            raise DisciplineAlreadyExists(f"Disciplina '{data.get('name')}' já existe")

        discipline = Discipline(
            name=data.get('name'),
            description=data.get('description', ''),
            ano_turma=data.get('ano_turma', ''),
            nivel_ensino=data.get('nivel_ensino', ''),
            is_active=True
        )

        # Atribuir professor se fornecido
        if data.get('professor_id'):
            professor = User.query.get(data.get('professor_id'))
            if not professor or professor.role != 'teacher':
                raise ProfessorNotFound("Professor não encontrado")
            discipline.professor_id = professor.id

        db.session.add(discipline)
        db.session.commit()

        return discipline.to_dict()

    @staticmethod
    def update_discipline(discipline_id, data):
        """Atualizar disciplina (admin)"""
        if Discipline is None:
            raise ImportError("Modelo Discipline não disponível")

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            raise DisciplineNotFound(f"Disciplina {discipline_id} não encontrada")

        if 'name' in data:
            discipline.name = data['name']
        if 'description' in data:
            discipline.description = data['description']
        if 'ano_turma' in data:
            discipline.ano_turma = data['ano_turma']
        if 'nivel_ensino' in data:
            discipline.nivel_ensino = data['nivel_ensino']
        if 'is_active' in data:
            discipline.is_active = data['is_active']

        db.session.commit()

        return discipline.to_dict()

    @staticmethod
    def delete_discipline(discipline_id):
        """Deletar disciplina (admin)"""
        if Discipline is None or Enrollment is None:
            raise ImportError("Modelos acadêmicos não disponíveis")

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            raise DisciplineNotFound(f"Disciplina {discipline_id} não encontrada")

        # Verificar se tem matrículas
        enrollment_count = Enrollment.query.filter_by(
            discipline_id=discipline_id
        ).count()

        if enrollment_count > 0:
            raise ValueError(
                f'Não é possível deletar disciplina com {enrollment_count} matrículas'
            )

        db.session.delete(discipline)
        db.session.commit()

        return {'success': True, 'message': 'Disciplina deletada com sucesso'}

    # ========================================================================
    # PROFESSOR - Atribuição
    # ========================================================================

    @staticmethod
    def assign_professor_to_discipline(discipline_id, professor_id):
        """
        Atribuir professor a uma disciplina

        Args:
            discipline_id: ID da disciplina
            professor_id: ID do professor (user_id)

        Returns:
            dict: Disciplina atualizada

        Raises:
            DisciplineNotFound: Se disciplina não existe
            ProfessorNotFound: Se professor não existe
        """
        if Discipline is None:
            raise ImportError("Modelo Discipline não disponível")

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            raise DisciplineNotFound(f"Disciplina {discipline_id} não encontrada")

        professor = User.query.get(professor_id)
        if not professor or professor.role != 'teacher':
            raise ProfessorNotFound(f"Professor {professor_id} não encontrado")

        discipline.professor_id = professor_id
        db.session.commit()

        return discipline.to_dict()

    @staticmethod
    def remove_professor_from_discipline(discipline_id):
        """Remover professor de uma disciplina"""
        if Discipline is None:
            raise ImportError("Modelo Discipline não disponível")

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            raise DisciplineNotFound(f"Disciplina {discipline_id} não encontrada")

        discipline.professor_id = None
        db.session.commit()

        return {
            'success': True,
            'message': 'Professor removido da disciplina'
        }

    # ========================================================================
    # ALUNO - Matrícula
    # ========================================================================

    @staticmethod
    def enroll_student(student_id, discipline_id):
        """
        Matricular aluno em disciplina

        Args:
            student_id: ID do aluno
            discipline_id: ID da disciplina

        Returns:
            dict: Matrícula criada

        Raises:
            StudentNotFound: Se aluno não existe
            DisciplineNotFound: Se disciplina não existe
            StudentAlreadyEnrolled: Se aluno já está matriculado
        """
        if Discipline is None or Enrollment is None:
            raise ImportError("Modelos acadêmicos não disponíveis")

        student = User.query.get(student_id)
        if not student or student.role != 'student':
            raise StudentNotFound(f"Aluno {student_id} não encontrado")

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            raise DisciplineNotFound(f"Disciplina {discipline_id} não encontrada")

        # Verificar se já está matriculado
        existing = Enrollment.query.filter_by(
            student_id=student_id,
            discipline_id=discipline_id
        ).first()

        if existing:
            raise StudentAlreadyEnrolled(
                f"Aluno já matriculado em {discipline.name}"
            )

        # Criar matrícula
        enrollment = Enrollment(
            student_id=student_id,
            discipline_id=discipline_id,
            enrollment_date=datetime.utcnow(),
            status='active'
        )

        db.session.add(enrollment)
        db.session.commit()

        return {
            'success': True,
            'message': f'Aluno matriculado em {discipline.name}',
            'enrollment': enrollment.to_dict()
        }

    @staticmethod
    def cancel_enrollment(enrollment_id):
        """
        Cancelar matrícula de aluno

        Args:
            enrollment_id: ID da matrícula

        Returns:
            dict: Status do cancelamento
        """
        if Enrollment is None:
            raise ImportError("Modelo Enrollment não disponível")

        enrollment = Enrollment.query.get(enrollment_id)
        if not enrollment:
            raise ValueError("Matrícula não encontrada")

        db.session.delete(enrollment)
        db.session.commit()

        return {
            'success': True,
            'message': 'Matrícula cancelada com sucesso'
        }

    @staticmethod
    def bulk_enroll_students(discipline_id, student_ids):
        """
        Matricular múltiplos alunos em uma disciplina

        Args:
            discipline_id: ID da disciplina
            student_ids: Lista de IDs de alunos

        Returns:
            dict: Status do resultado (sucesso, erros)
        """
        if Discipline is None or Enrollment is None:
            raise ImportError("Modelos acadêmicos não disponíveis")

        discipline = Discipline.query.get(discipline_id)
        if not discipline:
            raise DisciplineNotFound(f"Disciplina {discipline_id} não encontrada")

        success_count = 0
        error_count = 0
        errors = []

        for student_id in student_ids:
            try:
                DisciplineService.enroll_student(student_id, discipline_id)
                success_count += 1
            except Exception as e:
                error_count += 1
                errors.append({
                    'student_id': student_id,
                    'error': str(e)
                })

        return {
            'success': error_count == 0,
            'total': len(student_ids),
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }