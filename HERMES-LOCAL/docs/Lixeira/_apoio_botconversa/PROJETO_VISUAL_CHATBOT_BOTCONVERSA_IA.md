# Projeto Visual do Chatbot com IA - BotConversa + Hermes

Pastor Raniel, este documento mostra como o chatbot pastoral deve funcionar dentro do BotConversa, como os fluxos se relacionam, quais campos e etiquetas controlam o atendimento, onde a IA entra e por que cada peça existe.

---

## 1. Visão Geral do Chatbot

```mermaid
flowchart TD
    W["Pessoa no WhatsApp"] --> BC["BotConversa"]
    BC --> BV["Fluxo 1<br/>Boas Vindas Filadélfia"]

    BV --> R["Mensagem Padrão<br/>IA Rute"]
    BV --> CAD["Fluxo 2<br/>Atualização Cadastral"]
    BV --> VIS["Fluxo 3<br/>Visitante / Consolidação 24h"]

    R --> ORA["Pedido de Oração"]
    R --> ACON["Pedido de Aconselhamento<br/>Humano Necessário"]
    R --> CEL["G12 e Células"]
    R --> MIN["Ministérios"]
    R --> EVT["Eventos e Agenda"]
    R --> HUM["Atendimento Humano"]

    CAD --> WH["Webhook Hermes<br/>/webhook_atualizacao_cadastral"]
    VIS --> WH2["Webhook futuro<br/>/webhook_visitante"]
    ORA --> WH3["Webhook futuro<br/>/webhook_pedido_oracao"]

    WH --> DB["SQLite<br/>database/pastoral.db"]
    WH --> API["API BotConversa<br/>campos, etiquetas e sequências"]
    DB --> DASH["Dashboard Pastoral"]
```

**Resumo simples:** o BotConversa conversa com a pessoa, os fluxos organizam o caminho, a IA interpreta mensagens livres, as etiquetas dizem o estado do contato, os campos guardam dados, o webhook envia informações para o Hermes, e o dashboard mostra a visão pastoral.

---

## 2. Papel de Cada Camada

| Camada | O que faz | Por que precisamos |
|---|---|---|
| WhatsApp | Entrada real das pessoas | É onde membros, visitantes e liderança já falam |
| BotConversa | Organiza fluxos, botões, campos e etiquetas | Dá controle visual e reduz dependência de código |
| IA Rute | Interpreta mensagens livres e identifica intenção | Pessoas não falam sempre por botões; a IA entende linguagem natural |
| Fluxos visuais | Executam passos exatos | Cadastro, etiquetas, sequências e webhooks precisam ser previsíveis |
| Campos personalizados | Guardam dados do contato | Permitem saber bairro, célula, líder, G12, ministérios, status |
| Etiquetas | Marcam estado operacional | Permitem segmentar, filtrar, encaminhar e impedir confusão |
| Sequências | Fazem follow-up por tempo | Retomar cadastro, recadastro anual, consolidar visitante em 24h |
| Webhook Hermes | Liga BotConversa ao sistema local | Salva dados no SQLite e sincroniza com o dashboard |
| Dashboard | Mostra métricas e pendências | O Pastor enxerga cuidado, cadastro, consolidação e comunicação |

---

## 3. Regra Principal da Arquitetura

```mermaid
flowchart LR
    IA["IA"] --> IAF["Interpreta<br/>classifica<br/>resume<br/>extrai dados"]
    FL["Fluxo Visual"] --> FLF["Aplica etiqueta<br/>salva campo<br/>chama webhook<br/>inicia outro fluxo"]

    IAF --> DEC["Decisão clara"]
    DEC --> FLF
```

**A IA interpreta. O fluxo visual executa.**

Essa separação evita que a Rute diga “vou encaminhar” mas o BotConversa não encaminhe de verdade. O encaminhamento real precisa acontecer por saída do Assistente GPT, condição por campo, ou webhook/API.

---

## 4. Roteamento Principal da Rute

