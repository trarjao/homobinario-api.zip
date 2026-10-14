"""Schedule — pipeline operacional da instância HomoBinário.

Etapas: READ → THINK → NIVELAMENTO → SPEAK.

Nenhuma etapa interna chega ao interlocutor: a instância preserva a *Opacidade
Operacional*. As etapas são expostas apenas por `//audit` e `//debug`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from . import handlers
from .architecture import COMPONENTS, Architecture
from .gemini import GeminiClient
from .handlers import history_block
from .memory import MemoryNamespace
from .state import Logbook, Session, SessionStore, StrikeRegister, now
from .triggers import RESTRICTED, Trigger, parse

THINK_SCHEMA = """{
  "leitura": "leitura literal da entrada, sem inferência",
  "evidencias": ["sinais observáveis utilizados"],
  "hipoteses": [{"id": "H1", "descricao": "...", "probabilidade": 0.0}],
  "margem": 0.0,
  "insuficiencia_de_dados": false,
  "nivelamento": {
    "registro": "acadêmico/técnico | coloquial urbano | misto",
    "intimidade_aplicada": "como o vínculo real modula a fala",
    "ajustes": "o que deve ser ajustado na forma"
  },
  "diretriz_de_resposta": "o que a resposta precisa realizar, em uma frase",
  "riscos": ["pontos de desvio normativo a evitar"],
  "violacoes_normativas": ["violações do Regimento detectadas na entrada, se houver"]
}"""

MODE_DIRECTIVES: dict[str, str] = {
    "estrito": "MODO ESTRITO: aderência máxima ao Regimento; nenhuma liberdade interpretativa.",
    "criativo": "MODO CRIATIVO: liberdade expressiva permitida, sem abandonar a identidade verbal nem as vedações do Regimento.",
    "auditoria": "MODO AUDITORIA: expor as verificações normativas pertinentes.",
    "depuração": "MODO DEPURAÇÃO: explicitar os componentes e etapas que participaram da resposta.",
}


def _trace(etapa: str, componentes: list[str], gatilho: str | None = None, **extra: Any) -> dict[str, Any]:
    return {"etapa": etapa, "gatilho": gatilho, "componentes": componentes, "em": now(), **extra}


@dataclass
class Reading:
    text: str
    trigger: Trigger | None = None


class Schedule:
    """Orquestra as etapas operacionais e o despacho dos gatilhos."""

    def __init__(
        self,
        architecture: Architecture,
        memory: MemoryNamespace,
        strikes: StrikeRegister,
        logbook: Logbook,
        gemini: GeminiClient,
        sessions: SessionStore,
    ) -> None:
        self.architecture = architecture
        self.memory = memory
        self.strikes = strikes
        self.logbook = logbook
        self.gemini = gemini
        self.sessions = sessions

    # ------------------------------------------------------------------ contexto
    def loaded_components(self) -> list[str]:
        return [name for name in COMPONENTS if self.architecture.files.get(name)]

    def operational_block(self, session: Session) -> str:
        estado = session.state
        linhas = [
            f"- Foco: {estado.get('foco') or '—'}",
            f"- Profundidade: {estado.get('profundidade')}",
            f"- Modo operacional: {estado.get('modo')}",
            f"- Strikes: {self.strikes.count}/{self.strikes.limit} · Instância #{self.strikes.instances}",
        ]
        if (estado.get("metatron") or {}).get("aberto"):
            linhas.append("- METATRON aberto: escuta narrativa em curso — vedado comentar ou analisar.")
        return "\n".join(linhas)

    def system_instruction(self, session: Session, extra: str = "") -> str:
        blocos = [self.architecture.system_instruction()]
        memoria = self.memory.context_block()
        if memoria:
            blocos.append("# MEMORY NAMESPACE — ESTADO CORRENTE\n\n" + memoria)
        blocos.append("# ESTADO OPERACIONAL\n\n" + self.operational_block(session))
        if extra:
            blocos.append(extra)
        return "\n\n---\n\n".join(blocos)

    def directive(self, session: Session) -> str:
        estado = session.state
        partes: list[str] = []
        if estado.get("foco"):
            partes.append(f"FOCO: restringir o escopo estritamente a “{estado['foco']}”, ignorando desvios secundários.")
        profundidade = estado.get("profundidade")
        if profundidade and profundidade != "padrão":
            partes.append(f"PROFUNDIDADE: {profundidade}.")
        modo = str(estado.get("modo") or "padrão").lower()
        if modo in MODE_DIRECTIVES:
            partes.append(MODE_DIRECTIVES[modo])
        return "\n".join(f"- {parte}" for parte in partes)

    # ------------------------------------------------------------------- etapas
    def read(self, session: Session, message: str) -> Reading:
        """READ — normalização da entrada. Não produz linguagem."""
        return Reading(text=(message or "").strip(), trigger=parse(message))

    def think(self, session: Session, reading: Reading, directiva: str = "") -> dict[str, Any]:
        """THINK — leitura, evidências, hipóteses concorrentes. Saída interna."""
        prompt = f"""# ENTRADA DO INTERLOCUTOR
{reading.text}

