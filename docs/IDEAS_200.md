# 200 Ideas para el Infinite Revenue Engine

> Generadas 2026-06-13. 200 ideas nuevas y distintas (deduped contra las 109 que ya estaban en `data/revenue_ideas.json`).
> Todas construibles por una persona sobre el stack $0: GitHub Actions cron + Supabase + GitHub Pages (pSEO) + tracker Vercel + Gumroad + Discord.

## La apuesta en una línea
Arriesgas ~$3 USD/mes (máx ~$36/año) por una probabilidad **real** de $500–2,000+/mes en 12–24 meses si pega. Asimetría a favor. La vía rápida al primer dinero = **servicios** (un cliente de $149–399 ya supera una semana de chamba); las herramientas gratis y el pSEO son el motor de tráfico que los alimenta.

## Reparto por categoría (200 total)
| Categoría | Cuántas | Para qué sirve |
|---|---|---|
| Free Tools — Dev | 48 | Imanes de tráfico SEO (devs) |
| Free Tools — No-Dev | 27 | Amplían audiencia (negocios, marketers, estudiantes) |
| Digital Products | 36 | Venta pasiva $9–49 en Gumroad |
| Services | 27 | **Dinero rápido** $99–399 |
| pSEO Clusters | 23 | Cientos de páginas long-tail automáticas |
| Data & Reports | 20 | Data first-party que nadie más tiene |
| Lead Magnets | 14 | Construir lista de email |
| Distribution & Affiliate | 5 | Conseguir los ojos (el cuello de botella real) |

---

## Free Tools — Dev (SEO funnel)