```mermaid
flowchart TD
    MSG["Mensagem livre do contato"] --> RUTE["IA Rute<br/>Mensagem Padrão"]

    RUTE --> UI["Salva<br/>Ultima_Intencao"]
    RUTE --> RES["Salva<br/>Resumo_Atend_IA"]
    RUTE --> URG["Salva<br/>Nivel_Urgencia"]

    UI --> COND{"Qual intenção?"}

    COND -->|Atualizacao_Cadastral| C2["Fluxo 2A<br/>Atualização ou Recadastro"]
    COND -->|Visitante| C3["Fluxo 3<br/>Visitante"]
    COND -->|Pedido_Oracao| C4["Pedido de Oração"]
    COND -->|Aconselhamento| C5["Pedido de Aconselhamento<br/>Humano Necessário"]
    COND -->|Celula_G12| C6["G12 e Células"]
    COND -->|Ministerio| C7["Ministérios"]
    COND -->|Evento| C8["Eventos e Agenda"]
    COND -->|Humano ou Interrupcao| C9["Atendimento Humano"]
    COND -->|Outros| C10["Rute responde ou mostra menu"]
```

### Saídas recomendadas do Assistente GPT

| Saída | Quando usar | Destino |
|---|---|---|
| `AtualizaCadastro` | Pessoa quer atualizar ou confirmar dados | Atualização Cadastral |
| `PedidoOracao` | Pedido de oração/intercessão | Pedido de Oração |
| `Aconselhamento` | Pedido pastoral, crise, assunto sensível | Atendimento humano/pastoral |
| `CelulaG12` | Célula, G12, líder, participação | G12 e Células |
| `Ministerio` | Servir, ministério, louvor, mídia, recepção | Ministérios |
| `Evento` | Culto, agenda, inscrição, programação | Eventos e Agenda |
| `Humano` | Pede secretaria, pastor ou atendente | Atendimento humano |
| `Interrupcao` | Frustração, repetição, fora do escopo | Interrupção / humano |
| `Inatividade` | Não respondeu dentro do tempo | Encerrar ou retomar |
| `Menu` | Pedido confuso ou quer recomeçar | Menu principal |

---

## 5. Fluxos Visuais do Chatbot

```mermaid
flowchart TB
    F1["1. Boas Vindas Filadélfia"]
    F2["2. Atualização Cadastral Completa"]
    F2A["2A. Recadastro Anual"]
    F3["3. Visitante / Consolidação 24h"]
    F4["4. Mensagem Padrão - IA Rute"]
    F5["5. Pedido de Oração"]
    F6["6. Pedido de Aconselhamento"]
    F7["7. G12 e Células"]
    F8["8. Ministérios"]
    F9["9. Eventos e Agenda"]
    F10["10. Atendimento Humano / Interrupção"]

    F1 --> F2
    F1 --> F2A
    F1 --> F3
    F1 --> F4

    F4 --> F2A
    F4 --> F3
    F4 --> F5
    F4 --> F6
    F4 --> F7
    F4 --> F8
    F4 --> F9
    F4 --> F10

    F2A --> F2
```

### Por que cada fluxo existe

| Fluxo | Objetivo | Por que não deixar tudo na IA |
|---|---|---|
| Boas Vindas | Receber e classificar contato | Primeiro contato precisa de caminho simples e controlado |
| Atualização Cadastral | Coletar dados obrigatórios | Cadastro exige campos específicos e confirmação |
| Recadastro Anual | Ver uma vez por ano se os dados continuam iguais | Mantém base limpa sem cansar membros |
| Visitante | Garantir consolidação em 24h | Visitante não pode ficar perdido em conversa livre |
| IA Rute | Responder e rotear mensagens livres | A pessoa pode escrever de muitos jeitos diferentes |
| Pedido de Oração | Registrar cuidado espiritual | Separa oração de cadastro e agenda |
| Aconselhamento | Triagem pastoral sensível | Precisa humano e cuidado, não automação livre |
| G12 e Células | Direcionar célula/consolidação | Ajuda Caleb e liderança a acompanhar |
| Ministérios | Organizar interesse em servir | Ajuda a conectar pessoas ao serviço correto |
| Eventos e Agenda | Informar datas confirmadas | Evita resposta inventada sobre eventos |
| Atendimento Humano | Encerrar automação quando necessário | Protege a pessoa e a igreja em casos sensíveis |

---

## 6. Etiquetas: O Estado do Contato

