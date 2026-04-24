"""
Módulo de blueprints acadêmicos refatorados
Facilita o registro de todos os blueprints no aplicativo Flask
"""

from .discipline import discipline_bp
from .professor import professor_bp
# from .student import student_bp  ← REMOVA ESTA LINHA (comente ou delete)
from .enrollment import enrollment_bp
from .grade import grade_bp
from .chat import chat_bp
from .admin import admin_bp  # NOVO: Blueprint do administrador master


def register_blueprints(app, url_prefix='/api'):
    """
    Registra todos os blueprints acadêmicos no aplicativo Flask

    Args:
        app: Instância do Flask
        url_prefix: Prefixo de URL para todos os blueprints (padrão: '/api')
    """

    # Registrar cada blueprint
    app.register_blueprint(discipline_bp, url_prefix=url_prefix)
    app.register_blueprint(professor_bp, url_prefix=url_prefix)
    # app.register_blueprint(student_bp, url_prefix=url_prefix)  ← REMOVA ESTA LINHA
    app.register_blueprint(enrollment_bp, url_prefix=url_prefix)
    app.register_blueprint(grade_bp, url_prefix=url_prefix)
    app.register_blueprint(chat_bp, url_prefix=url_prefix)
    app.register_blueprint(admin_bp, url_prefix=url_prefix)  # NOVO: Admin master

    print("✅ Todos os blueprints acadêmicos foram registrados com sucesso!")
    print(f"   - Discipline Blueprint ({url_prefix})")
    print(f"   - Professor Blueprint ({url_prefix})")
    print(f"   - Enrollment Blueprint ({url_prefix})")
    print(f"   - Grade Blueprint ({url_prefix})")
    print(f"   - Chat Blueprint ({url_prefix})")
    print(f"   - Admin Blueprint ({url_prefix}) [CONTROLE MASTER]")


__all__ = [
    'discipline_bp',
    'professor_bp',
    # 'student_bp',  ← REMOVA ESTA LINHA
    'enrollment_bp',
    'grade_bp',
    'chat_bp',
    'admin_bp',
    'register_blueprints'
]