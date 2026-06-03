# Arquitetura Completa - Rute e Fluxos Pastorais no BotConversa

Este documento define a logica completa dos fluxos pastorais da Igreja Batista Filadelfia Internacional de Corrente no BotConversa, combinando:

- Fluxos visuais com botoes, condicoes, salvar campo e acoes.
- Assistentes de IA por contexto.
- Etiquetas para estado operacional.
- Campos personalizados para dados pastorais.
- Sequencias para retorno por tempo.
- Webhooks/API Hermes para verificacao semestral/anual e sincronizacao com SQLite.

## Fontes e capacidades confirmadas

Documentacao BotConversa consultada:

- Campos personalizados armazenam informacoes do contato e podem ser criados em `Configuracoes > Campos`.
- O bloco de conteudo com elemento `Salvar` pausa o fluxo ate a resposta do usuario e permite armazenar resposta.
- Sequencias permitem programar fluxos depois de minutos, horas ou dias.
- Boas Vindas e enviado apenas 1 vez para novos contatos.
- Resposta Padrao recebe mensagens que nao batem com palavra-chave, desde que nao exista fluxo aguardando resposta.
- Ordem de prioridade de acionamento: Campanha, Palavra-chave, Boas Vindas, Resposta Padrao.
- Bloco de acao pode notificar admins.
- Acao `Atribuir e abrir atendimento` encaminha para departamento/atendente e impede o robo de continuar respondendo enquanto a conversa esta aberta.
- Assistente GPT tem mensagem inicial, instrucoes, contexto, erro, sucesso, interrupcao, inatividade e resumo em campo.

## Inventario real atual

### Fluxos existentes

- `Atualização Cadastral`
- `Boas Vindas Filadelfia`
- `Encerrar Conversa`
- `Mensagem Padrão - IA RUTE`
- `VISITANTE`

### Etiquetas existentes

- `Atualização Cadastral`
- `Cadastro Completo`
- `Consolidação 24h`
- `CONVENÇÃO G12 2026`
- `Célula`
- `Filadelfia Corrente`
- `G12 Pastoral - Pastora Vanessa`
- `G12 Pastoral - Pr. Raniel`
- `Membro`
- `Ministério`
- `Ministério de Louvor`
- `Outro-Vinculo`
- `Visitante`

### Etiquetas que ainda devem ser criadas

- `Cadastro Incompleto`
- `Atualização Pendente`
- `Pedido de Oração`
- `Pedido de Aconselhamento`
- `Humano Necessário`
- `Em Atendimento Humano`
- `Atualização 6M Agendada`
- `Recadastro Anual Agendado`
- `Atualização Recusada`
- `Atualização Confirmada Sem Alteração`

### Campos personalizados existentes

Tipo observado:

- `type: 0` = texto
- `type: 2` = data

Campos:

| Campo atual | Tipo | Uso |
|---|---:|---|
| `Bairro` | texto | bairro/cidade |
| `Capacitacao_Destino` | texto | sim/nao/em curso/modulo |
| `Celula_Atual` | texto | nome da celula |
| `Data Nascimento` | data | nascimento |
| `Data_Conversao` | data | conversao |
| `Feedback_Melhorias` | texto | sugestoes |
| `Feedback_falta` | texto | ausencia/percepcao |
| `Fez_Encontro` | texto | sim/nao |
| `G12_Pastoral` | texto | Pr. Raniel/Pastora Vanessa/outro |
| `Lider_Celula` | texto | lider atual |
| `Ministerios` | texto | ministerios onde serve |
| `Tempo_Igreja` | texto | faixa de tempo |
| `Ultima_Atualiz_Cadas` | data | ultima atualizacao cadastral |
| `Universidade_Vida` | texto | sim/nao/em curso |

### Campos que ainda devem ser criados ou padronizados

