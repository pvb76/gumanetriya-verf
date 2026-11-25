# общий стиль панелей Гуманетрии: палитра и шрифты сайта gumanetriya.ru, простые крупные графики «понятно и ребёнку»
import html, re

RUTUBE_TOP = 'https://rutube.ru/feeds/top/'
RUTUBE_OWN = 'https://rutube.ru/channel/82631414/'

def rutube_cards(page):
    """Return public card counters; missing counters do not mean zero."""
    cards = {}
    for block in re.findall(r'<article\b[^>]*>(.*?)</article>', page, re.S):
        link = re.search(r'<a\b[^>]*\bid="cardTitle[0-9a-f]*"[^>]*>', block)
        if not link:
            continue
        attrs = dict(re.findall(r'\b(title|href)="([^"]*)"', link.group(0)))
        url = re.fullmatch(r'/(?:video|shorts)/([0-9a-f]{32})/?', attrs.get('href', ''))
        title = html.unescape(attrs.get('title', '')).strip()
        if not (url and title):
            continue
        view = re.search(r'<p\b[^>]*class="[^"]*__metaInfo(?:V2)?Views\b[^"]*"[^>]*>(.*?)</p>', block, re.S)
        label = html.unescape(re.sub(r'<[^>]*>', ' ', view.group(1))) if view else ''
        label = ' '.join(label.split())
        value = re.match(r'([\d ]+(?:[,.]\d+)?)\s*(тыс\.|млн|млрд)?', label)
        views = None
        if value:
            n, unit = value.groups()
            views = round(float(n.replace(' ', '').replace(',', '.')) *
                          {None: 1, 'тыс.': 1000, 'млн': 1000000, 'млрд': 1000000000}[unit])
        vid = url.group(1)
        created = re.search(r'"id":"' + vid + r'"(?:(?!"id":).){0,2400}?"created_ts":"(\d{4}-\d{2}-\d{2})', page)
        card = dict(id=vid, title=title, url='https://rutube.ru' + attrs['href'],
                    views=views, label=label, date=created.group(1) if created else '')
        if vid not in cards or cards[vid]['views'] is None:
            cards[vid] = card
    return list(cards.values())
