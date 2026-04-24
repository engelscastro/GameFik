from flask import session
from datetime import datetime
from src.models.user import db, User  # <- Importação correta

class Student(db.Model):
    __tablename__ = 'student'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    matricula = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    curso = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    ano_turma = db.Column(db.String(20), nullable=True)
    nivel_ensino = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relacionamento com User
    user = db.relationship('User', backref='student_profile', foreign_keys=[user_id])

    def add_xp_from_grade(self, grade):
        """Adiciona XP baseado na nota do estudante"""
        if grade.media:
            xp_reward = grade.get_xp_reward()
            if xp_reward > 0 and self.user:
                result = self.user.add_xp(xp_reward, f"grade_{grade.id}")
                return {'xp_added': xp_reward, 'leveled_up': result['leveled_up']}
        return {'xp_added': 0, 'leveled_up': False}

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'matricula': self.matricula,
            'nome': self.nome,
            'curso': self.curso,
            'cpf': self.cpf,
            'ano_turma': self.ano_turma,
            'nivel_ensino': self.nivel_ensino,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_data': self.user.to_dict() if self.user else None
        }


class Discipline(db.Model):
    __tablename__ = 'discipline'
    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    carga_horaria = db.Column(db.Integer, nullable=False)
    professor_id = db.Column(db.Integer, db.ForeignKey('professor.id'), nullable=True)
    ano_turma = db.Column(db.String(20), nullable=True)
    nivel_ensino = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    professor = db.relationship('Professor', backref='disciplines', foreign_keys=[professor_id])

    def get_enrolled_students(self):
        """Retorna todos os estudantes matriculados"""
        return [e.student for e in self.enrollments if e.status == 'active']

    def to_dict(self):
        professor_nome = None
        try:
            if self.professor:
                professor_nome = self.professor.nome
        except Exception as e:
            print(f"❌ Erro ao carregar professor para disciplina {self.id}: {e}")

        return {
            'id': self.id,
            'codigo': self.codigo,
            'nome': self.nome,
            'carga_horaria': self.carga_horaria,
            'professor_id': self.professor_id,
            'professor_nome': professor_nome,
            'ano_turma': self.ano_turma,
            'nivel_ensino': self.nivel_ensino,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Professor(db.Model):
    __tablename__ = 'professor'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    departamento = db.Column(db.String(100), nullable=False)
    anos_turmas = db.Column(db.String(200), nullable=True)
    niveis_ensino = db.Column(db.String(200), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='professor_profile', foreign_keys=[user_id])

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'nome': self.nome,
            'cpf': self.cpf,
            'departamento': self.departamento,
            'anos_turmas': self.anos_turmas,
            'niveis_ensino': self.niveis_ensino,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_data': self.user.to_dict() if self.user else None
        }


class Enrollment(db.Model):
    __tablename__ = 'enrollment'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    enrollment_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='active')

    student = db.relationship('Student', backref='enrollments', foreign_keys=[student_id])
    discipline = db.relationship('Discipline', backref='enrollments', foreign_keys=[discipline_id])

    def complete_course(self):
        """Completa o curso e dá XP de conclusão"""
        if self.status == 'active':
            self.status = 'completed'
            if self.student and self.student.user:
                # Bônus de 200 XP por disciplina concluída
                result = self.student.user.add_xp(200, f"course_completion_{self.discipline_id}")
                return {'xp_added': 200, 'leveled_up': result['leveled_up']}
        return {'xp_added': 0, 'leveled_up': False}

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'discipline_id': self.discipline_id,
            'enrollment_date': self.enrollment_date.isoformat() if self.enrollment_date else None,
            'status': self.status,
            'student_nome': self.student.nome if self.student else None,
            'student_matricula': self.student.matricula if self.student else None,
            'discipline_nome': self.discipline.nome if self.discipline else None,
            'discipline_codigo': self.discipline.codigo if self.discipline else None
        }


