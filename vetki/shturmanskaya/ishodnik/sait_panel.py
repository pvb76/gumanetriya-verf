#!/usr/bin/env python3
# 25.11.2026 панель «Сайт и бюро»: связка сайта, аналитики и бюро бухгалтера. Только числа, без имён, почт и телефонов.
# Источники: журнал Caddy (люди = запросы /hit, их шлёт только браузер с JS), таблица оплат n8n (заказы с сайта), папки бюро (стадии).
# Ничего никуда не шлёт. Страница: https://gumanetriya.ru/v/<секретная папка>/sait.html, обновление раз в час (sait-panel.timer).
import sys, os, re, json, gzip, glob, html, hashlib, datetime, collections, urllib.request, urllib.parse
sys.path.insert(0, '/opt/klon')
import panel_stil as S
EKB = datetime.timezone(datetime.timedelta(hours=5)); NOW = datetime.datetime.now(EKB)
D = '/var/lib/gonets/stat'; OUT = '/opt/stack/vitrina/v'
LOGDIR = open('/etc/gonets-sait-log').read().strip() if os.path.exists('/etc/gonets-sait-log') else '/var/lib/docker/volumes/stack_caddy_data/_data'
BYURO = '/home/foma/byuro'
KEYF = '/home/foma/seif/sobrano/pesochnica/n8n_api_key'
T_PL = 'xlJI9BGFIo06afAn'
DAYS = 30
def day(dt): return dt.astimezone(EKB).strftime('%Y-%m-%d')
cut = NOW - datetime.timedelta(days=DAYS)
# --- 1. посещения из журнала Caddy
STEP = [('/', 'главная'), ('/oplata.html', 'каталог'), ('/usluga.html', 'карточка услуги'), ('/oplata-ok.html', 'после оплаты'), ('/zakaz.html', 'мой заказ')]
def norm(p):
    p = (p or '/').split('?')[0].split('#')[0]
    if p in ('', '/index.html'): p = '/'
    if p.startswith('/en/'): p = p[3:] or '/'
    return p
vis = collections.defaultdict(set)        # (день, шаг) -> {посетитель}
uniq = collections.defaultdict(set)       # день -> {посетитель}
refs = collections.Counter()
nlines = 0
files = sorted(glob.glob(LOGDIR + '/vitrina*.log*'))
for f in files:
    try:
        if os.path.getmtime(f) < cut.timestamp(): continue
        fh = gzip.open(f, 'rt', errors='replace') if f.endswith('.gz') else open(f, errors='replace')
    except Exception: continue
    for ln in fh:
        if '/hit?' not in ln: continue
        try: o = json.loads(ln)
        except Exception: continue
        rq = o.get('request') or {}; uri = rq.get('uri', '')
        if not uri.startswith('/hit?'): continue
        ts = datetime.datetime.fromtimestamp(float(o.get('ts', 0)), EKB)
        if ts < cut: continue
        q = urllib.parse.parse_qs(uri[5:]); p = norm((q.get('p') or ['/'])[0]); r = (q.get('r') or [''])[0]
        ua = ((rq.get('headers') or {}).get('User-Agent') or [''])[0]
        if re.search(r'bot|crawl|spider|headless|lighthouse|playwright', ua, re.I): continue
        who = hashlib.sha1(((rq.get('client_ip') or rq.get('remote_ip') or '') + ua).encode()).hexdigest()[:12]
        d = day(ts); uniq[d].add(who); nlines += 1
        for sp, name in STEP:
            if p == sp: vis[(d, name)].add(who)
        if r:
            h = urllib.parse.urlparse(r).hostname or ''
            if h and 'gumanetriya' not in h: refs[h.replace('www.', '')] += 1
# --- 2. заказы с сайта из таблицы оплат n8n
orders = []
err = ''
try:
    key = open(KEYF).read().strip(); nxt = None
    for _ in range(20):
        u = f'https://n8n.gumanetriya.ru/api/v1/data-tables/{T_PL}/rows?limit=250&sortBy=createdAt:desc' + (f'&cursor={nxt}' if nxt else '')
        j = json.load(urllib.request.urlopen(urllib.request.Request(u, headers={'X-N8N-API-KEY': key}), timeout=60))
        for x in j.get('data', []):
            if not str(x.get('chat', '')).startswith('sait:'): continue
            ts = datetime.datetime.fromisoformat(str(x.get('createdAt')).replace('Z', '+00:00'))
            if ts < cut: continue
            try: s = float(str(x.get('sum') or 0).replace(',', '.'))
            except Exception: s = 0
            what = re.sub(r'^Корзина:\s*', '', str(x.get('what') or ''))
            orders.append({'d': day(ts), 'sum': s, 'paid': bool(x.get('done')) and not bool(x.get('cancel')), 'cancel': bool(x.get('cancel')), 'what': what})
        nxt = j.get('nextCursor')
        if not nxt: break
