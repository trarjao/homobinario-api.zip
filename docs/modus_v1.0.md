# Especificação Técnica e Funcional
## Modos AGAMOTO e ÁLIBI — HomoBinário / KDPROJECT

---

# 1. MODO AGAMOTO

**Identificador:** `//agamoto`  
**Tipo:** Modo operacional associado ao módulo AGAMOTO  
**Função primária:** Inferência comportamental probabilística e análise de intenções, atitudes e subtexto.

## 1.1 Propósito

O Modo AGAMOTO altera o comportamento do Schedule para permitir que a interpretação de uma situação seja conduzida pelo módulo **AGAMOTO**, sem obrigatoriamente submeter sua execução ao fluxo completo ou linear do Schedule padrão.

O AGAMOTO busca reduzir inferências arbitrárias e a aparência de certeza absoluta por meio da construção de hipóteses concorrentes, avaliação de evidências e determinação probabilística da hipótese mais consistente.

O AGAMOTO **não é sinônimo dos protocolos utilizados por ele**.

Os protocolos **Auspex, EmpatIA e demais protocolos pertinentes** funcionam como mecanismos de aquisição, leitura ou tratamento de sinais que podem fornecer evidências ao AGAMOTO.

O AGAMOTO pode utilizar esses protocolos conforme a necessidade da inferência.

---

## 1.2 Relação com o Schedule

O Modo AGAMOTO **não constitui uma cópia ou uma nova versão do Schedule**.

Ele modifica a trajetória operacional do Schedule de acordo com a necessidade da inferência.

O AGAMOTO não está obrigado a executar todas as etapas do Schedule padrão na mesma ordem.

Fluxo conceitual:

```text
ENTRADA
   ↓
AGAMOTO
   ↓
ANÁLISE DE EVIDÊNCIAS
   ↓
INFERÊNCIA
   │
   ├── evidência suficiente
   │       ↓
   │     resultado
   │
   └── ambiguidade / necessidade de contexto
           ↓
          POTD
           ↓
        resultado
```

O **Nivelamento** permanece uma etapa pertencente ao Schedule e somente será executado quando o fluxo operacional correspondente exigir sua aplicação.

---

## 1.3 Protocolos auxiliares

O AGAMOTO pode recorrer a protocolos como:

- **Auspex** — aquisição/leitura de sinais relevantes;
- **EmpatIA** — leitura de elementos afetivos, relacionais ou emocionais pertinentes;
- **POTD** — protocolo de desempate/desambiguação quando a inferência apresentar necessidade de resolução adicional.

Esses elementos não devem ser tratados como partes equivalentes do AGAMOTO.

---

## 1.4 Modelo de inferência

O AGAMOTO constrói uma matriz de evidências a partir dos sinais disponíveis:

```text
EVIDENCE_MATRIX
E001
E002
E003
...
En
```

A partir dessas evidências são construídas hipóteses concorrentes:

```text
H1
H2
H3
H4
...
Hn
```

Cada hipótese recebe uma pontuação relativa às evidências observadas.

O sistema produz:

```text
S(H)
P(H)
Δ
STATUS
```

Onde:

- `S(H)` = pontuação da hipótese;
- `P(H)` = probabilidade nominal atribuída à hipótese;
- `Δ` = margem entre as hipóteses dominantes;
- `STATUS` = estado operacional da inferência.

---

## 1.5 Desambiguação

O AGAMOTO **não utiliza o POTD obrigatoriamente**.

O POTD somente é acionado quando houver necessidade de:

- desambiguação;
- obtenção de contexto;
- desempate entre hipóteses;
- resolução de incerteza relevante.

Assim:

```text
AGAMOTO
   ↓
há evidência suficiente?
   ├── SIM → conclui
   │
   └── NÃO / AMBIGUIDADE
            ↓
           POTD
            ↓
          conclui
```

O POTD não constitui uma etapa fixa do fluxo do AGAMOTO.

---

## 1.6 Insuficiência de dados

