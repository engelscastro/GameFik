import os
import sys
import sqlite3
from sqlalchemy import text

# ============= IMPORTS FLASK E EXTENSÕES =============
from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS

# ============= IMPORTS DE MODELOS =============
from src.models.user import db, User, Achievement

# ============= IMPORTS DE BLUEPRINTS =============
from src.routes.user_routes import user_bp
from src.routes.mission_routes import mission_bp
from src.routes.achievement_routes import achievement_bp
from src.routes.reward_routes import reward_bp
from src.routes.discipline_routes import discipline_bp
from src.routes.admin_routes import admin_bp
from src.routes.professor_routes import professor_bp
from src.routes.student_routes import student_bp
from src.routes.enrollment_routes import enrollment_bp
from src.routes.grade_routes import grade_bp
from src.blueprints.chat import chat_bp

# ============= CONFIGURAR PATHS =============
currentdir = os.path.dirname(__file__)  # Pasta src onde está o main.py
staticfolder_path = os.path.join(currentdir, "static")  # Caminho para src/static
database_path = os.path.join(os.path.dirname(currentdir), "database")  # gamefik-system/database

if not os.path.exists(database_path):
    os.makedirs(database_path)

# Aponta para gamefik-system (uma pasta acima de src)
sys.path.insert(0, os.path.dirname(currentdir))

# ============= CRIAR APLICAÇÃO FLASK =============
app = Flask(__name__, static_folder=staticfolder_path)

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
try:
    # Registrar todos os blueprints aqui (centralizado no main)
    blueprints = [
        ("user", user_bp),
        ("mission", mission_bp),
        ("achievement", achievement_bp),
        ("reward", reward_bp),
        ("discipline", discipline_bp),
        ("admin", admin_bp),         # url_prefix do blueprint: '/admin' → final: /api/admin/...
        ("professor", professor_bp),
        ("student", student_bp),
        ("enrollment", enrollment_bp),
        ("grade", grade_bp),
        ("chat", chat_bp),
    ]

    for name, bp in blueprints:
        app.register_blueprint(bp, url_prefix="/api")
        print(f"✅ {name} registrado com sucesso!")

    print("\n✅ Todos os blueprints registrados com sucesso!")

except Exception as e:
    print(f"❌ Erro crítico ao registrar blueprints: {e}")
    import traceback

    traceback.print_exc()
    sys.exit(1)

# ============= ROTAS DE DEBUG =============


