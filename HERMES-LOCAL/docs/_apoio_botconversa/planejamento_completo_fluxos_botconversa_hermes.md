# Planejamento Completo dos Fluxos BotConversa + Hermes

Este documento e o roteiro mestre para criar manualmente os fluxos no BotConversa e depois conectar tudo ao Hermes, SQLite e dashboard pastoral.

## 1. Objetivo

Criar uma arquitetura de atendimento no WhatsApp onde:

- a Rute acolhe e identifica a intencao;
- o BotConversa roteia para o fluxo correto;
- a IA interpreta texto/audio quando isso for melhor que botoes;
- os dados importantes sao salvos em campos personalizados;
- webhooks enviam eventos importantes para o Hermes;
- o Hermes atualiza o SQLite local, sincroniza campos/etiquetas no BotConversa e alimenta o dashboard.

## 2. Estado Atual do Hermes

### Ja existe

Arquivos principais:

- `integrations/botconversa_client.py`
- `integrations/webhook_server.py`
- `integrations/sync_botconversa_config.py`
- `database/migrate_pastoral_system.py`
- `dashboard/app.py`

Capacidades ja implementadas:

- listar contatos, etiquetas, fluxos, sequencias e campos personalizados do BotConversa;
- salvar mapeamentos na tabela `botconversa_config`;
- enviar mensagem;
- enviar fluxo;
- aplicar/remover etiqueta;
- salvar/limpar campo personalizado;
- adicionar/remover de sequencia;
- abrir/fechar conversa humana;
- processar o webhook cadastral em `/webhook_atualizacao_cadastral`;
- registrar logs em `botconversa_sync_log`;
- atualizar tabela `membros`;
- atualizar campos e etiquetas finais no BotConversa apos cadastro.

### Webhook ja existente

Endpoint:

```text
POST /webhook_atualizacao_cadastral
```

Uso:

- atualizacao cadastral completa;
- confirmacao cadastral semestral;
- recadastro anual;
- qualquer fluxo que gere bloco `[ATUALIZACAO_CADASTRAL]`.

### Webhooks que ainda precisam ser criados no Hermes

Ainda nao existem endpoints separados para:

- evento generico de contato/entrada;
- visitante/consolidacao;
- pedido de oracao;
- pedido de aconselhamento;
- interesse em ministerio;
- pedido de celula/G12;
- relatorio de celula;
- evento/inscricao;
- atendimento humano generico.

Eles devem ser implementados depois, seguindo a mesma estrutura do `webhook_atualizacao_cadastral`.

## 3. Padroes Globais

### Linguagem

- Cumprimento oficial: `Graça e Paz!`
- Nao usar `Paz do Senhor` nos fluxos oficiais.
- Mensagens longas devem usar linhas curtas.
- Titulos em WhatsApp devem usar negrito com asteriscos:

```text
*Nascimento:* {Data Nascimento}
*Bairro/cidade:* {Bairro}
```

### Responsabilidade da IA

A IA deve interpretar e classificar. O fluxo visual deve aplicar estado.

Use IA para:

- entender texto/audio livre;
- resumir atendimento;
- identificar intencao;
- extrair campos de uma fala natural;
- perguntar o que faltou.

Use fluxo visual para:

- botoes;
- condicoes;
- aplicar/remover etiquetas;
- salvar campos simples;
- chamar webhooks;
- abrir atendimento humano;
- iniciar outro fluxo;
- inscrever em sequencias.

### Regra anti-deducao

Se a informacao nao estiver em `conhecimento/`, nos documentos da Rute, no Obsidian ou no banco do Hermes, a Rute deve responder:

```text
Graça e Paz! Ainda nao tenho essa informacao confirmada por aqui. Vou encaminhar para a secretaria/lideranca responder com seguranca.
```

## 4. Etiquetas Globais

Crie ou padronize estas etiquetas no BotConversa.

| Etiqueta | Uso |
|---|---|
| `Filadelfia Corrente` | etiqueta geral de todo contato do WhatsApp da igreja |
| `Membro` | pessoa que declara ser membro |
| `Visitante` | visitante/interessado |
| `Outro-Vinculo` | contato que nao e membro nem visitante claro |
| `Cadastro Completo` | dados minimos preenchidos |
| `Cadastro Incompleto` | faltam dados obrigatorios |
| `Atualização Cadastral` | confirmacao do ciclo vigente concluida |
| `Atualização Pendente` | precisa atualizar neste ciclo |
| `Atualização Recusada` | pessoa recusou ou adiou explicitamente |
| `Atualização Confirmada Sem Alteração` | confirmou que nada mudou |
| `Atualização 6M Agendada` | controle de revisao semestral |
| `Recadastro Anual Agendado` | controle de recadastro anual |
| `Consolidação 24h` | visitante precisa de contato rapido |
| `Pedido de Oração` | pedido registrado para intercessao |
| `Pedido de Aconselhamento` | precisa de triagem pastoral |
| `Humano Necessário` | robo deve parar e humano assumir |
| `Em Atendimento Humano` | conversa aberta com atendente |
| `Célula` | interesse/assunto de celula |
| `Ministério` | interesse em servir |
| `G12 Pastoral - Pr. Raniel` | rede do Pr. Raniel |
| `G12 Pastoral - Pastora Vanessa` | rede da Pastora Vanessa |
| `CONVENÇÃO G12 2026` | interesse/inscricao na convencao |
| `Ministério de Louvor` | interesse especifico em louvor |

## 5. Campos Personalizados Globais

| Campo | Tipo recomendado | Uso |
|---|---|---|
| `Data Nascimento` | texto/data | nascimento |
| `Bairro` | texto | bairro/cidade |
| `Tempo_Igreja` | texto | tempo na igreja |
| `Lider_Celula` | texto | lider atual |
| `Celula_Atual` | texto | celula atual |
| `G12_Pastoral` | texto | Pr. Raniel / Pastora Vanessa / outro / nao sei |
| `Fez_Encontro` | texto | Sim / Nao / Quero informacoes |
| `Universidade_Vida` | texto | Sim / Nao / Estou fazendo / Quero informacoes |
| `Capacitacao_Destino` | texto | Sim / Nao / Estou fazendo / Quero informacoes |
| `Ministerios` | texto | ministerios onde ja serve |
| `Interesse_Ministerio` | texto | area onde deseja servir |
| `Feedback_Melhorias` | texto | sugestoes de melhoria |
| `Feedback_falta` | texto | o que sente falta |
| `Data_Conversao` | texto/data | data de conversao, se informada |
| `Ultima_Atualiz_Cadas` | data/texto | ultima atualizacao cadastral |
| `Proxima_Atualizacao_Cadastral` | data/texto | proxima revisao 6M |
| `Proximo_Recadastro_Anual` | data/texto | proximo recadastro anual |
| `Status_Cadastro` | texto | Completo / Incompleto / Atualizar / Recusou |
| `Tipo_Vinculo` | texto | Membro / Visitante / Lider / Outro |
| `Resumo_Atend_IA` | texto | resumo da IA |
| `Ultima_Intencao` | texto | roteamento da Rute geral |
| `Precisa_Encaminhar` ou `Encaminhamento_Necessario` | texto | Sim / Nao |
| `Nivel_Urgencia` | texto | Baixa / Media / Alta / Crise |
| `Pedido_Oracao` | texto | criar se quiser separar pedido de oracao do resumo geral |
| `Resumo_Aconselhamento` | texto | criar para triagem pastoral |
| `Consolidador_Responsavel` | texto | visitante/consolidacao |
| `Status_Consolidacao` | texto | Pendente / Contatado / Integrado / Desistiu |
| `Como_Conheceu_Igreja` | texto | origem do visitante |
| `Disponibilidade_Celula` | texto | melhor dia/horario para celula |