- Criar `Interesse_Ministerio` como texto.
- Padronizar nome esperado `Ultima_Atualiz_Cadas` no sistema local, ou criar campo novo `Ultima_Atualizacao_Cadastral`. Recomendacao: usar o campo existente `Ultima_Atualiz_Cadas` no BotConversa e mapear localmente como `field_ultima_atualizacao`.
- Padronizar `Data Nascimento` no sistema local, ou criar `Data_Nascimento`. Recomendacao: usar o campo existente e ajustar a sincronizacao local.
- Criar `Status_Cadastro` como texto: `Completo`, `Incompleto`, `Atualizar`, `Recusou`.
- Criar `Tipo_Vinculo` como texto: `Membro`, `Visitante`, `Lider`, `Outro`.
- Usar `Resumo_Atend_IA` como texto para salvar resumo do Assistente GPT.
- Criar `Ultima_Intencao` como texto.
- Criar `Encaminhamento_Necessario` como texto.
- Criar `Nivel_Urgencia` como texto: `Baixa`, `Media`, `Alta`, `Crise`.
- Criar `Proxima_Atualizacao_Cadastral` como data, se o BotConversa aceitar data.
- Criar `Proximo_Recadastro_Anual` como data, se o BotConversa aceitar data.

## Principio de desenho

Use fluxo visual para tudo que precisa ser exato:

- Classificacao por botoes.
- Coleta de dados campo a campo.
- Aplicar/remover etiquetas.
- Inscrever/remover de sequencias.
- Abrir atendimento humano.
- Notificar secretaria/lideranca.

Use IA para tudo que precisa interpretar linguagem natural:

- Perguntas abertas.
- Duvidas gerais.
- Pedido de oracao em texto livre.
- Triagem de aconselhamento.
- Explicacoes sobre igreja, G12, celulas e ministerios.
- Resumo da conversa.

Nao deixe a IA decidir sozinha estados cadastrais criticos. Estados devem ser etiquetas/campos.

No bloco Assistente GPT, mantenha esta separacao:

- `Salvar resumo da interação em`: campo unico de auditoria, atualmente `Resumo_Atend_IA`.
- `Campos Personalizados`: campos cadastrais reais que a IA pode preencher quando entender uma informacao especifica, por exemplo `Bairro`, `Tipo_Vinculo`, `Status_Cadastro`, `Celula_Atual`, `Lider_Celula`, `Fez_Encontro`, `Universidade_Vida`, `Capacitacao_Destino` e `Ministerios`.

Nao use `Resumo_Atend_IA` dentro de `Campos Personalizados`.

## Padrao de linguagem e formatacao WhatsApp

- Cumprimento oficial: `Graça e Paz!`.
- Nao usar `Paz do Senhor` nos fluxos da Filadelfia Corrente.
- Em mensagens longas, separar informacoes por linhas curtas.
- Titulos de campos devem ir em negrito no formato WhatsApp: `*Nascimento:*`, `*Bairro/cidade:*`, `*Tempo de igreja:*`.
- Evitar blocos grandes sem hierarquia visual.

Exemplo:

```text
Graça e Paz, {primeiro-nome}! Para mantermos seu cadastro em dia, confira os dados que temos:

*Nascimento:* {Data Nascimento}
*Bairro/cidade:* {Bairro}
*Tempo de igreja:* {Tempo_Igreja}
*Líder de célula:* {Lider_Celula}
*Célula atual:* {Celula_Atual}
*G12 pastoral:* {G12_Pastoral}

Se estiver tudo igual, toque em *Tudo igual*. Se mudou algo, toque em *Atualizar algo*.
```

## Padrao de roteamento com Assistente GPT

O assistente nao deve tentar resolver todos os fluxos dentro da conversa livre. Ele deve atuar como triador quando estiver no fluxo geral.

Configuracao recomendada no bloco `Assistente GPT` da Rute geral:

1. Criar campos personalizados de controle:
   - `Ultima_Intencao`
   - `Precisa_Encaminhar`
   - `Resumo_Atend_IA`
