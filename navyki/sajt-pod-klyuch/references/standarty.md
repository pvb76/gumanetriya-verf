# Acceptance gates (check on the live URL)

| Gate | Threshold | How to check |
|---|---|---|
| Path to pay | ≤ 5 clicks from home to the bank page, no messenger jump | Playwright walk at 375 px and 1280 px |
| Links | 0 broken (HTTP ≥ 400 or DNS fail); count checked links | `scripts/qa_site.py` crawl; sites that block robots → verify in a real browser and say so |
| Buttons | 0 dead (no href/handler, or click does nothing) | qa_site.py button pass; report the count |
| Phone layout | 375 px: scrollWidth = 375 on every page | qa_site.py |
| Text size | body text ≥ 16 px at ≤ 600 px | qa_site.py (lists offenders) |
| Speed | home load < 3 s, LCP < 2.5 s on slow 4G (1.6 Mbit/s, RTT 150 ms, CPU ×4) | qa_site.py `--speed` |
| Payment | test order appears in the orders table; return page shows status and order number | real order only with the user's OK; otherwise unpaid probe |
| Details form | message with the order number reaches the owner's chat | check the automation execution log |
| Look | screenshot rubric average ≥ 8, no score < 7, nothing overlaps on mobile | motionsites `references/review.md` |
| Copy | short, human, no promises beyond fact, one CTA verb per block | read every page once |

Report format, one line each: `N. <gate> — проверено (<how>, <number>)` or `не проверено (<why>)`.
