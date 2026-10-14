"""Carregamento dos componentes oficiais da arquitetura HomoBinário.

O loader não interpreta o conteúdo dos documentos: apenas os organiza na ordem
canônica e os apresenta às etapas do Schedule.

Regra de integridade (Gatilhos §3): sem os documentos oficiais a instância não
deve operar. `Architecture.ready` permanece falso enquanto faltar um componente
crítico — é vedado reconstruir a arquitetura por aproximação probabilística.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .config import settings

# Ordem canônica da instrução de sistema.
COMPONENTS = ("CORE", "REGIMENTO", "SCHEDULE", "MODUS", "PROTOCOLOS", "GATILHOS")

# Componentes sem os quais a instância não opera.
CRITICAL = ("CORE", "REGIMENTO", "SCHEDULE", "GATILHOS")

# Marcadores de reconhecimento por nome de arquivo (minúsculas, sem acentos).
MATCHERS: dict[str, tuple[str, ...]] = {
    "CORE": ("core", "kael"),
    "REGIMENTO": ("regimento",),
    "SCHEDULE": ("schedule", "cronograma"),
    "MODUS": ("modus",),
    "PROTOCOLOS": ("protocolo",),
    "GATILHOS": ("gatilho",),
    "MEMORY": ("memory", "memoria"),
}

SUFFIXES = {".md", ".markdown", ".txt"}


def slug(text: str) -> str:
    """Minúsculas e sem acentos — usado apenas para reconhecer arquivos."""
    normalized = unicodedata.normalize("NFKD", text.lower())
    return "".join(char for char in normalized if not unicodedata.combining(char))


def classify(filename: str) -> str | None:
    """Componente correspondente ao nome do arquivo, ou None."""
    name = slug(filename)
    best: tuple[int, str] | None = None
    for component, markers in MATCHERS.items():
        for marker in markers:
            index = name.find(marker)
            if index == -1:
                continue
            if best is None or index < best[0]:
                best = (index, component)
    return best[1] if best else None


def protocol_index(text: str) -> list[str]:
    """Extrai os nomes de protocolo a partir dos títulos do componente PROTOCOLOS."""
    names: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("#"):
            continue
        title = stripped.lstrip("#").strip(" :-*")
        if not title or slug(title).startswith("protocolo"):
            continue
        names.append(title)

    seen: set[str] = set()
    unique: list[str] = []
    for name in names:
        key = slug(name)
        if key in seen:
            continue
        seen.add(key)
        unique.append(name)
    return unique


@dataclass
class Architecture:
    files: dict[str, str] = field(default_factory=dict)
    sources: dict[str, str] = field(default_factory=dict)
    unclassified: dict[str, str] = field(default_factory=dict)

    @property
    def missing(self) -> list[str]:
        return [name for name in COMPONENTS if not self.files.get(name)]

    @property
    def missing_critical(self) -> list[str]:
        return [name for name in CRITICAL if not self.files.get(name)]

    @property
    def ready(self) -> bool:
        return not self.missing_critical

    def component(self, name: str) -> str:
        return self.files.get(name.upper(), "")

    def memory_seed(self) -> str:
        return self.files.get("MEMORY", "")

    def protocols(self) -> list[str]:
        return protocol_index(self.component("PROTOCOLOS"))

    def manifest(self) -> dict[str, Any]:
        return {
            "componentes": {
                name: {
                    "arquivo": self.sources.get(name),
                    "caracteres": len(self.files.get(name, "")),
                }
                for name in COMPONENTS
            },
            "memory_namespace": self.sources.get("MEMORY"),
            "anexos": sorted(self.unclassified),
            "ausentes": self.missing,
            "ausentes_criticos": self.missing_critical,
            "pronta": self.ready,
        }

    def system_instruction(self) -> str:
        """Instrução de sistema com os componentes na ordem canônica."""
        blocks: list[str] = []
        for name in COMPONENTS:
            content = self.files.get(name, "").strip()
            if content:
                blocks.append(f"# COMPONENTE OFICIAL: {name}\n\n{content}")
        for filename, content in self.unclassified.items():
            blocks.append(f"# ANEXO NÃO CLASSIFICADO: {filename}\n\n{content.strip()}")
        return "\n\n---\n\n".join(blocks)


def load_architecture(docs_dir: Path | None = None) -> Architecture:
    directory = Path(docs_dir or settings.docs_dir)
    architecture = Architecture()
    if not directory.exists():
        return architecture

    documents = sorted(
        (path for path in directory.rglob("*") if path.is_file() and path.suffix.lower() in SUFFIXES),
        key=lambda path: path.name.lower(),
    )

    for path in documents:
        content = path.read_text(encoding="utf-8", errors="replace")
        if not content.strip():
            continue
        component = classify(path.name)
        if component is None:
            architecture.unclassified[path.name] = content
            continue
        architecture.files[component] = content
        architecture.sources[component] = str(path.relative_to(directory))

    return architecture