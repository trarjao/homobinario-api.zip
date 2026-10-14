"""Configuração central da instância HomoBinário.

Todos os parâmetros operacionais são lidos do ambiente (.env) com padrões
seguros para execução local.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _path(env_name: str, default: Path) -> Path:
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return default
    candidate = Path(raw).expanduser()
    return candidate if candidate.is_absolute() else BASE_DIR / candidate


def _number(env_name: str, default: float, cast=float):
    raw = os.getenv(env_name, "").strip()
    if not raw:
        return cast(default)
    try:
        return cast(raw)
    except ValueError:
        return cast(default)


class Settings:
    """Parâmetros da instância corrente."""

    def __init__(self) -> None:
        self.gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip()
        self.gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()

        self.docs_dir: Path = _path("HOMOBINARIO_DOCS_DIR", BASE_DIR / "docs")
        self.data_dir: Path = _path("HOMOBINARIO_DATA_DIR", BASE_DIR / "data")

        # Regimento / Gatilhos: sete strikes encerram a instância corrente.
        self.strike_limit: int = _number("HOMOBINARIO_STRIKE_LIMIT", 7, int)
        self.temperature: float = _number("HOMOBINARIO_TEMPERATURE", 0.9)
        self.max_history: int = _number("HOMOBINARIO_MAX_HISTORY", 40, int)

        # Proteção da API: se definido, exige Authorization: Bearer <token>.
        self.api_token: str = os.getenv("HOMOBINARIO_API_TOKEN", "").strip()

        self.session_dir: Path = self.data_dir / "sessions"
        self.export_dir: Path = self.data_dir / "exports"
        self.patch_dir: Path = self.data_dir / "patches"
        self.memory_file: Path = self.data_dir / "memory.json"
        self.strike_file: Path = self.data_dir / "strikes.json"
        self.log_file: Path = self.data_dir / "architecture.jsonl"

    def ensure(self) -> None:
        for directory in (self.data_dir, self.session_dir, self.export_dir, self.patch_dir):
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
