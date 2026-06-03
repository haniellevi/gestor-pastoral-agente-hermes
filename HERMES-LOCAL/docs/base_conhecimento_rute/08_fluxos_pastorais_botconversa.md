# Fluxos Pastorais no BotConversa

## Fluxo 1 - Boas Vindas

Objetivo: recepcionar a pessoa, identificar se esta cadastrada e encaminhar corretamente.

### Mensagem inicial

```text
Graça e Paz! Seja bem-vindo(a) a Igreja Batista Filadelfia Internacional de Corrente. Sou a Rute, assistente virtual da secretaria pastoral.
```

### Logica

1. Aplicar etiqueta `Filadelfia Corrente`.
2. Verificar etiquetas:
   - Se tem `Cadastro Completo` e `Atualização Cadastral`: enviar para Rute geral.
   - Se tem `Cadastro Completo`, mas nao tem `Atualização Cadastral`: enviar para confirmacao cadastral semestral.
   - Se nao tem `Cadastro Completo`: perguntar se e membro, visitante ou outro vinculo.

### Opcoes

- `Sou membro`
- `Sou visitante`
- `Quero conhecer`
- `Outro vínculo`

## Fluxo 2 - Cadastro / Atualizacao Cadastral Completa

Objetivo: coletar dados obrigatorios de membro e manter cadastro em dia.

Campos principais:

- Nome completo
- WhatsApp
- Data de nascimento
- Bairro/cidade
- Tempo de igreja
- Lider de celula
- Celula atual
- G12 pastoral
- Fez Encontro com Deus
- Universidade da Vida
- Capacitacao Destino
- Ministerios
- Interesse em servir
- Feedback/melhorias
- Ultima atualizacao cadastral

Encerramento:

- Aplicar `Cadastro Completo`.
- Aplicar `Atualização Cadastral`.
- Remover `Cadastro Incompleto`.
- Remover `Atualização Pendente`.
- Definir `Status_Cadastro = Completo`.
- Definir `Ultima_Atualiz_Cadas = data atual`.
- Inscrever em revisao cadastral futura.

## Fluxo 2A - Confirmacao Cadastral Semestral

Objetivo: verificar se os dados continuam iguais ou se algo mudou.

Mensagem padronizada:

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

Opcoes:

- `Tudo igual`
- `Atualizar algo`
- `Prefiro falar com a secretaria`

Se `Tudo igual`:

- aplicar `Atualização Cadastral`;
- remover `Atualização Pendente`;
- atualizar `Ultima_Atualiz_Cadas`;
- reinscrever em revisao futura.

Se `Atualizar algo`:

- ativar `Rute Cadastro`;
- salvar resumo em `Resumo_Atend_IA`;
- salvar campos personalizados especificos quando configurados;
- enviar webhook para Hermes quando necessario.

## Fluxo 3 - Visitante / Consolidacao

Objetivo: acolher visitante e garantir contato em ate 24h.

Campos:

- Nome
- WhatsApp
- Bairro/cidade
- Como conheceu a igreja
- Interesse
- Deseja contato da lideranca?

Acoes:

- Aplicar `Visitante`.
- Aplicar `Consolidação 24h`.
- Notificar Luciane/consolidacao.
- Encaminhar para Caleb quando envolver celula/consolidacao.

Mensagem:

```text
Graça e Paz! Ficamos felizes com sua visita. Queremos cuidar bem de voce e te conhecer melhor.
```

## Fluxo 4 - Pedido de Oracao

Objetivo: registrar pedido e encaminhar para intercessao.

Passos:

1. Acolher.
2. Perguntar se pode registrar.
3. Salvar resumo em `Resumo_Atend_IA` ou campo `Pedido_Oracao`, se criado.
4. Aplicar etiqueta `Pedido de Oração`, se existir.
5. Notificar intercessao/secretaria.
6. Se houver crise, abrir atendimento humano.

## Fluxo 5 - Pedido de Aconselhamento

Objetivo: triagem segura e atendimento humano.

Regras:

- Nao confirmar horario automaticamente.
- Nao prometer resposta imediata.
- Nao deixar robo continuar apos abrir atendimento humano.
- A Rute pode acolher, mas nao deve aconselhar profundamente.

Passos:

1. Mensagem de privacidade/cuidado.
2. Perguntar nome e melhor horario para retorno, se necessario.
3. Salvar resumo curto.
4. Aplicar `Pedido de Aconselhamento`.
5. Aplicar `Humano Necessário`.
6. Atribuir e abrir atendimento para secretaria/departamento pastoral.

## Fluxo 6 - Ministerios e Voluntariado

Objetivo: registrar interesse de servir e encaminhar responsavel.

Perguntas:

- Voce ja e membro?
- Em qual area gostaria de servir?

Areas conhecidas:

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

Acoes:

- Salvar `Interesse_Ministerio`.
- Aplicar `Ministério`.
- Notificar responsavel/departamento.

## Fluxo 7 - G12 e Celulas

Objetivo: orientar sobre celulas/G12 e encaminhar para Caleb/lideranca.

Opcoes:

- `Quero participar de uma celula`
- `Ja sou lider`
- `Tenho duvida sobre G12`
- `Relatorio de celula`

Acoes:

- Se deseja participar: salvar bairro e disponibilidade.
- Aplicar `Célula`.
- Se visitante: aplicar `Consolidação 24h`.
- Encaminhar para Caleb/central de celulas.

## Fluxo 8 - Encerrar Conversa

Mensagem:

```text
Fico a disposicao. Deus abencoe!
```

Se atendimento foi por IA:

- salvar `Resumo_Atend_IA`, se configurado;
- remover etiquetas temporarias quando aplicavel.

## Sequencias recomendadas

- `SEQ - Retomar Atualizacao Cadastral`
- `SEQ - Revisao Cadastral 6M`
- `SEQ - Recadastro Anual`
- `SEQ - Follow-up Visitante 24h`
- `SEQ - Pedido de Oracao Follow-up`

## Quando usar Hermes/API

Usar Hermes quando precisar:

- calcular datas com base em `Ultima_Atualiz_Cadas`;
- aplicar/remover etiquetas em massa;
- cruzar dados com SQLite, Google Sheets, Notion ou dashboard;
- verificar contatos fora de sequencia;
- rodar rotina mensal.

