# Roadmap de ingeniería — Infinite Revenue Engine

Backlog priorizado de las mejoras que mueven el loop de dinero. El banco
completo de 184 ideas está en [IDEAS.md](IDEAS.md); esto es solo lo que
requiere **código** y cierra el ciclo de cobro.

## ✅ Hecho

- [x] Tracker en Vercel (`/click`, `/webhooks/conversion/{provider}`, `/webhooks/buymeacoffee`) — vivo y probado
- [x] 10 microtools funcionales client-side (cron, env auditor, docker, OpenAI cost, webhook HMAC, regex, llms.txt, AI robots.txt, SupaCost, RLS Forge)
- [x] Notificador de Discord vía webhook (resumen diario, conversiones, errores)
- [x] Catálogo de 109 ideas sembrado en Supabase + GitHub
- [x] **Stripe Payment Links por API** (`--create-stripe-links`) — listo, falta solo `STRIPE_SECRET_KEY`

## 🔜 Alta prioridad (cierra el cobro)

- [ ] **Webhook de Stripe firmado**: validar `Stripe-Signature` (HMAC) en `/webhooks/conversion/stripe` antes de aceptar — hoy usa token plano. El microtool HMAC ya tiene la lógica de referencia.
- [ ] **Captura de email real**: conectar `LEAD_CAPTURE_URL` a MailerLite/Buttondown/Resend y disparar la secuencia de bienvenida (5 emails "De cron a cobro").
- [ ] **Cross-traffic con aipickd.com**: publicar 10-15 artículos de automatización en aipickd que enlacen a los microtools (canal propio, link equity casi gratis).
- [ ] **Sistema de winners**: job semanal que calcula CTR/conversión por oferta desde `click_events`+`conversion_events`, marca `winner=true` y auto-genera 10 variantes de las ganadoras.

## 🟡 Media prioridad (más tráfico/inventario)

- [ ] **Tool Factory**: pipeline hourly que toma la keyword-opportunity top y autogenera un microtool HTML nuevo (con checks de sanidad) → el inventario crece solo.
- [ ] **pSEO de cron**: generar ~300 páginas estáticas "cron every X" / "github actions schedule every Monday" — long-tail masivo de intención dev.
- [ ] **Más microtools de alto score**: CronCraft (generador YAML de cron), SupaJWT (decoder), ActionsBill (calculadora de minutos), GitUndo (wizard), JWTBench, HMACBox, CSV2SQL, DockerAudit, JQBox, OGPreview, SPFCheck.
- [ ] **Self-healing workflows**: retry con backoff + issue automático en fallo (nació del outage de cold-start, commit b1444aa).

## 🟢 Baja prioridad / largo plazo

- [ ] Dashboard web de revenue/clicks/offers/errores (Pages estático leyendo Supabase con anon key + RLS de solo lectura).
- [ ] Reporte diario/semanal automatizado por email además de Discord.
- [ ] GitHub Marketplace Action propia (`supabase-auto-backup`) como canal de adquisición + sponsorship.
- [ ] Gumroad/Lemon Squeezy automation para productos digitales (espejo de la integración de Stripe).
- [ ] Versión bilingüe ES/EN de los microtools (mercado dev hispano poco atendido — CronGuru ES, etc.).

## Reglas que se mantienen

Solo canales propios (sitio, repo, blog aipickd, newsletter, store). Nada de
spam, nada de respuestas AI en Stack Overflow, nada de links de pago en
comunidades ajenas. No commitear `.env`. No imprimir secretos.
