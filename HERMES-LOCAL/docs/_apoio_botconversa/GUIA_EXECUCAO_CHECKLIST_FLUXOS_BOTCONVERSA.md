# Guia de Execucao - Checklist dos Fluxos BotConversa

Data: 2026-06-05  
Projeto: Hermes Filadelfia  
Objetivo: acompanhar a construcao dos fluxos no BotConversa sem deixar pontas soltas.

Este arquivo e o guia de trabalho do dia a dia.  
Use assim:

1. Abra o sumario.
2. Escolha o fluxo que vai construir.
3. Veja a proxima tarefa indicada.
4. Marque os checkboxes conforme terminar.
5. Consulte o guia mestre nos links de referencia.

Referencia superior: [Guia Mestre - Chatbot WhatsApp, BotConversa e Hermes](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md)

Documentos da Fase 3 Hermes 2.0:

- [Inventario BotConversa - Fase 3 Hermes 2.0](./INVENTARIO_BOTCONVERSA_FASE_3_HERMES_2.md)
- [Passo a Passo dos Fluxos BotConversa - Hermes 2.0](./PASSO_A_PASSO_FLUXOS_BOTCONVERSA_HERMES_2.md)
- [Plano de Recadastro Anual - Toda a Base](./PLANO_RECADASTRO_ANUAL_TODA_BASE.md)

---

## Sumario clicavel

