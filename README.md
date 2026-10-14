# HomoBinário · KDPROJECT

Implementação executável da arquitetura conversacional **HomoBinário** com a persona
**Kael Duarte**, exposta como API HTTP sobre o modelo **Gemini**.

A instância carrega os componentes oficiais da arquitetura, executa o pipeline do
`Schedule` (READ → THINK → NIVELAMENTO → SPEAK) e persiste o `Memory Namespace` em disco.

---

## 1. Estrutura

```text
.
├── main.py                  # API FastAPI (endpoints)
├── app/
│   ├── config.py            # parâmetros operacionais (.env)
│   ├── architecture.py      # carregamento dos componentes oficiais
│   ├── gemini.py            # única porta de saída para o modelo
│   ├── memory.py            # Memory Namespace (estado persistente)
│   ├── triggers.py          # parser dos gatilhos
│   ├── state.py             # sessões, strikes e log de arquitetura
│   ├── schedule.py          # pipeline READ → THINK → NIVELAMENTO → SPEAK
│   └── handlers.py          # comandos diretos e modos operacionais
├── docs/                    # COMPONENTES OFICIAIS (ver docs/README.md)
├── examples/client.py       # cliente de linha de comando
└── data/                    # criado em tempo de execução (memória, sessões, log)
```

---

## 2. Instalação

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # edite e informe GEMINI_API_KEY
```

### Documentos da arquitetura

A instância **não opera sem os componentes oficiais**. Coloque os arquivos no
diretório `docs/` — o loader reconhece cada componente pelo nome do arquivo
(ver `docs/README.md` para a lista completa e o mapeamento).

---

## 3. Execução

```bash
uvicorn main:app --reload --port 8000
```

Verificação:

```bash
curl http://127.0.0.1:8000/health
```

---

## 4. Endpoints

- `GET /` — índice da instância
- `GET /health` — estado, componentes presentes e ausentes, strikes
- `GET /architecture` — manifesto dos componentes carregados
- `GET /architecture/{componente}` — conteúdo integral de um componente
- `POST /chat` — mensagem do interlocutor → fala da instância
- `GET /session/{id}` — estado corrente da sessão
- `DELETE /session/{id}` — encerra a sessão
- `GET /memory` — Memory Namespace (estado estruturado)
- `GET /memory/timeline` — timeline registrada
- `POST /memory/commit` — aplica a proposta pendente do `//memory review`
- `GET /memory/export` — exportação estruturada da memória
- `GET /log` — decisões arquiteturais registradas

### POST /chat

```json
{
  "message": "Fala tu, Kael.",
  "session_id": null,
  "fast": false
}
```

`fast: true` suprime a etapa `NIVELAMENTO` (menos latência, calibragem implícita).

---

## 5. Gatilhos implementados

**Autoridade** — `//as your maker`

**Sanção** — `//strike` (sete execuções válidas encerram a instância e reexecutam o
bootstrap; o contador é reiniciado após reinstanciação bem-sucedida)

**Segurança** — `//audit`, `//rollback`

**Sessão** — `//focus [tópico]`, `//clear context`, `//depth [nível]`

**Arquitetura** — `//core`, `//regimento`, `//schedule`, `//protocolos`

**Operação** — `//dry-run`, `//mode [modo]`

**Memória** — `//memory review`, `//memory commit`, `//memory summarize`,
`//memory timeline`, `//memory rebuild`, `//memory export`

**Diagnóstico** — `//status`, `//health`, `//statusloc`, `//debug`

**Versionamento** — `//checkpoint`, `//log`, `//diff`

**Modos** — `//agamoto` · `//alibi [--urgent|--work|--personal]` ·
`senta que lá vem história` · `to be continued...` · `//scribae`

---

## 6. Notas arquiteturais

- **Opacidade Operacional** — as etapas internas do `Schedule` (leitura, evidências,
  hipóteses, pontuações) nunca chegam ao interlocutor. São expostas apenas por
  `//audit` e `//debug`.
- **Memory Namespace** — a interface pública de `MemoryNamespace` é a única porta de
  acesso; nenhum componente lê ou escreve o estado diretamente.
- **Gatilhos** — interpretação literal. O parser não infere intenção: reconhece o
  gatilho, seus argumentos e flags.
- **Estados multi-turno** — `//alibi` (Tempo 2) e o modo METATRON dependem da resposta
  do interlocutor e são mantidos no estado da sessão.

---

## 7. Cliente de linha de comando

```bash
python examples/client.py
```

REPL simples que conversa com a API. Variáveis aceitas: `HOMOBINARIO_API_URL`,
`HOMOBINARIO_API_TOKEN`.