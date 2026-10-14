# Componentes oficiais da arquitetura

Coloque aqui os documentos oficiais. O loader (`app/architecture.py`) reconhece cada
componente pelo **nome do arquivo** — sem interpretar o conteúdo.

- `CORE_Kael_Duarte_v2-2_Consolidado.md` → **CORE** (crítico)
- `REGIMENTO_DO_HOMOBINARIO.md` → **REGIMENTO** (crítico)
- `Schedule_HomoBinario_KDPROJECT_v2.2.md` → **SCHEDULE** (crítico)
- `Gatilhos_HomoBinario_v1.5.md` → **GATILHOS** (crítico)
- `modus_v1.0.md` → **MODUS**
- `Protocolos_HomoBinario_KDPROJECT_v1-1_Consolidado-1_atualizado.md` → **PROTOCOLOS**
- `Memory_Namespace_v2.3_Consolidado.md` → **MEMORY**

Reconhecimento: o nome é convertido para minúsculas e sem acentos; o primeiro
marcador encontrado define o componente (`core`/`kael`, `regimento`, `schedule`,
`modus`, `protocolo`, `gatilho`, `memory`/`memoria`).

Arquivos sem marcador reconhecível entram em `ANEXOS` e são incluídos ao final.

## Ordem canônica da instrução de sistema

```text
CORE → REGIMENTO → SCHEDULE → MODUS → PROTOCOLOS → GATILHOS
```

O componente `MEMORY` não é enviado como texto fixo a cada turno: ele semeia o
`Memory Namespace`, cujo estado corrente é injetado como contexto volátil.

## Integridade

Se faltar um componente crítico, a instância **não opera** (`GET /health` reporta
`ready: false` e `POST /chat` responde `503`). Nesse caso, reenvie as fontes oficiais
ou atualize o diretório. É vedado reconstruir a arquitetura por aproximação.