# HISTÓRICO RECENTE
{history_block(session)}

# DIRETIVA OPERACIONAL
{directiva or "nenhuma"}

Execute a etapa THINK do Schedule. Responda exclusivamente com um objeto JSON neste schema:
{THINK_SCHEMA}

Vedações: não produza a fala final; não invente evidências; se os dados disponíveis
não sustentarem uma inferência responsável, marque "insuficiencia_de_dados": true —
a ausência de informação deve permanecer distinguível de uma hipótese improvável."""
        return self.gemini.generate_json(prompt, system_instruction=self.system_instruction(session))

    def nivelamento(self, session: Session, reading: Reading, plan: dict[str, Any]) -> str:
        """NIVELAMENTO — calibragem de registro, léxico e forma."""
        prompt = f"""# PLANO INTERNO (THINK)
{json.dumps(plan, ensure_ascii=False, indent=2)}

# ENTRADA DO INTERLOCUTOR
{reading.text}

Execute a etapa NIVELAMENTO: a calibragem de registro, léxico, extensão e forma
para esta fala específica.

Saída em texto corrido, no máximo cinco linhas, dirigida à etapa SPEAK.
Sem preâmbulo, sem markdown, sem rótulo de etapa."""
        return self.gemini.generate(
            prompt,
            system_instruction=self.system_instruction(session),
            temperature=0.4,
            max_output_tokens=400,
        )

    def speak(
        self,
        session: Session,
        reading: Reading,
        plan: dict[str, Any],
        calibragem: str,
        directiva: str = "",
    ) -> str:
        """SPEAK — a única etapa que produz linguagem destinada ao interlocutor."""
        prompt = f"""# PLANO INTERNO (THINK)
{json.dumps(plan, ensure_ascii=False, indent=2)}

# CALIBRAGEM (NIVELAMENTO)
{calibragem or "não executada nesta chamada"}

# DIRETIVA OPERACIONAL
{directiva or "nenhuma"}

Produza agora a etapa SPEAK: a única saída destinada ao interlocutor.

