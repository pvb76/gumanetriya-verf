# 25.11.2026 «Наши каналы»: одна таблица по всем площадкам — люди, просмотры, заявки, оплаты за 7 и 30 дней,
# у каждой строки дата среза и источник (открытые данные / кабинет / нет доступа). Нет числа — пишем «нет данных», не ноль.
# Вывод из пяти строк строится по правилам из этих же чисел (без модели, чтобы не выдумать). Ничего никуда не шлёт.
import os, re, json, glob, gzip, html, hashlib, datetime, urllib.request, urllib.parse, collections

EKB = datetime.timezone(datetime.timedelta(hours=5))
SEIF = '/home/foma/seif/'
KAPITAN_CHAT = os.environ.get('KAPITAN_CHAT', '')  # id чата владельца: его пробы не считаются продажами
ND, NA = 'нет данных', 'нет доступа'
URL = {'Telegram: Мастерская': 'https://t.me/gumanetriya_ai', 'Telegram: 3D': 'https://t.me/gumanetriya_3d', 'YouTube': 'https://youtube.com/@gumanetriya',
       'RUTUBE': 'https://rutube.ru/channel/82631414/', 'ВКонтакте': 'https://vk.com/club242703612', 'MAX: канал «Гуманет»': 'https://max.ru/se15096221_biz',
       'Авито': 'https://www.avito.ru/brands/31e395ff57880874e5112425a482cb9a', 'Дзен': 'https://dzen.ru/gumanetriya', 'Kwork': '{{KWORK_URL}}',
       'FL.ru': 'https://www.fl.ru/users/pvb76/', 'Lava.top': 'https://app.lava.top/gumanetriya', 'Сайт gumanetriya.ru': 'https://gumanetriya.ru/'}
OPEN, CAB, NOACC = 'открытые данные', 'кабинет', 'нет доступа'


def _get(url, data=None, h=None, js=None):
    h = dict(h or {}); body = None
    if js is not None: body = json.dumps(js).encode(); h['Content-Type'] = 'application/json'
    elif data is not None: body = urllib.parse.urlencode(data).encode(); h['Content-Type'] = 'application/x-www-form-urlencoded'
    return json.load(urllib.request.urlopen(urllib.request.Request(url, data=body, headers=h), timeout=40))


def dm(d): return f'{d[8:10]}.{d[5:7]}' if d and len(d) >= 10 else ''


