# Infinite Revenue Loop Playbook

This project is built to accumulate revenue through many small legal loops. It does not guarantee income, but it gives the system a repeatable way to discover opportunities, score expected value, create reviewable assets, measure conversion, and keep running past every milestone.

Current operating target:

- Supabase project: Sonident.
- Protected pipeline: `aipickd` stays off-limits unless explicitly authorized.
- Local idea catalog: `IDEA_CATALOG_PATH=data/revenue_ideas.json`.
- Manual keyword list: `KEYWORD_CSV_PATH=data/revenue_keywords.csv`.
- Local review queue: `ASSET_OUTPUT_DIR=out/revenue-assets`.
- Owned static site: `SITE_OUTPUT_DIR=out/site`.
- Public site base URL: `SITE_BASE_URL=https://your-domain.example`.
- Launch queue: `LAUNCH_QUEUE_OUTPUT_DIR=out/launch-queue`.
- Interactive microtools: `MICROTOOL_OUTPUT_DIR=out/microtools`.
- Offer catalog: `OFFER_OUTPUT_DIR=out/offers`.
- Checkout setup: `CHECKOUT_SETUP_OUTPUT_DIR=out/checkout-setup`.
- Tracking deploy bundle: `TRACKING_DEPLOY_OUTPUT_DIR=out/tracking-deploy`.
- Lead magnets: `LEAD_MAGNET_OUTPUT_DIR=out/lead-magnets`.
- Digital products: `DIGITAL_PRODUCT_OUTPUT_DIR=out/digital-products`.
- Affiliate articles: `AFFILIATE_ARTICLE_OUTPUT_DIR=out/affiliate-articles`.
- Opportunity roadmap: `ROADMAP_OUTPUT_DIR=out/roadmap`.
- Revenue bundle: `BUNDLE_OUTPUT_DIR=out/revenue-bundle`.
- Optional click redirect: `CLICK_REDIRECT_URL=https://your-domain.example/click`.
- Optional service intake: `SERVICE_INTAKE_URL=https://your-form-or-checkout.example`.
- Optional lead capture: `LEAD_CAPTURE_URL=https://your-form-or-newsletter.example`.
- Optional checkout mapping: `OFFER_PAYMENT_URLS=fixed_scope_service=https://buy.stripe.com/setup,digital_product=https://gumroad.com/l/template`.
- Optional affiliate mapping: `AFFILIATE_URLS=fastapi=https://affiliate.example/fastapi,*=https://affiliate.example/default`.
- Live-readiness check: `.\scripts\doctor.ps1`.
- Milestones: `$15`, `$200`, `$1,000`, `$20,000`.
- Default behavior: keep running after milestones because `STOP_AFTER_TARGET=false`.

## Operating Model

1. Discover problems from permitted sources: GitHub issues, manual keyword lists, the idea catalog, owned analytics later, and Stack Exchange only as pain discovery.
2. Score each opportunity with expected value: payout estimate times conversion probability, minus estimated cost and risk.
3. Generate reviewable assets only: tool specs, article outlines, patch plans, product listings, landing copy, and support offers.
4. Publish manually on owned or permitted channels.
5. Track clicks, conversions, tips, offers, and experiments.
6. Double down on channels with revenue and prune weak experiments.

The engine should behave like a portfolio. A single loop may earn nothing, but the system keeps producing measured experiments until one or more channels convert.

## Commands

Discovery dry-run:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase discover --dry-run --max-opportunities 10
```

Generate top assets dry-run:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10
```

Generate top assets into a local review queue:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --asset-output-dir out/revenue-assets
```

Each selected opportunity gets a folder with `manifest.json` and Markdown drafts. These files are still manual review only; they are not auto-published.

Generate an owned static site:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --site-output-dir out/site
```

The site is a local owned channel draft with an index and one page per opportunity. It also writes `sitemap.xml` and `robots.txt`; set `SITE_BASE_URL` before publishing so the sitemap contains absolute public URLs. It can carry a support CTA when `TIP_URL` is configured, but it still needs manual review before public deployment.

The site also writes `offers/index.html` as a central owned-channel catalog of all generated service, support, and product offers, plus `intake/index.html` for paid setup/service requests. Set `SERVICE_INTAKE_URL` before publishing service CTAs.