CSS = '''@font-face{font-family:Onest;src:url(https://gumanetriya.ru/assets/fonts/Onest-normal-cyrillic.woff2) format("woff2");font-weight:100 900;unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:Onest;src:url(https://gumanetriya.ru/assets/fonts/Onest-normal-latin.woff2) format("woff2");font-weight:100 900;unicode-range:U+0000-00FF,U+20BD}
@font-face{font-family:Literata;src:url(https://gumanetriya.ru/assets/fonts/Literata-normal-cyrillic.woff2) format("woff2");font-weight:200 900;unicode-range:U+0400-04FF,U+2116}
@font-face{font-family:Literata;src:url(https://gumanetriya.ru/assets/fonts/Literata-normal-latin.woff2) format("woff2");font-weight:200 900;unicode-range:U+0000-00FF,U+20BD}
:root{--ink:#131a11;--moss:#31442a;--olive:#7b8c45;--olive2:#a3b46a;--sage:#bccaa3;--mist:#e3ead4;--paper:#f5f2e3;--paper2:#ebe6cf;--cream:#fffbee;--apricot:#f0a868;--apricot2:#ffd6a8;--clay:#b9673c;--teal:#7fb5a5;--rose:#dba59c;--text:#1a2216;--muted:#5d6652}
*{box-sizing:border-box}body{margin:0;background:var(--paper);color:var(--text);font:17px/1.5 Onest,system-ui,sans-serif}
.w{max-width:980px;margin:0 auto;padding:18px 16px 60px}h1,h2{font-family:Literata,Georgia,serif;color:var(--moss);line-height:1.2}h1{font-size:34px;margin:6px 0 4px}h2{font-size:25px;margin:38px 0 4px}
.nav{display:flex;gap:8px;flex-wrap:wrap;margin:6px 0 10px}.nav a{padding:9px 16px;border-radius:99px;background:var(--mist);color:var(--moss);text-decoration:none;font-weight:600}.nav a.on{background:var(--moss);color:var(--cream)}
.sub{color:var(--muted);margin:0 0 10px}.say{background:var(--cream);border-left:6px solid var(--apricot);border-radius:12px;padding:10px 14px;margin:8px 0 14px;font-size:16px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:12px}.card{background:var(--cream);border-radius:18px;padding:14px 16px;border:1px solid rgba(26,34,22,.12)}.card b{display:block;color:var(--moss)}.card .n{font:700 34px Literata,serif;color:var(--clay)}.card small{color:var(--muted)}
.box{background:var(--cream);border-radius:22px;padding:16px;border:1px solid rgba(26,34,22,.12);overflow-x:auto}.bar{display:grid;grid-template-columns:minmax(120px,210px) 1fr;gap:10px;align-items:center;margin:8px 0}.bar .l{font-weight:600;font-size:15px}.bar .t{background:var(--mist);border-radius:99px;height:26px;position:relative}.bar .f{height:26px;border-radius:99px;background:var(--olive);min-width:6px}.bar .v{position:absolute;right:10px;top:2px;font-weight:700;font-size:14px}
.ai{background:var(--moss);color:var(--cream);border-radius:22px;padding:18px 20px;white-space:pre-wrap}.ai b{color:var(--apricot2)}
table{border-collapse:collapse;width:100%;font-size:14px}td,th{border-bottom:1px solid rgba(26,34,22,.12);padding:7px 5px;text-align:left}th{color:var(--muted);font-weight:600}.m{color:var(--muted);font-size:13px}svg text{font-family:Onest,sans-serif}
details.sv{margin:0}details.sv>summary{list-style:none;cursor:pointer}details.sv>summary::-webkit-details-marker{display:none}details.sv>summary h2{display:inline-block}details.sv>summary h2::after{content:" ▾";font-size:18px;color:var(--muted)}details.sv[open]>summary h2::after{content:" ▴"}details.sv>summary small{display:block;color:var(--muted);font-size:14px;margin:-2px 0 6px}
.bar .l a{color:var(--moss);text-decoration:underline;text-underline-offset:3px}
/* PANEL_KRASOTA_V1: штурманская — морская карта, латунь, штампы */
body{background-color:var(--paper);background-image:linear-gradient(rgba(49,68,42,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(49,68,42,.05) 1px,transparent 1px),radial-gradient(60% 40% at 90% 0%,rgba(240,168,104,.12),transparent 70%);background-size:48px 48px,48px 48px,100% 100%;background-attachment:fixed}
h1{position:relative;padding-bottom:10px;border-bottom:3px double #b08d57}h1::before{content:'ШТУРМАНСКАЯ · ГУМАНЕТ';display:block;font:700 11px/1 Onest,sans-serif;letter-spacing:.2em;color:var(--clay);margin:0 0 8px}
h2{display:flex;align-items:center;gap:10px}h2::before{content:'';width:14px;height:14px;flex:none;border:2px solid #b08d57;border-radius:50%;box-shadow:inset 0 0 0 3px var(--paper),inset 0 0 0 6px var(--apricot)}details.sv>summary h2{display:inline-flex}
.card,.box{box-shadow:0 1px 0 rgba(255,255,255,.7) inset,0 14px 30px -22px rgba(20,32,25,.55);border-top:3px solid #b08d57}
.nav a{border:1px solid rgba(176,141,87,.45)}.nav a.on{box-shadow:0 6px 16px -8px rgba(49,68,42,.8)}
.ai{background:#142019;border:1px solid #b08d57}
@media(max-width:640px){h1::before{font-size:10px}}'''
def nav(on):
    L = [('mir.html', 'Что в мире'), ('stat.html', 'Наши каналы'), ('sait.html', 'Сайт и бюро')]
    return '<div class=nav>' + ''.join(f'<a href="{h}"{" class=on" if h == on else ""}>{t}</a>' for h, t in L) + '</div>'
ICONS = {
 'stat.html': "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='16' fill='#31442a'/><rect x='12' y='36' width='9' height='16' rx='3' fill='#bccaa3'/><rect x='27' y='26' width='9' height='26' rx='3' fill='#a3b46a'/><rect x='42' y='14' width='9' height='38' rx='3' fill='#f0a868'/><path d='M12 28 L28 18 L40 22 L53 8' fill='none' stroke='#fffbee' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'/></svg>",
 'mir.html': "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='16' fill='#b9673c'/><circle cx='32' cy='32' r='19' fill='#7fb5a5'/><path d='M32 13c-7 6-7 32 0 38M32 13c7 6 7 32 0 38M13 32h38M16 22h32M16 42h32' fill='none' stroke='#fffbee' stroke-width='2.6' stroke-linecap='round'/><circle cx='32' cy='32' r='19' fill='none' stroke='#fffbee' stroke-width='3'/></svg>",
 'sait.html': "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='16' fill='#f0a868'/><rect x='12' y='14' width='40' height='30' rx='5' fill='#fffbee'/><path d='M12 22h40' stroke='#31442a' stroke-width='3'/><path d='M20 36l7-7 6 5 9-9' fill='none' stroke='#7b8c45' stroke-width='3.5' stroke-linecap='round' stroke-linejoin='round'/><rect x='24' y='46' width='16' height='6' rx='3' fill='#31442a'/></svg>",
 'byuro': "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'><rect width='64' height='64' rx='16' fill='#7b8c45'/><path d='M24 22v-5a4 4 0 0 1 4-4h8a4 4 0 0 1 4 4v5' fill='none' stroke='#fffbee' stroke-width='4' stroke-linecap='round'/><rect x='10' y='22' width='44' height='30' rx='7' fill='#f0a868'/><path d='M10 35h44' stroke='#fffbee' stroke-width='3'/><rect x='28' y='31' width='8' height='9' rx='2' fill='#31442a'/></svg>"}
