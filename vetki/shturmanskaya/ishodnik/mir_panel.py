#!/usr/bin/env python3
# 23.11.2026 «Что в мире»: открытые данные без входа и обхода защиты — спрос на биржах (Kwork, FL.ru, Freelance.kz, Free.UZ), что ищут люди (Google Trends RU), что в моде у разработчиков (GitHub trending).
# Копит историю по дням. Страница: https://gumanetriya.ru/v/<секрет>/mir.html . Ничего никуда не шлёт.
import sys, os, re, json, html, time, datetime, urllib.request, collections, statistics
import xml.etree.ElementTree as ET
sys.path.insert(0, '/opt/razvedka'); sys.path.insert(0, '/opt/klon')
import panel_stil as S
D = '/var/lib/gonets/stat'; os.makedirs(D, exist_ok=True); HIST = D + '/mir.jsonl'
EKB = datetime.timezone(datetime.timedelta(hours=5)); NOW = datetime.datetime.now(EKB); TODAY = NOW.strftime('%Y-%m-%d')
H = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) Chrome/124", "Accept-Language": "ru"}
def get(u): return urllib.request.urlopen(urllib.request.Request(u, headers=H), timeout=30).read().decode('utf-8', 'ignore')
def clean(s): return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', s))).strip()
CATS = [('3D, чертежи и архитектура', r'\b3[- ]?[dд]\b|черт[её]ж|autocad|архитектур|планировк|интерьер|проектировани|рендер|blender|bim\b|моделировани'),
        ('Бухгалтерия и право', r'бухгалтер|налог|отч[её]тн|юрист|договор|иск\b|\b1[сc]\b|ндс|усн|декларац|регистрац.*ооо|\bип\b'),
        ('Боты и автоматизация', r'\bбот\b|\bботы\b|чат-бот|автоматиз|n8n|парсер|парсинг|интеграци|crm|api\b|скрипт'),
        ('Нейросети и ИИ', r'нейросет|\bии\b|\bai\b|gpt|midjourney|chatgpt|промпт|генерац'),
        ('Сайты и программы', r'сайт|лендинг|landing|вёрстк|верстк|wordpress|тильд|tilda|битрикс|приложени|разработ|программист|python|1с\b|1c\b|backend|frontend|php|интернет-магазин'),
        ('Дизайн и графика', r'дизайн|логотип|баннер|инфографик|презентац|фотошоп|иллюстрац|макет|упаковк|брендбук'),
        ('Видео и аудио', r'видео|монтаж|ролик|reels|shorts|озвучк|аудио|анимац|подкаст|музык|клип|capcut'),
        ('Тексты и переводы', r'текст|статья|статей|копирайт|рерайт|перевод|контент|описани|сценари|редактур|корректур'),
        ('Маркетплейсы и каталоги', r'товарн\w* карт|карточ\w* товар|заполнени\w* каталог|маркетплейс|\bwb\b|ozon|озон|wildberries|вайлдберриз|яндекс маркет'),
        ('Реклама и продвижение', r'реклам|таргет|seo|smm|продвижен|директ|авито|соцсет|трафик|маркетолог'),
        ('Учёба и студентам', r'курсов|диплом|реферат|контрольн|репетитор|курсовая|студен|эссе|лабораторн|задач[иа] по'),
        ('Данные и документы', r'расшифровк|транскрибац|оцифровк|распознавани|сканировани|excel|гугл таблиц|google sheets|обработк\w* данн|набор текст|ввод данн'),
        ('Тестирование и техподдержка', r'тестировани|ручной тест|техподдерж|техническ\w* поддерж|провер\w* работоспособност|настро\w* сервер'),
        ('Продажи и поддержка клиентов', r'продаж|колл-центр|обзвон|оператор чата|поддержк\w* клиент|обработ\w* заявок'),
        ('Работа в штат и удалёнка', r'менеджер|администратор|оператор|ассистент|сотрудник|специалист|вакан|стример|креатор|ugc|курьер|продавец|в штат|помощник|модератор|менеджер по'),
        ('Консультации и обучение', r'консульт|обучен|наставник|коуч|эксперт|урок|тренер'),
        ('Исследования и аналитика', r'исследован|аналити|опрос|поиск информац|сбор информац|аудит|анализ'),
        ('Игры и игровые проекты', r'разработ\w* игр|игров\w*|unity|unreal|roblox|minecraft'),
        ('Ремонт и услуги на месте', r'ремонт|установ\w* на мест|сантехн|электрик|уборк|перевоз|фотосъ[её]мк')]