- [0. Regra principal](#0-regra-principal)
- [1. Proxima tarefa indicada](#1-proxima-tarefa-indicada)
- [2. Painel rapido de progresso](#2-painel-rapido-de-progresso)
- [3. Fluxos padroes](#3-fluxos-padroes)
- [4. Fluxos pastorais principais](#4-fluxos-pastorais-principais)
- [5. Webhooks e Hermes](#5-webhooks-e-hermes)
- [6. Testes obrigatorios](#6-testes-obrigatorios)
- [7. Modelo para novo fluxo](#7-modelo-para-novo-fluxo)

---

## 0. Regra principal

Todo bloco precisa terminar em uma destas opcoes:

- [ ] Responder e conectar em `Encerrar Conversa`.
- [ ] Encaminhar para outro fluxo.
- [ ] Abrir atendimento humano.
- [ ] Chamar webhook do Hermes e depois encerrar/encaminhar.
- [ ] Ir para tratamento de inatividade com destino definido.

Referencia: [Guia Mestre - Modelo mental de cada ponta](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#5-modelo-mental-de-cada-ponta)

---

## 1. Proxima tarefa indicada

### Agora

- [ ] Criar etiqueta `Atualização Recusada`.
- [ ] Criar sequencia `SEQ - Recadastro Anual`.
- [ ] Criar sequencia `SEQ - Follow-up Visitante 24h`.
- [ ] Revisar `4- Recadastro Anual` para campanha em ondas com toda a base.
- [ ] Revisar `5- Visitante` para chamar `POST /webhook/botconversa`.
- [ ] Fechar o fluxo `0- Boas Vindas Filadelfia`, especialmente a saida de visitante para `5- Visitante`.

Motivo: a v2 ja tem webhook unico e dashboard operacional; agora o gargalo esta no estado do BotConversa.

### Depois

- [ ] Revisar `1- RUTE SECRETARIA` com as saidas diretas do Assistente GPT.
- [ ] Usar `0000 - Encerrar Conversa` como encerramento oficial.
- [ ] Criar/revisar `Inatividade - Encerrar ou Retomar`.
- [ ] Revisar `13 - Atendimento Humano`.

Referencia: [Guia Mestre - Ordem de implementacao revisada](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#20-ordem-de-implementacao-revisada)

---

## 2. Painel rapido de progresso

### Fase 1 - fechar pontas dos fluxos existentes

- [ ] `0- Boas Vindas Filadelfia`
- [ ] `1- RUTE SECRETARIA` (hoje aparece como `1-  RUTE SECRETARIA`)
- [ ] `0000 - Encerrar Conversa`
- [ ] `Inatividade - Encerrar ou Retomar`
- [ ] `13 - Atendimento Humano`
- [ ] `00 - Midia Recebida - Rute`
- [ ] `000- Pos-atendimento - Feedback`

### Fase 2 - dados essenciais

- [ ] Rodar `python database/migrate_pastoral_system.py`
- [ ] Rodar `python integrations/sync_botconversa_config.py`
- [ ] Conferir IDs em `botconversa_config`
- [ ] Padronizar nomes de campos no BotConversa
- [ ] Padronizar nomes de etiquetas de estado
- [ ] Criar/localizar etiqueta `Atualização Recusada`
- [ ] Criar `SEQ - Recadastro Anual`
- [ ] Criar `SEQ - Follow-up Visitante 24h`
- [ ] Criar `SEQ - Retomar Atualizacao Cadastral`
- [ ] Criar `SEQ - Pedido de Oracao Follow-up`
- [ ] Remover/substituir regra `6M`; usar apenas recadastro anual
- [x] Webhook v2 unico criado: `POST /webhook/botconversa`
- [ ] Padronizar nomes duplicados de fluxos: `0000 - Encerrar Conversa`, `1- RUTE SECRETARIA` e fluxos numerados com `5-`

### Fase 3 - fluxos de maior valor pastoral

- [ ] `Atualizacao Cadastral`
- [ ] `Recadastro Anual`
- [ ] `Visitante / Acompanhamento 24h`
- [ ] `Pedido de Aconselhamento`
- [ ] `Pedido de Oracao`
- [ ] `G12 e Celulas`
- [ ] `Relatorio de Celula`

### Fase 4 - webhooks que faltam

- [x] Usar webhook unico v2 com idempotencia: `/webhook/botconversa`
- [x] Separar por `tipo_evento` no payload: `visitante`, `relatorio_celula`, `pedido_oracao`, `aconselhamento`, `humano_necessario`
- [ ] Conectar `5- Visitante` ao webhook v2
- [ ] Conectar `7- Pedido de Oração` ao webhook v2
- [ ] Conectar `8- Aconselhamento` ao webhook v2
- [ ] Conectar `CALEB CELULAS LIDERANÇA` ao webhook v2
- [ ] Conectar dashboard

### Fase 5 - comunicacao ativa

- [ ] Opt-in de notificacoes de culto
- [ ] Templates/sequencias aprovadas
- [ ] Agenda G12
- [ ] Lembretes de relatorio
- [ ] Resumo de culto com revisao humana antes de disparo

---

## 3. Fluxos padroes

Referencia geral: [Guia Mestre - Matriz de encerramento por fluxo](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#6-matriz-de-encerramento-por-fluxo)

### 3.1 `0- Boas Vindas Filadelfia`

Proxima tarefa indicada:

- [ ] Conectar todas as saidas do menu `Permitir Acompanhamento Visitante`.

Checklist:

- [ ] Entrada do fluxo configurada como `Fluxo de boas vindas`.
- [ ] Primeiro bloco aplica etiqueta `Filadelfia Corrente`.
- [ ] Condicao verifica `Cadastro Completo`.
- [ ] Condicao verifica `Atualizacao Pendente`.
- [ ] Botao `Sou membro` aplica `Membro`, `Cadastro Incompleto`, `Atualizacao Pendente`.
- [ ] Botao `Sou membro` conecta em `Atualizacao Cadastral`.
- [ ] Botao `Sou visitante` aplica `Visitante`.
- [ ] Botao `Sou visitante` salva `Tipo_Vinculo = Visitante`.
- [ ] Botao `Sou visitante` conecta no menu `Permitir Acompanhamento Visitante`.
- [ ] Botao `Quero conhecer` aplica `Visitante`.
- [ ] Botao `Quero conhecer` salva `Tipo_Vinculo = Visitante`.
- [ ] Botao `Quero conhecer` conecta no menu `Permitir Acompanhamento Visitante`.
- [ ] Botao `Outro vinculo` aplica `Outro-Vinculo`.
- [ ] Botao `Outro vinculo` conecta em `1- RUTE SECRETARIA`.
- [ ] Entrada invalida do menu principal tem texto claro.
- [ ] Limite de erro do menu principal conecta em `1- RUTE SECRETARIA`.
- [ ] Inatividade do menu principal conecta em `Encerrar Conversa`.

Menu `Permitir Acompanhamento Visitante`:

- [ ] `Sim, pode` aplica `Consolidacao 24h`.
- [ ] `Sim, pode` salva `Aceita_Acompanhamento = Sim`, se campo existir.
- [ ] `Sim, pode` conecta em `Visitante / Acompanhamento 24h`.
- [ ] `Agora nao` salva `Aceita_Acompanhamento = Nao`, se campo existir.
- [ ] `Agora nao` envia mensagem curta de acolhimento.
- [ ] `Agora nao` conecta em `Encerrar Conversa`.
- [ ] `Quero saber mais` salva `Ultima_Intencao = Visitante`.
- [ ] `Quero saber mais` envia informacoes basicas confirmadas.
- [ ] `Quero saber mais` conecta em `1- RUTE SECRETARIA`.
- [ ] Entrada invalida repete o menu.
- [ ] Limite de erro conecta em `1- RUTE SECRETARIA`.
- [ ] `Se usuario nao responder` envia lembrete curto.
- [ ] `Se usuario nao responder` conecta em `Encerrar Conversa`.

Referencia: [Guia Mestre - Matriz de encerramento por fluxo](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#6-matriz-de-encerramento-por-fluxo)

### 3.2 `1- RUTE SECRETARIA`

Proxima tarefa indicada:

- [ ] Confirmar que todas as saidas diretas do Assistente GPT estao conectadas.

Checklist:

- [ ] Entrada do fluxo configurada como `Fluxo de resposta padrao`.
- [ ] Primeira condicao verifica `Atend Humano Ativo`.
- [ ] Primeira condicao verifica `Humano Necessario`.
- [ ] Se ja tem humano ativo, nao chama IA.
- [ ] Se precisa humano e nao foi atribuido, notifica `Pastor Raniel Levi`.
- [ ] Antes da IA, aplica `IA - Em Atendimento`.
- [ ] Bloco `Assistente GPT` usa `Rute Geral`.
- [ ] Saida `Resposta bem-sucedida` remove `IA - Em Atendimento`.
- [ ] Saida `Resposta bem-sucedida` conecta em `Encerrar Conversa` ou mensagem curta final.
- [ ] Saida `Resposta falha` aplica `Humano Necessario`.
- [ ] Saida `Resposta falha` abre atendimento humano.
- [ ] Saida `Inatividade` remove `IA - Em Atendimento`.
- [ ] Saida `Inatividade` conecta em `Inatividade - Encerrar ou Retomar`.
- [ ] Saida `AtualizaCadastro` remove `IA - Em Atendimento` e conecta em `Atualizacao Cadastral` ou `Recadastro Anual`.
- [ ] Saida `Visitante` remove `IA - Em Atendimento` e conecta em `Visitante / Acompanhamento 24h`.
- [ ] Saida `PedidoOracao` remove `IA - Em Atendimento` e conecta em `Pedido de Oracao`.
- [ ] Saida `Aconselhamento` aplica `Humano Necessario` e conecta em `Pedido de Aconselhamento`.
- [ ] Saida `CelulaG12` conecta em `G12 e Celulas`.
- [ ] Saida `Ministerio` conecta em `Ministerios`.
- [ ] Saida `Evento` conecta em `Eventos e Agenda`.

Referencia: [Guia Mestre - Uso correto de IA](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#9-uso-correto-de-ia)

### 3.3 `Encerrar Conversa`

Proxima tarefa indicada:

- [ ] Criar este fluxo antes de continuar criando pontas de encerramento.

Checklist:

- [ ] Remove `IA - Em Atendimento`.
- [ ] Remove etiquetas temporarias de erro/inatividade, se existirem.
- [ ] Mantem etiquetas permanentes, como `Membro`, `Visitante`, `Cadastro Completo`.
- [ ] Salva `Status_Atendimento_IA = Resolvido` ou `Encerrado`, se campo existir.
- [ ] Envia mensagem curta somente se fizer sentido.
- [ ] Nao chama outro fluxo depois de encerrar.

Referencia: [Guia Mestre - Ponta resolvida](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#a-ponta-resolvida)

### 3.4 `Inatividade - Encerrar ou Retomar`

Proxima tarefa indicada:

- [ ] Criar um fluxo unico para usar nas saidas `Se usuario nao responder`.

Checklist:

- [ ] Envia uma mensagem curta perguntando se a pessoa ainda precisa.
- [ ] Botao `Continuar` volta para o fluxo adequado, quando possivel.
- [ ] Botao `Encerrar` conecta em `Encerrar Conversa`.
- [ ] Sem resposta final conecta em `Encerrar Conversa`.
- [ ] Em cadastro, mantem `Atualizacao Pendente`.
- [ ] Em visitante, mantem `Visitante`.
- [ ] Em humano, nao chama IA.

Referencia: [Guia Mestre - Ponta de inatividade](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#e-ponta-de-inatividade)

### 3.5 `Atendimento Humano`

Proxima tarefa indicada:

- [ ] Padronizar uma acao/bloco para todo caminho humano.

Checklist:

- [ ] Remove `IA - Em Atendimento`.
- [ ] Aplica `Humano Necessario`.
- [ ] Define `Status_Atendimento_IA = Humano`, se campo existir.
- [ ] Atribui atendimento para responsavel correto.
- [ ] Notifica `Pastor Raniel Levi` quando necessario.
- [ ] Envia mensagem clara: `Vou encaminhar voce para uma pessoa da nossa equipe.`
- [ ] Nao deixa a IA responder por cima do humano.

Referencia: [Guia Mestre - Ponta humana](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#d-ponta-humana)

### 3.6 `00 - Midia Recebida - Rute`

Proxima tarefa indicada:

- [ ] Criar tratamento para anexo fora de contexto.

Checklist:

- [ ] Entrada configurada como `Fluxo padrao para midia`.
- [ ] Informa que recebeu anexo.
- [ ] Pede explicacao curta em texto/audio.
- [ ] Botao `Digitar mensagem` conecta em `1- RUTE SECRETARIA`.
- [ ] Botao `Falar com equipe` conecta em `Atendimento Humano`.
- [ ] Inatividade conecta em `Encerrar Conversa`.
- [ ] Nao tenta interpretar documento/imagem sem contexto.

Referencia: [Guia Mestre - Matriz de encerramento por fluxo](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#6-matriz-de-encerramento-por-fluxo)

### 3.7 `000- Pos-atendimento - Feedback`

Proxima tarefa indicada:

- [ ] Criar fluxo de feedback curto.

Checklist:

- [ ] Entrada configurada como `Fluxo Pos-Atendimento`.
- [ ] Pergunta se o atendimento resolveu.
- [ ] Botao `Sim, resolveu` salva feedback positivo e conecta em `Encerrar Conversa`.
- [ ] Botao `Ainda preciso` aplica `Humano Necessario` e abre atendimento humano.
- [ ] Opcional: botao `Enviar feedback` salva texto em campo.
- [ ] Inatividade conecta em `Encerrar Conversa`.

Referencia: [Guia Mestre - Matriz de encerramento por fluxo](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#6-matriz-de-encerramento-por-fluxo)

---

## 4. Fluxos pastorais principais

### 4.1 `Atualizacao Cadastral`

Proxima tarefa indicada:

- [ ] Revisar se o fluxo salva campos antes de chamar webhook.

Checklist:

- [ ] Consentimento inicial.
- [ ] Botao `Sim` inicia coleta.
- [ ] Botao `Agora nao` aplica `Atualizacao Pendente`.
- [ ] Botao `Agora nao` inscreve em retomada.
- [ ] Botao `Agora nao` conecta em `Encerrar Conversa`.
- [ ] Campos obrigatorios salvos.
- [ ] Dados revisados antes do envio.
- [ ] Webhook cadastral chamado.
- [ ] Aplica `Cadastro Completo`.
- [ ] Remove `Cadastro Incompleto`.
- [ ] Programa recadastro anual.
- [ ] Final conecta em `Encerrar Conversa`.

Referencia: [Guia Mestre - Ponta de webhook](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#c-ponta-de-webhook)

### 4.2 `Recadastro Anual`

Proxima tarefa indicada:

- [ ] Definir caminhos `Tudo igual` e `Mudar algo`.

Checklist:

- [ ] Mostra dados atuais resumidos.
- [ ] `Tudo igual` chama webhook de confirmacao.
- [ ] `Tudo igual` atualiza data de recadastro.
- [ ] `Tudo igual` conecta em `Encerrar Conversa`.
- [ ] `Mudar algo` chama Rute Cadastro ou fluxo cadastral.
- [ ] Inatividade mantem pendencia e conecta em retomada/encerrar.

Referencia: [Guia Mestre - Matriz de encerramento por fluxo](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#6-matriz-de-encerramento-por-fluxo)

### 4.3 `Visitante / Acompanhamento 24h`

Proxima tarefa indicada:

- [ ] Garantir que visitante aceito chama webhook e sequencia 24h.

Checklist:

- [ ] Entrada recebe apenas quem aceitou acompanhamento ou veio da Rute com intencao clara.
- [ ] Nao usa a palavra `consolidador` com visitante.
- [ ] Assistente `Caleb Visitantes` conectado.
- [ ] Coleta nome se faltar.
- [ ] Coleta bairro/cidade se faltar.
- [ ] Coleta origem se possivel.
- [ ] Coleta interesse: culto, celula, oracao, aconselhamento.
- [ ] Se aceita acompanhamento, chama `/webhook_visitante` ou registra equivalente.
- [ ] Aplica `Consolidacao 24h`.
- [ ] Inscreve em `SEQ - Follow-up Visitante 24h`.
- [ ] Se pede celula, conecta em `G12 e Celulas`.
- [ ] Se pede oracao, conecta em `Pedido de Oracao`.
- [ ] Se assunto sensivel, conecta em `Atendimento Humano`.
- [ ] Final conecta em `Encerrar Conversa`.

Referencia: [Guia Mestre - Payload Visitante](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#visitante)

### 4.4 `Pedido de Aconselhamento`

Proxima tarefa indicada:

- [ ] Confirmar que sempre termina em humano.

Checklist:

- [ ] Mensagem de privacidade/confidencialidade.
- [ ] Coleta motivo geral, sem detalhes excessivos.
- [ ] Classifica urgencia.
- [ ] Se crise, aplica urgencia `Crise`.
- [ ] Salva resumo.
- [ ] Chama `/webhook_aconselhamento` quando existir.
- [ ] Aplica `Humano Necessario`.
- [ ] Abre atendimento humano.
- [ ] Nao encerra sem humano.

Referencia: [Guia Mestre - Payload Aconselhamento](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#aconselhamento)

### 4.5 `Pedido de Oracao`

Proxima tarefa indicada:

- [ ] Definir se o primeiro MVP salva em campo/log ou webhook dedicado.

Checklist:

- [ ] Pede permissao para registrar.
- [ ] Coleta pedido de forma discreta.
- [ ] Se crise, conecta em `Atendimento Humano`.
- [ ] Se simples, salva pedido/resumo.
- [ ] Chama `/webhook_pedido_oracao` quando existir.
- [ ] Confirma que o pedido foi recebido.
- [ ] Final conecta em `Encerrar Conversa`.

Referencia: [Guia Mestre - Payload Pedido de oracao](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#pedido-de-oracao)

### 4.6 `G12 e Celulas`

Proxima tarefa indicada:

- [ ] Separar interesse em celula de relatorio de celula.

Checklist:

- [ ] Se pessoa quer celula, coleta bairro/disponibilidade.
- [ ] Se e lider enviando relatorio, conecta em `Relatorio de Celula`.
- [ ] Se duvida simples e confirmada, responde e encerra.
- [ ] Se falta dado oficial, humano.
- [ ] Se interesse em celula, webhook `pedido_celula` futuro ou humano.
- [ ] Final conecta em `Encerrar Conversa` ou humano.

Referencia: [Guia Mestre - Webhooks prioritarios](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#16-webhooks-prioritarios)

### 4.7 `Relatorio de Celula`

Proxima tarefa indicada:

- [ ] Criar coleta estruturada para lideres.

Checklist:

- [ ] Confirma nome da celula.
- [ ] Confirma lider.
- [ ] Coleta data.
- [ ] Coleta presenca de membros.
- [ ] Coleta visitantes.
- [ ] Coleta decisoes.
- [ ] Coleta novos nomes.
- [ ] Coleta observacoes.
- [ ] Chama `/webhook_g12_celulas`.
- [ ] Final conecta em `Encerrar Conversa`.
- [ ] Se lider nao envia por 3 semanas, sinaliza pastor.

Referencia: [Guia Mestre - Payload Relatorio de celula](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#relatorio-de-celula)

### 4.8 `Ministerios`

Proxima tarefa indicada:

- [ ] Definir webhook ou notificacao inicial para responsavel.

Checklist:

- [ ] Coleta area de interesse.
- [ ] Coleta disponibilidade.
- [ ] Coleta se ja e membro.
- [ ] Nao aprova entrada em escala automaticamente.
- [ ] Notifica responsavel ou chama webhook futuro.
- [ ] Final conecta em `Encerrar Conversa`.

Referencia: [Guia Mestre - Webhooks prioritarios](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#16-webhooks-prioritarios)

### 4.9 `Eventos e Agenda`

Proxima tarefa indicada:

- [ ] Responder apenas agenda confirmada.

Checklist:

- [ ] Consulta base confirmada.
- [ ] Se evento existe, responde curto.
- [ ] Se nao confirmado, humano ou `1- RUTE SECRETARIA`.
- [ ] Nao inventa data.
- [ ] Final conecta em `Encerrar Conversa`.

Referencia: [Guia Mestre - Assistentes oficiais e limites](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#10-assistentes-oficiais-e-limites)

---

## 5. Webhooks e Hermes

Referencia: [Guia Mestre - BotConversa API e webhooks](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#11-botconversa-api-e-webhooks)

- [ ] `/webhook_atualizacao_cadastral` validado.
- [ ] `/webhook_visitante` definido ou implementado.
- [ ] `/webhook_pedido_oracao` definido ou implementado.
- [ ] `/webhook_aconselhamento` definido ou implementado.
- [ ] `/webhook_g12_celulas` validado.
- [ ] `/webhook_ministerio` definido ou implementado.
- [ ] Todo webhook tem `subscriber_id`.
- [ ] Todo webhook tem `evento`.
- [ ] Todo webhook tem `resumo`.
- [ ] Todo webhook tem idempotencia.
- [ ] Todo webhook registra log.

---

## 6. Testes obrigatorios

Referencia: [Guia Mestre - Testes obrigatorios](./GUIA_MESTRE_CHATBOT_WHATSAPP_BOTCONVERSA_HERMES.md#22-testes-obrigatorios)

- [ ] Novo contato membro.
- [ ] Novo contato visitante que aceita acompanhamento.
- [ ] Visitante que clica `Agora nao`.
- [ ] Visitante que clica `Quero saber mais`.
- [ ] Visitante que fica inativo.
- [ ] Visitante digita opcao invalida 3 vezes.
- [ ] Membro pede atualizacao cadastral.
- [ ] Membro abandona cadastro.
- [ ] Pessoa pede oracao.
- [ ] Pessoa traz assunto de aconselhamento.
- [ ] Lider envia relatorio de celula.
- [ ] Pessoa envia imagem fora de contexto.
- [ ] Conversa humana marcada como concluida.
- [ ] Falha do Assistente GPT.
- [ ] Atendimento humano ativo recebe nova mensagem.

---

## 7. Modelo para novo fluxo

Copie este modelo antes de criar qualquer fluxo novo.

### Nome do fluxo

- [ ] Nome:
- [ ] Objetivo:
- [ ] Entrada:
- [ ] Assistente usado:
- [ ] Campos que salva:
- [ ] Etiquetas que aplica:
- [ ] Webhook chamado:

### Saidas

| Saida | Acao antes de sair | Destino |
|---|---|---|
| sucesso |  |  |
| erro |  |  |
| inatividade |  |  |
| humano |  |  |

### Checklist anti-ponta-solta

- [ ] Todo botao tem destino.
- [ ] Toda condicao tem destino no sim.
- [ ] Toda condicao tem destino no nao.
- [ ] Toda entrada invalida tem destino.
- [ ] Todo limite de erro tem destino.
- [ ] Toda inatividade tem destino.
- [ ] Todo webhook tem destino de sucesso.
- [ ] Todo webhook tem destino de falha.
- [ ] Todo humano remove/desliga IA.
- [ ] Todo encerramento limpa estado temporario.
