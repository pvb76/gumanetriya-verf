#!/usr/bin/env python3
"""Site QA gates: crawl same-site pages, check links, dead buttons, 375 px overflow, text < 16 px, optional slow-4G speed.

Usage:
  python scripts/qa_site.py https://example.ru/ [--max 40] [--speed]
Needs: pip install playwright && python -m playwright install chromium
Prints a JSON report and a one-line verdict per gate. Exit code 1 if any gate fails.
"""
import asyncio, json, sys, urllib.request, urllib.error, concurrent.futures as cf
from urllib.parse import urljoin, urlparse
from playwright.async_api import async_playwright

args = [a for a in sys.argv[1:] if not a.startswith("--")]
if not args: sys.exit(__doc__)
BASE = args[0]; HOST = urlparse(BASE).hostname
MAX = int(sys.argv[sys.argv.index("--max") + 1]) if "--max" in sys.argv else 40
SKIP = ("mailto:", "tel:", "javascript:", "#")

PAGE_JS = """() => {
  const vw = document.documentElement.clientWidth;
  const txt = e => [...e.childNodes].some(t => t.nodeType === 3 && t.textContent.trim());
  const small = [...document.querySelectorAll('body *')].filter(e => e.offsetParent && txt(e) && parseFloat(getComputedStyle(e).fontSize) < 16)
    .slice(0, 6).map(e => e.tagName.toLowerCase() + '.' + (typeof e.className === 'string' ? e.className.split(' ')[0] : '') + ' ' + getComputedStyle(e).fontSize);
  const links = [...document.querySelectorAll('a[href]')].map(a => a.href);
  const dead = [...document.querySelectorAll('a,button,[role=button]')].filter(e => e.offsetParent).filter(e => {
    if (e.tagName === 'A') { const h = e.getAttribute('href') || ''; return h === '' || h === '#' && !e.dataset.chat && !e.onclick; }
    return e.tagName === 'BUTTON' && e.disabled === false && !e.onclick && !e.form && !e.getAttribute('aria-controls') && !e.dataset.chat && !e.closest('form') && !e.id && !e.className;
  }).slice(0, 6).map(e => e.outerHTML.slice(0, 100));
  return {sw: document.documentElement.scrollWidth, vw, small, links, buttons: document.querySelectorAll('a,button,[role=button]').length, dead};
}"""

def check(u):
    for m in ("HEAD", "GET"):
        try:
            r = urllib.request.Request(u, method=m, headers={"User-Agent": "Mozilla/5.0 (Linux; Android 13) Chrome/124 Mobile"})
            with urllib.request.urlopen(r, timeout=20) as x: return u, x.status
        except urllib.error.HTTPError as e:
            if m == "GET": return u, e.code
        except Exception as e:
            if m == "GET": return u, str(e)[:60]

async def speed(p):
    b = await p.chromium.launch(); ctx = await b.new_context(viewport={"width": 375, "height": 800}, is_mobile=True, device_scale_factor=2)
    pg = await ctx.new_page(); c = await ctx.new_cdp_session(pg)
    await c.send("Network.enable"); await c.send("Network.setCacheDisabled", {"cacheDisabled": True})
    await c.send("Network.emulateNetworkConditions", {"offline": False, "latency": 150, "downloadThroughput": 1.6e6 / 8, "uploadThroughput": 750e3 / 8})
    await c.send("Emulation.setCPUThrottlingRate", {"rate": 4})
    await pg.add_init_script("window.__lcp=0;new PerformanceObserver(l=>{for(const e of l.getEntries())window.__lcp=e.startTime}).observe({type:'largest-contentful-paint',buffered:true});")
    await pg.goto(BASE, wait_until="load", timeout=90000); await pg.wait_for_timeout(2500)
    r = await pg.evaluate("()=>{const n=performance.getEntriesByType('navigation')[0];return {load:Math.round(n.loadEventEnd),lcp:Math.round(window.__lcp)}}")
    await b.close(); return r

async def main():
    rep = {"pages": {}, "links": {}, "fail": []}
    async with async_playwright() as p:
        b = await p.chromium.launch()
        for w in (375, 1280):
            ctx = await b.new_context(viewport={"width": w, "height": 820}, is_mobile=w < 500, has_touch=w < 500)
            todo, seen = [BASE], set()
            while todo and len(seen) < MAX:
                u = todo.pop(0).split("#")[0]
                if u in seen: continue
                seen.add(u); pg = await ctx.new_page()
                try:
                    await pg.goto(u, wait_until="networkidle", timeout=45000); await pg.wait_for_timeout(800)
                    r = await pg.evaluate(PAGE_JS)
                except Exception as e:
                    r = {"error": str(e)[:80], "links": [], "sw": 0, "vw": w, "small": [], "buttons": 0, "dead": []}
                await pg.close()
                rep["pages"].setdefault(u, {})[w] = {k: r[k] for k in r if k != "links"}
                for l in r["links"]:
                    if l.startswith(SKIP): continue
                    rep["links"][l.split("#")[0]] = None
                    if urlparse(l).hostname == HOST and l.split("#")[0] not in seen and not l.endswith((".pdf", ".zip", ".mp4", ".jpg", ".png", ".webp")):
                        todo.append(l)
            await ctx.close()
        await b.close()
        links = [l for l in rep["links"] if l.startswith("http")]
        with cf.ThreadPoolExecutor(12) as ex:
            for u, st in ex.map(check, links): rep["links"][u] = st
        if "--speed" in sys.argv: rep["speed"] = await speed(p)
    over = [u for u, v in rep["pages"].items() if v.get(375, {}).get("sw", 0) > 375]
    small = {u: v[375]["small"] for u, v in rep["pages"].items() if v.get(375, {}).get("small")}
    dead = {u: v[w]["dead"] for u, v in rep["pages"].items() for w in v if v[w].get("dead")}
    blocked = {u: s for u, s in rep["links"].items() if s in (401, 403, 429)}   # защита от роботов: проверить в браузере
    broken = {u: s for u, s in rep["links"].items() if not (isinstance(s, int) and s < 400) and u not in blocked}
    nbtn = sum(v[w]["buttons"] for v in rep["pages"].values() for w in v)
    print(json.dumps({"overflow_375": over, "small_text_375": small, "dead_buttons": dead, "broken_links": broken, "blocked_check_in_browser": blocked, "speed": rep.get("speed")}, ensure_ascii=False, indent=1))
    g = [("375 px без прокрутки вбок", not over, f"{len(rep['pages'])} страниц"), ("текст ≥ 16 px на телефоне", not small, f"{len(small)} страниц с мелким"),
         ("0 мёртвых кнопок", not dead, f"проверено {nbtn}"), ("0 битых ссылок", not broken, f"проверено {len(links)}, битых {len(broken)}, закрыто от роботов {len(blocked)} — открыть их в браузере")]
    if rep.get("speed"): g.append(("главная < 3 с", rep["speed"]["load"] < 3000, f"load {rep['speed']['load']} мс, LCP {rep['speed']['lcp']} мс"))
    for n, ok, how in g: print(("OK   " if ok else "FAIL ") + n + " — " + how)
    sys.exit(0 if all(ok for _, ok, _ in g) else 1)

asyncio.run(main())