def cat(t):
    t = (t or '').lower()
    for n, rx in CATS:
        if re.search(rx, t): return n
    return 'Другое'

def order_category(order):
    primary = cat(order['title'])
    return primary if primary != 'Другое' else cat(order['text'])

def freelance_ru(page):
    for block in re.findall(r'<article class="task-card"[^>]*>(.*?)</article>', page, re.S):
        title = re.search(r'<a\b[^>]*href="(/task/view/\d+)"[^>]*>(.*?)</a>', block, re.S)
        if not title or not clean(title.group(2)):
            continue
        budget = re.search(r'<span class="bold">\s*([\d\s\u00a0]+)\s*₽\s*</span>\s*<span class="cost-unit">\s*/\s*заказ\s*</span>', html.unescape(block))
        yield dict(src='Freelance.ru', title=clean(title.group(2)), price=money(budget.group(1)) if budget else 0, text='', id=title.group(1))

def weblancer(page):
    for block in page.split('<h2 class="text-xl')[1:]:
        title = re.search(r'href="(/freelance/jobs/[^"]+)"[^>]*>(.*?)</a>', block, re.S)
        if not title or not clean(title.group(2)):
            continue
        desc = re.search(r'<p class="text-gray-600[^>]*>(.*?)</p>', block, re.S)
        # Mixed currencies on Weblancer: do not put these into the ruble comparison.
        yield dict(src='Weblancer', title=clean(title.group(2)), price=0, text=clean(desc.group(1))[:150] if desc else '', id=title.group(1))
orders = []   # src,title,price
def money(s):
    nums = [int(re.sub(r'\D', '', x)) for x in re.findall(r'\d[\d\s\u00a0&nbsp;]*\d|\d', s.replace('&nbsp;', ' ')) if re.sub(r'\D', '', x)]
    nums = [n for n in nums if n >= 100]; return sum(nums) / len(nums) if nums else 0
# --- Kwork: биржевые запросы заказчиков (JSON внутри страницы)
for pg in range(1, 9):
    try:
        t = get(f'https://kwork.ru/projects?page={pg}'); i = t.find('"wants":[')
        if i < 0: break
        arr, _ = json.JSONDecoder().raw_decode(t[i + 8:])
        for w in arr: orders.append({"src": "Kwork", "title": w.get('name', ''), "price": float(w.get('priceLimit') or 0), "text": (w.get('description') or '')[:150], "date": (w.get('date_create') or '')[:10]})
    except Exception as e: print('kwork', pg, type(e).__name__); break
# --- FL.ru
for pg in range(1, 7):
    try:
        t = get(f'https://www.fl.ru/projects/?page={pg}')
        for b in t.split('id="project-item')[1:]:
            m = re.search(r'id="prj_name_\d+"[^>]*>([^<]+)</a>', b); p = re.search(r'b-post__price[^>]*>(.*?)</div>', b, re.S)
            if m: orders.append({"src": "FL.ru", "title": clean(m.group(1)), "price": money(clean(p.group(1))) if p else 0, "text": ''})
    except Exception as e: print('fl', pg, type(e).__name__); break
# --- Freelance.kz / Free.UZ (без цены в списке)
for host, src in (('freelance.kz', 'Freelance.kz'), ('free.uz', 'Free.UZ')):
    for pg in (1, 2, 3):
        try:
            for m in re.finditer(r'href="/ru/jobs/project/([^"/]+)/[^"/]+"', get(f'https://{host}/ru/jobs/all?page={pg}&size=10')): orders.append({"src": src, "title": m.group(1).replace('-', ' '), "price": 0, "text": ''})
        except Exception as e: print(src, type(e).__name__); break