def head(title, on):
    import urllib.parse
    ic = 'data:image/svg+xml,' + urllib.parse.quote(ICONS.get(on, ICONS['stat.html']))
    return f'<!doctype html><meta charset=utf-8><link rel=icon href="{ic}"><link rel=apple-touch-icon href="{ic}"><meta name=viewport content="width=device-width,initial-scale=1"><meta name=robots content=noindex><title>{html.escape(title)}</title><style>{CSS}</style><div class=w>{nav(on)}'
COL = ['#7b8c45', '#f0a868', '#7fb5a5', '#dba59c', '#b9673c', '#31442a', '#a3b46a', '#c9a36b']
def bars(items, fmt=lambda v: f'{v:.0f}', color=None):
    # items: [(подпись, число)] или [(подпись, число, ссылка)]
    if not items: return '<p class=m>данных пока нет</p>'
    mx = max(it[1] for it in items) or 1; o = ''
    for i, it in enumerate(items):
        n, v = it[0], it[1]; u = it[2] if len(it) > 2 else ''
        lab = f'<a href="{html.escape(u)}" target="_blank" rel="noopener noreferrer">{html.escape(str(n))}</a>' if u else html.escape(str(n))
        o += f'<div class=bar><div class=l>{lab}</div><div class=t><div class=f style="width:{max(2, 100*v/mx):.0f}%;background:{color or COL[i%8]}"></div><span class=v>{fmt(v)}</span></div></div>'
    return '<div class=box>' + o + '</div>'
def lines(series, w=760, h=240):
    allv = [v for s in series.values() for _, v in s]
    if not allv: return '<p class=m>данных пока нет</p>'
    mx = max(allv) or 1; ds = sorted({d for s in series.values() for d, _ in s})
    X = lambda d: 52 + (ds.index(d) * (w - 80) / max(len(ds) - 1, 1)); Y = lambda v: h - 34 - v * (h - 64) / mx
    o = f'<div class=box><svg viewBox="0 0 {w} {h}" width="100%">'
    for i in range(5): y = h - 34 - i * (h - 64) / 4; o += f'<line x1=52 x2={w-20} y1={y:.0f} y2={y:.0f} stroke="#dcd7bd"/><text x=46 y={y+4:.0f} font-size=12 text-anchor=end fill="#5d6652">{mx*i/4:.0f}</text>'
    for d in ds[::max(1, len(ds) // 7)]: o += f'<text x={X(d):.0f} y={h-12} font-size=12 text-anchor=middle fill="#5d6652">{d[8:]}.{d[5:7]}</text>'
    for n, (name, s) in enumerate(series.items()):
        c = COL[n % 8]; s = sorted(s); pts = ' '.join(f'{X(d):.0f},{Y(v):.0f}' for d, v in s)
        o += f'<polyline points="{pts}" fill=none stroke="{c}" stroke-width=3.5 stroke-linecap=round />' + ''.join(f'<circle cx={X(d):.0f} cy={Y(v):.0f} r=4.5 fill="{c}"/>' for d, v in s)
        o += f'<rect x={60+n*150} y=4 width=14 height=14 rx=4 fill="{c}"/><text x={80+n*150} y=16 font-size=13 fill="#1a2216">{html.escape(name)}</text>'
    return o + '</svg></div>'

def sverni(title, body, sub='', open_=False, id_=''):
    """Раздел, который сворачивается: заголовок h2 нажимается."""
    return (f'<details class=sv{" open" if open_ else ""}{f" id={id_}" if id_ else ""}><summary><h2>{html.escape(title)}</h2>'
            + (f'<small>{html.escape(sub)}</small>' if sub else '') + f'</summary>{body}</details>')

def sverni_vse(page, open_titles=(), footer_marker=None):
    """Каждый раздел <h2>…</h2> до следующего <h2> превращает в сворачиваемый. Открыты только open_titles."""
    i = page.find('<h2>')
    if i < 0: return page
    head, rest = page[:i], page[i:]
    foot = ''
    if footer_marker and footer_marker in rest:
        j = rest.rfind(footer_marker); rest, foot = rest[:j], rest[j:]
    elif rest.endswith('</div>'):
        rest, foot = rest[:-6], '</div>'
    out = []
    for ch in rest.split('<h2>')[1:]:
        title, _, body = ch.partition('</h2>')
        out.append(f'<details class=sv{" open" if title in open_titles else ""}><summary><h2>{title}</h2></summary>{body}</details>\n')
    return head + ''.join(out) + foot