## 6. Sequencias Recomendadas

| Sequencia | Objetivo | Quando inscrever | Quando remover |
|---|---|---|---|
| `SEQ - Retomar Atualizacao Cadastral` | lembrar quem abandonou ou adiou cadastro | quando clicar `Agora nao` ou abandonar fluxo | quando concluir cadastro |
| `SEQ - Revisao Cadastral 6M` | chamar revisao semestral | apos cadastro/confirmacao concluida | ao iniciar nova revisao, se necessario |
| `SEQ - Recadastro Anual` | chamar recadastro anual | apos cadastro completo | ao iniciar recadastro |
| `SEQ - Follow-up Visitante 24h` | garantir consolidacao | visitante registrado | quando status for integrado/desistiu |
| `SEQ - Pedido de Oracao Follow-up` | cuidado apos oracao | pedido registrado sem crise | ao concluir acompanhamento |

## 7. Arquitetura de Roteamento da Rute Geral

Fluxo: `Mensagem Padrão - IA RUTE`

### Configuracao do Assistente GPT

Campos:

- `Salvar resumo da interação em`: `Resumo_Atend_IA`
- `Campos Personalizados`:
  - `Ultima_Intencao`
  - `Precisa_Encaminhar`
  - `Nivel_Urgencia`

### Valores de `Ultima_Intencao`

| Valor | Destino |
|---|---|
| `Atualizacao_Cadastral` | `Fluxo 2A - Confirmacao Cadastral Semestral` ou `Atualização Cadastral` |
| `Visitante` | `VISITANTE` |
| `Pedido_Oracao` | `Pedido de Oração` |
| `Aconselhamento` | `Pedido de Aconselhamento` / atendimento humano |
| `Celula_G12` | `G12 e Células` |
| `Ministerio` | `Ministérios` |
| `Evento` | `Eventos e Agenda` |
| `Humano` | atendimento humano |
| `Interrupcao` | `Interrupcao - Humano / Fora de Escopo` |
| `Inatividade` | `Inatividade - Encerrar ou Retomar` |
| `Outros` | permanecer na Rute geral |

### Bloco apos Assistente GPT

Esse bloco e obrigatorio para roteamento confiavel.

A Rute deve identificar a intencao e salvar campos. Ela nao deve apenas responder "vou te encaminhar", porque isso nao garante que o BotConversa iniciou outro fluxo. O encaminhamento real deve acontecer por uma das tres formas:

1. `Saidas do Assistente GPT`: criar uma saida para cada intencao e conectar cada saida ao fluxo correto.
2. `Campo + Condicao`: salvar `Ultima_Intencao` e, logo depois do Assistente GPT, usar um bloco de condicao para iniciar o fluxo correto.
3. `Webhook/API`: enviar a intencao para o Hermes e o Hermes chama `BotConversaClient.send_flow` quando a decisao depender de dados externos, historico ou regra mais complexa.

Recomendacao para a Filadelfia:

- usar `Saidas do Assistente GPT` quando a plataforma permitir criar saidas nomeadas;
- manter `Ultima_Intencao` salvo como campo de auditoria;
- usar `Webhook/API` apenas nos casos em que o Hermes precisa validar dados antes de disparar outro fluxo.

### Configuracao correta das saidas condicionais

Use nomes curtos, sem acento e sem espaco, porque o BotConversa limita o nome da saida.

Saidas recomendadas:

| Saida | Descricao para colar no BotConversa |
|---|---|
| `AtualizaCadastro` | Use esta saida quando a pessoa pedir para atualizar cadastro, confirmar cadastro, mudar dados pessoais, corrigir bairro, telefone, celula, lider, G12 pastoral ou ministerio. Nao responda que vai encaminhar. Apenas acione esta saida. |
| `PedidoOracao` | Use esta saida quando a pessoa pedir oracao, intercessao, cobertura espiritual ou compartilhar uma causa de oracao. |
| `Aconselhamento` | Use esta saida quando a pessoa pedir conversa pastoral, aconselhamento, ajuda emocional, crise, problema familiar ou assunto sensivel. |
| `CelulaG12` | Use esta saida quando a pessoa perguntar sobre celula, G12, equipe de 12, lider de celula ou quiser participar de uma celula. |
| `Ministerio` | Use esta saida quando a pessoa quiser servir, entrar em ministerio, louvor, midia, recepcao, infantil, intercessao ou outro voluntariado. |
| `Evento` | Use esta saida quando a pessoa perguntar sobre culto, agenda, calendario, evento, inscricao ou programacao. |
| `Humano` | Use esta saida quando a pessoa pedir secretaria, pastor, pastora, humano, atendente, responsavel ou reclamar que a IA nao resolveu. |
| `Interrupcao` | Use esta saida quando a pessoa interromper o fluxo, pedir para parar, demonstrar frustracao, disser que a IA esta repetindo, trouxer assunto sensivel, sair do escopo ou pedir humano/pastor/secretaria de forma urgente. |
| `Inatividade` | Use esta saida quando o contato ficar sem responder pelo tempo configurado no bloco do Assistente GPT. |
| `Menu` | Use esta saida quando a pessoa pedir menu, opcoes, comecar de novo ou quando a intencao estiver confusa. |

Instrucao obrigatoria no prompt/interrupcao do Assistente:

```text
Quando a mensagem do usuario corresponder a uma das saidas condicionais, NAO diga "vou encaminhar", "um momento" ou frases parecidas. Acione diretamente a saida condicional correta. So responda em texto quando a pergunta puder ser resolvida dentro da propria Rute sem iniciar outro fluxo.

Se o usuario disser "quero atualizar meu cadastro", "atualizar cadastro", "mudar meus dados", "confirmar cadastro" ou algo equivalente, acione a saida AtualizaCadastro imediatamente.
```

