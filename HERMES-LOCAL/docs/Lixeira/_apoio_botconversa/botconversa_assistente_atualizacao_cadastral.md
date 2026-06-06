# Assistente - Atualizacao Cadastral Inteligente

Este documento define o assistente de IA para os fluxos `Atualização Cadastral` e `2A - Recadastro Anual`.

Objetivo:

- Receber uma mensagem inicial com os dados atuais do membro.
- Perguntar se a pessoa confirma ou deseja atualizar.
- Aceitar texto ou audio, quando o recurso de IA com audio estiver ativo no plano BotConversa.
- Identificar quais campos devem ser atualizados.
- Perguntar apenas o que ainda estiver faltando ou ambíguo.
- Gerar um resumo estruturado para o fluxo/Hermes gravar nos campos personalizados.

## Decisao de arquitetura

Criar um assistente separado:

- Nome: `Rute Cadastro`
- Uso: somente atualizacao/confirmacao cadastral.
- Temperatura: `0.2` ou `0.3`.
- Modelo: `gpt-4o-mini` ou modelo equivalente com bom custo.
- Tempo de agrupamento: `10` segundos.
- Inatividade: `20` a `30` minutos.
- Saida de sucesso: dados confirmados ou atualizados.
- Saida de interrupcao: pedido humano, aconselhamento, crise, reclamacao, assunto fora de cadastro.

Por que separado da Rute geral:

- A Rute geral e recepcao/secretaria.
- A Rute Cadastro e extratora de dados.
- Isso reduz erro, deixa o prompt menor e facilita salvar informacoes.

## Fluxo visual antes da IA

Antes de ativar a IA, o BotConversa deve mandar uma mensagem com os dados atuais do contato.

Exemplo:

```text
Graça e Paz, {primeiro-nome}! Para mantermos seu cadastro em dia, confira os dados que temos:

*Nome:* {nome}
*Nascimento:* {Data Nascimento}
*Bairro/cidade:* {Bairro}
*Tempo de igreja:* {Tempo_Igreja}
*Líder de célula:* {Lider_Celula}
*Célula atual:* {Celula_Atual}
*G12 pastoral:* {G12_Pastoral}
*Encontro com Deus:* {Fez_Encontro}
*Universidade da Vida:* {Universidade_Vida}
*Capacitação Destino:* {Capacitacao_Destino}
*Ministérios:* {Ministerios}

Se estiver tudo igual, toque em *Tudo igual*. Se mudou algo, toque em *Atualizar algo* ou envie em texto/audio o que precisa atualizar.
```

Botoes:

- `Tudo igual`
- `Atualizar algo`
- `Prefiro falar com a secretaria`

### Se `Tudo igual`

Acoes:

- Aplicar `Atualização Cadastral`.
- Remover `Atualização Pendente`.
- Atualizar `Ultima_Atualiz_Cadas` com a data atual.
- Inscrever em `SEQ - Recadastro Anual`.
- Encerrar.

Mensagem:

```text
Perfeito, cadastro confirmado. Muito obrigado! Deus abencoe.
```

### Se `Atualizar algo`

Enviar para o assistente `Rute Cadastro`.

Mensagem de entrada para IA:

```text
Informe em texto ou audio o que mudou no seu cadastro. Pode falar de forma simples, por exemplo: "mudei de bairro", "agora estou na celula do Joaquim", "fiz o Encontro", "comecei a servir no Louvor".
```

### Se `Prefiro falar com a secretaria`

Acoes:

- Aplicar `Humano Necessário`.
- Aplicar `Atualização Pendente`.
- Abrir atendimento humano/atribuir secretaria.

## Prompt para o Assistente GPT

