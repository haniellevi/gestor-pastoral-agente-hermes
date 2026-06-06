# Passo a Passo dos Fluxos BotConversa - Hermes 2.0

Data: 2026-06-05  
Status: guia operacional da Fase 3

Este documento descreve como montar ou revisar cada fluxo no BotConversa para a arquitetura Hermes 2.0. A regra principal e que todo dado pastoral relevante deve terminar em registro no Hermes via `POST /webhook/botconversa`.

Plano especifico para campanha com toda a base: [Plano de Recadastro Anual - Toda a Base](./PLANO_RECADASTRO_ANUAL_TODA_BASE.md)

---

## 1. Configuracao base

### URLs

| Ambiente | URL |
|---|---|
| Producao | `https://api.filadelfiacorrente.com/webhook/botconversa` |
| Local com porta padrao | `http://localhost:5050/webhook/botconversa` |
| Local usado em teste quando 5050 estiver ocupada | `http://127.0.0.1:5051/webhook/botconversa` |

### Payload padrao do webhook v2

Use bloco de integracao/webhook com metodo `POST`, header `Content-Type: application/json` e corpo:

```json
{
  "event_id": "{{subscriber.id}}-{{flow.id}}-{{date.now}}",
  "subscriber_id": "{{subscriber.id}}",
  "nome": "{{subscriber.name}}",
  "telefone": "{{subscriber.phone}}",
  "mensagem": "{{last_input}}",
  "fluxo_origem": "NOME_DO_FLUXO",
  "tipo_evento": "TIPO_EVENTO",
  "campos": {
    "Resumo_Atend_IA": "{{custom_field.Resumo_Atend_IA}}",
    "Ultima_Intencao": "{{custom_field.Ultima_Intencao}}",
    "Nivel_Urgencia": "{{custom_field.Nivel_Urgencia}}"
  }
}
```

Se o BotConversa nao aceitar alguma variavel exatamente assim, use a variavel equivalente do painel e mantenha os nomes das chaves JSON.

### Tipos de evento aceitos inicialmente

| `tipo_evento` | Responsavel logico | Resultado esperado |
|---|---|---|
| `visitante` | Caleb | Cria inbox, pessoa e tarefa de consolidacao 24h. |
| `relatorio_celula` | Caleb | Cria relatorio se dados estiverem completos; senao cria tarefa de pendencia. |
| `pedido_oracao` | Rute | Cria tarefa pastoral. |
| `aconselhamento` | Rute | Cria tarefa urgente e encaminha para humano. |
| `humano_necessario` | Rute | Cria tarefa urgente. |
| `cadastro` | Rute | Registra entrada de cadastro/recadastro. |
| `celula_g12` | Caleb | Cria tarefa de acompanhamento. |
| `agenda` | Rute | Cria tarefa de agenda. |
| `conteudo` | Barnabe | Cria tarefa de comunicacao. |
| `foco` | Neemias | Cria tarefa privada de foco. |

### Finalizacao obrigatoria

Todo caminho deve terminar em uma destas opcoes:

- conectar em `0000 - Encerrar Conversa`;
- conectar em outro fluxo;
- abrir `13 - Atendimento Humano`;
- chamar webhook v2 e depois encerrar/encaminhar;
- ir para inatividade com destino definido.

---

## 2. Fluxos padrao

### 2.1 `0000 - Encerrar Conversa`

Objetivo: encerrar qualquer ponta resolvida sem deixar estado temporario.

Blocos:

1. **Acao - remover etiquetas temporarias**
   - Remover `Em Atendimento`.
   - Remover `inativo-30min`, se estiver aplicada.
2. **Acao - atualizar campo**
   - `Status_Atendiment_IA = Resolvido`.
3. **Mensagem**
   - Texto: `Fico à disposição. Deus abençoe!`
4. **Finalizar**
   - Nao conectar em outro fluxo.

