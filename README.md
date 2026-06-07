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

The site includes an index, one page per opportunity, `offers/index.html` as a central owned-channel offer catalog, `intake/index.html` for paid setup/service requests, plus `sitemap.xml` and `robots.txt`. Set `SITE_BASE_URL` before publishing so search engines receive absolute sitemap URLs. Set `SERVICE_INTAKE_URL` to a Tally, Google Form, Calendly, Stripe Payment Link, or other owned intake path before publishing service CTAs.

Generate a prioritized launch queue from the selected opportunities:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --launch-queue-output-dir out/launch-queue
```

The launch queue writes `launch_queue.json` and `LAUNCH_QUEUE.md` with activation blockers, manual review tasks, owned publishing tasks, payment/support CTA tasks, and measurement tasks. When exported from the CLI, it runs the same activation preflight as `scripts/doctor.ps1`, so missing credentials, placeholder secrets, absent git remote, or missing `gh` auth become top-priority tasks.

Generate monetizable offer drafts:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --offer-output-dir out/offers
```

The offer catalog writes `offers.json` and `OFFERS.md` with draft prices, CTA labels, and owned-channel descriptions for support, setup services, digital products, and sponsorship-style offers.

Generate a ranked opportunity roadmap for every discovered idea:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --roadmap-output-dir out/roadmap
```

The opportunity roadmap writes `opportunity_roadmap.json` and `OPPORTUNITY_ROADMAP.md` with activation blockers, channel summary, milestone plan, and all ranked ideas so the engine keeps a long backlog toward 20000 USD.

Generate an activation manifest with exact next files and commands:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --activation-manifest-output-dir out/activation
```

The activation manifest writes `activation_manifest.json`, `ACTIVATE_NOW.md`, `RUNBOOK.md`, and `CLAUDE_HANDOFF.md`. It links each selected opportunity to local review files, owned pages, checkout setup, tracking deploy docs, offer keys, dry-run conversion commands, and safe handoff instructions for another coding agent.

Generate an offer-level revenue forecast:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --revenue-forecast-output-dir out/revenue-forecast
```

The revenue forecast writes `revenue_forecast.json` and `REVENUE_FORECAST.md` with the number of conversions each generated offer needs to reach `$15`, `$200`, `$1,000`, and `$20,000`. It is a planning artifact, not an income guarantee.

Generate higher-ticket offer ladders:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --offer-ladder-output-dir out/offer-ladder
```

The offer ladder writes `offer_ladder.json` and `OFFER_LADDER.md`. It turns one opportunity into support, starter setup, fixed-scope service, and premium sprint tiers, so the system can prioritize paths where `$20,000` means tens of sales instead of thousands of tips.

Generate the full local revenue bundle in one command:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --bundle-output-dir out/revenue-bundle
```

The revenue bundle writes review assets, the owned site, interactive tools under `site/tools`, offer drafts, checkout setup, tracking deploy files, lead magnets, digital product packs, service packages, niche reports, affiliate article drafts, sponsor repo kits, the opportunity roadmap, activation manifest, revenue forecast, offer ladder, and the launch queue using one standard folder tree.

Record a confirmed sale from any payment path:

```powershell
python -m farm_loop.main --record-conversion --conversion-provider gumroad --conversion-external-id sale-123 --conversion-amount-usd 29 --conversion-source digital_product --conversion-offer-id offer-id
```

Use `--dry-run` first to verify the payload without writing to Supabase. Conversion external ids are stored as `<provider>:<id>` so Stripe, Gumroad, Lemon Squeezy, manual invoices, and other providers can share `conversion_events` safely. If you do not know the Supabase offer UUID, pass `--conversion-offer-key source:external_id:offer_type` so dashboards and pruning can still attribute the sale.

Generate interactive microtools for supported opportunities:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --microtool-output-dir out/microtools
```

The first supported interactive microtools are a Supabase RLS policy checker and a GitHub Actions YAML checker. They are static HTML files for owned channels and still require manual review before publishing.

The GitHub Pages workflow writes those microtools under `out/site/tools` so they are included in the deployed Pages artifact with the owned static site.

