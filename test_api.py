# test_api.py
import requests
import json

BASE_URL = "http://localhost:5000"

def test_login():
    print("🔐 Testando login...")
    response = requests.post(
        f"{BASE_URL}/api/login",
        json={"username": "admin", "password": "admin123"},
        headers={"Content-Type": "application/json"}
    )
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")
    return response.cookies

def test_auth_me(cookies):
    print("\n🔍 Testando /api/auth/me...")
    response = requests.get(
        f"{BASE_URL}/api/auth/me",
        cookies=cookies
    )
    print(f"Status: {response.status_code}")
    print(f"Resposta: {response.json()}")

def test_disciplines(cookies):
    print("\n📚 Testando /api/disciplines...")
    response = requests.get(
        f"{BASE_URL}/api/disciplines",
        cookies=cookies
    )
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        data = response.json()
        print(f"Total de disciplinas: {len(data.get('disciplines', []))}")
    else:
        print(f"Erro: {response.text}")

if __name__ == "__main__":
    cookies = test_login()
    if cookies:
        test_auth_me(cookies)
        test_disciplines(cookies)