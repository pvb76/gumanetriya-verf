#!/usr/bin/env python3
# 23.11.2026 панель статистики Гуманетрии: свой «Metricool» на 0 ₽. Читает ТОЛЬКО свои каналы: ВК-сообщество (токен из сейфа), t.me/s/*, YouTube @gumanetriya.
# Копит историю, считает вовлечённость, группирует по темам, рисует графики (SVG, без внешних библиотек), даёт совет «что постить дальше» (модель).
# Ничего никуда не шлёт. Страница: https://gumanetriya.ru/v/<секретная папка>/stat.html
import sys, os, re, json, csv, time, html, datetime, urllib.request, urllib.parse, collections
sys.path.insert(0, '/opt/razvedka')
sys.path.insert(0, '/opt/klon')
import panel_stil as S
D = '/var/lib/gonets/stat'; os.makedirs(D, exist_ok=True)
EKB = datetime.timezone(datetime.timedelta(hours=5)); NOW = datetime.datetime.now(EKB); TODAY = NOW.strftime('%Y-%m-%d')
SNAP = D + '/snap.jsonl'; META = D + '/meta.json'
OUT = '/opt/stack/vitrina/v'
H = {"User-Agent": "Mozilla/5.0", "Accept-Language": "en"}
def get(u, data=None):
    return urllib.request.urlopen(urllib.request.Request(u, data=data, headers=H), timeout=30).read().decode('utf-8', 'ignore')
def num(v):
    v = str(v).strip().replace(',', '').replace(' views', '').replace(' view', ''); m = 1
    if v.endswith('K'): m, v = 1000, v[:-1]
    if v.endswith('M'): m, v = 1000000, v[:-1]
    try: return int(float(v) * m)
    except ValueError: return 0
try: meta = json.load(open(META))
except Exception: meta = {"first": {}, "text": {}, "date": {}, "seeded": False}
rows = []   # {p,id,views,likes,reposts,comments,saves,subs}
subs = {}
def add(p, i, views=0, likes=0, reposts=0, comments=0, text='', date=''):
    k = f'{p}|{i}'; rows.append({"p": p, "id": str(i), "views": views, "likes": likes, "reposts": reposts, "comments": comments})
    if text and k not in meta["text"]: meta["text"][k] = text[:200]
    if date: meta["date"][k] = date
    meta["first"].setdefault(k, TODAY)
# --- сид из репозитория (одноразово)
if not meta["seeded"] and os.path.exists('/tmp/stat_seed'):
    for f in ('tg.csv', 'yt.csv'):
        try:
            for r in csv.reader(open('/tmp/stat_seed/' + f, encoding='utf-8')):
                if len(r) < 4: continue
                d, p, i, v = r[0], r[1], r[2], r[3]; t = r[4] if len(r) > 4 else ''
                if i == 'subs': open(SNAP, 'a').write(json.dumps({"d": d, "p": p, "subs": num(v)}) + '\n'); continue
                open(SNAP, 'a').write(json.dumps({"d": d, "p": p, "id": i, "views": num(v), "likes": 0, "reposts": 0, "comments": 0}) + '\n')
                k = f'{p}|{i}'; meta["first"].setdefault(k, d)
                if t: meta["text"].setdefault(k, t)
        except Exception as e: print('сид', f, type(e).__name__)
    meta["seeded"] = True
# --- ВК
VKG = 242703612; vkinfo = {}; g = {}
def vk(m, token, **q):
    q.update({"access_token": token, "v": "5.199"})
    return json.loads(get('https://api.vk.com/method/' + m, urllib.parse.urlencode(q).encode()))

try:
    with open('/home/foma/seif/vk_stat_service_token') as secret:
        wall_token = secret.read().strip()
except OSError:
    wall_token = ''

try:
    with open('/home/foma/seif/vk_gumanetriya_token') as secret:
        tok = secret.read().strip().split()[-1]
    r = vk('groups.getById', tok, group_id=VKG, fields='members_count')
    groups = r.get('response') or []
    if isinstance(groups, dict): groups = groups.get('groups') or []
    g = groups[0] if groups else {}
    if isinstance(g.get('members_count'), int): subs['vk'] = g['members_count']
    vkinfo['group'] = {k: g.get(k) for k in ('name', 'members_count')}
except Exception as e:
    tok = ''
    vkinfo['group_err'] = type(e).__name__
