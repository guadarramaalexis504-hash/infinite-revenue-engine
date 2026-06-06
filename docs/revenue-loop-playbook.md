# Infinite Revenue Loop Playbook

This project is built to accumulate revenue through many small legal loops. It does not guarantee income, but it gives the system a repeatable way to discover opportunities, score expected value, create reviewable assets, measure conversion, and keep running past every milestone.

Current operating target:

- Supabase project: Sonident.
- Protected pipeline: `aipickd` stays off-limits unless explicitly authorized.
- Local idea catalog: `IDEA_CATALOG_PATH=data/revenue_ideas.json`.
- Manual keyword list: `KEYWORD_CSV_PATH=data/revenue_keywords.csv`.
- Local review queue: `ASSET_OUTPUT_DIR=out/revenue-assets`.
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

Local continuous review loop:

```powershell
python -m farm_loop.main --loop --interval-seconds 300 --dry-run
```

Production cron phases in GitHub Actions:

- every 5 minutes: discovery and scoring
- hourly: asset generation
- daily: summary event
- weekly: prune event

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
- Payment path: Buy Me a Coffee, Stripe, Gumroad, Lemon Squeezy, or GitHub Sponsors.
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
