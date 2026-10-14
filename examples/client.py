"""Cliente de linha de comando para a API HomoBinário.

Uso:
    python examples/client.py

Variáveis de ambiente:
    HOMOBINARIO_API_URL   (padrão: http://127.0.0.1:8000)
    HOMOBINARIO_API_TOKEN (opcional, se a API exigir credencial)
"""

from __future__ import annotations

import os
import sys

import requests

BASE = os.getenv("HOMOBINARIO_API_URL", "http://127.0.0.1:8000").rstrip("/")
TOKEN = os.getenv("HOMOBINARIO_API_TOKEN", "").strip()


def headers() -> dict[str, str]:
    return {"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}


def main() -> int:
    try:
        saude = requests.get(f"{BASE}/health", headers=headers(), timeout=10).json()
    except requests.RequestException as exc:
        print(f"API inacessível em {BASE}: {exc}")
        return 1

    print(f"HomoBinário · KDPROJECT — modelo: {saude.get('modelo')}")
    ausentes = saude.get("componentes_ausentes") or []
    print(f"Componentes ausentes: {', '.join(ausentes) or '—'}")
    if not saude.get("pronta"):
        print("A instância não opera: componentes críticos ausentes.")
        return 1

    print("Gatilhos: //status · //focus [tópico] · //memory review · //alibi · //agamoto · //scribae")
    print("Digite 'sair' para encerrar.\n")

    session_id: str | None = None
    while True:
        try:
            entrada = input("Túlio › ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if not entrada:
            continue
        if entrada.lower() in {"sair", "exit", "quit"}:
            break

        try:
            resposta = requests.post(
                f"{BASE}/chat",
                headers=headers(),
                json={"message": entrada, "session_id": session_id},
                timeout=300,
            )
        except requests.RequestException as exc:
            print(f"Falha na requisição: {exc}")
            continue

        if resposta.status_code != 200:
            print(f"[{resposta.status_code}] {resposta.text}")
            continue

        dados = resposta.json()
        session_id = dados.get("session_id")
        if dados.get("gatilho"):
            print(f"[gatilho: {dados['gatilho']} · strikes: {dados.get('strikes')}]")
        print(f"\nKael › {dados.get('reply')}\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())