try:
    public_wall_token = wall_token or (tok if g.get('is_closed') == 0 else '')
    w = vk('wall.get', public_wall_token, owner_id=-VKG, count=100, filter='owner') if public_wall_token else {}
    vkinfo['wall'] = 'есть' if 'response' in w else ('нет данных: код ' + str(w['error'].get('error_code')) if 'error' in w else 'нет ключа')
    for it in w.get('response', {}).get('items', []):
        if it.get('owner_id') != -VKG or it.get('is_friends_only') or it.get('donut', {}).get('is_donut'):
            continue
        add('vk', it['id'], it.get('views', {}).get('count', 0), it.get('likes', {}).get('count', 0), it.get('reposts', {}).get('count', 0), it.get('comments', {}).get('count', 0), re.sub(r'\s+', ' ', it.get('text', '')), datetime.datetime.fromtimestamp(it['date'], EKB).strftime('%Y-%m-%d'))
except Exception as e:
    vkinfo['wall'] = type(e).__name__
try:
    s = vk('stats.get', tok, group_id=VKG, date_from=(NOW - datetime.timedelta(days=30)).strftime('%Y-%m-%d'), date_to=TODAY) if tok else {}
    vkinfo['stats'] = 'есть' if 'response' in s else 'нет данных'
    if 'response' in s:
        for x in s['response']:
            meta.setdefault('vkday', {})[x.get('period_from') or str(x.get('day'))] = {"v": x.get('visitors', {}).get('visitors', 0), "views": x.get('visitors', {}).get('views', 0), "reach": x.get('reach', {}).get('reach', 0)}
except Exception as e: vkinfo['stats'] = type(e).__name__
print('ВК:', vkinfo, 'постов', sum(1 for r in rows if r['p'] == 'vk'))
# --- Telegram
for ch in ('gumanetriya_ai', 'gumanetriya_roboty', 'gumanetriya_3d'):
    try:
        t = get(f'https://t.me/s/{ch}')
        m = re.search(r'counter_value">([^<]+)</span>\s*<span class="counter_type">subscribers', t)
        if m: subs[ch] = num(m.group(1))
        for b in t.split('tgme_widget_message_wrap')[1:]:
            pid = re.search(r'data-post="[^"/]+/(\d+)"', b); vw = re.search(r'tgme_widget_message_views">([^<]+)<', b)
            if not (pid and vw): continue
            tx = re.search(r'tgme_widget_message_text[^>]*>(.*?)</div>', b, re.S); dt = re.search(r'<time[^>]+datetime="([^"]+)"', b)
            rx = sum(num(x) for x in re.findall(r'tgme_reaction[^>]*>.*?<i class="emoji">.*?</i>(\d+)', b, re.S))
            add(ch, pid.group(1), num(vw.group(1)), rx, 0, 0, ' '.join(html.unescape(re.sub(r'<[^>]+>', ' ', tx.group(1) if tx else '')).split()), dt.group(1)[:10] if dt else '')
    except Exception as e: print('tg', ch, type(e).__name__)
# --- YouTube
try:
    for tab in ('shorts', 'videos'):
        t = get(f'https://www.youtube.com/@gumanetriya/{tab}'); s = re.search(r'"(\d[\d,.KM]*) subscribers?"', t)
        if s: subs['youtube'] = num(s.group(1))
        seen = set()
        for vid, ch in re.findall(r'"videoId":"([\w-]{11})"(.{0,2500})', t, re.S):
            if vid in seen: continue
            v = re.search(r'"(\d[\d,.KM]* views?)"', ch)
            if not v: continue
            seen.add(vid); k = f'youtube|{tab}:{vid}'
            if k not in meta["text"]:
                try: meta["text"][k] = json.loads(get(f'https://www.youtube.com/oembed?url=https://www.youtube.com/watch?v={vid}&format=json')).get('title', '')[:200]
                except Exception: pass
            add('youtube', f'{tab}:{vid}', num(v.group(1)))
except Exception as e: print('yt', type(e).__name__)
# --- RUTUBE: public channel, no Studio account metrics
rt_note = 'Нет свежего среза открытого канала.'
try:
    public = get(S.RUTUBE_OWN)
    source_subs = re.search(r'"subscribers_count":\s*(\d+)', public)
    if source_subs:
        subs['rutube'] = int(source_subs.group(1))
    videos = [v for v in S.rutube_cards(public) if v['views'] is not None]
    for v in videos:
        add('rutube', v['id'], v['views'], text=v['title'], date=v['date'])
    if videos:
        rt_note = f"В открытом канале найдено публикаций со счётчиком: {len(videos)}. Закрытая аналитика Studio не включена."
    print('rutube', len(videos))
except Exception as e:
    print('rutube', type(e).__name__)
# --- MAX: открытая страница канала «Гуманет» (только число подписчиков)
try:
    mx = re.search(r'participantsCount:(\d+)', get('https://max.ru/se15096221_biz'))
    if mx: subs['max'] = int(mx.group(1))