```mermaid
flowchart LR
    E["Etiquetas"] --> V["Vínculo<br/>Membro / Visitante / Outro"]
    E --> C["Cadastro<br/>Completo / Incompleto / Pendente"]
    E --> A["Atualização<br/>Concluída / Recusada / Anual"]
    E --> P["Pastoral<br/>Oração / Aconselhamento / Humano"]
    E --> G["Células e G12<br/>Célula / G12 Pastoral"]
    E --> M["Ministério<br/>Interesse ou área específica"]
    E --> IA["Controle da IA<br/>Em Atendimento / Encaminhado / Resolvido"]
```

### Etiquetas globais recomendadas

| Etiqueta | Serve para |
|---|---|
| `Filadelfia Corrente` | Marcar todo contato do WhatsApp da igreja |
| `Membro` | Separar quem já faz parte da igreja |
| `Visitante` | Separar interessados e novos contatos |
| `Outro-Vinculo` | Pessoas que não entram claramente como membro ou visitante |
| `Cadastro Completo` | Dados mínimos preenchidos |
| `Cadastro Incompleto` | Faltam dados obrigatórios |
| `Atualização Cadastral` | Atualização do ciclo vigente concluída |
| `Atualização Pendente` | Precisa atualizar neste ciclo |
| `Atualização Recusada` | Pessoa recusou ou adiou |
| `Atualização Confirmada Sem Alteração` | Confirmou que nada mudou |
| `Recadastro Anual Agendado` | Está na rotina anual |
| `Consolidação 24h` | Visitante precisa de contato rápido |
| `Pedido de Oração` | Pedido registrado para intercessão |
| `Pedido de Aconselhamento` | Precisa triagem pastoral |
| `Humano Necessário` | Robô deve parar e humano assumir |
| `Em Atendimento Humano` | Conversa aberta com atendente |
| `Célula` | Interesse ou assunto de célula |
| `Ministério` | Interesse em servir |
| `IA - Em Atendimento` | IA está conduzindo a conversa |
| `IA - Encaminhado` | IA já enviou para outro fluxo |
| `IA - Resolvido` | Atendimento automatizado concluído |

**Por que etiquetas são essenciais:** elas impedem que todos os contatos sejam tratados igual. Sem etiqueta, o bot não sabe se está falando com membro, visitante, pessoa em crise, cadastro incompleto ou alguém aguardando humano.

---

## 7. Campos Personalizados: A Memória do Contato

```mermaid
flowchart TD
    CP["Campos Personalizados"] --> DADOS["Dados pessoais<br/>Nome, telefone, nascimento, bairro"]
    CP --> IGREJA["Vida na igreja<br/>tempo, célula, líder, G12"]
    CP --> TRILHA["Trilha de crescimento<br/>Encontro, UV, CD"]
    CP --> SERV["Serviço<br/>ministérios e interesse"]
    CP --> CUID["Cuidado pastoral<br/>oração, aconselhamento, urgência"]
    CP --> IA["Controle da IA<br/>última intenção, resumo, status"]
```

### Campos principais

| Campo | Uso lógico |
|---|---|
| `Data Nascimento` | Dados pessoais e cuidado por faixa etária/aniversário |
| `Bairro` | Saber região, célula próxima e logística pastoral |
| `Tempo_Igreja` | Entender maturidade e integração |
| `Lider_Celula` | Saber quem acompanha a pessoa |
| `Celula_Atual` | Mapear vínculo com célula |
| `G12_Pastoral` | Identificar rede pastoral |
| `Fez_Encontro` | Saber etapa da trilha de crescimento |
| `Universidade_Vida` | Acompanhar formação |
| `Capacitacao_Destino` | Acompanhar capacitação |
| `Ministerios` | Saber onde já serve |
| `Interesse_Ministerio` | Encaminhar para área de serviço |
| `Feedback_Melhorias` | Ouvir sugestões da igreja |
| `Feedback_falta` | Perceber dores e necessidades |
| `Ultima_Atualiz_Cadas` | Saber quando o cadastro foi atualizado |
| `Prox_Recadastro` | Programar recadastro anual |
| `Status_Cadastro` | Completo, Incompleto, Atualizar ou Recusou |
| `Tipo_Vinculo` | Membro, Visitante, Líder ou Outro |
| `Resumo_Atend_IA` | Auditoria da conversa com IA |
| `Ultima_Intencao` | Roteamento da Rute geral |
| `Nivel_Urgencia` | Baixa, Média, Alta ou Crise |
| `Status_Atendimento_IA` | Aberto, Encaminhado, Resolvido ou Humano |
| `Ultimo_Fluxo_Encaminhado` | Evita repetição e mostra para onde foi enviado |

