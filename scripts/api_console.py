import requests
import getpass
import sys
import os
from pathlib import Path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.core.config import load_default_config

BASE_URL = load_default_config().get("base_url", "http://localhost:8000")

def extrair_resposta_final(data):
    resposta_raw = data.get("response")
    
    if isinstance(resposta_raw, str):
        return resposta_raw
    elif isinstance(resposta_raw, dict):
        # fallback para formatos com messages, se você voltar a usar isso no futuro
        messages = resposta_raw.get("messages", [])
        if messages:
            return messages[-1].get("content", "")
    return "⚠️ Resposta malformada ou vazia"

def login(username: str, password: str) -> str:
    resp = requests.post(f"{BASE_URL}/login", data={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def query(prompt: str, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/agent/query", json={"prompt": prompt}, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    resposta = extrair_resposta_final(data)
    return resposta


def main() -> None:
    user = input("Usuário: ") or 'elian'
    password = input("Senha: ") or 'teste123'
    token = login(user, password)
    print("🔑 Autenticado com sucesso!")

    while True:
        prompt = input("\n📝 Pergunta: ")
        if prompt.lower() in {"exit", "quit", "sair"}:
            print("Até logo!")
            break
        if not prompt:
            continue
        response = query(prompt, token)
        print(f"🤖 Resposta: {response}")


if __name__ == "__main__":
    main()