class Grade(db.Model):
    __tablename__ = 'grade'
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    nota1 = db.Column(db.Float, nullable=True)
    nota2 = db.Column(db.Float, nullable=True)
    media = db.Column(db.Float, nullable=True)
    xp_awarded = db.Column(db.Boolean, default=False)  # <- Novo campo para evitar duplicação
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    student = db.relationship('Student', backref='grades', foreign_keys=[student_id])
    discipline = db.relationship('Discipline', backref='grades', foreign_keys=[discipline_id])

    def calculate_media(self):
        if self.nota1 is not None and self.nota2 is not None:
            self.media = (self.nota1 + self.nota2) / 2
        return self.media

    def get_xp_reward(self):
        if self.media is None:
            return 0
        if self.media >= 9.0:
            return 100
        elif self.media >= 8.0:
            return 80
        elif self.media >= 7.0:
            return 60
        elif self.media >= 6.0:
            return 40
        else:
            return 10

    def award_xp_to_student(self):
        """Concede XP ao estudante baseado na nota"""
        if not self.xp_awarded and self.media is not None and self.student:
            xp_reward = self.get_xp_reward()
            if xp_reward > 0:
                result = self.student.add_xp_from_grade(self)
                self.xp_awarded = True
                return {'xp_added': xp_reward, 'leveled_up': result['leveled_up']}
        return {'xp_added': 0, 'leveled_up': False}

    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'discipline_id': self.discipline_id,
            'nota1': self.nota1,
            'nota2': self.nota2,
            'media': self.media,
            'xp_reward': self.get_xp_reward(),
            'xp_awarded': self.xp_awarded,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'student_nome': self.student.nome if self.student else None,
            'student_matricula': self.student.matricula if self.student else None,
            'discipline_nome': self.discipline.nome if self.discipline else None,
            'discipline_codigo': self.discipline.codigo if self.discipline else None
        }


