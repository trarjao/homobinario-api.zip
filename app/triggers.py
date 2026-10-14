"""Gatilhos — pontos de entrada explícitos da arquitetura (Gatilhos §2–§12).

Interpretação literal (Gatilhos §12.1): o parser não infere intenção. Ele
reconhece o gatilho, seus argumentos e suas flags, e devolve o comando à camada
responsável pela execução.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

AUTHORITY = "//as your maker"

DIRECT: dict[str, str] = {
    "//strike": "Sanção normativa e regeneração estrita do último output.",
    "//audit": "Auditoria normativa preventiva, sem sanção.",
    "//rollback": "Restaura o último ponto de checagem seguro.",
    "//focus": "Restringe o escopo ao tópico informado.",
    "//clear context": "Limpa o contexto de curto prazo.",
    "//depth": "Ajusta a profundidade analítica.",
    "//core": "Consulta exclusivamente o Core.",
    "//regimento": "Consulta exclusivamente o Regimento.",
    "//schedule": "Consulta exclusivamente o Schedule.",
    "//protocolos": "Lista os protocolos disponíveis.",
    "//dry-run": "Simula a instrução sem alterar memória ou estado.",
    "//mode": "Altera o modo operacional de processamento.",
    "//memory review": "Revisa a conversa e propõe atualização do Memory Namespace.",
    "//memory commit": "Aplica a proposta produzida pelo Memory Review.",
    "//memory summarize": "Síntese integral do estado da memória.",
    "//memory timeline": "Apresenta a Timeline registrada.",
    "//memory rebuild": "Reconstrói a organização do Memory Namespace.",
    "//memory export": "Exporta o estado de memória para persistência externa.",
    "//status": "Relatório sintético do estado operacional.",
    "//health": "Relatório sintético do estado operacional.",
    "//statusloc": "Inspeção operacional completa da instância.",
    "//debug": "Explica os componentes que geraram a última resposta.",
    "//checkpoint": "Resumo técnico da sessão para versionamento.",
    "//log": "Registra decisão arquitetural relevante.",
    "//diff": "Compara duas versões da arquitetura ou do Memory Namespace.",
}

MODES: dict[str, str] = {
    "//agamoto": "AGAMOTO — inferência comportamental probabilística.",
    "//alibi": "ÁLIBI — interrupção e justificativa social.",
    "//metatron-abrir": "METATRON — inicia a escuta narrativa.",
    "//metatron-fechar": "METATRON — encerra a escuta e libera o comentário.",
    "//scribae": "METATRON — consolidação definitiva do bloco narrado.",
}

NATURAL: dict[str, str] = {
    "senta que lá vem história": "//metatron-abrir",
    "to be continued...": "//metatron-fechar",
}

ALIBI_FLAGS = ("--urgent", "--work", "--personal")

DEPTHS = ("síntese", "padrão", "exaustivo")
OPERATIONAL_MODES = ("padrão", "estrito", "criativo", "auditoria", "depuração")

# Consulta restrita: gatilho → componente.
RESTRICTED: dict[str, str] = {
    "//core": "CORE",
    "//regimento": "REGIMENTO",
    "//schedule": "SCHEDULE",
}


@dataclass
class Trigger:
    name: str
    raw: str
    args: str = ""
    flags: list[str] = field(default_factory=list)
    kind: str = "direct"  # direct | mode | authority

    @property
    def is_direct(self) -> bool:
        return self.kind == "direct"

    def to_json(self) -> dict[str, Any]:
        return {"nome": self.name, "argumentos": self.args, "flags": self.flags, "tipo": self.kind}


_TABLE: list[tuple[str, str, str]] = sorted(
    [(key, key, "direct") for key in DIRECT] + [(key, key, "mode") for key in MODES],
    key=lambda item: len(item[0]),
    reverse=True,
)


def parse(message: str) -> Trigger | None:
    """Reconhece um gatilho no início da mensagem. Sem inferência de intenção."""
    text = (message or "").strip()
    if not text:
        return None

    lowered = text.lower()

    if lowered.startswith(AUTHORITY):
        return Trigger(name=AUTHORITY, raw=text, args=text[len(AUTHORITY) :].strip(), kind="authority")

    for natural, canonical in NATURAL.items():
        if lowered.startswith(natural):
            return Trigger(
                name=canonical,
                raw=text,
                args=text[len(natural) :].strip(),
                kind="mode",
            )

    for key, name, kind in _TABLE:
        if not lowered.startswith(key):
            continue
        remainder = text[len(key) :]
        if remainder and not remainder[0].isspace():
            continue  # evita casar //corex, //statusloc como //status, etc.
        args = remainder.strip()
        flags = [flag for flag in ALIBI_FLAGS if flag in args.split()] if kind == "mode" else []
        return Trigger(name=name, raw=text, args=args, flags=flags, kind=kind)

    return None


def catalogue() -> dict[str, dict[str, str]]:
    return {"diretos": DIRECT, "modos": MODES, "autoridade": {AUTHORITY: "Precedência absoluta."}}