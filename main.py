import os
import sys
from sqlalchemy import text

# ============= IMPORTS FLASK E EXTENSÕES =============
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# ============= IMPORTS DE MODELOS =============
from src.models.user import db, User, Achievement

# ============= IMPORTS DE BLUEPRINTS (com fallback) =============
try:
    from src.routes.user_routes import user_bp
    from src.routes.mission_routes import mission_bp
    from src.routes.achievement_routes import achievement_bp
    from src.routes.reward_routes import reward_bp
    from src.routes.discipline_routes import discipline_bp
    from src.routes.admin_routes import admin_bp
    from src.routes.professor_routes import professor_bp
    from src.routes.student_routes import student_bp
    from src.blueprints.enrollment import enrollment_bp
    from src.blueprints.turma import turma_bp
    from src.routes.grade_routes import grade_bp
    from src.blueprints.chat import chat_bp
except ImportError as e:
    print(f"❌ Erro ao importar blueprints: {e}")
    sys.exit(1)

# ============= CONFIGURAR PATHS =============
currentdir = os.path.dirname(__file__)                 # raiz do projeto
static_root = os.path.join(currentdir, "static")       # static/ (landing + app)
database_path = os.path.join(currentdir, "database")

if not os.path.exists(database_path):
    os.makedirs(database_path)

# Adiciona a pasta src ao path para importar os módulos
sys.path.insert(0, os.path.join(currentdir, "src"))

# ============= CRIAR APLICAÇÃO FLASK =============
app = Flask(__name__, static_folder=static_root)       # agora aponta para static/

# ============= CONFIGURAÇÕES =============
app.config["SECRET_KEY"] = "asdfFGSgvasgf5WGT"
app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{os.path.join(database_path, 'app.db')}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# ============= CONFIGURAR CORS =============
CORS(app, supports_credentials=True)

# ============= INICIALIZAR DATABASE =============
db.init_app(app)

# ============= REGISTRAR BLUEPRINTS =============
print("🚀 Registrando blueprints...")
blueprints = [
    ("user", user_bp, "/api"),
    ("mission", mission_bp, "/api"),
    ("achievement", achievement_bp, "/api"),
    ("reward", reward_bp, "/api"),
    ("discipline", discipline_bp, "/api"),
    ("professor", professor_bp, "/api"),
    ("student", student_bp, "/api"),
    ("enrollment", enrollment_bp, "/api"),
    ("grade", grade_bp, "/api"),
    ("chat", chat_bp, "/api"),
    ("admin", admin_bp, "/api/admin"),
    ("turma", turma_bp, "/api"),
]

for name, bp, prefix in blueprints:
    try:
        app.register_blueprint(bp, url_prefix=prefix)
        print(f"✅ {name} registrado (prefixo: {prefix})")
    except Exception as e:
        print(f"❌ Falha ao registrar {name}: {e}")

print("\n✅ Todos os blueprints registrados com sucesso!")

# ============= ROTAS DE DEBUG =============
@app.route("/api/debug/routes", methods=["GET"])
def debug_routes():
    """Lista todas as rotas disponíveis no sistema"""
    try:
        routes = []
        for rule in app.url_map.iter_rules():
            if "static" not in rule.endpoint:
                routes.append({
                    "endpoint": rule.endpoint,
                    "methods": list(rule.methods),
                    "path": str(rule),
                })
        return jsonify({"success": True, "total_routes": len(routes), "routes": routes})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/debug/blueprints", methods=["GET"])
def debug_blueprints():
    """Debug dos blueprints registrados"""
    try:
        blueprints_info = []
        for name, blueprint in app.blueprints.items():
            blueprint_routes = []
            for rule in app.url_map.iter_rules():
                if rule.endpoint.startswith(name):
                    blueprint_routes.append(str(rule))
            blueprints_info.append({
                "name": name,
                "url_prefix": blueprint.url_prefix,
                "total_routes": len(blueprint_routes),
            })
        return jsonify({"success": True, "blueprints": blueprints_info})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/debug/system-status", methods=["GET"])
def debug_system_status():
    """Status completo do sistema"""
    try:
        with app.app_context():
            result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
            tables = [row[0] for row in result]
            counts = {}
            for table in ["user", "student", "professor", "discipline", "enrollment", "mission", "achievement", "reward"]:
                if table in tables:
                    try:
                        count_result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                        counts[table] = count_result.scalar()
                    except Exception:
                        counts[table] = "erro"
                else:
                    counts[table] = "tabela não existe"
        return jsonify({"success": True, "tables": tables, "record_counts": counts})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/debug/check-data", methods=["GET"])
def check_data_existence():
    """Contagem direta de registros"""
    try:
        tables = ["discipline", "mission", "student", "professor", "enrollment", "achievement", "user", "reward"]
        results = {}
        for table in tables:
            try:
                result = db.session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                results[table] = result.scalar()
            except Exception:
                results[table] = 0
        return jsonify({"success": True, "counts": results})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/debug/modals", methods=["GET"])