Nao usar em fluxos novos: `2- Encerrar Conversa`.

### 2.2 `13 - Atendimento Humano`

Objetivo: tirar a IA da conversa e abrir atendimento humano.

Blocos:

1. **Acao - etiquetas**
   - Remover `Em Atendimento`.
   - Aplicar `Humano Necessario`.
   - Aplicar `Atend Humano Ativo`.
2. **Acao - campos**
   - `Status_Atendiment_IA = Humano`.
   - `Precisa_Encaminhar = Sim`.
3. **Mensagem**
   - Texto: `Vou encaminhar você para uma pessoa da nossa equipe.`
4. **Atendimento humano**
   - Abrir conversa humana ou atribuir responsavel.
5. **Webhook v2**
   - `tipo_evento = humano_necessario`.
   - `fluxo_origem = 13 - Atendimento Humano`.
6. **Finalizacao**
   - Nao chamar IA novamente enquanto `Atend Humano Ativo` estiver aplicado.

### 2.3 `Inatividade - Encerrar ou Retomar`

Se esse fluxo ainda nao existir, criar.

Blocos:

1. **Mensagem com botoes**
   - Texto: `Você ainda precisa de ajuda?`
   - Botao `Continuar`
   - Botao `Encerrar`
2. **Botao Continuar**
   - Conectar de volta ao fluxo de origem quando o BotConversa permitir.
   - Se nao souber a origem, conectar em `1- RUTE SECRETARIA`.
3. **Botao Encerrar**
   - Conectar em `0000 - Encerrar Conversa`.
4. **Sem resposta**
   - Aplicar `inativo-30min`.
   - Conectar em `0000 - Encerrar Conversa`.

---

## 3. Fluxos de entrada

### 3.1 `0- Boas Vindas Filadelfia`

Objetivo: identificar vinculo inicial e encaminhar.

Blocos:

1. **Acao inicial**
   - Aplicar `Filadelfia Corrente`.
   - Salvar `Origem_Entrada = Boas Vindas`.
2. **Mensagem de boas-vindas**
   - Texto: `Olá! Seja bem-vindo à Igreja Batista Filadélfia Internacional de Corrente. Como podemos te identificar hoje?`
3. **Menu com botoes**
   - `Sou membro`
   - `Sou visitante`
   - `Quero conhecer`
   - `Outro vínculo`
4. **Caminho Sou membro**
   - Aplicar `Membro`.
   - Salvar `Tipo_Vinculo = Membro`.
   - Se nao tiver `Cadastro Completo`, aplicar `Atualização Pendente` e conectar em `3- Atualização Cadastral`.
   - Se tiver `Cadastro Completo`, conectar em `1- RUTE SECRETARIA`.
5. **Caminho Sou visitante**
   - Aplicar `Visitante`.
   - Salvar `Tipo_Vinculo = Visitante`.
   - Conectar em `5- Visitante`.
6. **Caminho Quero conhecer**
   - Aplicar `Visitante`.
   - Salvar `Tipo_Vinculo = Visitante`.
   - Conectar em `5- Visitante`.
7. **Caminho Outro vínculo**
   - Aplicar `Outro-Vinculo`.
   - Salvar `Tipo_Vinculo = Outro`.
   - Conectar em `1- RUTE SECRETARIA`.
8. **Entrada invalida**
   - Repetir menu uma vez.
   - Na segunda falha, conectar em `1- RUTE SECRETARIA`.
9. **Inatividade**
   - Conectar em `Inatividade - Encerrar ou Retomar`.

### 3.2 `1- RUTE SECRETARIA`

Objetivo: roteador principal de mensagem livre.

Padronizacao: renomear `1-  RUTE SECRETARIA` para `1- RUTE SECRETARIA` quando for seguro.

Blocos:

1. **Condicao: humano ativo**
   - Se tem `Atend Humano Ativo`, nao chamar IA. Enviar mensagem curta ou manter atendimento humano.