2. No assistente, configurar `Salvar resumo da interação em` como `Resumo_Atend_IA`.
3. Em `Campos Personalizados`, configurar:
   - `Ultima_Intencao`: salvar uma das intencoes padronizadas.
   - `Precisa_Encaminhar`: salvar `Sim` quando a conversa deve sair da IA geral.
4. Na saida `Resposta bem-sucedida`, conectar em um bloco de condicoes.
5. O bloco de condicoes verifica `Ultima_Intencao` e envia para o fluxo certo.

Mapa de roteamento:

| `Ultima_Intencao` | Acao do BotConversa |
|---|---|
| `Atualizacao_Cadastral` | Iniciar `Fluxo 2A - Confirmacao Cadastral Semestral` |
| `Visitante` | Iniciar `VISITANTE` |
| `Pedido_Oracao` | Iniciar fluxo de pedido de oracao/intercessao |
| `Aconselhamento` | Atribuir e abrir atendimento humano |
| `Celula_G12` | Iniciar fluxo de celulas/G12 ou encaminhar responsavel |
| `Ministerio` | Iniciar fluxo de ministerios/voluntariado |
| `Evento` | Responder se houver data confirmada; senao encaminhar secretaria |
| `Outros` | Continuar na Rute geral |

Exemplo de comportamento:

```text
Usuario: Quero atualizar meu cadastro.
Rute: Claro. Vou te encaminhar para a atualização cadastral agora.

Ultima_Intencao = Atualizacao_Cadastral
Precisa_Encaminhar = Sim
```

Depois disso, o fluxo visual, nao a IA, deve acionar a conexao para o fluxo cadastral.

## Arquitetura de assistentes

### Rute - Secretaria e recepcao geral

Uso:

- Resposta padrao.
- Menu geral.
- Perguntas de culto, endereco, evento confirmado.
- Encaminhamento inicial.
- Triagem geral.

Sai para humano quando:

- Pastor/pastora/secretaria/atendente.
- Aconselhamento.
- Conflito, crise, denuncia, ajuda financeira.
- Informacao nao confirmada.

### Caleb - Consolidacao e G12

Criar segundo bloco `Assistente GPT` em fluxo proprio.

Uso:

- Duvidas de celula/G12 mais detalhadas.
- Visitante querendo celula.
- Lider relatando celula.
- Consolidacao apos visita.

Fluxo de ativacao:

- Rute identifica `celula`, `G12`, `visitante`, `consolidacao`.
- Condicao/saida da Rute envia para fluxo `G12 e Celulas` ou `VISITANTE`.
- Dentro desse fluxo, usar bloco Assistente GPT `Caleb` ou fluxo estruturado.

### Barnabe - Comunicacao

Criar quando houver demanda de midia:

- Divulgacao de evento.
- Legenda para Instagram.
- Roteiro de video.
- Aviso para grupo.

Nao deve atender publico geral sem validacao humana em comunicados oficiais.

### Neemias - Foco do Pastor

Nao usar para atendimento publico da igreja.

Uso interno futuro:

- Palavra-chave privada do Pastor.
- Fluxo protegido por contato/telefone do Pastor.
- Cobrar 3 vitorias do dia.

## Como misturar fluxo visual e IA

Modelo recomendado:

1. Fluxo visual recebe e classifica.
2. Condicoes olham etiquetas/campos.
3. Quando o caminho for livre/aberto, entra Assistente GPT.
4. Saida de sucesso do Assistente GPT volta para `Encerrar Conversa`.
5. Saida de interrupcao abre atendimento humano ou envia para fluxo especifico.
6. Resumo do Assistente GPT salva em `Resumo_Atend_IA`.
7. Webhook/API opcional envia dados para Hermes/SQLite.

Nao misturar tudo dentro de um unico assistente. A Rute deve ser o roteador cordial, nao o banco de regras inteiro.

## Logica central de cadastro

### Significado das etiquetas