Support links on generated pages include attribution parameters such as `utm_campaign=<external_id>` plus `ire_source`, `ire_external_id`, and offer CTAs include `ire_offer_key`, so future analytics or webhook handlers can tie clicks/conversions back to a specific opportunity and offer.

If `CLICK_REDIRECT_URL` is set, support links point to your owned click redirect endpoint first, so clicks can be saved to Supabase `click_events` before sending the visitor to the final support/payment URL.

GitHub Actions runs portfolio phases through `.github/workflows/farm-loop.yml`:

- every 5 minutes: discover and score opportunities
- hourly: generate top reviewable assets
- daily: summarize portfolio progress into `portfolio_snapshots`
- weekly: prune low-performing loops by marking revenue winners, pausing stale zero-signal experiments, and creating offer-revision tasks when clicks do not convert

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
- `SITE_BASE_URL`, optional public site URL used in `sitemap.xml` and `robots.txt`
- `CLICK_REDIRECT_URL`, optional owned click redirect endpoint such as `https://your-domain.example/click`
- `CLICK_ALLOWED_HOSTS`, comma-separated final redirect host allowlist, default `buymeacoffee.com,www.buymeacoffee.com`
- `CONVERSION_WEBHOOK_TOKEN`, optional shared token for your owned conversion webhook endpoint
- `SERVICE_INTAKE_URL`, optional setup/service intake form URL used by service CTAs
- `OFFER_PAYMENT_URLS`, optional comma-separated checkout links such as `fixed_scope_service=https://buy.stripe.com/...,digital_product=https://gumroad.com/l/...`
- `LAUNCH_QUEUE_OUTPUT_DIR`, optional launch queue export path such as `out/launch-queue`
- `MICROTOOL_OUTPUT_DIR`, optional interactive microtool export path such as `out/microtools`
- `OFFER_OUTPUT_DIR`, optional offer catalog export path such as `out/offers`
- `CHECKOUT_SETUP_OUTPUT_DIR`, optional checkout setup export path such as `out/checkout-setup`
- `CONVERSION_WEBHOOK_BASE_URL`, optional public webhook base such as `https://your-domain.example/webhooks/conversion`
- `TRACKING_DEPLOY_OUTPUT_DIR`, optional server-side tracking app deploy bundle path such as `out/tracking-deploy`
- `TRACKING_PUBLIC_BASE_URL`, optional public tracking app base URL such as `https://track.your-domain.example`
- `LEAD_MAGNET_OUTPUT_DIR`, optional lead magnet export path such as `out/lead-magnets`
- `LEAD_CAPTURE_URL`, optional owned opt-in form or newsletter URL used by lead magnet CTAs
- `DIGITAL_PRODUCT_OUTPUT_DIR`, optional digital product pack export path such as `out/digital-products`
- `SERVICE_PACKAGE_OUTPUT_DIR`, optional fixed-scope service package export path such as `out/service-packages`
- `NICHE_REPORT_OUTPUT_DIR`, optional paid niche report export path such as `out/niche-reports`
- `AFFILIATE_ARTICLE_OUTPUT_DIR`, optional affiliate article export path such as `out/affiliate-articles`
- `AFFILIATE_URLS`, optional comma-separated tag=url or *=url affiliate links
- `SPONSOR_REPO_OUTPUT_DIR`, optional GitHub Sponsors repo kit export path such as `out/sponsor-repos`
- `SPONSOR_URLS`, optional comma-separated tag=url, github=url, sponsorship=url, or *=url sponsor links
- `ROADMAP_OUTPUT_DIR`, optional ranked opportunity roadmap path such as `out/roadmap`
- `ACTIVATION_MANIFEST_OUTPUT_DIR`, optional launch activation manifest path such as `out/activation`
- `REVENUE_FORECAST_OUTPUT_DIR`, optional offer-level milestone forecast path such as `out/revenue-forecast`
- `OFFER_LADDER_OUTPUT_DIR`, optional higher-ticket offer ladder path such as `out/offer-ladder`
- `BUNDLE_OUTPUT_DIR`, optional all-in-one local revenue bundle path such as `out/revenue-bundle`