Teste correto:

1. Usuario: `Quero atualizar meu cadastro`.
2. Esperado: o BotConversa deve iniciar o fluxo `Atualização Cadastral`.
3. Nao esperado: a Rute responder `Vou te encaminhar...` e parar.

Adicionar bloco de condicoes:

1. Se `Ultima_Intencao = Atualizacao_Cadastral`: iniciar fluxo cadastral.
2. Se `Ultima_Intencao = Visitante`: iniciar `VISITANTE`.
3. Se `Ultima_Intencao = Pedido_Oracao`: iniciar `Pedido de Oração`.
4. Se `Ultima_Intencao = Aconselhamento`: aplicar `Humano Necessário`, abrir atendimento e iniciar `Pedido de Aconselhamento`.
5. Se `Ultima_Intencao = Celula_G12`: iniciar `G12 e Células`.
6. Se `Ultima_Intencao = Ministerio`: iniciar `Ministérios`.
7. Se `Ultima_Intencao = Evento`: iniciar `Eventos e Agenda`.
8. Se `Ultima_Intencao = Humano` ou a saida for `Interrupcao`: iniciar `Interrupcao - Humano / Fora de Escopo`.
9. Se a saida for `Inatividade`: iniciar `Inatividade - Encerrar ou Retomar`.
10. Senao: encerrar com `Encerrar Conversa`.

### Regra anti-repeticao

Problema comum: a Rute responde uma informacao, diz que vai encaminhar, mas continua presa no mesmo Assistente GPT. Quando o usuario responde `ok`, `oi`, `sim` ou reclama que esta repetindo, o assistente usa a mesma intencao anterior e repete a resposta.

Para evitar isso, todo atendimento da Rute geral deve ter estado.

Campos recomendados:

- `Ultima_Intencao`: intencao detectada.
- `Status_Atendimento_IA`: `Aberto`, `Encaminhado`, `Resolvido`, `Humano`.
- `Ultimo_Fluxo_Encaminhado`: nome tecnico do fluxo iniciado.
- `Ultima_Resposta_IA`: resumo curto da resposta enviada.

Etiquetas recomendadas:

- `IA - Em Atendimento`
- `IA - Encaminhado`
- `IA - Resolvido`

Regra pratica no BotConversa:

1. Antes do Assistente GPT, verificar se tem `IA - Encaminhado` ou `Status_Atendimento_IA = Encaminhado`.
2. Se tiver, nao chamar a Rute geral de novo.
3. Enviar mensagem curta:

```text
Graça e Paz! Ja encaminhei essa solicitação. Se quiser tratar outro assunto, toque em uma opção abaixo.
```

4. Mostrar botoes:
   - `Atualizar cadastro`
   - `Pedir oração`
   - `Falar com secretaria`
   - `Menu`

5. Quando a Rute encaminhar para um fluxo, aplicar:
   - `IA - Encaminhado`;
   - salvar `Status_Atendimento_IA = Encaminhado`;
   - salvar `Ultimo_Fluxo_Encaminhado`.

6. No fim de cada fluxo específico, remover `IA - Encaminhado` e aplicar `IA - Resolvido`.

Regra para respostas curtas:

- Se a mensagem do usuario for apenas `ok`, `sim`, `ta`, `tá`, `obrigado`, `valeu`, `beleza`, `certo`, nao repetir a resposta completa anterior.
- Responder apenas:

```text
Amem. Permaneço à disposição.
```

ou mostrar o menu, se houver fluxo ativo.

Regra para reclamacao de repeticao:

- Se o usuario disser `voce esta repetindo`, `vc esta repetindo`, `ja falou`, `de novo`, `repetindo`, pedir desculpas de forma curta, limpar a intencao e oferecer menu.

```text
Desculpe, vou corrigir isso. Sobre qual assunto voce quer falar agora?
```

Em seguida:

- limpar `Ultima_Intencao`;
- salvar `Status_Atendimento_IA = Aberto`;
- remover `IA - Encaminhado`;
- enviar para `Menu`.

## 8. Fluxo 1 - Boas Vindas Filadelfia

### Objetivo

Receber todo novo contato, aplicar etiqueta geral e decidir se vai para cadastro, visitante ou Rute geral.

### Gatilho

- Fluxo inicial do WhatsApp.
- Palavra-chave como `oi`, `olá`, `menu`, `começar`.

### Mensagem inicial

```text
Graça e Paz! Eu sou a Rute, secretaria virtual da Igreja Batista Filadelfia Internacional de Corrente.

Como posso te ajudar hoje?
```

### Acoes iniciais

- Aplicar `Filadelfia Corrente`.
- Se ainda nao tem tipo de vinculo, perguntar.

### Logica por etiquetas

1. Tem `Cadastro Completo` e tem `Atualização Cadastral`:
   - enviar para `Mensagem Padrão - IA RUTE`.

2. Tem `Cadastro Completo`, mas nao tem `Atualização Cadastral`:
   - enviar para `Fluxo 2A - Confirmacao Cadastral Semestral`.

3. Nao tem `Cadastro Completo`:
   - perguntar vinculo:
     - `Sou membro`
     - `Sou visitante`
     - `Quero conhecer`
     - `Outro vínculo`

### Acoes por resposta

| Resposta | Acoes |
|---|---|
| `Sou membro` | aplicar `Membro`, `Cadastro Incompleto`, `Atualização Pendente`; iniciar `Atualização Cadastral` |
| `Sou visitante` | aplicar `Visitante`, `Consolidação 24h`; iniciar `VISITANTE` |
| `Quero conhecer` | aplicar `Visitante`; enviar endereco/cultos; oferecer consolidacao |
| `Outro vínculo` | aplicar `Outro-Vinculo`; enviar para Rute geral ou humano |

### Webhook

Nao obrigatorio no primeiro momento.

Recomendado no futuro:

```text
POST /webhook_evento_contato
```

Finalidade:

- registrar primeira interacao;
- criar ou atualizar membro/contato local;
- alimentar metricas de entrada.

### Atualizacao Hermes

Futuro:

- criar endpoint generico de contato;
- criar tabela `botconversa_eventos` ou usar `botconversa_sync_log`;
- opcionalmente atualizar `membros.tipo_vinculo`.

## 9. Fluxo 2 - Atualizacao Cadastral Completa

### Objetivo

Coletar cadastro completo de membro.

### Entrada

- membro sem `Cadastro Completo`;
- membro com `Cadastro Incompleto`;
- pessoa que clicou `Sou membro` no fluxo inicial.

### Campos obrigatorios minimos para o Hermes considerar completo

O webhook atual considera estes campos como obrigatorios:

