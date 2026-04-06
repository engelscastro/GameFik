from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    current_xp = db.Column(db.Integer, default=0)
    current_level = db.Column(db.Integer, default=1)
    coins = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_missions = db.relationship('UserMission', backref='user', lazy=True)
    user_achievements = db.relationship('UserAchievement', backref='user', lazy=True)
    user_rewards = db.relationship('UserReward', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def add_xp(self, xp_amount, source="unknown"):
        """Adiciona XP e verifica level up"""
        old_level = self.current_level
        self.current_xp += xp_amount

        # Cálculo do novo nível (fórmula: 100, 200, 300...)
        new_level = 1
        xp_needed = 0
        while self.current_xp >= xp_needed:
            xp_needed += new_level * 100
            if self.current_xp >= xp_needed:
                new_level += 1

        if new_level > self.current_level:
            self.current_level = new_level
            return {'leveled_up': True, 'old_level': old_level, 'new_level': new_level}
        return {'leveled_up': False}

    def add_coins(self, coin_amount):
        self.coins += coin_amount

    def spend_coins(self, coin_amount):
        if self.coins >= coin_amount:
            self.coins -= coin_amount
            return True
        return False

    def get_student_profile(self):
        """Obtém perfil de estudante se existir"""
        from src.models.academic import Student
        return Student.query.filter_by(user_id=self.id).first()

    def get_professor_profile(self):
        """Obtém perfil de professor se existir"""
        from src.models.academic import Professor
        return Professor.query.filter_by(user_id=self.id).first()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'current_xp': self.current_xp,
            'current_level': self.current_level,
            'coins': self.coins,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class Mission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    xp_reward = db.Column(db.Integer, default=0)
    coin_reward = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_missions = db.relationship('UserMission', backref='mission', lazy=True)
    creator = db.relationship('User', backref='created_missions', foreign_keys=[created_by])

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'xp_reward': self.xp_reward,
            'coin_reward': self.coin_reward,
            'is_active': self.is_active,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class UserMission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mission_id = db.Column(db.Integer, db.ForeignKey('mission.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')
    assigned_at = db.Column(db.DateTime, default=datetime.utcnow)
    completion_date = db.Column(db.DateTime)

    def complete(self):
        """Completa a missão e dá recompensas"""
        if self.status == 'pending':
            self.status = 'completed'
            self.completion_date = datetime.utcnow()

            user = User.query.get(self.user_id)
            mission = Mission.query.get(self.mission_id)

            if user and mission:
                user.add_xp(mission.xp_reward, f"mission_{mission.id}")
                user.add_coins(mission.coin_reward)
                return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'mission_id': self.mission_id,
            'status': self.status,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'completion_date': self.completion_date.isoformat() if self.completion_date else None,
            'mission': self.mission.to_dict() if self.mission else None
        }


class Achievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    xp_threshold = db.Column(db.Integer)
    level_threshold = db.Column(db.Integer)
    mission_count_threshold = db.Column(db.Integer)
    icon = db.Column(db.String(100))

    user_achievements = db.relationship('UserAchievement', backref='achievement', lazy=True)

    def check_and_award(self, user_id):
        """Verifica se o usuário merece esta conquista"""
        from sqlalchemy import func

        user = User.query.get(user_id)
        if not user:
            return False

        # Verificar thresholds
        if self.xp_threshold and user.current_xp < self.xp_threshold:
            return False
        if self.level_threshold and user.current_level < self.level_threshold:
            return False
        if self.mission_count_threshold:
            completed_missions = UserMission.query.filter_by(
                user_id=user_id, status='completed'
            ).count()
            if completed_missions < self.mission_count_threshold:
                return False

        # Verificar se já possui
        existing = UserAchievement.query.filter_by(
            user_id=user_id, achievement_id=self.id
        ).first()

        if not existing:
            new_achievement = UserAchievement(
                user_id=user_id,
                achievement_id=self.id
            )
            db.session.add(new_achievement)
            return True
        return False

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'xp_threshold': self.xp_threshold,
            'level_threshold': self.level_threshold,
            'mission_count_threshold': self.mission_count_threshold,
            'icon': self.icon
        }


class UserAchievement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievement.id'), nullable=False)
    date_achieved = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'achievement_id': self.achievement_id,
            'date_achieved': self.date_achieved.isoformat() if self.date_achieved else None,
            'achievement': self.achievement.to_dict() if self.achievement else None
        }


class Reward(db.Model):
    __tablename__ = 'reward'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    coin_cost = db.Column(db.Integer, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    icon = db.Column(db.String(10), default="🎁")
    image_url = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user_rewards = db.relationship('UserReward', backref='reward', lazy=True)

    def purchase(self, user_id):
        """Processa a compra da recompensa"""
        user = User.query.get(user_id)
        if user and user.coins >= self.coin_cost and self.is_active:
            user.spend_coins(self.coin_cost)
            user_reward = UserReward(user_id=user_id, reward_id=self.id)
            db.session.add(user_reward)
            return True
        return False

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "coin_cost": self.coin_cost,
            "is_active": self.is_active,
            "icon": self.icon,
            "image_url": self.image_url,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class UserReward(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reward_id = db.Column(db.Integer, db.ForeignKey('reward.id'), nullable=False)
    purchase_date = db.Column(db.DateTime, default=datetime.utcnow)
    is_redeemed = db.Column(db.Boolean, default=False)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'reward_id': self.reward_id,
            'purchase_date': self.purchase_date.isoformat() if self.purchase_date else None,
            'is_redeemed': self.is_redeemed,
            'reward': self.reward.to_dict() if self.reward else None
        }