def debug_modals():
    """Verifica as rotas necessárias para os modais do frontend"""
    try:
        modal_routes = {
            "disciplines_modal": {
                "get_disciplines": "/api/disciplines",
                "create_discipline": "/api/disciplines",
                "assign_professor": "/api/disciplines/<int:discipline_id>/assign-professor",
                "delete_discipline": "/api/disciplines/<int:discipline_id>",
                "available_disciplines": "/api/disciplines/available",
            },
            "students_modal": {
                "get_students": "/api/admin/students",
                "create_student": "/api/students",
                "delete_student": "/api/students/<int:student_id>",
                "sync_students": "/api/sync-students",
            },
            "professors_modal": {
                "get_professors": "/api/admin/professors",
                "create_professor": "/api/professors",
                "delete_professor": "/api/professors/<int:professor_id>",
            },
            "missions_modal": {
                "get_missions": "/api/missions",
                "create_mission": "/api/missions",
                "update_mission": "/api/missions/<int:mission_id>",
                "delete_mission": "/api/missions/<int:mission_id>",
            },
            "enrollments_modal": {
                "get_enrollments": "/api/admin/enrollments",
                "create_enrollment": "/api/enrollments",
                "create_enrollment_admin": "/api/admin/enrollments",
                "bulk_enrollment": "/api/enrollments/bulk",
                "cancel_enrollment": "/api/enrollments/<int:enrollment_id>",
            },
            "grades_modal": {
                "create_grade": "/api/grades",
                "get_all_grades": "/api/admin/grades",
            },
            "achievements_modal": {
                "get_achievements": "/api/achievements",
                "create_achievement": "/api/achievements",
                "update_achievement": "/api/achievements/<int:achievement_id>",
                "delete_achievement": "/api/achievements/<int:achievement_id>",
            },
            "rewards_modal": {
                "get_rewards": "/api/rewards",
                "create_reward": "/api/rewards",
                "update_reward": "/api/rewards/<int:reward_id>",
                "delete_reward": "/api/rewards/<int:reward_id>",
                "purchase_reward": "/api/purchase-reward/<int:reward_id>",
            },
        }

        available_routes = {}
        for modal, routes in modal_routes.items():
            available_routes[modal] = {}
            for route_name, route_path in routes.items():
                route_exists = any(
                    route_path.split("<")[0] in str(rule) for rule in app.url_map.iter_rules()
                )
                available_routes[modal][route_name] = {
                    "path": route_path,
                    "available": route_exists,
                }

        return jsonify({
            "success": True,
            "modal_routes": available_routes,
            "message": "Diagnóstico completo das rotas dos modais"
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============= FUNÇÕES DE MIGRAÇÃO E VERIFICAÇÃO =============
def check_database_schema():
    """Verifica o schema atual do banco de dados"""
    try:
        print("\n🔍 DIAGNÓSTICO DO SCHEMA DO BANCO DE DADOS")
        result = db.session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result]
        print(f"   Tabelas existentes: {tables}")
        for table in ["student", "professor", "discipline"]:
            if table in tables:
                result = db.session.execute(text(f"PRAGMA table_info({table})"))
                columns = [row[1] for row in result]
                print(f"   {table}: {columns}")
        print("✅ Diagnóstico completo\n")
    except Exception as e:
        print(f"❌ Erro no diagnóstico: {e}")

def run_migrations():
    """Executa migrações de colunas adicionais"""
    migrations = [
        {"table": "professor", "column": "cpf", "type": "VARCHAR(14)", "description": "CPF professor"},
        {"table": "student", "column": "cpf", "type": "VARCHAR(14)", "description": "CPF student"},
        {"table": "student", "column": "ano_turma", "type": "VARCHAR(20)", "description": "ano_turma student"},
        {"table": "professor", "column": "anos_turmas", "type": "VARCHAR(200)", "description": "anos_turmas professor"},
        {"table": "discipline", "column": "ano_turma", "type": "VARCHAR(20)", "description": "ano_turma discipline"},
        {"table": "student", "column": "nivel_ensino", "type": "VARCHAR(50)", "description": "nivel_ensino student"},
        {"table": "discipline", "column": "nivel_ensino", "type": "VARCHAR(50)", "description": "nivel_ensino discipline"},
        {"table": "professor", "column": "niveis_ensino", "type": "VARCHAR(200)", "description": "niveis_ensino professor"},
    ]
    for migration in migrations:
        try:
            result = db.session.execute(text(f"PRAGMA table_info({migration['table']})"))
            columns = [row[1] for row in result]
            if migration["column"] not in columns:
                print(f"   Adicionando {migration['column']} em {migration['table']}...")
                db.session.execute(text(
                    f"ALTER TABLE {migration['table']} ADD COLUMN {migration['column']} {migration['type']}"
                ))
                db.session.commit()
                print(f"   ✅ {migration['column']} adicionada!")
            else:
                print(f"   ℹ️ {migration['column']} já existe em {migration['table']}")
        except Exception as e:
            print(f"   ❌ Erro em {migration['description']}: {e}")
            db.session.rollback()

def verify_migration():
    """Verifica se todas as colunas necessárias existem"""
    try:
        print("\n✅ VERIFICAÇÃO DA MIGRAÇÃO")
        tables_to_check = {
            "student": ["nivel_ensino", "ano_turma", "cpf"],
            "discipline": ["nivel_ensino", "ano_turma"],
            "professor": ["niveis_ensino", "anos_turmas", "cpf"],
        }
        all_success = True
        for table, columns in tables_to_check.items():
            for column in columns:
                try:
                    db.session.execute(text(f"SELECT {column} FROM {table} LIMIT 1"))
                    print(f"   ✅ {column} existe em {table}")
                except Exception:
                    print(f"   ❌ {column} NÃO existe em {table}")
                    all_success = False
        if all_success:
            print("   ✅ Todas as migrações OK!")
        else:
            print("   ⚠️ Algumas migrações falharam")
        return all_success
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False

# ============= VERIFICAR ARQUIVOS ESTÁTICOS =============
print("\n🔍 Verificando estrutura de pastas...")
if os.path.exists(static_root):
    # Verifica arquivos da landing page e do app
    landing_files = ["index.html", "css/styles.css", "js/app.js"]
    app_files = ["app/index.html", "app/js/app.js", "app/css/styles.css"]
    for f in landing_files:
        full = os.path.join(static_root, f)
        print(f"   {'✅' if os.path.exists(full) else '❌'} {f}")
    for f in app_files:
        full = os.path.join(static_root, f)
        print(f"   {'✅' if os.path.exists(full) else '❌'} {f}")
else:
    print(f"   ❌ Pasta static não encontrada em {static_root}")

# ============= INICIALIZAR APLICAÇÃO (cria tabelas, admin, conquistas) =============
with app.app_context():
    print("\n🔧 Criando tabelas...")
    from src.models.academic import (
        Discipline, Professor, Student, Enrollment,
        Grade, AcademicMission, DisciplineChat, ChatMessage,
        TurmaFeedPost, TurmaAssignmentSubmission
    )
    db.create_all()
    print("   ✅ Tabelas criadas!")

    check_database_schema()
    print("🔧 Executando migrações...")
    run_migrations()
    verify_migration()

    # Criar admin se não existir
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", role="admin")
        admin.set_password("admin123")
        db.session.add(admin)
        db.session.commit()
        print("✅ Usuário admin criado (admin/admin123).")

    # Criar conquistas padrão se não existirem
    if Achievement.query.count() == 0:
        achievements = [
            Achievement(name="Primeiro Passo", description="Complete sua primeira missão", mission_count_threshold=1, icon="🎯"),
            Achievement(name="Iniciante", description="Alcance o nível 2", level_threshold=2, icon="⭐"),
            Achievement(name="Explorador", description="Acumule 100 XP", xp_threshold=100, icon="🗺️"),
            Achievement(name="Veterano", description="Complete 10 missões", mission_count_threshold=10, icon="🏆"),
            Achievement(name="Mestre", description="Alcance o nível 5", level_threshold=5, icon="👑"),
            Achievement(name="Lenda", description="Acumule 1000 XP", xp_threshold=1000, icon="💎"),
        ]
        for ach in achievements:
            db.session.add(ach)
        db.session.commit()
        print("✅ Conquistas padrão criadas.")

    print("\n✅ Sistema inicializado com sucesso!")

# ============= ROTAS PARA SERVIR ARQUIVOS ESTÁTICOS =============

@app.route('/')
def landing():
    """Landing page (marketing)"""
    return send_from_directory(static_root, 'index.html')

@app.route('/css/<path:path>')
def serve_css(path):
    return send_from_directory(os.path.join(static_root, 'css'), path)

@app.route('/js/<path:path>')
def serve_js(path):
    return send_from_directory(os.path.join(static_root, 'js'), path)

@app.route('/images/<path:path>')
def serve_images(path):
    return send_from_directory(os.path.join(static_root, 'images'), path)

# Rotas para o aplicativo principal (EduQuest)
@app.route('/app')
def app_index():
    return send_from_directory(os.path.join(static_root, 'app'), 'index.html')

@app.route('/app/<path:path>')
def app_static(path):
    return send_from_directory(os.path.join(static_root, 'app'), path)

# Fallback para rotas não encontradas (opcional)
@app.errorhandler(404)
def page_not_found(e):
    return jsonify({'success': False, 'error': 'Página não encontrada'}), 404

# ============= EXECUTAR APLICAÇÃO =============
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 INICIANDO SISTEMA EDUQUEST (MODO DESENVOLVIMENTO)")
    print("=" * 70)
    print("📍 Landing page: http://localhost:5000/")
    print("📍 Sistema EduQuest: http://localhost:5000/app")
    print("🐛 Modo Debug: ATIVADO")
    print("\n📊 Rotas de debug disponíveis:")
    print("   • /api/debug/routes")
    print("   • /api/debug/blueprints")
    print("   • /api/debug/system-status")
    print("   • /api/debug/check-data")
    print("=" * 70 + "\n")
    app.run(host="0.0.0.0", port=5000, debug=True)