- nome;
- telefone;
- bairro/cidade;
- tempo de igreja;
- lider de celula;
- celula atual;
- G12 pastoral;
- fez Encontro;
- Universidade da Vida;
- Capacitacao Destino.

### Ordem sugerida

1. Consentimento.
2. Nome completo.
3. Data de nascimento.
4. Bairro/cidade.
5. Tempo de igreja.
6. Lider de celula.
7. Celula atual.
8. G12 pastoral.
9. Encontro com Deus.
10. Universidade da Vida.
11. Capacitacao Destino.
12. Ministerios/interesse.
13. Feedback.
14. Confirmacao final.
15. Webhook Hermes.

### Mensagem inicial

```text
Graça e Paz! Vamos atualizar seus dados para melhorar nossa comunicacao e cuidado pastoral.

Leva poucos minutos. Podemos comecar?
```

Botoes:

- `Sim, vamos la`
- `Agora nao`
- `Falar com secretaria`

### Acoes finais

- Aplicar `Cadastro Completo`.
- Aplicar `Atualização Cadastral`.
- Remover `Cadastro Incompleto`.
- Remover `Atualização Pendente`.
- Remover `Atualização Recusada`.
- Definir `Status_Cadastro = Completo`.
- Definir `Ultima_Atualiz_Cadas = data atual`.
- Inscrever em `SEQ - Revisao Cadastral 6M`.
- Inscrever em `SEQ - Recadastro Anual`.
- Chamar webhook cadastral.

### Webhook

Usar endpoint ja existente:

```text
POST {NGROK_URL}/webhook_atualizacao_cadastral
```

Payload recomendado:

```json
{
  "evento": "cadastro_completo",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "data_nascimento": "{{Data Nascimento}}",
  "bairro": "{{Bairro}}",
  "tempo_igreja": "{{Tempo_Igreja}}",
  "lider_celula": "{{Lider_Celula}}",
  "celula_atual": "{{Celula_Atual}}",
  "g12_pastoral": "{{G12_Pastoral}}",
  "fez_encontro": "{{Fez_Encontro}}",
  "universidade_vida": "{{Universidade_Vida}}",
  "capacitacao_destino": "{{Capacitacao_Destino}}",
  "ministerios": "{{Ministerios}}",
  "interesse_ministerio": "{{Interesse_Ministerio}}",
  "feedback_melhorias": "{{Feedback_Melhorias}}",
  "feedback_falta": "{{Feedback_falta}}",
  "resumo_ia": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes

Ja suportado parcialmente pelo `webhook_server.py`.

Conferir:

- `botconversa_config` precisa ter IDs de campos e etiquetas preenchidos;
- rodar `python database/migrate_pastoral_system.py`;
- rodar `python integrations/sync_botconversa_config.py`;
- manter `integrations/webhook_server.py` rodando;
- expor com ngrok ou outro tunel.

## 10. Fluxo 2A - Confirmacao Cadastral Semestral

### Objetivo

Perguntar se os dados continuam iguais e permitir atualizacao por texto/audio.

### Entrada

- contato tem `Cadastro Completo`;
- contato nao tem `Atualização Cadastral` do ciclo atual;
- ou contato tem `Atualização Pendente`.

### Mensagem inicial

```text
Graça e Paz, {primeiro-nome}! Para mantermos seu cadastro em dia, confira os dados que temos:

*Nascimento:* {Data Nascimento}
*Bairro/cidade:* {Bairro}
*Tempo de igreja:* {Tempo_Igreja}
*Líder de célula:* {Lider_Celula}
*Célula atual:* {Celula_Atual}
*G12 pastoral:* {G12_Pastoral}
*Encontro:* {Fez_Encontro}
*Universidade da Vida:* {Universidade_Vida}
*Capacitação Destino:* {Capacitacao_Destino}
*Ministérios:* {Ministerios}

