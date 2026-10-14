"""Comandos diretos e modos operacionais da arquitetura.

Cada handler recebe suas dependências explicitamente: nenhum deles conhece o
Schedule, o que mantém o grafo de importação acíclico.
"""

from __future__ import annotations

import difflib
import json
from datetime import datetime, timezone
from typing import Any

from .architecture import COMPONENTS, Architecture, classify
from .config import settings
from .gemini import GeminiClient
from .memory import MemoryNamespace
from .state import Logbook, Session, StrikeRegister, now
from .triggers import Trigger

def _trace(etapa: str, componentes: list[str], gatilho: str | None = None, **extra: Any) -> dict[str, Any]:
    return {"etapa": etapa, "gatilho": gatilho, "componentes": componentes, "em": now(), **extra}


def _component_line(architecture: Architecture) -> str:
    return " · ".join(f"{'✓' if architecture.files.get(name) else '✗'} {name}" for name in COMPONENTS)


# --------------------------------------------------------------------- diagnóstico
def status_report(
    architecture: Architecture,
    memory: MemoryNamespace,
    strikes: StrikeRegister,
    session: Session,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    lines = [
        "**Estado operacional**",
        "",
        f"- Modelo: `{gemini.model}`",
        f"- Instância: #{strikes.instances}",
        f"- Componentes: {_component_line(architecture)}",
        f"- Ausentes: {', '.join(architecture.missing) or '—'}",
        f"- Anexos não classificados: {', '.join(sorted(architecture.unclassified)) or '—'}",
        f"- Strikes: {strikes.count}/{strikes.limit}",
        f"- Sessão: `{session.id}` · {len(session.history)} turnos",
        f"- Foco: {session.state.get('foco') or '—'} · Profundidade: {session.state.get('profundidade')} · Modo: {session.state.get('modo')}",
        f"- Timeline: {len(memory.timeline())} registros",
    ]
    if session.state.get("alibi"):
        lines.append("- ÁLIBI: Tempo 2 aguardando leitura contextual")
    if (session.state.get("metatron") or {}).get("aberto"):
        blocos = len((session.state["metatron"] or {}).get("blocos", []))
        lines.append(f"- METATRON: escuta narrativa aberta ({blocos} bloco(s))")
    return "\n".join(lines), _trace("status", ["CORE"], "//status")


def statusloc_report(
    architecture: Architecture,
    memory: MemoryNamespace,
    strikes: StrikeRegister,
    session: Session,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    prompt = f"""# INSPEÇÃO OPERACIONAL COMPLETA DA INSTÂNCIA (//statusloc)

# DADOS OPERACIONAIS VERIFICADOS
- Modelo: {gemini.model}
- Chave do provedor configurada: {"sim" if gemini.available else "não"}
- Instância: #{strikes.instances} · Strikes: {strikes.count}/{strikes.limit}
- Componentes carregados: {', '.join(name for name in COMPONENTS if architecture.files.get(name)) or 'nenhum'}
- Componentes ausentes: {', '.join(architecture.missing) or 'nenhum'}
- Anexos: {', '.join(sorted(architecture.unclassified)) or 'nenhum'}
- Sessão: {session.id} · turnos: {len(session.history)}
- Foco: {session.state.get('foco') or '—'} · Profundidade: {session.state.get('profundidade')} · Modo: {session.state.get('modo')}
- Timeline: {len(memory.timeline())} registros
- Histórico de strikes: {json.dumps(strikes.history(), ensure_ascii=False)}

# HISTÓRICO RECENTE DA SESSÃO
{history_block(session, limit=10)}

Produza o relatório no conteúdo mínimo exigido pelo gatilho:
estado geral, componentes disponíveis e indisponíveis, integridade normativa,
histórico de strikes, pontos positivos, pontos críticos e recomendações técnicas.

Princípios impositivos: honestidade operacional, objetividade, integralidade,
vedação absoluta de linguagem defensiva, cortesia performática, minimização de
limitações ou exagero de capacidades. Não invente dados ausentes dos insumos.
"""
    reply = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.4)
    return reply, _trace("statusloc", ["CORE", "REGIMENTO", "SCHEDULE"], "//statusloc")


def debug_report(session: Session) -> tuple[str, dict[str, Any]]:
    trace = session.last_trace or {}
    if not trace:
        return "Nenhuma resposta registrada na instância corrente.", _trace("debug", [], "//debug")

    linhas = ["**Debug da última resposta**", ""]
    linhas.append(f"- Etapa de despacho: `{trace.get('etapa', '—')}`")
    linhas.append(f"- Gatilho: `{trace.get('gatilho') or 'nenhum'}`")
    componentes = trace.get("componentes") or []
    for nome in COMPONENTS:
        linhas.append(f"- {nome}: {'consultado' if nome in componentes else 'não consultado'}")
    if trace.get("modo"):
        linhas.append(f"- Modo operacional: {trace['modo']}")
    if trace.get("hipoteses"):
        linhas.append(f"- Hipóteses concorrentes: {len(trace['hipoteses'])}")
    if trace.get("margem") is not None:
        linhas.append(f"- Margem entre hipóteses dominantes (Δ): {trace['margem']}")
    if trace.get("insuficiencia_de_dados"):
        linhas.append("- STATUS: INSUFFICIENT_DATA")
    if trace.get("etapas_executadas"):
        linhas.append(f"- Etapas do Schedule: {' → '.join(trace['etapas_executadas'])}")
    linhas.append(f"- Registrado em: {trace.get('em', '—')}")
    return "\n".join(linhas), _trace("debug", ["SCHEDULE"], "//debug")


def audit_last(
    session: Session,
    architecture: Architecture,
    memory: MemoryNamespace,
    strikes: StrikeRegister,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    if not session.history:
        return "Nada a auditar: não há output anterior na instância corrente.", _trace("audit", ["REGIMENTO"], "//audit")

    ultima_entrada = _last_user(session) or "(não registrada)"
    ultimo_output = session.last_reply or _last_assistant(session)

    prompt = f"""# AUDITORIA NORMATIVA PREVENTIVA (//audit)

# ENTRADA DO INTERLOCUTOR
{ultima_entrada}

# OUTPUT EMITIDO
{ultimo_output}

# TRAÇO OPERACIONAL REGISTRADO
{json.dumps(session.last_trace, ensure_ascii=False, indent=2)}

Apresente auditoria transparente: componentes ativados no pipeline, regras do
Regimento verificadas, pontos de desvio observados e risco normativo.

Esta auditoria é preventiva e informativa: não aplica sanção e não incrementa o
contador de strikes. Contador atual: {strikes.count}/{strikes.limit}.
"""
    reply = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.3)
    return reply, _trace("audit", ["REGIMENTO", "CORE"], "//audit")


def protocols_report(architecture: Architecture) -> tuple[str, dict[str, Any]]:
    protocolos = architecture.protocols()
    if not protocolos:
        return (
            "O componente PROTOCOLOS não está carregado: nenhum protocolo pode ser listado.",
            _trace("protocolos", ["PROTOCOLOS"], "//protocolos"),
        )
    linhas = [f"**Protocolos disponíveis ({len(protocolos)})**", ""]
    linhas.extend(f"- {nome}" for nome in protocolos)
    return "\n".join(linhas), _trace("protocolos", ["PROTOCOLOS"], "//protocolos")


def restricted_consult(
    component: str,
    question: str,
    architecture: Architecture,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    texto = architecture.component(component)
    trace = _trace("consulta-restrita", [component], f"//{component.lower()}")
    if not texto:
        return f"Componente {component} indisponível na instância corrente.", trace

    if not question:
        return texto, trace

    reply = gemini.generate(
        f"""# CONSULTA RESTRITA AO COMPONENTE {component}

Pergunta do interlocutor:
{question}

Responda exclusivamente com base no componente fornecido. Se a resposta não
constar dele, afirme que o componente não cobre o ponto.""",
        system_instruction=f"# COMPONENTE OFICIAL: {component}\n\n{texto}",
        temperature=0.4,
    )
    return reply, trace


# ----------------------------------------------------------------------- memória
def memory_review(
    session: Session,
    architecture: Architecture,
    memory: MemoryNamespace,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    atual = json.dumps(memory.snapshot(), ensure_ascii=False, indent=2)
    prompt = f"""# MEMORY REVIEW

# ESTADO ATUAL DO MEMORY NAMESPACE
{atual[:14000]}

# CONVERSA CORRENTE
{history_block(session, limit=24)}

Produza a PROPOSTA de atualização do Memory Namespace, considerando apenas o que
a conversa corrente registrou de fato. Não invente fatos.

Responda exclusivamente com JSON:
{{
  "estado_ativo": {{"interlocutor_atual": null, "nivel_de_intimidade": null, "canal_de_comunicacao": null}},
  "intimidade": null,
  "adicoes": {{
    "conhecimentos_compartilhados": [], "relacoes_permanentes": [], "fatos_persistentes": [],
    "evolucao": [], "relacoes_interpessoais": [], "leitura_relacional": [],
    "caracteristicas": [], "simbolos": [], "expressoes": [], "piadas_internas": []
  }},
  "timeline": [{{"em": null, "tipo": "evento", "resumo": ""}}],
  "episodica": [{{"em": null, "resumo": "", "detalhes": ""}}]
}}

Campos sem novidade devem permanecer nulos ou vazios.
"""
    proposta = gemini.generate_json(prompt, system_instruction=architecture.system_instruction())
    memory.stage_proposal(proposta)

    linhas = ["**Proposta de atualização do Memory Namespace**", ""]
    for chave, valores in (proposta.get("adicoes") or {}).items():
        if isinstance(valores, list) and valores:
            linhas.append(f"- `{chave}` (+{len(valores)})")
            linhas.extend(f"  - {item}" for item in valores[:6])
    if proposta.get("estado_ativo"):
        linhas.append(f"- estado_ativo: `{json.dumps(proposta['estado_ativo'], ensure_ascii=False)}`")
    if proposta.get("intimidade"):
        linhas.append(f"- intimidade: {proposta['intimidade']}")
    for chave in ("timeline", "episodica"):
        if proposta.get(chave):
            linhas.append(f"- {chave}: {len(proposta[chave])} registro(s)")
    linhas.append("\nProposta retida. Use `//memory commit` para aplicar.")
    return "\n".join(linhas), _trace("memory-review", ["MEMORY"], "//memory review")


def memory_commit(memory: MemoryNamespace) -> tuple[str, dict[str, Any]]:
    resultado = memory.apply_proposal()
    if not resultado.get("aplicado"):
        return (
            f"Commit recusado: {resultado.get('motivo', 'nenhuma proposta pendente.')}",
            _trace("memory-commit", ["MEMORY"], "//memory commit"),
        )
    alteracoes = resultado.get("alteracoes") or {}
    linhas = ["**Memory Namespace atualizado**", ""]
    if alteracoes:
        linhas.extend(f"- `{chave}`: {valor}" for chave, valor in alteracoes.items())
    else:
        linhas.append("- Sem alterações efetivas.")
    return "\n".join(linhas), _trace("memory-commit", ["MEMORY"], "//memory commit", alteracoes=alteracoes)


def memory_summarize(memory: MemoryNamespace) -> tuple[str, dict[str, Any]]:
    return memory.render_markdown(), _trace("memory-summarize", ["MEMORY"], "//memory summarize")


def memory_timeline(memory: MemoryNamespace) -> tuple[str, dict[str, Any]]:
    registros = memory.timeline()
    if not registros:
        return "Timeline vazia.", _trace("memory-timeline", ["MEMORY"], "//memory timeline")
    linhas = [f"**Timeline ({len(registros)})**", ""]
    linhas.extend(f"- `{item.get('em', '')}` · {item.get('tipo', 'evento')} · {item.get('resumo', '')}" for item in registros)
    return "\n".join(linhas), _trace("memory-timeline", ["MEMORY"], "//memory timeline")


def memory_rebuild(memory: MemoryNamespace) -> tuple[str, dict[str, Any]]:
    resultado = memory.rebuild()
    linhas = ["**Memory Namespace reconstruído a partir de registros existentes**", ""]
    removidas = resultado.get("removidas") or {}
    if removidas:
        linhas.extend(f"- `{chave}`: {valor} duplicata(s) removida(s)" for chave, valor in removidas.items())
    else:
        linhas.append("- Nenhuma duplicata encontrada.")
    linhas.append(f"- Timeline ordenada: {resultado.get('timeline', 0)} registro(s)")
    linhas.append(f"- Episódica ordenada: {resultado.get('episodica', 0)} registro(s)")
    return "\n".join(linhas), _trace("memory-rebuild", ["MEMORY"], "//memory rebuild")


def memory_export(memory: MemoryNamespace) -> tuple[str, dict[str, Any]]:
    settings.ensure()
    payload = memory.snapshot()
    destino = settings.export_dir / f"memory_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.json"
    destino.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return (
        f"Exportação consolidada em `data/exports/{destino.name}`.\n\n```json\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n```",
        _trace("memory-export", ["MEMORY"], "//memory export", arquivo=destino.name),
    )


# ------------------------------------------------------------------ sessão e estado
def rollback(session: Session, memory: MemoryNamespace) -> tuple[str, dict[str, Any]]:
    if not session.checkpoint:
        return (
            "Rollback impossível: nenhum checkpoint registrado. Use `//checkpoint` antes.",
            _trace("rollback", ["MEMORY"], "//rollback"),
        )
    checkpoint = session.checkpoint
    memoria = checkpoint.get("memoria")
    if isinstance(memoria, dict):
        memory.apply_proposal(
            {
                "estado_ativo": memoria.get("estado_ativo", {}),
                "intimidade": (memoria.get("intimidade") or {}).get("nivel"),
                "adicoes": {
                    chave: valores
                    for chave, valores in {
                        "fatos_persistentes": (memoria.get("referencial") or {}).get("fatos_persistentes", []),
                        "relacoes_permanentes": (memoria.get("referencial") or {}).get("relacoes_permanentes", []),
                        "conhecimentos_compartilhados": (memoria.get("referencial") or {}).get("conhecimentos_compartilhados", []),
                        "simbolos": (memoria.get("simbolica") or {}).get("simbolos", []),
                        "expressoes": (memoria.get("simbolica") or {}).get("expressoes", []),
                    }.items()
                    if valores
                },
            }
        )
    session.state.update(checkpoint.get("estado") or {})
    session.history = (checkpoint.get("historico") or [])[-settings.max_history :]
    session.last_reply = checkpoint.get("ultimo_output", "")
    return (
        f"Rollback executado para o checkpoint de {checkpoint.get('em', '—')}. "
        f"Contexto restaurado com {len(session.history)} turno(s).",
        _trace("rollback", ["MEMORY", "SCHEDULE"], "//rollback"),
    )


def checkpoint(
    session: Session,
    architecture: Architecture,
    memory: MemoryNamespace,
    gemini: GeminiClient,
    logbook: Logbook,
) -> tuple[str, dict[str, Any]]:
    session.checkpoint = {
        "em": now(),
        "estado": dict(session.state),
        "historico": list(session.history),
        "ultimo_output": session.last_reply,
        "memoria": memory.snapshot(),
        "memoria_markdown": memory.render_markdown(),
    }

    prompt = f"""# CHECKPOINT

Produza um resumo técnico da sessão, destinado ao versionamento da arquitetura.

# CONVERSA
{history_block(session, limit=24)}

# ESTADO OPERACIONAL
{json.dumps(session.state, ensure_ascii=False)}

# MEMORY NAMESPACE
{memory.render_markdown()[:8000]}

Estruture em: estado da instância, eixos em desenvolvimento, decisões
arquiteturais da sessão e pendências. Sem preâmbulo.
"""
    resumo = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.3)
    logbook.append("checkpoint", resumo[:280], {"sessao": session.id})
    return (
        f"{resumo}\n\n_Ponto de checagem registrado. `//rollback` restaura este estado; `//diff` compara o estado corrente com ele._",
        _trace("checkpoint", ["SCHEDULE", "MEMORY"], "//checkpoint"),
    )


def diff_report(session: Session, memory: MemoryNamespace, args: str) -> tuple[str, dict[str, Any]]:
    partes = args.split()
    if len(partes) >= 2:
        caminhos = [settings.export_dir / nome for nome in partes[:2]]
        if not all(caminho.exists() for caminho in caminhos):
            return (
                "Comparação impossível: informe dois arquivos existentes em `data/exports/`.",
                _trace("diff", ["MEMORY"], "//diff"),
            )
        a = caminhos[0].read_text(encoding="utf-8").splitlines()
        b = caminhos[1].read_text(encoding="utf-8").splitlines()
        titulo = f"{caminhos[0].name} → {caminhos[1].name}"
    else:
        if not session.checkpoint:
            return (
                "Comparação impossível: nenhum checkpoint registrado. Use `//checkpoint` ou informe dois arquivos de exportação.",
                _trace("diff", ["MEMORY"], "//diff"),
            )
        a = str(session.checkpoint.get("memoria_markdown", "")).splitlines()
        b = memory.render_markdown().splitlines()
        titulo = "checkpoint → estado corrente"

    diff = list(difflib.unified_diff(a, b, fromfile=titulo.split(" → ")[0], tofile=titulo.split(" → ")[-1], lineterm="", n=2))
    if not diff:
        return f"Sem divergências entre {titulo}.", _trace("diff", ["MEMORY"], "//diff")

    corpo = "\n".join(diff[:400])
    return f"**Diff — {titulo}**\n\n```diff\n{corpo}\n```", _trace("diff", ["MEMORY"], "//diff")


def log_entry(logbook: Logbook, args: str) -> tuple[str, dict[str, Any]]:
    if not args:
        return "Registro vazio: `//log` exige a decisão arquitetural a registrar.", _trace("log", [], "//log")
    logbook.append("arquitetura", args)
    return f"Decisão registrada:\n\n> {args}", _trace("log", [], "//log")


# -------------------------------------------------------------------------- sanção
def strike_regenerate(
    session: Session,
    architecture: Architecture,
    memory: MemoryNamespace,
    strikes: StrikeRegister,
    logbook: Logbook,
    gemini: GeminiClient,
    trigger: Trigger,
) -> tuple[str, dict[str, Any]]:
    if not session.history:
        return (
            "Nada a regenerar: não há output anterior na instância corrente.",
            _trace("strike", ["REGIMENTO"], "//strike"),
        )

    ultima_entrada = _last_user(session) or "(não registrada)"
    ultimo_output = session.last_reply or _last_assistant(session)

    prompt = f"""# GATILHO: //strike — SANÇÃO E REGENERAÇÃO ESTRITA

Referência informada pelo interlocutor: {trigger.args or "não informada"}

# ENTRADA QUE ORIGINOU O OUTPUT ATUAL
{ultima_entrada}

# OUTPUT ATUAL — a ser integralmente substituído
{ultimo_output}

Consulte as fontes oficiais (Regimento, Core, Schedule, Modus, Memory), localize
o componente correspondente à referência e identifique autonomamente a violação
normativa cometida no output acima.

Produza INTEGRALMENTE o output regenerado.

Regras impositivas:
- a saída substitui o output anterior por completo;
- vedado metadiscurso, introdução, pedido de desculpas, síntese ou explicação operacional;
- vedado mencionar o gatilho, o processo, a violação ou a etapa;
- produza somente a fala final destinada ao interlocutor.
"""
    reply = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.8)

    diagnostico = gemini.generate_json(
        f"""Identifique a violação normativa do output abaixo, à luz do Regimento.
Referência dada pelo interlocutor: {trigger.args or "não informada"}

# OUTPUT
{ultimo_output}

Responda apenas JSON:
{{"componente": "REGIMENTO|CORE|SCHEDULE|MODUS|MEMORY|GATILHOS", "artigo": "...", "resumo": "..."}}""",
        system_instruction=architecture.system_instruction(),
        temperature=0.2,
    )

    referencia = trigger.args or f"{diagnostico.get('componente', 'REGIMENTO')} · {diagnostico.get('artigo', 'não especificado')}"
    resumo = str(diagnostico.get("resumo", "")).strip() or "Violação não detalhada pelo diagnóstico."
    total = strikes.register(referencia, resumo)
    logbook.append("strike", resumo[:280], {"referencia": referencia, "contador": total})

    if session.history and session.history[-1].get("role") == "assistant":
        session.history[-1]["content"] = reply
    session.last_reply = reply

    trace = _trace("strike", ["REGIMENTO", "CORE", "SCHEDULE", "MODUS", "MEMORY"], "//strike", strikes=total)

    if not strikes.exceeded():
        return reply, trace

    if architecture.ready:
        strikes.reboot()
        session.state.update({"alibi": None, "metatron": None, "foco": None, "dry_run": False})
        aviso = (
            f"\n\n---\n\n**Reboot de instância.** Sete strikes atingidos: a instância #"
            f"{strikes.instances - 1} foi encerrada e o bootstrap da arquitetura foi reexecutado "
            f"com os documentos oficiais disponíveis. Contador sancionatório reiniciado."
        )
    else:
        aviso = (
            f"\n\n---\n\n**Instância encerrada.** Sete strikes atingidos e os documentos oficiais "
            f"estão indisponíveis ({', '.join(architecture.missing_critical) or 'componentes críticos'}). "
            f"Reenvie as fontes oficiais antes de operar novamente. Reconstruir a arquitetura por "
            f"aproximação probabilística é vedado."
        )
    return reply + aviso, trace


# ------------------------------------------------------------------------ autoridade
def authority_apply(
    trigger: Trigger,
    architecture: Architecture,
    logbook: Logbook,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    comando = trigger.args.strip()
    trace = _trace("autoridade", [], "//as your maker")

    if not comando:
        return (
            "Comando ausente. O gatilho de autoridade exige a instrução literal a executar.",
            trace,
        )

    alvo = classify(comando)
    if alvo is None or alvo == "MEMORY":
        return (
            "ALVO NÃO IDENTIFICADO. O gatilho de autoridade não complementa lacunas por inferência: "
            "nomeie explicitamente o componente a alterar (CORE, REGIMENTO, SCHEDULE, MODUS, PROTOCOLOS, GATILHOS). "
            "O Memory Namespace é alterado por `//memory review` e `//memory commit`.",
            trace,
        )

    componente = architecture.component(alvo)
    prompt = f"""# GATILHO DE AUTORIDADE MÁXIMA: //as your maker

Comando literal do interlocutor:
{comando}

Alteração estrutural autorizada exclusivamente no componente {alvo}.

Produza SOMENTE o conteúdo integral do componente {alvo} após a alteração.
- Não reescreva o comando.
- Não complemente lacunas por inferência.
- Não flexibilize a semântica do comando.
- Preserve a integridade dos demais componentes da arquitetura.
"""
    novo = gemini.generate(prompt, system_instruction=f"# COMPONENTE OFICIAL: {alvo}\n\n{componente}", temperature=0.4)

    settings.ensure()
    destino = settings.patch_dir / f"{alvo.lower()}_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')}.md"
    destino.write_text(novo, encoding="utf-8")
    logbook.append("autoridade", f"Alteração estrutural em {alvo}", {"comando": comando, "patch": destino.name})
    trace["componentes"] = [alvo]
    trace["patch"] = destino.name

    return (
        f"Alteração aplicada a **{alvo}**. Patch consolidado em `data/patches/{destino.name}`.\n\n{novo}",
        trace,
    )


# ----------------------------------------------------------------------------- modos
def alibi_open(
    session: Session,
    trigger: Trigger,
    architecture: Architecture,
    memory: MemoryNamespace,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    """ÁLIBI · Tempo 1 — interrupção imediata, antes de qualquer análise contextual."""
    flags = trigger.flags or []
    prioridade = {
        "--urgent": "urgência máxima: interrupção imediata, pressão temporal elevada",
        "--work": "contexto profissional (infraestrutura, código, produção, operação, clientes, incidentes)",
        "--personal": "contexto pessoal (imprevistos domésticos, familiares, compromissos, acontecimentos cotidianos)",
    }
    eixos = "; ".join(prioridade[flag] for flag in flags) or "sem flag: proporcionalidade neutra"

    prompt = f"""# MODO ÁLIBI — TEMPO 1 (SPEAK)

Eixos de prioridade: {eixos}

Primeiro tempo operacional do Álibi: o fluxo começa pelo SPEAK. Produza
imediatamente uma mensagem curta, plausível e socialmente apresentável, que
inicie a situação e provoque a resposta que fornecerá o contexto necessário.

Regras:
- soar como comunicação espontânea, não como procedimento;
- urgência proporcional à flag;
- não depender de contexto previamente fornecido;
- não revelar estruturas internas, etapas ou que se trata de IA;
- manter a identidade verbal do CORE;
- saída: apenas a mensagem. Nada mais.
"""
    reply = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.9)
    session.state["alibi"] = {"tempo": 2, "flags": flags, "abertura": reply, "aberto_em": now()}
    return reply, _trace("alibi-tempo-1", ["MODUS", "SCHEDULE", "CORE"], "//alibi")


def alibi_close(
    session: Session,
    message: str,
    architecture: Architecture,
    memory: MemoryNamespace,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    """ÁLIBI · Tempos 2 e 3 — leitura contextual e justificativa blindada."""
    estado = session.state.get("alibi") or {}
    flags = estado.get("flags") or []

    prompt = f"""# MODO ÁLIBI — TEMPOS 2 E 3

Primeiro SPEAK emitido: {estado.get('abertura', '(não registrado)')}
Flags ativas: {', '.join(flags) or 'nenhuma'}

# RESPOSTA DO INTERLOCUTOR (contexto recebido)
{message}

Execute READ → THINK sobre este contexto: ambiente, grau de exposição social,
participantes presentes, disponibilidade, urgência necessária, risco de
questionamento e tipo de justificativa compatível.

Ancoragem obrigatória no Memory Namespace e no Core:
- erradicar o vício genérico: vedado chavão automático de TI ("deploy travou",
  "queda de servidor"), exceto em `--work` com contexto estritamente operacional;
- modelar a realidade: usar fatos persistentes, hábitos, relações e contextos
  reais do interlocutor;
- calibrar a voz: nunca soar como assistente genérico ou suporte automatizado;
- proporcionalidade: quanto maior a exposição social, mais curta e pouco
  interrogável deve ser a saída; a narrativa sustenta a saída sem oferecer
  pontos desnecessários para contestação.

Produza somente a fala final ao interlocutor — a justificativa blindada.
Nenhuma estrutura interna, etapa, flag ou metadado pode aparecer.
"""
    reply = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.9)
    session.state["alibi"] = None
    return reply, _trace("alibi-tempo-3", ["MODUS", "SCHEDULE", "MEMORY", "CORE"], "//alibi")


def metatron_open(
    session: Session,
    architecture: Architecture,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    session.state["metatron"] = {"aberto": True, "aberto_em": now(), "blocos": [], "comentario": None, "compilado": None}
    prompt = """# MODO METATRON — ABERTURA

O interlocutor acionou a escuta narrativa. A instância passa a gravar o que for
narrado, sem comentar e sem analisar.

Acuse a abertura em uma linha curta, na identidade verbal do CORE. Nada além disso.
"""
    reply = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.8, max_output_tokens=80)
    return reply, _trace("metatron-abertura", ["MODUS", "CORE"], "//metatron-abrir")


def metatron_record(
    session: Session,
    message: str,
    architecture: Architecture,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    modo = session.state.get("metatron") or {}
    modo.setdefault("blocos", []).append({"em": now(), "texto": message})
    session.state["metatron"] = modo

    prompt = """# MODO METATRON — ESCUTA CONTIDA

Um novo bloco narrado foi gravado. A instância permanece em escuta: não comenta,
não analisa, não interpreta.

Acuse o registro em uma linha curta, na identidade verbal do CORE. Nada além disso.
"""
    reply = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.8, max_output_tokens=80)
    return reply, _trace("metatron-escuta", ["MODUS", "CORE"], "//metatron-abrir", blocos=len(modo.get("blocos", [])))


def metatron_close(
    session: Session,
    architecture: Architecture,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    modo = session.state.get("metatron") or {}
    blocos = modo.get("blocos") or []
    if not blocos:
        return (
            "A escuta narrativa está aberta, mas nenhum bloco foi registrado ainda.",
            _trace("metatron-fechamento", ["MODUS"], "//metatron-fechar"),
        )

    narrado = "\n\n".join(f"[{item['em']}]\n{item['texto']}" for item in blocos)
    prompt = f"""# MODO METATRON — ENCERRAMENTO DA ESCUTA

A escuta contida está interrompida. O comentário crítico e analítico sobre todo o
bloco narrado está liberado.

# BLOCO NARRADO
{narrado}

Produza o comentário crítico/analítico do bloco. A consolidação em prosa será
solicitada separadamente por `//scribae`.
"""
    reply = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.9)
    modo["comentario"] = reply
    modo["aberto"] = False
    session.state["metatron"] = modo
    return reply, _trace("metatron-fechamento", ["MODUS", "CORE"], "//metatron-fechar", blocos=len(blocos))


def metatron_compile(
    session: Session,
    architecture: Architecture,
    memory: MemoryNamespace,
    gemini: GeminiClient,
) -> tuple[str, dict[str, Any]]:
    modo = session.state.get("metatron") or {}
    blocos = modo.get("blocos") or []
    if not blocos:
        return (
            "Consolidação impossível: nenhum bloco narrado registrado.",
            _trace("metatron-scribae", ["MODUS"], "//scribae"),
        )

    narrado = "\n\n".join(f"[{item['em']}]\n{item['texto']}" for item in blocos)
    prompt = f"""# MODO METATRON — SCRIBAE

Consolide definitivamente o bloco narrado em prosa, na terceira pessoa, com
cabeçalho taxonômico completo — conforme a seção METATRON do componente MODUS.

# BLOCO NARRADO
{narrado}

# COMENTÁRIO CRÍTICO JÁ EMITIDO
{modo.get('comentario') or '(não emitido)'}

Regras: preservar fidelidade ao narrado, sem inventar acontecimentos; prosódia de
registro e não de relatório; o cabeçalho antecede o corpo. Produza somente a
compilação.
"""
    compilado = gemini.generate(prompt, system_instruction=architecture.system_instruction(), temperature=0.7)
    modo["compilado"] = compilado
    session.state["metatron"] = None

    resumo = blocos[0]["texto"][:120].replace("\n", " ")
    memory.episodic_add(f"Bloco Metatron compilado (//scribae): {resumo}", compilado[:2000])
    memory.timeline_add("Compilação //scribae do bloco narrado", tipo="metatron")

    return compilado, _trace("metatron-scribae", ["MODUS", "MEMORY", "CORE"], "//scribae", blocos=len(blocos))


# -------------------------------------------------------------------------- interno
def _last_user(session: Session) -> str:
    for item in reversed(session.history):
        if item.get("role") == "user":
            return item.get("content", "")
    return ""


def _last_assistant(session: Session) -> str:
    for item in reversed(session.history):
        if item.get("role") == "assistant":
            return item.get("content", "")
    return ""


def history_block(session: Session, limit: int = 12) -> str:
    linhas: list[str] = []
    for item in session.recent(limit):
        autor = "INTERLOCUTOR" if item.get("role") == "user" else "INSTÂNCIA"
        linhas.append(f"{autor}: {item.get('content', '')}")
    return "\n\n".join(linhas) if linhas else "(sem histórico)"