Generate a prioritized launch queue:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --launch-queue-output-dir out/launch-queue
```

The launch queue writes `launch_queue.json` and `LAUNCH_QUEUE.md`. It converts each selected opportunity into activation, review, owned publishing, monetization, and measurement tasks. CLI exports also include the current activation preflight from the doctor check, so missing `.env` values, git remote setup, and `gh` authentication become blocking tasks at the top. In live Supabase runs, these tasks are inserted into `launch_tasks`.

Generate an offer catalog:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --offer-output-dir out/offers
```

The offer catalog writes `offers.json` and `OFFERS.md`. It turns selected opportunities into draft support offers, setup services, digital products, or sponsorship-style CTAs with prices. In live Supabase runs, these offers are inserted into `offers`.

Generate checkout setup instructions:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --checkout-setup-output-dir out/checkout-setup --conversion-webhook-base-url https://your-domain.example/webhooks/conversion
```

This writes `checkout_setup.json` and `CHECKOUT_SETUP.md` with checkout metadata, stable `offer_key` values, provider webhook URLs, and manual conversion fallback commands.

Generate a tracking app deploy bundle:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --tracking-deploy-output-dir out/tracking-deploy --tracking-public-base-url https://track.your-domain.example
```

This writes `Dockerfile`, `.env.tracking.example`, `tracking_deploy.json`, and `DEPLOY_TRACKING_APP.md` for the server-side click redirect and conversion webhook app. Deploy it behind HTTPS, then set `CLICK_REDIRECT_URL=https://track.your-domain.example/click` and `CONVERSION_WEBHOOK_BASE_URL=https://track.your-domain.example/webhooks/conversion`.

Generate lead magnet pages and checklists:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --lead-magnet-output-dir out/lead-magnets --lead-capture-url https://your-form-or-newsletter.example
```

This writes `lead_magnets.json`, `LEAD_MAGNETS.md`, an index page, and one landing/checklist pair per selected lead magnet opportunity. Use these only on owned channels with explicit opt-in and a clear next paid offer.

Generate digital product packs:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --digital-product-output-dir out/digital-products --offer-payment-urls "digital_product=https://gumroad.com/l/template"
```

This writes `digital_products.json`, `DIGITAL_PRODUCTS.md`, and one folder per selected digital product with `README.md`, `STORE_LISTING.md`, `LAUNCH_CHECKLIST.md`, `product.json`, and an owned landing page. Set checkout metadata with `offer_key` before publishing the product.

Generate disclosed affiliate article drafts:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 20 --affiliate-article-output-dir out/affiliate-articles --affiliate-urls "fastapi=https://affiliate.example/fastapi,*=https://affiliate.example/default"
```

This writes `affiliate_articles.json`, `AFFILIATE_ARTICLES.md`, an index page, and one `ARTICLE.md`/`DISCLOSURE.md`/landing page set per selected affiliate article opportunity. Publish only on owned channels with visible disclosure, verified claims, and allowed affiliate programs.

Generate an opportunity roadmap:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --roadmap-output-dir out/roadmap
```

The opportunity roadmap writes `opportunity_roadmap.json` and `OPPORTUNITY_ROADMAP.md`. It keeps all ranked ideas, channel summaries, activation blockers, and a milestone plan for `$15`, `$200`, `$1,000`, and `$20,000`, so the backlog stays visible even when only the top few assets are generated in one run.

Generate the full revenue bundle:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --bundle-output-dir out/revenue-bundle
```

The revenue bundle writes assets, an owned static site, microtools under `site/tools`, offers, checkout setup instructions, tracking deploy files, lead magnets, digital product packs, affiliate article drafts, opportunity roadmap, and launch queue in one standard tree. This is the fastest local review artifact before publishing anything.

Attach real payment links to generated offers:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --offer-payment-urls "fixed_scope_service=https://buy.stripe.com/setup,digital_product=https://gumroad.com/l/template" --site-output-dir out/site --offer-output-dir out/offers
```

`OFFER_PAYMENT_URLS` accepts comma-separated `offer_type=url`, `channel=url`, or `*=url` entries. The exporter stores matching URLs in `offers.json` and uses them for owned offer CTAs. If `CLICK_REDIRECT_URL` is configured, those CTAs route through `/click` first so checkout traffic is measurable.

Each generated offer includes an `offer_key` like `idea_catalog:offer-webhook-setup-service:fixed_scope_service`. Use that key as checkout metadata (`offer_key` or `ire_offer_key`) when the payment provider cannot return Supabase `offers.id`. The dashboard and pruning loop can attribute clicks and confirmed revenue by either `offer_id` or `offer_key`.

Record a confirmed conversion:

```powershell
python -m farm_loop.main --record-conversion --conversion-provider stripe --conversion-external-id evt_123 --conversion-amount-usd 99 --conversion-source paid_setup_kit --conversion-offer-id offer-id
```

This writes to `conversion_events` in live mode and supports dry-run validation first. Use it for confirmed Stripe, Gumroad, Lemon Squeezy, manual invoice, affiliate, or sponsorship revenue when a provider-specific integration is not wired yet.

If you only have the stable offer key:

```powershell
python -m farm_loop.main --record-conversion --dry-run --conversion-provider manual --conversion-external-id invoice-123 --conversion-amount-usd 199 --conversion-source paid_setup_kit --conversion-offer-key idea_catalog:offer-webhook-setup-service:fixed_scope_service
```

Generate interactive microtools:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 10 --microtool-output-dir out/microtools
```

Supported interactive microtools start with Supabase RLS policy checker and GitHub Actions YAML checker. These are static owned-channel tools, not third-party posts. Each tool still needs manual review, proof, and payment/tracking setup before public launch.

Attribution:

- support CTAs include `utm_source=revenue_site`, `utm_medium=<channel>`, `utm_campaign=<external_id>`, and `utm_content=support_cta`
- internal attribution fields use `ire_source` and `ire_external_id`
- direct links work with only UTM parameters
- when `CLICK_REDIRECT_URL` is configured, support CTAs use an owned click redirect before the final support/payment URL
- the click redirect handler validates allowed target hosts and inserts rows into `click_events` with `source='revenue_site'`
- service offers use `SERVICE_INTAKE_URL` first and add UTM attribution such as `utm_content=fixed_scope_service_intake`
- confirmed payment events can be recorded through `--record-conversion` or a custom webhook calling `handle_conversion_webhook`

tracking HTTP app:

```powershell
python -m farm_loop.http_app --host 127.0.0.1 --port 8080
```

The app exposes `/health`, `/click`, `/webhooks/buymeacoffee`, and `/webhooks/conversion/<provider>`. Use it behind HTTPS on a server-side host so generated pages can send visitors through `/click` and payment providers can confirm revenue through `/webhooks/conversion`. Configure `CLICK_ALLOWED_HOSTS`, `BUYMEACOFFEE_WEBHOOK_TOKEN`, and `CONVERSION_WEBHOOK_TOKEN` before using it live.

Local continuous review loop:

```powershell
python -m farm_loop.main --loop --interval-seconds 300 --dry-run
```

Production cron phases in GitHub Actions:

- every 5 minutes: discovery and scoring
- hourly: asset generation
- daily: portfolio snapshot with revenue, attribution, milestone progress, and next actions
- weekly: pruning pass for winners, stale zero-signal experiments, and click-without-revenue offers

Daily summary command:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase summarize
```

In live mode, this reads `conversion_events`, `tip_events`, `click_events`, `offers`, `assets`, and `experiments`, then stores the dashboard payload in `portfolio_snapshots`. The snapshot is the learning layer: it shows which channel or offer is producing revenue and recommends where to double down next.

Weekly prune command:

```powershell
python -m farm_loop.main --portfolio-once --portfolio-phase prune
```

In live mode, pruning reads `experiments`, `offers`, `click_events`, and `conversion_events`. It never deletes records. It marks experiments with confirmed revenue as `won`, pauses stale experiments with no clicks or revenue, and creates `launch_tasks` for offers that get clicks but no confirmed revenue.

Owned static site deployment:

- workflow file: `.github/workflows/pages-site.yml`
- target: GitHub Pages
- build command: `python -m farm_loop.main --portfolio-once --portfolio-phase generate --dry-run --max-opportunities 12 --site-output-dir out/site --microtool-output-dir out/site/tools`
- SEO outputs: `sitemap.xml` and `robots.txt`
- deploy method: GitHub's official Pages actions after Pages is configured to deploy from GitHub Actions

## Best First Loops

### Microtools SEO

Small tools can compound because each one becomes an owned asset:

- Supabase RLS policy checker
- GitHub Actions YAML validator
- OpenAI API cost calculator
- JSON schema diff tool
- Regex explainer and test generator
- Webhook signature tester
- Cron expression explainer
- SQL index suggestion helper
- Stripe webhook signature verifier
- Supabase Auth redirect URL checker
- CORS preflight debugger
- Docker Compose env checker

Monetization paths:

- optional Buy Me a Coffee support
- paid downloadable template
- support offer under the tool
- affiliate links where honest and allowed
- email capture for advanced version

