# BotConversa - Fluxos Pastorais

Este guia define os itens que devem existir no BotConversa para integrar WhatsApp, Hermes e o dashboard pastoral.

## Itens Já Encontrados

- Fluxo: `Boas Vindas`
- Fluxo: `Atualização Cadastral`
- Etiqueta: `Filadelfia Corrente`
- Etiqueta: `CONVENÇÃO G12 2026`
- Etiqueta: `G12 Pastoral - Pr. Raniel`
- Etiqueta: `G12 Pastoral - Pastora Vanessa`
- Etiqueta: `Ministério de Louvor`

## Etiquetas a Criar

Crie estas etiquetas no BotConversa:

- `Membro`
- `Visitante`
- `Atualização Cadastral`
- `Cadastro Completo`
- `Cadastro Incompleto`
- `Atualização Pendente`
- `Consolidação 24h`
- `Célula`
- `G12 Pastoral`
- `Ministério`

## Campos Personalizados a Criar

Crie estes campos personalizados no BotConversa:

- `Data_Nascimento`
- `Bairro`
- `Tempo_Igreja`
- `Lider_Celula`
- `Fez_Encontro`
- `Universidade_Vida`
- `Capacitacao_Destino`
- `Interesse_Ministerio`
- `Feedback_Melhorias`
- `Feedback_Falta`
- `Celula_Atual`
- `G12_Pastoral`
- `Ministerios`
- `Data_Conversao`
- `Ultima_Atualizacao_Cadastral`

Use texto para campos livres. Para datas, use data se o BotConversa aceitar bem no fluxo; se houver atrito com formato, use texto e padronize como `DD/MM/AAAA`.

## Fluxo 1 - Boas Vindas

Objetivo: recepcionar a pessoa, identificar se está cadastrada e encaminhar para atualização cadastral quando necessário.

### Lógica recomendada de triagem cadastral

Use as etiquetas com estes significados:

- `Cadastro Completo`: a pessoa já preencheu os dados mínimos obrigatórios.
- `Atualização Cadastral`: a pessoa já fez a atualização do ciclo vigente.
- `Cadastro Incompleto`: faltam dados obrigatórios.
- `Atualização Pendente`: precisa atualizar dados neste ciclo.

Regra principal:

1. Se o contato **não tem** `Atualização Cadastral`, ele precisa passar pela atualização do ciclo atual.
2. Se o contato tem `Cadastro Completo`, mesmo assim deve confirmar os dados a cada 6 meses e, depois que o processo estiver maduro, ao menos 1 vez por ano.
3. Se o contato não tem `Cadastro Completo` e também não tem `Atualização Cadastral`, perguntar primeiro se é membro ou visitante.
4. Se for membro, iniciar atualização cadastral, salvar os dados obrigatórios e marcar `Cadastro Completo` + `Atualização Cadastral`.
5. Se for visitante, enviar para consolidação de visitante.

### Estrutura sugerida

1. Mensagem de recepção:
   "Graça e Paz! Seja bem-vindo(a) à Igreja Batista Filadélfia Internacional de Corrente. Sou a assistente virtual da secretaria pastoral."

2. Condição por etiquetas:
   - Se tem `Atualização Cadastral` + `Cadastro Completo`: enviar para Rute / menu principal.
   - Se não tem `Atualização Cadastral` mas tem `Cadastro Completo`: enviar para confirmação semestral de dados.
   - Se não tem `Cadastro Completo`: perguntar se é membro ou visitante.

3. Pergunta:
   "Você já faz parte da nossa igreja ou está nos visitando?"

4. Opções:
   - `Sou membro`
   - `Sou visitante`
   - `Quero conhecer melhor`

5. Ações:
   - Se `Sou membro`: aplicar etiqueta `Membro`, aplicar `Cadastro Incompleto` se faltar dado obrigatório e enviar para `Atualização Cadastral`.
   - Se `Sou visitante`: aplicar etiqueta `Visitante` e enviar para `Consolidação de Visitante`.
   - Se `Quero conhecer melhor`: aplicar etiqueta `Visitante` e enviar mensagem com endereço, horários e convite.

## Fluxo 2 - Atualização Cadastral

