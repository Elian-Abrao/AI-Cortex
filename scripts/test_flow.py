"""Exemplo de autenticação e consulta ao agente via API."""

import getpass
import requests
from typing import Optional
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from src.core.config import load_default_config

__test__ = False

BASE_URL = load_default_config().get("base_url", "http://localhost:8000")


def login(username: str, password: str) -> str:
    resp = requests.post(f"{BASE_URL}/login", data={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def query(prompt: str, token: str) -> dict:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/agent/query", json={"prompt": prompt}, headers=headers)
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    user = input("Usuário: ")
    passwd = getpass.getpass("Senha: ")
    token = login(user, passwd)
    print("🔑 Login ok! Enviando pergunta...")
    pergunta = input("Pergunta: ")
    data = query(pergunta, token)
    print(f"Resposta: {data.get('response')}")


if __name__ == "__main__":
    main()