**Por que campos são essenciais:** etiqueta diz “estado”; campo guarda “informação”. Exemplo: `Visitante` é etiqueta; `Bairro`, `Como_Conheceu_Igreja` e `Disponibilidade_Celula` são campos.

---

## 8. Cadastro: Como o Bot Decide se Está Completo

```mermaid
flowchart TD
    M["Contato se declara membro"] --> C{"Dados mínimos existem?"}
    C -->|Não| INC["Aplicar<br/>Cadastro Incompleto<br/>Atualização Pendente"]
    INC --> FL["Iniciar<br/>Atualização Cadastral"]
    FL --> WH["Chamar webhook Hermes"]
    WH --> DB["Atualizar membros no SQLite"]
    DB --> CHECK{"Cadastro completo?"}
    CHECK -->|Sim| OK["Aplicar Cadastro Completo<br/>Atualização Cadastral<br/>inscrever recadastro anual"]
    CHECK -->|Não| PEND["Manter Cadastro Incompleto<br/>pedir dados faltantes"]
    C -->|Sim| CONF["Recadastro Anual, se vencido"]
```

### Campos mínimos para membro

| Obrigatório | Por que importa |
|---|---|
| Nome | Identificação básica |
| Telefone | Contato pastoral |
| Bairro/cidade | Célula, logística e cuidado regional |
| Tempo de igreja | Maturidade e histórico |
| Líder de célula | Responsável pelo acompanhamento |
| Célula atual | Vínculo prático de cuidado |
| G12 pastoral | Rede pastoral |
| Fez Encontro | Trilha de consolidação |
| Universidade da Vida | Formação |
| Capacitação Destino | Capacitação |

---

## 9. Fluxo de Atualização Cadastral com Webhook

```mermaid
sequenceDiagram
    participant Pessoa as Pessoa
    participant Bot as BotConversa
    participant IA as Rute Cadastro
    participant WH as Hermes Webhook
    participant DB as SQLite
    participant API as API BotConversa

    Pessoa->>Bot: Quero atualizar meus dados
    Bot->>Pessoa: Mostra dados atuais e opções
    Pessoa->>Bot: Atualizar algo
    Bot->>IA: Ativa Rute Cadastro
    IA->>Pessoa: Pergunta o que mudou
    Pessoa->>IA: "Mudei de célula e fiz o Encontro"
    IA->>Bot: Salva Resumo_Atend_IA com bloco estruturado
    Bot->>WH: POST /webhook_atualizacao_cadastral
    WH->>DB: Atualiza tabela membros
    WH->>API: Atualiza campos personalizados
    WH->>API: Aplica/remove etiquetas
    WH->>API: Inscreve sequência anual se completo
    DB->>Pessoa: Dashboard passa a refletir os dados
```

### Endpoint já existente

```text
POST /webhook_atualizacao_cadastral
```

### O que ele faz hoje

| Ação | Resultado |
|---|---|
| Recebe `subscriber_id`, `nome`, `telefone` e `resumo_ia` | Identifica o contato |
| Extrai bloco `[ATUALIZACAO_CADASTRAL]` | Transforma texto da IA em dados |
| Busca ou cria membro local | Garante vínculo com SQLite |
| Atualiza tabela `membros` | Mantém base pastoral local |
| Verifica se cadastro ficou completo | Decide status final |
| Atualiza campos no BotConversa | Mantém a plataforma sincronizada |
| Aplica/remove etiquetas | Atualiza estado operacional |
| Inscreve em sequências | Agenda recadastro anual |
| Grava `botconversa_sync_log` | Permite auditoria |

---

## 10. Visitante e Consolidação 24h

