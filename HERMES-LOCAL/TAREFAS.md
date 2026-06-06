# 📋 Quadro de Tarefas - Hermes Filadélfia

Este arquivo serve como o painel de progresso geral do ecossistema. Ele deve ser atualizado ao final de cada sprint para sabermos exatamente o que foi concluído e o que está planejado para os próximos passos.

---

## 🟢 Concluído

### 📂 Organização de Base e Documentação
- [x] Limpeza e organização estrutural da pasta `docs/` conforme índice oficial.
- [x] Criação de `docs/README.md` e `docs/METODO_PLANEJAMENTO_COLABORATIVO.md` oficiais.
- [x] Definição e revisão do [PLANO_MESTRE_HERMES_FILADELFIA.md](file:///c:/Users/hanie/OneDrive/Documentos/WORKSPACE/Projetos%20Locais/Gestao%20Pastoral%20-%20Pr%20Raniel%20Levi/HERMES-LOCAL/docs/PLANO_MESTRE_HERMES_FILADELFIA.md) e [PROJETO_VISUAL_CHATBOT_BOTCONVERSA_IA.md](file:///c:/Users/hanie/OneDrive/Documentos/WORKSPACE/Projetos%20Locais/Gestao%20Pastoral%20-%20Pr%20Raniel%20Levi/HERMES-LOCAL/docs/PROJETO_VISUAL_CHATBOT_BOTCONVERSA_IA.md).

### 👩‍💼 Módulo 1: Rute Inbox / Central Hermes de Atendimento
- [x] Criação da tabela SQLite `atendimentos_rute` para consolidar pedidos de oração, aconselhamento, células, etc.
- [x] Script de migração (`database/migrate_pastoral_system.py`) e adaptação do banco (`database/initialize_db.py`).
- [x] Criação da aba **👩‍💼 Rute Inbox** no painel Streamlit com gráficos de status e tipo de demanda.
- [x] Adicionado formulário de abertura de atendimento manual e atualização de status pelo painel.
- [x] Criação da rota `/webhook_atendimento_rute` no servidor de webhooks.

### 🦁 Módulo 2: Células, G12 e Consolidação (Agente Caleb)
- [x] Criação das tabelas `consolidacao_visitantes` e `relatorios_celulas` no SQLite.
- [x] Rota `/webhook_visitante` na API para registrar novos contatos e inseri-los no funil de consolidação.
- [x] Rota `/webhook_g12_celulas` na API para receber relatórios de frequência, visitantes e decisões dos líderes.
- [x] Atualização da aba **🦁 Visão G12 & Caleb** no dashboard com:
  - Tabela com fila de visitantes pendentes e integrados.
  - Formulário para atribuição de consolidador, checagem do prazo de 24h e registro de feedback do visitante.
  - Formulário manual para registrar relatórios de células diretamente pelo painel.
  - Tabela com os relatórios semanais de células enviados recentemente.
- [x] Criação do script de verificação de prazo crítico de consolidação (`agents/verificar_consolidacao_24h.py`).
- [x] Criação e execução com sucesso de testes de webhook automatizados simulando o BotConversa (`database/test_webhooks.py`).

---

### 🚀 Fase 1: Supabase e Banco Central Online
- [x] Criar e configurar o projeto no Supabase (PostgreSQL remoto).
- [x] Adicionar `psycopg2-binary==2.9.10` em [requirements.txt](file:///c:/Users/hanie/OneDrive/Documentos/WORKSPACE/Projetos%20Locais/Gestao%20Pastoral%20-%20Pr%20Raniel%20Levi/HERMES-LOCAL/requirements.txt) e instalar dependências.
- [x] Configurar chaves no arquivo `.env` a partir do template estruturado.
- [x] Criar tabelas faltantes (`metas_diarias`, `registro_procrastinacao`, `sugestoes_bi`) e RLS nas tabelas expostas.
- [x] Criar view de compatibilidade `posts_conteudo` com trigger `INSTEAD OF` para converter enums.
- [x] Desenvolver script de migração relacional atômica de dados SQLite -> Supabase (`sqlite_to_supabase.py`).
- [x] Adaptar o servidor de webhooks (`webhook_server.py`) e o dashboard (`app.py`) para PostgreSQL com fallback dinâmico e tradução de query placeholders (`?` para `%s`).

### ☁️ Fase 2: Deploy e Operação Online 24h
- [x] Configurar servidor VPS Hostinger com Docker Compose.
- [x] Realizar deploy do servidor de webhooks e dashboard Hermes.
- [x] Configurar proxy reverso Caddy / SSL para fornecer URL HTTPS pública estável para os webhooks do BotConversa.
- [x] Propagar domínio oficial.
- [x] Validar `https://api.filadelfiacorrente.com/health` e `https://painel.filadelfiacorrente.com` em produção.

### Hermes 2.0 MVP
- [x] Criar camada `hermes_v2/` com normalização, classificação, idempotência, inbox e tarefas.
- [x] Criar migration Supabase para `event_logs`, `inbox_pastoral` e `tarefas_pastorais`.
- [x] Adicionar webhook único `POST /webhook/botconversa` mantendo rotas legadas ativas.
- [x] Criar dashboard operacional enxuto em `dashboard/app_v2.py`.
- [x] Atualizar Docker/local scripts para abrir o dashboard Hermes 2.0 por padrão.
- [x] Registrar congelamento da v1 em `docs/v1-legado/README.md`.
- [x] Adicionar testes automatizados da v2 em `database/test_hermes_v2.py`.

---

## 🟡 Em Andamento

### 💬 Fase 3: Integração em Produção com BotConversa
- [ ] Substituir URL temporária do Ngrok pela URL oficial HTTPS nos blocos de integração do BotConversa.
- [ ] Rodar a migration `supabase/migrations/20260605143000_hermes_v2_mvp.sql` no Supabase de produção.
- [ ] Configurar um fluxo piloto do BotConversa para `POST /webhook/botconversa`.
- [x] Verificar inventário real de etiquetas, campos, fluxos e sequências do BotConversa.
- [x] Criar inventário da Fase 3 em `docs/_apoio_botconversa/INVENTARIO_BOTCONVERSA_FASE_3_HERMES_2.md`.
- [x] Criar guia passo a passo em `docs/_apoio_botconversa/PASSO_A_PASSO_FLUXOS_BOTCONVERSA_HERMES_2.md`.
- [x] Atualizar checklist de execução dos fluxos para Hermes 2.0.
- [x] Criar plano de recadastro anual para toda a base em `docs/_apoio_botconversa/PLANO_RECADASTRO_ANUAL_TODA_BASE.md`.
- [ ] Criar etiqueta `Atualização Recusada` no BotConversa.
- [ ] Criar `SEQ - Recadastro Anual`.
- [ ] Criar `SEQ - Follow-up Visitante 24h`.
- [ ] Criar `SEQ - Retomar Atualizacao Cadastral`.
- [ ] Criar `SEQ - Pedido de Oracao Follow-up`.
- [ ] Parar de usar `Revisao 6M Agend` e `SEQ - Revisao Cadastral 6M`.
- [ ] Padronizar `1-  RUTE SECRETARIA` para `1- RUTE SECRETARIA`.
- [ ] Definir `0000 - Encerrar Conversa` como encerramento oficial e substituir conexões para `2- Encerrar Conversa`.
- [ ] Validar recebimento de webhooks a partir de interações reais no WhatsApp.
- [ ] Ligar etiquetas (`Membro`, `Visitante`, `Consolidação 24h`) e campos personalizados reais às ações dos webhooks.

---

## 🔴 Pendente / Planejado

### 📅 Fase 4: Integração de Agenda (Google Calendar)
- [ ] Implementar a sincronização incremental da tabela `compromissos` com o Google Calendar do Pastor na VPS.
- [ ] Criar regras de agendamento automático e bloqueios de horário.

### 📁 Fase 5: Integração Google Drive (Acervo e Conhecimento)
- [ ] Criar worker para monitorar a pasta `IGREJA - BASE HERMES` no Google Drive.
- [ ] Sincronizar metadados dos arquivos e criar rotina de indexação semântica no banco de dados.

### ⛪ Fase 6: Site Público da Igreja
- [ ] Desenvolver site institucional (cultos, eventos, células, solicitação de oração e aconselhamento).
- [ ] Conectar formulários do site diretamente ao WhatsApp / BotConversa.

### 💵 Fase 7: Módulo Financeiro
- [ ] Definir regras de lançamento de receitas e despesas por ministério e contas.
- [ ] Implementar relatórios financeiros mensais e controle de aprovações.

### 📢 Fase 8: Módulo de Comunicação (Barnabé)
- [ ] Organizar pipeline editorial de posts e roteiros no dashboard.