# ---------- счёт по истории срезов (snap.jsonl)
def okno_prosmotry(old, p, days, now):
    """Просмотры, набранные за окно: сумма приростов по постам. Если истории меньше окна — считаем с первого среза и помечаем."""
    by = collections.defaultdict(dict)
    for o in old:
        if o.get('p') == p and 'id' in o: by[o['d']][o['id']] = o['views']
    if not by: return None, '', False
    ds = sorted(by); last = ds[-1]
    start = (now - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    base = max([d for d in ds if d <= start], default=None); partial = base is None
    if partial: base = ds[0]
    if base == last and partial:
        return None, last, True
    first_val = {}
    for d in ds:
        for i, v in by[d].items(): first_val.setdefault(i, v)
    tot = 0
    for i, v in by[last].items():
        b = by[base].get(i)
        if b is None: b = 0 if i not in by[base] and not any(i in by[d] for d in ds if d <= base) else first_val.get(i, 0)
        tot += max(0, v - b)
    return tot, last, (base if partial else False)


def okno_lyudi(old, p, days, now):
    s = sorted((o['d'], o['subs']) for o in old if o.get('p') == p and 'subs' in o and o['subs'] >= 0)
    if not s: return None, None, '', False
    last_d, cur = s[-1]
    start = (now - datetime.timedelta(days=days)).strftime('%Y-%m-%d')
    base = [x for x in s if x[0] <= start]
    if base: return cur, cur - base[-1][1], last_d, False
    if s[0][0] == last_d: return cur, None, last_d, s[0][0]
    return cur, cur - s[0][1], last_d, s[0][0]


def vsego_prosmotrov(old, p):
    by = collections.defaultdict(dict)
    for o in old:
        if o.get('p') == p and 'id' in o: by[o['d']][o['id']] = o['views']
    if not by: return None, ''
    last = max(by); return sum(by[last].values()), last


# ---------- Авито: кабинет через API (ключ в сейфе), копим дни
def avito(D, now):
    path = D + '/avito_days.json'
    try: days = json.load(open(path))
    except Exception: days = {}
    err = ''; chats = []
    try:
        k = json.load(open(SEIF + 'avito.json'))
        tok = _get('https://api.avito.ru/token/', {'grant_type': 'client_credentials', 'client_id': k['client_id'], 'client_secret': k['client_secret']})['access_token']
        A = {'Authorization': 'Bearer ' + tok}
        uid = _get('https://api.avito.ru/core/v1/accounts/self', h=A)['id']
        ids = [x['id'] for x in _get('https://api.avito.ru/core/v1/items?per_page=100', h=A).get('resources', [])]
        d2 = now.date(); d1 = d2 - datetime.timedelta(days=29)
        st = _get(f'https://api.avito.ru/stats/v1/accounts/{uid}/items', h=A, js={'dateFrom': str(d1), 'dateTo': str(d2), 'itemIds': ids[:200], 'fields': ['uniqViews', 'uniqContacts', 'uniqFavorites'], 'periodGrouping': 'day'})
        fresh = collections.defaultdict(lambda: {'v': 0, 'c': 0})
        for it in st.get('result', {}).get('items', []):
            for s in it.get('stats', []):
                fresh[s['date']]['v'] += s.get('uniqViews', 0); fresh[s['date']]['c'] += s.get('uniqContacts', 0)
        for d, v in fresh.items(): days[d] = v
        days['_ads'] = len(ids); days['_srez'] = now.strftime('%Y-%m-%d')
        chats = [c.get('created', 0) for c in _get(f'https://api.avito.ru/messenger/v2/accounts/{uid}/chats?limit=100', h=A).get('chats', [])]
        days['_chats'] = chats
        json.dump(days, open(path, 'w'))
    except Exception as e:
        err = type(e).__name__; chats = days.get('_chats', [])
    def summ(n, key):
        start = (now - datetime.timedelta(days=n - 1)).strftime('%Y-%m-%d')
        ks = [d for d in days if not d.startswith('_') and d >= start]
        return sum(days[d][key] for d in ks) if ks else None
    def chat_n(n): return len([c for c in chats if c >= (now - datetime.timedelta(days=n)).timestamp()])
    return {'v7': summ(7, 'v'), 'v30': summ(30, 'v'), 'c7': summ(7, 'c'), 'c30': summ(30, 'c'), 'ch7': chat_n(7), 'ch30': chat_n(30),
            'ads': days.get('_ads'), 'srez': days.get('_srez', ''), 'err': err}


# ---------- Lava: кабинет через API
def lava(now):
    try:
        key = open(SEIF + 'lava_api_key').read().strip()
        j = _get('https://gate.lava.top/api/v1/sales?page=0&size=100', h={'X-Api-Key': key, 'Accept': 'application/json'})
        items = j.get('items', []) if isinstance(j, dict) else []
        def n(days):
            c = 0
            for it in items:
                d = str(it.get('createdAt') or it.get('date') or it.get('created') or '')[:10]
                if d and d >= (now - datetime.timedelta(days=days)).strftime('%Y-%m-%d'): c += 1
            return c
        return {'p7': n(7), 'p30': n(30), 'total': j.get('total', len(items)), 'srez': now.strftime('%Y-%m-%d'), 'err': ''}
    except Exception as e:
        return {'err': type(e).__name__}


# ---------- n8n: оплаты и диалоги чата сайта
def n8n(now):
    out = {'err': ''}
    try:
        key = open(SEIF + 'sobrano/pesochnica/n8n_api_key').read().strip()
        H = {'X-N8N-API-KEY': key}
        rows = []; nxt = None
        for _ in range(20):
            j = _get('https://n8n.gumanetriya.ru/api/v1/data-tables/xlJI9BGFIo06afAn/rows?limit=250' + (f'&cursor={nxt}' if nxt else ''), h=H)
            rows += j.get('data', []); nxt = j.get('nextCursor')
            if not nxt: break
        out['rows'] = rows
        ex = []; nxt = None
        for _ in range(10):
            j = _get('https://n8n.gumanetriya.ru/api/v1/executions?workflowId=aMaOxiWP0e5sNkiJ&limit=100&includeData=true' + (f'&cursor={nxt}' if nxt else ''), h=H)
            for x in j.get('data', []):
                s = json.dumps(x.get('data', {}))[:300000]
                m = re.search(r'\\"sid\\":\s*\\"([^\\"]+)', s) or re.search(r'"sid":\s*"([^"]+)', s)
                ex.append((x.get('startedAt', ''), m.group(1) if m else ''))
            nxt = j.get('nextCursor')
            if not nxt: break
        out['chat'] = ex
    except Exception as e:
        out['err'] = type(e).__name__
    return out


def orders_calc(o, now):
    res = {}
    if o.get('err') and 'rows' not in o: return None
    def since(n): return (now - datetime.timedelta(days=n)).astimezone(datetime.timezone.utc).strftime('%Y-%m-%dT%H:%M')
    for n in (7, 30):
        rs = [x for x in o['rows'] if str(x.get('createdAt', '')) >= since(n)]
        kap = [x for x in rs if KAPITAN_CHAT in str(x.get('chat', '')) or str(x.get('what', '')).startswith('Проба')]
        cl = [x for x in rs if x not in kap]
        paid = [x for x in cl if x.get('done') and not x.get('cancel') and not x.get('refund')]
        site = [x for x in cl if str(x.get('chat', '')).startswith('sait:')]
        def fsum(l): return sum(float(str(x.get('sum') or 0).replace(',', '.')) for x in l)
        res[n] = {'paid': len(paid), 'paid_sum': fsum(paid), 'site': len(site), 'site_cancel': len([x for x in site if x.get('cancel')]),
                  'kap': len(kap), 'kap_paid': len([x for x in kap if x.get('done') and not x.get('cancel')]),
                  'site_paid': len([x for x in paid if str(x.get('chat', '')).startswith('sait:')]),
                  'bot_paid': len([x for x in paid if not str(x.get('chat', '')).startswith('sait:')])}
        ch = [(t, s) for t, s in o.get('chat', []) if t >= since(n) and s and not s.startswith('test')]
        res[n]['dialogs'] = len({s for _, s in ch})
    first = min((t for t, _ in o.get('chat', [])), default='')
    res['chat_from'] = first[:10]
    res['srez'] = now.strftime('%Y-%m-%d')
    return res


# ---------- сайт: журнал Caddy (люди = браузер, выполнивший скрипт /hit)
def sait(now):
    logdir = open('/etc/gonets-sait-log').read().strip() if os.path.exists('/etc/gonets-sait-log') else '/var/lib/docker/volumes/stack_caddy_data/_data'
    cut = now - datetime.timedelta(days=30)
    who = collections.defaultdict(set); hits = collections.Counter(); first = None
    for f in sorted(glob.glob(logdir + '/vitrina*.log*')):
        try:
            if os.path.getmtime(f) < cut.timestamp(): continue
            fh = gzip.open(f, 'rt', errors='replace') if f.endswith('.gz') else open(f, errors='replace')
        except Exception: continue
        for ln in fh:
            if '/hit?' not in ln: continue
            try: o = json.loads(ln)
            except Exception: continue
            rq = o.get('request') or {}
            if not rq.get('uri', '').startswith('/hit?'): continue
            ts = datetime.datetime.fromtimestamp(float(o.get('ts', 0)), EKB)
            if ts < cut: continue
            ua = ((rq.get('headers') or {}).get('User-Agent') or [''])[0]
            if re.search(r'bot|crawl|spider|headless|lighthouse|playwright', ua, re.I): continue
            d = ts.strftime('%Y-%m-%d'); first = min(first or d, d)
            who[d].add(hashlib.sha1(((rq.get('client_ip') or rq.get('remote_ip') or '') + ua).encode()).hexdigest()[:12]); hits[d] += 1
    if not who: return None
    def win(n):
        s = (now - datetime.timedelta(days=n - 1)).strftime('%Y-%m-%d')
        return len(set().union(*[v for d, v in who.items() if d >= s] or [set()])), sum(v for d, v in hits.items() if d >= s)
    p7, h7 = win(7); p30, h30 = win(30)
    return {'p7': p7, 'p30': p30, 'h7': h7, 'h30': h30, 'first': first, 'srez': now.strftime('%Y-%m-%d')}


# ---------- ручные срезы из кабинетов (через Comet, с датой): /var/lib/gonets/stat/kabinet_ruchnoy.json
def ruchnoy(D):
    try: return json.load(open(D + '/kabinet_ruchnoy.json'))
    except Exception: return {}


# ---------- сборка строк
def build(D, old, now, vkinfo):
    rows = []  # kanal, pokaz, vsego, d7, d30, srez, ist, prim
    def R(k, p, vs, a7, a30, srez, ist, prim=''):
        rows.append({'k': k, 'p': p, 'vs': vs, 'd7': a7, 'd30': a30, 'srez': srez or now.strftime('%Y-%m-%d'), 'ist': ist, 'prim': prim})
    def sign(x): return f'{x:+d}' if isinstance(x, int) else x
    def part(v, b): return f'{v} (с {dm(b)})' if b and v is not None else v
    def soc(k, p, ist_people=OPEN, ist_views=OPEN, views_na=None, people_prim=''):
        cur, d7, sz, b7 = okno_lyudi(old, p, 7, now); _, d30, _, b30 = okno_lyudi(old, p, 30, now)
        if cur is None: R(k, 'Люди (подписчики)', ND, ND, ND, '', NOACC)
        else: R(k, 'Люди (подписчики)', cur, part(sign(d7), b7) if d7 is not None else ND, part(sign(d30), b30) if d30 is not None else ND, sz, ist_people, people_prim)
        if views_na: R(k, 'Просмотры', NA, NA, NA, '', NOACC, views_na); return
        tv, tz = vsego_prosmotrov(old, p)
        v7, z7, b7 = okno_prosmotry(old, p, 7, now); v30, z30, b30 = okno_prosmotry(old, p, 30, now)
        if tv is None: R(k, 'Просмотры', ND, ND, ND, '', ist_views); return
        R(k, 'Просмотры', tv, part(v7, b7) if v7 is not None else ND, part(v30, b30) if v30 is not None else ND, tz, ist_views, 'всего — сумма по видимым постам; за период — прирост')
    def nz(k, req_prim='заявки по этому каналу не размечены', ord_prim='оплаты не привязаны к каналу'):
        R(k, 'Заявки', ND, ND, ND, '', NOACC, req_prim); R(k, 'Оплаченные заказы', ND, ND, ND, '', NOACC, ord_prim)

    soc('Telegram: Мастерская', 'gumanetriya_ai'); nz('Telegram: Мастерская')
    soc('Telegram: 3D', 'gumanetriya_3d'); nz('Telegram: 3D')
    soc('YouTube', 'youtube'); nz('YouTube')
    soc('RUTUBE', 'rutube'); nz('RUTUBE')
    vk_wall = vkinfo.get('wall', '')
    soc('ВКонтакте', 'vk', ist_people=CAB + ' (ключ сообщества)', views_na=None if vk_wall == 'есть' else f'стена не читается ключом сообщества ({vk_wall})')
    nz('ВКонтакте')
    soc('MAX: канал «Гуманет»', 'max'); nz('MAX: канал «Гуманет»')
    # Авито
    a = avito(D, now)
    if a.get('v30') is None:
        for p in ('Люди (подписчики)', 'Просмотры', 'Заявки', 'Оплаченные заказы'): R('Авито', p, ND, ND, ND, '', NOACC, a.get('err', ''))
    else:
        R('Авито', 'Люди (подписчики)', ND, ND, ND, a['srez'], CAB + ' (API Авито)', 'API не отдаёт подписчиков')
        R('Авито', 'Просмотры', f"объявлений {a['ads']}", a['v7'], a['v30'], a['srez'], CAB + ' (API Авито)', 'уникальные просмотры объявлений по дням')
        R('Авито', 'Заявки', '', a['c7'], a['c30'], a['srez'], CAB + ' (API Авито)', f"уникальные контакты; новых чатов: {a['ch7']} за 7 дн., {a['ch30']} за 30 дн.")
        R('Авито', 'Оплаченные заказы', ND, ND, ND, '', NOACC, 'оплата на Авито не проходит через нас')
    # кабинеты, снятые вручную (Comet), и площадки без доступа
    for k, how in (('Дзен', 'Студия Дзена → Статистика; открытая страница канала отдаёт заглушку'),
                   ('Kwork', 'кабинет Kwork → Мои кворки; открытый профиль даёт только отзывы'),
                   ('FL.ru', 'кабинет FL.ru → Продвижение → посещения профиля')):
        for p in ('Люди (подписчики)', 'Просмотры', 'Заявки', 'Оплаченные заказы'):
            R(k, p, NA, NA, NA, '', NOACC, how if p == 'Просмотры' else '')
    # Lava
    l = lava(now)
    R('Lava.top', 'Люди (подписчики)', NA, NA, NA, '', NOACC, 'API не отдаёт')
    R('Lava.top', 'Просмотры', NA, NA, NA, '', NOACC, 'API не отдаёт просмотры витрины')
    R('Lava.top', 'Заявки', NA, NA, NA, '', NOACC, '')
    if l.get('err'): R('Lava.top', 'Оплаченные заказы', ND, ND, ND, '', NOACC, l['err'])
    else: R('Lava.top', 'Оплаченные заказы', l['total'], l['p7'], l['p30'], l['srez'], CAB + ' (API Lava)', 'продажи по ключу API')
    # сайт
    s = sait(now); o = n8n(now); oc = orders_calc(o, now)
    if s:
        pp = (lambda v: f"{v} (с {dm(s['first'])})" if s['first'] > (now - datetime.timedelta(days=29)).strftime('%Y-%m-%d') else v)
        R('Сайт gumanetriya.ru', 'Люди (подписчики)', '', s['p7'], pp(s['p30']), s['srez'], OPEN + ' (журнал сервера)', 'люди = браузеры без роботов')
        R('Сайт gumanetriya.ru', 'Просмотры', '', s['h7'], pp(s['h30']), s['srez'], OPEN + ' (журнал сервера)', 'открытые страницы')
    else:
        for p in ('Люди (подписчики)', 'Просмотры'): R('Сайт gumanetriya.ru', p, ND, ND, ND, '', NOACC, 'журнал не прочитан')
    if oc:
        Z = 'Заказы — итог по n8n'; zs = CAB + ' (n8n)'
        zrows = [
            {'k': Z, 'p': 'Оплачено клиентами', 'vs': '', 'd7': f"{oc[7]['paid']} ({oc[7]['paid_sum']:.0f} ₽)", 'd30': f"{oc[30]['paid']} ({oc[30]['paid_sum']:.0f} ₽)", 'srez': oc['srez'], 'ist': zs, 'prim': 'сайт и бот, оплата прошла и не отменена; пробы Капитана не входят'},
            {'k': Z, 'p': 'Заявки с сайта: создано заказов', 'vs': '', 'd7': f"{oc[7]['site']} (отменено {oc[7]['site_cancel']})", 'd30': f"{oc[30]['site']} (отменено {oc[30]['site_cancel']})", 'srez': oc['srez'], 'ist': zs, 'prim': 'человек дошёл до оплаты на сайте'},
            {'k': Z, 'p': 'Заявки с сайта: диалоги в чате', 'vs': '', 'd7': oc[7]['dialogs'], 'd30': f"{oc[30]['dialogs']} (с {dm(oc.get('chat_from'))})", 'srez': oc['srez'], 'ist': zs, 'prim': 'разные собеседники в чате сайта, без тестов'},
            {'k': Z, 'p': 'Пробы Капитана', 'vs': '', 'd7': f"{oc[7]['kap']} (оплачено {oc[7]['kap_paid']})", 'd30': f"{oc[30]['kap']} (оплачено {oc[30]['kap_paid']})", 'srez': oc['srez'], 'ist': zs, 'prim': 'для честности: это не продажи'},
        ]
        rows[0:0] = zrows
        cf = oc.get('chat_from')
        R('Сайт gumanetriya.ru', 'Заявки', '', f"{oc[7]['dialogs']} диал. / {oc[7]['site']} заказ.", f"{oc[30]['dialogs']} диал. (с {dm(cf)}) / {oc[30]['site']} заказ.", oc['srez'], CAB + ' (n8n)',
          f"диалоги в чате сайта без тестов; созданные заказы, из них отменено: {oc[30]['site_cancel']}")
        R('Сайт gumanetriya.ru', 'Оплаченные заказы', '', oc[7]['site_paid'], oc[30]['site_paid'], oc['srez'], CAB + ' (n8n)', 'оплата прошла и не отменена')
    else:
        for p in ('Заявки', 'Оплаченные заказы'): R('Сайт gumanetriya.ru', p, ND, ND, ND, '', NOACC, o.get('err', ''))
    # ручной срез кабинетов (Comet): заменяет «нет данных» или добавляет строку к своему каналу
    for k, m in ruchnoy(D).items():
        if k.startswith('_') or not isinstance(m, dict): continue
        for p, x in m.items():
            new = {'k': k, 'p': p, 'vs': x.get('vs', ''), 'd7': x.get('d7', ND), 'd30': x.get('d30', ND), 'srez': x.get('srez', ''), 'ist': CAB + ' (снято через Comet)', 'prim': x.get('prim', '')}
            same = [i for i, r in enumerate(rows) if r['k'] == k and r['p'] == p]
            if same: rows[same[0]] = new; continue
            last = max([i for i, r in enumerate(rows) if r['k'] == k], default=len(rows) - 1)
            rows.insert(last + 1, new)
    return rows, a, l, s, oc


def zaklyuchenie(rows, a, l, s, oc):
    """Пять строк: что работает, что нет, что делать завтра. Каждая с пометкой и с числами из таблицы."""
    def g(k, p, f='d7'):
        for r in rows:
            if r['k'] == k and r['p'] == p: return r[f]
    def n(v):
        m = re.match(r'[+-]?\d+', str(v)) if v is not None else None
        return int(m.group(0)) if m else None
    lines = []
    if oc:
        paid = oc[30]['paid']; kp = oc[30]['kap_paid']
        lines.append(('факт', f"Оплаченных заказов от клиентов за 30 дней: {paid} на {oc[30]['paid_sum']:.0f} ₽. Пробы Капитана не считаем (оплачено проб: {kp}). Заказов с сайта создано {oc[30]['site']}, отменено {oc[30]['site_cancel']}."))
    views = []
    for k in ('Telegram: Мастерская', 'Telegram: 3D', 'YouTube', 'RUTUBE', 'ВКонтакте', 'MAX: канал «Гуманет»', 'Авито', 'Сайт gumanetriya.ru'):
        v = n(g(k, 'Просмотры: кабинет', 'd7'))
        if v is None: v = n(g(k, 'Просмотры', 'd7'))
        if v is not None: views.append((v, k))
    views.sort(reverse=True)
    if views:
        lines.append(('факт', 'Просмотры за 7 дней (кабинет, где он снят, иначе открытые данные): ' + ', '.join(f'{k} — {v}' for v, k in views[:4]) + (f'; меньше всех: {views[-1][1]} — {views[-1][0]}.' if len(views) > 4 else '.')))
    subs = [(n(g(k, 'Люди (подписчики)', 'vs')), k) for k in ('Telegram: Мастерская', 'Telegram: 3D', 'YouTube', 'RUTUBE', 'ВКонтакте', 'MAX: канал «Гуманет»')]
    subs = [(v, k) for v, k in subs if v is not None]
    if subs:
        lines.append(('факт', 'Подписчиков всего: ' + ', '.join(f'{k} {v}' for v, k in sorted(subs, reverse=True)) + f' — вместе {sum(v for v, _ in subs)}.'))
    if s and oc:
        lines.append(('гипотеза', f"Не работает переход из просмотра в заказ: на сайте {s['p7']} чел. за 7 дней, диалогов в чате {oc[7]['dialogs']}, оплат 0"
                      + (f"; на Авито за 30 дней просмотров {a['v30']}, контактов {a['c30']}" if a.get('v30') is not None else '') + '. Аудитория маленькая, а в постах и объявлениях нет понятного шага «написать или заказать».'))
    soc = [k for v, k in views if k not in ('Сайт gumanetriya.ru', 'Авито')]
    best = soc[0] if soc else 'Telegram'
    lines.append(('гипотеза', f"Что сделать завтра: в канале «{best}» (больше всех просмотров среди соцсетей) и в объявлениях Авито поставить ссылку на сайт с меткой канала (?from=…), тогда заявки начнут считаться по каналам; снять кабинеты, где сейчас «нет доступа»."))
    return lines[:5]


def kak_podklyuchit(rows):
    need = collections.OrderedDict()
    for r in rows:
        if r['ist'] == NOACC: need.setdefault(r['k'], []).append(r['p'])
    HOW = {
        'Telegram: Мастерская': 'заявки и оплаты: ссылка на бота с меткой t.me/…?start=tg_ai',
        'Telegram: 3D': 'заявки и оплаты: ссылка на бота с меткой ?start=tg_3d',
        'YouTube': 'заявки: ссылка в описании с меткой ?from=yt; просмотры Studio — кабинет YouTube через Comet (вход есть)',
        'RUTUBE': 'заявки: ссылка с меткой ?from=rt; закрытая статистика — Студия RUTUBE через Comet',
        'ВКонтакте': 'просмотры: ключ доступа приложения ВК (сервисный ключ, бесплатно) — скрипт vk-stat-key.py; заявки: метка ?from=vk',
        'MAX: канал «Гуманет»': 'заявки: ссылка на бота с ?start=max_kanal; просмотры постов страница не отдаёт',
        'Авито': 'оплаты идут вне Авито — считать по метке ?from=avito в ссылке на сайт',
        'Дзен': 'Студия Дзена через Comet (вход Яндекс ID у Капитана), срез раз в неделю вручную',
        'Kwork': 'кабинет Kwork через Comet: Статистика кворков (показы, заказы)',
        'FL.ru': 'кабинет FL.ru через Comet: статистика профиля',
        'Lava.top': 'просмотры витрины API не отдаёт; оплаты уже идут из API',
        'Сайт gumanetriya.ru': 'журнал или n8n не прочитаны — повторить сбор',
    }
    return [(k, ', '.join(v).lower(), HOW.get(k, '')) for k, v in need.items()]


def itogo(rows):
    """Короткая сводка: одна строка на канал."""
    def g(k, ps, f):
        for p in ps:
            for r in rows:
                if r['k'] == k and r['p'] == p and r[f] not in (None, '', ND, NA): return r[f]
        return None
    ks = []
    for r in rows:
        if r['k'] not in ks and not r['k'].startswith('Заказы'): ks.append(r['k'])
    out = []
    for k in ks:
        src = sorted({r['ist'].split(' (')[0] for r in rows if r['k'] == k and r['ist'] != NOACC}) or [NOACC]
        vr = next((r for p in ('Просмотры: кабинет', 'Просмотры') for r in rows if r['k'] == k and r['p'] == p and r['d7'] not in (None, '', ND, NA)), None)
        v30 = vr['d30'] if vr and vr['d30'] not in (None, '', ND, NA) else (None if vr else g(k, ('Просмотры: кабинет', 'Просмотры'), 'd30'))
        out.append({'k': k, 'lyudi': g(k, ('Люди (подписчики)', 'Люди: кабинет'), 'vs'), 'v7': vr['d7'] if vr else None,
                    'v30': v30, 'z30': g(k, ('Заявки',), 'd30'),
                    'o30': g(k, ('Оплаченные заказы',), 'd30') or g(k, ('Оплаченные заказы',), 'vs'), 'src': ', '.join(src)})
    return out


def num_of(v):
    m = re.match(r'[+-]?\d[\d ]*', str(v)) if v is not None else None
    return int(m.group(0).replace(' ', '')) if m else None


def render_itogo(rows):
    it = itogo(rows)
    def c(v): return '<span class=nd>нет</span>' if v is None else f'<span class=num>{html.escape(str(v))}</span>'
    tr = ''
    for x in it:
        u = URL.get(x['k'])
        name = f'<a href="{u}" target="_blank" rel="noopener noreferrer">{html.escape(x["k"])}</a>' if u else html.escape(x['k'])
        tr += (f"<tr><td class=pk>{name}<small>{html.escape(x['src'])}</small></td><td data-l='люди'>{c(x['lyudi'])}</td>"
               f"<td data-l='просм. 7 дн.'>{c(x['v7'])}</td><td data-l='просм. 30 дн.'>{c(x['v30'])}</td><td data-l='заявки 30 дн.'>{c(x['z30'])}</td><td data-l='оплаты 30 дн.'>{c(x['o30'])}</td></tr>")
    sl = sum(num_of(x['lyudi']) or 0 for x in it); sv = sum(num_of(x['v7']) or 0 for x in it)
    zr = next((r for r in rows if r['p'] == 'Оплачено клиентами'), None)
    tr += (f"<tr class=it><td class=pk>Итого<small>сумма там, где есть число</small></td><td data-l='люди'><span class=num>{sl}</span></td>"
           f"<td data-l='просм. 7 дн.'><span class=num>{sv}</span></td><td data-l='просм. 30 дн.'>—</td><td data-l='заявки 30 дн.'>—</td>"
           f"<td data-l='оплаты 30 дн.'><span class=num>{html.escape(str(zr['d30'])) if zr else 'нет'}</span></td></tr>")
    return ('<table class="kt kti"><thead><tr><th>Канал<th>Люди<th>Просмотры 7 дн.<th>Просмотры 30 дн.<th>Заявки 30 дн.<th>Оплаты 30 дн.</tr></thead><tbody>' + tr + '</tbody></table>'
            '<p class=m>«нет» — числа нет (нет данных или нет доступа), это не ноль. Название канала открывает сам канал. Даты и источники каждого числа — в разделе «Все цифры» ниже.</p>')


def csv_text(rows, zak):
    def c(x): x = '' if x is None else str(x); return '"' + x.replace('"', '""') + '"' if any(ch in x for ch in ';"\n') else x
    out = ['Канал;Показатель;Всего сейчас;За 7 дней;За 30 дней;Дата среза;Источник;Примечание']
    for r in rows: out.append(';'.join(c(r[f]) for f in ('k', 'p', 'vs', 'd7', 'd30')) + ';' + c(dm(r['srez']) + '.' + r['srez'][:4] if r['srez'] else '') + ';' + c(r['ist']) + ';' + c(r['prim']))
    out.append(''); out += ['Вывод;' + c(f'{t}: {s}') for t, s in zak]
    return '\ufeff' + '\r\n'.join(out) + '\r\n'


def tsv_text(rows):
    out = ['Канал\tПоказатель\tВсего сейчас\tЗа 7 дней\tЗа 30 дней\tДата среза\tИсточник\tПримечание']
    for r in rows: out.append('\t'.join(str(r[f] if r[f] is not None else '') for f in ('k', 'p', 'vs', 'd7', 'd30')) + '\t' + (dm(r['srez']) + '.' + r['srez'][:4] if r['srez'] else '') + '\t' + r['ist'] + '\t' + r['prim'])
    return '\n'.join(out)


CSS = '''.kt{width:100%;border-collapse:collapse;font-size:15px;background:var(--cream);border-radius:18px;overflow:hidden}
.kt th{background:var(--mist);color:var(--moss);font-weight:700;padding:8px 6px;text-align:left}
.kt td{padding:7px 6px;border-bottom:1px solid rgba(26,34,22,.12);vertical-align:top}
.kt tr.kh td{background:var(--moss);color:var(--cream);font:700 17px Literata,serif;padding:9px 10px}
.kt .num{font-weight:700;color:var(--clay);white-space:nowrap}.kt .nd{color:var(--muted);font-weight:500}
.kt small{color:var(--muted);display:block;font-size:12px}
.src{display:inline-block;border-radius:99px;padding:1px 8px;font-size:12px;font-weight:600;white-space:nowrap}
.src.o{background:#dfeccd;color:#31442a}.src.c{background:#ffe3c2;color:#7a3f1d}.src.n{background:#ece7d6;color:#5d6652}
.btns{display:flex;gap:10px;flex-wrap:wrap;margin:10px 0}.btns button,.btns a{font:600 15px Onest,sans-serif;padding:10px 16px;border-radius:99px;border:0;background:var(--moss);color:var(--cream);text-decoration:none;cursor:pointer}
.btns a{background:var(--apricot);color:var(--ink)}
.zak{background:var(--cream);border-radius:18px;padding:12px 16px;border:1px solid rgba(26,34,22,.12)}.zak p{margin:6px 0}.zak b.f{color:var(--moss)}.zak b.h{color:var(--clay)}
.kp td{font-size:14px}
.kti tr.it td{background:var(--mist);font-weight:700}.kti a{color:inherit;text-decoration:underline;text-underline-offset:3px}.kt tr.kh a{color:var(--cream);text-decoration:underline}a.src{text-decoration:none}h3{font-family:Literata,serif;color:var(--moss)}
@media(max-width:640px){.kt thead{display:none}.kt,.kt tbody,.kt tr,.kt td{display:block;width:100%}.kt tr{border-bottom:1px solid rgba(26,34,22,.15);padding:6px 4px}.kt td{border:0;padding:2px 6px}
.kt td[data-l]{display:inline-block;width:auto;margin-right:12px}.kt td[data-l]::before{content:attr(data-l) ": ";color:var(--muted);font-size:13px}.kt td.pk{font-weight:700;color:var(--moss)}.kp tr:first-child{display:none}.kp tr,.kp td{display:block;width:100%}.kp tr{border-bottom:1px solid rgba(26,34,22,.15);padding:6px 0}.kp td{border:0;padding:2px 4px}.kp td:first-child{font-weight:700;color:var(--moss)}.w{padding-left:10px;padding-right:10px}}
'''


def cell(v):
    if v is None or v == '': return '<span class=nd>—</span>'
    if v in (ND, NA): return f'<span class=nd>{v}</span>'
    return f'<span class=num>{html.escape(str(v))}</span>'


def render(rows, zak, now, csv_name):
    body = ''; cur = None
    for r in rows:
        if r['k'] != cur:
            cur = r['k']; u = URL.get(cur); body += '<tr class=kh><td colspan=6>' + (f'<a href="{u}" target="_blank" rel="noopener noreferrer">{html.escape(cur)}</a>' if u else html.escape(cur)) + '</td></tr>'
        kind = 'o' if r['ist'].startswith(OPEN) else ('c' if r['ist'].startswith(CAB) else 'n')
        srez = dm(r['srez']) + '.' + r['srez'][:4] if r['srez'] else '—'
        prim = f"<small>{html.escape(r['prim'])}</small>" if r['prim'] else ''
        body += (f"<tr><td class=pk>{html.escape(r['p'])}{prim}</td>"
                 f"<td data-l='всего'>{cell(r['vs'])}</td><td data-l='за 7 дней'>{cell(r['d7'])}</td><td data-l='за 30 дней'>{cell(r['d30'])}</td>"
                 f"<td data-l='срез'>{srez}</td><td data-l='источник'><a class='src {kind}' href='#istochniki'>{html.escape(r['ist'])}</a></td></tr>")
    tsv = tsv_text(rows)
    pk = kak_podklyuchit(rows)
    podkl = ('<h3>Где нет данных и как подключить</h3><div class=box><table class=kp><tr><th>Канал<th>Чего нет<th>Как подключить</tr>' + ''.join(f'<tr><td>{html.escape(k)}<td>{html.escape(w)}<td>{html.escape(h)}</tr>' for k, w, h in pk) + '</table></div>') if pk else ''
    zh = ''.join(f"<p><b class={'f' if t == 'факт' else 'h'}>{t.capitalize()}.</b> {html.escape(s)}</p>" for t, s in zak)
    legend = ('<div class=say id=istochniki><b>Откуда числа.</b> Открытые данные — то, что видно любому без входа (страница канала, журнал нашего сервера). '
              'Кабинет — числа из личного кабинета площадки: по ключу API (Авито, Lava, n8n, ключ сообщества ВК) или снятые вручную через браузер Comet (дата среза в строке). '
              'Нет доступа — площадка не даёт число без входа или ключа; как подключить — в таблице ниже.</div>')
    script = ("<script>document.getElementById('kcopy').onclick=async()=>{const t=document.getElementById('ktsv').value,ok=document.getElementById('kok');try{await navigator.clipboard.writeText(t);ok.textContent='Таблица скопирована, вставь в Excel или письмо.'}catch(e){const a=document.createElement('textarea');a.value=t;document.body.appendChild(a);a.select();let r=false;try{r=document.execCommand('copy')}catch(_){}a.remove();ok.textContent=r?'Таблица скопирована.':'Браузер не дал скопировать. Нажми «Скачать CSV».'}};"
              "document.querySelectorAll('a[href=\"#istochniki\"]').forEach(a=>a.addEventListener('click',()=>{const d=document.getElementById('vse');if(d)d.open=true}));</script>")
    vse = ('<div class=say>За 7 и 30 дней. У каждого числа дата среза и источник. «нет данных» и «нет доступа» — не ноль. Ноль — только там, где кабинет сам его подтвердил.</div>'
           f'<table class=kt id=ktab><thead><tr><th>Показатель<th>Всего<th>За 7 дней<th>За 30 дней<th>Срез<th>Источник</tr></thead><tbody>{body}</tbody></table>{legend}{podkl}')
    return (f'<h2>Вывод</h2><div class=zak>{zh}</div>'
            f'<h2>Итого по каналам</h2><div class=btns><button type=button id=kcopy>Копировать таблицу</button><a href="{csv_name}" download="nashi-kanaly-{now.strftime("%Y-%m-%d")}.csv">Скачать CSV для Excel</a><span id=kok class=m></span></div>'
            + render_itogo(rows)
            + f'<details class=sv id=vse><summary><h2>Все цифры: дата и источник у каждого числа</h2><small>{len(rows)} строк: по 4 на канал и заказы. Нажми, чтобы открыть.</small></summary>{vse}</details>'
            + f'<textarea id=ktsv hidden>{html.escape(tsv)}</textarea>' + script)

