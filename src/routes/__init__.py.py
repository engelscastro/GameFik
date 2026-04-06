# src/routes/__init__.py
"""
Inicialização das rotas do sistema
"""

import sys
from importlib import import_module

# Lista de todos os blueprints disponíveis
ALL_BLUEPRINTS = []

# Blueprints para importar (lista completa)
blueprint_modules = [
    # Blueprints principais
    'src.routes.user_routes',          # Autenticação e usuários
    'src.routes.mission_routes',       # Missões
    'src.routes.achievement_routes',   # Conquistas
    'src.routes.reward_routes',        # Recompensas/Loja

    # Blueprints acadêmicos
    'src.routes.discipline_routes',    # Disciplinas
    'src.routes.professor_routes',     # Professores (CRUD)
    'src.routes.student_routes',       # Estudantes (CRUD)
    'src.routes.enrollment_routes',    # Matrículas
    'src.routes.grade_routes',         # Notas
    'src.routes.chat_routes',          # Chat

    # Blueprint de administração (NOVO)
    'src.routes.admin_routes',         # Admin - gestão completa
]

# Importar dinamicamente todos os blueprints
for module_name in blueprint_modules:
    try:
        module = import_module(module_name)

        # Extrair o nome do blueprint baseado no módulo
        bp_name = module_name.split('.')[-1].replace('_routes', '')

        # Tenta encontrar o blueprint com diferentes padrões de nome
        blueprint = None

        # Padrão 1: nome_bp (ex: user_bp, admin_bp)
        if hasattr(module, f"{bp_name}_bp"):
            blueprint = getattr(module, f"{bp_name}_bp")

        # Padrão 2: nomes específicos
        elif hasattr(module, 'mission_bp'):
            blueprint = getattr(module, 'mission_bp')
        elif hasattr(module, 'achievement_bp'):
            blueprint = getattr(module, 'achievement_bp')
        elif hasattr(module, 'reward_bp'):
            blueprint = getattr(module, 'reward_bp')
        elif hasattr(module, 'discipline_bp'):
            blueprint = getattr(module, 'discipline_bp')
        elif hasattr(module, 'professor_bp'):
            blueprint = getattr(module, 'professor_bp')
        elif hasattr(module, 'student_bp'):
            blueprint = getattr(module, 'student_bp')
        elif hasattr(module, 'enrollment_bp'):
            blueprint = getattr(module, 'enrollment_bp')
        elif hasattr(module, 'grade_bp'):
            blueprint = getattr(module, 'grade_bp')
        elif hasattr(module, 'chat_bp'):
            blueprint = getattr(module, 'chat_bp')
        elif hasattr(module, 'admin_bp'):
            blueprint = getattr(module, 'admin_bp')

        if blueprint:
            ALL_BLUEPRINTS.append(blueprint)
            print(f"✅ {module_name} carregado (blueprint: {blueprint.name})")
        else:
            print(f"⚠️  Aviso: {module_name} não possui blueprint identificável")

    except ImportError as e:
        print(f"⚠️  Aviso: Não foi possível carregar {module_name}: {e}")
    except Exception as e:
        print(f"❌ Erro ao carregar {module_name}: {e}")

print(f"\n{'='*50}")
print(f"🎯 Módulo de rotas inicializado com {len(ALL_BLUEPRINTS)} blueprints")
for bp in ALL_BLUEPRINTS:
    print(f"   - {bp.name} ({bp.url_prefix if bp.url_prefix else '/'})")
print(f"{'='*50}")