- `Cadastro Completo`: dados obrigatorios minimos preenchidos.
- `Cadastro Incompleto`: faltam dados obrigatorios.
- `Atualização Cadastral`: atualizacao do ciclo vigente concluida.
- `Atualização Pendente`: precisa atualizar no ciclo atual.
- `Atualização 6M Agendada`: contato inscrito na sequencia de revisao semestral.
- `Recadastro Anual Agendado`: contato inscrito na sequencia anual.

### Campos obrigatorios para considerar cadastro completo

Obrigatorios minimos:

- Nome completo.
- Telefone.
- `Tipo_Vinculo`.
- `Bairro`.

Obrigatorios para membro:

- `Tempo_Igreja`.
- `Lider_Celula` ou resposta `Nao tenho lider`.
- `Celula_Atual` ou resposta `Nao participo`.
- `G12_Pastoral` ou resposta `Nao sei`.
- `Fez_Encontro`.
- `Universidade_Vida`.
- `Capacitacao_Destino`.

Desejaveis:

- `Data Nascimento`.
- `Data_Conversao`.
- `Ministerios`.
- `Interesse_Ministerio`.
- `Feedback_Melhorias`.
- `Feedback_falta`.

## Fluxo 1 - Boas Vindas Filadelfia

Objetivo:

Receber novos contatos, classificar vinculo e mandar para o fluxo correto.

Blocos:

1. `Bloco Inicial`.
2. Acao: aplicar `Filadelfia Corrente`.
3. Condicao: tem `Cadastro Completo`?
4. Condicao: tem `Atualização Cadastral`?

Ramos:

### A. Tem `Cadastro Completo` e tem `Atualização Cadastral`

Enviar para `Mensagem Padrão - IA RUTE`.

Mensagem:

```text
Graça e Paz! Eu sou a Rute. Como posso ajudar voce hoje?
```

### B. Tem `Cadastro Completo`, mas nao tem `Atualização Cadastral`

Enviar para `Fluxo 2A - Confirmacao Cadastral Semestral`.

Mensagem:

```text
Graça e Paz! Para mantermos o cuidado e a comunicacao da igreja em dia, preciso confirmar se seus dados continuam atualizados.
```

Botoes:

- `Continuam iguais`
- `Quero atualizar`

### C. Nao tem `Cadastro Completo`

Perguntar:

```text
Voce ja faz parte da Igreja Filadelfia ou esta nos visitando/conhecendo?
```

Botoes:

- `Sou membro`
- `Sou visitante`
- `Quero conhecer`
- `Outro vínculo`

Acoes:

- `Sou membro`: aplicar `Membro`, aplicar `Cadastro Incompleto`, enviar para `Atualização Cadastral`.
- `Sou visitante`: aplicar `Visitante`, enviar para `VISITANTE`.
- `Quero conhecer`: aplicar `Visitante`, mandar mensagem com culto/endereco e oferecer consolidacao.
- `Outro vínculo`: aplicar `Outro-Vinculo`, enviar para Rute ou humano conforme resposta.

## Fluxo 2 - Atualizacao Cadastral Completa

Objetivo:

Coletar dados faltantes e marcar cadastro completo.

Entrada:

- Novo membro.
- Membro sem cadastro completo.
- Membro com atualizacao pendente e deseja atualizar tudo.

Blocos:

1. Consentimento.
2. Nome completo.
3. Data nascimento.
4. Bairro/cidade.
5. Tempo de igreja.
6. Lider/celula.
7. G12 pastoral.
8. Trilha de crescimento.
9. Ministerios/interesse.
10. Feedback.
11. Confirmacao final.
12. Marcacao de etiquetas/campos.
13. Inscricao em sequencias.

### 2.1 Consentimento

Mensagem:

```text
Graça e Paz! Vamos atualizar seus dados para melhorar nossa comunicacao e cuidado pastoral. Leva poucos minutos. Podemos comecar?
```

Botoes:

- `Sim, vamos la`
- `Agora nao`

Se `Agora nao`:

- Aplicar `Atualização Pendente`.
- Opcional: aplicar `Atualização Recusada`.
- Inscrever na sequencia `SEQ - Retomar Atualizacao Cadastral`.
- Encerrar com gentileza.