Se estiver tudo igual, toque em *Tudo igual*. Se mudou algo, toque em *Atualizar algo* ou envie em texto/audio o que precisa atualizar.
```

### Botoes

- `Tudo igual`
- `Atualizar algo`
- `Prefiro falar com a secretaria`

### Ramo Tudo igual

Acoes:

- aplicar `Atualização Cadastral`;
- aplicar `Atualização Confirmada Sem Alteração`;
- remover `Atualização Pendente`;
- remover `Atualização Recusada`;
- definir `Status_Cadastro = Completo`;
- definir `Ultima_Atualiz_Cadas = data atual`;
- inscrever em `SEQ - Revisao Cadastral 6M`;
- inscrever em `SEQ - Recadastro Anual`;
- chamar webhook cadastral com `status=sem_alteracao`.

Payload:

```json
{
  "evento": "confirmacao_cadastral_sem_alteracao",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "resumo_ia": "[ATUALIZACAO_CADASTRAL]\nstatus=sem_alteracao\nresumo=Contato confirmou que os dados continuam iguais.\n[/ATUALIZACAO_CADASTRAL]"
}
```

### Ramo Atualizar algo

Ativar Assistente GPT `Rute Cadastro`.

Configuracao:

- `Salvar resumo da interação em`: `Resumo_Atend_IA`;
- `Campos Personalizados`: campos cadastrais especificos, nunca `Resumo_Atend_IA`.

O assistente deve gerar:

```text
[ATUALIZACAO_CADASTRAL]
status=atualizado
Bairro=
Tempo_Igreja=
Lider_Celula=
Celula_Atual=
G12_Pastoral=
Fez_Encontro=
Universidade_Vida=
Capacitacao_Destino=
Ministerios=
Interesse_Ministerio=
Feedback_Melhorias=
Feedback_falta=
campos_faltando=
resumo=
[/ATUALIZACAO_CADASTRAL]
```

Depois:

- chamar `/webhook_atualizacao_cadastral`;
- o Hermes extrai o bloco e atualiza SQLite/BotConversa.

### Ramo Secretaria

Acoes:

- aplicar `Humano Necessário`;
- manter `Atualização Pendente`;
- abrir atendimento humano;
- se chamar webhook, usar `status=humano`.

Payload:

```json
{
  "evento": "atualizacao_cadastral_humano",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "resumo_ia": "[ATUALIZACAO_CADASTRAL]\nstatus=humano\nresumo=Contato pediu atendimento humano para atualizacao cadastral.\n[/ATUALIZACAO_CADASTRAL]"
}
```

### Webhook

Ja suportado:

```text
POST /webhook_atualizacao_cadastral
```

## 11. Fluxo 2B - Recadastro Anual

### Objetivo

Revisao completa anual.

### Entrada

- `Ultima_Atualiz_Cadas` superior a 365 dias;
- sequencia `SEQ - Recadastro Anual`;
- rotina Hermes mensal detectou vencimento.

### Estrutura

1. Explicar que e recadastro anual.
2. Mostrar dados atuais.
3. Perguntar se deseja confirmar por partes ou atualizar tudo.
4. Reaproveitar blocos do fluxo completo.
5. Chamar webhook cadastral.

### Webhook

Usar:

```text
POST /webhook_atualizacao_cadastral
```

Payload com:

```json
{
  "evento": "recadastro_anual",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "resumo_ia": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes

Ja pode usar endpoint existente se gerar bloco `[ATUALIZACAO_CADASTRAL]`.

Futuro:

- criar rotina `jobs/verificar_recadastros.py`;
- buscar contatos com `ultima_atualizacao_cadastral` vencida;
- aplicar/remover etiquetas;
- disparar fluxo via `BotConversaClient.send_flow`.

## 12. Fluxo 3 - VISITANTE / Consolidacao 24h

### Objetivo

Receber visitante e garantir contato de consolidacao em ate 24h.

### Entrada

- resposta `Sou visitante`;
- `Quero conhecer`;
- intencao `Visitante` na Rute geral.

### Campos

- nome;
- telefone;
- bairro/cidade;
- como conheceu a igreja;
- deseja contato da lideranca;
- melhor horario;
- interesse em celula.

### Mensagem inicial

```text
Graça e Paz! Ficamos felizes com seu contato.

Queremos cuidar bem de voce e te conhecer melhor.
```

### Acoes finais

- aplicar `Visitante`;
- aplicar `Consolidação 24h`;
- definir `Tipo_Vinculo = Visitante`;
- definir `Ultima_Intencao = Visitante`;
- inscrever em `SEQ - Follow-up Visitante 24h`;
- notificar/encaminhar para Luciane ou equipe de consolidacao.

### Webhook

Recomendado criar novo endpoint:

```text
POST /webhook_visitante
```

Payload:

```json
{
  "evento": "visitante_registrado",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "bairro": "{{Bairro}}",
  "como_conheceu": "{{Como_Conheceu_Igreja}}",
  "deseja_contato": "{{Deseja_Contato_Lideranca}}",
  "interesse_celula": "{{Interesse_Celula}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes necessaria

Implementar:

- endpoint `/webhook_visitante`;
- funcao `processar_visitante(payload)`;
- inserir/atualizar tabela `consolidacao_visitantes`;
- criar membro/contato local se necessario;
- registrar em `botconversa_sync_log`;
- aplicar etiquetas via API;
- opcionalmente abrir atendimento humano ou enviar fluxo de follow-up.

Tabela atual existente:

```text
consolidacao_visitantes
```

Colunas atuais:

- `data_visita`
- `visitante_nome`
- `visitante_whatsapp`
- `consolidador_nome`
- `contato_24h`
- `data_contato`
- `feedback`
- `status`

Possivel melhoria futura:

- adicionar `bairro`;
- adicionar `como_conheceu`;
- adicionar `subscriber_id`;
- adicionar `interesse_celula`.

## 13. Fluxo 4 - Pedido de Oracao

### Objetivo

Registrar pedido e encaminhar para intercessao.

### Entrada

- pessoa pede oracao;
- intencao `Pedido_Oracao`;
- botao no menu.

### Campos

- `Pedido_Oracao`;
- `Resumo_Atend_IA`;
- `Nivel_Urgencia`;

### Mensagem inicial

```text
Graça e Paz! Posso registrar seu pedido para a equipe de intercessao?
```

Botoes:

- `Sim, pode registrar`
- `Prefiro falar com alguem`
- `Cancelar`

### Regras

- Se for pedido simples: registrar e encaminhar intercessao.
- Se houver crise/risco: aplicar `Humano Necessário`, `Nivel_Urgencia = Crise` e abrir atendimento humano.
- A IA nao deve fazer aconselhamento profundo.

### Webhook

Recomendado criar:

```text
POST /webhook_pedido_oracao
```

Payload:

```json
{
  "evento": "pedido_oracao",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "pedido_oracao": "{{Pedido_Oracao}}",
  "nivel_urgencia": "{{Nivel_Urgencia}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes necessaria

Criar tabela nova:

```sql
CREATE TABLE IF NOT EXISTS pedidos_oracao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_pedido TEXT DEFAULT CURRENT_TIMESTAMP,
    nome TEXT,
    telefone TEXT,
    botconversa_subscriber_id INTEGER,
    pedido TEXT NOT NULL,
    nivel_urgencia TEXT DEFAULT 'Baixa',
    status TEXT DEFAULT 'Recebido',
    encaminhado_para TEXT,
    feedback TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Criar endpoint e registrar log.

## 14. Fluxo 5 - Pedido de Aconselhamento

### Objetivo

Triar com seguranca e abrir atendimento humano.

### Entrada

- intencao `Aconselhamento`;
- pedido para falar com pastor/pastora;
- tema sensivel.

### Mensagem inicial

```text
Entendo. Esse assunto merece cuidado e privacidade.

Vou encaminhar sua mensagem para a secretaria/lideranca responsavel te orientar da melhor forma.
```

### Campos

- nome;
- telefone;
- melhor horario;
- resumo curto;
- `Nivel_Urgencia`;
- `Resumo_Aconselhamento`;

### Acoes

- aplicar `Pedido de Aconselhamento`;
- aplicar `Humano Necessário`;
- abrir atendimento humano;
- se urgente, `Nivel_Urgencia = Alta` ou `Crise`;
- nao prometer horario;
- nao deixar robo continuar respondendo.

### Webhook

Recomendado criar:

```text
POST /webhook_aconselhamento
```

Payload:

```json
{
  "evento": "pedido_aconselhamento",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "melhor_horario": "{{Melhor_Horario}}",
  "nivel_urgencia": "{{Nivel_Urgencia}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes necessaria

Opcoes:

1. Criar tabela propria `pedidos_aconselhamento`.
2. Ou criar compromisso em `compromissos` somente depois da secretaria confirmar.

Tabela recomendada:

```sql
CREATE TABLE IF NOT EXISTS pedidos_aconselhamento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_pedido TEXT DEFAULT CURRENT_TIMESTAMP,
    nome TEXT,
    telefone TEXT,
    botconversa_subscriber_id INTEGER,
    resumo TEXT,
    nivel_urgencia TEXT DEFAULT 'Media',
    melhor_horario TEXT,
    status TEXT DEFAULT 'Pendente',
    responsavel TEXT,
    compromisso_id INTEGER,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Dashboard:

- mostrar pedidos pendentes;
- destacar urgencias altas/crise;
- permitir marcar como agendado/concluido futuramente.

## 15. Fluxo 6 - G12 e Celulas

### Objetivo

Orientar sobre celulas/G12 e coletar pedidos de participacao ou relatorios.

### Entrada

- intencao `Celula_G12`;
- palavra-chave celula, G12, lider, encontro, UV, CD;
- visitante quer celula;
- lider envia relatorio.

### Menu

- `Quero participar de uma celula`
- `Ja sou lider`
- `Tenho duvida sobre G12`
- `Relatorio de celula`
- `Falar com lideranca`

### Ramo participar de celula

Campos:

- `Bairro`;
- `Disponibilidade_Celula`;
- `Tipo_Vinculo`;
- `Resumo_Atend_IA`.

Acoes:

- aplicar `Célula`;
- se visitante, aplicar `Consolidação 24h`;
- encaminhar para Caleb/central de celulas.

### Ramo relatorio de celula

Coletar:

- nome da celula;
- lider;
- presenca de membros;
- visitantes;
- decisoes;
- rede.

### Webhook

Criar dois endpoints ou um endpoint com `evento`.

Recomendado:

```text
POST /webhook_g12_celulas
```

Payload para pedido de celula:

```json
{
  "evento": "pedido_celula",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "bairro": "{{Bairro}}",
  "disponibilidade": "{{Disponibilidade_Celula}}",
  "tipo_vinculo": "{{Tipo_Vinculo}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

Payload para relatorio:

```json
{
  "evento": "relatorio_celula",
  "subscriber_id": "{{subscriber_id}}",
  "lider_nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "nome_celula": "{{Nome_Celula}}",
  "presenca_membros": "{{Presenca_Membros}}",
  "visitantes": "{{Visitantes}}",
  "decisoes_fe": "{{Decisoes_Fe}}",
  "rede": "{{Rede}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes necessaria

Para relatorios:

- inserir em `relatorios_celulas`.

Para pedido de celula:

- criar tabela `pedidos_celula` ou registrar em `botconversa_sync_log`;
- opcionalmente criar visitante/consolidacao.

Tabela recomendada:

```sql
CREATE TABLE IF NOT EXISTS pedidos_celula (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_pedido TEXT DEFAULT CURRENT_TIMESTAMP,
    nome TEXT,
    telefone TEXT,
    botconversa_subscriber_id INTEGER,
    bairro TEXT,
    disponibilidade TEXT,
    tipo_vinculo TEXT,
    status TEXT DEFAULT 'Pendente',
    encaminhado_para TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 16. Fluxo 7 - Ministerios e Voluntariado

### Objetivo

Registrar desejo de servir e encaminhar ao responsavel.

### Entrada

- intencao `Ministerio`;
- pessoa fala que quer servir;
- menu de ministerios.

### Perguntas

1. Voce ja e membro?
2. Em qual area gostaria de servir?
3. Voce ja serve em algum ministerio?

### Opcoes de ministerio

- Louvor
- Artes/danca
- Obreiros
- Jovens
- Kids
- Consolidacao
- Tecnologia
- Cafe Filadelfia
- Secretaria
- Outro

### Campos

- `Tipo_Vinculo`;
- `Interesse_Ministerio`;
- `Ministerios`;
- `Resumo_Atend_IA`.

### Acoes

- aplicar `Ministério`;
- se Louvor, aplicar `Ministério de Louvor`;
- notificar responsavel;
- se ainda nao e membro, encaminhar antes para cadastro/visitante.

### Webhook

Recomendado criar:

```text
POST /webhook_ministerio
```

Payload:

```json
{
  "evento": "interesse_ministerio",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "tipo_vinculo": "{{Tipo_Vinculo}}",
  "interesse_ministerio": "{{Interesse_Ministerio}}",
  "ministerios": "{{Ministerios}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes necessaria

Criar tabela:

```sql
CREATE TABLE IF NOT EXISTS interesses_ministerio (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_interesse TEXT DEFAULT CURRENT_TIMESTAMP,
    nome TEXT,
    telefone TEXT,
    botconversa_subscriber_id INTEGER,
    tipo_vinculo TEXT,
    area_interesse TEXT NOT NULL,
    ministerios_atuais TEXT,
    status TEXT DEFAULT 'Pendente',
    responsavel TEXT,
    feedback TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP,
    atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
```

Dashboard:

- listar interesses pendentes por ministerio;
- mostrar responsavel sugerido.

## 17. Fluxo 8 - Eventos e Agenda

### Objetivo

Responder sobre eventos confirmados e encaminhar datas incertas.

### Entrada

- pergunta sobre culto, campanha, convencao, rede, encontro, UV, CD.

### Regras

- Se esta em `calendario_2026`: responder.
- Se nao esta confirmado: encaminhar secretaria.
- Para evento com inscricao, criar fluxo especifico.

### Evento especial ja conhecido

`CONVENÇÃO G12 2026`

- Data registrada: 26/07/2026 a 01/08/2026.
- Local: Teresina.
- Usar etiqueta `CONVENÇÃO G12 2026`.

### Webhook

Opcional:

```text
POST /webhook_evento
```

Payload:

```json
{
  "evento": "interesse_evento",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "evento_nome": "{{Evento_Nome}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes necessaria

Criar tabela futura:

```sql
CREATE TABLE IF NOT EXISTS interesses_eventos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_interesse TEXT DEFAULT CURRENT_TIMESTAMP,
    nome TEXT,
    telefone TEXT,
    botconversa_subscriber_id INTEGER,
    evento_nome TEXT,
    status TEXT DEFAULT 'Interessado',
    observacoes TEXT,
    criado_em TEXT DEFAULT CURRENT_TIMESTAMP
);
```

## 18. Fluxo 9 - Atendimento Humano / Secretaria

### Objetivo

Parar o robo e abrir conversa para humano.

### Entradas

- pessoa pede humano;
- assunto sensivel;
- IA identifica interrupcao;
- erro do assistente;
- pedido de pastor/pastora/secretaria.

### Acoes

- aplicar `Humano Necessário`;
- aplicar `Em Atendimento Humano`;
- salvar `Resumo_Atend_IA`;
- abrir conversa humana;
- notificar responsavel.

### Webhook

Opcional:

```text
POST /webhook_atendimento_humano
```

Payload:

```json
{
  "evento": "atendimento_humano",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "nivel_urgencia": "{{Nivel_Urgencia}}",
  "ultima_intencao": "{{Ultima_Intencao}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes necessaria

Pode usar `botconversa_sync_log` inicialmente.

Futuro:

- tabela `atendimentos_humanos`;
- dashboard de fila de atendimento.

## 19. Fluxo 10 - Interrupcao - Humano / Fora de Escopo

### Objetivo

Parar o atendimento automatico quando a pessoa pedir humano, pastor, secretaria, demonstrar frustracao, trouxer assunto sensivel ou sair do escopo da Rute.

Este fluxo existe para proteger a pessoa, a igreja e a qualidade do atendimento. Ele deve ser prioridade sobre qualquer resposta longa da IA.

### Entradas

- Saida condicional `Interrupcao` no Assistente GPT.
- Saida condicional `Humano`.
- Pessoa digitou termos como:
  - `quero falar com humano`;
  - `quero falar com pastor`;
  - `quero falar com secretaria`;
  - `você está repetindo`;
  - `não resolveu`;
  - `isso não ajudou`;
  - `assunto urgente`;
  - `preciso de ajuda`;
  - `não quero falar com robô`.
- Pedido de aconselhamento sensivel.
- Assunto fora do escopo da igreja ou da base de conhecimento.
- Frustracao detectada pela IA.

### Mensagem principal

```text
Graça e Paz! Entendi.

Vou encaminhar sua conversa para uma pessoa da nossa equipe te atender com mais cuidado.
```

### Mensagem para frustracao/repeticao

```text
Graça e Paz! Desculpe pela repetição.

Vou encaminhar sua conversa para atendimento humano para cuidarmos melhor disso.
```

### Mensagem para assunto sensivel

```text
Graça e Paz! Entendi que esse assunto precisa de cuidado especial.

Vou encaminhar para uma pessoa responsável da equipe.
```

### Acoes no BotConversa

1. Aplicar etiqueta `Humano Necessário`.
2. Aplicar etiqueta `Em Atendimento Humano`.
3. Remover etiqueta `IA - Em Atendimento`.
4. Remover etiqueta `IA - Encaminhado`.
5. Salvar `Status_Atendimento_IA = Humano`.
6. Salvar `Nivel_Urgencia`:
   - `Normal` para secretaria comum;
   - `Alta` para pastor/pastora, aconselhamento ou assunto sensivel;
   - `Crise` se houver risco, desespero intenso, ameaça, violência ou emergência.
7. Salvar `Ultima_Intencao = Humano` ou `Interrupcao`.
8. Salvar `Resumo_Atend_IA` com uma frase objetiva.
9. Abrir atendimento humano no BotConversa.
10. Notificar secretaria/responsavel, se houver recurso no plano.

### Quando usar webhook

Usar webhook se quiser registrar a fila no Hermes, mostrar no dashboard ou criar historico de interrupcoes.

```text
POST /webhook_atendimento_humano
```

Payload:

```json
{
  "evento": "interrupcao_humano",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "nivel_urgencia": "{{Nivel_Urgencia}}",
  "ultima_intencao": "{{Ultima_Intencao}}",
  "motivo": "{{Motivo_Interrupcao}}",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes

Inicialmente pode registrar em `botconversa_sync_log`.

Futuro:

- tabela `atendimentos_humanos`;
- campo `motivo_interrupcao`;
- dashboard com fila: nome, telefone, urgencia, motivo e horario.

## 20. Fluxo 11 - Inatividade - Encerrar ou Retomar

### Objetivo

Tratar contatos que entraram em um atendimento da Rute ou fluxo cadastral e ficaram sem responder.

O objetivo nao e ficar insistindo. E encerrar com cuidado, manter etiquetas corretas e permitir retomada depois.

### Entrada

- Saida condicional `Inatividade` do Assistente GPT.
- Bloco de inatividade do BotConversa, por exemplo:
  - 10 minutos para atendimento geral;
  - 30 minutos para cadastro;
  - 24 horas para cadastro pendente, se a pessoa abandonou.

### Mensagem curta de 10 a 30 minutos

```text
Graça e Paz! Como não tivemos resposta agora, vou pausar este atendimento.

Quando quiser continuar, é só me chamar por aqui.
```

### Mensagem para cadastro pendente

```text
Graça e Paz! Percebi que não conseguimos concluir sua atualização cadastral agora.

Quando puder continuar, toque em uma opção abaixo.
```

Botoes:

- `Continuar cadastro`
- `Falar com secretaria`
- `Menu`

### Acoes no BotConversa

1. Remover `IA - Em Atendimento`.
2. Remover `IA - Encaminhado`, se nao houver fluxo ativo real.
3. Aplicar `IA - Inativo`.
4. Salvar `Status_Atendimento_IA = Inativo`.
5. Manter `Ultima_Intencao`, para auditoria.
6. Se estava em cadastro:
   - manter `Atualização Pendente`;
   - manter `Cadastro Incompleto`, se ainda nao concluiu;
   - adicionar em `SEQ - Retomar Atualizacao Cadastral`.
7. Se era atendimento comum:
   - enviar para `Encerrar Conversa`.

### Quando usar webhook

Webhook nao e obrigatorio no primeiro momento.

Usar webhook se o Hermes precisar medir abandono ou disparar follow-up confiavel.

```text
POST /webhook_evento_contato
```

Payload:

```json
{
  "evento": "inatividade",
  "subscriber_id": "{{subscriber_id}}",
  "nome": "{{nome}}",
  "telefone": "{{telefone}}",
  "ultima_intencao": "{{Ultima_Intencao}}",
  "status_atendimento": "Inativo",
  "resumo": "{{Resumo_Atend_IA}}"
}
```

### Atualizacao Hermes

Inicialmente pode ficar apenas no BotConversa.

Futuro:

- registrar abandono em `botconversa_eventos`;
- medir conversao por fluxo;
- criar rotina de retomada pelo Hermes quando o contato ficar pendente por 1, 3 ou 7 dias.

## 21. Fluxo 12 - Encerrar Conversa

### Objetivo

Encerrar com gentileza.

Mensagem:

```text
Fico a disposicao. Deus abencoe!
```

### Acoes opcionais

- limpar `Precisa_Encaminhar`;
- manter `Ultima_Intencao`;
- salvar resumo se o atendimento foi por IA.

### Webhook

Nao obrigatorio.

## 22. Matriz de Webhooks

| Fluxo | Webhook | Existe hoje? | Prioridade | Atualiza |
|---|---|---:|---:|---|
| Atualizacao Cadastral Completa | `/webhook_atualizacao_cadastral` | Sim | Alta | `membros`, BotConversa campos/tags/sequencias |
| Confirmacao Cadastral 6M | `/webhook_atualizacao_cadastral` | Sim | Alta | `membros`, BotConversa campos/tags/sequencias |
| Recadastro Anual | `/webhook_atualizacao_cadastral` | Sim | Alta | `membros`, BotConversa campos/tags/sequencias |
| Boas Vindas / Entrada | `/webhook_evento_contato` | Nao | Baixa | `botconversa_sync_log` ou `botconversa_eventos` |
| Visitante | `/webhook_visitante` | Nao | Alta | `consolidacao_visitantes`, tags, sequencia 24h |
| Pedido de Oracao | `/webhook_pedido_oracao` | Nao | Media | `pedidos_oracao`, tags, follow-up |
| Aconselhamento | `/webhook_aconselhamento` | Nao | Alta | `pedidos_aconselhamento`, atendimento humano |
| G12 e Celulas | `/webhook_g12_celulas` | Nao | Media | `relatorios_celulas`, `pedidos_celula` |
| Ministerios | `/webhook_ministerio` | Nao | Media | `interesses_ministerio`, tags |
| Eventos | `/webhook_evento` | Nao | Baixa/Media | `interesses_eventos`, tags |
| Atendimento Humano | `/webhook_atendimento_humano` | Nao | Media | `botconversa_sync_log` / fila humana |
| Interrupcao | `/webhook_atendimento_humano` | Nao | Alta | `botconversa_sync_log`, futura fila humana |
| Inatividade | `/webhook_evento_contato` | Nao | Baixa | abandono, retomada, sequencias |

## 23. Ordem de Criacao Manual no BotConversa

### Fase 1 - Base

1. Criar/padronizar etiquetas.
2. Criar/padronizar campos personalizados.
3. Subir os 6 arquivos `.txt` da base da Rute.
4. Revisar prompt da Rute geral.
5. Revisar prompt da Rute Cadastro.

### Fase 2 - Fluxos essenciais

1. `Encerrar Conversa`
2. `Atendimento Humano / Secretaria`
3. `Interrupcao - Humano / Fora de Escopo`
4. `Inatividade - Encerrar ou Retomar`
5. `Boas Vindas Filadelfia`
6. `Mensagem Padrão - IA RUTE`
7. `Atualização Cadastral`
8. `Fluxo 2A - Confirmacao Cadastral Semestral`

### Fase 3 - Fluxos pastorais

1. `VISITANTE`
2. `Pedido de Aconselhamento`
3. `Pedido de Oração`
4. `G12 e Células`
5. `Ministérios`
6. `Eventos e Agenda`

### Fase 4 - Sequencias

1. `SEQ - Retomar Atualizacao Cadastral`
2. `SEQ - Revisao Cadastral 6M`
3. `SEQ - Recadastro Anual`
4. `SEQ - Follow-up Visitante 24h`
5. `SEQ - Pedido de Oracao Follow-up`

### Fase 5 - Webhooks

1. Configurar ngrok/tunel.
2. Ligar `/webhook_atualizacao_cadastral`.
3. Testar chamada vazia do BotConversa.
4. Testar contato ficticio.
5. Implementar novos endpoints no Hermes, um por vez.

## 24. Atualizacao do Hermes e Sistema

### Antes de usar webhooks

Rodar:

```powershell
python database\migrate_pastoral_system.py
python integrations\sync_botconversa_config.py
```

Subir servidor:

```powershell
python integrations\webhook_server.py
```

Expor porta 5050:

```powershell
ngrok http 5050
```

No dashboard, usar a aba WhatsApp & BotConversa para copiar a URL:

```text
https://SEU-NGROK/webhook_atualizacao_cadastral
```

### Para novos endpoints

Alterar:

- `integrations/webhook_server.py`
- `database/migrate_pastoral_system.py`
- `dashboard/app.py`
- opcionalmente `integrations/sync_botconversa_config.py`

Criar funcoes:

- `processar_evento_contato`
- `processar_visitante`
- `processar_pedido_oracao`
- `processar_aconselhamento`
- `processar_g12_celulas`
- `processar_ministerio`
- `processar_evento`
- `processar_atendimento_humano`

Adicionar rotas:

```python
Route("/webhook_evento_contato", endpoint=webhook_evento_contato_endpoint, methods=["POST"])
Route("/webhook_visitante", endpoint=webhook_visitante_endpoint, methods=["POST"])
Route("/webhook_pedido_oracao", endpoint=webhook_pedido_oracao_endpoint, methods=["POST"])
Route("/webhook_aconselhamento", endpoint=webhook_aconselhamento_endpoint, methods=["POST"])
Route("/webhook_g12_celulas", endpoint=webhook_g12_celulas_endpoint, methods=["POST"])
Route("/webhook_ministerio", endpoint=webhook_ministerio_endpoint, methods=["POST"])
Route("/webhook_evento", endpoint=webhook_evento_endpoint, methods=["POST"])
Route("/webhook_atendimento_humano", endpoint=webhook_atendimento_humano_endpoint, methods=["POST"])
```

### Tabelas futuras recomendadas

- `pedidos_oracao`
- `pedidos_aconselhamento`
- `pedidos_celula`
- `interesses_ministerio`
- `interesses_eventos`
- `atendimentos_humanos`
- opcional: `botconversa_eventos`

## 25. Testes Obrigatorios

Criar contatos ficticios e testar:

1. Visitante novo pergunta horario.
2. Visitante pede para conhecer uma celula.
3. Membro sem cadastro clica `Sou membro`.
4. Membro completo sem atualizacao entra no fluxo 2A.
5. Membro diz `tudo igual`.
6. Membro envia audio/texto: "mudei de bairro e agora estou na celula do Joaquim".
7. Pessoa pede oracao simples.
8. Pessoa pede aconselhamento.
9. Pessoa pede para servir no louvor.
10. Lider envia relatorio de celula.
11. Pessoa pergunta evento confirmado.
12. Pessoa pergunta evento nao confirmado.
13. Pessoa pede humano/pastor/secretaria.
14. Pessoa reclama que a IA esta repetindo.
15. Pessoa abandona o fluxo e cai em inatividade.

Para cada teste, conferir:

- mensagem correta;
- etiquetas aplicadas/removidas;
- campos salvos;
- fluxo de destino;
- webhook recebido;
- tabela SQLite atualizada;
- log em `botconversa_sync_log`;
- dashboard refletindo informacao.

## 26. Checklist de Pronto

Um fluxo esta pronto quando:

- tem nome padronizado;
- tem entrada clara;
- tem mensagens com `Graça e Paz!`;
- tem botoes claros;
- salva campos corretos;
- aplica/remove etiquetas corretas;
- tem saida para humano;
- tem saida de interrupcao;
- tem saida de inatividade;
- tem saida de encerramento;
- chama webhook quando precisa persistir no Hermes;
- foi testado com contato ficticio;
- resultado aparece no dashboard ou no log.

## 27. Observacoes Criticas

1. `Resumo_Atend_IA` e para resumo da conversa, nao para salvar todos os dados cadastrais.
2. `Campos Personalizados` do Assistente GPT devem ser usados para campos especificos que a IA pode extrair.
3. Estados criticos devem ser etiquetas/campos, nao somente texto da IA.
4. O BotConversa deve rotear; a IA deve classificar.
5. O Hermes deve ser a fonte de sincronizacao e auditoria.
6. Toda rotina de tempo longa, como 180/365 dias, pode comecar em sequencia do BotConversa, mas deve evoluir para rotina Hermes se precisar de confiabilidade e cruzamento de dados.