except Exception as e: print('max', type(e).__name__)
# --- запись среза дня (повтор за день заменяет)
old = [json.loads(l) for l in open(SNAP)] if os.path.exists(SNAP) else []
old = [o for o in old if o['d'] != TODAY]
for r in rows: old.append(dict(r, d=TODAY))
for p, n in subs.items(): old.append({"d": TODAY, "p": p, "subs": n})
open(SNAP, 'w').write('\n'.join(json.dumps(o, ensure_ascii=False) for o in old) + '\n')
json.dump(meta, open(META, 'w'), ensure_ascii=False)
# --- темы
TOP = [('Боты и автоматизация', r'бот|автоматиз|n8n|воркфлоу|заявк|менеджер|crm|интеграц'), ('ИИ и нейросети', r'нейросет|\bии\b|ai\b|gpt|модел|промпт|ассистент|робот'),
       ('Бухгалтерия и самозанятые', r'бухгалтер|самозанят|налог|чек|юkassa|юкасс|ндс|усн|отчёт|отчет'), ('Ролики и истории', r'shorts|ролик|мульт|истори|команда|мастерск'), ('3D и печать', r'3d|печат|деталь|модел.*принт|принтер')]
def topic(txt):
    t = (txt or '').lower()
    for n, rx in TOP:
        if re.search(rx, t): return n
    return 'Другое'
# --- расчёт
def score(r): return r['views'] + 5 * r['likes'] + 10 * r['reposts'] + 5 * r['comments']
hist = collections.defaultdict(dict)     # key -> date -> row
for o in old:
    if 'id' in o: hist[f"{o['p']}|{o['id']}"][o['d']] = o
dates = sorted({o['d'] for o in old})
def total_on(d): return sum(v[d]['views'] for v in hist.values() if d in v)
posts = []
for k, v in hist.items():
    last = v[max(v)]; first_seen = meta['first'].get(k, min(v)); dt = meta['date'].get(k) or first_seen
    prev = v.get((NOW - datetime.timedelta(days=7)).strftime('%Y-%m-%d')) or v[min(v)]
    posts.append({"k": k, "p": k.split('|')[0], "date": dt, "text": meta['text'].get(k, ''), "views": last['views'], "likes": last['likes'], "reposts": last['reposts'], "comments": last['comments'], "score": score(last), "d7": last['views'] - prev['views'], "topic": topic(meta['text'].get(k, ''))})
cut = (NOW - datetime.timedelta(days=30)).strftime('%Y-%m-%d')
p30 = [x for x in posts if x['date'] >= cut] or posts
p30.sort(key=lambda x: -x['score'])
bytopic = collections.defaultdict(list)
for x in p30: bytopic[x['topic']].append(x)
tstat = sorted(({"t": t, "n": len(l), "avg": sum(i['score'] for i in l) / len(l), "views": sum(i['views'] for i in l), "likes": sum(i['likes'] for i in l), "rep": sum(i['reposts'] for i in l)} for t, l in bytopic.items()), key=lambda x: -x['avg'])
# --- совет модели
advice = ''
try:
    import lib
    PR = ("Ты аналитик соцсетей студии «Гуманетрия» (боты, n8n, ИИ-автоматизация, бухгалтерия через ИИ). Ниже статистика собственных каналов за 30 дней: лучшие посты, темы со средней вовлечённостью, площадки. "
          "Сделай по-русски кратко (до 900 знаков): 1) что общего у самых сильных постов; 2) какие темы работают лучше и на какой площадке; 3) пять конкретных тем и форматов постов на ближайшую неделю с площадкой для каждого; 4) одна честная оговорка про малость выборки. Без воды, без воскл. знаков, без выдуманных цифр.\n\n")
    data = 'ТЕМЫ: ' + json.dumps(tstat, ensure_ascii=False) + '\nТОП ПОСТЫ: ' + json.dumps([{k: x[k] for k in ('p', 'text', 'views', 'likes', 'reposts', 'comments')} for x in p30[:8]], ensure_ascii=False) + '\nПОДПИСЧИКИ: ' + json.dumps(subs)
    out, mod = lib.chat('stat-panel', ['polza:deepseek/deepseek-v4-flash'], PR + data, 900); advice = (out or '').strip()
except Exception as e: print('модель:', type(e).__name__)
if not advice:
    b = tstat[0] if tstat else None
    advice = f"Лучшая тема за 30 дней: {b['t']} (средняя вовлечённость {b['avg']:.0f}). Повторять формат лучших постов, смотреть таблицу ниже." if b else 'Данных пока мало.'
# --- страница в стиле сайта
PN = {'max': 'MAX', 'vk': 'ВК', 'gumanetriya_ai': 'Telegram: Мастерская', 'gumanetriya_roboty': 'Telegram: Истории роботов', 'gumanetriya_3d': 'Telegram: 3D', 'youtube': 'YouTube', 'rutube': 'RUTUBE'}
subser = collections.defaultdict(list)
for o in old:
    if 'subs' in o and o['subs'] >= 0: subser[o['p']].append((o['d'], o['subs']))