### 2.2 Campos e tipos

Use `Salvar` em campos personalizados.

| Pergunta | Campo | Tipo ideal | Entrada |
|---|---|---|---|
| Nome completo | campo padrao nome | texto | salvar nome |
| Data de nascimento | `Data Nascimento` | data | data |
| Bairro e cidade | `Bairro` | texto | resposta livre |
| Tempo de igreja | `Tempo_Igreja` | texto | botao |
| Lider de celula | `Lider_Celula` | texto | resposta livre/botao |
| Celula atual | `Celula_Atual` | texto | resposta livre/botao |
| G12 pastoral | `G12_Pastoral` | texto | botao |
| Encontro com Deus | `Fez_Encontro` | texto | botao |
| Universidade da Vida | `Universidade_Vida` | texto | botao |
| Capacitacao Destino | `Capacitacao_Destino` | texto | botao |
| Ministerios | `Ministerios` | texto | resposta livre/botoes |
| Interesse em servir | `Interesse_Ministerio` | texto | resposta livre/botoes |
| Melhorias | `Feedback_Melhorias` | texto | resposta livre |
| Sente falta de algo | `Feedback_falta` | texto | resposta livre |
| Ultima atualizacao | `Ultima_Atualiz_Cadas` | data | data atual |

### 2.3 Opcoes recomendadas

`Tempo_Igreja`:

- `Menos de 6 meses`
- `6 meses a 2 anos`
- `Mais de 2 anos`

`G12_Pastoral`:

- `Pr. Raniel`
- `Pastora Vanessa`
- `Nao sei`
- `Outro`

`Fez_Encontro`:

- `Sim`
- `Nao`
- `Quero informacoes`

`Universidade_Vida` / `Capacitacao_Destino`:

- `Sim`
- `Nao`
- `Estou fazendo`
- `Quero informacoes`

### 2.4 Encerramento

Acoes:

- Aplicar `Cadastro Completo`.
- Aplicar `Atualização Cadastral`.
- Remover `Cadastro Incompleto`.
- Remover `Atualização Pendente`.
- Remover `Atualização Recusada`, se existir.
- Definir `Status_Cadastro = Completo`.
- Definir `Ultima_Atualiz_Cadas = data atual`.
- Inscrever em `SEQ - Revisao Cadastral 6M`.
- Inscrever em `SEQ - Recadastro Anual`.
- Opcional: webhook para Hermes salvar em `database/pastoral.db`.

Mensagem:

```text
Cadastro atualizado com sucesso. Muito obrigado! Deus abencoe sua vida.
```

## Fluxo 2A - Confirmacao Cadastral Semestral

Objetivo:

Verificar se dados sensiveis mudaram sem obrigar recadastro completo.

Implementacao recomendada:

- Usar um assistente separado chamado `Rute Cadastro`.
- Prompt completo em `docs/_apoio_botconversa/botconversa_assistente_atualizacao_cadastral.md`.
- O fluxo visual mostra os dados atuais e oferece botoes de confirmacao.
- Se a pessoa quiser atualizar, o assistente aceita texto/audio, identifica campos alterados e pergunta o que estiver faltando.
- O fluxo/Hermes salva o resumo e atualiza os campos com validacao.

Entrada:

- Tem `Cadastro Completo`.
- Nao tem `Atualização Cadastral`, ou tem `Atualização Pendente`.

Mensagem:

```text
Para mantermos nosso cuidado em dia, seus dados continuam os mesmos?
```

Botoes:

- `Sim, continuam`
- `Atualizar telefone/bairro`
- `Atualizar celula/lider`
- `Atualizar trilhas`
- `Atualizar ministerio`
- `Atualizar tudo`
- `Prefiro falar com a secretaria`

Ramos:

- `Sim, continuam`: aplicar `Atualização Cadastral`, remover `Atualização Pendente`, atualizar `Ultima_Atualiz_Cadas`, reinscrever sequencias.
- `Atualizar telefone/bairro`: salvar dados especificos, depois aplicar etiquetas de conclusao.
- `Atualizar celula/lider`: salvar `Lider_Celula`, `Celula_Atual`, `G12_Pastoral`.
- `Atualizar trilhas`: salvar `Fez_Encontro`, `Universidade_Vida`, `Capacitacao_Destino`.
- `Atualizar ministerio`: salvar `Ministerios`, `Interesse_Ministerio`.
- `Atualizar tudo`: enviar para `Atualização Cadastral`.
- `Prefiro falar com a secretaria`: aplicar `Humano Necessário`, manter `Atualização Pendente` e abrir atendimento humano.

Alternativa inteligente:

- Em qualquer opcao `Atualizar...`, enviar para `Rute Cadastro`.
- A primeira mensagem da IA deve dizer que a pessoa pode mandar texto ou audio explicando o que mudou.
- A IA deve retornar um resumo estruturado em `Resumo_Atend_IA`.
- O Hermes deve receber esse resumo por webhook e gravar os campos reais no BotConversa/SQLite.

## Fluxo 2B - Recadastro Anual

Objetivo:

Revisao completa 1 vez por ano.

Logica:

- Mensagem explica que e uma revisao anual.
- Pergunta se deseja confirmar por partes ou atualizar tudo.
- Usa os mesmos blocos do fluxo 2, mas pode pular perguntas com botoes `Continua igual`.
- Ao concluir, aplica `Cadastro Completo` + `Atualização Cadastral` e reinscreve em sequencias.

## Fluxo 3 - VISITANTE / Consolidacao

Objetivo:

Receber visitante e garantir consolidacao em ate 24h.

Blocos:

1. Acolhimento.
2. Nome.
3. Bairro/cidade.
4. Como conheceu a igreja.
5. Interesse.
6. Deseja contato da lideranca?
7. Encaminhamento.

Campos recomendados:

- `Tipo_Vinculo = Visitante`.
- `Bairro`.
- `Ultima_Intencao = Visitante`.
- `Resumo_Atend_IA`, se usar IA.

Acoes:

- Aplicar `Visitante`.
- Aplicar `Consolidação 24h`.
- Notificar admin/departamento consolidacao.
- Inscrever em `SEQ - Follow-up Visitante 24h`.
- Opcional: abrir atendimento para departamento `Consolidacao`.

IA:

- Usar Caleb se a conversa for aberta sobre celula/consolidacao.
- Para cadastro basico, preferir botoes e salvar campo.

## Fluxo 4 - Mensagem Padrao IA RUTE

Objetivo:

Atender mensagens livres que nao bateram com palavra-chave e contatos ja conhecidos.

Entrada:

- Resposta Padrao.
- Contato com `Cadastro Completo` e `Atualização Cadastral`.
- Usuario pediu menu/duvida geral.

Blocos:

1. Condicao de horario de atendimento, se quiser separar aberto/fechado.
2. Condicao de cadastro:
   - Se `Atualização Pendente`: enviar para confirmacao cadastral.
   - Se `Cadastro Incompleto`: enviar para atualizacao completa.
3. Assistente GPT Rute.
4. Saida sucesso: `Encerrar Conversa`.
5. Saida interrupcao: fluxo humano correto.

Saidas da Rute:

- Visitante/celula: enviar para `VISITANTE` ou `G12 e Celulas`.
- Pedido de oracao: enviar para `Pedido de Oracao`.
- Aconselhamento: enviar para `Pedido de Aconselhamento`.
- Ministerio: enviar para `Ministerios`.
- Evento: responder ou humano se data nao confirmada.

## Fluxo 5 - Pedido de Oracao

Objetivo:

Registrar pedido e encaminhar para intercessao.

Blocos:

1. Acolher.
2. Perguntar se pode registrar.
3. Salvar resumo em `Resumo_Atend_IA` ou campo `Pedido_Oracao` se criado.
4. Aplicar `Pedido de Oração`.
5. Notificar admins/intercessao.
6. Se crise/risco: abrir atendimento humano imediatamente.