`scripts/configure-github.ps1` sets the required secrets and also sets optional activation secrets such as `CLICK_REDIRECT_URL`, `CONVERSION_WEBHOOK_TOKEN`, `SERVICE_INTAKE_URL`, `SITE_BASE_URL`, `OFFER_PAYMENT_URLS`, `CONVERSION_WEBHOOK_BASE_URL`, `TRACKING_PUBLIC_BASE_URL`, `LEAD_CAPTURE_URL`, `AFFILIATE_URLS`, and `SPONSOR_URLS` when present and not placeholders. The GitHub Actions workflow uses GitHub's built-in `github.token` for issue discovery rate limits.

## Tracking HTTP App

Run the built-in tracking HTTP app locally:

```powershell
python -m farm_loop.http_app --host 127.0.0.1 --port 8080
```

Endpoints:

- `GET /health`: returns `{"status":"ok"}`.
- `GET /click`: records a `click_events` row, inserts a `click_recorded` event, then redirects to the validated `target` URL.
- `POST /webhooks/buymeacoffee`: validates `X-BuyMeACoffee-Token`, records `tip_events`, and updates revenue progress.
- `POST /webhooks/conversion/<provider>`: validates `X-Revenue-Webhook-Token`, records `conversion_events`, and attributes revenue to an offer/source when provider metadata includes it.

Deploy this app only on a server-side HTTPS host with `SUPABASE_URL`, `SUPABASE_KEY`, `BUYMEACOFFEE_WEBHOOK_TOKEN`, `CONVERSION_WEBHOOK_TOKEN`, and `CLICK_ALLOWED_HOSTS` configured. Do not expose the Supabase server-side key in browser JavaScript.

## Offer Payment Links

Use `OFFER_PAYMENT_URLS` to route each generated offer type to a real checkout while keeping attribution:

```powershell
$env:OFFER_PAYMENT_URLS="support=https://www.buymeacoffee.com/your-handle,fixed_scope_service=https://buy.stripe.com/setup,digital_product=https://gumroad.com/l/template,sponsorship=https://github.com/sponsors/your-handle"
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --site-output-dir out/site --offer-output-dir out/offers
```

Supported keys are offer types such as `support`, `setup_service`, `fixed_scope_service`, `digital_product`, and `sponsorship`; channel keys such as `microtool_seo` also work, and `*` is a default fallback. When `CLICK_REDIRECT_URL` is set, generated offer CTAs route through `/click` before the checkout so `click_events` can be recorded.

Every generated offer also has a stable `offer_key` in the form `source:external_id:offer_type`. The site appends it to checkout URLs as `ire_offer_key`, stores it in `click_events.payload.offer_key`, and accepts it back from conversion webhooks through provider metadata such as `offer_key` or `ire_offer_key`. Use this when Stripe, Gumroad, or another provider cannot send the internal Supabase `offers.id`.

Export copy-paste checkout setup instructions:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --checkout-setup-output-dir out/checkout-setup --conversion-webhook-base-url https://your-domain.example/webhooks/conversion
```

This writes `checkout_setup.json` and `CHECKOUT_SETUP.md` with metadata keys, provider webhook URLs, and manual conversion fallback commands for each generated offer.

Provider details are included in `CHECKOUT_SETUP.md`: Stripe uses Checkout Session metadata, Gumroad Ping can post form-encoded sale fields and can use `?token=CONVERSION_WEBHOOK_TOKEN`, and Lemon Squeezy should receive metadata as checkout custom data so it comes back under `meta.custom_data`.

Generate a deployable tracking app bundle:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --tracking-deploy-output-dir out/tracking-deploy --tracking-public-base-url https://track.your-domain.example
```

This writes `Dockerfile`, `.env.tracking.example`, `tracking_deploy.json`, and `DEPLOY_TRACKING_APP.md` for the server-side click and conversion webhook app. Host it behind HTTPS, then set `CLICK_REDIRECT_URL` and `CONVERSION_WEBHOOK_BASE_URL` to its public endpoints before regenerating the site/offers.

Generate lead magnet pages and checklists:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --lead-magnet-output-dir out/lead-magnets --lead-capture-url https://your-form.example/signup
```

This writes `lead_magnets.json`, `LEAD_MAGNETS.md`, an index page, and one landing/checklist pair per selected lead magnet opportunity. Use this for opt-in assets on owned channels before selling templates, setup services, or support.

Generate digital product packs:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --digital-product-output-dir out/digital-products --offer-payment-urls "digital_product=https://gumroad.com/l/template"
```