### Paid Setup Kits

This is the fastest path to higher ticket revenue:

- Supabase + GitHub Actions setup
- webhook setup into Supabase
- GitHub Actions cron setup
- AI automation audit
- Supabase RLS fix service
- GitHub Actions debug service
- OpenAI SaaS starter setup

Suggested pricing:

- basic fixed setup: 49 to 99 USD
- full setup: 149 to 299 USD
- urgent/debug setup: 299+ USD

### Digital Products

Good products are reusable and do not require constant labor:

- FastAPI + Supabase Auth template
- OpenAI SaaS starter kit
- Next.js Supabase Stripe starter
- GitHub Actions release kit
- AI support bot starter kit
- Notion AI cost tracker
- Excel SaaS metrics template
- GitHub Sponsors README/funding kit

### GitHub Issue Helper

Use GitHub as a discovery source and create drafts:

- documentation patch plans
- reproduction templates
- failing-test plans
- dependency upgrade PR plans
- CI flake triage notes
- README improvements
- sponsor-ready open-source helper repos

Do not spam maintainers. Only submit PRs manually when they are genuinely useful.

### Affiliate and Content

Use owned sites only:

- Supabase RLS launch checklist
- GitHub Actions cost and quota guide
- OpenAI API cost controls guide
- FastAPI deployment comparison
- Stripe vs Lemon Squeezy for tiny SaaS
- Supabase alternatives and pricing guide

Revenue comes later, but it can compound if articles rank.

### Lead Magnets

These do not monetize immediately, but they build an opt-in list:

- AI app launch checklist
- Supabase production checklist
- GitHub Actions secret safety checklist
- AI automation ROI calculator

### Bounty Scanning

Only use rules-compliant programs:

- docs bounty scanner
- beginner-safe bug triage scanner
- open-source docs bounty starter
- reproducible issue finder

Avoid intrusive security testing unless the program explicitly allows it.

### Niche Reports

Reports can become paid PDFs, mini-sites, or lead magnets:

- local AI tools
- Supabase templates
- AI spreadsheet templates
- small-business automation stacks
- webhook/payment integration starter niches

## Scoring And Thresholds

Formula:

```text
expected_value = payout_estimate * conversion_probability - estimated_cost - risk_penalty
```

Bonuses:

- reusable asset bonus for microtools, digital products, and open-source sponsorship loops
- speed bonus for assets that can be built in 45 minutes or less

Prioritize:

- high-intent pain
- low build time
- reusable output
- owned distribution
- low policy or platform risk

Prune:

- no clicks after 30 days
- no conversion after repeated qualified traffic
- high manual labor with low repeatability
- channels that require spam or unauthorized posting
- do not delete history; mark experiments `paused`, `lost`, or `won` and preserve the measurement trail

## Milestones

Milestones are not stop conditions:

- `$15`: first proof
- `$200`: useful side income
- `$1,000`: repeatable loop
- `$20,000`: major cumulative target

Revenue should be counted only from confirmed `tip_events` and `conversion_events`. The engine keeps running after each milestone and records progress rather than shutting down.

## What Must Be Added To Actually Earn

- Real Supabase service-role/secret key for Sonident.
- OpenAI API key.
- GitHub token or GitHub Actions secrets.
- GitHub remote and authenticated `gh` or repository UI access so workflows can be dispatched.
- If no remote exists locally, use `.\scripts\configure-github.ps1 -Repo owner/repo -RunWorkflow`.
- Payment path: Buy Me a Coffee, Stripe, Gumroad, Lemon Squeezy, or GitHub Sponsors.
- Offer payment URL mapping: `OFFER_PAYMENT_URLS`.
- Optional conversion webhook token: `CONVERSION_WEBHOOK_TOKEN`.
- Optional click redirect allowlist: `CLICK_ALLOWED_HOSTS`.
- Service intake URL: `SERVICE_INTAKE_URL`.
- Lead capture URL: `LEAD_CAPTURE_URL`.
- Owned publishing surface: repo, website, landing pages, newsletter, or store.
- Manual review process for assets before public release.
- Basic analytics for click and conversion attribution.

## Safety Boundaries

- Do not publish AI-generated Stack Overflow answers.
- Do not mass-post payment links into communities.
- Do not touch `aipickd` without explicit authorization.
- Do not use anon/publishable Supabase keys for server-side writes.
- Do not claim revenue until it exists in `tip_events` or `conversion_events`.
- Do not rely on a single trick; grow the portfolio and measure what works.
