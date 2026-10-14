"""API HTTP da instância HomoBinário · KDPROJECT.

Expõe a arquitetura conversacional com a persona Kael Duarte sobre o Gemini.

Execução:
    uvicorn main:app --reload --port 8000
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from app import __version__
from app.architecture import COMPONENTS, load_architecture
from app.config import settings
from app.gemini import GeminiClient, GeminiError
from app.memory import MemoryNamespace
from app.schedule import Schedule
from app.state import Logbook, SessionStore, StrikeRegister
from app.triggers import catalogue

STATE: dict[str, Any] = {}


@asynccontextmanager
async def lifespan(_: FastAPI):
    """Bootstrap da instância: documentos, memória, strikes, log e sessões."""
    settings.ensure()

    architecture = load_architecture()
    memory = MemoryNamespace(seed_text=architecture.memory_seed())
    strikes = StrikeRegister()
    logbook = Logbook()
    sessions = SessionStore()
    gemini = GeminiClient()
    schedule = Schedule(architecture, memory, strikes, logbook, gemini, sessions)

    STATE.update(
        {
            "architecture": architecture,
            "memory": memory,
            "strikes": strikes,
            "logbook": logbook,
            "sessions": sessions,
            "gemini": gemini,
            "schedule": schedule,
        }
    )
    logbook.append(
        "bootstrap",
        f"Instância #{strikes.instances} inicializada",
        {"pronta": architecture.ready, "ausentes": architecture.missing},
    )
    yield
    STATE.clear()


app = FastAPI(
    title="HomoBinário · KDPROJECT",
    version=__version__,
    description=(
        "Instância conversacional da arquitetura HomoBinário com a persona Kael Duarte. "
        "Pipeline Schedule: READ → THINK → NIVELAMENTO → SPEAK."
    ),
    lifespan=lifespan,
)


# ------------------------------------------------------------------------- guardas
def require_token(authorization: str | None = Header(default=None)) -> None:
    """Se HOMOBINARIO_API_TOKEN estiver definido, exige Authorization: Bearer."""
    if not settings.api_token:
        return
    if authorization != f"Bearer {settings.api_token}":
        raise HTTPException(status_code=401, detail="Credencial inválida.")


def require_ready() -> None:
    architecture = STATE.get("architecture")
    if architecture is None or architecture.ready:
        return
    raise HTTPException(
        status_code=503,
        detail={
            "erro": "Arquitetura incompleta: a instância não opera sem os componentes críticos.",
            "ausentes_criticos": architecture.missing_critical,
            "ausentes": architecture.missing,
            "instrucao": "Reenvie as fontes oficiais para o diretório docs/ e reinicie o serviço.",
        },
    )


# -------------------------------------------------------------------------- modelos
class ChatRequest(BaseModel):
    message: str = Field(min_length=1, description="Mensagem do interlocutor.")
    session_id: str | None = Field(default=None, description="Sessão existente; ausente cria uma nova.")
    fast: bool = Field(default=False, description="Suprime a etapa NIVELAMENTO.")


class ChatResponse(BaseModel):
    session_id: str
    reply: str
    gatilho: str | None = None
    etapa: str | None = None
    strikes: int = 0
    simulacao: bool = False


# ------------------------------------------------------------------------ endpoints
@app.get("/", dependencies=[Depends(require_token)])
def index() -> dict[str, Any]:
    return {
        "instancia": "HomoBinário · KDPROJECT",
        "versao": __version__,
        "persona": "Kael Duarte",
        "modelo": settings.gemini_model,
        "endpoints": [
            "GET /health",
            "GET /architecture",
            "GET /architecture/{componente}",
            "POST /chat",
            "GET /session/{id}",
            "DELETE /session/{id}",
            "GET /memory",
            "GET /memory/timeline",
            "POST /memory/commit",
            "GET /memory/export",
            "GET /log",
        ],
        "gatilhos": catalogue(),
    }


@app.get("/health", dependencies=[Depends(require_token)])
def health() -> dict[str, Any]:
    architecture = STATE["architecture"]
    strikes: StrikeRegister = STATE["strikes"]
    return {
        "pronta": architecture.ready,
        "modelo": settings.gemini_model,
        "chave_configurada": STATE["gemini"].available,
        "componentes": [name for name in COMPONENTS if architecture.files.get(name)],
        "componentes_ausentes": architecture.missing,
        "componentes_criticos_ausentes": architecture.missing_critical,
        "strikes": strikes.report(),
    }


@app.get("/architecture", dependencies=[Depends(require_token)])
def architecture_manifest() -> dict[str, Any]:
    return STATE["architecture"].manifest()


@app.get("/architecture/{componente}", dependencies=[Depends(require_token)])
def architecture_component(componente: str) -> dict[str, Any]:
    nome = componente.upper()
    texto = STATE["architecture"].component(nome)
    if nome not in COMPONENTS or not texto:
        raise HTTPException(status_code=404, detail=f"Componente {nome} indisponível.")
    return {"componente": nome, "conteudo": texto}


@app.post("/chat", response_model=ChatResponse, dependencies=[Depends(require_token)])
def chat(payload: ChatRequest) -> ChatResponse:
    require_ready()
    schedule: Schedule = STATE["schedule"]
    sessions: SessionStore = STATE["sessions"]
    strikes: StrikeRegister = STATE["strikes"]

    session = sessions.get(payload.session_id)
    try:
        resultado = schedule.respond(session, payload.message, fast=payload.fast)
    except GeminiError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    sessions.save(session)
    trace = resultado.get("trace") or {}
    return ChatResponse(
        session_id=session.id,
        reply=resultado["reply"],
        gatilho=trace.get("gatilho"),
        etapa=trace.get("etapa"),
        strikes=strikes.count,
        simulacao=bool(resultado.get("dry_run")),
    )


@app.get("/session/{session_id}", dependencies=[Depends(require_token)])
def session_state(session_id: str) -> dict[str, Any]:
    session = STATE["sessions"].get(session_id)
    return {
        "id": session.id,
        "criada_em": session.created_at,
        "estado": session.state,
        "turnos": len(session.history),
        "ultimo_traco": session.last_trace,
        "checkpoint": bool(session.checkpoint),
    }


@app.delete("/session/{session_id}", dependencies=[Depends(require_token)])
def session_delete(session_id: str) -> dict[str, Any]:
    removida = STATE["sessions"].delete(session_id)
    return {"encerrada": removida, "session_id": session_id}


@app.get("/memory", dependencies=[Depends(require_token)])
def memory_snapshot() -> dict[str, Any]:
    return STATE["memory"].snapshot()


@app.get("/memory/timeline", dependencies=[Depends(require_token)])
def memory_timeline() -> dict[str, Any]:
    registros = STATE["memory"].timeline()
    return {"total": len(registros), "registros": registros}


@app.post("/memory/commit", dependencies=[Depends(require_token)])
def memory_commit() -> dict[str, Any]:
    return STATE["memory"].apply_proposal()


@app.get("/memory/export", dependencies=[Depends(require_token)])
def memory_export() -> dict[str, Any]:
    from app import handlers  # import local: mantém o topo limpo

    _, trace = handlers.memory_export(STATE["memory"])
    return {"arquivo": trace.get("arquivo"), "memoria": STATE["memory"].snapshot()}


@app.get("/log", dependencies=[Depends(require_token)])
def log_entries(limit: int = 50) -> dict[str, Any]:
    entries = STATE["logbook"].read(limit=limit)
    return {"total": len(entries), "entradas": entries}