class AcademicMission(db.Model):
    __tablename__ = 'academic_mission'
    id = db.Column(db.Integer, primary_key=True)
    mission_id = db.Column(db.Integer, db.ForeignKey('mission.id'), nullable=False)
    mission_type = db.Column(db.String(50), nullable=False)
    target_value = db.Column(db.Float, nullable=True)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=True)

    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text)
    xp_reward = db.Column(db.Integer, default=0)
    due_date = db.Column(db.Date)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    mission = db.relationship('Mission', backref='academic_mission')
    discipline = db.relationship('Discipline', backref='academic_missions')

    def to_dict(self):
        return {
            'id': self.id,
            'mission_id': self.mission_id,
            'title': self.title,
            'description': self.description,
            'mission_type': self.mission_type,
            'target_value': self.target_value,
            'discipline_id': self.discipline_id,
            'discipline_nome': self.discipline.nome if self.discipline else None,
            'xp_reward': self.xp_reward,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class DisciplineChat(db.Model):
    __tablename__ = 'discipline_chat'
    id = db.Column(db.Integer, primary_key=True)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    discipline = db.relationship('Discipline', backref=db.backref('chat', passive_deletes=True))
    messages = db.relationship('ChatMessage', backref='chat', lazy=True, order_by="desc(ChatMessage.created_at)")


class ChatMessage(db.Model):
    __tablename__ = 'chat_message'
    id = db.Column(db.Integer, primary_key=True)
    chat_id = db.Column(db.Integer, db.ForeignKey('discipline_chat.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    message_type = db.Column(db.String(20), default='text')
    content = db.Column(db.Text, nullable=False)
    file_url = db.Column(db.String(500))
    is_pinned = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # NOVOS CAMPOS (adicionar)
    reactions = db.Column(db.JSON, default=dict)           # {"👍": [user_id1, user_id2], ...}
    reply_to = db.Column(db.Integer, db.ForeignKey('chat_message.id'), nullable=True)

    # Relacionamentos
    user = db.relationship('User', backref='chat_messages')
    parent = db.relationship('ChatMessage', remote_side=[id], backref='replies')

    def to_dict(self):
        user_name = self.user.username if self.user else "Unknown"

        if self.user and self.user.role == 'student':
            student = Student.query.filter_by(user_id=self.user.id).first()
            if student and student.nome:
                user_name = student.nome
        elif self.user and self.user.role == 'teacher':
            professor = Professor.query.filter_by(user_id=self.user.id).first()
            if professor and professor.nome:
                user_name = professor.nome

        # Dados da mensagem original (se for resposta)
        parent_info = None
        if self.reply_to:
            parent_msg = ChatMessage.query.get(self.reply_to)
            if parent_msg:
                parent_info = {
                    'id': parent_msg.id,
                    'user_name': parent_msg.user.username,
                    'content': parent_msg.content[:100]
                }

        return {
            'id': self.id,
            'chat_id': self.chat_id,
            'user_id': self.user_id,
            'user_name': user_name,
            'user_role': self.user.role if self.user else None,
            'message_type': self.message_type,
            'content': self.content,
            'file_url': self.file_url,
            'is_pinned': self.is_pinned,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_own_message': self.user_id == session.get('user_id') if session else False,
            'reactions': self.reactions or {},
            'reply_to': self.reply_to,
            'parent_message': parent_info
        }

class ClassActivity(db.Model):
    __tablename__ = 'class_activity'
    id = db.Column(db.Integer, primary_key=True)
    discipline_id = db.Column(db.Integer, db.ForeignKey('discipline.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    activity_type = db.Column(db.String(50), default='assignment')
    due_date = db.Column(db.DateTime)
    xp_reward = db.Column(db.Integer, default=0)
    coin_reward = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    discipline = db.relationship('Discipline', backref='activities')

    def to_dict(self):
        return {
            'id': self.id,
            'discipline_id': self.discipline_id,
            'discipline_nome': self.discipline.nome if self.discipline else None,
            'title': self.title,
            'description': self.description,
            'activity_type': self.activity_type,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'xp_reward': self.xp_reward,
            'coin_reward': self.coin_reward,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


# ============================================================================
# ADMIN MODEL - CORRETO (FORA DA CLASSE ClassActivity)
# ============================================================================

class Admin(db.Model):
    """Modelo para administradores - Controle total do sistema"""
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, unique=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), unique=True, nullable=False)
    cargo = db.Column(db.String(100), nullable=False, default='Administrador')
    setor = db.Column(db.String(100), nullable=True)
    permissoes = db.Column(db.String(500), nullable=True)
    nivel_acesso = db.Column(db.Integer, default=2)  # 1=Master, 2=Supervisor, 3=Suporte
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref='admin_profile', foreign_keys=[user_id], uselist=False)

    def has_permission(self, permission):
        """Verifica se o admin tem uma permissão específica"""
        if self.nivel_acesso == 1:  # Master tem todas as permissões
            return True
        if not self.permissoes:
            return False
        permissoes_list = self.permissoes.split(',')
        return permission in permissoes_list

    def is_master(self):
        """Verifica se é admin master"""
        return self.nivel_acesso == 1

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'nome': self.nome,
            'cpf': self.cpf,
            'cargo': self.cargo,
            'setor': self.setor,
            'permissoes': self.permissoes.split(',') if self.permissoes else [],
            'nivel_acesso': self.nivel_acesso,
            'is_master': self.is_master(),
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'user_data': self.user.to_dict() if self.user else None
        }

class TurmaFeedPost(db.Model):
    """Postagens no mural da turma"""
    __tablename__ = 'turma_feed_posts'
    id = db.Column(db.Integer, primary_key=True)
    ano_turma = db.Column(db.String(20), nullable=False)          # ex: '7_ano_final'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_type = db.Column(db.String(20), default='announcement')  # announcement, material, assignment, question
    file_url = db.Column(db.String(500))
    due_date = db.Column(db.DateTime)                             # para atividades
    points = db.Column(db.Integer, default=0)                     # pontuação máxima
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref='feed_posts')

    def to_dict(self):
        return {
            'id': self.id,
            'ano_turma': self.ano_turma,
            'user_id': self.user_id,
            'user_name': self.user.username,
            'user_role': self.user.role,
            'title': self.title,
            'content': self.content,
            'post_type': self.post_type,
            'file_url': self.file_url,
            'due_date': self.due_date.isoformat() if self.due_date else None,
            'points': self.points,
            'created_at': self.created_at.isoformat() if self.created_at else None,
        }


class TurmaAssignmentSubmission(db.Model):
    """Entrega de atividades pelos alunos"""
    __tablename__ = 'turma_assignment_submissions'
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('turma_feed_posts.id'), nullable=False)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    content = db.Column(db.Text)               # resposta em texto
    file_url = db.Column(db.String(500))       # arquivo enviado
    grade = db.Column(db.Float)                # nota atribuída (0 a 100)
    feedback = db.Column(db.Text)              # feedback do professor
    status = db.Column(db.String(20), default='submitted')  # submitted, graded, late

    post = db.relationship('TurmaFeedPost', backref='submissions')
    student = db.relationship('Student', backref='submissions')

    def to_dict(self):
        return {
            'id': self.id,
            'post_id': self.post_id,
            'student_id': self.student_id,
            'student_name': self.student.nome,
            'submitted_at': self.submitted_at.isoformat() if self.submitted_at else None,
            'content': self.content,
            'file_url': self.file_url,
            'grade': self.grade,
            'feedback': self.feedback,
            'status': self.status,
        }