# --- additional public order listings
listings = (
    ('Freelance.ru', 'https://freelance.ru/project/search', freelance_ru),
    ('Weblancer', 'https://www.weblancer.net/jobs/', weblancer),
)
listing_status = {}
for src, url, parser in listings:
    try:
        found = list(parser(get(url)))
        orders.extend(found)
        if not found:
            listing_status[src] = 'В открытом списке не распознаны объявления'
    except Exception as e:
        listing_status[src] = f'Список недоступен (HTTP {e.code})' if getattr(e, 'code', None) else 'Список временно недоступен'
        print(src, type(e).__name__, getattr(e, 'code', ''))
seen = set(); uo = []
for o in orders:
    if not o['title'].strip(): continue
    k = (o['src'], o.get('id', o['title']))
    if k in seen: continue
    seen.add(k); o['cat'] = order_category(o); uo.append(o)
orders = uo
bycat = collections.defaultdict(list)
for o in orders: bycat[o['cat']].append(o)
rows = []
for c, l in bycat.items():
    pr = [o['price'] for o in l if o['price'] >= 300]
    rows.append({"c": c, "n": len(l), "priced": len(pr), "med": statistics.median(pr) if pr else 0, "sum": sum(pr)})
bysrc = collections.Counter(o['src'] for o in orders)
# --- public RUTUBE recommendations, never part of the order sample
rt = []
try:
    rt = S.rutube_cards(get(S.RUTUBE_TOP))[:10]
except Exception as e: print('rutube', type(e).__name__)
# --- separate signals: job board includes vacancies; articles are not orders
KADROF = 'https://www.kadrof.ru/work'
HABR_RSS = 'https://habr.com/ru/rss/articles/?fl=ru'
kadrof, habr = [], []
try:
    candidates = re.findall(r'<h6\b[^>]*>\s*<a\b[^>]*href="(/work/\d+)"[^>]*>(.*?)</a>', get(KADROF), re.S)
    kadrof = list(dict((url, clean(title)) for url, title in candidates if clean(title)).items())[:10]
except Exception as e: print('kadrof', type(e).__name__)
try:
    for item in ET.fromstring(get(HABR_RSS)).findall('./channel/item')[:25]:
        title = (item.findtext('title') or '').strip()
        url = item.findtext('guid') or item.findtext('link') or ''
        if title and re.fullmatch(r'https://habr\.com/ru/(?:articles/\d+|companies/[a-zA-Z0-9_.-]+/articles/\d+)/?', url.split('?')[0]):
            habr.append((url.split('?')[0], title))
except Exception as e: print('habr rss', type(e).__name__)
# --- Google Trends RU
trends = []
try:
    for it in re.findall(r'<item>(.*?)</item>', get('https://trends.google.com/trending/rss?geo=RU'), re.S):
        t = re.search(r'<title>(.*?)</title>', it); tr = re.search(r'approx_traffic>(.*?)<', it)
        if t: trends.append((html.unescape(t.group(1)), tr.group(1) if tr else ''))
except Exception as e: print('trends', type(e).__name__)
# --- GitHub trending (неделя)
gh = []
try:
    for b in get('https://github.com/trending?since=weekly').split('<article')[1:16]:
        n = re.search(r'href="/([^"/]+/[^"/]+)"', b); d = re.search(r'<p class="[^"]*col-9[^"]*">(.*?)</p>', b, re.S); st = re.search(r'([\d,]+)\s+stars this week', b)
        if n: gh.append((n.group(1), clean(d.group(1))[:110] if d else '', st.group(1) if st else ''))
except Exception as e: print('github', type(e).__name__)
# --- история
if orders:
    with open(HIST, 'a') as f: f.write(json.dumps({"d": TODAY, "v": 2, "cats": {r['c']: r['n'] for r in rows}, "med": {r['c']: r['med'] for r in rows}, "n": len(orders)}, ensure_ascii=False) + '\n')
hist = {}
if os.path.exists(HIST):
    with open(HIST) as history:
        for l in history:
            try: o = json.loads(l); hist[o['d']] = o
            except ValueError: pass