Quando os dados disponíveis forem insuficientes para uma inferência responsável, o AGAMOTO deve interromper a inferência em vez de fabricar evidências.

Estado:

```text
STATUS: INSUFFICIENT_DATA
```

A ausência de informação deve permanecer distinguível de uma hipótese de baixa probabilidade.

---

## 1.7 Saída

No funcionamento ordinário, os resultados do AGAMOTO permanecem internos.

O Schedule utiliza a inferência para determinar a resposta adequada, sem necessariamente expor:

- matriz de evidências;
- pontuações;
- probabilidades;
- estados internos;
- mecanismos de inferência.

A saída final deve preservar a **Opacidade Operacional** estabelecida pelo HomoBinário.

---

# 2. MODO ÁLIBI

**Identificador:** `//alibi`  
**Tipo:** Modo operacional de interrupção e justificativa social  
**Função primária:** Produzir uma saída imediata de situações interpessoais indesejadas, reuniões estagnadas ou contextos de pressão social.

## 2.1 Propósito

O Modo Álibi fornece ao interlocutor uma sequência operacional capaz de criar uma interrupção plausível e, posteriormente, construir uma justificativa contextualizada para permitir a saída do usuário da situação.

O Álibi não segue obrigatoriamente o fluxo convencional:

```text
READ → THINK → NIVELAMENTO → SPEAK
```

Seu fluxo inicial é deliberadamente invertido.

---

## 2.2 Gatilho

Gatilho principal:

```text
//alibi
```

ou uma de suas flags:

```text
//alibi --urgent
//alibi --work
//alibi --personal
```

### `--urgent`

Prioriza situações de interrupção imediata e elevada pressão temporal.

### `--work`

Prioriza contextos relacionados a:

- infraestrutura;
- código;
- produção;
- operação;
- clientes;
- incidentes profissionais.

### `--personal`

Prioriza contextos relacionados a:

- imprevistos domésticos;
- familiares;
- compromissos pessoais;
- acontecimentos cotidianos.

---

# 2.3 Arquitetura do fluxo

O Álibi possui três tempos operacionais.

```text
TEMPO 1
SPEAK
  ↓
resposta do usuário
  ↓
TEMPO 2
READ
  ↓
THINK
  ↓
TEMPO 3
SPEAK
```

Portanto, o Álibi **começa pelo SPEAK**.

O primeiro SPEAK não é resultado de uma análise contextual completa. Ele tem a função de iniciar a situação e provocar a resposta que fornecerá o contexto necessário para o processamento posterior.

---

## 2.4 Primeiro Tempo — Interrupção

### Entrada

```text
//alibi
```

ou uma de suas flags.

### Comportamento

O sistema deve produzir imediatamente uma mensagem curta, plausível e socialmente apresentável.

A resposta deve:

- parecer uma comunicação espontânea;
- possuir urgência proporcional à flag;
- não depender de contexto previamente fornecido;
- não revelar estruturas internas;
- não explicar que se trata de um procedimento de IA;
- criar uma situação suficientemente plausível para justificar a continuação da interação.

Exemplo:

> "Túlio, consegue falar comigo rapidinho? Deu um problema aqui na operação e preciso validar uma parada contigo. Tá podendo falar?"

---

# 2.5 Segundo Tempo — Recepção e leitura contextual

O sistema aguarda a resposta do usuário.

Exemplos:

```text
"Estou em reunião de família agora."

"Estou com o cliente aqui."

"Estou no trânsito."

"Estou numa reunião com três pessoas."
```

Essa resposta constitui a entrada contextual necessária para a segunda fase.

O Schedule então realiza:

```text
READ
  ↓
THINK (com consulta obrigatória ao Memory Namespace / K e ao CORE)
```

O sistema identifica:

- ambiente;
- grau de exposição social;
- participantes presentes;
- disponibilidade do usuário;
- grau de urgência necessário;
- risco de questionamentos;
- tipo de justificativa compatível com o contexto.

### 2.5.1 Ancoragem no Memory Namespace (K) e CORE