1. **ULIDForge** — Generate and bulk-decode ULIDs in-browser, showing embedded timestamp + monotonic sort order vs UUIDv4. `free-tool-seo` · $0 · S
2. **UUIDLab** — Generate UUID v1/v4/v7 and decode any UUID to reveal version, variant, and v7 timestamp client-side. `free-tool-seo` · $0 · S
3. **EpochFlip** — Convert Unix epoch (s/ms/μs/ns) to human dates and back with a live "now" ticker and copy-as-ISO8601. `free-tool-seo` · $0 · S
4. **TZConvert** — Paste a timestamp and see it across multiple IANA timezones at once with DST-aware offsets, no server. `free-tool-seo` · $0 · M
5. **YAML2JSON Bridge** — Bidirectional YAML↔JSON converter with anchor/alias expansion and error-line highlighting, fully client-side. `free-tool-seo` · $0 · M
6. **TOMLCheck** — Validate and pretty-print TOML (pyproject.toml, Cargo.toml) in-browser with inline parse-error messages. `free-tool-seo` · $0 · M
7. **JSONLint Pro** — Format, minify, and repair broken JSON (trailing commas, single quotes) with one click, runs in-tab. `free-tool-seo` · $0 · S
8. **NDJSONViewer** — Paste newline-delimited JSON / JSON Lines and browse each record as a collapsible tree, no upload. `free-tool-seo` · $0 · M
9. **JSONPath Tester** — Type a JSONPath expression against pasted JSON and see matched nodes highlighted live, client-side. `free-tool-seo` · $0 · M
10. **Base64 Studio** — Encode/decode text, files, and data-URIs with a URL-safe toggle and image preview, all in-browser. `free-tool-seo` · $0 · S
11. **URLDecode Workbench** — Encode/decode URL components and parse query strings into an editable key-value table, no backend. `free-tool-seo` · $0 · S
12. **RegexBuilder ES** — Spanish-language regex tester with live match highlighting, named groups, and flag toggles in-browser. `free-tool-seo` · $0 · M
13. **RegexConvert** — Translate a regex between PCRE, JavaScript, Python, and Go flavors, flagging unsupported constructs. `free-tool-seo` · $0 · M
14. **HashForge** — Compute MD5/SHA-1/SHA-256/SHA-512 of pasted text or a dropped file via WebCrypto, 100% local. `free-tool-seo` · $0 · S
15. **BcryptCheck** — Generate and verify bcrypt hashes in-browser to test password rounds and compare a hash to a string. `free-tool-seo` · $0 · M
16. **ColorConvert** — Convert any color between HEX, RGB(A), HSL, and OKLCH with a live swatch and copy buttons, no server. `free-tool-seo` · $0 · S
17. **ContrastCheck** — Paste two colors and get the WCAG contrast ratio plus AA/AAA pass/fail for normal and large text. `free-tool-seo` · $0 · S
18. **CubicEase** — Visual cubic-bezier editor that outputs the CSS transition-timing-function string, runs in-browser. `free-tool-seo` · $0 · M
19. **FlexboxPlay** — Interactive flexbox playground that generates copy-paste CSS as you toggle justify/align/wrap, no backend. `free-tool-seo` · $0 · M
20. **HeaderInspect** — Paste raw HTTP request/response headers and get a parsed, explained table (CORS, cache, security) in-tab. `free-tool-seo` · $0 · M
21. **CSPBuilder** — Build a Content-Security-Policy header from checkboxes and paste an existing CSP to get it explained, local. `free-tool-seo` · $0 · M
22. **DiffViewer** — Paste two text blobs and get a side-by-side / inline word-level diff with copy-as-patch, 100% in-browser. `free-tool-seo` · $0 · M
23. **SQLFormat** — Format and minify SQL with dialect-aware keyword casing for Postgres/MySQL, runs entirely in the tab. `free-tool-seo` · $0 · M
24. **CSVToJSON** — Drop a CSV and convert to JSON array, NDJSON, or Markdown table with delimiter auto-detect, no upload. `free-tool-seo` · $0 · M
25. **SlugForge** — Turn any title into a URL-safe slug with accent/diacritic stripping (great for Spanish), client-side. `free-tool-seo` · $0 · S
26. **PASETOPeek** — Decode and inspect PASETO v2/v4 tokens (the JWT alternative) showing footer, payload, and version, local. `free-tool-seo` · $0 · M
27. **DNSExplain** — Paste a raw DNS record (A/AAAA/CNAME/MX/TXT/SRV) and get a plain-English breakdown of each field, no server. `free-tool-seo` · $0 · M
28. **CIDRCalc** — Enter a CIDR block and get network/broadcast/usable-range/host-count plus subnet splitting, client-side. `free-tool-seo` · $0 · M
29. **UnicodeInspect** — Paste text to reveal hidden zero-width chars, code points, and normalization form (NFC/NFD), in-browser. `free-tool-seo` · $0 · M
30. **DataURIGen** — Convert a dropped image/SVG/font into an inline data:URI for CSS, with a size warning, fully local. `free-tool-seo` · $0 · S
31. **QRForge** — Generate a QR code from text/URL/WiFi entirely in-browser and download as SVG or PNG, no API call. `free-tool-seo` · $0 · S
32. **MarkdownTablePro** — Paste CSV or type cells to build aligned Markdown tables with GitHub-flavored preview, client-side. `free-tool-seo` · $0 · S
33. **PromptLint** — Paste a prompt; client-side checks flag missing role/output-format/few-shot, vague verbs, and token bloat with fixes. `free-tool-seo` · $0 · S
34. **TokenViz** — Paste text and see token counts side-by-side for GPT-4o/Claude/Gemini plus per-call cost for each, in-browser. `free-tool-seo` · $0 · M
35. **ContextFit** — Enter system prompt + docs + history sizes; tool shows if it fits a model's context window and what to trim. `free-tool-seo` · $0 · S
36. **JSONMode Validator** — Paste an LLM's JSON output + your JSON Schema; validates client-side and shows exactly which field broke. `free-tool-seo` · $0 · S
37. **ChunkLab** — Paste a document, pick chunk size + overlap, preview the actual chunks and count, copy as JSON for your vector DB. `free-tool-seo` · $0 · M
38. **EmbedCost** — Enter doc count + avg tokens; estimates embedding API cost and vector storage across OpenAI/Cohere/Voyage. `free-tool-seo` · $0 · S
39. **MCPGen** — Pick tools + transport, get a ready claude_desktop_config.json / mcp.json snippet with stdio or SSE wiring, in-browser. `free-tool-seo` · $0 · M
40. **AgentLoopCost** — Enter steps, avg tokens/step, and model; estimates total + worst-case cost for a tool-calling agent loop. `free-tool-seo` · $0 · S
41. **GEOcheck** — Paste a URL's HTML; scores answer-first formatting, FAQ schema, entity clarity, and llms.txt for AI citability. `free-tool-seo` · $0 · M
42. **Prompt Injection Tester** — Paste your system prompt; runs 30 known jailbreak/injection strings client-side and flags leaks. `free-tool-seo` · $0 · M
43. **TempJSON** — Pick a task (extraction, code, creative); recommends temperature/top-p/penalty settings with one-click copy per provider. `free-tool-seo` · $0 · S
44. **Markdown-to-Prompt Cleaner** — Paste messy docs/HTML; strips noise, normalizes to clean Markdown, and reports token savings. `free-tool-seo` · $0 · S
45. **Hallucina-Check** — Paste an LLM answer + source text; highlights claims unsupported by the source so you catch hallucinations. `free-tool-seo` · $0 · M
46. **System Prompt Library** — Browsable client-side library of battle-tested system prompts (support bot, SQL gen, code reviewer) with copy + token count. `free-tool-seo` · $0 · M
47. **RateLimitCalc** — Enter expected requests + avg tokens; computes whether you'll hit OpenAI/Anthropic tier RPM/TPM limits and which tier to buy. `free-tool-seo` · $0 · S
48. **PromptDiff** — Paste two prompt versions; word-diffs them and estimates token-cost delta so you see what changed and what it costs. `free-tool-seo` · $0 · S

