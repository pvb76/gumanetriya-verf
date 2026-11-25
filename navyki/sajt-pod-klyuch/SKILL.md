---
name: sajt-pod-klyuch
description: "Build a complete website for any niche end to end without stopping: niche and competitor research, catalog, design from a real reference, build, on-site payment or lead capture, order status, analytics hook, QA gates, deploy with backup. Use for «сделай сайт под ключ», landing or shop for a client or Gumanetriya. Not for dashboards or small text edits."
metadata:
  author: Foma (Gumanetriya)
  version: "1.0"
---

# Сайт под ключ (end-to-end website)

Run the whole job in one pass. Ask the user only for things that spend money or need their accounts (payment provider keys, OAuth apps, domain purchase). Everything else: decide, state the choice in one line, continue.

## Inputs (fill from the request; never stall on them)

- Niche, business name, city/market, language. Unknown name → use a neutral working name and flag it.
- What is sold: ready products (fixed price, pay now) vs built-to-task (price after agreement).
- Real prices only: from the user, their price list, marketplace profile or existing site. Never invent prices, discounts, reviews, response times or guarantees.
- Where it lives: existing project (build inside its stack), Gumanetriya server, or a standalone folder.

## Workflow

1. **Было?** Search the user's repo/notes for prior work on this site or niche; reuse it.
2. **Research (30–60 min of real pages).** Open 5–10 competitor or reference sites in the niche, plus the authors the user follows if given. For each record: login methods, registration and 2FA, purchase path in clicks, how the product is delivered, prices. Separate facts (seen) from hypotheses. Save as a dated research note. Read `references/vhod-i-oplata.md` before choosing login and payment.
3. **Catalog.** Split offers into "оплата сразу" (ready) and "сначала обсудим" (built-to-task). Each offer: name, one-line result for the client, price "от", term, what is included. Max 10 on the home page.
4. **Design.** Load the `motionsites-web-builder` skill: pick ONE reference design, adapt copy, palette and type to the brand, use the user's own media first. For a website app or dashboard load `website-building` instead. Mobile first: most buyers are on a phone.
5. **Build the buyer path.** Home → offer card → details/consent → payment → "оплата получена" page with order number → short details form that reaches the owner's chat with the order number. Built-to-task offers go to a chat/lead form instead of payment. Add a "Мой заказ" page: status by order number, no registration.
6. **Wire the back end.** Payments and leads through the owner's existing automation (n8n webhooks + data table for orders when available). Keys stay on the server; never print secrets in logs or reports.
7. **Analytics hook.** Count people (JS beacon, robots excluded), catalog opens, orders created, orders paid; show them on the owner's panel without personal data. If the owner has a back office (bureau, CRM), add only counts and links unless asked for more.
8. **QA gates** — run `scripts/qa_site.py <url>` and the screenshot review from `motionsites-web-builder`; read `references/standarty.md` for the exact thresholds. Fix every failure, re-run.
9. **Deploy.** Back up the live root first, deploy with an idempotent script, verify what the server actually serves, roll back automatically on any failed check.
10. **Report.** Per acceptance item: "проверено (как)" or "не проверено (почему)"; one link to the result; one line to the work log.

Done when: every gate in `references/standarty.md` passes on the live URL and the report is written.

## Files

- `references/standarty.md`: acceptance gates and report line format; read at step 8.
- `references/vhod-i-oplata.md`: login and payment options in Russia; read at step 2.
- `references/prompt.md`: the user's bilingual task template; read when the user asks for a site prompt or a reusable task text.
- `scripts/qa_site.py`: crawl + links + dead buttons + 375 px + 16 px + slow-4G speed; run at step 8.

## Rules

- Payment tests that move real money: stop and ask the user once.
- Outgoing messages to clients only after the user's approval.
- Foreign logins (Google, Apple, Telegram Login) are not allowed on Russian sites; see `references/vhod-i-oplata.md`.
- Do not add paid services, animations or blocks beyond the brief.
