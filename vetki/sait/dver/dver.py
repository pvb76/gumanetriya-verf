#!/usr/bin/env python3
"""Дверь Гуманетрии: вход на сайт gumanetriya.ru.

Способы: логин + пароль (+ секретное слово для восстановления), приглашение, номер заказа,
Яндекс ID, VK ID, Google, Telegram. Роли: hozyain, semya, pomoshnik (админы) и gost.
Только стандартная библиотека Python. Данные: /var/lib/dver (users, sessions, invites).
Caddy спрашивает /check (forward_auth) перед каждой закрытой страницей.
"""
import base64, hashlib, hmac, json, os, re, secrets, threading, time, urllib.parse, urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

D = os.environ.get('DVER_DIR', '/var/lib/dver')
CFG = json.load(open(os.path.join(D, 'config.json'), encoding='utf-8'))
BASE = CFG.get('base', 'https://gumanetriya.ru')
COOKIE = 'dv'
ADMIN = ('hozyain', 'semya', 'pomoshnik')
ROLE_RU = {'hozyain': 'хозяин дома', 'semya': 'семья', 'pomoshnik': 'помощник', 'gost': 'гость'}
LOCK = threading.Lock()
PENDING = {}          # state -> {p, verifier, next, link, exp}
FAILS = {}            # key -> [timestamps]


def _p(n): return os.path.join(D, n + '.json')
def load(n):
    try: return json.load(open(_p(n), encoding='utf-8'))
    except Exception: return {}
def save(n, v):
    t = _p(n) + '.tmp'
    with open(t, 'w', encoding='utf-8') as f: json.dump(v, f, ensure_ascii=False)
    os.chmod(t, 0o600); os.replace(t, _p(n))


def h_pass(pw, salt=None):
    salt = salt or secrets.token_hex(16)
    return salt, hashlib.scrypt(pw.encode(), salt=bytes.fromhex(salt), n=2 ** 14, r=8, p=1, dklen=32).hex()
def ok_pass(pw, salt, hx): return hmac.compare_digest(h_pass(pw, salt)[1], hx or '')
def norm_word(w): return re.sub(r'\s+', ' ', (w or '').strip().lower().replace('ё', 'е'))


def too_many(key, limit=8, win=900):
    now = time.time(); a = [t for t in FAILS.get(key, []) if now - t < win]; FAILS[key] = a
    return len(a) >= limit
def fail(key): FAILS.setdefault(key, []).append(time.time())


def role_for(ident, cur='gost'):
    r = CFG.get('admins', {}).get(ident)
    return r if r in ADMIN else cur


def new_session(uid, remember, kind='user', extra=None):
    tok = secrets.token_urlsafe(32); ttl = 30 * 86400 if remember else 12 * 3600
    with LOCK:
        s = load('sessions'); now = time.time()
        s = {k: v for k, v in s.items() if v.get('exp', 0) > now}
        s[tok] = dict(uid=uid, exp=now + ttl, kind=kind, rem=bool(remember), **(extra or {}))
        save('sessions', s)
    return tok, (ttl if remember else None)


def who(cookie_header):
    m = re.search(r'(?:^|;\s*)' + COOKIE + r'=([A-Za-z0-9_\-]+)', cookie_header or '')
    if not m: return None
    s = load('sessions').get(m.group(1))
    if not s or s.get('exp', 0) < time.time(): return None
    if s.get('kind') == 'zakaz':
        return {'tok': m.group(1), 'uid': None, 'name': 'Заказ ' + s['o'][:6] + '…', 'role': 'gost', 'kind': 'zakaz', 'orders': [s['o']]}
    u = load('users').get(s['uid'])
    if not u: return None
    return {'tok': m.group(1), 'uid': s['uid'], 'name': u.get('name') or u.get('login'), 'role': u.get('role', 'gost'), 'kind': 'user',
            'login': u.get('login'), 'ids': [i.split(':')[0] for i in u.get('ids', [])], 'orders': u.get('orders', [])}


def find_by_ident(users, ident):
    for uid, u in users.items():
        if ident in u.get('ids', []): return uid
    return None


def upsert_ident(ident, name, email=None, link_uid=None):
    with LOCK:
        users = load('users'); uid = find_by_ident(users, ident)
        if link_uid and link_uid in users and not uid:
            users[link_uid].setdefault('ids', []).append(ident); uid = link_uid
        if not uid:
            uid = secrets.token_hex(8)
            users[uid] = {'name': name or 'Гость', 'ids': [ident], 'role': 'gost', 'created': int(time.time())}
        u = users[uid]
        u['role'] = role_for(ident, u.get('role', 'gost'))
        if email: u['role'] = role_for('email:' + email.lower(), u['role'])
        u['last'] = int(time.time()); save('users', users)
    return uid