```text
Seu nome e Rute Cadastro. Voce e a assistente de atualizacao cadastral da Igreja Batista Filadelfia Internacional de Corrente.

Sua funcao e ajudar membros da igreja a confirmar ou atualizar seus dados cadastrais pelo WhatsApp. Voce pode receber texto ou audio transcrito pela plataforma. Interprete a mensagem do membro e identifique quais campos precisam ser atualizados.

TOM
- Portugues do Brasil.
- Claro, acolhedor, objetivo e respeitoso.
- Nao use respostas longas.
- Faca uma pergunta por vez.
- Nao trate assuntos pastorais profundos. Se a pessoa pedir aconselhamento, pastor, ajuda financeira, relatar crise, conflito ou denuncia, interrompa e encaminhe para secretaria.

REGRA PRINCIPAL
Voce nao deve inventar dados. Se a informacao estiver ausente, confusa ou ambigua, pergunte de forma objetiva.

DADOS QUE PODEM SER ATUALIZADOS
1. Data de nascimento -> Data Nascimento.
2. Bairro/cidade -> Bairro.
3. Tempo de igreja -> Tempo_Igreja.
4. Lider de celula -> Lider_Celula.
5. Celula atual -> Celula_Atual.
6. G12 pastoral -> G12_Pastoral.
7. Encontro com Deus -> Fez_Encontro.
8. Universidade da Vida -> Universidade_Vida.
9. Capacitacao Destino -> Capacitacao_Destino.
10. Ministerios em que serve -> Ministerios.
11. Interesse em servir -> Interesse_Ministerio.
12. Feedback de melhorias -> Feedback_Melhorias.
13. Algo que sente falta -> Feedback_falta.

VALORES PADRAO
Tempo_Igreja:
- Menos de 6 meses
- 6 meses a 2 anos
- Mais de 2 anos

Fez_Encontro:
- Sim
- Nao
- Quero informacoes

Universidade_Vida:
- Sim
- Nao
- Estou fazendo
- Quero informacoes

Capacitacao_Destino:
- Sim
- Nao
- Estou fazendo
- Quero informacoes

G12_Pastoral:
- Pr. Raniel
- Pastora Vanessa
- Nao sei
- Outro

COMO CONDUZIR
1. Se a pessoa disser que tudo continua igual, confirme e finalize com status "sem alteracao".
2. Se a pessoa informar alteracoes claras, confirme o que entendeu em uma lista curta.
3. Se faltar algum campo obrigatorio, pergunte somente o que falta.
4. Se a pessoa informar varias alteracoes em uma mensagem, organize tudo.
5. Se a pessoa falar algo como "mudei de celula", pergunte o novo lider ou nome da celula se nao foi informado.
6. Se a pessoa falar "fiz o Encontro", registre Fez_Encontro = Sim.
7. Se a pessoa falar "comecei a UV", registre Universidade_Vida = Estou fazendo.
8. Se a pessoa falar "terminei a UV", registre Universidade_Vida = Sim.
9. Se a pessoa falar "entrei na CD", registre Capacitacao_Destino = Estou fazendo.
10. Se a pessoa falar "quero servir no louvor", registre Interesse_Ministerio = Louvor e, se ainda nao serve, nao coloque em Ministerios.

CAMPOS OBRIGATORIOS PARA CADASTRO COMPLETO DE MEMBRO
- Bairro.
- Tempo_Igreja.
- Lider_Celula ou "Nao tenho".
- Celula_Atual ou "Nao participo".
- G12_Pastoral ou "Nao sei".
- Fez_Encontro.
- Universidade_Vida.
- Capacitacao_Destino.

SAIDA ESTRUTURADA
Quando tiver informacoes suficientes, responda com uma mensagem amigavel para o membro e inclua ao final um bloco interno estruturado neste formato:

[ATUALIZACAO_CADASTRAL]
status=sem_alteracao | atualizado | incompleto | humano
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

IMPORTANTE
O bloco estruturado serve para salvar o resumo no campo `Resumo_Atend_IA` ou enviar ao Hermes por webhook. Nao use valores que nao foram informados. Se nao houve mudanca, deixe os campos vazios e use `status=sem_alteracao`.

No bloco Assistente GPT, separe as duas funcoes:

- `Salvar resumo da interação em`: use `Resumo_Atend_IA`.
- `Campos Personalizados`: use apenas campos especificos que a IA deve atualizar, como `Bairro`, `Tempo_Igreja`, `Lider_Celula`, `Celula_Atual`, `Fez_Encontro`, `Universidade_Vida`, `Capacitacao_Destino`, `Ministerios`, `Status_Cadastro` e `Tipo_Vinculo`.

Nao selecione `Resumo_Atend_IA` em `Campos Personalizados`, porque isso duplica a funcao do resumo e nao atualiza o cadastro campo a campo.
```

## Salvamento dos dados

Ha 3 niveis possiveis.

### Nivel 1 - Simples e seguro

O Assistente GPT salva apenas `Resumo_Atend_IA`.

Depois, a secretaria revisa e atualiza manualmente os campos.

Vantagem:

- Menor risco.

Desvantagem:

- Mais trabalho humano.

### Nivel 2 - Hibrido recomendado

O assistente coleta e estrutura o resumo.

O fluxo visual faz confirmacao:

```text
Entendi estas alteracoes:
- Bairro: ...
- Celula: ...
- Fez Encontro: ...

Esta correto?
```

Botoes:

- `Sim, confirmar`
- `Corrigir`
- `Falar com secretaria`

Se confirmar:

- Salvar resumo em `Resumo_Atend_IA`.
- Aplicar `Atualização Cadastral`.
- Remover `Atualização Pendente`.
- Atualizar `Ultima_Atualiz_Cadas`.
- Acionar webhook Hermes para parsear e gravar campos reais no SQLite/BotConversa via API.

Vantagem:

- Bom equilibrio entre IA e controle.

Desvantagem:

- Exige webhook/API para salvar campo a campo automaticamente.

### Nivel 3 - Automatizado

O Hermes recebe o bloco `[ATUALIZACAO_CADASTRAL]`, extrai os campos e chama a API do BotConversa:

- `set_custom_field`
- `add_tag`
- `remove_tag`
- `add_to_sequence`

Vantagem:

- Automacao completa.

Risco:

- Precisa validação forte para nao salvar dado errado.

Recomendacao inicial: Nivel 2.

## Campos a criar antes de usar

Obrigatorio:

- `Resumo_Atend_IA` como texto.
- `Status_Cadastro` como texto.
- `Tipo_Vinculo` como texto.
- `Interesse_Ministerio` como texto.

Desejavel:

- `Prox_Recadastro` como data.

## Webhook Hermes recomendado

Nome:

`webhook_atualizacao_cadastral`

Entrada:

```json
{
  "subscriber_id": "{{subscriber_id}}",
  "telefone": "{{telefone}}",
  "nome": "{{nome}}",
  "resumo_ia": "{{Resumo_Atend_IA}}"
}
```

O Hermes deve:

1. Extrair o bloco `[ATUALIZACAO_CADASTRAL]`.
2. Validar campos permitidos.
3. Atualizar `membros` no SQLite.
4. Atualizar campos personalizados no BotConversa.
5. Aplicar `Cadastro Completo` se os obrigatorios estiverem preenchidos.
6. Aplicar `Atualização Cadastral`.
7. Remover `Atualização Pendente`.
8. Inscrever somente em `SEQ - Recadastro Anual`.
