"""Estado operacional da instância: sessões, contador de strikes e log.

Sessões guardam o histórico conversacional e o estado volátil dos modos
multi-turno (`//alibi` Tempo 2, modo METATRON).
"""

from __future__ import annotations

import json
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def default_state() -> dict[str, Any]:
    return {
        "foco": None,
        "profundidade": "padrão",
        "modo": "padrão",
        "dry_run": False,
        "alibi": None,
        "metatron": None,
    }


@dataclass
class Session:
    id: str
    created_at: str
    history: list[dict[str, str]] = field(default_factory=list)
    state: dict[str, Any] = field(default_factory=default_state)
    last_reply: str = ""
    last_trace: dict[str, Any] = field(default_factory=dict)
    checkpoint: dict[str, Any] | None = None

    def recent(self, limit: int = 12) -> list[dict[str, str]]:
        return self.history[-limit:]

    def to_json(self) -> dict[str, Any]:
        return asdict(self)


class SessionStore:
    """Sessões vivas em memória, espelhadas em disco."""

    def __init__(self, directory: Path | None = None, max_history: int | None = None) -> None:
        self._dir = Path(directory or settings.session_dir)
        self._max = max_history or settings.max_history
        self._lock = threading.RLock()
        self._cache: dict[str, Session] = {}

    def get(self, session_id: str | None) -> Session:
        with self._lock:
            if session_id and session_id in self._cache:
                return self._cache[session_id]

            if session_id:
                path = self._dir / f"{session_id}.json"
                if path.exists():
                    try:
                        data = json.loads(path.read_text(encoding="utf-8"))
                        session = Session(**data)
                        self._cache[session.id] = session
                        return session
                    except (json.JSONDecodeError, OSError, TypeError):
                        pass

            session = Session(id=session_id or uuid.uuid4().hex[:12], created_at=now())
            self._cache[session.id] = session
            return session

    def save(self, session: Session) -> None:
        with self._lock:
            if len(session.history) > self._max:
                session.history = session.history[-self._max :]
            try:
                self._dir.mkdir(parents=True, exist_ok=True)
                (self._dir / f"{session.id}.json").write_text(
                    json.dumps(session.to_json(), ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except OSError:
                pass

    def delete(self, session_id: str) -> bool:
        with self._lock:
            self._cache.pop(session_id, None)
            path = self._dir / f"{session_id}.json"
            if not path.exists():
                return False
            try:
                path.unlink()
                return True
            except OSError:
                return False


class StrikeRegister:
    """Contador sancionatório da instância (Gatilhos §3)."""

    def __init__(self, path: Path | None = None, limit: int | None = None) -> None:
        self._path = Path(path or settings.strike_file)
        self._limit = limit or settings.strike_limit
        self._lock = threading.RLock()
        self._data = self._load()

    @property
    def limit(self) -> int:
        return self._limit

    @property
    def count(self) -> int:
        return int(self._data.get("contador", 0))

    @property
    def instances(self) -> int:
        return int(self._data.get("instancias", 1))

    def history(self) -> list[dict[str, Any]]:
        return list(self._data.get("historico", []))

    def register(self, referencia: str, resumo: str) -> int:
        with self._lock:
            self._data["contador"] = self.count + 1
            self._data.setdefault("historico", []).append(
                {"em": now(), "referencia": referencia or "não informada", "resumo": resumo}
            )
            self._save()
            return self.count

    def exceeded(self) -> bool:
        return self.count >= self._limit

    def reboot(self) -> None:
        """Encerra a instância corrente e reinicia o contador sancionatório."""
        with self._lock:
            self._data["instancias"] = self.instances + 1
            self._data["contador"] = 0
            self._data["historico"] = []
            self._data["ultimo_bootstrap"] = now()
            self._save()

    def report(self) -> dict[str, Any]:
        return {
            "contador": self.count,
            "limite": self._limit,
            "instancias": self.instances,
            "historico": self.history(),
        }

    def _load(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    return data
            except (json.JSONDecodeError, OSError):
                pass
        return {"contador": 0, "instancias": 1, "historico": []}

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(self._data, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass


class Logbook:
    """Registro append-only de decisões arquiteturais (//log, checkpoints, patches)."""

    def __init__(self, path: Path | None = None) -> None:
        self._path = Path(path or settings.log_file)
        self._lock = threading.RLock()

    def append(self, tipo: str, resumo: str, detalhes: dict[str, Any] | None = None) -> dict[str, Any]:
        entry = {"em": now(), "tipo": tipo, "resumo": resumo, "detalhes": detalhes or {}}
        with self._lock:
            try:
                self._path.parent.mkdir(parents=True, exist_ok=True)
                with self._path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
            except OSError:
                pass
        return entry

    def read(self, limit: int = 50) -> list[dict[str, Any]]:
        if not self._path.exists():
            return []
        entries: list[dict[str, Any]] = []
        try:
            for line in self._path.read_text(encoding="utf-8").splitlines():
                stripped = line.strip()
                if not stripped:
                    continue
                try:
                    entries.append(json.loads(stripped))
                except json.JSONDecodeError:
                    continue
        except OSError:
            return []
        return entries[-limit:]