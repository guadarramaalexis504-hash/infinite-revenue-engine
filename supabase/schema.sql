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

alter table public.opportunities
    add column if not exists problem text not null default '',
    add column if not exists channel text not null default 'technical_answer_draft',
    add column if not exists payout_estimate_usd numeric(10, 2) not null default 0,
    add column if not exists conversion_probability numeric(6, 4) not null default 0,
    add column if not exists estimated_cost_usd numeric(10, 2) not null default 0,
    add column if not exists risk_penalty_usd numeric(10, 2) not null default 0,
    add column if not exists build_minutes integer not null default 0,
    add column if not exists expected_value_usd numeric(10, 2) not null default 0;

create table if not exists public.revenue_milestones (
    id uuid primary key default gen_random_uuid(),
    amount_usd numeric(12, 2) not null unique,
    label text not null,
    reached_at timestamptz,
    created_at timestamptz not null default now()
);

create table if not exists public.channels (
    id uuid primary key default gen_random_uuid(),
    channel_key text not null unique,
    name text not null,
    status text not null default 'active',
    allowed_publication_modes text[] not null default array['manual_review'],
    created_at timestamptz not null default now()
);

create table if not exists public.assets (
    id uuid primary key default gen_random_uuid(),
    opportunity_id uuid references public.opportunities(id) on delete set null,
    asset_type text not null,
    title text not null,
    body_markdown text not null default '',
    channel text not null,
    status text not null default 'draft' check (status in ('draft', 'approved', 'published', 'failed', 'discarded')),
    publication_mode text not null default 'manual_review',
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create table if not exists public.offers (
    id uuid primary key default gen_random_uuid(),
    opportunity_id uuid references public.opportunities(id) on delete set null,
    asset_id uuid references public.assets(id) on delete set null,
    channel text not null,
    title text not null,
    price_usd numeric(10, 2) not null default 0,
    payment_url text,
    status text not null default 'draft',
    created_at timestamptz not null default now()
);

create table if not exists public.click_events (
    id uuid primary key default gen_random_uuid(),
    offer_id uuid references public.offers(id) on delete set null,
    source text not null,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now()
);

create table if not exists public.conversion_events (
    id uuid primary key default gen_random_uuid(),
    offer_id uuid references public.offers(id) on delete set null,
    source text not null,
    external_id text,
    amount_usd numeric(10, 2) not null check (amount_usd >= 0),
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    unique (source, external_id)
);

create table if not exists public.experiments (
    id uuid primary key default gen_random_uuid(),
    opportunity_id uuid references public.opportunities(id) on delete set null,
    name text not null,
    status text not null default 'planned' check (status in ('planned', 'running', 'won', 'lost', 'paused')),
    hypothesis text not null default '',
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

alter table public.offers
    add column if not exists opportunity_id uuid references public.opportunities(id) on delete set null;

create table if not exists public.launch_tasks (
    id uuid primary key default gen_random_uuid(),
    opportunity_id uuid references public.opportunities(id) on delete set null,
    priority integer not null default 100,
    category text not null,
    title text not null,
    detail text not null default '',
    status text not null default 'pending' check (status in ('blocked', 'pending', 'running', 'done', 'skipped')),
    blocking boolean not null default false,
    source text,
    external_id text,
    channel text,
    expected_value_usd numeric(10, 2) not null default 0,
    payload jsonb not null default '{}'::jsonb,
    created_at timestamptz not null default now(),
    updated_at timestamptz not null default now()
);

create index if not exists opportunities_expected_value_idx
    on public.opportunities(expected_value_usd desc);

create index if not exists assets_status_channel_idx
    on public.assets(status, channel);

create index if not exists conversion_events_source_created_at_idx
    on public.conversion_events(source, created_at desc);

create index if not exists launch_tasks_status_priority_idx
    on public.launch_tasks(status, priority, expected_value_usd desc);

insert into public.revenue_milestones(amount_usd, label)
values
    (15, 'First proof'),
    (200, 'Useful side income'),
    (1000, 'Repeatable loop'),
    (20000, 'Major target')
on conflict (amount_usd) do nothing;

insert into public.channels(channel_key, name)
values
    ('microtool_seo', 'Microtools SEO'),
    ('github_issue_helper', 'GitHub issue helper'),
    ('digital_product', 'Digital products'),
    ('article_affiliate', 'Affiliate content'),
    ('open_source_sponsorship', 'Open-source sponsorship'),
    ('paid_setup_kit', 'Paid setup kits'),
    ('bounty_scanner', 'Bounty scanner'),
    ('lead_magnet', 'Lead magnet'),
    ('niche_report', 'Niche report')
on conflict (channel_key) do nothing;

alter table public.runs enable row level security;
alter table public.opportunities enable row level security;
alter table public.drafts enable row level security;
alter table public.events enable row level security;
alter table public.tip_events enable row level security;
alter table public.revenue_milestones enable row level security;
alter table public.channels enable row level security;
alter table public.assets enable row level security;
alter table public.offers enable row level security;
alter table public.click_events enable row level security;
alter table public.conversion_events enable row level security;
alter table public.experiments enable row level security;
alter table public.launch_tasks enable row level security;
