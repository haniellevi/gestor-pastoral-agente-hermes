-- Hermes 2.0 MVP operational layer.
-- Supabase CLI was unavailable in this workspace, so this migration keeps the
-- existing timestamped format used by the project.

create table if not exists public.event_logs (
    id uuid primary key default gen_random_uuid(),
    provider text not null default 'botconversa',
    event_type text not null default 'mensagem',
    idempotency_key text not null unique,
    external_id text,
    payload jsonb not null default '{}'::jsonb,
    status text not null default 'recebido'
        check (status in ('recebido', 'processado', 'erro', 'ignorado')),
    resultado jsonb,
    criado_em timestamptz not null default now(),
    processado_em timestamptz
);

create table if not exists public.inbox_pastoral (
    id uuid primary key default gen_random_uuid(),
    event_log_id uuid references public.event_logs(id) on delete set null,
    pessoa_id uuid references public.pessoas(id) on delete set null,
    subscriber_id bigint,
    nome text,
    telefone text,
    origem text not null default 'BotConversa',
    fluxo_origem text,
    tipo_evento text,
    papel_responsavel text not null default 'Rute'
        check (papel_responsavel in ('Rute', 'Caleb', 'Neemias', 'Barnabe', 'Hermes')),
    intencao text not null default 'outro',
    status text not null default 'Novo'
        check (status in ('Novo', 'Em triagem', 'Encaminhado', 'Resolvido', 'Arquivado')),
    nivel_urgencia text not null default 'Normal'
        check (nivel_urgencia in ('Baixa', 'Normal', 'Alta', 'Urgente')),
    prioridade integer not null default 5 check (prioridade between 1 and 10),
    mensagem text,
    resumo text,
    campos jsonb not null default '{}'::jsonb,
    prazo_resposta timestamptz,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create table if not exists public.tarefas_pastorais (
    id uuid primary key default gen_random_uuid(),
    inbox_id uuid references public.inbox_pastoral(id) on delete set null,
    pessoa_id uuid references public.pessoas(id) on delete set null,
    titulo text not null,
    tipo text not null,
    responsavel text not null default 'Rute'
        check (responsavel in ('Rute', 'Caleb', 'Neemias', 'Barnabe', 'Hermes')),
    status text not null default 'Pendente'
        check (status in ('Pendente', 'Em andamento', 'Concluida', 'Cancelada', 'Arquivada')),
    prioridade integer not null default 5 check (prioridade between 1 and 10),
    prazo_para timestamptz,
    payload jsonb not null default '{}'::jsonb,
    concluido_em timestamptz,
    criado_em timestamptz not null default now(),
    atualizado_em timestamptz not null default now()
);

create index if not exists idx_event_logs_idempotency_key on public.event_logs(idempotency_key);
create index if not exists idx_inbox_pastoral_status on public.inbox_pastoral(status);
create index if not exists idx_inbox_pastoral_intencao on public.inbox_pastoral(intencao);
create index if not exists idx_inbox_pastoral_criado_em on public.inbox_pastoral(criado_em desc);
create index if not exists idx_tarefas_pastorais_status on public.tarefas_pastorais(status);
create index if not exists idx_tarefas_pastorais_prazo on public.tarefas_pastorais(prazo_para);

create or replace function public.set_updated_at()
returns trigger
language plpgsql
as $$
begin
    new.atualizado_em = now();
    return new;
end;
$$;

alter table public.event_logs enable row level security;
alter table public.inbox_pastoral enable row level security;
alter table public.tarefas_pastorais enable row level security;

drop policy if exists service_role_all_event_logs on public.event_logs;
create policy service_role_all_event_logs
on public.event_logs
for all
to service_role
using (true)
with check (true);

drop policy if exists service_role_all_inbox_pastoral on public.inbox_pastoral;
create policy service_role_all_inbox_pastoral
on public.inbox_pastoral
for all
to service_role
using (true)
with check (true);

drop policy if exists service_role_all_tarefas_pastorais on public.tarefas_pastorais;
create policy service_role_all_tarefas_pastorais
on public.tarefas_pastorais
for all
to service_role
using (true)
with check (true);

grant select, insert, update, delete on public.event_logs to service_role;
grant select, insert, update, delete on public.inbox_pastoral to service_role;
grant select, insert, update, delete on public.tarefas_pastorais to service_role;

drop trigger if exists trg_inbox_pastoral_updated_at on public.inbox_pastoral;
create trigger trg_inbox_pastoral_updated_at
before update on public.inbox_pastoral
for each row execute function public.set_updated_at();

drop trigger if exists trg_tarefas_pastorais_updated_at on public.tarefas_pastorais;
create trigger trg_tarefas_pastorais_updated_at
before update on public.tarefas_pastorais
for each row execute function public.set_updated_at();