## Free Tools — Non-Dev (SEO funnel)

49. **QuoteCraft** — Enter line items, hours, and rate; instantly generates a branded printable PDF quote with subtotal, tax, and validity date. `free-tool-seo` · $0 · M
50. **MargenYa** — Spanish tool: input product cost + desired margin %, outputs sale price, markup, and profit per unit for small shops. `free-tool-seo` · $0 · S
51. **FreelanceRate** — Input target yearly income, billable hours/week, and expenses; returns the hourly rate you must charge to hit it. `free-tool-seo` · $0 · S
52. **CaptionForge** — Pick a vibe and topic; generates 10 caption variants with hashtag sets and emoji, all client-side from templates. `free-tool-seo` · $0 · M
53. **BioLink** — Enter niche + 3 keywords; outputs 8 formatted 150-char Instagram bios with line breaks, symbols, and CTA. `free-tool-seo` · $0 · S
54. **GrowthClock** — Enter followers, likes, and comments; returns engagement rate %, niche benchmark, and a shareable score card. `free-tool-seo` · $0 · S
55. **PostPlanner** — Select platform + timezone; generates a weekly best-time-to-post grid you can download as PNG. `free-tool-seo` · $0 · M
56. **ColdOpen** — Paste a subject line; scores spam-trigger words, length, emoji, and caps, returns a deliverability grade and rewrite tips. `free-tool-seo` · $0 · M
57. **SalaryReal** — Enter gross salary and country/state; returns monthly net pay, tax breakdown, and hourly equivalent. `free-tool-seo` · $0 · M
58. **ROAS Calculator** — Input ad spend, conversions, and order value; returns ROAS, CPA, break-even, and a profit/loss verdict. `free-tool-seo` · $0 · S
59. **DiscountCheck** — Enter original price and discount %, or reverse-solve markup; shows final price, savings, and effective margin. `free-tool-seo` · $0 · S
60. **TipSplit** — Enter bill, tip %, and number of people; instantly shows per-person amount, rounding option, and total with tip. `free-tool-seo` · $0 · S
61. **SaveGoal** — Enter target amount, current savings, and monthly deposit; shows the date you hit the goal and interest earned. `free-tool-seo` · $0 · S
62. **WordCountPro** — Paste text; shows word/character/sentence counts, keyword density, and estimated reading + speaking time live. `free-tool-seo` · $0 · S
63. **CaseShift** — Paste text and one-click convert to UPPER, lower, Title, Sentence, camelCase, or kebab-case, copy instantly. `free-tool-seo` · $0 · S
64. **BusinessName** — Enter keywords + industry; generates 30 brandable name ideas with .com-style slugs and a tagline for each. `free-tool-seo` · $0 · M
65. **DateDiff** — Pick two dates; returns days/weeks/months between, business days, age in years, and a countdown to an event. `free-tool-seo` · $0 · S
66. **PomoFocus** — Set study hours and break ratio; generates a timed Pomodoro schedule with a built-in in-browser timer and chime. `free-tool-seo` · $0 · M
67. **GPACalc** — Enter course grades and credit hours; computes weighted GPA, what-if target grades, and semester average. `free-tool-seo` · $0 · S
68. **PaletteSnap** — Pick a base color or mood; generates a 5-swatch palette with HEX/RGB codes and a copyable CSS variable block. `free-tool-seo` · $0 · M
69. **ThumbCheck** — Upload an image; crop/resize in-browser to exact IG, YouTube thumb, FB, and LinkedIn dimensions, download each. `free-tool-seo` · $0 · M
70. **PesoConvert** — Spanish-first converter with offline cached rates between MXN, USD, COP, ARS, and EUR plus copy-paste amounts. `affiliate` · $0 · M
71. **MealMacros** — Enter weight, goal, and activity; returns daily calories and protein/carb/fat grams with a simple meal split. `affiliate` · $0 · M
72. **RentSplit** — Enter total rent, room sizes, and shared bills; computes each roommate's fair share, optionally weighted by room. `free-tool-seo` · $0 · S
73. **GiveawayPicker** — Paste a list of names/handles; fairly draws random winners with duplicate removal and a shareable result. `free-tool-seo` · $0 · S
74. **HashtagMix** — Enter a topic; builds 3 mixed-size hashtag sets (big/medium/niche), counts them, and warns if over 30. `free-tool-seo` · $0 · S
75. **LoanLens** — Input loan amount, rate, and term; returns monthly payment, total interest, and an exportable amortization table. `affiliate` · $0 · M

## Digital Products