2. **Condicao: humano necessario**
   - Se tem `Humano Necessario`, conectar em `13 - Atendimento Humano`.
3. **Acao antes da IA**
   - Aplicar `Em Atendimento`.
   - Salvar `Status_Atendiment_IA = Em Atendimento`.
4. **Assistente GPT: Rute Geral**
   - Deve responder em pt-BR.
   - Deve classificar uma saida: `AtualizaCadastro`, `Visitante`, `PedidoOracao`, `Aconselhamento`, `CelulaG12`, `Ministerio`, `Evento`, `Humano`, `Menu`.
   - Deve salvar resumo em `Resumo_Atend_IA`.
   - Deve salvar intencao em `Ultima_Intencao`.
5. **Saidas**
   - `AtualizaCadastro`: conectar em `3- Atualização Cadastral`.
   - `Visitante`: conectar em `5- Visitante`.
   - `PedidoOracao`: conectar em `7- Pedido de Oração`.
   - `Aconselhamento`: aplicar `Humano Necessario` e conectar em `8- Aconselhamento`.
   - `CelulaG12`: conectar em `9- Central de Células`.
   - `Ministerio`: conectar em `10 - Ministérios`.
   - `Evento`: conectar em `11 - Eventos` ou `12 - Calendário Igreja`.
   - `Humano`: conectar em `13 - Atendimento Humano`.
   - `Menu` ou resposta simples: conectar em `0000 - Encerrar Conversa`.
6. **Falha da IA**
   - Aplicar `Humano Necessario`.
   - Conectar em `13 - Atendimento Humano`.
7. **Inatividade**
   - Remover `Em Atendimento`.
   - Conectar em `Inatividade - Encerrar ou Retomar`.

---

## 4. Fluxos pastorais prioritarios

### 4.1 `5- Visitante`

Objetivo: registrar visitante e abrir consolidacao 24h.

Blocos:

1. **Acao**
   - Aplicar `Visitante`.
   - Aplicar `Consolidacao 24h` se aceitar acompanhamento.
   - Salvar `Tipo_Vinculo = Visitante`.
2. **Perguntas**
   - Nome, se nao vier no contato.
   - Bairro.
   - Como conheceu a igreja.
   - Se aceita contato de acompanhamento.
   - Se tem interesse em celula.
3. **Campos**
   - `Bairro`
   - `Como_Conheceu_Igreja`
   - `Disponibilida_Celula`
   - `Status_Consolidacao = Pendente`
4. **Webhook v2**
   - `tipo_evento = visitante`
   - `fluxo_origem = 5- Visitante`
   - Incluir em `campos`: `Bairro`, `Como_Conheceu_Igreja`, `Disponibilida_Celula`, `Status_Consolidacao`.
5. **Resposta de sucesso**
   - Texto: `Recebemos suas informações. Nossa equipe vai cuidar do acompanhamento.`
6. **Finalizacao**
   - Se aceitou acompanhamento: inscrever em `SEQ - Follow-up Visitante 24h` quando a sequencia existir.
   - Conectar em `0000 - Encerrar Conversa`.
7. **Se nao aceitar acompanhamento**
   - Nao aplicar `Consolidacao 24h`.
   - Chamar webhook v2 mesmo assim com `campos.Aceita_Acompanhamento = Nao`.
   - Conectar em `0000 - Encerrar Conversa`.

### 4.2 `7- Pedido de Oração`

Objetivo: acolher e registrar pedido de oracao.

Blocos:

1. **Acao**
   - Aplicar `Pedido de Oracao`.
2. **Mensagem**
   - Texto: `Pode me enviar seu pedido de oração em poucas palavras?`
3. **Entrada**
   - Salvar em `Resumo_Atend_IA`.
4. **Condicao de crise**
   - Se houver risco, autolesao, abuso, violencia ou urgencia grave: aplicar `Humano Necessario` e conectar em `13 - Atendimento Humano`.
