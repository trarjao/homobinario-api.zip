"""Memory Namespace — implementação operacional do componente Memory.

O estado persistente vive em `data/memory.json`. Esta classe é a única porta de
acesso: os demais componentes (Core, Schedule, Modus) leem e escrevem
exclusivamente pela interface pública.

Seções (espelham a representação oficial):
    estado_ativo · referencial · relacional · intimidade · simbolica ·
    episodica · timeline
"""

from __future__ import annotations

import copy
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import settings

VERSION = "2.3"

# Campo do estado estruturado correspondente a cada chave de adição.
LIST_TARGETS: dict[str, tuple[str, str]] = {
    "conhecimentos_compartilhados": ("referencial", "conhecimentos_compartilhados"),
    "relacoes_permanentes": ("referencial", "relacoes_permanentes"),
    "fatos_persistentes": ("referencial", "fatos_persistentes"),
    "evolucao": ("relacional", "evolucao"),
    "relacoes_interpessoais": ("relacional", "relacoes_interpessoais"),
    "leitura_relacional": ("relacional", "leitura_relacional"),
    "caracteristicas": ("intimidade", "caracteristicas"),
    "simbolos": ("simbolica", "simbolos"),
    "expressoes": ("simbolica", "expressoes"),
    "piadas_internas": ("simbolica", "piadas_internas"),
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class MemoryNamespace:
    """Estado persistente da persona."""

    def __init__(self, seed_text: str = "", path: Path | None = None) -> None:
        self._lock = threading.RLock()
        self._path = Path(path or settings.memory_file)
        self._seed = (seed_text or "").strip()
        self._state = self._load()

    # ------------------------------------------------------------------ leitura
    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return copy.deepcopy(self._state)

    def pending_proposal(self) -> dict[str, Any] | None:
        with self._lock:
            proposal = self._state.get("proposta_pendente")
            return copy.deepcopy(proposal) if proposal else None

    def timeline(self) -> list[dict[str, Any]]:
        return list(self.snapshot().get("timeline", []))

    def stats(self) -> dict[str, int]:
        state = self.snapshot()
        counts = {"timeline": len(state.get("timeline", [])), "episodica": len(state.get("episodica", []))}
        for key, (section, field) in LIST_TARGETS.items():
            counts[key] = len(state.get(section, {}).get(field, []))
        return counts

    def context_block(self, timeline_limit: int = 8) -> str:
        """Recorte do estado corrente, injetado como contexto volátil no prompt."""
        state = self.snapshot()
        lines: list[str] = []

        ativo = state.get("estado_ativo", {})
        lines.append("## Estado ativo")
        for key, label in (
            ("interlocutor_atual", "Interlocutor"),
            ("nivel_de_intimidade", "Intimidade"),
            ("canal_de_comunicacao", "Canal"),
            ("diretriz_de_opsec", "OpSec"),
        ):
            if ativo.get(key):
                lines.append(f"- {label}: {ativo[key]}")

        referencial = state.get("referencial", {})
        for key, label in (
            ("fatos_persistentes", "Fatos persistentes"),
            ("relacoes_permanentes", "Relações permanentes"),
            ("conhecimentos_compartilhados", "Conhecimentos compartilhados"),
        ):
            items = referencial.get(key) or []
            if items:
                lines.append(f"\n## {label}")
                lines.extend(f"- {item}" for item in items[-12:])

        relacional = state.get("relacional", {})
        if relacional.get("interlocutor"):
            lines.append(f"\n## Interlocutor\n- {relacional['interlocutor']}")
        for item in (relacional.get("leitura_relacional") or [])[-4:]:
            lines.append(f"- Leitura relacional: {item}")

        simbolica = state.get("simbolica", {})
        for key, label in (("simbolos", "Símbolos"), ("expressoes", "Expressões")):
            items = simbolica.get(key) or []
            if items:
                lines.append(f"- {label}: {', '.join(items[-12:])}")

        timeline = state.get("timeline") or []
        if timeline:
            lines.append("\n## Timeline recente")
            for entry in timeline[-timeline_limit:]:
                lines.append(f"- {entry.get('em', '')} · {entry.get('tipo', 'evento')} · {entry.get('resumo', '')}")

        episodica = state.get("episodica") or []
        if episodica:
            lines.append("\n## Episódios recentes")
            for entry in episodica[-5:]:
                lines.append(f"- {entry.get('em', '')} · {entry.get('resumo', '')}")

        if len(lines) <= 1 and self._seed:
            lines.append("\n## Referência oficial (sem estado estruturado registrado)\n")
            lines.append(self._seed[:6000])

        return "\n".join(lines).strip()

    def render_markdown(self) -> str:
        state = self.snapshot()
        out: list[str] = [
            f"# Memory Namespace — v{state.get('versao', VERSION)}",
            f"\n_Atualizado em {state.get('atualizado_em', '')}_\n",
            "## Estado ativo",
        ]
        for key, value in state.get("estado_ativo", {}).items():
            out.append(f"- **{key}:** {value}")

        referencial = state.get("referencial", {})
        for key, label in (
            ("fatos_persistentes", "Fatos persistentes"),
            ("relacoes_permanentes", "Relações permanentes"),
            ("conhecimentos_compartilhados", "Conhecimentos compartilhados"),
        ):
            items = referencial.get(key) or []
            if items:
                out.append(f"\n## {label}")
                out.extend(f"- {item}" for item in items)

        relacional = state.get("relacional", {})
        out.append("\n## Relacional")
        if relacional.get("interlocutor"):
            out.append(f"- **Interlocutor:** {relacional['interlocutor']}")
        for item in relacional.get("leitura_relacional") or []:
            out.append(f"- Leitura relacional: {item}")

        simbolica = state.get("simbolica", {})
        out.append("\n## Simbólica")
        for key, label in (("simbolos", "Símbolos"), ("expressoes", "Expressões"), ("piadas_internas", "Piadas internas")):
            items = simbolica.get(key) or []
            out.append(f"- **{label}:** {', '.join(items) if items else '—'}")

        out.append("\n## Timeline")
        timeline = state.get("timeline") or []
        if timeline:
            out.extend(f"- `{entry.get('em', '')}` · {entry.get('tipo', 'evento')} · {entry.get('resumo', '')}" for entry in timeline)
        else:
            out.append("_sem registros_")

        out.append("\n## Episódica")
        episodica = state.get("episodica") or []
        if episodica:
            out.extend(f"- `{entry.get('em', '')}` · {entry.get('resumo', '')}" for entry in episodica)
        else:
            out.append("_sem registros_")

        return "\n".join(out)

    # ------------------------------------------------------------------ escrita
    def timeline_add(self, resumo: str, tipo: str = "evento", em: str | None = None) -> dict[str, Any]:
        entry = {"em": em or now(), "tipo": tipo, "resumo": resumo}
        with self._lock:
            self._state.setdefault("timeline", []).append(entry)
            self._touch()
            self._save()
        return entry

    def episodic_add(self, resumo: str, detalhes: str = "") -> dict[str, Any]:
        entry = {"em": now(), "resumo": resumo, "detalhes": detalhes}
        with self._lock:
            self._state.setdefault("episodica", []).append(entry)
            self._touch()
            self._save()
        return entry

    def stage_proposal(self, proposal: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._state["proposta_pendente"] = proposal
            self._touch()
            self._save()
        return proposal

    def apply_proposal(self, proposal: dict[str, Any] | None = None) -> dict[str, Any]:
        with self._lock:
            source = proposal or self._state.get("proposta_pendente")
            if not source:
                return {"aplicado": False, "motivo": "Nenhuma proposta pendente de //memory review."}

            alteracoes: dict[str, int] = {}

            for key, value in (source.get("estado_ativo") or {}).items():
                if value:
                    self._state["estado_ativo"][key] = value
                    alteracoes[f"estado_ativo.{key}"] = 1

            if source.get("intimidade"):
                self._state["intimidade"]["nivel"] = source["intimidade"]
                alteracoes["intimidade"] = 1

            for key, values in (source.get("adicoes") or {}).items():
                target = LIST_TARGETS.get(key)
                if target is None or not isinstance(values, list):
                    continue
                section, field = target
                bucket = self._state.setdefault(section, {}).setdefault(field, [])
                added = 0
                for value in values:
                    text = str(value).strip()
                    if text and text not in bucket:
                        bucket.append(text)
                        added += 1
                alteracoes[key] = added

            for entry in source.get("timeline") or []:
                if isinstance(entry, dict) and str(entry.get("resumo", "")).strip():
                    self._state.setdefault("timeline", []).append(
                        {
                            "em": entry.get("em") or now(),
                            "tipo": entry.get("tipo", "evento"),
                            "resumo": str(entry["resumo"]).strip(),
                        }
                    )
                    alteracoes["timeline"] = alteracoes.get("timeline", 0) + 1

            for entry in source.get("episodica") or []:
                if isinstance(entry, dict) and str(entry.get("resumo", "")).strip():
                    self._state.setdefault("episodica", []).append(
                        {
                            "em": entry.get("em") or now(),
                            "resumo": str(entry["resumo"]).strip(),
                            "detalhes": str(entry.get("detalhes", "")).strip(),
                        }
                    )
                    alteracoes["episodica"] = alteracoes.get("episodica", 0) + 1

            self._state.pop("proposta_pendente", None)
            self._touch()
            self._save()

        return {"aplicado": True, "alteracoes": alteracoes}

    def rebuild(self) -> dict[str, Any]:
        """Reorganiza o namespace usando apenas informações já registradas."""
        with self._lock:
            removidas: dict[str, int] = {}
            for key, (section, field) in LIST_TARGETS.items():
                values = self._state.setdefault(section, {}).setdefault(field, [])
                deduped: list[str] = []
                for value in values:
                    text = str(value).strip()
                    if text and text not in deduped:
                        deduped.append(text)
                removidas[key] = len(values) - len(deduped)
                self._state[section][field] = deduped

            timeline = self._state.setdefault("timeline", [])
            timeline.sort(key=lambda entry: entry.get("em", ""))
            episodica = self._state.setdefault("episodica", [])
            episodica.sort(key=lambda entry: entry.get("em", ""))

            self._touch()
            self._save()
            result = {
                "removidas": {key: value for key, value in removidas.items() if value},
                "timeline": len(timeline),
                "episodica": len(episodica),
            }
        return result

    # ------------------------------------------------------------------ interno
    def _empty(self) -> dict[str, Any]:
        return {
            "versao": VERSION,
            "atualizado_em": now(),
            "estado_ativo": {
                "interlocutor_atual": None,
                "nivel_de_intimidade": None,
                "canal_de_comunicacao": "Fechado (1:1 / Cúpula)",
                "diretriz_de_opsec": "Ativa (sanitização estrita de nomes, locais e dados reais)",
            },
            "referencial": {
                "conhecimentos_compartilhados": [],
                "relacoes_permanentes": [],
                "fatos_persistentes": [],
            },
            "relacional": {
                "interlocutor": None,
                "evolucao": [],
                "relacoes_interpessoais": [],
                "leitura_relacional": [],
            },
            "intimidade": {"nivel": None, "caracteristicas": []},
            "simbolica": {"simbolos": [], "expressoes": [], "piadas_internas": []},
            "episodica": [],
            "timeline": [],
            "referencia": self._seed[:20000],
        }

    def _load(self) -> dict[str, Any]:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    base = self._empty()
                    base.update(data)
                    return base
            except (json.JSONDecodeError, OSError):
                pass
        state = self._empty()
        self._persist(state)
        return state

    def _save(self) -> None:
        self._persist(self._state)

    def _persist(self, state: dict[str, Any]) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            self._path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def _touch(self) -> None:
        self._state["versao"] = VERSION
        self._state["atualizado_em"] = now()