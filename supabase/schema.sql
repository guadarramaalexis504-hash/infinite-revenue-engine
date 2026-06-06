create extension if not exists pgcrypto;

create table if not exists public.runs (
    id uuid primary key default gen_random_uuid(),
    started_at timestamptz not null default now(),
    finished_at timestamptz,
    status text not null check (status in ('running', 'success', 'monitoring', 'error')),
    error text
);

create table if not exists public.opportunities (
    id uuid primary key default gen_random_uuid(),
    source text not null,
    external_id text not null,
    title text not null,
    url text not null,
    tags text[] not null default '{}',
    score integer not null check (score >= 0 and score <= 100),
    status text not null default 'new',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now(),
    unique (source, external_id)
);

create table if not exists public.drafts (
    id uuid primary key default gen_random_uuid(),
    opportunity_id uuid not null references public.opportunities(id) on delete cascade,
    answer_markdown text not null,
    code_snippet text not null default '',
    status text not null default 'draft' check (status in ('draft', 'approved', 'posted', 'discarded')),
    created_at timestamptz not null default now()
);

create table if not exists public.events (
    id uuid primary key default gen_random_uuid(),
    run_id uuid references public.runs(id) on delete set null,
    event_type text not null,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.tip_events (
    id uuid primary key default gen_random_uuid(),
    provider text not null,
    external_id text not null,
    amount_usd numeric(10, 2) not null check (amount_usd >= 0),
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (provider, external_id)
);

create index if not exists opportunities_status_score_idx
    on public.opportunities(status, score desc);

create index if not exists drafts_opportunity_id_idx
    on public.drafts(opportunity_id);

create index if not exists events_run_id_created_at_idx
    on public.events(run_id, created_at desc);

create index if not exists tip_events_created_at_idx
    on public.tip_events(created_at desc);

alter table public.runs enable row level security;
alter table public.opportunities enable row level security;
alter table public.drafts enable row level security;
alter table public.events enable row level security;
alter table public.tip_events enable row level security;
