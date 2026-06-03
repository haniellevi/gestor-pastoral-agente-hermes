-- Initial foundation for Hermes Filadelfia pastoral management.
-- Production data access is intentionally closed by RLS until app policies are defined.

create extension if not exists pgcrypto with schema extensions;
create extension if not exists vector with schema extensions;
create extension if not exists unaccent with schema extensions;

do $$
begin
    create type public.pessoa_tipo as enum ('membro', 'visitante', 'lider', 'equipe', 'outro');
exception when duplicate_object then null;
end $$;

do $$
begin
    create type public.status_cadastro as enum ('incompleto', 'completo', 'atualizar', 'recusou');
exception when duplicate_object then null;
end $$;

do $$
begin
    create type public.status_geral as enum ('pendente', 'em_andamento', 'concluido', 'cancelado', 'arquivado');
exception when duplicate_object then null;
end $$;

do $$
begin
    create type public.nivel_urgencia as enum ('baixa', 'media', 'alta', 'crise');
exception when duplicate_object then null;
end $$;

do $$
begin
    create type public.compromisso_categoria as enum (
        'Aconselhamento',
        'Culto',
        'Reuniao Lideranca',
        'Estudo/Sermao',
        'Pessoal',
        'Outros'
    );
exception when duplicate_object then null;
end $$;

do $$
begin
    create type public.rede_g12 as enum ('Jovens', 'Casais', 'Homens', 'Mulheres', 'Outro');
exception when duplicate_object then null;
end $$;

do $$
begin
    create type public.financeiro_tipo as enum ('receita', 'despesa', 'transferencia');
exception when duplicate_object then null;
end $$;

do $$
begin
    create type public.conteudo_status as enum ('ideia', 'rascunho', 'aprovado', 'roteirizado', 'gravado', 'postado', 'arquivado');
exception when duplicate_object then null;
end $$;

do $$
begin
    create type public.conhecimento_status as enum ('bruto', 'indexado', 'pendente_aprovacao', 'aprovado', 'rejeitado', 'arquivado', 'erro');
exception when duplicate_object then null;
end $$;

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.atualizado_em = now();
    return new;
end;
$$;