76. **The Cold DM Swipe File for Indie Hackers** — 120 copy-paste outreach DMs (X, LinkedIn, email) for first 10 SaaS users, with fill-in-the-blank variables. `digital-product` · $19 · S
77. **Changelog & Release Notes Swipe Pack** — 60 Markdown changelog templates plus a tone guide for writing release notes fast. `digital-product` · $12 · S
78. **ChatGPT Prompt Pack for Code Review** — 75 tested prompts that turn an LLM into a reviewer for PRs, security, perf, and naming. `digital-product` · $15 · S
79. **Notion Indie SaaS Operating System** — One Notion template: roadmap, changelog, feedback inbox, churn log, and weekly metrics dashboard linked. `digital-product` · $29 · M
80. **Cold Email Deliverability Checklist (PDF)** — 47-point pre-send checklist covering SPF/DKIM/DMARC, warmup, spam words, and link domains. `digital-product` · $12 · S
81. **The Bootstrapped Pricing Page Swipe File** — 30 annotated real SaaS pricing pages plus 5 copy-paste HTML pricing tables. `digital-product` · $19 · M
82. **SQL Interview Cheat Sheet (PDF)** — 40 SQL patterns (window functions, CTEs, joins, anti-joins) with the exact query and when to use it. `digital-product` · $9 · S
83. **Plantillas de Contratos para Freelancers (ES)** — 8 editable Spanish contracts (web dev, retainer, NDA, fixed scope) with payment and IP clauses for LATAM. `digital-product` · $19 · M
84. **The Airtable CRM for Solo Consultants** — Airtable base with lead pipeline, proposal tracker, invoice status, and follow-up reminders pre-linked. `digital-product` · $29 · M
85. **Midjourney Prompt Pack for App Icons** — 200 structured prompts for app icons, logos, and favicons grouped by style with parameter recipes. `digital-product` · $15 · S
86. **Landing Page Copy Formulas Swipe File** — 25 fill-in-the-blank copy frameworks (hero, social proof, FAQ, CTA) with 3 worked examples each. `digital-product` · $19 · M
87. **The Markdown Resume Template Pack for Devs** — 6 ATS-safe Markdown resume templates plus a library of 80 action-verb achievement bullets. `digital-product` · $12 · S
88. **Discord Community Starter Pack** — Importable server template (channels, roles, rules, welcome flow) plus 30 onboarding message scripts. `digital-product` · $19 · S
89. **The Solo Founder's Legal Pages Pack** — Fill-in-the-blank Privacy, ToS, Cookie, and Refund templates (Markdown + HTML) for indie SaaS. `digital-product` · $19 · M
90. **Spreadsheet Runway & Burn Calculator** — Google Sheets model: enter cash, MRR, and expenses to see runway, break-even date, and churn sensitivity. `digital-product` · $15 · M
91. **Git Commands Cheat Sheet (Printable PDF)** — 90 git commands grouped by task (undo, rebase, stash, bisect) with exact flags and an "oh-no" recovery section. `digital-product` · $9 · S
92. **The Product Hunt Launch Kit** — Tagline formulas, first-comment template, hunter DM scripts, 7-day promo schedule, 40-item pre-launch checklist. `digital-product` · $29 · M
93. **Prompts de Marketing para PyMEs (ES)** — 150 Spanish prompts for social, ads, and emails, organized by objective (sell, retain, announce). `digital-product` · $15 · S
94. **The Onboarding Email Sequence Swipe File** — 7-email SaaS onboarding sequence as copy-paste templates with subject lines. `digital-product` · $19 · M
95. **Color Palette & Gradient Pack for Devs** — 120 UI palettes and gradients exported as CSS variables, Tailwind config snippets, and SVG swatches. `digital-product` · $12 · S
96. **The Freelance Rate & Proposal Pack** — Pricing calculator sheet plus 5 proposal templates and a scope-creep clause library for dev/design freelancers. `digital-product` · $19 · M
97. **Keyboard Shortcuts Mega Cheat Sheet** — Printable deck for VS Code, Chrome DevTools, terminal, and Vim — the 30 shortcuts per tool that matter. `digital-product` · $9 · S
98. **The Indie Hacker's Tweet Bank** — 300 build-in-public tweet templates with placeholders, sorted by engagement type. `digital-product` · $15 · S
99. **API Documentation Starter Template** — OpenAPI-friendly docs template (endpoint, auth, error-table, examples) plus a 20-rule docs style guide. `digital-product` · $15 · S
100. **The Notion Content Calendar for Creators** — Idea backlog, multi-platform repurposing board, publish status, and a 30-day batch-production checklist. `digital-product` · $19 · M
101. **Customer Interview Question Bank (PDF)** — 100 Mom-Test-style questions sorted by stage plus a one-page interview script template. `digital-product` · $12 · S
102. **The SaaS Metrics Glossary Card Deck** — 50 printable cards defining a metric (MRR, NRR, CAC, payback) with formula, worked example, and benchmark. `digital-product` · $12 · S
103. **Bug Report & Issue Template Pack** — 20 GitHub/GitLab issue templates (.md) plus a triage-label taxonomy guide. `digital-product` · $12 · S
104. **PromptPack: 50 Dev Workflow Prompts** — 50 copy-paste prompts for code review, commit messages, SQL, regex, and docs with variable placeholders. `digital-product` · $19 · S
105. **RAG Starter Kit (Supabase pgvector + FastAPI)** — Template repo: pgvector schema, embed-and-upsert script, retrieval endpoint, and prompt template. `digital-product` · $39 · L
106. **Prompts para Devs ES (Spanish prompt pack)** — 60 Spanish prompts for coding, emails, and marketing, tuned for ChatGPT/Claude with placeholders. `digital-product` · $15 · S
107. **AI-for-Support Macro Kit** — 20 prompt+workflow templates turning support tickets into draft replies, with tone presets and an escalation rubric. `digital-product` · $29 · M
108. **Embedding Drift Monitor Recipe** — Template: nightly Actions cron re-embeds sample queries and alerts Discord when retrieval similarity drops. `digital-product` · $39 · L
109. **Affiliate Commission Benchmark Dataset** — First-party CSV of commission rates, cookie windows, and payout terms for 120 verified AI/SaaS programs. `digital-product` · $39 · L
110. **SaaS Free-to-Paid Wall Index** — Dataset scoring exactly where each AI tool's free plan stops being usable (the paywall trigger) across 70 tools. `digital-product` · $19 · M
111. **AI Tool Trust Signals Dataset** — Scored Supabase table per tool (SOC2 page?, status page?, refund policy, support SLA) for vendor vetting. `digital-product` · $49 · L

