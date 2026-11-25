/* Витрина Гуманетрии (слово Капитана 25.11): карточки услуг → страница услуги (образец, варианты, допы, оплата) + корзина.
   Страница с data-shop="grid" (oplata.html) — каталог и корзина; data-shop="item" (usluga.html) — одна услуга. */
(function () {
  'use strict';
  var API = 'https://n8n.gumanetriya.ru/webhook/', CHAT = API + '{{N8N_WEBHOOK_CHAT}}';
  var LAVA = 'https://app.lava.top/gumanetriya';
  var TALKS = ['wb', 'kanal', 'ai', 'n8n', 'k1c', 'sopr', 'chas'];
  var isT = function (k) { return TALKS.indexOf(k) >= 0; };
  var $ = function (id) { return document.getElementById(id); };
  var rub = function (v) { return Number(v).toLocaleString('ru-RU') + '\u00a0₽'; };
  var esc = function (s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); };
  var K = [], DISC = [];
  var ICON = {
    video: '<rect x="3" y="5" width="18" height="14" rx="3"/><path d="M10 9.5v5l4.5-2.5z"/>',
    wb: '<path d="M4 5h16v11H9l-5 4z"/><path d="M8 9.5h8M8 12.5h5"/>',
    kanal: '<path d="M21 3 3 10.5l7 2.5 2.5 7z"/><path d="m10 13 5-5"/>',
    ai: '<rect x="5" y="7" width="14" height="11" rx="3"/><path d="M12 7V4M9 12h.01M15 12h.01M9.5 15.5h5"/>',
    n8n: '<circle cx="5" cy="12" r="2"/><circle cx="19" cy="6" r="2"/><circle cx="19" cy="18" r="2"/><path d="M7 12h4l4-5.5M11 12l4 5.5"/>',
    k1c: '<path d="M3 8l9-5 9 5v8l-9 5-9-5z"/><path d="M3 8l9 5 9-5M12 13v8"/>',
    kstor: '<path d="M12 3 4 6v6c0 4.5 3.4 8 8 9 4.6-1 8-4.5 8-9V6z"/><path d="m9 12 2 2 4-4"/>',
    scan: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 15h6M9 18h3"/>',
    sopr: '<circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="3.5"/><path d="m5.5 5.5 3.5 3.5M15 15l3.5 3.5M18.5 5.5 15 9M9 15l-3.5 3.5"/>',
    chas: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>'
  };
  var BG = { video: 'linear-gradient(135deg,#6B1F2A,#9A3345)', wb: 'linear-gradient(135deg,#0E7C6B,#14a58f)', kanal: 'linear-gradient(135deg,#0B1F1B,#1f4a40)', ai: 'linear-gradient(135deg,#6B1F2A,#0E7C6B)',
    n8n: 'linear-gradient(135deg,#9A7B58,#c4a27b)', k1c: 'linear-gradient(135deg,#0A6356,#0B1F1B)', kstor: 'linear-gradient(135deg,#1E1A19,#6B1F2A)', scan: 'linear-gradient(135deg,#9A7B58,#6B1F2A)',
    sopr: 'linear-gradient(135deg,#0E7C6B,#0B1F1B)', chas: 'linear-gradient(135deg,#6E6660,#1E1A19)' };
  var SAMPLE = {
    video: ['Три фото товара и название', 'Ролик 5–10 секунд: движение, крупный план, подпись с главным преимуществом. Две правки входят.'],
    wb: ['Отзыв покупателя: «Пришло с трещиной»', 'Готовый ответ в тоне вашего бренда и кнопки «Опубликовать» или «Переписать» в Telegram.'],
    kanal: ['Покупатель оплатил доступ в закрытый канал', 'Бот прислал личную ссылку, за 3 дня до конца напомнил о продлении, вы видите список подписчиков.'],
    ai: ['Ваш прайс и вопросы-ответы', 'Бот отвечает клиентам по вашим документам, а чего не знает, передаёт человеку.'],
    n8n: ['Заявка из формы на сайте', 'Строка в таблице, карточка в Telegram, крупный заказ сразу менеджеру, без дублей.'],
    k1c: ['Новый заказ в 1С', 'Сообщение в Telegram, утренняя сводка в 9:00, предупреждение, когда товар заканчивается.'],
    kstor: ['Сайт перестал открываться', 'Сообщение в мессенджер за 5 минут; за 30 дней предупреждение о конце домена и сертификата.'],
    scan: ['Скан счёта или PDF', 'Редактируемая таблица Excel или документ Word со строками и итогами.'],
    sopr: ['Бот или автоматизация сломались', 'Исправление, мелкая доработка или ответ на вопрос без новой сметы.'],
    chas: ['Задача, которую нужно решить вместе', 'Почасовая или посуточная работа специалиста над вашей задачей.']
  };
  var CK = 'gum_cart', TTL = 7 * 864e5;
  function cget() { try { var c = JSON.parse(localStorage.getItem(CK) || 'null'); if (!c || !Array.isArray(c.i) || Date.now() - c.t > TTL) { localStorage.removeItem(CK); return { t: 0, i: [] }; } return c; } catch (e) { return { t: 0, i: [] }; } }
  function cset(c) { try { if (c.i.length) localStorage.setItem(CK, JSON.stringify(c)); else localStorage.removeItem(CK); } catch (e) {} fab(); }
  function svc(k) { return K.filter(function (x) { return x.k === k; })[0]; }
  function discOf(n) { for (var i = 0; i < DISC.length; i++) if (n >= DISC[i][0]) return DISC[i][1]; return 0; }
  function priceOf(it) {
    var s = svc(it.svc); if (!s || s.sub || isT(it.svc)) return null; var pl = s.plans[it.pi]; if (!pl) return null;
    var sum = pl.p, na = 0, ex = [];
    s.add.forEach(function (a, i) { if (it.mask & (1 << i)) { sum += a.p * (pl.mult || 1); na++; ex.push(a.n); } });
    return { it: it, sum: sum, pos: 1 + na, txt: s.t + ': ' + pl.n + (ex.length ? ' + ' + ex.join(', ') : '') };
  }
  function total(list) {
    var t = 0, pos = 0; list.forEach(function (r) { t += r.sum; pos += r.pos; });
    var d = discOf(pos); return { raw: t, sum: Math.round(t * (100 - d) / 100), d: d, pos: pos };
  }
  function iconSvg(k) { return '<svg viewBox="0 0 24 24" aria-hidden="true">' + (ICON[k] || ICON.sopr) + '</svg>'; }
  function minPrice(s) { return Math.min.apply(null, s.plans.map(function (p) { return p.p; })); }
  function fab() {
    var b = $('sh-fab'); if (!b) { b = document.createElement('a'); b.id = 'sh-fab'; b.className = 'sh-fab'; b.href = '/oplata.html#korzina'; document.body.appendChild(b); }
    var n = cget().i.length; b.className = 'sh-fab' + (n ? ' on' : ''); b.textContent = 'Корзина: ' + n + ' · к оплате';
  }
  function chatSend(tekst, imya, kontakt) {
    var sid = ''; try { sid = localStorage.getItem('fc_sid') || ''; } catch (e) {}
    return fetch(CHAT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ sid: sid || ('s' + Math.random().toString(36).slice(2, 10)), imya: imya, kontakt: kontakt, tekst: tekst, foto: '', yazyk: 'ru', stranitsa: location.pathname.slice(0, 100) }) })
      .then(function (r) { if (!r.ok) throw new Error('chat'); return true; });
  }
  /* ---------- карточки ---------- */
  function card(s) {
    var link = 'oplata.html#u=' + s.k;
    return '<article class="sc"><div class="sc-pic" style="background:' + (BG[s.k] || BG.sopr) + '">' + iconSvg(s.k) + '</div><div class="sc-b">' +
      '<h3><a href="' + link + '" data-open="' + s.k + '">' + esc(s.t) + '</a></h3><p class="sc-d">' + esc(s.x.length > 120 ? s.x.slice(0, 117).replace(/\s+\S*$/, '') + '…' : s.x) + '</p>' +
      '<div class="sc-pr"><b>от ' + rub(minPrice(s)) + '</b><span>' + esc(s.d) + '</span></div>' +
      '<div class="sc-a"><a class="mb alt" href="' + link + '" data-open="' + s.k + '">Подробнее</a>' +
      '<button class="mb" type="button" data-add="' + s.k + '">В корзину</button></div></div></article>';
  }
  /* ---------- оплата (общая для корзины и услуги) ---------- */
  function payBlock(opts) {
    var who = '<div class="sh-who"><label>Имя<input id="' + opts.id + '-n" name="name" autocomplete="name" maxlength="80" placeholder="Как к вам обращаться"></label>' +
      '<label>Контакт: телефон, почта или Telegram<input id="' + opts.id + '-k" name="kontakt" maxlength="120" autocomplete="off" placeholder="+7…, почта или @ник"></label></div>' +
      '<label class="sh-ok"><input type="checkbox" id="' + opts.id + '-c"><span>Согласен на обработку персональных данных по <a href="soglasie.html" target="_blank">согласию</a> и <a href="politika.html" target="_blank">политике</a>. Данные нужны только для выполнения заказа.</span></label>';
    if (opts.noPay) return who + '<p class="sh-err" id="' + opts.id + '-e" role="alert"></p>';
    return who + '<p class="sh-say">Если вас всё устраивает, переходите к оплате.</p>' +
      '<div class="sh-pm" id="' + opts.id + '-pm">' +
      '<button type="button" class="pm-b main" data-m="card"><b>Картой</b><small>Visa, Mastercard, Мир, SberPay, T-Pay</small></button>' +
      '<button type="button" class="pm-b" data-m="sbp"><b>По СБП</b><small>откроется приложение вашего банка</small></button>' +
      '<a class="pm-b" id="' + opts.id + '-lava" href="' + LAVA + '" target="_blank" rel="noopener"><b>Картой зарубежного банка</b><small>в долларах, через Lava.top; условия те же</small></a></div>' +
      '<p class="sh-err" id="' + opts.id + '-e" role="alert"></p>' +
      '<p class="sh-note">Платёж принимает ЮKassa, данные карты к нам не попадают. Оплачивая, вы принимаете <a href="oferta.html">договор-оферту</a>. Нужен счёт для компании — напишите в чат справа.</p>';
  }
  function who(id) {
    var e = $(id + '-e'); e.textContent = '';
    var name = $(id + '-n').value.trim(), kontakt = $(id + '-k').value.trim();
    if (name.length < 2 || kontakt.length < 3) { e.textContent = 'Укажите имя и контакт, чтобы мы могли передать результат.'; $(id + '-n').focus(); return null; }
    if (!$(id + '-c').checked) { e.textContent = 'Отметьте согласие на обработку данных.'; return null; }
    try { localStorage.setItem('sh_who', JSON.stringify({ n: name, k: kontakt })); } catch (x) {}
    return { name: name, kontakt: kontakt };
  }
  function fillWho(id) {
    var rem = null; try { rem = JSON.parse(localStorage.getItem('sh_who') || 'null'); } catch (e) {}
    if (rem) { if ($(id + '-n')) $(id + '-n').value = rem.n || ''; if ($(id + '-k')) $(id + '-k').value = rem.k || ''; }
  }
  function wirePay(opts) {
    fillWho(opts.id);
    [].forEach.call(document.querySelectorAll('#' + opts.id + '-pm [data-m]'), function (b) {
      b.addEventListener('click', function () {
        var e = $(opts.id + '-e'); e.textContent = '';
        var o = opts.getOrder(); if (!o || !o.items.length) { e.textContent = 'Сначала выберите услугу.'; return; }
        var w = who(opts.id); if (!w) return;
        var all = [].slice.call(document.querySelectorAll('#' + opts.id + '-pm [data-m]')); all.forEach(function (x) { x.disabled = true; }); var old = b.innerHTML; b.innerHTML = '<b>Создаём платёж…</b>';
        fetch(API + 'sait-pay', { method: 'POST', body: new URLSearchParams({ cart: JSON.stringify(o.items), name: w.name, kontakt: w.kontakt, soglasie: '1', method: b.dataset.m }) })
          .then(function (r) { return r.json(); })
          .then(function (j) {
            if (j.ok && j.url) { if (o.fromCart) { var c = cget(); var rest = c.i.filter(function (it) { return !priceOf(it); }); if (rest.length) { c.i = rest; cset(c); } else cset({ t: 0, i: [] }); } location.href = j.url; return; }
            e.textContent = j.err || 'Не получилось создать платёж. Попробуйте ещё раз или напишите в чат справа.'; all.forEach(function (x) { x.disabled = false; }); b.innerHTML = old;
          })
          .catch(function () { e.textContent = 'Нет связи с платёжным сервером. Попробуйте ещё раз или напишите в чат справа.'; all.forEach(function (x) { x.disabled = false; }); b.innerHTML = old; });
      });
    });
  }
  /* ---------- модальное окно: услуга открывается прямо на странице ---------- */
  function openModal(k, push) {
    if (!svc(k)) return;
    var m = $('sh-modal');
    if (!m) {
      m = document.createElement('div'); m.id = 'sh-modal'; m.className = 'sh-modal'; m.setAttribute('role', 'dialog'); m.setAttribute('aria-modal', 'true');
      m.innerHTML = '<div class="sh-mbox"><button type="button" class="sh-mx" aria-label="Закрыть">×</button><div id="sh-mroot"></div></div>';
      document.body.appendChild(m);
      m.addEventListener('click', function (e) { if (e.target === m || (e.target.closest && e.target.closest('.sh-mx'))) closeModal(true); });
      document.addEventListener('keydown', function (e) { if (e.key === 'Escape') closeModal(true); });
      window.addEventListener('popstate', function () { var h = (location.hash.match(/^#u=([a-z0-9]+)$/) || [])[1]; if (h) openModal(h, false); else closeModal(false); });
    }
    renderItem(k, $('sh-mroot'), true);
    m.classList.add('on'); document.body.classList.add('sh-lock'); m.scrollTop = 0;
    if (push) { try { history.pushState({ u: k }, '', '#u=' + k); } catch (e) {} }
  }
  function closeModal(fromUi) {
    var m = $('sh-modal'); if (!m || !m.classList.contains('on')) return;
    if (fromUi && history.state && history.state.u) { history.back(); return; }
    m.classList.remove('on'); document.body.classList.remove('sh-lock'); $('sh-mroot').innerHTML = '';
    if (/^#u=/.test(location.hash)) { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) {} }
  }
  /* ---------- страница-каталог с корзиной ---------- */
  function renderGrid() {
    var root = $('sh-root');
    root.innerHTML = '<div id="sh-cartbox"></div><div class="sh-grid">' + K.map(card).join('') + '</div>';
    root.addEventListener('click', function (e) {
      var o = e.target.closest && e.target.closest('[data-open]');
      if (o) { e.preventDefault(); openModal(o.getAttribute('data-open'), true); return; }
      var b = e.target.closest && e.target.closest('[data-add]'); if (!b) return;
      var c = cget(); if (c.i.length >= 6) { alert('В корзине может быть до 6 позиций.'); return; }
      c.i.push({ svc: b.dataset.add, pi: 0, mask: 0 }); if (!c.t) c.t = Date.now(); cset(c); drawCart(true);
    });
    drawCart(false);
  }
  function rowsOf(c) {
    return c.i.map(function (it, idx) { var p = priceOf(it); if (p) return { idx: idx, p: p }; var t = talkOf(it); return t ? { idx: idx, t: t } : null; }).filter(Boolean);
  }
  function drawCart(scroll, done) {
    var box = $('sh-cartbox'); if (!box) return;
    var c = cget(), rows = rowsOf(c);
    if (!rows.length) { box.innerHTML = done ? '<section class="sh-cart" id="korzina"><div class="sh-done" style="margin:0">' + done + '</div></section>' : ''; return; }
    var list = rows.filter(function (r) { return r.p; }).map(function (r) { return r.p; }), talks = rows.filter(function (r) { return r.t; });
    var t = total(list), left = Math.max(1, Math.ceil((c.t + TTL - Date.now()) / 864e5));
    var h = '<section class="sh-cart" id="korzina"><h2>Корзина</h2>' + (done ? '<div class="sh-done">' + done + '</div>' : '') + '<ul>' + rows.map(function (r) {
      return '<li><span>' + esc(r.p ? r.p.txt : r.t.txt) + '</span>' + (r.p ? '<b>' + rub(r.p.sum) + '</b>' : '<b class="tk">по согласованию</b>') + '<button type="button" data-rm="' + r.idx + '" aria-label="Убрать из корзины">×</button></li>';
    }).join('') + '</ul>';
    if (list.length) {
      h += '<div class="sh-sum"><div class="what">' + (t.d ? 'Скидка ' + t.d + '% за ' + t.pos + ' поз.: было ' + rub(t.raw) : 'Добавьте ещё услугу или дополнение: скидка от 5%') + '<small>Корзина хранится 7 дней, осталось ' + left + ' дн. <a href="#" id="sh-clear">Очистить корзину</a></small></div><div class="tot">' + rub(t.sum) + '</div></div>';
    } else {
      h += '<div class="sh-sum"><div class="what">Цену и срок назовём до начала работы<small>Корзина хранится 7 дней, осталось ' + left + ' дн. <a href="#" id="sh-clear">Очистить корзину</a></small></div></div>';
    }
    h += payBlock({ id: 'cp', noPay: !list.length });
    if (talks.length) h += '<div class="sh-pm" style="margin-top:12px"><button type="button" class="pm-b' + (list.length ? '' : ' main') + '" id="cp-tq"><b>Отправить заявку: услуги по согласованию (' + talks.length + ')</b><small>цену и срок назовём до начала работы, деньги берём только после согласования</small></button></div>';
    box.innerHTML = h + '</section>';
    if (list.length) wirePay({ id: 'cp', getOrder: function () { var cc = cget(); return { items: cc.i.filter(function (it) { return priceOf(it); }), fromCart: true }; } }); else fillWho('cp');
    box.querySelector('ul').addEventListener('click', function (e) { var i = e.target.dataset && e.target.dataset.rm; if (i == null) return; var cc = cget(); cc.i.splice(+i, 1); if (!cc.i.length) cc.t = 0; cset(cc); drawCart(false); });
    $('sh-clear').addEventListener('click', function (e) { e.preventDefault(); cset({ t: 0, i: [] }); drawCart(false); });
    if (talks.length) $('cp-tq').addEventListener('click', function () {
      var w = who('cp'); if (!w) return; var b = $('cp-tq'), old = b.innerHTML; b.disabled = true; b.innerHTML = '<b>Отправляем…</b>';
      chatSend('ЗАЯВКА С САЙТА (КОРЗИНА). Услуги по согласованию:\n' + talks.map(function (r) { return '- ' + r.t.txt; }).join('\n') + '\nЦену и срок согласуем до начала работы.', w.name, w.kontakt).then(function () {
        var cc = cget(); cc.i = cc.i.filter(function (it) { return !talkOf(it); }); if (!cc.i.length) cc.t = 0; cset(cc);
        drawCart(true, '<b>Заявка получена, спасибо.</b><br>Мы прочитаем и ответим в ближайшее время на контакт, который вы оставили. Цену и срок назовём до начала работы.');
      }).catch(function () { $('cp-e').textContent = 'Не получилось отправить. Напишите нам в чат справа.'; b.disabled = false; b.innerHTML = old; });
    });
    if (scroll) box.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  function talkOf(it) {
    var s = svc(it.svc); if (!s || !(isT(it.svc) || s.sub)) return null; var pl = s.plans[it.pi] || s.plans[0];
    return { it: it, txt: s.t + (pl ? ': ' + pl.n : '') };
  }
  /* ---------- страница или окно услуги ---------- */
  function renderItem(k, root, modal) {
    var s = svc(k);
    if (!s) { root.innerHTML = '<p>Такой услуги нет. <a href="oplata.html">Все услуги</a></p>'; return; }
    if (!modal) document.title = s.t + ' — Гуманетрия';
    var talk = isT(k) || s.sub, sm = SAMPLE[k] || ['Ваша задача', 'Результат по описанию'];
    var head = modal ? '<h2 class="sh-mt">' + esc(s.t) + '</h2>' : '<h1 style="margin:0 0 8px">' + esc(s.t) + '</h1>';
    var h = '<div class="sh-itm">' + (modal ? '' : '<a class="sh-back" href="oplata.html">← Все услуги</a>') + '<div class="sh-hero"><div class="sc-pic" style="background:' + (BG[k] || BG.sopr) + '">' + iconSvg(k) + '</div><div>' + head + '<p class="lead" style="margin:0">' + esc(s.x) + '</p>' +
      '<div class="sh-meta"><span>от <b>' + rub(minPrice(s)) + '</b></span><span>срок: <b>' + esc(s.d) + '</b></span></div>' + '<div class="sh-top"><button type="button" class="pm-b sh-tc" id="toCartTop"><b>В корзину</b><small>выбрать ещё или оформить</small></button><button type="button" class="pm-b" id="toPayTop"><b>' + (talk ? 'Описать задачу' : 'К оплате') + ' ↓</b><small>вариант и сумма ниже</small></button></div></div></div>' +
      '<section class="sh-sec"><h2>Образец</h2><div class="sh-sample"><div><small>Что вы даёте</small>' + esc(sm[0]) + '</div><div class="ar">→</div><div><small>Что получаете</small>' + esc(sm[1]) + '</div></div><span class="sh-tag">Учебный пример, не чужая работа и не отзыв</span> <a class="link-arrow" href="primery.html">Больше примеров</a></section>' +
      '<section class="sh-sec"><h2>Варианты</h2><div class="sh-opts" id="plans">' + s.plans.map(function (p, i) { return '<label class="opt' + (i === 0 ? ' on' : '') + '"><input type="radio" name="plan" value="' + i + '"' + (i === 0 ? ' checked' : '') + '><span class="t">' + esc(p.n) + '</span><span class="p">' + rub(p.p) + '</span></label>'; }).join('') + '</div></section>' +
      (s.add.length ? '<section class="sh-sec"><h2>Дополнительно</h2><div class="sh-opts" id="adds">' + s.add.map(function (a, i) { return '<label class="opt"><input type="checkbox" name="add" value="' + i + '"><span class="t">' + esc(a.n) + '</span><span class="p" data-p="' + a.p + '">+' + rub(a.p) + '</span></label>'; }).join('') + '</div></section>' : '') +
      '<section class="sh-pay" id="oplata"><h2 style="margin:0 0 12px">' + (talk ? 'Описать задачу' : 'Оплата') + '</h2><div class="sh-sum"><div class="what" id="what"></div><div class="tot" id="tot"></div></div>';
    if (talk) {
      h += '<p>Эту услугу собираем под вашу задачу: цену и срок назовём после описания, до начала работы. Напишите, что есть сейчас и что должно получиться.</p>' +
        '<div class="sh-ta"><label>Ваша задача<textarea id="tt" maxlength="1500" placeholder="Например: нужен бот, который отвечает по нашему прайсу"></textarea></label></div>' +
        '<div class="sh-who" style="margin-top:12px"><label>Имя<input id="tn" maxlength="80" autocomplete="name"></label><label>Контакт: телефон, почта или Telegram<input id="tk" maxlength="160" autocomplete="off" placeholder="+7…, почта или @ник"></label></div>' +
        '<label class="sh-ok"><input type="checkbox" id="tc"><span>Согласен на обработку персональных данных по <a href="soglasie.html" target="_blank">согласию</a> и <a href="politika.html" target="_blank">политике</a>.</span></label>' +
        '<div class="sh-pm"><button type="button" class="pm-b main" id="tsend"><b>Отправить описание</b><small>назовём цену и срок до начала работы</small></button>' +
        '<button type="button" class="pm-b" id="toCart"><b>В корзину и выбрать ещё</b><small>заявку отправите из корзины, вместе с другими услугами</small></button></div><p class="sh-err" id="te" role="alert"></p><div id="tdone"></div>';
    } else {
      h += payBlock({ id: 'ip' }) + '<div class="sh-pm" style="margin-top:12px"><button type="button" class="pm-b" id="toCart"><b>В корзину и выбрать ещё</b><small>скидка за вторую позицию — 5%, за третью — 10%</small></button></div>';
    }
    h += '</section></div>';
    root.innerHTML = h;
    var box = root.firstChild;
    function sel() { var pi = +((box.querySelector('[name=plan]:checked') || {}).value || 0), mask = 0; [].forEach.call(box.querySelectorAll('[name=add]'), function (c, i) { if (c.checked) mask |= 1 << i; }); return { pi: pi, mask: mask }; }
    function upd() {
      var v = sel(), pl = s.plans[v.pi], mult = pl.mult || 1;
      [].forEach.call(box.querySelectorAll('.opt'), function (o) { o.classList.toggle('on', o.querySelector('input').checked); });
      [].forEach.call(box.querySelectorAll('#adds .p'), function (p) { p.textContent = '+' + rub(+p.dataset.p * mult); });
      if (talk) { $('what').textContent = pl.n + ' от ' + rub(pl.p); $('tot').textContent = ''; return; }
      var c = cget(), list = c.i.map(priceOf).filter(Boolean), cur = priceOf({ svc: k, pi: v.pi, mask: v.mask }); list.push(cur);
      var t = total(list);
      $('what').innerHTML = esc(cur.txt) + (c.i.length ? '<small>Вместе с товарами в корзине (' + c.i.length + '). Скидка ' + t.d + '%</small>' : (t.d ? '<small>Скидка ' + t.d + '% за дополнение</small>' : '<small>Добавьте дополнение или вторую услугу: скидка от 5%</small>')); $('tot').textContent = rub(t.sum);
    }
    box.addEventListener('change', upd); upd(); /* VITRINA5_V1 */
    var v5c = box.querySelector('#toCartTop'), v5p = box.querySelector('#toPayTop');
    if (v5c) v5c.addEventListener('click', function () { var b = box.querySelector('#toCart'); if (b) { b.click(); var e = box.querySelector('.sh-err:not(:empty)'); if (e) e.scrollIntoView({ behavior: 'smooth', block: 'center' }); } });
    if (v5p) v5p.addEventListener('click', function () { var o = box.querySelector('#oplata'); if (o) o.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    function toCart(errId) {
      var v = sel(), c = cget(); if (c.i.length >= 6) { $(errId).textContent = 'В корзине может быть до 6 позиций.'; return; }
      c.i.push({ svc: k, pi: v.pi, mask: v.mask }); if (!c.t) c.t = Date.now(); cset(c);
      if (modal) { closeModal(true); setTimeout(function () { drawCart(true); }, 30); } else location.href = 'oplata.html#korzina';
    }
    if (talk) {
      fillWho('t'); var rem = null; try { rem = JSON.parse(localStorage.getItem('sh_who') || 'null'); } catch (e) {} if (rem) { $('tn').value = rem.n || ''; $('tk').value = rem.k || ''; }
      $('toCart').addEventListener('click', function () { toCart('te'); });
      $('tsend').addEventListener('click', function () {
        var e = $('te'); e.textContent = ''; var t = $('tt').value.trim(), n = $('tn').value.trim(), kk = $('tk').value.trim();
        if (t.length < 10) { e.textContent = 'Опишите задачу хотя бы в двух словах.'; $('tt').focus(); return; }
        if (n.length < 2 || kk.length < 3) { e.textContent = 'Укажите имя и контакт, чтобы мы могли ответить.'; return; }
        if (!$('tc').checked) { e.textContent = 'Отметьте согласие на обработку данных.'; return; }
        try { localStorage.setItem('sh_who', JSON.stringify({ n: n, k: kk })); } catch (x) {}
        var v = sel(), b = $('tsend'); b.disabled = true; b.innerHTML = '<b>Отправляем…</b>';
        chatSend('ЗАЯВКА С САЙТА. Услуга: ' + s.t + ' (' + s.plans[v.pi].n + ').\n' + t, n, kk).then(function () {
          $('tdone').innerHTML = '<div class="sh-done"><b>Описание получено.</b><br>Мы прочитаем и ответим в ближайшее время на контакт, который вы оставили. Цену и срок назовём до начала работы, деньги берём только после согласования.<div style="margin-top:12px"><a class="mb alt" href="oplata.html">К другим услугам</a></div></div>';
          b.hidden = true;
        }).catch(function () { e.textContent = 'Не получилось отправить. Напишите нам в чат справа.'; b.disabled = false; b.innerHTML = '<b>Отправить описание</b><small>назовём цену и срок до начала работы</small>'; });
      });
      return;
    }
    wirePay({ id: 'ip', getOrder: function () { var v = sel(), c = cget(), items = c.i.filter(function (it) { return priceOf(it); }); items.push({ svc: k, pi: v.pi, mask: v.mask }); return { items: items, fromCart: c.i.length > 0 }; } });
    $('toCart').addEventListener('click', function () { toCart('ip-e'); });
  }
  /* ---------- запуск ---------- */
  var kind = document.body.getAttribute('data-shop');
  if (!kind) return;
  var u = new URLSearchParams(location.search).get('u');
  fab();
  fetch(API + 'sait-katalog').then(function (r) { return r.json(); }).then(function (j) {
    K = j.items || []; DISC = j.disc || [];
    if (kind === 'item') { renderItem(u || '', $('sh-root'), false); return; }
    renderGrid();
    var h = (location.hash.match(/^#u=([a-z0-9]+)$/) || [])[1] || u;
    if (h) openModal(h, false); else if (location.hash === '#korzina') { var b = $('korzina'); if (b) b.scrollIntoView(); }
  }).catch(function () { $('sh-root').innerHTML = '<p class="pay-load">Каталог не загрузился. Обновите страницу или напишите нам в чат справа.</p>'; });
})();