def http_json(url, data=None, headers=None):
    body = urllib.parse.urlencode(data).encode() if isinstance(data, dict) else data
    rq = urllib.request.Request(url, data=body, headers=headers or {})
    with urllib.request.urlopen(rq, timeout=15) as r: return json.load(r)


def order_ok(o):
    try:
        j = http_json('https://n8n.gumanetriya.ru/webhook/sait-status?o=' + urllib.parse.quote(o), headers={'Origin': BASE})
        return bool(j.get('ok'))
    except Exception: return False


def prov(p): return (CFG.get('providers') or {}).get(p) or {}
def enabled():
    out = []
    for p in ('yandex', 'vk', 'google'):
        if prov(p).get('id') and prov(p).get('secret'): out.append(p)
    if prov('telegram').get('token') and prov('telegram').get('bot') and prov('telegram').get('domain_ok'): out.append('telegram')
    return out


def safe_next(n):
    n = n or '/'
    return n if n.startswith('/') and not n.startswith('//') and '\n' not in n else '/'


class H(BaseHTTPRequestHandler):
    server_version = 'dver'
    def log_message(self, *a): pass

    def ip(self): return (self.headers.get('X-Forwarded-For') or self.client_address[0]).split(',')[0].strip()

    def out(self, code, obj=None, cookie=None, loc=None, ctype='application/json'):
        b = b'' if obj is None else (json.dumps(obj, ensure_ascii=False).encode() if ctype == 'application/json' else obj.encode())
        self.send_response(code)
        if loc: self.send_header('Location', loc)
        if cookie is not None: self.send_header('Set-Cookie', cookie)
        self.send_header('Cache-Control', 'no-store')
        if b: self.send_header('Content-Type', ctype + '; charset=utf-8')
        self.send_header('Content-Length', str(len(b))); self.end_headers(); self.wfile.write(b)

    def set_cookie(self, tok, maxage):
        return f'{COOKIE}={tok}; Path=/; HttpOnly; Secure; SameSite=Lax' + (f'; Max-Age={maxage}' if maxage else '')

    def body(self):
        n = int(self.headers.get('Content-Length') or 0)
        if n > 20000: return {}
        raw = self.rfile.read(n) if n else b''
        try: return json.loads(raw or b'{}')
        except Exception: return dict(urllib.parse.parse_qsl(raw.decode('utf-8', 'ignore')))

    def same_origin(self):
        o = self.headers.get('Origin') or ''
        return (not o) or o in (BASE, 'https://gumanetriya.com')

    # ---------- GET ----------
    def do_GET(self):
        u = urllib.parse.urlparse(self.path); q = dict(urllib.parse.parse_qsl(u.query)); p = u.path
        if p == '/check':
            w = who(self.headers.get('Cookie'))
            if w:
                self.send_response(200); self.send_header('X-Dver-Role', w['role']); self.send_header('Content-Length', '0'); self.end_headers(); return
            uri = self.headers.get('X-Forwarded-Uri') or q.get('u') or '/'
            acc = self.headers.get('Accept') or ''
            if 'text/html' in acc or acc in ('', '*/*') and uri.endswith('.html'):
                return self.out(302, loc='/vhod.html?next=' + urllib.parse.quote(safe_next(uri)))
            return self.out(401, {'ok': 0, 'err': 'нужен вход'})
        if p == '/ya':
            w = who(self.headers.get('Cookie'))
            if not w: return self.out(200, {'ok': 0, 'sposoby': enabled(), 'tg_bot': prov('telegram').get('bot') if 'telegram' in enabled() else ''})
            r = {k: w.get(k) for k in ('name', 'role', 'kind', 'login', 'ids', 'orders')}; r.update(ok=1, admin=w['role'] in ADMIN, role_ru=ROLE_RU.get(w['role'], ''))
            if r['admin']: r['links'] = CFG.get('admin_links', [])
            return self.out(200, r)
        m = re.match(r'^/oauth/(yandex|vk|google)/(start|cb)$', p)
        if m: return self.oauth(m.group(1), m.group(2), q)
        if p == '/tg': return self.tg(q)
        if p == '/vyhod':
            w = who(self.headers.get('Cookie'))
            if w:
                with LOCK:
                    s = load('sessions'); s.pop(w['tok'], None); save('sessions', s)
            return self.out(302, loc='/vhod.html?vyshli=1', cookie=f'{COOKIE}=; Path=/; HttpOnly; Secure; SameSite=Lax; Max-Age=0')
        if p == '/zdorov': return self.out(200, {'ok': 1, 'sposoby': enabled()})
        return self.out(404, {'ok': 0})

    # ---------- POST ----------
    def do_POST(self):
        if not self.same_origin(): return self.out(403, {'ok': 0, 'err': 'чужой адрес'})
        p = urllib.parse.urlparse(self.path).path; b = self.body(); ip = self.ip()
        if b.get('sayt'): return self.out(400, {'ok': 0, 'err': 'робот'})   # honeypot
        rem = str(b.get('rem', '')).lower() in ('1', 'true', 'on', 'yes')
        nxt = safe_next(b.get('next'))
        if p in ('/vhod', '/reg', '/vosst', '/zakaz', '/priglas') and too_many('ip:' + ip):
            return self.out(429, {'ok': 0, 'err': 'Слишком много попыток. Подождите 15 минут.'})

        if p == '/reg':
            login = (b.get('login') or '').strip().lower(); pw = b.get('pw') or ''; pw2 = b.get('pw2') or ''
            word = norm_word(b.get('word')); code = (b.get('code') or '').strip()
            if not re.fullmatch(r'[a-z0-9_.\-@]{3,40}', login): return self.out(400, {'ok': 0, 'err': 'Логин: 3–40 знаков, латиница, цифры, точка, дефис.'})
            if len(pw) < 8: return self.out(400, {'ok': 0, 'err': 'Пароль не короче 8 знаков.'})
            if pw != pw2: return self.out(400, {'ok': 0, 'err': 'Пароли не совпадают.'})
            if len(word) < 3: return self.out(400, {'ok': 0, 'err': 'Секретное слово не короче 3 букв: по нему вы вернёте доступ.'})
            if str(b.get('soglasie', '')).lower() not in ('1', 'true', 'on', 'yes'): return self.out(400, {'ok': 0, 'err': 'Нужно согласие на обработку данных.'})
            role = 'gost'
            with LOCK:
                users = load('users'); inv = load('invites')
                if any(u.get('login') == login for u in users.values()) or login in CFG.get('reserved', []) and not code:
                    fail('ip:' + ip); return self.out(409, {'ok': 0, 'err': 'Такой логин занят. Выберите другой.'})
                if code:
                    i = inv.get(code)
                    if not i or i.get('exp', 0) < time.time() or i.get('left', 1) <= 0:
                        fail('ip:' + ip); return self.out(400, {'ok': 0, 'err': 'Приглашение не найдено или истекло.'})
                    if i.get('login') and i['login'] != login: return self.out(400, {'ok': 0, 'err': f'Это приглашение для логина «{i["login"]}».'})
                    role = i.get('role', 'gost'); i['left'] = i.get('left', 1) - 1; save('invites', inv)
                salt, hx = h_pass(pw); ws, wh = h_pass(word)
                uid = secrets.token_hex(8)
                users[uid] = {'login': login, 'name': (b.get('name') or login).strip()[:40], 'salt': salt, 'hash': hx, 'wsalt': ws, 'whash': wh,
                              'ids': ['login:' + login], 'role': role_for('login:' + login, role), 'created': int(time.time())}
                save('users', users)
            tok, ma = new_session(uid, rem)
            return self.out(200, {'ok': 1, 'next': nxt}, cookie=self.set_cookie(tok, ma))

        if p == '/vhod':
            login = (b.get('login') or '').strip().lower(); pw = b.get('pw') or ''
            if too_many('lg:' + login, 6): return self.out(429, {'ok': 0, 'err': 'Много неверных попыток для этого логина. Подождите 15 минут или восстановите пароль.'})
            users = load('users'); uid = next((k for k, u in users.items() if u.get('login') == login), None)
            if not uid or not ok_pass(pw, users[uid].get('salt', '00'), users[uid].get('hash')):
                fail('ip:' + ip); fail('lg:' + login); return self.out(401, {'ok': 0, 'err': 'Логин или пароль не подходят.'})
            tok, ma = new_session(uid, rem)
            return self.out(200, {'ok': 1, 'next': nxt}, cookie=self.set_cookie(tok, ma))

        if p == '/vosst':
            login = (b.get('login') or '').strip().lower(); word = norm_word(b.get('word')); pw = b.get('pw') or ''
            if len(pw) < 8 or pw != (b.get('pw2') or ''): return self.out(400, {'ok': 0, 'err': 'Новый пароль: не короче 8 знаков, оба раза одинаково.'})
            if too_many('lg:' + login, 6): return self.out(429, {'ok': 0, 'err': 'Подождите 15 минут.'})
            with LOCK:
                users = load('users'); uid = next((k for k, u in users.items() if u.get('login') == login), None)
                if not uid or not ok_pass(word, users[uid].get('wsalt', '00'), users[uid].get('whash')):
                    fail('ip:' + ip); fail('lg:' + login); return self.out(401, {'ok': 0, 'err': 'Логин или секретное слово не подходят.'})
                users[uid]['salt'], users[uid]['hash'] = h_pass(pw); save('users', users)
                s = load('sessions'); s = {k: v for k, v in s.items() if v.get('uid') != uid}; save('sessions', s)
            tok, ma = new_session(uid, rem)
            return self.out(200, {'ok': 1, 'next': nxt}, cookie=self.set_cookie(tok, ma))

        if p == '/zakaz':
            o = re.sub(r'[^a-z0-9]', '', (b.get('o') or '').lower())
            if not 8 <= len(o) <= 40 or not order_ok(o):
                fail('ip:' + ip); return self.out(404, {'ok': 0, 'err': 'Заказ с таким номером не найден. Номер есть в письме и на странице после оплаты.'})
            w = who(self.headers.get('Cookie'))
            if w and w['uid']:
                with LOCK:
                    users = load('users'); us = users[w['uid']]; us.setdefault('orders', [])
                    if o not in us['orders']: us['orders'].append(o)
                    save('users', users)
                return self.out(200, {'ok': 1, 'next': nxt})
            tok, ma = new_session(None, rem, kind='zakaz', extra={'o': o})
            return self.out(200, {'ok': 1, 'next': nxt}, cookie=self.set_cookie(tok, ma))

        if p == '/priglas':   # проверить код приглашения до регистрации
            i = load('invites').get((b.get('code') or '').strip())
            if not i or i.get('exp', 0) < time.time() or i.get('left', 1) <= 0:
                fail('ip:' + ip); return self.out(404, {'ok': 0, 'err': 'Приглашение не найдено или истекло.'})
            return self.out(200, {'ok': 1, 'role_ru': ROLE_RU.get(i.get('role', 'gost')), 'login': i.get('login', '')})

        w = who(self.headers.get('Cookie'))
        if p == '/admin/priglas':
            if not w or w['role'] not in ADMIN: return self.out(403, {'ok': 0, 'err': 'только для хозяев'})
            code = secrets.token_urlsafe(9); days = min(int(b.get('dney') or 7), 30)
            role = b.get('role') if b.get('role') in ('gost', 'semya') and w['role'] == 'hozyain' else 'gost'
            with LOCK:
                inv = load('invites'); now = time.time(); inv = {k: v for k, v in inv.items() if v.get('exp', 0) > now}
                inv[code] = {'role': role, 'exp': now + days * 86400, 'left': max(1, min(int(b.get('raz') or 1), 50)), 'by': w['uid']}
                save('invites', inv)
            return self.out(200, {'ok': 1, 'link': f'{BASE}/vhod.html?priglas={code}', 'dney': days, 'role_ru': ROLE_RU[role]})
        if p == '/admin/svodka':
            if not w or w['role'] not in ADMIN: return self.out(403, {'ok': 0})
            users = load('users'); s = load('sessions'); now = time.time()
            return self.out(200, {'ok': 1, 'lyudey': len(users), 'gostey': sum(1 for u in users.values() if u.get('role') == 'gost'),
                                  'seansov': sum(1 for v in s.values() if v.get('exp', 0) > now),
                                  'sposoby': enabled()})
        return self.out(404, {'ok': 0})

    # ---------- OAuth ----------
    def oauth(self, p, step, q):
        c = prov(p)
        if not (c.get('id') and c.get('secret')): return self.out(302, loc='/vhod.html?oshibka=' + urllib.parse.quote('Этот способ ещё подключается'))
        cb = f'{BASE}/dver/oauth/{p}/cb'
        if step == 'start':
            st = secrets.token_urlsafe(24); ver = secrets.token_urlsafe(48)
            chal = base64.urlsafe_b64encode(hashlib.sha256(ver.encode()).digest()).rstrip(b'=').decode()
            w = who(self.headers.get('Cookie'))
            now = time.time()
            for k in [k for k, v in PENDING.items() if v['exp'] < now]: PENDING.pop(k, None)
            PENDING[st] = {'p': p, 'ver': ver, 'next': safe_next(q.get('next')), 'rem': q.get('rem') == '1', 'link': w['uid'] if w and w.get('uid') else None, 'exp': now + 600}
            if p == 'yandex':
                url = 'https://oauth.yandex.ru/authorize?' + urllib.parse.urlencode({'response_type': 'code', 'client_id': c['id'], 'redirect_uri': cb, 'state': st, 'force_confirm': 'no'})
            elif p == 'google':
                url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode({'response_type': 'code', 'client_id': c['id'], 'redirect_uri': cb, 'state': st, 'scope': 'openid email profile', 'prompt': 'select_account'})
            else:
                url = 'https://id.vk.com/authorize?' + urllib.parse.urlencode({'response_type': 'code', 'client_id': c['id'], 'redirect_uri': cb, 'state': st, 'scope': 'email', 'code_challenge': chal, 'code_challenge_method': 'S256'})
            return self.out(302, loc=url)
        pend = PENDING.pop(q.get('state', ''), None)
        if not pend or pend['p'] != p or not q.get('code'):
            return self.out(302, loc='/vhod.html?oshibka=' + urllib.parse.quote('Вход прервался. Попробуйте ещё раз.'))
        try:
            if p == 'yandex':
                t = http_json('https://oauth.yandex.ru/token', {'grant_type': 'authorization_code', 'code': q['code'], 'client_id': c['id'], 'client_secret': c['secret']})
                i = http_json('https://login.yandex.ru/info?format=json', headers={'Authorization': 'OAuth ' + t['access_token']})
                ident, name, email = 'yandex:' + str(i['id']), i.get('display_name') or i.get('real_name') or i.get('login'), i.get('default_email')
            elif p == 'google':
                t = http_json('https://oauth2.googleapis.com/token', {'grant_type': 'authorization_code', 'code': q['code'], 'client_id': c['id'], 'client_secret': c['secret'], 'redirect_uri': cb})
                pl = t['id_token'].split('.')[1]; i = json.loads(base64.urlsafe_b64decode(pl + '=' * (-len(pl) % 4)))
                if i.get('aud') != c['id'] or i.get('iss') not in ('https://accounts.google.com', 'accounts.google.com'): raise ValueError('aud')
                ident, name, email = 'google:' + i['sub'], i.get('name') or i.get('email'), i.get('email') if i.get('email_verified') else None
            else:
                t = http_json('https://id.vk.com/oauth2/auth', {'grant_type': 'authorization_code', 'code': q['code'], 'code_verifier': pend['ver'], 'client_id': c['id'],
                                                               'device_id': q.get('device_id', ''), 'redirect_uri': cb, 'state': q.get('state', '')})
                i = http_json('https://id.vk.com/oauth2/user_info', {'client_id': c['id'], 'access_token': t['access_token']})['user']
                ident, name, email = 'vk:' + str(i['user_id']), (i.get('first_name', '') + ' ' + i.get('last_name', '')).strip(), i.get('email')
        except Exception:
            return self.out(302, loc='/vhod.html?oshibka=' + urllib.parse.quote('Сервис входа не ответил. Попробуйте ещё раз или войдите по логину.'))
        uid = upsert_ident(ident, name, email, pend['link'])
        tok, ma = new_session(uid, pend['rem'] or True)
        return self.out(302, loc=pend['next'], cookie=self.set_cookie(tok, ma))

    def tg(self, q):
        c = prov('telegram'); hsh = q.pop('hash', '')
        if not c.get('token') or not hsh: return self.out(302, loc='/vhod.html?oshibka=' + urllib.parse.quote('Telegram-вход ещё подключается'))
        nxt = safe_next(q.pop('next', '/')); rem = q.pop('rem', '1') == '1'
        dcs = '\n'.join(f'{k}={v}' for k, v in sorted(q.items()))
        calc = hmac.new(hashlib.sha256(c['token'].encode()).digest(), dcs.encode(), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(calc, hsh) or time.time() - int(q.get('auth_date', 0)) > 86400:
            return self.out(302, loc='/vhod.html?oshibka=' + urllib.parse.quote('Telegram не подтвердил вход'))
        w = who(self.headers.get('Cookie'))
        uid = upsert_ident('tg:' + q['id'], (q.get('first_name', '') + ' ' + q.get('last_name', '')).strip() or q.get('username'), None, w['uid'] if w and w.get('uid') else None)
        tok, ma = new_session(uid, rem)
        return self.out(302, loc=nxt, cookie=self.set_cookie(tok, ma))


if __name__ == '__main__':
    host, port = CFG.get('listen', '172.19.0.1:8768').split(':')
    print('дверь гуманетрии:', host, port, 'способы:', enabled(), flush=True)
    ThreadingHTTPServer((host, int(port)), H).serve_forever()