## Services

112. **Supabase Migration Rescue (from Firebase)** — Migrate your Firebase Auth + Firestore app to Supabase Postgres with schema, RLS, and data copy in 72h. `service` · $399 · L
113. **Heroku/Render Escape Hatch** — Move a dying free-tier app to GitHub Actions + Supabase + Vercel with working CI and env secrets. `service` · $299 · L
114. **Programmatic SEO Cluster Build-Out** — Generate 50 templated "X for Y" SEO landing pages from your keyword list and deploy to your static site in 72h. `service` · $349 · M
115. **Done-For-You Free Microtool Build** — One client-side WebCrypto/JS dev tool built, styled, and deployed to GitHub Pages as a lead magnet. `service` · $249 · M
116. **Lighthouse 90+ Performance Fix** — Take your slow site to a 90+ Lighthouse score (LCP/CLS/TBT) with a before/after report in 48h. `service` · $199 · M
117. **Google Search Console Setup + Sitemap Fix** — Verify GSC, submit a valid sitemap, fix "discovered not indexed" pages, hand over a coverage report. `service` · $129 · S
118. **WordPress to Static Site Migration** — Convert a slow WordPress site to a fast static GitHub Pages site, preserving URLs and 301 redirects. `service` · $349 · L
119. **Custom Domain + SSL + Email Setup** — Point your domain, fix DNS/SSL, and configure SPF/DKIM/DMARC so emails stop landing in spam. `service` · $99 · S
120. **OpenAI Chatbot Embed for Your Website** — A branded GPT-powered FAQ/support widget trained on your site content, embedded with one script tag. `service` · $299 · M
121. **Spreadsheet to Automated Dashboard** — Turn a messy Sheet/Excel into a live auto-refreshing dashboard on Supabase plus a shareable page. `service` · $249 · M
122. **Zapier-to-GitHub-Actions Cost Cutter** — Rebuild paid Zapier/Make automations as free GitHub Actions cron jobs to stop per-task fees. `service` · $299 · M
123. **Airtable to Supabase Migration** — Move an Airtable base hitting row limits into Supabase Postgres with a REST API and admin views in 72h. `service` · $349 · L
124. **Stripe Checkout + Webhook Wire-Up** — Install working Stripe Checkout with verified webhooks and a thank-you/fulfillment flow into your app. `service` · $249 · M
125. **Bilingual SEO Translation (EN to ES)** — Translate and SEO-localize 10 pages into Spanish with hreflang tags to capture LATAM search traffic. `service` · $249 · M
126. **Landing Page Build in 48h** — A single high-converting static landing page (copy + design + form + analytics) shipped to your domain. `service` · $199 · M
127. **Email Capture + Welcome Automation Setup** — Wire a signup form to your list with double opt-in and a 3-email welcome sequence, fully automated. `service` · $149 · S
128. **Broken Webhook Emergency Fix** — Same-day diagnosis and fix of a failing Stripe/GitHub/Discord webhook, with a repro test so it stays fixed. `service` · $149 · S
129. **GA4 + Conversion Tracking Setup** — Install GA4, define key events (signup/purchase), and deliver a one-page funnel report you can read. `service` · $179 · M
130. **Auto-Updating SEO Content Refresh** — Set up a cron that re-checks and refreshes your top 20 posts' dates/stats to protect rankings, hands-off. `service` · $299 · M
131. **Postgres Slow Query Tune-Up** — Profile your slowest Supabase queries, add the right indexes, and cut p95 latency with a before/after report. `service` · $199 · M
132. **Internal Tool Build (Admin CRUD app)** — A password-protected admin panel over your Supabase tables (view/edit/export) deployed in 72h. `service` · $349 · L
133. **Repo Privacy & Secret Leak Cleanup** — Scan your public repo history for leaked keys, rotate-guide them, and scrub git history before damage. `service` · $199 · M
134. **AI Bulk Product Description Writer Setup** — A cron job that auto-generates SEO product descriptions for your whole catalog from a CSV, on schedule. `service` · $249 · M
135. **First-Sale Funnel Setup for Creators** — Wire a free lead magnet to a Gumroad paid product with email follow-up, fully connected and live in 72h. `service` · $299 · M
136. **AI Cost Guardrails Setup Service** — Add budget caps, per-key usage logging to Supabase, and a Discord alert when monthly LLM spend crosses your limit. `service` · $199 · M
137. **llms.txt Authoring Service** — Crawl your site and deliver a hand-tuned llms.txt + llms-full.txt with curated sections and priorities. `service` · $149 · M
138. **GEO Audit Service (AI-answer optimization)** — Productized 20-point report on why your pages aren't cited by AI engines plus a prioritized fix list. `service` · $299 · M

