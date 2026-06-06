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

Export reviewable local assets from the portfolio:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --asset-output-dir out/revenue-assets
```

Generate an owned static site from the same selected opportunities:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --site-output-dir out/site
```

Generate a prioritized launch queue from the selected opportunities:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --launch-queue-output-dir out/launch-queue
```

The launch queue writes `launch_queue.json` and `LAUNCH_QUEUE.md` with activation blockers, manual review tasks, owned publishing tasks, payment/support CTA tasks, and measurement tasks.

Generate interactive microtools for supported opportunities:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --microtool-output-dir out/microtools
```

The first supported interactive microtools are a Supabase RLS policy checker and a GitHub Actions YAML checker. They are static HTML files for owned channels and still require manual review before publishing.

The GitHub Pages workflow writes those microtools under `out/site/tools` so they are included in the deployed Pages artifact with the owned static site.

Support links on generated pages include attribution parameters such as `utm_campaign=<external_id>` plus `ire_source` and `ire_external_id`, so future analytics or webhook handlers can tie clicks/conversions back to a specific opportunity.

If `CLICK_REDIRECT_URL` is set, support links point to your owned click redirect endpoint first, so clicks can be saved to Supabase `click_events` before sending the visitor to the final support/payment URL.

GitHub Actions runs portfolio phases through `.github/workflows/farm-loop.yml`:

- every 5 minutes: discover and score opportunities
- hourly: generate top reviewable assets
- daily: summarize portfolio progress
- weekly: prune low-performing loops

`.github/workflows/pages-site.yml` builds the owned static site and deploys it to GitHub Pages through GitHub's official Pages Actions. It runs manually and once per day after Pages is configured for GitHub Actions in the repository settings.

## One-Command Automation

From PowerShell:

```powershell
.\scripts\bootstrap.ps1
```

That creates `.env` from `.env.example` when needed, creates `.venv`, installs dependencies, runs tests, and runs one safe dry-run.

Check exactly what is still blocking live automation:

```powershell
.\scripts\doctor.ps1
```

After filling `.env` with real credentials, configure GitHub repository secrets automatically:

```powershell
.\scripts\configure-github.ps1 -RunWorkflow
```

If this local clone does not have a git remote yet, pass the repository explicitly:

```powershell
.\scripts\configure-github.ps1 -Repo owner/repo -RunWorkflow
```

If `.env` also includes `DATABASE_URL` and `psql` is installed, apply the Supabase schema automatically:

```powershell
.\scripts\bootstrap.ps1 -ApplySchema
```

Start the local infinite loop:

```powershell
.\scripts\run-local-loop.ps1 -IntervalSeconds 300
```

Generate the owned site locally before pushing:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 12 --site-output-dir out/site
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
- `IDEA_CATALOG_PATH`, default `data/revenue_ideas.json`
- `ASSET_OUTPUT_DIR`, optional local manual-review export path such as `out/revenue-assets`
- `SITE_OUTPUT_DIR`, optional owned static site export path such as `out/site`
- `CLICK_REDIRECT_URL`, optional owned click redirect endpoint such as `https://your-domain.example/click`
- `LAUNCH_QUEUE_OUTPUT_DIR`, optional launch queue export path such as `out/launch-queue`
- `MICROTOOL_OUTPUT_DIR`, optional interactive microtool export path such as `out/microtools`

`scripts/configure-github.ps1` sets the required secrets and also sets `CLICK_REDIRECT_URL` when it is present and not a placeholder. The GitHub Actions workflow uses GitHub's built-in `github.token` for issue discovery rate limits.

## Click Redirect Handler

Host a small HTTPS endpoint and call the reusable handler with a server-side Supabase key:

```python
from farm_loop.click_handler import handle_click_redirect
from farm_loop.supabase_client import SupabaseClient

result = handle_click_redirect(
    query=request_args,
    supabase=SupabaseClient(SUPABASE_URL, SUPABASE_KEY),
    allowed_target_hosts={"buymeacoffee.com"},
)
return redirect(result["location"])
```

The handler rejects non-HTTPS targets and hosts outside the allowlist.

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
- `launch_tasks`: prioritized manual launch tasks for review, publishing, monetization, and measurement.

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
