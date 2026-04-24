#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Verificador de Estrutura de Pastas do EduQuest - VERSÃO CORRIGIDA
"""

import os
from pathlib import Path

class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def find_file(start_path, filename):
    """Procura um arquivo recursivamente"""
    for root, dirs, files in os.walk(start_path):
        if filename in files:
            return Path(root)
    return None

def main():
    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}🔍 EDUQUEST - LOCALIZADOR DE ARQUIVOS{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    base_path = Path(__file__).parent
    print(f"{Colors.BLUE}📁 Projeto em: {base_path}{Colors.RESET}\n")

    # Procurar arquivos importantes
    print(f"{Colors.YELLOW}🔍 Procurando arquivos do sistema...{Colors.RESET}\n")

    files_to_find = [
        "main.py",
        "index.html",
        "app.js",
        "academic-teacher-system.js",
        "styles.css"
    ]

    found_locations = {}

    for filename in files_to_find:
        location = find_file(base_path, filename)
        if location:
            found_locations[filename] = location
            print(f"  {Colors.GREEN}✅{Colors.RESET} {filename} encontrado em: {location}")
        else:
            print(f"  {Colors.RED}❌{Colors.RESET} {filename} NÃO encontrado")

    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}📁 ESTRUTURA COMPLETA DO PROJETO{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}\n")

    # Listar todas as pastas e arquivos importantes
    for root, dirs, files in os.walk(base_path):
        # Ignorar pastas de sistema
        if '__pycache__' in root or '.git' in root or 'venv' in root or 'env' in root:
            continue

        nivel = root.replace(str(base_path), '').count(os.sep)
        if nivel <= 3:  # Mostrar até 3 níveis de profundidade
            indent = '  ' * nivel
            folder_name = os.path.basename(root)
            if folder_name and folder_name != 'gamefik-system':
                print(f"{indent}📁 {folder_name}/")

                # Mostrar alguns arquivos importantes
                for file in files[:5]:  # Limitar a 5 arquivos por pasta
                    if file.endswith(('.py', '.html', '.js', '.css', '.db')):
                        print(f"{indent}  📄 {file}")
                if len(files) > 5:
                    print(f"{indent}  ... e mais {len(files)-5} arquivos")

    print(f"\n{Colors.CYAN}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}📊 RESUMO FINAL{Colors.RESET}")
    print(f"{Colors.CYAN}{'='*60}{Colors.RESET}")

    # Sugestões baseado no que foi encontrado
    if 'index.html' in found_locations:
        html_path = found_locations['index.html']
        print(f"\n{Colors.GREEN}✅ Seus arquivos estáticos estão em: {html_path}{Colors.RESET}")
        print(f"{Colors.BLUE}💡 O arquivo classroom-manager.js deve ser salvo em:{Colors.RESET}")
        print(f"   {html_path}/js/classroom-manager.js")
    else:
        print(f"\n{Colors.RED}❌ Não foi possível localizar a pasta de arquivos estáticos{Colors.RESET}")
        print(f"{Colors.YELLOW}💡 Procure manualmente onde está seu index.html{Colors.RESET}")

if __name__ == "__main__":
    main()