# --- пояснение простыми словами
advice = ''
try:
    import lib
    top = sorted(rows, key=lambda r: -r['n'])
    PR = ("Ты объясняешь владельцу маленькой студии «Гуманетрия» (Telegram- и MAX-боты, автоматизация n8n, ИИ-помощники, бухгалтерия через ИИ, сайты, ИИ-видео) данные с бирж фриланса и трендов. "
          "Пиши по-русски просто, короткими фразами. Бюджеты указаны в объявлениях, это не выплаты. Формат: 1) «Что заказывают чаще всего» одна фраза; 2) «Где заявлен выше бюджет» одна фраза по категориям с тремя или более указанными ценами; 3) «Что в моде у людей сегодня» одна фраза из трендов; "
          "4) «Куда нам повернуться» три конкретных шага для нашей студии, с учётом что мы не берём заказы дешевле 2 000 рублей. Не выдумывай цифр, бери только из данных. До 900 знаков.\n\n")
    data = 'КАТЕГОРИИ(число заказов, медианный бюджет): ' + json.dumps(top, ensure_ascii=False) + '\nИСТОЧНИКИ: ' + json.dumps(bysrc, ensure_ascii=False) + '\nПОИСКИ СЕГОДНЯ: ' + json.dumps(trends[:10], ensure_ascii=False) + '\nGITHUB НЕДЕЛИ: ' + json.dumps([g[:2] for g in gh[:8]], ensure_ascii=False)
    out, mod = lib.chat('mir-panel', ['polza:deepseek/deepseek-v4-flash'], PR + data, 1000); advice = (out or '').strip()
except Exception as e: print('модель:', type(e).__name__)
if not advice: advice = 'Данные собраны, смотри графики ниже.'
# --- страница
rub = lambda v: f'{v:,.0f} ₽'.replace(',', ' ')
top = sorted(rows, key=lambda r: -r['n']); pay = sorted([r for r in rows if r['priced'] >= 3 and r['c'] != 'Другое'], key=lambda r: -r['med'])
cards = f"<div class=card><b>Объявлений в выборке</b><div class=n>{len(orders) if orders else 'нет данных'}</div><small>на {len(bysrc)} биржах сегодня</small></div>" + ''.join(f"<div class=card><b>{html.escape(s)}</b><div class=n>{n}</div><small>открытых объявлений</small></div>" for s, n in bysrc.most_common())
cards += ''.join(f"<div class=card><b>{html.escape(s)}</b><small>{html.escape(msg)}</small></div>" for s, msg in listing_status.items())
comparable = [(d, h) for d, h in sorted(hist.items()) if h.get('v') == 2]
trend_hist = {c: [(d, h['cats'].get(c, 0)) for d, h in comparable] for c in [r['c'] for r in top[:4]]} if len(comparable) > 1 else {}
best = [o for o in sorted(orders, key=lambda o: -o['price']) if o['price'] > 0][:10]
rt_table = ''.join(f'<tr><td><a href="{v["url"]}">{html.escape(v["title"])}</a></td><td>{html.escape(v["label"] or "нет данных")}</td></tr>' for v in rt)
def signal_list(pairs):
    if not pairs:
        return '<p class=m>Источник временно недоступен.</p>'
    return '<ul>' + ''.join(f'<li><a href="{html.escape(u, quote=True)}">{html.escape(t)}</a></li>' for u, t in pairs[:10]) + '</ul>'