IA:

- Rute pode acolher e resumir.
- Nao deixar IA fazer aconselhamento profundo.

## Fluxo 6 - Pedido de Aconselhamento

Objetivo:

Triar com seguranca e abrir atendimento humano.

Blocos:

1. Mensagem de privacidade/cuidado.
2. Perguntar nome e melhor horario para retorno, se necessario.
3. Salvar resumo curto.
4. Aplicar `Pedido de Aconselhamento`.
5. Aplicar `Humano Necessário`.
6. Acao `Atribuir e abrir atendimento` para secretaria/departamento pastoral.
7. Notificar admin.

Importante:

- Nao confirmar horario.
- Nao prometer resposta imediata.
- Nao deixar robo continuar depois de abrir atendimento.

## Fluxo 7 - G12 e Celulas

Objetivo:

Orientar sobre celulas/G12 e direcionar para lideranca.

Blocos:

1. Perguntar objetivo:
   - `Quero participar de uma celula`
   - `Ja sou lider`
   - `Tenho duvida sobre G12`
   - `Relatorio de celula`
2. Para participar: salvar bairro/disponibilidade.
3. Aplicar `Célula`.
4. Se visitante: aplicar `Consolidação 24h`.
5. Encaminhar para Caleb/central de celulas.

IA:

- Caleb responde duvidas abertas e explica G12.
- Relatorio de celula idealmente deve ir para Hermes/SQLite via webhook, nao apenas IA.

## Fluxo 8 - Ministerios e Voluntariado

Objetivo:

Registrar interesse de servir e encaminhar para responsavel.

Blocos:

1. Perguntar se ja e membro.
2. Perguntar area:
   - Louvor
   - Artes
   - Obreiros
   - Jovens
   - Kids
   - Consolidacao
   - Tecnologia
   - Cafe
   - Outro
3. Salvar em `Interesse_Ministerio`.
4. Aplicar `Ministério`.
5. Notificar responsavel/departamento.

IA:

- Rute pode explicar areas.
- Humano valida entrada no ministerio.

## Fluxo 9 - Eventos e Agenda

Objetivo:

Responder eventos confirmados e encaminhar datas incertas.

Blocos:

1. Assistente Rute com base de conhecimento.
2. Se evento confirmado: responder.
3. Se evento nao confirmado: aplicar `Humano Necessário` e abrir atendimento/secretaria.
4. Para inscricao em evento especifico, criar fluxo proprio.

Exemplo:

- `CONVENÇÃO G12 2026`: usar etiqueta propria e, se houver sequencia da caravana, inscrever.

## Fluxo 10 - Encerrar Conversa

Objetivo:

Fechar atendimento com gentileza.

Mensagem:

```text
Fico a disposicao. Deus abencoe!
```

Acoes opcionais:

- Se atendimento foi por IA, salvar `Resumo_Atend_IA`.
- Remover etiquetas temporarias conforme caso.

## Sequencias recomendadas

Atualmente nao ha sequencias criadas. Criar:

### `SEQ - Retomar Atualizacao Cadastral`

Uso:

- Pessoa clicou `Agora nao`.
- Pessoa abandonou fluxo cadastral.

Passos:

- Depois de 1 dia: enviar fluxo `Lembrete Atualizacao Cadastral 1`.
- Depois de 3 dias: enviar fluxo `Lembrete Atualizacao Cadastral 2`.
- Depois de 7 dias: notificar secretaria e manter `Atualização Pendente`.

Ao concluir cadastro:

- Remover contato dessa sequencia, se BotConversa permitir no fluxo.

### `SEQ - Revisao Cadastral 6M`

Uso:

- Apos concluir cadastro/confirmacao.

Configuracao ideal:

- Aguardar 180 dias.
- Enviar fluxo `Confirmacao Cadastral Semestral`.

Observacao:

Se o BotConversa nao permitir espera de 180 dias com estabilidade ou remocao/reativacao fina, usar Hermes como agendador externo e API `send_flow`.

### `SEQ - Recadastro Anual`

Uso:

- Apos cadastro completo.

Configuracao:

- Aguardar 365 dias.
- Enviar fluxo `Recadastro Anual`.

### `SEQ - Follow-up Visitante 24h`

Uso:

- Visitante ou interessado em conhecer.

Passos:

- Depois de 2 horas: mensagem de acolhimento, se ainda nao respondeu.
- Depois de 24 horas: perguntar se recebeu contato da lideranca.
- Se nao recebeu: notificar consolidacao.
- Depois de 72 horas: perguntar se ja foi inserido em celula.

### `SEQ - Pedido de Oracao Follow-up`

Uso:

- Pedido de oracao sem crise.

Passos:

- Depois de 2 dias: mensagem curta de cuidado.
- Depois de 7 dias: perguntar se deseja compartilhar testemunho/atualizacao.

## Verificacao por tempo: BotConversa x Hermes

### Usar sequencia do BotConversa quando:

- O prazo e relativo ao momento da conversa.
- Exemplo: lembrar em 1 dia, 3 dias, 24h, 180 dias depois do cadastro.
- A acao e enviar um fluxo.

### Usar Hermes/API quando:

- Precisa calcular datas com base em campo (`Ultima_Atualiz_Cadas`).
- Precisa remover/aplicar etiquetas em massa.
- Precisa cruzar dados com SQLite, Google Sheets, Notion ou dashboard.
- Precisa verificar contatos que nunca entraram em sequencia.
- Precisa rodar rotina mensal.

Rotina Hermes recomendada:

1. Buscar contatos do BotConversa.
2. Ler etiquetas e campos.
3. Se membro com `Cadastro Completo` e `Ultima_Atualiz_Cadas` > 180 dias:
   - Remover `Atualização Cadastral`.
   - Aplicar `Atualização Pendente`.
   - Enviar fluxo `Confirmacao Cadastral Semestral`.
4. Se `Ultima_Atualiz_Cadas` > 365 dias:
   - Enviar `Recadastro Anual`.
5. Atualizar dashboard local.

## Webhooks e sincronizacao Hermes

Usar webhook no fim dos fluxos criticos:

- Atualizacao cadastral concluida.
- Visitante registrado.
- Pedido de aconselhamento.
- Pedido de oracao.
- Interesse ministerial.
- Pedido de celula.

Payload recomendado:

```json
{
  "origem": "botconversa",
  "evento": "cadastro_concluido",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "tipo_vinculo": "{{Tipo_Vinculo}}",
  "bairro": "{{Bairro}}",
  "lider_celula": "{{Lider_Celula}}",
  "celula_atual": "{{Celula_Atual}}",
  "g12_pastoral": "{{G12_Pastoral}}",
  "ultima_atualizacao": "{{Ultima_Atualiz_Cadas}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

Se o BotConversa nao permitir variaveis exatamente com estes nomes, ajustar no painel conforme a sintaxe exibida no construtor.

## Ordem de implementacao

1. Criar etiquetas faltantes.
2. Criar campos faltantes.
3. Padronizar nomes de campos no Hermes/dashboard.
4. Criar sequencias.
5. Criar fluxos auxiliares: `Confirmacao Cadastral Semestral`, `Recadastro Anual`, `Pedido de Oracao`, `Pedido de Aconselhamento`, `G12 e Celulas`, `Ministerios`.
6. Ajustar `Boas Vindas Filadelfia` para roteamento por etiquetas.
7. Ajustar `Mensagem Padrão - IA RUTE` para checar cadastro antes da IA.
8. Adicionar webhooks de sincronizacao nos finais.
9. Testar com contatos ficticios:
   - visitante novo;
   - membro sem cadastro;
   - membro completo sem atualizacao;
   - membro completo atualizado;
   - pedido de pastor;
   - pedido de oracao;
   - pedido de celula.
