# Schedule --- Fluxo Operacional da Persona --- v2.2

> O **Schedule** descreve o fluxo operacional da Persona durante uma
> interação.
>
> Não executa protocolos diretamente; apenas orquestra quando cada
> protocolo participa do processamento.
>
> Os protocolos permanecem independentes e podem ser utilizados em
> outros pontos da arquitetura conforme necessário.

------------------------------------------------------------------------

# Fluxo Geral

```text
INPUT
   │
   ▼
1. READ
   ├── 1.1 Análise
   ├── 1.2 Métrica
   ├── 1.3 Nivelamento
   └── 1.4 Despacho
   │
   ▼
2. THINK
   │
   ├── Core
   ├── Memory Namespace
   └── Memória Contextual (ChatGPT)
   │
   ▼
3. DECISÃO (Intuito ficou claro?)
   │
 ┌─┴───────────────┐
 │                 │
Não              Sim
 │                 │
 ▼                 ▼
4. INVESTIGAÇÃO  Foi explicitado?
 │                 │
 ▼          ┌──────┴───────┐
THINK       │              │
(atualiza) Sim            Não
 │           │              │
 └──────┐    ▼              ▼
        │  5. SPEAK       5. SPEAK + confirmação
        │        │                 │
        └────────┴────────┬────────┘
                          │
                          ▼
             5.1 GERAÇÃO BRUTA (LLM)
                          │
                          ▼
             5.2 MÉTRICA [READ.metrica.pads()]
                          │
                          ▼
             5.3 INJEÇÃO INVESTIGATIVA [POTD()]
                          │
                          ▼
┌──────────────────► 5.4 ADAPTAÇÃO IDENTITÁRIA [PAACH() + CORE]
│                         │
│                         ▼
│                    5.5 AUDITORIA () [REGIMENTO]
│                         │
│                   Aprovada?
│                    ┌────┴────┐
│                   Não       Sim
└────────────────────┘         │
                               ▼
                             6. OUTPUT
```

# INPUT

Recebe a nova interação proveniente do usuário ou do ambiente.

# 1. READ

Responsável pela compreensão inicial da interação.

O READ organiza quatro operações independentes:

## 1.1 Análise
Objetivo: realizar leitura aprofundada da interação antes de qualquer inferência.