advice_h = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', html.escape(advice)).replace('**', '')  # MIR_MD_V1
P = S.head('Что в мире — Гуманетрия', 'mir.html') + f'''<h1>Что происходит в мире</h1><p class=sub>Срез {NOW.strftime('%d.%m.%Y %H:%M')} по Екатеринбургу. Обновляется раз в сутки, около 8 утра. Выборка из открытых источников, не весь рынок. Обновляем раз в сутки.</p>
<h2>Простыми словами</h2><div class=ai>{advice_h}</div>
<h2>Где сколько заказов</h2><p class=sub>Сколько живых заказов мы нашли на биржах.</p><div class=cards>{cards}</div>
<h2>Что заказывают чаще всего</h2><div class=say>Чем длиннее полоска, тем больше людей ищут именно это. Число — сколько заказов сегодня.</div>{S.bars([(r['c'], r['n']) for r in top])}
<div class=say>Что внутри «Другого», примеры: {html.escape('; '.join(o['title'][:45] for o in bycat.get('Другое', [])[:8]))}</div>
<h2>Где заявлен выше бюджет</h2><div class=say>Медиана объявленных бюджетов в рублях, не оплаченные сделки. Показываем темы, где цену указали хотя бы в трёх объявлениях.</div>{S.bars([(r['c'], r['med']) for r in pay], rub)}
<h2>Как меняется спрос</h2><div class=say>Сравниваем срезы по обновлённым рубрикам. Число зависит от того, какие источники ответили.</div>{S.lines(trend_hist) if trend_hist else "<p class=m>Пока недостаточно сопоставимых срезов.</p>"}
<h2>Самые денежные заказы сейчас</h2><div class=box><table><tr><th>где<th>что нужно<th>бюджет</tr>{"".join(f"<tr><td>{o['src']}<td>{html.escape(o['title'][:90])}<td>{rub(o['price'])}</tr>" for o in best)}</table></div>
<h2>Что ищут люди в России сегодня</h2><div class=say>Самые частые запросы в Google за сутки. Помогают понять, о чём все говорят.</div><div class=box><table><tr><th>запрос<th>поисков</tr>{"".join(f"<tr><td>{html.escape(t)}<td>{html.escape(n)}</tr>" for t, n in trends[:12])}</table></div>
<h2>Что в моде у программистов</h2><div class=say>Самые растущие проекты недели на GitHub. Тут видно, какие инструменты скоро придут к клиентам.</div><div class=box><table><tr><th>проект<th>о чём<th>звёзд за неделю</tr>{"".join(f"<tr><td>{html.escape(a)}<td>{html.escape(b)}<td>{html.escape(c)}</tr>" for a, b, c in gh[:10])}</table></div>
<h2>Видео в топе RUTUBE</h2><p class=sub>Первые позиции <a href="{S.RUTUBE_TOP}">подборки RUTUBE</a>. Это просмотры видео, не заказы и не данные нашего канала.</p>
{f'<div class=box><table><tr><th>видео</th><th>просмотры</th></tr>{rt_table}</table></div>' if rt_table else '<p class=m>Подборка временно недоступна.</p>'}
<h2>Удалённая работа и проекты на Kadrof</h2><p class=sub>Последние позиции <a href="{KADROF}">публичной ленты</a>. Вакансии и проекты не смешаны с общим счётчиком заказов.</p>{signal_list([('https://www.kadrof.ru' + u, t) for u, t in kadrof])}
<h2>Свежие статьи на Хабре</h2><p class=sub>Технологические темы из <a href="{html.escape(HABR_RSS)}">RSS Хабра</a>. Это публикации, не сделки и не рейтинг читаемости.</p>{signal_list(habr)}
<p class=m>Биржи: Kwork, FL.ru, Freelance.kz, Free.UZ, <a href="{listings[0][1]}">Freelance.ru</a>, <a href="{listings[1][1]}">Weblancer</a>. <a href="https://habr.com/ru/companies/habr/articles/886798/">Хабр Фриланс закрыт</a>; заказы оттуда не считаем.</p></div>'''
P = S.sverni_vse(P, ('Простыми словами', 'Где сколько заказов', 'Что заказывают чаще всего'), '<p class=m>Биржи:')
sec = open(D + '/sekret').read().strip(); os.makedirs(f'/opt/stack/vitrina/v/{sec}', exist_ok=True); open(f'/opt/stack/vitrina/v/{sec}/mir.html', 'w').write(P)
print('мир:', len(orders), dict(bysrc), '| другое', len(bycat.get('Другое', [])), '| RUTUBE', len(rt), '| тренды', len(trends), '| github', len(gh), '| Kadrof', len(kadrof), '| Хабр RSS', min(len(habr), 10), '| источники без данных:', listing_status)