## pSEO Clusters

139. **ErrCodex** — One page per error code (HTTP 4xx/5xx, Node ERR_*, Python tracebacks, npm/pip codes) explaining cause + fix. `pseo-cluster` · $0 · M
140. **CronText** — One static page per common cron string showing human-readable schedule + next 5 run times. `pseo-cluster` · $0 · S
141. **UnitDex** — "X to Y" converter pages for dev units (bytes/KB/MB, ms/s, hex/dec/bin, px/rem, RGB/HEX) — 300+ pairwise pages. `pseo-cluster` · $0 · M
142. **PortPedia** — One page per TCP/UDP port ("what runs on port 5432", "is port 3000 safe") covering service, protocol, security — 1000+ ports. `pseo-cluster` · $0 · M
143. **ExitCodes Atlas** — One page per Unix/Docker/bash exit code and signal ("exit code 137 meaning", SIGKILL/SIGTERM explained). `pseo-cluster` · $0 · S
144. **MIMEFinder** — One page per file extension to MIME type and reverse (".webp MIME type", "application/pdf extension") — 500+ pages. `pseo-cluster` · $0 · S
145. **GitFix Recipes** — One page per git situation ("undo last commit but keep changes", "remove file from history") — 150+ how-tos. `pseo-cluster` · $0 · M
146. **RegexBook** — One page per regex need ("regex for email", "IPv4 regex") with copy-paste pattern + test cases — 200+ patterns. `pseo-cluster` · $0 · M
147. **TimezoneJump** — "X time to Y time" converter pages across city pairs ("CST to IST", "9am EST in PST") — 400+ pages. `pseo-cluster` · $0 · M
148. **IsItFree Stack** — One page per tool answering "is X free / free tier limits" ("is Vercel free") — 200+ tool pages with current specs. `pseo-cluster` · $0 + affiliate · M
149. **CLIFlags Cheat** — One page per CLI flag for popular tools ("git clone --depth", "docker run -v") with examples — 300+ pages. `pseo-cluster` · $0 · M
150. **StatusCake ES (¿está caído?)** — Spanish "is X down" pages with live status per service ("WhatsApp está caído") — 150+ services. `pseo-cluster` · $0 · M
151. **ConviertePDF (ES)** — Spanish "convertir X a Y" file-conversion pages ("PDF a Word", "MP4 a MP3") — 300+ format pairs. `pseo-cluster` · $0 + affiliate · M
152. **ColorNamer** — One page per hex color ("what color is #FF5733") with name, RGB/HSL/CMYK, palette, Tailwind class — 1000+ pages. `pseo-cluster` · $0 · M
153. **EmojiMeaning** — One page per emoji with meaning, unicode codepoint, and copy button — 1500+ emoji pages. `pseo-cluster` · $0 · S
154. **BestFor Picker** — "Best <tool> for <use case>" matrix ("best database for Next.js", "best hosting for Django") — 250+ pages. `pseo-cluster` · $0 + affiliate · M
155. **CommandDiff** — One page per command/tool comparison ("npm vs pnpm", "curl vs wget", "apt vs apt-get") — 200+ pages. `pseo-cluster` · $0 + affiliate · M
156. **SQLByDB** — "How to <task> in <database>" matrix ("upsert in Postgres", "current date in MySQL") — 400+ pages. `pseo-cluster` · $0 · M
157. **CurrencyPair Static** — "X to Y" currency pages with today's rate + 1/10/100 table ("1 USD to MXN"), cron-refreshed daily — 300+ pairs. `pseo-cluster` · $0 + affiliate · M
158. **HTTPHeader Reference** — One page per HTTP header with purpose, values, example ("Cache-Control directives") — 200+ header pages. `pseo-cluster` · $0 · M
159. **LangSnippet** — "How to <task> in <language>" matrix ("read a file in Go", "parse JSON in Python") — 500+ pages. `pseo-cluster` · $0 · L
160. **Model Comparison Cluster (X vs Y for 2026)** — Programmatic pages comparing model pairs on price, context, speed, with copy-paste verdict. `pseo-cluster` · $0 · M
161. **AI Tools Comparador ES** — Spanish "X vs Y" and "mejor IA para X" pages comparing ChatGPT/Claude/Gemini for low-competition queries. `pseo-cluster` · $0 · M