create table if not exists public.pessoas (
    id uuid primary key default gen_random_uuid(),
    nome_completo text not null,
    nome_preferido text,
    tipo public.pessoa_tipo not null default 'outro',
    data_nascimento date,
    observacoes text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.pessoa_contatos (
    id uuid primary key default gen_random_uuid(),
    pessoa_id uuid not null references public.pessoas(id) on delete cascade,
    canal text not null check (canal in ('whatsapp', 'telefone', 'email', 'telegram', 'outro')),
    valor text not null,
    principal boolean not null default false,
    verificado boolean not null default false,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now(),
    unique (canal, valor)
);

create table if not exists public.enderecos (
    id uuid primary key default gen_random_uuid(),
    pessoa_id uuid references public.pessoas(id) on delete cascade,
    bairro text,
    cidade text,
    uf text,
    endereco_livre text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.membros (
    id uuid primary key default gen_random_uuid(),
    pessoa_id uuid not null unique references public.pessoas(id) on delete cascade,
    tempo_igreja text,
    lider_celula text,
    celula_atual text,
    g12_pastoral text,
    fez_encontro text,
    universidade_vida text,
    capacitacao_destino text,
    ministerios text,
    interesse_ministerio text,
    data_conversao date,
    status_cadastro public.status_cadastro not null default 'incompleto',
    consentimento_comunicacao boolean not null default false,
    botconversa_subscriber_id bigint unique,
    ultima_atualizacao_cadastral date,
    proxima_atualizacao_cadastral date,
    proximo_recadastro_anual date,
    feedback_melhorias text,
    feedback_falta text,
    observacoes text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.visitantes (
    id uuid primary key default gen_random_uuid(),
    pessoa_id uuid not null references public.pessoas(id) on delete cascade,
    data_primeira_visita date,
    como_conheceu_igreja text,
    disponibilidade_celula text,
    status public.status_geral not null default 'pendente',
    botconversa_subscriber_id bigint unique,
    observacoes text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.consentimentos (
    id uuid primary key default gen_random_uuid(),
    pessoa_id uuid not null references public.pessoas(id) on delete cascade,
    finalidade text not null,
    concedido boolean not null default true,
    origem text,
    registrado_em timestamptz not null default now()
);

create table if not exists public.ministerios (
    id uuid primary key default gen_random_uuid(),
    nome text not null unique,
    descricao text,
    responsavel_pessoa_id uuid references public.pessoas(id),
    ativo boolean not null default true,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.ministerio_membros (
    id uuid primary key default gen_random_uuid(),
    ministerio_id uuid not null references public.ministerios(id) on delete cascade,
    pessoa_id uuid not null references public.pessoas(id) on delete cascade,
    papel text,
    status public.status_geral not null default 'em_andamento',
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now(),
    unique (ministerio_id, pessoa_id)
);

create table if not exists public.celulas (
    id uuid primary key default gen_random_uuid(),
    nome text not null,
    lider_pessoa_id uuid references public.pessoas(id),
    lider_nome text,
    rede public.rede_g12 not null default 'Outro',
    bairro text,
    dia_semana text,
    horario time,
    status public.status_geral not null default 'em_andamento',
    observacoes text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.celula_membros (
    id uuid primary key default gen_random_uuid(),
    celula_id uuid not null references public.celulas(id) on delete cascade,
    pessoa_id uuid not null references public.pessoas(id) on delete cascade,
    papel text not null default 'membro',
    ativo boolean not null default true,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now(),
    unique (celula_id, pessoa_id)
);

create table if not exists public.relatorios_celulas (
    id uuid primary key default gen_random_uuid(),
    data_relatorio date not null,
    celula_id uuid references public.celulas(id),
    nome_celula text not null,
    lider_pessoa_id uuid references public.pessoas(id),
    lider_nome text not null,
    presenca_membros integer not null default 0 check (presenca_membros >= 0),
    visitantes integer not null default 0 check (visitantes >= 0),
    decisoes_fe integer not null default 0 check (decisoes_fe >= 0),
    rede public.rede_g12 not null default 'Outro',
    observacoes text,
    origem text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.consolidacao_visitantes (
    id uuid primary key default gen_random_uuid(),
    visitante_id uuid references public.visitantes(id) on delete set null,
    pessoa_id uuid references public.pessoas(id) on delete set null,
    data_visita date not null,
    visitante_nome text not null,
    visitante_whatsapp text,
    consolidador_pessoa_id uuid references public.pessoas(id),
    consolidador_nome text,
    contato_24h boolean not null default false,
    data_contato timestamptz,
    feedback text,
    status text not null default 'Pendente' check (status in ('Pendente', 'Contatado', 'Integrado', 'Desistiu')),
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.consolidacao_acoes (
    id uuid primary key default gen_random_uuid(),
    consolidacao_id uuid not null references public.consolidacao_visitantes(id) on delete cascade,
    tipo text not null,
    descricao text,
    responsavel_pessoa_id uuid references public.pessoas(id),
    realizado_em timestamptz not null default now(),
    criado_em timestamptz not null default now()
);

create table if not exists public.pedidos_oracao (
    id uuid primary key default gen_random_uuid(),
    pessoa_id uuid references public.pessoas(id) on delete set null,
    nome text,
    telefone text,
    pedido text not null,
    nivel_urgencia public.nivel_urgencia not null default 'baixa',
    status public.status_geral not null default 'pendente',
    origem text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.pedidos_aconselhamento (
    id uuid primary key default gen_random_uuid(),
    pessoa_id uuid references public.pessoas(id) on delete set null,
    nome text,
    telefone text,
    melhor_horario text,
    resumo text,
    nivel_urgencia public.nivel_urgencia not null default 'media',
    status public.status_geral not null default 'pendente',
    responsavel_pessoa_id uuid references public.pessoas(id),
    compromisso_id uuid,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.pedidos_celula (
    id uuid primary key default gen_random_uuid(),
    pessoa_id uuid references public.pessoas(id) on delete set null,
    nome text,
    telefone text,
    bairro text,
    disponibilidade text,
    tipo_vinculo text,
    status public.status_geral not null default 'pendente',
    encaminhado_para text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.compromissos (
    id uuid primary key default gen_random_uuid(),
    titulo text not null,
    categoria public.compromisso_categoria not null default 'Outros',
    data_inicio timestamptz not null,
    data_fim timestamptz not null,
    descricao text,
    duracao_minutos integer generated always as ((extract(epoch from (data_fim - data_inicio)) / 60)::integer) stored,
    google_event_id text unique,
    pessoa_relacionada_id uuid references public.pessoas(id),
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now(),
    check (data_fim > data_inicio)
);

alter table public.pedidos_aconselhamento
    add constraint pedidos_aconselhamento_compromisso_fk
    foreign key (compromisso_id) references public.compromissos(id) on delete set null;

create table if not exists public.eventos (
    id uuid primary key default gen_random_uuid(),
    nome text not null,
    descricao text,
    data_inicio timestamptz,
    data_fim timestamptz,
    local text,
    status public.status_geral not null default 'pendente',
    google_event_id text unique,
    publico boolean not null default true,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.evento_inscricoes (
    id uuid primary key default gen_random_uuid(),
    evento_id uuid not null references public.eventos(id) on delete cascade,
    pessoa_id uuid references public.pessoas(id) on delete set null,
    nome text,
    telefone text,
    status public.status_geral not null default 'pendente',
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.google_calendar_sync_state (
    id uuid primary key default gen_random_uuid(),
    calendar_id text not null unique,
    sync_token text,
    last_sync_at timestamptz,
    status text not null default 'ativo',
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.financeiro_contas (
    id uuid primary key default gen_random_uuid(),
    nome text not null unique,
    tipo text,
    ativo boolean not null default true,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.financeiro_categorias (
    id uuid primary key default gen_random_uuid(),
    nome text not null,
    tipo public.financeiro_tipo not null,
    ativo boolean not null default true,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now(),
    unique (nome, tipo)
);

create table if not exists public.financeiro_lancamentos (
    id uuid primary key default gen_random_uuid(),
    conta_id uuid references public.financeiro_contas(id),
    categoria_id uuid references public.financeiro_categorias(id),
    ministerio_id uuid references public.ministerios(id),
    tipo public.financeiro_tipo not null,
    data_lancamento date not null,
    valor numeric(12,2) not null check (valor >= 0),
    descricao text not null,
    forma_pagamento text,
    status public.status_geral not null default 'pendente',
    responsavel_pessoa_id uuid references public.pessoas(id),
    observacoes text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.conteudos (
    id uuid primary key default gen_random_uuid(),
    tema text not null,
    tipo text not null default 'Outro',
    roteiro text,
    status public.conteudo_status not null default 'ideia',
    canal text,
    data_publicacao date,
    views integer not null default 0 check (views >= 0),
    engajamento integer not null default 0 check (engajamento >= 0),
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.comunicacoes (
    id uuid primary key default gen_random_uuid(),
    titulo text not null,
    tipo text not null default 'Outro',
    canal text not null default 'WhatsApp',
    publico_alvo text,
    mensagem text,
    status public.conteudo_status not null default 'ideia',
    botconversa_flow_id bigint,
    botconversa_sequence_id bigint,
    botconversa_campaign_id bigint,
    data_programada timestamptz,
    data_envio timestamptz,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.botconversa_config (
    chave text primary key,
    valor text,
    descricao text,
    atualizado_em timestamptz not null default now()
);

create table if not exists public.webhook_events (
    id uuid primary key default gen_random_uuid(),
    provider text not null,
    event_type text not null,
    external_id text,
    payload jsonb not null default '{}'::jsonb,
    status text not null default 'recebido' check (status in ('recebido', 'processando', 'sucesso', 'erro', 'ignorado')),
    resultado text,
    recebido_em timestamptz not null default now(),
    processado_em timestamptz,
    criado_em timestamptz not null default now()
);

create table if not exists public.integration_logs (
    id uuid primary key default gen_random_uuid(),
    integracao text not null,
    acao text not null,
    entidade_tipo text,
    entidade_id text,
    payload jsonb,
    status text not null default 'pendente' check (status in ('sucesso', 'erro', 'pendente')),
    resultado text,
    criado_em timestamptz not null default now()
);

create table if not exists public.drive_sources (
    id uuid primary key default gen_random_uuid(),
    nome text not null,
    drive_folder_id text not null unique,
    area text,
    ativo boolean not null default true,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.drive_files (
    id uuid primary key default gen_random_uuid(),
    drive_file_id text not null unique,
    source_id uuid references public.drive_sources(id) on delete set null,
    nome text not null,
    mime_type text,
    web_view_link text,
    modified_time timestamptz,
    size_bytes bigint,
    checksum text,
    status public.conhecimento_status not null default 'bruto',
    resumo text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.document_chunks (
    id uuid primary key default gen_random_uuid(),
    drive_file_id uuid references public.drive_files(id) on delete cascade,
    chunk_index integer not null,
    conteudo text not null,
    embedding extensions.vector(1536),
    metadata jsonb not null default '{}'::jsonb,
    criado_em timestamptz not null default now(),
    unique (drive_file_id, chunk_index)
);

create table if not exists public.knowledge_items (
    id uuid primary key default gen_random_uuid(),
    titulo text not null,
    area text,
    conteudo text not null,
    fonte_tipo text,
    fonte_id uuid,
    status public.conhecimento_status not null default 'pendente_aprovacao',
    aprovado_por uuid references public.pessoas(id),
    aprovado_em timestamptz,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.agent_tasks (
    id uuid primary key default gen_random_uuid(),
    agente text not null,
    tipo text not null,
    titulo text not null,
    payload jsonb not null default '{}'::jsonb,
    status text not null default 'pendente' check (status in ('pendente', 'rodando', 'sucesso', 'erro', 'cancelado')),
    prioridade integer not null default 5 check (prioridade between 1 and 10),
    agendado_para timestamptz,
    iniciado_em timestamptz,
    concluido_em timestamptz,
    resultado text,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.agent_runs (
    id uuid primary key default gen_random_uuid(),
    task_id uuid references public.agent_tasks(id) on delete set null,
    agente text not null,
    status text not null,
    entrada jsonb,
    saida jsonb,
    erro text,
    iniciado_em timestamptz not null default now(),
    concluido_em timestamptz
);

create table if not exists public.agent_feedback (
    id uuid primary key default gen_random_uuid(),
    run_id uuid references public.agent_runs(id) on delete cascade,
    nota integer check (nota between 1 and 10),
    feedback text,
    criado_por uuid references public.pessoas(id),
    criado_em timestamptz not null default now()
);

create table if not exists public.audit_log (
    id uuid primary key default gen_random_uuid(),
    ator_tipo text not null default 'sistema',
    ator_id uuid,
    acao text not null,
    tabela text,
    registro_id text,
    dados jsonb,
    criado_em timestamptz not null default now()
);

create table if not exists public.system_health_checks (
    id uuid primary key default gen_random_uuid(),
    componente text not null,
    status text not null check (status in ('ok', 'alerta', 'erro')),
    detalhes text,
    checked_at timestamptz not null default now()
);

create index if not exists idx_pessoa_contatos_valor on public.pessoa_contatos(valor);
create index if not exists idx_membros_botconversa_subscriber_id on public.membros(botconversa_subscriber_id);
create index if not exists idx_visitantes_botconversa_subscriber_id on public.visitantes(botconversa_subscriber_id);
create index if not exists idx_relatorios_celulas_data on public.relatorios_celulas(data_relatorio);
create index if not exists idx_consolidacao_status on public.consolidacao_visitantes(status);
create index if not exists idx_compromissos_data_inicio on public.compromissos(data_inicio);
create index if not exists idx_webhook_events_status on public.webhook_events(status);
create index if not exists idx_webhook_events_provider_type on public.webhook_events(provider, event_type);
create index if not exists idx_drive_files_drive_file_id on public.drive_files(drive_file_id);
create index if not exists idx_agent_tasks_status on public.agent_tasks(status);
create index if not exists idx_financeiro_lancamentos_data on public.financeiro_lancamentos(data_lancamento);

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'pessoas',
        'pessoa_contatos',
        'enderecos',
        'membros',
        'visitantes',
        'consentimentos',
        'ministerios',
        'ministerio_membros',
        'celulas',
        'celula_membros',
        'relatorios_celulas',
        'consolidacao_visitantes',
        'consolidacao_acoes',
        'pedidos_oracao',
        'pedidos_aconselhamento',
        'pedidos_celula',
        'compromissos',
        'eventos',
        'evento_inscricoes',
        'google_calendar_sync_state',
        'financeiro_contas',
        'financeiro_categorias',
        'financeiro_lancamentos',
        'conteudos',
        'comunicacoes',
        'botconversa_config',
        'webhook_events',
        'integration_logs',
        'drive_sources',
        'drive_files',
        'document_chunks',
        'knowledge_items',
        'agent_tasks',
        'agent_runs',
        'agent_feedback',
        'audit_log',
        'system_health_checks'
    ] loop
        execute format('alter table public.%I enable row level security', table_name);
    end loop;
end $$;

do $$
declare
    table_name text;
begin
    foreach table_name in array array[
        'pessoas',
        'pessoa_contatos',
        'enderecos',
        'membros',
        'visitantes',
        'ministerios',
        'ministerio_membros',
        'celulas',
        'celula_membros',
        'relatorios_celulas',
        'consolidacao_visitantes',
        'pedidos_oracao',
        'pedidos_aconselhamento',
        'pedidos_celula',
        'compromissos',
        'eventos',
        'evento_inscricoes',
        'financeiro_contas',
        'financeiro_categorias',
        'financeiro_lancamentos',
        'conteudos',
        'comunicacoes',
        'drive_sources',
        'drive_files',
        'knowledge_items',
        'agent_tasks'
    ] loop
        execute format('drop trigger if exists trg_%I_updated_at on public.%I', table_name, table_name);
        execute format(
            'create trigger trg_%I_updated_at before update on public.%I for each row execute function public.set_updated_at()',
            table_name,
            table_name
        );
    end loop;
end $$;