Objetivo: atualizar dados a cada 6 meses e manter célula, liderança e trilha de crescimento em dia.

Blocos:

1. Boas-vindas e consentimento
   "Graça e Paz! Estamos atualizando os dados dos nossos membros para melhorar nossa comunicação e cuidado com você. Leva menos de 3 minutos. Podemos começar?"

   Botões:
   - `Sim, vamos lá!`
   - `Agora não`

   Se `Agora não`: encerrar com gentileza e manter a etiqueta `Atualização Cadastral`.

2. Dados pessoais
   - Nome completo -> campo padrão Nome
   - WhatsApp com DDD -> campo padrão Telefone
   - Data de nascimento -> `Data_Nascimento`
   - Bairro e cidade -> `Bairro`

3. Jornada e liderança
   - Tempo de igreja -> `Tempo_Igreja`
     - `Menos de 6 meses`
     - `De 6 meses a 2 anos`
     - `Mais de 2 anos`
   - Líder de célula -> `Lider_Celula`
   - Célula atual -> `Celula_Atual`
   - G12 pastoral -> `G12_Pastoral`

4. Trilhas de crescimento
   - Encontro com Deus -> `Fez_Encontro`
     - `Sim`
     - `Não`
   - Universidade da Vida -> `Universidade_Vida`
     - `Sim`
     - `Não`
     - `Estou fazendo`
   - Capacitação Destino -> `Capacitacao_Destino`
     - `Sim`
     - `Não`
     - `Estou fazendo`

5. Ministério e voluntariado
   - Deseja servir? Se sim, perguntar áreas de interesse.
   - Salvar em `Interesse_Ministerio`.
   - Se já serve, registrar ministérios em `Ministerios`.

6. Feedback
   - Melhorias -> `Feedback_Melhorias`
   - O que sente falta -> `Feedback_Falta`

7. Encerramento
   - Aplicar etiqueta `Cadastro Completo`.
   - Aplicar etiqueta `Atualização Cadastral`.
   - Remover etiqueta `Atualização Pendente`, se existir.
   - Remover etiqueta `Cadastro Incompleto`, se existir.
   - Definir `Ultima_Atualizacao_Cadastral`.
   - Mensagem final:
     "Muito obrigado! Seus dados foram atualizados com sucesso. Deus abençoe muito a sua vida!"

## Fluxo 3 - Consolidação de Visitante

Objetivo: garantir cuidado em até 24 horas após a visita.

Blocos:

1. Recepção:
   "Graça e Paz! Ficamos felizes com sua visita. Queremos cuidar bem de você e te conhecer melhor."

2. Dados mínimos:
   - Nome completo
   - WhatsApp
   - Bairro/cidade
   - Como conheceu a igreja
   - Gostaria de receber contato de alguém da liderança?

3. Ações:
   - Aplicar etiqueta `Visitante`.
   - Aplicar etiqueta `Consolidação 24h`.
   - Encaminhar para atendente/responsável, se o BotConversa permitir.

## Rotina Semestral

A cada 6 meses:

1. Filtrar membros com `Ultima_Atualizacao_Cadastral` antiga ou vazia.
2. Remover etiqueta `Atualização Cadastral`.
3. Aplicar etiqueta `Atualização Pendente`.
4. Disparar fluxo `Atualização Cadastral`.
5. Ao concluir, aplicar `Atualização Cadastral`, remover `Atualização Pendente` e atualizar `Ultima_Atualizacao_Cadastral`.

Depois que o processo estiver estabilizado, manter:

- Confirmação leve a cada 6 meses para dados sensíveis a mudança: telefone, bairro, célula, líder, ministérios e trilhas.
- Recadastramento completo 1 vez por ano.
6. Acompanhar pendências no dashboard.

## Comunicação Segmentada

Tipos de comunicação planejados:

- Agenda Semanal
- Resumo do Culto
- Resumo da Reunião G12
- Posts nas Redes Sociais
- Post no Blog da Igreja
- Novo Vídeo no Canal
- Devocional Diário
- Eventos

No dashboard, cada comunicação deve ter:

- Público-alvo
- Canal
- Status
- Mensagem
- Data programada
- ID do fluxo, sequência ou campanha no BotConversa
