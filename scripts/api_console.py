import requests
import getpass

BASE_URL = "http://localhost:8000"


def login(username: str, password: str) -> str:
    resp = requests.post(f"{BASE_URL}/login", data={"username": username, "password": password})
    resp.raise_for_status()
    return resp.json()["access_token"]


def query(prompt: str, token: str) -> str:
    headers = {"Authorization": f"Bearer {token}"}
    resp = requests.post(f"{BASE_URL}/agent/query", json={"prompt": prompt}, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    return data.get("response", "")


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