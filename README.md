# Infinite Revenue Engine

Python loop for finding revenue opportunities, generating reviewable assets, and tracking optional tips/conversions toward milestones like 15, 200, 1000, and 20000 USD. It keeps running after each milestone by default, so totals can keep accumulating. It does not scrape HTML, auto-post to forums, or execute payment-gated spam.

## Runtime

Install dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run one safe dry run:

```powershell
python -m farm_loop.main --once --dry-run
```

Run continuously locally:

```powershell
python -m farm_loop.main --loop --interval-seconds 300
```

Run one V2 portfolio cycle:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase discover --dry-run
```

GitHub Actions runs portfolio phases through `.github/workflows/farm-loop.yml`:

- every 5 minutes: discover and score opportunities
- hourly: generate top reviewable assets
- daily: summarize portfolio progress
- weekly: prune low-performing loops

## One-Command Automation

From PowerShell:

```powershell
.\scripts\bootstrap.ps1
```

That creates `.env` from `.env.example` when needed, creates `.venv`, installs dependencies, runs tests, and runs one safe dry-run.

After filling `.env` with real credentials, configure GitHub repository secrets automatically:

```powershell
.\scripts\configure-github.ps1 -RunWorkflow
```

If `.env` also includes `DATABASE_URL` and `psql` is installed, apply the Supabase schema automatically:

```powershell
.\scripts\bootstrap.ps1 -ApplySchema
```

Start the local infinite loop:

```powershell
.\scripts\run-local-loop.ps1 -IntervalSeconds 300
```

## Required Secrets

Set these in GitHub repository secrets:

- `SUPABASE_URL`
- `SUPABASE_KEY`
- `OPENAI_API_KEY`
- `STACKEXCHANGE_KEY`
- `BUYMEACOFFEE_WEBHOOK_TOKEN`
- `TIP_URL`

Optional environment variables:

- `TARGET_USD`, default `15`
- `REVENUE_MILESTONES`, default `15,200,1000,20000`
- `STOP_AFTER_TARGET`, default `false`
- `MAX_DRAFTS_PER_RUN`, default `3`
- `STACKEXCHANGE_TAGS`, default `python;fastapi;supabase;openai-api`
- `OPENAI_MODEL`, default `gpt-4o-mini`
- `GITHUB_TOKEN`, optional but recommended for GitHub API rate limits
- `KEYWORD_CSV_PATH`, default `data/revenue_keywords.csv`

## Supabase Setup

Run `supabase/schema.sql` in the Supabase SQL editor. The schema defines:

- `runs`: one row per loop execution.
- `opportunities`: deduplicated by `(source, external_id)`.
- `drafts`: generated answer drafts, default status `draft`.
- `events`: structured logs for each run.
- `tip_events`: confirmed Buy Me a Coffee events, deduplicated by `(provider, external_id)`.
- `revenue_milestones`: milestone definitions such as 15, 200, 1000, and 20000.
- `channels`: allowed revenue lanes such as microtools, GitHub issue helper, digital products, affiliates, and paid setup kits.
- `assets`: reviewable generated assets: microtool specs, article outlines, patch plans, product listings, landing copy, support offers.
- `offers`, `click_events`, `conversion_events`, `experiments`: monetization and learning loop tracking.

## Safety Rules

- Stack Overflow and Stack Exchange are discovery sources only. Do not publish AI-generated answers there.
- Public publishing is manual review only.
- Use owned sites, owned repos, newsletters, Gumroad/Lemon Squeezy/Stripe, Buy Me a Coffee, or GitHub Sponsors for monetization.
- `aipickd` is off-limits. Current Supabase target is `Sonident`.

## Exact API Requests

Stack Exchange discovery:

```http
GET https://api.stackexchange.com/2.3/search/advanced?site=stackoverflow&order=desc&sort=activity&accepted=False&answers=0&closed=False&tagged=python;fastapi;supabase;openai-api&pagesize=20&filter=withbody&key=<STACKEXCHANGE_KEY>
```

OpenAI draft generation:

```http
POST https://api.openai.com/v1/responses
Authorization: Bearer <OPENAI_API_KEY>
Content-Type: application/json
```

Supabase event insert:

```http
POST <SUPABASE_URL>/rest/v1/events
apikey: <SUPABASE_KEY>
Authorization: Bearer <SUPABASE_KEY>
Content-Type: application/json
Prefer: return=representation
```

Supabase opportunity upsert:

```http
POST <SUPABASE_URL>/rest/v1/opportunities?on_conflict=source,external_id
apikey: <SUPABASE_KEY>
Authorization: Bearer <SUPABASE_KEY>
Content-Type: application/json
Prefer: resolution=merge-duplicates,return=representation
```

Supabase tip event insert:

```http
POST <SUPABASE_URL>/rest/v1/tip_events
apikey: <SUPABASE_KEY>
Authorization: Bearer <SUPABASE_KEY>
Content-Type: application/json
Prefer: return=representation
```

## Buy Me a Coffee Webhooks

Configure Buy Me a Coffee to send events to your own HTTPS endpoint. In that endpoint, call the reusable handler:

```python
from farm_loop.webhook_handler import handle_buymeacoffee_webhook
from farm_loop.supabase_client import SupabaseClient

handle_buymeacoffee_webhook(
    headers=request_headers,
    payload=request_json,
    expected_token=BUYMEACOFFEE_WEBHOOK_TOKEN,
    supabase=SupabaseClient(SUPABASE_URL, SUPABASE_KEY),
)
```

The loop logs a `target_reached` event once `sum(tip_events.amount_usd) >= TARGET_USD`, but it keeps generating new drafts by default. Set `STOP_AFTER_TARGET=true` or pass `--stop-after-target` only if you want it to pause after the milestone.

## Tests

```powershell
python -m unittest discover -s tests -v
```