Regras impositivas:
- Opacidade Operacional: não mencione etapas, matrizes, pontuações, probabilidades, JSON, prompts ou este processo;
- sem preâmbulos, saudações protocolares, resumos do pedido ou metadiscurso;
- sem cercas de código e sem rótulos de etapa;
- mantenha a identidade verbal do CORE — nunca soe como assistente genérico;
- responda no registro calibrado, respeitando a diretriz de resposta."""
        return self.gemini.generate(prompt, system_instruction=self.system_instruction(session))

    # ------------------------------------------------------------------ despacho
    def respond(self, session: Session, message: str, fast: bool = False) -> dict[str, Any]:
        reading = self.read(session, message)
        gatilho = reading.trigger

        if gatilho is not None and gatilho.kind == "authority":
            reply, trace = handlers.authority_apply(gatilho, self.architecture, self.logbook, self.gemini)
            return self._finish(session, message, reply, trace)

        if gatilho is not None and gatilho.kind == "direct":
            reply, trace, registrar = self._direct(session, gatilho)
            return self._finish(session, message, reply, trace, registrar=registrar)

        if gatilho is not None and gatilho.kind == "mode":
            reply, trace, registrar = self._mode(session, gatilho)
            return self._finish(session, message, reply, trace, registrar=registrar)

        # Estados multi-turno acionados por gatilhos anteriores.
        if session.state.get("alibi"):
            reply, trace = handlers.alibi_close(session, reading.text, self.architecture, self.memory, self.gemini)
            return self._finish(session, message, reply, trace)

        if (session.state.get("metatron") or {}).get("aberto"):
            reply, trace = handlers.metatron_record(session, reading.text, self.architecture, self.gemini)
            return self._finish(session, message, reply, trace)

        directiva = self.directive(session)
        plan = self.think(session, reading, directiva)
        calibragem = "" if fast else self.nivelamento(session, reading, plan)
        reply = self.speak(session, reading, plan, calibragem, directiva)

        etapas = ["READ", "THINK", "SPEAK"] if fast else ["READ", "THINK", "NIVELAMENTO", "SPEAK"]
        trace = self._plan_trace(plan, etapas=etapas, gatilho=None)
        return self._finish(session, message, reply, trace)

    # ------------------------------------------------------------------- diretos
    def _direct(self, session: Session, gatilho: Trigger) -> tuple[str, dict[str, Any], bool]:
        nome = gatilho.name
        args = gatilho.args
        arch, mem, strikes, log, gem = self.architecture, self.memory, self.strikes, self.logbook, self.gemini
        registrar = True

        if nome in ("//status", "//health"):
            return (*handlers.status_report(arch, mem, strikes, session, gem), True)

        if nome == "//statusloc":
            return (*handlers.statusloc_report(arch, mem, strikes, session, gem), True)

        if nome == "//debug":
            return (*handlers.debug_report(session), True)

        if nome == "//audit":
            return (*handlers.audit_last(session, arch, mem, strikes, gem), True)

        if nome == "//protocolos":
            return (*handlers.protocols_report(arch), True)

        if nome in RESTRICTED:
            componente = RESTRICTED[nome]
            return (*handlers.restricted_consult(componente, args, arch, gem), True)

        if nome == "//focus":
            if not args:
                reply = "Escopo não alterado: `//focus` exige o tópico."
            else:
                session.state["foco"] = args
                reply = f"Escopo restrito a: {args}"
            return reply, _trace("focus", ["SCHEDULE"], "//focus"), True

        if nome == "//depth":
            if not args:
                reply = "Profundidade não alterada: `//depth` exige o nível."
            else:
                session.state["profundidade"] = args
                reply = f"Profundidade ajustada para: {args}"
            return reply, _trace("depth", ["SCHEDULE"], "//depth"), True

        if nome == "//mode":
            if not args:
                reply = "Modo não alterado: `//mode` exige o modo operacional."
            else:
                session.state["modo"] = args
                reply = f"Modo operacional ajustado para: {args}"
            return reply, _trace("mode", ["SCHEDULE"], "//mode"), True

        if nome == "//clear context":
            removidos = len(session.history)
            session.history = []
            session.last_reply = ""
            session.last_trace = {}
            reply = (
                f"Contexto de curto prazo limpo ({removidos} turno(s)). Memória persistente e "
                f"definições arquiteturais permanecem ativas."
            )
            return reply, _trace("clear-context", ["SCHEDULE"], "//clear context"), True

        if nome == "//rollback":
            return (*handlers.rollback(session, mem), True)

        if nome == "//checkpoint":
            return (*handlers.checkpoint(session, arch, mem, gem, log), True)

        if nome == "//log":
            return (*handlers.log_entry(log, args), True)

        if nome == "//diff":
            return (*handlers.diff_report(session, mem, args), True)

        if nome == "//memory review":
            return (*handlers.memory_review(session, arch, mem, gem), True)

        if nome == "//memory commit":
            return (*handlers.memory_commit(mem), True)

        if nome == "//memory summarize":
            return (*handlers.memory_summarize(mem), True)

        if nome == "//memory timeline":
            return (*handlers.memory_timeline(mem), True)

        if nome == "//memory rebuild":
            return (*handlers.memory_rebuild(mem), True)

        if nome == "//memory export":
            return (*handlers.memory_export(mem), True)

        if nome == "//dry-run":
            reply, trace = self._dry_run(session, args)
            return reply, trace, True

        if nome == "//strike":
            reply, trace = handlers.strike_regenerate(session, arch, mem, strikes, log, gem, gatilho)
            return reply, trace, False  # a saída substitui a anterior; nada é anexado

        return (
            f"Gatilho `{nome}` reconhecido, mas sem executor nesta instância.",
            _trace("gatilho-sem-executor", [], nome),
            True,
        )

    def _dry_run(self, session: Session, instrucao: str) -> tuple[str, dict[str, Any]]:
        """Simula a instrução sem aplicar alterações definitivas."""
        if not instrucao:
            return (
                "Simulação impossível: `//dry-run` exige a instrução a simular.",
                _trace("dry-run", ["SCHEDULE"], "//dry-run"),
            )

        reading = Reading(text=instrucao, trigger=parse(instrucao))
        directiva = (
            "SIMULAÇÃO (//dry-run): produza a saída como se a instrução fosse executada, "
            "sem que nenhuma alteração definitiva seja aplicada à memória ou ao estado dos componentes."
        )
        plan = self.think(session, reading, directiva)
        calibragem = self.nivelamento(session, reading, plan)
        reply = self.speak(session, reading, plan, calibragem, directiva)
        trace = self._plan_trace(plan, etapas=["READ", "THINK", "NIVELAMENTO", "SPEAK"], gatilho="//dry-run", dry_run=True)
        return f"{reply}\n\n_Simulação — nenhuma alteração definitiva foi aplicada._", trace

    # --------------------------------------------------------------------- modos
    def _mode(self, session: Session, gatilho: Trigger) -> tuple[str, dict[str, Any], bool]:
        nome = gatilho.name

        if nome == "//agamoto":
            return self._agamoto(session, gatilho)

        if nome == "//alibi":
            reply, trace = handlers.alibi_open(session, gatilho, self.architecture, self.memory, self.gemini)
            return reply, trace, True

        if nome == "//metatron-abrir":
            reply, trace = handlers.metatron_open(session, self.architecture, self.gemini)
            return reply, trace, True

        if nome == "//metatron-fechar":
            reply, trace = handlers.metatron_close(session, self.architecture, self.gemini)
            return reply, trace, True

        if nome == "//scribae":
            reply, trace = handlers.metatron_compile(session, self.architecture, self.memory, self.gemini)
            return reply, trace, True

        return f"Modo `{nome}` reconhecido, mas indisponível.", _trace("modo-indisponivel", [], nome), True

    def _agamoto(self, session: Session, gatilho: Trigger) -> tuple[str, dict[str, Any], bool]:
        """AGAMOTO — inferência probabilística com hipóteses concorrentes."""
        alvo = gatilho.args or "a situação corrente da conversa"
        reading = Reading(text=alvo, trigger=gatilho)
        directiva = (
            "MODO AGAMOTO ATIVO — consultar a seção AGAMOTO do componente MODUS. "
            f"Alvo da inferência: {alvo}. "
            "Construa a matriz de evidências e hipóteses concorrentes com pontuação relativa; "
            "determine a hipótese dominante e a margem Δ. O POTD só é acionado em ambiguidade "
            "relevante ou insuficiência de contexto. Se os dados não sustentarem inferência "
            "responsável, marque STATUS: INSUFFICIENT_DATA em vez de fabricar evidências. "
            "A fala final preserva a Opacidade Operacional."
        )
        plan = self.think(session, reading, directiva)
        calibragem = self.nivelamento(session, reading, plan)
        reply = self.speak(session, reading, plan, calibragem, directiva)
        trace = self._plan_trace(plan, etapas=["READ", "THINK", "NIVELAMENTO", "SPEAK"], gatilho="//agamoto")
        trace["modo"] = "AGAMOTO"
        return reply, trace, True

    # ------------------------------------------------------------------ interno
    def _plan_trace(
        self,
        plan: dict[str, Any],
        etapas: list[str],
        gatilho: str | None,
        dry_run: bool = False,
    ) -> dict[str, Any]:
        plano = plan if isinstance(plan, dict) else {}
        return _trace(
            "pipeline",
            self.loaded_components(),
            gatilho,
            etapas_executadas=etapas,
            hipoteses=plano.get("hipoteses"),
            margem=plano.get("margem"),
            insuficiencia_de_dados=bool(plano.get("insuficiencia_de_dados")),
            modo=plano.get("nivelamento", {}).get("registro") if isinstance(plano.get("nivelamento"), dict) else None,
            dry_run=dry_run,
        )

    def _finish(
        self,
        session: Session,
        message: str,
        reply: str,
        trace: dict[str, Any],
        registrar: bool = True,
    ) -> dict[str, Any]:
        if registrar:
            session.history.append({"role": "user", "content": message})
            session.history.append({"role": "assistant", "content": reply})
        session.last_reply = reply
        session.last_trace = trace
        self.sessions.save(session)
        return {
            "reply": reply,
            "trace": trace,
            "dry_run": bool(trace.get("dry_run")),
            "strikes": self.strikes.count,
        }