# analyze_routes.py
def analyze_route_coverage():
    # Rotas do backend
    backend_routes = set()
    for rule in academic_bp.url_map.iter_rules():
        if 'static' not in rule.endpoint:
            backend_routes.add(f"{rule.endpoint} - {list(rule.methods)}")

    # Rotas que você conhece do frontend (adicione manualmente)
    frontend_routes = {
        "get_disciplines - ['GET']",
        "create_enrollment - ['POST']",
        "get_available_disciplines - ['GET']",
        # Adicione todas as rotas que você usa no frontend
    }

    print("=== COBERTURA DE ROTAS ===")
    print(f"Total rotas backend: {len(backend_routes)}")
    print(f"Total rotas frontend conhecidas: {len(frontend_routes)}")

    unused_routes = backend_routes - frontend_routes
    missing_routes = frontend_routes - backend_routes

    print(f"\n🔴 Rotas não utilizadas no frontend ({len(unused_routes)}):")
    for route in sorted(unused_routes):
        print(f"   - {route}")

    print(f"\n🟡 Rotas do frontend não encontradas no backend ({len(missing_routes)}):")
    for route in sorted(missing_routes):
        print(f"   - {route}")

    coverage = (len(frontend_routes) / len(backend_routes)) * 100
    print(f"\n📊 Cobertura: {coverage:.1f}%")

# Execute no seu main.py após criar o app
if __name__ == '__main__':
    analyze_route_coverage()