5. **Webhook v2**
   - `tipo_evento = pedido_oracao`
   - `fluxo_origem = 7- Pedido de Oração`
   - `mensagem = pedido recebido`
6. **Mensagem final**
   - Texto: `Recebemos seu pedido de oração. Deus abençoe.`
7. **Finalizacao**
   - Inscrever em `SEQ - Pedido de Oracao Follow-up` quando existir.
   - Conectar em `0000 - Encerrar Conversa`.

### 4.3 `8- Aconselhamento`

Objetivo: registrar triagem minima e levar para humano.

Blocos:

1. **Acao**
   - Aplicar `Pedido Aconselh`.
   - Aplicar `Humano Necessario`.
2. **Mensagem**
   - Texto: `Vou registrar sua solicitação para que uma pessoa responsável acompanhe. Se puder, descreva brevemente o assunto.`
3. **Entrada**
   - Salvar em `Resumo_Aconselhament`.
   - Salvar `Nivel_Urgencia`.
4. **Webhook v2**
   - `tipo_evento = aconselhamento`
   - `fluxo_origem = 8- Aconselhamento`
   - Incluir `Resumo_Aconselhament` e `Nivel_Urgencia`.
5. **Finalizacao**
   - Conectar em `13 - Atendimento Humano`.

### 4.4 `9- Central de Células`

Objetivo: separar interesse em celula de relatorio de lider.

Blocos:

1. **Mensagem com botoes**
   - `Quero participar de uma célula`
   - `Sou líder e vou enviar relatório`
   - `Tenho dúvida sobre G12/células`
2. **Participar de célula**
   - Aplicar `Célula`.
   - Salvar `Ultima_Intencao = InteresseCelula`.
   - Perguntar bairro/disponibilidade.
   - Chamar webhook v2 com `tipo_evento = celula_g12`.
   - Conectar em `0000 - Encerrar Conversa`.
3. **Líder e relatório**
   - Conectar em `CALEB CELULAS LIDERANÇA`.
4. **Dúvida**
   - Conectar em `1- RUTE SECRETARIA` ou assistente Caleb, se configurado.

### 4.5 `CALEB CELULAS LIDERANÇA`

Objetivo: receber relatorio semanal de celula.

Blocos:

1. **Perguntas obrigatorias**
   - Nome da celula.
   - Nome do lider.
   - Data da celula.
   - Presenca de membros.
   - Visitantes.
   - Decisoes de fe.
   - Observacoes.
2. **Campos**
   - `Data_Celula`
   - `Presenca_Membros`
   - `Visitantes_Celula`
   - `Decisoes_Fe`
   - `Novos_Nomes`
   - `Obs_Celula`
   - `Ult_Relatorio_Cel`
3. **Webhook v2**
   - `tipo_evento = relatorio_celula`
   - `fluxo_origem = CALEB CELULAS LIDERANÇA`
   - `campos.nome_celula`
   - `campos.lider_nome`
   - `campos.data_relatorio`
   - `campos.presenca_membros`
   - `campos.visitantes`
   - `campos.decisoes_fe`
   - `campos.rede`
4. **Se faltar dado**
   - O Hermes v2 retorna `dados_faltando`.
   - Enviar mensagem pedindo completar os dados.
5. **Sucesso**
   - Texto: `Relatório recebido. Obrigado por enviar.`
   - Remover `Celula Sem Relatorio`, se existir.
   - Conectar em `0000 - Encerrar Conversa`.

### 4.6 `3- Atualização Cadastral`

Objetivo: atualizar dados de membro.

Blocos:

1. **Acao**
   - Aplicar `Atualização Cadastral`.
   - Aplicar `Atualização Pendente`.
2. **Perguntas**
   - Data de nascimento.
   - Bairro.
   - Tempo de igreja.
   - Lider/celula.
   - Trilha G12.
   - Ministerios.