## Data & Reports

162. **AI Tool Price Index (monthly)** — Cron scrapes 80 AI SaaS pricing pages into Supabase; publishes who raised/cut prices plus a downloadable CSV history. `dataset-report` · $0 + $29 CSV · M
163. **LLM API Uptime Monitor** — Cron pings OpenAI/Anthropic/Google/Mistral status every 15 min; publishes a live "is OpenAI down?" board with 90-day uptime. `free-tool-seo` · $0 · M
164. **AI Free Tier Tracker** — Tracks exact free-tier limits (requests/mo, tokens, seats) of 60 AI tools over time and flags quiet nerfs. `free-tool-seo` · $0 · M
165. **State of AI Pricing 2026 Report** — Annual PDF auto-built from the price-index table: median change, who went usage-based, cheapest per category, charts. `lead-magnet` · email-gated · M
166. **LLM Token Price per Million Tracker** — Daily table of input/output $ per 1M tokens for every model with a "cheapest model for your use case" filter. `free-tool-seo` · $0 · M
167. **AI Tool Sunset & Shutdown Tracker** — Flags AI products that shut down, got acquired, or paused signups, kept as a searchable Supabase log. `free-tool-seo` · $0 · M
168. **AI Coding Tool Latency Benchmark** — Cron runs a fixed prompt against Copilot/Cursor/Codeium APIs weekly and publishes median latency + completion length. `dataset-report` · $0 + $19 · L
169. **GitHub Star Velocity Index (AI repos)** — Daily stars/forks/issues snapshot for 200 trending AI repos via GitHub API, with a momentum leaderboard. `free-tool-seo` · $0 · M
170. **AI Tool Rate Limit Tracker** — Documents published rate limits (RPM/TPM/concurrent) of every major LLM API and tier, versioned over time. `free-tool-seo` · $0 · M
171. **Programmatic SEO Decay Benchmark** — First-party metrics from the engine's own 82+ article corpus: days-to-rank, decay curve, refresh lift. `dataset-report` · $49 · M
172. **AI Tool Context Window Tracker** — Versioned table of max context window per model over time, charting the arms race with exact bump dates. `free-tool-seo` · $0 · S
173. **Spanish AI Tools Price Comparison (LATAM)** — Spanish monitor of AI tool prices in MXN/COP/ARS with local-tax notes, refreshed monthly. `free-tool-seo` · $0 · M
174. **LLM Model Deprecation Calendar** — Scrapes provider deprecation notices into a dated calendar with a per-model "days until sunset" counter. `free-tool-seo` · $0 · S
175. **Image Generation Cost-per-Image Index** — Tracks real $ per 1024px image across Midjourney/DALL-E/Flux/SD-API tiers monthly, normalized. `free-tool-seo` · $0 · M
176. **AI Voice/TTS Pricing & Limits Tracker** — $ per 1,000 chars, monthly caps, and voice-count limits for ElevenLabs/PlayHT/Azure/Google, versioned. `free-tool-seo` · $0 · M
177. **Vercel/Netlify/CF Pages Free Tier Benchmark** — Cron records published free-tier limits (bandwidth, build min, functions) of static hosts monthly and flags changes. `free-tool-seo` · $0 · M
178. **AI Tool Review Sentiment Index** — Scrapes G2/Reddit/Trustpilot mention counts + star averages per tool monthly into a tracked sentiment-over-time score. `dataset-report` · $29 · L
179. **Cron/Cloud Cost Reality Index** — Publishes the engine's own real monthly spend by line item across Actions/Supabase/Vercel/OpenAI as a live dashboard. `free-tool-seo` · $0 · S
180. **Best AI Tool Deals Monitor** — Cron scrapes vendor deal pages for promos, lifetime deals, and coupon codes; publishes a freshness-stamped live deals page. `affiliate` · $0 · M
181. **Dataset: LLM API Pricing History CSV** — Auto-updated CSV of every model's $/1M tokens, context window, and release date, refreshed weekly by cron. `dataset-report` · $29 · M

## Lead Magnets