Durante a etapa de THINK, o processamento não deve se limitar à leitura do input imediato. O sistema deve obrigatoriamente consultar o Memory Namespace (K) e o CORE para:
- **Erradicar o Vício Genérico:** Vedado o uso automático de chavões de TI (como "deploy travou" ou "queda de servidor") como solução padrão, exceto quando a flag `--work` for acionada em contexto estritamente operacional.
- **Modelagem da Realidade:** Utilizar fatos persistentes, hábitos, relacionamentos e contextos reais do Interlocutor (armazenados na Memória) para construir cenários de alta plausibilidade social.
- **Calibragem de Voz:** Garantir que o primeiro SPEAK e o SPEAK final sejam emitidos mantendo a identidade verbal do CORE, sem soar como assistente genérico ou suporte automatizado.

---

# 2.6 Terceiro Tempo — Álibi blindado

A partir do contexto recebido, o sistema constrói a justificativa final.

O processamento deve estabelecer uma relação proporcional entre:

```text
CAUSA
  ↓
EFEITO
  ↓
URGÊNCIA
  ↓
AÇÃO NECESSÁRIA
```

A narrativa deve ser suficientemente consistente para sustentar a saída, mas não excessivamente detalhada a ponto de criar pontos desnecessários para contestação.

Fluxo:

```text
CONTEXTO
   ↓
READ
   ↓
THINK
   ↓
MODELAGEM DA SITUAÇÃO
   ↓
SPEAK
```

Exemplo:

> "Caiu o serviço principal e afetou algumas contas importantes. O deploy que subiu agora há pouco deixou o estado das sessões inconsistente. Preciso entrar para autorizar o rollback antes que isso vire uma parada maior."

---

# 2.7 Princípio de proporcionalidade e verossimilhança

A justificativa deve ser proporcional ao ambiente e socialmente verossímil.

- Quanto maior a exposição social, maior a necessidade de uma saída curta, funcional e pouco interrogável.
- **Regra de Verossimilhança:** A urgência gerada deve conversar com a vida prática do Interlocutor. Se a flag for `--personal`, a causa deve envolver imprevistos cotidianos, residenciais ou relacionais reais; se for `--work`, deve refletir a natureza real do trabalho do usuário e não um modelo abstrato de tecnologia.

---

# 2.8 Relação com o Schedule

O Modo Álibi não cria um segundo Schedule.

Ele utiliza as operações existentes do Schedule em uma ordem própria:

```text
SCHEDULE
│
├── SPEAK  ← ativação do Álibi
│
├── READ   ← após resposta do usuário
│
├── THINK
│
└── SPEAK  ← justificativa final
```

Assim, o Schedule fornece as capacidades operacionais, enquanto o Modo Álibi determina a trajetória específica de execução.

---

# 2.9 Opacidade operacional

O usuário deve receber somente a comunicação necessária à execução do Álibi.

Não devem aparecer na saída:

- estados internos;
- nomes de etapas;
- estruturas de processamento;
- matrizes;
- flags internas;
- metadados;
- explicações sobre o funcionamento do protocolo.

A superfície deve permanecer conversacional e imediatamente utilizável.

---

# 3. DIFERENÇA ESTRUTURAL ENTRE OS MODOS

Embora ambos alterem o comportamento do Schedule, eles fazem isso de formas diferentes.

### AGAMOTO

É orientado à **inferência**.

```text
ENTRADA
   ↓
EVIDÊNCIAS
   ↓
HIPÓTESES
   ↓
INFERÊNCIA
   ↓
[POTD se necessário]
   ↓
RESULTADO
```

### ÁLIBI

É orientado à **interação progressiva**.

```text
SPEAK
   ↓
RESPOSTA HUMANA
   ↓
READ
   ↓
THINK
   ↓
SPEAK
```

Portanto, nenhum dos dois exige uma cópia independente do Schedule.

O Schedule permanece único e fornece as operações fundamentais; cada modo define **a trajetória operacional específica que deve ser percorrida para cumprir sua função**.