This writes `digital_products.json`, `DIGITAL_PRODUCTS.md`, and one folder per selected digital product with `README.md`, `STORE_LISTING.md`, `LAUNCH_CHECKLIST.md`, `product.json`, and an owned landing page. Use the included `offer_key` as checkout metadata before publishing.

Generate fixed-scope service packages:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --service-package-output-dir out/service-packages --offer-payment-urls "fixed_scope_service=https://buy.stripe.com/setup" --intake-url https://forms.example.com/setup
```

This writes `service_packages.json`, `SERVICE_PACKAGES.md`, and one folder per selected paid setup kit with `PROPOSAL.md`, `SCOPE.md`, `DELIVERY_CHECKLIST.md`, `HANDOFF.md`, `service.json`, and an owned landing page. Use this to sell bounded setup work without silently expanding scope.

Generate paid niche report drafts:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --niche-report-output-dir out/niche-reports --offer-payment-urls "paid_report=https://gumroad.com/l/report"
```

This writes `niche_reports.json`, `NICHE_REPORTS.md`, and one folder per selected niche report with `REPORT.md`, `STORE_LISTING.md`, `VALIDATION_PLAN.md`, and an owned landing page. Publish only after manually verifying keywords, competitors, claims, and sources.

Generate disclosed affiliate article drafts:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --affiliate-article-output-dir out/affiliate-articles --affiliate-urls "fastapi=https://affiliate.example/fastapi,*=https://affiliate.example/default"
```

This writes `affiliate_articles.json`, `AFFILIATE_ARTICLES.md`, an index page, and one `ARTICLE.md`/`DISCLOSURE.md`/landing page set per selected affiliate article opportunity. Publish only on owned channels with visible disclosure and verified claims.

Generate GitHub Sponsors repo kits:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --sponsor-repo-output-dir out/sponsor-repos --sponsor-urls "github=https://github.com/sponsors/your-handle"
```

This writes `sponsor_repos.json`, `SPONSOR_REPOS.md`, an index page, and one owned repo kit per selected open-source sponsorship opportunity with `README.md`, `.github/FUNDING.yml`, `.github/ISSUE_TEMPLATE/support.yml`, `CONTRIBUTING.md`, `ROADMAP.md`, `examples/usage.md`, and an owned landing page. Publish only in your own GitHub repos after manual review.

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

## Conversion Webhooks

Host a small HTTPS endpoint for confirmed payment events and call the reusable handler with a server-side Supabase key:

```python
from farm_loop.webhook_handler import handle_conversion_webhook
from farm_loop.supabase_client import SupabaseClient

handle_conversion_webhook(
    headers=request_headers,
    payload=request_json,
    expected_token=CONVERSION_WEBHOOK_TOKEN,
    provider="stripe",
    supabase=SupabaseClient(SUPABASE_URL, SUPABASE_KEY),
)
```

The handler accepts `X-Revenue-Webhook-Token`, extracts USD amount, provider/event id, optional `offer_id`, stable `offer_key`, and attribution source metadata, then inserts `conversion_events`.

## Supabase Setup

Run `supabase/schema.sql` in the Supabase SQL editor. The schema defines:

- `runs`: one row per loop execution.
- `opportunities`: deduplicated by `(source, external_id)`.
- `drafts`: generated answer drafts, default status `draft`.
- `events`: structured logs for each run.
- `tip_events`: confirmed Buy Me a Coffee events, deduplicated by `(provider, external_id)`.
- `revenue_milestones`: milestone definitions such as 15, 200, 1000, and 20000.
- `channels`: allowed revenue lanes such as microtools, GitHub issue helper, digital products, affiliates, open-source sponsorship, and paid setup kits.
- `assets`: reviewable generated assets: microtool specs, article outlines, patch plans, product listings, landing copy, support offers.
- `offers`, `click_events`, `conversion_events`, `experiments`: monetization and learning loop tracking.
- `launch_tasks`: prioritized manual launch tasks for review, publishing, monetization, and measurement.
- `portfolio_snapshots`: daily revenue dashboard snapshots with milestone progress, best source, best offer, click/conversion rate, and recommended next actions.

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