except Exception as e: err = type(e).__name__
# --- 3. бюро: стадии дел (только количество файлов)
stages = [('01-пришло', 'пришло'), ('02-в-работе', 'в работе'), ('03-сдано-и-отчёты', 'сдано')]
bst = {}
for st, name in stages:
    n = 0
    for p in glob.glob(f'{BYURO}/*/{st}') + glob.glob(f'{BYURO}/*/*/{st}'):
        for _, _, fs in os.walk(p): n += len([f for f in fs if not f.startswith('.')])
    bst[name] = n
try: nklient = len([x for x in os.listdir(BYURO) if not x.startswith('.') and os.path.isdir(os.path.join(BYURO, x))])
except Exception: nklient = 0
# --- расчёт
d7 = (NOW - datetime.timedelta(days=7)).strftime('%Y-%m-%d')
def step7(name): return len(set().union(*[v for (d, n), v in vis.items() if n == name and d >= d7] or [set()]))
people7 = len(set().union(*[v for d, v in uniq.items() if d >= d7] or [set()]))
o7 = [o for o in orders if o['d'] >= d7]
paid30 = [o for o in orders if o['paid']]
funnel = [('люди на сайте', people7)] + [(n, step7(n)) for _, n in STEP[:3]] + [('создали заказ', len(o7)), ('оплатили', len([o for o in o7 if o['paid']]))]
dates = sorted(set(uniq) | {o['d'] for o in orders})
top = collections.Counter()
for o in orders:
    for part in re.split(r';\s*|\n', o['what']):
        t = re.sub(r'\s*\(.*', '', part).strip()
        if t: top[t] += 1
def card(t, n, sub): return f'<div class=card><b>{html.escape(t)}</b><div class=n>{n}</div><small>{html.escape(sub)}</small></div>'
cards = (card('Люди на сайте', people7, 'за 7 дней, без роботов') + card('Открыли каталог', step7('каталог'), 'за 7 дней') +
         card('Заказы с сайта', len(o7), f"за 7 дней · оплачено {len([o for o in o7 if o['paid']])}") +
         card('Оплачено за 30 дней', f"{sum(o['sum'] for o in paid30):,.0f} ₽".replace(',', ' '), f'заказов {len(paid30)}'))
bcards = ''.join(card(f'Бюро: {n}', v, 'файлов в делах') for n, v in bst.items()) + card('Бюро: папок', nklient, 'клиенты и контрагенты')
note = f'Записей посещений за {DAYS} дней: {nlines}. Журналов: {len(files)}.' + (f' Таблица оплат не прочиталась ({err}).' if err else '')
page = S.head('Сайт и бюро — Гуманетрия', 'sait.html') + f'''<h1>Сайт и бюро</h1><p class=sub>Срез {NOW.strftime('%d.%m.%Y %H:%M')} по Екатеринбургу. Обновляется каждый час. Только числа: ни имён, ни почт, ни телефонов.</p>
<h2>Что с сайтом</h2><div class=cards>{cards}</div>
<h2>Путь покупателя за 7 дней</h2><div class=say>Сверху вниз — сколько людей дошло до каждого шага. Резкий обрыв показывает, где теряем покупателя.</div>{S.bars(funnel)}
<h2>По дням</h2><div class=say>Люди на сайте и заказы с сайта.</div>{S.lines({'люди': [(d, len(uniq.get(d, ()))) for d in dates], 'заказы': [(d, len([o for o in orders if o['d'] == d])) for d in dates]})}
<h2>Что заказывают</h2>{S.bars(top.most_common(10))}
<h2>Откуда приходят</h2><div class=say>Сайты, с которых люди перешли к нам. Название нажимается и открывает этот сайт.</div>{S.bars([(h, n, 'https://' + h) for h, n in refs.most_common(8)])}
<h2>Бюро бухгалтера</h2><div class=say>Сколько документов на каждой стадии. Сами дела открываются на столе бюро.</div><div class=cards>{bcards}</div>
<p class=m><a href="/byuro/">Открыть стол бюро</a> · <a href="stat.html">Наши каналы</a> · <a href="mir.html">Что в мире</a></p>
<p class=m>{html.escape(note)} Человек = браузер, который выполнил скрипт страницы; роботы и проверки не считаются.</p></div>'''
sec = open(D + '/sekret').read().strip()
os.makedirs(f'{OUT}/{sec}', exist_ok=True)
open(f'{OUT}/{sec}/sait.html', 'w').write(page)
print('сайт и бюро: люди 7д', people7, '| заказы 7д', len(o7), '| оплачено 30д', len(paid30), '| бюро', bst, '| журналов', len(files), '| ошибка', err or '-')