@app.route("/api/debug/routes", methods=["GET"])
def debug_routes():
    """Lista todas as rotas disponíveis no sistema"""
    try:
        routes = []
        for rule in app.url_map.iter_rules():
            if "static" not in rule.endpoint:
                routes.append(
                    {
                        "endpoint": rule.endpoint,
                        "methods": list(rule.methods),
                        "path": str(rule),
                    }
                )

        # Agrupar rotas por categoria
        routes_by_category = {
            "user": [r for r in routes if "user" in r["endpoint"]],
            "mission": [r for r in routes if "mission" in r["endpoint"]],
            "achievement": [r for r in routes if "achievement" in r["endpoint"]],
            "reward": [r for r in routes if "reward" in r["endpoint"]],
            "discipline": [r for r in routes if "discipline" in r["endpoint"]],
            "professor": [r for r in routes if "professor" in r["endpoint"]],
            "student": [r for r in routes if "student" in r["endpoint"]],
            "enrollment": [r for r in routes if "enrollment" in r["endpoint"]],
            "grade": [r for r in routes if "grade" in r["endpoint"]],
            "chat": [r for r in routes if "chat" in r["endpoint"]],
            "other": [
                r
                for r in routes
                if not any(
                    keyword in r["endpoint"]
                    for keyword in [
                        "user",
                        "mission",
                        "achievement",
                        "reward",
                        "discipline",
                        "professor",
                        "student",
                        "enrollment",
                        "grade",
                        "chat",
                    ]
                )
            ],
        }

        categories_summary = {
            category: len(routes_list)
            for category, routes_list in routes_by_category.items()
            if routes_list
        }

        return jsonify(
            {
                "success": True,
                "total_routes": len(routes),
                "routes": sorted(routes, key=lambda x: x["path"]),
                "routes_by_category": routes_by_category,
                "categories_summary": categories_summary,
            }
        )
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
                    blueprint_routes.append(
                        {
                            "endpoint": rule.endpoint,
                            "methods": list(rule.methods),
                            "path": str(rule),
                        }
                    )

            blueprints_info.append(
                {
                    "name": name,
                    "url_prefix": blueprint.url_prefix,
                    "total_routes": len(blueprint_routes),
                    "routes": blueprint_routes,
                }
            )

        return jsonify(
            {
                "success": True,
                "total_blueprints": len(blueprints_info),
                "blueprints": blueprints_info,
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/debug/system-status", methods=["GET"])
def debug_system_status():
    """Status completo do sistema"""
    try:
        with app.app_context():
            # Verificar tabelas do banco
            result = db.session.execute(
                text("SELECT name FROM sqlite_master WHERE type='table'")
            )
            tables = [row[0] for row in result]

            # Contar registros nas principais tabelas
            counts = {}
            for table in [
                "user",
                "student",
                "professor",
                "discipline",
                "enrollment",
                "mission",
                "achievement",
                "reward",
            ]:
                if table in tables:
                    try:
                        count_result = db.session.execute(
                            text(f"SELECT COUNT(*) FROM {table}")
                        )
                        counts[table] = count_result.scalar()
                    except Exception:
                        counts[table] = "erro"
                else:
                    counts[table] = "tabela não existe"

        return jsonify(
            {
                "success": True,
                "system": {
                    "tables": tables,
                    "record_counts": counts,
                    "total_blueprints": len(app.blueprints),
                    "total_routes": len(
                        [r for r in app.url_map.iter_rules() if "static" not in r.endpoint]
                    ),
                },
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/debug/modals", methods=["GET"])
def debug_modals():
    """Verifica as rotas necessárias para os modais"""
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
                    route_path in str(rule) for rule in app.url_map.iter_rules()
                )
                available_routes[modal][route_name] = {
                    "path": route_path,
                    "available": route_exists,
                }

        return jsonify(
            {
                "success": True,
                "modal_routes": available_routes,
                "message": "Diagnóstico completo das rotas dos modais",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/api/debug/check-data", methods=["GET"])
def check_data_existence():
    """Verifica os dados SEM importar modelos - evita conflitos"""
    try:
        tables = [
            "discipline",
            "mission",
            "student",
            "professor",
            "enrollment",
            "achievement",
            "user",
            "reward",
        ]
        results = {}

        for table in tables:
            try:
                query = text(f"SELECT COUNT(*) as count FROM {table}")
                result = db.session.execute(query).fetchone()
                results[table] = result[0] if result else 0
            except Exception as e:
                print(f"Erro na tabela {table}: {e}")
                results[table] = 0

        return jsonify(
            {
                "success": True,
                "counts": results,
                "message": "Contagem direta do banco - sem conflitos",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ============= VERIFICAÇÃO E INICIALIZAÇÃO DO BANCO =============


def check_database_schema():
    """Verifica o schema atual do banco de dados"""
    try:
        print("\n🔍 DIAGNÓSTICO DO SCHEMA DO BANCO DE DADOS")
        result = db.session.execute(
            text("SELECT name FROM sqlite_master WHERE type='table'")
        )
        tables = [row[0] for row in result]
        print(f" Tabelas existentes: {tables}")

        for table in ["student", "professor", "discipline"]:
            if table in tables:
                result = db.session.execute(text(f"PRAGMA table_info({table})"))
                columns = [row[1] for row in result]
                print(f" {table}: {columns}")
        print("✅ Diagnóstico completo\n")
    except Exception as e:
        print(f"❌ Erro no diagnóstico: {e}")


def run_migrations():
    """Executa todas as migrações necessárias"""
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
            result = db.session.execute(
                text(f"PRAGMA table_info({migration['table']})")
            )
            columns = [row[1] for row in result]

            if migration["column"] not in columns:
                print(
                    f" Adicionando coluna {migration['column']} à tabela {migration['table']}..."
                )
                db.session.execute(
                    text(
                        f"ALTER TABLE {migration['table']} "
                        f"ADD COLUMN {migration['column']} {migration['type']}"
                    )
                )
                db.session.commit()
                print(
                    f" ✅ Coluna {migration['column']} adicionada com sucesso à tabela {migration['table']}!"
                )
            else:
                print(
                    f" ℹ️ Coluna {migration['column']} já existe na tabela {migration['table']}"
                )
        except Exception as e:
            print(f" ❌ Erro na migração {migration['description']}: {e}")
            db.session.rollback()


def verify_migration():
    """Verifica se todas as migrações foram aplicadas com sucesso"""
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
                    print(f" ✅ Coluna {column} existe na tabela {table}")
                except Exception:
                    print(f" ❌ Coluna {column} NÃO existe na tabela {table}")
                    all_success = False

        if all_success:
            print(" ✅ Todas as migrações foram aplicadas com sucesso!")
        else:
            print(" ⚠️ Algumas migrações podem ter falhado")

        print("✅ FIM DA VERIFICAÇÃO\n")
        return all_success
    except Exception as e:
        print(f"❌ Erro na verificação: {e}")
        return False


# ============= VERIFICAR ARQUIVOS ESTÁTICOS =============
print("\n🔍 Verificando estrutura de pastas...")
static_files_to_check = [
    "index.html",
    "js/app.js",
    "js/modals.js",
    "js/grade-selector.js",
    "css/main.css",
    "css/gamer-effects.css",
    "images/GamiBot.png",
]

for file_name in static_files_to_check:
    full_path = os.path.join(staticfolder_path, file_name)
    exists = os.path.exists(full_path)
    status = "✅" if exists else "❌"
    print(f" {status} {file_name}")

# ============= INICIALIZAR APLICAÇÃO =============
with app.app_context():
    print("\n🔧 Criando tabelas...")

    # Importar modelos acadêmicos para garantir criação das tabelas
    from src.models.academic import (
        Discipline,
        Professor,
        Student,
        Enrollment,
        Grade,
        AcademicMission,
        DisciplineChat,
        ChatMessage,
    )

    db.create_all()
    print(" ✅ Tabelas criadas!")

    # Executar diagnóstico
    check_database_schema()

    # Executar migrações
    print("🔧 Executando migrações...")
    run_migrations()

    # Verificar migrações
    migration_success = verify_migration()

    # Criar usuário admin se não existir
    admin_user = User.query.filter_by(username="admin").first()
    if not admin_user:
        admin_user = User(username="admin", role="admin")
        admin_user.set_password("admin123")
        db.session.add(admin_user)
        db.session.commit()
        print("✅ Usuário admin criado!")

    # Criar algumas conquistas padrão se não existirem
    if Achievement.query.count() == 0:
        achievements = [
            Achievement(
                name="Primeiro Passo",
                description="Complete sua primeira missão",
                mission_count_threshold=1,
                icon="🎯",
            ),
            Achievement(
                name="Iniciante",
                description="Alcance o nível 2",
                level_threshold=2,
                icon="⭐",
            ),
            Achievement(
                name="Explorador",
                description="Acumule 100 XP",
                xp_threshold=100,
                icon="🗺️",
            ),
            Achievement(
                name="Veterano",
                description="Complete 10 missões",
                mission_count_threshold=10,
                icon="🏆",
            ),
            Achievement(
                name="Mestre",
                description="Alcance o nível 5",
                level_threshold=5,
                icon="👑",
            ),
            Achievement(
                name="Lenda",
                description="Acumule 1000 XP",
                xp_threshold=1000,
                icon="💎",
            ),
        ]

        for achievement in achievements:
            db.session.add(achievement)
        db.session.commit()
        print("✅ Conquistas padrão criadas!")

    print("\n✅ Sistema inicializado com sucesso!")


# ============= ROTA PARA SERVIR ARQUIVOS ESTÁTICOS =============
@app.route("/", defaults={"path": ""})
@app.route("/<path:path>")
def serve_path(path):
    """Serve arquivos estáticos ou redireciona para index.html"""
    static_folder_path = app.static_folder

    if static_folder_path is None:
        return "Static folder not configured", 404

    file_path = os.path.join(static_folder_path, path)
    print(f" Solicitado: {path} - Existe: {os.path.exists(file_path)}")

    if path != "" and os.path.exists(file_path):
        print(f" ✅ Servindo arquivo: {path}")
        return send_from_directory(static_folder_path, path)
    else:
        print(f" ❌ Arquivo não encontrado: {path}, servindo index.html")
        index_path = os.path.join(static_folder_path, "index.html")
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, "index.html")
        else:
            return "index.html not found", 404


# ============= EXECUTAR APLICAÇÃO =============
if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("🚀 INICIANDO SISTEMA GAMER ÉPICO...")
    print("=" * 70)
    print("📍 URL: http://localhost:5000")
    print("🐛 Modo Debug: Ativado")
    print("\n📊 ROTAS DE DEBUG DISPONÍVEIS:")
    print(" • http://localhost:5000/api/debug/routes")
    print(" • http://localhost:5000/api/debug/blueprints")
    print(" • http://localhost:5000/api/debug/system-status")
    print(" • http://localhost:5000/api/debug/modals")
    print(" • http://localhost:5000/api/debug/check-data")
    print("=" * 70 + "\n")

    app.run(host="0.0.0.0", port=5000, debug=True)