```mermaid
flowchart TD
    V["Pessoa diz que é visitante<br/>ou quer conhecer"] --> TAG["Aplicar Visitante<br/>Aplicar Consolidação 24h"]
    TAG --> DADOS["Coletar nome, telefone, bairro,<br/>como conheceu, interesse em célula"]
    DADOS --> RESP["Definir pessoa da equipe<br/>para acompanhar"]
    RESP --> SEQ["Inscrever em<br/>SEQ - Follow-up Visitante 24h"]
    SEQ --> HUM["Notificar equipe/liderança"]
    HUM --> DASH["Futuro: alimentar dashboard de consolidação"]
```

**Por que este fluxo existe:** visitante precisa ser cuidado rapidamente por alguem proximo. A etiqueta `Consolidação 24h` torna visível internamente quem ainda precisa de contato, mas a palavra "consolidador" nao deve ser usada com o visitante.

Campos recomendados:

| Campo | Por que |
|---|---|
| `Tipo_Vinculo = Visitante` | Separar visitante de membro |
| `Bairro` | Indicar célula próxima |
| `Como_Conheceu_Igreja` | Entender origem do visitante |
| `Disponibilidade_Celula` | Facilitar encaminhamento |
| `Consolidador_Responsavel` | Uso interno: saber quem vai acompanhar |
| `Status_Consolidacao` | Pendente, Contatado, Integrado ou Desistiu |

---

## 11. Controle Anti-Repetição da IA

```mermaid
flowchart TD
    MSG["Nova mensagem"] --> CHECK{"Status_Atendimento_IA<br/>= Encaminhado?"}
    CHECK -->|Sim| SAFE["Não chamar Rute geral de novo"]
    SAFE --> MENU["Enviar mensagem curta<br/>e mostrar menu"]
    CHECK -->|Não| IA["Chamar IA Rute"]
    IA --> ENC["Se encaminhar:<br/>aplicar IA - Encaminhado<br/>salvar último fluxo"]
    ENC --> FLUXO["Iniciar fluxo correto"]
    FLUXO --> FIM["No fim:<br/>remover IA - Encaminhado<br/>aplicar IA - Resolvido"]
```

### Por que isso é necessário

Sem controle de estado, a IA pode repetir a mesma resposta quando a pessoa responde apenas “ok”, “sim”, “tá” ou “obrigado”.  
Com `Status_Atendimento_IA`, `Ultima_Intencao` e `Ultimo_Fluxo_Encaminhado`, o BotConversa entende se deve continuar, mostrar menu ou evitar repetição.

---

## 12. Sequências: O Relógio do Cuidado

| Sequência | Quando entra | Quando sai | Por que existe |
|---|---|---|---|
| `SEQ - Retomar Atualizacao Cadastral` | Pessoa adia ou abandona cadastro | Conclui cadastro | Evitar cadastro eternamente incompleto |
| `SEQ - Recadastro Anual` | Cadastro completo | Inicia recadastro anual | Fazer revisão completa 1 vez ao ano |
| `SEQ - Follow-up Visitante 24h` | Visitante registrado | Integrado/desistiu/contatado | Garantir cuidado rápido |
| `SEQ - Pedido de Oracao Follow-up` | Pedido de oração sem crise | Acompanhamento concluído | Demonstrar cuidado após intercessão |

---

## 13. Onde Cada Informação Fica

```mermaid
flowchart LR
    BC["BotConversa"] --> T["Etiquetas<br/>estado do contato"]
    BC --> F["Campos personalizados<br/>dados do contato"]
    BC --> S["Sequências<br/>tempo e follow-up"]
    BC --> FL["Fluxos<br/>caminho visual"]

    WH["Webhook Hermes"] --> DB1["membros"]
    WH --> DB2["botconversa_config"]
    WH --> DB3["botconversa_sync_log"]
    WH --> DB4["consolidacao_visitantes<br/>futuro visitante"]
    WH --> DB5["compromissos / posts / metas<br/>quando aplicável"]

    DB1 --> DASH["Dashboard"]
    DB3 --> DASH
```