cards = ''
for p, v in sorted(subser.items()):
    v = sorted(v); cur = v[-1][1]; d7 = cur - (next((s for d, s in v if d >= (NOW - datetime.timedelta(days=7)).strftime('%Y-%m-%d')), v[0][1])); pv = sum(x['views'] for x in posts if x['p'] == p)
    cards += f'<div class=card><b>{html.escape(PN.get(p, p))}</b><div class=n>{cur}</div><small>подписчиков · за неделю {d7:+d} · просмотров {pv}</small></div>'
trs = ''.join(f"<tr><td>{html.escape(PN.get(x['p'], x['p']))}<td>{x['date']}<td>{html.escape(x['text'][:90])}<td>{html.escape(x['topic'])}<td>{x['views']}<td>{x['likes']}<td>{x['reposts']}<td>{x['comments']}</tr>" for x in p30[:25])
import kanaly_panel as K
try:
    krows, ka, kl, ks, koc = K.build(D, old, NOW, vkinfo); kzak = K.zaklyuchenie(krows, ka, kl, ks, koc); kblock = K.render(krows, kzak, NOW, 'kanaly.csv'); kcsv = K.csv_text(krows, kzak)
    print('каналы: строк', len(krows), '| вывод', len(kzak))
except Exception as e:
    import traceback; traceback.print_exc(); kblock = f'<p class=say>Таблица каналов не собралась: {html.escape(type(e).__name__)}. Что сделать: запустить сбор ещё раз (s-stat-panel-refresh).</p>'; kcsv = ''
page = S.head('Наши каналы — Гуманетрия', 'stat.html') + f'''<style>{K.CSS}</style><h1>Наши каналы</h1><p class=sub>Собрано {NOW.strftime('%d.%m.%Y %H:%M')} по Екатеринбургу. Обновляется раз в сутки, около 8:10. Только подтверждённые числа; рекламный бюджет здесь не продажи.</p>
{kblock}
<h2>Что постить дальше</h2><div class=ai>{html.escape(advice)}</div>
<details class=sv><summary><h2>Сколько у нас людей</h2><small>подписчики по площадкам и прирост за неделю</small></summary><div class=cards>{cards}</div></details>
<details class=sv><summary><h2>Подписчики по дням</h2><small>график</small></summary><div class=say>Каждая линия — одна площадка. Идёт вверх — людей прибавляется.</div>{S.lines({PN.get(k, k): v for k, v in subser.items()})}</details>
<details class=sv><summary><h2>Сколько всего посмотрели</h2><small>график суммы просмотров</small></summary><div class=say>Сумма просмотров всех наших постов. Чем выше точка, тем больше нас смотрят.</div>{S.lines({'просмотры': [(d, total_on(d)) for d in dates]})}</details>
<details class=sv><summary><h2>О чём писать, чтобы смотрели</h2><small>темы и их отклик</small></summary><div class=say>Длиннее полоска — тема набирает больше внимания. Число в скобках — сколько у нас постов на эту тему.</div>{S.bars([(f"{t['t']} ({t['n']})", t['avg']) for t in tstat])}</details>
<details class=sv><summary><h2>Лучшие посты за 30 дней</h2><small>25 постов с просмотрами и реакциями</small></summary><div class=box><table><tr><th>где<th>дата<th>о чём<th>тема<th>просм.<th>лайки<th>репосты<th>комм.</tr>{trs}</table></div></details>
<p class=m><a href="{S.RUTUBE_OWN}">Открытый канал RUTUBE</a>. {html.escape(rt_note)} Для RUTUBE сравниваем только просмотры; реакции не собираем.</p>
<p class=m>Вовлечённость = просмотры + 5×лайки + 10×репосты + 5×комментарии. ВК: {html.escape(json.dumps(vkinfo, ensure_ascii=False))}</p></div>'''
sec = open(D + '/sekret').read().strip() if os.path.exists(D + '/sekret') else None
if not sec:
    import secrets; sec = secrets.token_hex(6); open(D + '/sekret', 'w').write(sec)
os.makedirs(f'{OUT}/{sec}', exist_ok=True); open(f'{OUT}/{sec}/stat.html', 'w').write(page)
if kcsv: open(f'{OUT}/{sec}/kanaly.csv', 'w', encoding='utf-8', newline='').write(kcsv); os.chmod(f'{OUT}/{sec}/kanaly.csv', 0o644)
print('наши каналы: постов за 30 дн.:', len(p30), '| подписчики:', subs)