182. **Free-Tier Tripwire Alerts** — Email list that pings subscribers when Supabase/Vercel/GitHub free-tier limits or pricing change, with the diff. `lead-magnet` · email-gated · M
183. **7-Day Ship-a-Microtool Challenge** — Daily drip email course from idea to a deployed client-side WebCrypto tool on GitHub Pages in 7 days. `lead-magnet` · email-gated · M
184. **The Supabase Snippet of the Week** — Weekly email with one copy-paste SQL/RLS/Edge snippet plus a 60-second explainer, from a curated vault. `lead-magnet` · email-gated · S
185. **Build-in-Public Numbers Newsletter** — Weekly email auto-generated from the engine's Supabase tables: traffic, signups, revenue, what shipped, what flopped. `lead-magnet` · email-gated · S
186. **30-Day Programmatic SEO Bootcamp** — Daily email series teaching you to spin an "X every Y" page cluster on GitHub Pages, one step per day. `lead-magnet` · email-gated · L
187. **Webhook Provider Cheat Vault** — Email-gated directory of signature-verification snippets and header formats for 30+ providers. `lead-magnet` · email-gated · M
188. **OpenAI Pricing Pulse** — Email alert that fires when OpenAI model prices/limits/deprecations change, with a per-1k-token before/after table. `lead-magnet` · email-gated · M
189. **Automatiza tu Negocio (curso por email ES)** — 10-day Spanish drip course to build an autonomous pipeline with GitHub Actions and Supabase free. `lead-magnet` · email-gated · M
190. **Curated Indie Dev Job & Bounty Board** — Email-gated weekly directory of remote contract gigs, doc bounties, and small paid dev tasks. `lead-magnet` · email-gated · M
191. **The Deprecation Desk** — Weekly email listing API/library/runtime deprecations devs must act on this week, with the migration one-liner. `lead-magnet` · email-gated · M
192. **The Long-Tail Keyword Drop** — Weekly email of 20 low-competition dev/SEO keywords with volume estimates and a tool/page idea for each. `lead-magnet` · email-gated · M
193. **RankInLLMs (AI-search visibility report)** — Email-gated report: how a brand/keyword surfaces in ChatGPT, Perplexity, and Gemini answers with screenshots and gaps. `lead-magnet` · email-gated · M
194. **Weekly AI Tools Movers Report** — Auto-emailed digest of the week's price changes, new free tiers, outages, and model launches from the monitor tables. `lead-magnet` · email-gated · M
195. **The Free Alternatives Almanac** — Monthly email-gated directory matching paid dev SaaS to a $0/free-tier substitute, with the catch and a migration note. `lead-magnet` · email-gated · M

## Distribution & Affiliate

196. **Indie Hacker Stack Directory** — Browsable directory of $0/cheap tools by category with affiliate links and an email-gated "starter stack" export. `affiliate` · $0 · L
197. **Connect Supabase to X (integration pages)** — Programmatic "how to connect Supabase to [Zapier/Make/Retool/Stripe/Resend]" pages, each ending in a partner affiliate link. `affiliate` · $0 · M
198. **Embeddable Uptime/Status Badge** — Free embeddable "cron last ran X ago" heartbeat badge devs paste on dashboards; every embed is a referer + backlink. `lead-magnet` · $0 · M
199. **Embeddable "Is It Down?" Mini-Pages** — Viral single-purpose "is [GitHub/Supabase/Vercel/OpenAI] down right now?" pages that capture outage-spike traffic and funnel to tools. `free-tool-seo` · $0 · M
200. **AI Coding Tools Affiliate Review Hub** — "Copilot vs Cursor vs Codeium vs Windsurf" hub with pricing, model support, and IDE-fit tables linking to each referral program. `affiliate` · $0 · M

---

## Top picks por objetivo (por dónde empezar)

**Tráfico rápido y barato (S, alto volumen de búsqueda):**
- #153 EmojiMeaning, #152 ColorNamer, #142 PortPedia, #139 ErrCodex, #144 MIMEFinder, #143 ExitCodes Atlas — clusters pSEO de miles de páginas, esfuerzo bajo.
- #14 HashForge, #31 QRForge, #7 JSONLint Pro, #10 Base64 Studio — tools dev de alto volumen.

**Dinero más rápido (servicios, un cliente > una semana de chamba):**
- #128 Broken Webhook Emergency Fix ($149), #119 Custom Domain + SSL + Email ($99), #117 GSC Setup ($129), #112 Firebase→Supabase Rescue ($399).

**Edge en español (baja competencia, Alexis es nativo):**
- #12 RegexBuilder ES, #50 MargenYa, #70 PesoConvert, #150 StatusCake ES, #151 ConviertePDF ES, #161 AI Tools Comparador ES, #189 Automatiza tu Negocio.

**Data que nadie más tiene (imán de links + autoridad):**
- #162 AI Tool Price Index, #163 LLM API Uptime Monitor, #166 Token Price Tracker, #179 Cron/Cloud Cost Reality Index.