| Local | Guarda |
|---|---|
| BotConversa | Estado rápido do contato e conversa atual |
| `membros` | Cadastro pastoral local |
| `botconversa_config` | IDs de etiquetas, campos, fluxos e sequências |
| `botconversa_sync_log` | Histórico de sincronizações |
| `consolidacao_visitantes` | Visitantes e follow-up pastoral |
| Dashboard | Visão executiva do que está acontecendo |

---

## 14. Lógica de Decisão em Uma Página

```mermaid
flowchart TD
    START["Contato entrou no WhatsApp"] --> TAGGER["Aplicar Filadelfia Corrente"]
    TAGGER --> FULL{"Tem Cadastro Completo?"}

    FULL -->|Não| VINC{"Qual vínculo?"}
    VINC -->|Membro| CAD["Atualização Cadastral Completa"]
    VINC -->|Visitante| VIS["Visitante / Consolidação 24h"]
    VINC -->|Quero conhecer| CONH["Enviar informações da igreja<br/>oferecer contato"]
    VINC -->|Outro| RUTE["IA Rute ou Humano"]

    FULL -->|Sim| CICLO{"Atualização do ciclo atual feita?"}
    CICLO -->|Não| CONF["Recadastro Anual"]
    CICLO -->|Sim| RUTE2["IA Rute Geral"]

    RUTE2 --> INT{"Intenção detectada"}
    INT -->|Cadastro| CONF
    INT -->|Visitante| VIS
    INT -->|Oração| ORA["Pedido de Oração"]
    INT -->|Aconselhamento| HUM["Humano Necessário"]
    INT -->|Célula/G12| CEL["G12 e Células"]
    INT -->|Ministério| MIN["Ministérios"]
    INT -->|Evento| EVT["Eventos e Agenda"]
    INT -->|Outro| RESP["Responder se houver conhecimento confirmado"]
```

---

## 15. Ordem de Construção Recomendada

| Prioridade | Construir | Motivo |
|---|---|---|
| 1 | Etiquetas globais | Sem etiquetas o bot não sabe o estado do contato |
| 2 | Campos personalizados | Sem campos não há memória pastoral |
| 3 | Fluxo Boas Vindas | É a porta de entrada |
| 4 | Fluxo Atualização Cadastral | Base limpa para qualquer estratégia |
| 5 | Webhook cadastral | Liga BotConversa ao Hermes e dashboard |
| 6 | IA Rute geral com saídas | Roteia mensagens livres sem bagunça |
| 7 | Recadastro anual | Mantém dados atualizados sem cansar membros |
| 8 | Visitante / Consolidação 24h | Garante cuidado rápido com novos contatos |
| 9 | Oração, aconselhamento, célula, ministério e eventos | Expande cuidado por área |
| 10 | Sequências e automações por tempo | Fecha o ciclo de acompanhamento |

---

## 16. O Que Não Pode Ficar Solto

| Coisa solta | Deve virar |
|---|---|
| “Essa pessoa é visitante” | Etiqueta `Visitante` + campos de consolidação |
| “Faltam dados” | Etiqueta `Cadastro Incompleto` + `Status_Cadastro` |
| “Precisa atualizar” | Etiqueta `Atualização Pendente` + sequência de retomada |
| “Pediu oração” | Etiqueta `Pedido de Oração` + resumo |
| “Quer aconselhamento” | Etiqueta `Humano Necessário` + atendimento aberto |
| “Quer célula” | Intenção `Celula_G12` + fluxo G12 |
| “Quer servir” | Campo `Interesse_Ministerio` + etiqueta `Ministério` |
| “IA encaminhou” | `Status_Atendimento_IA = Encaminhado` + último fluxo |

---

## 17. Resumo Final

O chatbot com IA não é apenas uma conversa automática. Ele é um sistema de cuidado pastoral organizado:

1. Acolhe a pessoa.
2. Identifica o vínculo.
3. Coleta dados importantes.
4. Encaminha para o fluxo certo.
5. Marca o estado com etiquetas.
6. Salva informações em campos.
7. Usa sequências para não esquecer follow-up.
8. Envia dados ao Hermes por webhook.
9. Alimenta o dashboard.
10. Dá ao Pastor visão e controle sem depender de memória mental.

**Princípio central:** a conversa precisa virar estado, dado, acompanhamento e decisão.