3. **Assistente GPT: Rute Cadastro**
   - Validar dados.
   - Nao inventar campo ausente.
4. **Webhook v2**
   - `tipo_evento = cadastro`
   - `fluxo_origem = 3- Atualização Cadastral`
   - Enviar campos preenchidos.
5. **Sucesso**
   - Aplicar `Cadastro Completo`.
   - Remover `Cadastro_Incompleto`.
   - Remover `Atualização Pendente`.
   - Salvar `Status_Cadastro = Completo`.
   - Conectar em `0000 - Encerrar Conversa`.
6. **Dados faltando**
   - Aplicar `Cadastro_Incompleto`.
   - Manter `Atualização Pendente`.
   - Inscrever em `SEQ - Retomar Atualizacao Cadastral` quando existir.
7. **Recusou**
   - Aplicar `Atualização Recusada` depois que a etiqueta for criada.
   - Conectar em `0000 - Encerrar Conversa`.

### 4.7 `4- Recadastro Anual`

Objetivo: substituir a antiga revisao 6M.

Blocos:

1. **Entrada por sequencia**
   - `SEQ - Recadastro Anual`.
2. **Mensagem**
   - Texto: `Estamos atualizando os dados cadastrais da igreja. Você pode confirmar ou atualizar suas informações?`
3. **Botoes**
   - `Confirmar sem alteração`
   - `Atualizar dados`
   - `Agora não`
4. **Confirmar sem alteração**
   - Aplicar `Cadastro Confirmado`.
   - Salvar `Ultima_Atualiza_Cad = data atual`.
   - Salvar `Proxima_Atualiza_Cad = data atual + 1 ano`.
   - Chamar webhook v2 com `tipo_evento = cadastro`.
   - Conectar em `0000 - Encerrar Conversa`.
5. **Atualizar dados**
   - Conectar em `3- Atualização Cadastral`.
6. **Agora não**
   - Aplicar `Atualização Pendente`.
   - Inscrever em `SEQ - Retomar Atualizacao Cadastral`.
   - Conectar em `0000 - Encerrar Conversa`.

---

## 5. Fluxos de fase posterior

### `10 - Ministérios`

Usar depois que os fluxos de visitante, oracao, aconselhamento e celulas estiverem validados.

Minimo esperado:

- Aplicar `Ministério`.
- Perguntar area de interesse.
- Salvar `Interesse_Ministerio`.
- Chamar webhook v2 com `tipo_evento = conteudo` ou futuro `ministerio`.
- Encaminhar para humano se envolver escala, conflito ou decisao sensivel.

### `11 - Eventos` e `12 - Calendário Igreja`

Usar apenas com informacao confirmada em conhecimento/base oficial.

Minimo esperado:

- Nunca inventar data ou horario.
- Se nao houver confirmacao, conectar em `13 - Atendimento Humano`.
- Para solicitacao de agenda, chamar webhook v2 com `tipo_evento = agenda`.

---

## 6. Teste obrigatorio por fluxo

Para cada fluxo revisado, executar:

1. Caminho feliz.
2. Entrada invalida.
3. Inatividade.
4. Humano necessario.
5. Webhook com resposta `status = ok`.
6. Duplicidade: reenviar o mesmo payload e confirmar que o Hermes v2 retorna `duplicate = true`.
7. Encerramento: confirmar que termina em `0000 - Encerrar Conversa` ou `13 - Atendimento Humano`.

Payload minimo de teste para visitante:

```json
{
  "event_id": "teste-visitante-001",
  "subscriber_id": "123",
  "nome": "Visitante Teste",
  "telefone": "558999999999",
  "mensagem": "Visitante deseja acompanhamento.",
  "fluxo_origem": "5- Visitante",
  "tipo_evento": "visitante",
  "campos": {
    "Bairro": "Centro",
    "Como_Conheceu_Igreja": "Amigo",
    "Disponibilida_Celula": "Noite"
  }
}
```