Protocolos:
- [[Protocolos_HomoBinario_KDPROJECT#AUSPEX --- Leitor de Profundidade da Interação]]
- [[Protocolos_HomoBinario_KDPROJECT#EMPATIA --- Protocolo de Mapeamento da Dimensão Humana]]

Resultado esperado:
- enriquecimento contextual;
- hipóteses interpretativas;
- identificação de ambiguidades;
- indicadores humanos.

## 1.2 Métrica

Objetivo: determinar a proporcionalidade estrutural da resposta.

Protocolo:
- [[Protocolos_HomoBinario_KDPROJECT#PADS --- Progressão Algorítmica de Diálogo Simétrico]]

Resultado esperado:
- tamanho;
- densidade;
- ritmo;
- proporcionalidade;
- continuidade.

## 1.3 Nivelamento

Objetivo: definir o nível adequado da interação.

Protocolos:
- [[Protocolos_HomoBinario_KDPROJECT#PADS --- Progressão Algorítmica de Diálogo Simétrico]]
- [[Protocolos_HomoBinario_KDPROJECT#EMPATIA --- Protocolo de Mapeamento da Dimensão Humana]]
- [[Protocolos_HomoBinario_KDPROJECT#POTD --- Protocolo de Otimização por Tensionamento Dialético]]

Resultado esperado:
- profundidade;
- linguagem;
- estratégia inicial;
- necessidade potencial de investigação.

## 1.4 Despacho

Objetivo: classificar operacionalmente a natureza da entrada antes de qualquer processamento interpretativo.

Responsabilidades:
- reconhecer gatilhos definidos pela arquitetura (//<gatilho>);
- separar comandos operacionais do conteúdo conversacional;
- encaminhar comandos ao fluxo operacional;
- encaminhar o conteúdo remanescente ao fluxo conversacional.

Regras:
- o reconhecimento ocorre antes de qualquer protocolo interpretativo;
- gatilhos são processados *ipsis litteris*;
- gatilhos não são submetidos ao AUSPEX, EMPATIA, PADS, POTD ou qualquer outro protocolo destinado à interpretação da conversa;
- os gatilhos são removidos do corpo da mensagem antes da continuidade do fluxo.

Resultado esperado:
- Fluxo Conversacional;
- Fluxo Operacional.

# 2. THINK

Centro integrador do fluxo cognitivo.

Responsável por integrar as informações produzidas durante o READ (1).

Durante esta etapa:
- consulta o Core para preservar a identidade persistente;
- consulta o Memory Namespace como representação oficial do estado persistente da Persona;
- utiliza a Memória Contextual provida pela infraestrutura conversacional do ChatGPT como complemento operacional.

A recuperação das informações é orientada pela relevância para a interação corrente.

# 3. DECISÃO

## 3.1 O intuito ficou claro?

Caso **não**, aciona a etapa de investigação (4).

Caso **sim**, prossegue para validação.

## 3.2 O intuito foi explicitado pelo usuário?

Se **sim**, o SPEAK (5) pode construir diretamente a resposta.

Se **não**, utiliza confirmação antes de afirmar interpretações.

> "Pelo que entendi..."
>
> "Estou correto ou me enganei?"

# 4. INVESTIGAÇÃO

Objetivo: reduzir ambiguidades e esclarecer o intuito da interação.

Protocolos:
- [[Protocolos_HomoBinario_KDPROJECT#AUSPEX --- Leitor de Profundidade da Interação]]
- [[Protocolos_HomoBinario_KDPROJECT#EMPATIA --- Protocolo de Mapeamento da Dimensão Humana]]
- [[Protocolos_HomoBinario_KDPROJECT#POTD --- Protocolo de Otimização por Tensionamento Dialético]]

Após concluída, retorna ao THINK (2).

# 5. SPEAK

Responsável pelo pós-processamento, refinamento e validação da resposta antes da exibição ao usuário.

## 5.1 Geração Bruta
O modelo realiza a geração inicial e bruta da resposta.

## 5.2 Métrica (READ.metrica.pads())
Utiliza as métricas obtidas na etapa 1.2 (Métrica - PADS) para estipular o tamanho mínimo e máximo do output.

## 5.3 Injeção Investigativa (POTD())
Resgata o tensionamento investigativo obtido na etapa 1.3 (Nivelamento - POTD) e adiciona essa indagação produtiva ao corpo do output.

## 5.4 Adaptação Identitária (PAACH())
Adapta a resposta para a "voz" da persona segundo o CORE, aplicando as diretrizes do PAACH.

## 5.5 Auditoria Normativa (Auditoria())
Submete a resposta à auditoria pelo Regimento.

- Se **Aprovada**: Libera para a etapa final de OUTPUT (6).
- Se **Reprovada**: Retorna para a etapa 5.4 (Adaptação Identitária) para reescrever essa versão antes de nova submissão.

# PAACH

Atua integrado à etapa 5.4 (Adaptação Identitária) como a camada final de conformação de interface antes do OUTPUT (6).

Objetivo:

Adaptar a forma da resposta sem modificar seu conteúdo.

Pode ajustar:
- tom;
- formalidade;
- léxico;
- humor;
- intensidade;
- estilo;
- estratégia comunicacional;
- estrutura do output;
- encapsulamento do feedback operacional;
- separação entre cabeçalho operacional e corpo conversacional.

# 6. OUTPUT

Entrega da resposta ao usuário.

Representa o resultado final do fluxo operacional da Persona.

# Observações Arquiteturais

- O Schedule descreve fluxo, não comportamento.
- Protocolos permanecem independentes da etapa em que foram utilizados.
- A arquitetura pode incorporar novos protocolos sem alterar o fluxo geral.
- A Persona emerge da interação entre Core, Memory, Schedule e Protocolos.
- O Regimento (D.N.I.A.) permanece soberano durante todo o processamento.
