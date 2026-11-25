/* Чат с Фомой: один файл, подключается на любой странице. Бэкенд — n8n. */
(function () {
  if (window.FomaChat) return;
  var URL_ = 'https://n8n.gumanetriya.ru/webhook/{{N8N_WEBHOOK_CHAT}}';
  var BOT = 'https://t.me/gumanetriya_zakaz_bot';
  var store = null; try { store = window['session' + 'Storage']; store.getItem('x'); } catch (e) { store = null; }
  var mem = {};
  function get(k) { try { return store ? store.getItem(k) : mem[k]; } catch (e) { return mem[k]; } }
  function set(k, v) { mem[k] = v; try { if (store) store.setItem(k, v); } catch (e) {} }
  function rnd() { var a = new Uint8Array(12); (window.crypto || window.msCrypto).getRandomValues(a); return Array.prototype.map.call(a, function (b) { return ('0' + b.toString(16)).slice(-2); }).join(''); }
  var EN = (document.documentElement.lang || '').slice(0, 2) === 'en';
  var L = EN ? { pill: 'Ask Foma', sub: 'AI assistant of the workshop · replies at once', hello: 'Hello. I am Foma, the workshop assistant. Tell me what you need: a website, a bot, automation, spreadsheets. I reply right away and pass it to the maker.', name: 'Name', contact: 'Phone, @telegram, email: all welcome', msg: 'What do you need?', note: 'By sending a message you agree to the <a href="https://gumanetriya.ru/politika.html" target="_blank" rel="noopener noreferrer">data processing policy</a>.', fail: 'The connection to the workshop failed. Please write to {{ПОЧТА_ВЛАДЕЛЬЦА}}', photo: 'Photo attached', remove: 'remove', onlyimg: 'You can attach a photo or a screenshot here. Please send documents by email.', bad: 'Could not attach this photo. Try another one or a screenshot.', nofile: 'This file did not open as an image. Try JPG or PNG.', close: 'Close chat', send: 'Send', clip: 'Attach a photo or screenshot', mic: 'Dictate', got: 'Got it, passed to the maker.', lang: 'en-US', ph: 'Photo', dlg: 'Chat with Foma' }
    : { pill: 'Спросить Фому', sub: 'ИИ-помощник мастерской · отвечает сразу', hello: 'Здравствуйте. Я Фома, помощник мастерской. Напишите, что нужно сделать: сайт, бот, автоматизация, таблицы. Отвечу сразу и передам мастеру.', name: 'Имя', contact: 'Телефон, @ник, почта: можно все', msg: 'Что нужно сделать?', note: 'Отправляя сообщение, вы соглашаетесь с <a href="https://gumanetriya.ru/politika.html" target="_blank" rel="noopener noreferrer">политикой обработки данных</a>.', fail: 'Связь с мастерской сейчас не прошла. Попробуйте ещё раз через минуту или напишите на {{ПОЧТА_СВЯЗИ}}', photo: 'Фото приложено', remove: 'убрать', onlyimg: 'Сюда можно приложить фото или скриншот. Документы пришлите, пожалуйста, на {{ПОЧТА_СВЯЗИ}}', bad: 'Не получилось приложить это фото. Попробуйте другое или скриншот.', nofile: 'Этот файл не открылся как картинка. Попробуйте JPG или PNG.', close: 'Закрыть чат', send: 'Отправить', clip: 'Приложить фото или скриншот', mic: 'Сказать голосом', got: 'Принял, передал мастеру.', lang: 'ru-RU', ph: 'Фото', dlg: 'Чат с Фомой' };
  var sid = get('fc_sid') || ('s' + rnd()); set('fc_sid', sid);
  var log = []; try { log = JSON.parse(get('fc_log') || '[]'); } catch (e) { log = []; }
  var who = { imya: get('fc_imya') || '', kontakt: get('fc_kontakt') || '' };

  var css = '' +
    '.fc-pill{position:fixed;right:20px;bottom:22px;z-index:70;display:inline-flex;align-items:center;gap:9px;padding:11px 16px 11px 13px;border:0;border-radius:999px;background:#fffbee;color:#17201a;font:600 14px/1 Onest,system-ui,sans-serif;cursor:pointer;box-shadow:0 14px 34px -12px rgba(0,0,0,.55),0 0 0 1px rgba(23,32,26,.08);transition:transform .25s ease,box-shadow .25s ease,opacity .25s ease}' +
    '.fc-pill:hover{transform:translateY(-2px);box-shadow:0 18px 38px -12px rgba(0,0,0,.6),0 0 0 1px rgba(23,32,26,.12)}' +
    '.fc-pill:focus-visible,.fc-x:focus-visible,.fc-send:focus-visible,.fc-mic:focus-visible{outline:2px solid #f0a868;outline-offset:2px}' +
    '.fc-pill i{width:9px;height:9px;border-radius:50%;background:#7fb04a;box-shadow:0 0 0 0 rgba(127,176,74,.6);animation:fcp 2.4s ease-out infinite}' +
    '@keyframes fcp{70%{box-shadow:0 0 0 9px rgba(127,176,74,0)}100%{box-shadow:0 0 0 0 rgba(127,176,74,0)}}' +
    'body.has-bot .fc-pill{right:204px;bottom:34px}' +
    '.fc-open .fc-pill{opacity:0;pointer-events:none}' +
    '.fc-panel,.fc-panel *,.fc-pill{box-sizing:border-box;margin:0;letter-spacing:normal;text-transform:none}.fc-panel{padding:0;border:0}.fc-panel label{display:block;padding:0}.fc-panel form{margin:0;border:0;background:none}.fc-panel .fc-head{margin:0}.fc-panel .fc-head b{display:block;color:#fffbee;font-family:Onest,system-ui,sans-serif}' +
    '.fc-panel{position:fixed;right:20px;bottom:20px;z-index:80;width:680px;max-width:calc(100vw - 24px);height:min(820px,calc(100dvh - 32px));display:flex;flex-direction:column;border-radius:22px;overflow:hidden;background:#fffbee;color:#17201a;font:17px/1.5 Onest,system-ui,sans-serif;box-shadow:0 40px 80px -30px rgba(0,0,0,.7),0 0 0 1px rgba(23,32,26,.1);opacity:0;transform:translateY(16px) scale(.97);transform-origin:100% 100%;pointer-events:none;transition:opacity .22s ease,transform .28s cubic-bezier(.2,.8,.2,1)}' +
    '.fc-open .fc-panel{opacity:1;transform:none;pointer-events:auto}' +
    '.fc-head{display:flex;align-items:center;gap:10px;padding:14px 14px 14px 18px;background:#1c2a1f;color:#fffbee}' +
    '.fc-head b{font-weight:700;font-size:18px}.fc-head span{display:block;font-size:14px;opacity:.7;margin-top:1px}' +
    '.fc-ava{width:34px;height:34px;border-radius:12px;background:#dfe9c8;display:grid;place-items:center;flex:none}' +
    '.fc-ava::before{content:"";width:20px;height:11px;border-radius:5px;background:#17201a;box-shadow:inset 5px 0 0 -2px #b9f27c,inset -5px 0 0 -2px #b9f27c}' +
    '.fc-x{margin-left:auto;width:34px;height:34px;border:0;border-radius:10px;background:transparent;color:inherit;font-size:20px;line-height:1;cursor:pointer}.fc-x:hover{background:rgba(255,251,238,.12)}' +
    '.fc-list{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:8px;overscroll-behavior:contain}' +
    '.fc-m{max-width:90%;padding:11px 15px;border-radius:16px;white-space:pre-wrap;overflow-wrap:anywhere}' +
    '.fc-m.f{align-self:flex-start;background:#ebe7d3;border-bottom-left-radius:5px}' +
    '.fc-m.u{align-self:flex-end;background:#2c4a33;color:#fffbee;border-bottom-right-radius:5px}' +
    '.fc-m a{color:inherit;text-decoration:underline}' +
    '.fc-dots{display:inline-flex;gap:4px;padding:4px 0}.fc-dots i{width:6px;height:6px;border-radius:50%;background:#6b7a66;animation:fcd 1s infinite}.fc-dots i:nth-child(2){animation-delay:.15s}.fc-dots i:nth-child(3){animation-delay:.3s}' +
    '@keyframes fcd{0%,60%,100%{opacity:.3;transform:none}30%{opacity:1;transform:translateY(-3px)}}' +
    '.fc-who{display:grid;grid-template-columns:1fr 1.3fr;gap:8px;padding:0 14px 8px}' +
    '.fc-who input,.fc-row textarea{width:100%;box-sizing:border-box;border:1px solid rgba(23,32,26,.18);border-radius:12px;background:#fff;color:#17201a;font:17px/1.35 Onest,system-ui,sans-serif;padding:13px 14px}' +
    '.fc-who input:focus,.fc-row textarea:focus{outline:2px solid #f0a868;outline-offset:0;border-color:transparent}' +
    '.fc-row{display:flex;gap:8px;align-items:flex-end;padding:0 14px 8px}.fc-row textarea{resize:none;height:54px;max-height:260px}' +
    '.fc-send,.fc-mic{flex:none;width:54px;height:54px;border:0;border-radius:12px;cursor:pointer;display:grid;place-items:center}' +
    '.fc-send{background:#f0a868;color:#17201a}.fc-send:disabled{opacity:.5;cursor:default}.fc-mic{background:#ebe7d3;color:#17201a}.fc-mic.on{background:#e2574c;color:#fff}' +
    '.fc-st{padding:0 14px 6px;font:14px/1.35 Onest,system-ui,sans-serif;color:#4b5a52}.fc-st:empty{display:none}' +
    '.fc-who label{position:relative;display:block}.fc-who input{padding-right:52px}.fc-wm{position:absolute;right:6px;top:50%;transform:translateY(-50%);width:38px;height:38px;border:0;border-radius:10px;background:#ebe7d3;color:#17201a;cursor:pointer;display:grid;place-items:center}.fc-wm.on{background:#e2574c;color:#fff}' +
    '.fc-obr{display:block;margin-top:8px;border-radius:12px;overflow:hidden;background:#ebe7d3;color:#17201a;text-decoration:none;font-size:13px}.fc-obr img{display:block;width:100%;height:auto}.fc-obr span{display:block;padding:7px 10px}.fc-panel a.fc-obr,.fc-panel a.fc-zak{text-decoration:none!important;border:0}.fc-zak{display:table;margin-top:10px;padding:9px 14px;border-radius:999px;background:#f2a35e;color:#17201a;font-weight:600;text-decoration:none}' +
    '.fc-clip{flex:none;width:44px;height:44px;border:0;border-radius:12px;cursor:pointer;display:grid;place-items:center;background:#ebe7d3;color:#17201a}.fc-clip:focus-visible{outline:2px solid #f0a868;outline-offset:2px}' +
    '.fc-prev{display:none;align-items:center;gap:10px;padding:0 14px 8px;font-size:13px;color:#5c6958}.fc-prev.on{display:flex}.fc-prev img{width:44px;height:44px;border-radius:10px;object-fit:cover}.fc-prev button{margin-left:auto;border:0;background:none;color:inherit;font:inherit;text-decoration:underline;cursor:pointer;padding:6px}' +
    '.fc-m img{display:block;max-width:100%;max-height:180px;border-radius:10px;margin-bottom:6px}' +
    '.fc-note{padding:0 16px 12px;font-size:11.5px;color:#5c6958}.fc-note a{color:inherit}' +
    '.fc-sr{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}' +
    '.fc-wide .fc-panel{width:min(1040px,calc(100vw - 40px));height:calc(100dvh - 40px)}.fc-big,.fc-clr{width:34px;height:34px;border:0;border-radius:10px;background:transparent;color:inherit;font-size:18px;line-height:1;cursor:pointer;flex:none}.fc-big:hover,.fc-clr:hover{background:rgba(255,251,238,.12)}.fc-head>div:nth-child(2){margin-right:auto}.fc-head .fc-x{margin-left:0}.fc-m{position:relative}.fc-del{position:absolute;top:-9px;right:-9px;width:26px;height:26px;padding:0;border-radius:50%;border:1px solid rgba(23,32,26,.2);background:#fffbee;color:#17201a;font-size:15px;line-height:1;cursor:pointer;opacity:0;transition:opacity .15s}.fc-m:hover .fc-del,.fc-del:focus-visible{opacity:1}@media (hover:none){.fc-del{opacity:.8}}@media (max-width:700px){.fc-big{display:none}}' +
    '@media (max-width:700px){body.has-bot .fc-pill{right:116px;bottom:26px;padding:10px 14px 10px 12px;font-size:13px}.fc-panel{right:12px;bottom:12px;width:calc(100vw - 24px);height:calc(100dvh - 24px)}}' +
    '@media (prefers-reduced-motion:reduce){.fc-pill i,.fc-dots i{animation:none}.fc-panel,.fc-pill{transition:none}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);

  var root = document.createElement('div');
  root.innerHTML =
    '<button class="fc-pill" type="button" aria-haspopup="dialog" aria-controls="fc-panel"><i aria-hidden="true"></i>' + L.pill + '</button>' +
    '<div class="fc-panel" id="fc-panel" role="dialog" aria-label="' + L.dlg + '" aria-hidden="true">' +
    '<div class="fc-head"><div class="fc-ava" aria-hidden="true"></div><div><b>' + (EN ? 'Foma' : 'Фома') + '</b><span>' + L.sub + '</span></div><button class="fc-clr" type="button" aria-label="' + (EN ? 'Clear chat' : 'Очистить чат') + '" title="' + (EN ? 'Clear chat on this device' : 'Очистить чат на этом устройстве') + '">&#128465;</button><button class="fc-big" type="button" aria-label="' + (EN ? 'Wider' : 'Шире') + '" title="' + (EN ? 'Wider window' : 'Сделать окно шире') + '">&#10530;</button><button class="fc-x" type="button" aria-label="' + L.close + '">×</button></div>' +
    '<div class="fc-list" aria-live="polite"></div>' +
    '<div class="fc-who"><label><span class="fc-sr">Ваше имя</span><input name="imya" maxlength="60" autocomplete="given-name" placeholder="' + L.name + '"></label><label><span class="fc-sr">Телефон или ник в Telegram</span><input name="kontakt" maxlength="160" autocomplete="off" placeholder="' + L.contact + '"></label></div>' +
    '<div class="fc-prev"><img alt=""><span>' + L.photo + '</span><button type="button">' + L.remove + '</button></div>' +
    '<form class="fc-row"><label style="flex:1"><span class="fc-sr">Сообщение</span><textarea name="t" maxlength="1200" placeholder="' + L.msg + '" rows="1"></textarea></label><button class="fc-clip" type="button" aria-label="' + L.clip + '"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.5l-8.5 8.5a5.5 5.5 0 0 1-7.8-7.8l9-9a3.7 3.7 0 0 1 5.2 5.2l-9 9a1.8 1.8 0 0 1-2.6-2.6l8.3-8.3"/></svg></button><input class="fc-file fc-sr" type="file" accept="image/*" tabindex="-1" aria-hidden="true"><button class="fc-mic" type="button" aria-label="' + L.mic + '" hidden><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg></button><button class="fc-send" type="submit" aria-label="' + L.send + '"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></button></form>' +
    '<div class="fc-note">' + L.note + '</div>' +
    '</div>';
  document.body.appendChild(root);
  var $ = function (s) { return root.querySelector(s); };
  var pill = $('.fc-pill'), panel = $('.fc-panel'), list = $('.fc-list'), form = $('.fc-row'), ta = form.elements.t, send = $('.fc-send'), mic = $('.fc-mic'), whoBox = $('.fc-who');
  var iN = whoBox.querySelector('[name=imya]'), iK = whoBox.querySelector('[name=kontakt]');
  iN.value = who.imya; iK.value = who.kontakt;

  var foto = '', prev = $('.fc-prev'), fileIn = $('.fc-file');
  $('.fc-clip').addEventListener('click', function () { fileIn.click(); });
  prev.querySelector('button').addEventListener('click', function () { foto = ''; prev.classList.remove('on'); fileIn.value = ''; });
  fileIn.addEventListener('change', function () {
    var f = fileIn.files && fileIn.files[0]; if (!f) return;
    if (!/^image\//.test(f.type)) { add('f', L.onlyimg, false); fileIn.value = ''; return; }
    var u = URL.createObjectURL(f), im = new Image();
    im.onload = function () {
      var q = 0.82, m = 1280, out = '';
      for (var k = 0; k < 4; k++) {
        var r = Math.min(1, m / Math.max(im.width, im.height)), c = document.createElement('canvas');
        c.width = Math.max(1, Math.round(im.width * r)); c.height = Math.max(1, Math.round(im.height * r));
        var x = c.getContext('2d'); x.fillStyle = '#fff'; x.fillRect(0, 0, c.width, c.height); x.drawImage(im, 0, 0, c.width, c.height);
        out = c.toDataURL('image/jpeg', q); if (out.length < 700000) break; m = Math.round(m * 0.75); q -= 0.08;
      }
      URL.revokeObjectURL(u);
      if (out.length >= 900000 || out.indexOf('data:image/jpeg') !== 0) { add('f', L.bad, false); return; }
      foto = out; prev.querySelector('img').src = out; prev.classList.add('on'); ta.focus({ preventScroll: true });
    };
    im.onerror = function () { URL.revokeObjectURL(u); add('f', L.nofile, false); };
    im.src = u;
  });
  function esc(s) { return String(s).replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }
  var OBR = { bot: ['ex-bot', 'Бот мастерской', 'Workshop bot'], n8n: ['ex-n8n', 'Заявка с сайта → таблица → Telegram', 'Site request → sheet → Telegram'], sverka: ['ex-sverka', 'Сверка выписки банка с 1С', 'Bank statement reconciliation'], skan: ['ex-skan', 'Скан счёта → Excel', 'Scanned invoice → Excel'], shema: ['ex-shema', 'Фото схемы → чистая блок-схема', 'Photo of a diagram → clean flowchart'], '3d': ['ex-3d', 'Кронштейн по чертежу', 'Bracket from a drawing'], pomoshnik: ['ex-pomoshnik', 'ИИ-помощник', 'AI assistant'], sait: ['ex-sait', 'Сайт мастерской', 'Workshop website'] };
  function html(s) {
    var h = esc(s).replace(/(https?:\/\/[^\s<]+[^\s<.,;:!?)])/g, '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');
    h = h.replace(/\s*\[obrazec:([a-z0-9]+)\]/g, function (m, k) { var o = OBR[k]; if (!o) return ''; var u = '/assets/img/' + o[0] + '.webp', c = EN ? o[2] : o[1]; return '<a class="fc-obr" href="' + u + '" target="_blank" rel="noopener"><img src="' + u + '" alt="' + c + '" loading="lazy"><span>' + (EN ? 'Sample: ' : 'Образец: ') + c + '</span></a>'; });
    h = h.replace(/\s*\[zakaz\]/g, EN ? '' : '<a class="fc-zak" href="/oplata.html">Оформить заказ</a>');
    return h;
  }
  function add(r, t, keep, o) { var d = document.createElement('div'); d.className = 'fc-m ' + r; d.innerHTML = html(t); list.appendChild(d); list.scrollTop = list.scrollHeight; if (keep !== false) { o = { r: r, t: t }; log.push(o); log = log.slice(-40); set('fc_log', JSON.stringify(log)); } if (o) { var x = document.createElement('button'); x.type = 'button'; x.className = 'fc-del'; x.textContent = '×'; x.title = EN ? 'Remove from this window' : 'Убрать из окна (мастеру уже передано)'; x.setAttribute('aria-label', x.title); x.addEventListener('click', function () { var i = log.indexOf(o); if (i >= 0) { log.splice(i, 1); set('fc_log', JSON.stringify(log)); } d.remove(); }); d.appendChild(x); } return d; } /* VITRINA5_V1 */
  var HELLO = L.hello;
  function render() { list.innerHTML = ''; add('f', HELLO, false); log.forEach(function (m) { add(m.r, m.t, false, m); }); }
  var opened = false, busy = false;
  function open(prefill) {
    if (!opened) { render(); opened = true; }
    document.documentElement.classList.add('fc-open'); panel.setAttribute('aria-hidden', 'false');
    if (prefill && !ta.value) ta.value = prefill;
    setTimeout(function () { (iN.value ? ta : iN).focus({ preventScroll: true }); }, 60);
  }
  function close() { document.documentElement.classList.remove('fc-open'); panel.setAttribute('aria-hidden', 'true'); pill.focus({ preventScroll: true }); }
  pill.addEventListener('click', function () { open(); });
  $('.fc-x').addEventListener('click', close);
  try { if (localStorage.getItem('fc_wide')) document.documentElement.classList.add('fc-wide'); } catch (e) {}
  $('.fc-big').addEventListener('click', function () { var w = document.documentElement.classList.toggle('fc-wide'); try { localStorage.setItem('fc_wide', w ? '1' : ''); } catch (e) {} });
  $('.fc-clr').addEventListener('click', function () { if (!confirm(EN ? 'Clear this chat window? The master has already received your messages.' : 'Очистить окно чата? Мастеру сообщения уже переданы.')) return; log = []; set('fc_log', '[]'); render(); });
  setInterval(function () { if (ta.scrollHeight > ta.clientHeight + 2 && ta.clientHeight < 260) ta.style.height = Math.min(260, ta.scrollHeight) + 'px'; }, 400);
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && document.documentElement.classList.contains('fc-open')) close(); });
  ta.addEventListener('input', function () { ta.style.height = '54px'; ta.style.height = Math.min(260, ta.scrollHeight) + 'px'; });
  ta.addEventListener('keydown', function (e) { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); form.requestSubmit ? form.requestSubmit() : form.dispatchEvent(new Event('submit', { cancelable: true })); } });

  form.addEventListener('submit', function (e) {
    e.preventDefault();
    var t = ta.value.trim(); if ((!t && !foto) || busy) { if (!busy) ta.focus(); return; }
    var ft = foto; foto = ''; prev.classList.remove('on'); fileIn.value = '';
    who.imya = iN.value.trim(); who.kontakt = iK.value.trim(); set('fc_imya', who.imya); set('fc_kontakt', who.kontakt);
    if (who.imya && who.kontakt) whoBox.style.display = 'none';
    var um = add('u', t || L.ph, true); if (ft) { var pi = document.createElement('img'); pi.src = ft; pi.alt = 'Приложенное фото'; um.insertBefore(pi, um.firstChild); list.scrollTop = list.scrollHeight; }
    ta.value = ''; ta.style.height = '44px'; busy = true; send.disabled = true;
    var wait = document.createElement('div'); wait.className = 'fc-m f'; wait.innerHTML = '<span class="fc-dots" aria-label="Фома печатает"><i></i><i></i><i></i></span>'; list.appendChild(wait); list.scrollTop = list.scrollHeight;
    var ctl = window.AbortController ? new AbortController() : null, timer = setTimeout(function () { if (ctl) ctl.abort(); }, 45000);
    fetch(URL_, { method: 'POST', headers: { 'Content-Type': 'application/json' }, signal: ctl ? ctl.signal : undefined, body: JSON.stringify({ sid: sid, imya: who.imya, kontakt: who.kontakt, tekst: t, foto: ft, yazyk: EN ? 'en' : 'ru', stranitsa: location.pathname.slice(0, 100) }) })
      .then(function (r) { if (!r.ok) throw new Error(r.status); return r.json(); })
      .then(function (j) {
        if (!j || typeof j.reply !== 'string' || !j.reply.trim()) throw new Error('empty reply');
        wait.remove(); add('f', j.reply);
        try { if (window.__botSay) window.__botSay('happy'); } catch (e) { /* animation cannot break the chat */ }
      })
      .catch(function () { wait.remove(); add('f', L.fail, false); })
      .then(function () { clearTimeout(timer); busy = false; send.disabled = false; ta.focus({ preventScroll: true }); });
  });

  // Голос (слово Капитана 25.11): текст виден по ходу речи, остаётся в поле, можно поправить и отправить самому.
  var STT = 'https://n8n.gumanetriya.ru/webhook/{{N8N_WEBHOOK_GOLOS}}';
  var AC = window.AudioContext || window.webkitAudioContext;
  var vrun = null;
  var V = EN
    ? { conn: 'Connecting the microphone. If the browser asks, press Allow.', listen: 'Listening', hint: 'The text appears as you speak. Press the microphone again to stop, then edit the text and send.', rec: 'Recognising…', done: 'Done. Edit the text if needed and press send.', quiet: 'Almost no sound on the input. The wrong input may be selected (Stereo Mix instead of Microphone): pick the microphone in the sound settings, or type the text.', empty: 'Could not make out the words. Speak a little louder and closer.', fail: 'Recognition is unavailable now. Please type the text.', short: 'Too short. Press the microphone, say a phrase, press it again.', denied: 'The browser blocked the microphone. Allow it for this site and try again.', none: 'No microphone found.', stop: 'Stop recording', say: 'Dictate' }
    : { conn: 'Подключаю микрофон. Если браузер спросит, нажмите «Разрешить».', listen: 'Слушаю', hint: 'Текст появляется по ходу речи. Нажмите на микрофон ещё раз, чтобы остановить, потом поправьте текст и отправьте.', rec: 'Распознаю…', done: 'Готово. Поправьте текст, если нужно, и нажмите «отправить».', quiet: 'На входе почти нет звука. Скорее всего выбран не тот микрофон («Стерео микшер» вместо «Микрофон»): выберите микрофон в настройках звука Windows или браузера, либо напишите текстом.', empty: 'Слов не разобрать. Скажите чуть громче и ближе к микрофону.', fail: 'Распознавание сейчас недоступно. Напишите текстом.', short: 'Слишком коротко. Нажмите на микрофон, скажите фразу и нажмите ещё раз.', denied: 'Браузер не дал микрофон. Разрешите его для этого сайта и повторите.', none: 'Микрофон не найден.', stop: 'Остановить запись', say: 'Сказать голосом' };
  var stBox = document.createElement('div'); stBox.className = 'fc-st'; stBox.setAttribute('aria-live', 'polite');
  form.parentNode.insertBefore(stBox, form);
  function vSay(t) { stBox.textContent = t || ''; }
  function vSpeech(blocks, rate) {
    var n = 0, i, j, k; for (i = 0; i < blocks.length; i++) n += blocks[i].length;
    var clean = new Float32Array(n), pole = Math.exp(-2 * Math.PI * 70 / rate), old = 0, f = 0, p = 0, energy = 0, peak = 0;
    for (i = 0; i < blocks.length; i++) for (j = 0; j < blocks[i].length; j++) { var x = blocks[i][j]; f = pole * (f + x - old); old = x; clean[p++] = f; energy += f * f; if (Math.abs(f) > peak) peak = Math.abs(f); }
    var ratio = rate / 16000, out = new Float32Array(Math.floor(n / ratio)), rms = Math.sqrt(energy / Math.max(1, n));
    var gain = Math.min(15, 0.9 / Math.max(0.00001, peak), Math.max(1, 0.045 / Math.max(rms, 0.00001)));
    for (k = 0; k < out.length; k++) { var lo = k * ratio, hi = lo + ratio, sum = 0; for (j = Math.floor(lo); j < Math.ceil(hi) && j < n; j++) sum += clean[j] * Math.max(0, Math.min(hi, j + 1) - Math.max(lo, j)); out[k] = Math.max(-0.95, Math.min(0.95, sum * gain / ratio)); }
    return { out: out, rms: rms, peak: peak };
  }
  function vWavB64(f32) {
    var bytes = new Uint8Array(44 + f32.length * 2), v = new DataView(bytes.buffer), i;
    function lab(o, s) { for (var q = 0; q < s.length; q++) v.setUint8(o + q, s.charCodeAt(q)); }
    lab(0, 'RIFF'); v.setUint32(4, 36 + f32.length * 2, true); lab(8, 'WAVE'); lab(12, 'fmt '); v.setUint32(16, 16, true); v.setUint16(20, 1, true); v.setUint16(22, 1, true);
    v.setUint32(24, 16000, true); v.setUint32(28, 32000, true); v.setUint16(32, 2, true); v.setUint16(34, 16, true); lab(36, 'data'); v.setUint32(40, f32.length * 2, true);
    for (i = 0; i < f32.length; i++) { var s = Math.max(-1, Math.min(1, f32[i])); v.setInt16(44 + i * 2, Math.round(s * (s < 0 ? 32768 : 32767)), true); }
    var bin = '', step = 0x8000; for (i = 0; i < bytes.length; i += step) bin += String.fromCharCode.apply(null, bytes.subarray(i, i + step));
    return btoa(bin);
  }
  function vAsk(blocks, rate) {
    var s = vSpeech(blocks, rate);
    if (s.peak < 0.0004 || s.rms < 0.00012) return Promise.resolve({ quiet: true });
    return fetch(STT, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ a: vWavB64(s.out), l: EN ? 'en' : 'ru' }) })
      .then(function (r) { if (!r.ok) throw new Error('http'); return r.json(); })
      .then(function (j) { return { text: String(j.tekst || '').trim(), osh: j.osh || '' }; });
  }
  var vMic = '';
  var BAD = /(стерео\s*микшер|stereo\s*mix|микшер|what\s*u\s*hear|loopback|monitor of|виртуальн|virtual|voicemeeter|vb-audio|cable output)/i;
  var GOOD = /(микрофон|microphone|\bmic\b|гарнитур|headset|headphone|webcam|камер)/i;
  function vOpenMic() {
    var md = navigator.mediaDevices, base = { channelCount: 1 };
    return md.getUserMedia({ audio: base }).then(function (st) {
      var lab = ''; try { lab = st.getAudioTracks()[0].label || ''; } catch (e) {}
      vMic = lab;
      if (!BAD.test(lab) || !md.enumerateDevices) return st;
      return md.enumerateDevices().then(function (all) {
        var list = all.filter(function (d) { return d.kind === 'audioinput' && d.deviceId && d.deviceId !== 'default' && d.deviceId !== 'communications' && !BAD.test(d.label); });
        var best = null, i; for (i = 0; i < list.length; i++) if (GOOD.test(list[i].label)) { best = list[i]; break; }
        best = best || list[0];
        if (!best) return st;
        return md.getUserMedia({ audio: { channelCount: 1, deviceId: { exact: best.deviceId } } }).then(function (st2) {
          st.getTracks().forEach(function (t) { t.stop(); }); vMic = best.label || vMic; return st2;
        }, function () { return st; });
      }, function () { return st; });
    });
  }
  function voice(target, btn) {
    if (vrun) { if (vrun.btn === btn && vrun.stop) vrun.stop(); return; }
    if (!navigator.mediaDevices || !AC) { vSay(V.none); return; }
    var run = { btn: btn, stream: null, ctx: null, src: null, proc: null, mute: null, tick: null, stop: null }, blocks = [], total = 0, level = 0, rate = 48000, busy = false, seq = 0, applied = 0, t0 = 0;
    var base = target.value ? target.value.replace(/ +$/, '') + ' ' : '';
    vrun = run; vSay(V.conn); btn.classList.add('on'); btn.setAttribute('aria-label', V.stop);
    function release() {
      clearInterval(run.tick);
      if (run.proc) run.proc.onaudioprocess = null;
      [run.src, run.proc, run.mute].forEach(function (n) { if (n) { try { n.disconnect(); } catch (e) {} } });
      if (run.stream) run.stream.getTracks().forEach(function (t) { t.stop(); });
      if (run.ctx) { try { run.ctx.close(); } catch (e) {} }
      btn.classList.remove('on'); btn.setAttribute('aria-label', V.say);
    }
    function show(t) { target.value = base + t; target.dispatchEvent(new Event('input', { bubbles: true })); }
    function bar() { var w = Math.round(Math.min(1, level) * 100); return ' ' + '\u2588'.repeat(Math.max(1, Math.round(w / 12))); }
    run.ctx = new AC(); var ready = run.ctx.resume();
    vOpenMic().then(function (st) {
      run.stream = st; return Promise.race([ready, new Promise(function (_, no) { setTimeout(function () { no({ name: 'AudioStartTimeout' }); }, 8000); })]);
    }).then(function () {
      rate = run.ctx.sampleRate; run.src = run.ctx.createMediaStreamSource(run.stream); run.proc = run.ctx.createScriptProcessor(4096, 1, 1); run.mute = run.ctx.createGain(); run.mute.gain.value = 0;
      run.proc.onaudioprocess = function (ev) { var part = new Float32Array(ev.inputBuffer.getChannelData(0)); blocks.push(part); total += part.length; var e = 0; for (var i = 0; i < part.length; i++) e += part[i] * part[i]; level = Math.sqrt(e / part.length) * 12; };
      run.src.connect(run.proc); run.proc.connect(run.mute); run.mute.connect(run.ctx.destination);
      t0 = Date.now();
      run.stop = function () {
        run.stop = null; release(); vSay(V.rec);
        if (total < rate * 0.65) { vSay(V.short); vrun = null; return; }
        vAsk(blocks, rate).then(function (r) {
          if (r.quiet) vSay(V.quiet + (vMic ? ' [' + vMic + ']' : '')); else if (!r.text) vSay(r.osh || V.empty); else { applied = ++seq; show(r.text); target.focus(); vSay(V.done); }
        }).catch(function () { vSay(V.fail); }).then(function () { vrun = null; });
      };
      run.tick = setInterval(function () {
        if (!run.stop) return;
        var sec = Math.floor((Date.now() - t0) / 1000);
        vSay(V.listen + ' ' + (sec < 10 ? '0' : '') + sec + ' с' + bar() + (vMic ? ' [' + vMic + ']' : '') + '. ' + V.hint);
        if (sec >= 19) { run.stop(); return; }
        if (sec >= 3 && sec % 2 === 1 && !busy && total >= rate * 1.2) {
          busy = true; var mine = ++seq;
          vAsk(blocks, rate).then(function (r) { if (r.text && mine > applied && run.stop) { applied = mine; show(r.text); } }).catch(function () {}).then(function () { busy = false; });
        }
      }, 500);
    }).catch(function (e) {
      release(); vrun = null; var n = e && e.name;
      vSay(n === 'NotAllowedError' || n === 'PermissionDeniedError' ? V.denied : n === 'NotFoundError' || n === 'DevicesNotFoundError' ? V.none : V.fail);
    });
  }
  if (navigator.mediaDevices && navigator.mediaDevices.getUserMedia && AC) {
    mic.hidden = false;
    mic.addEventListener('click', function () { voice(ta, mic); });
    [iN, iK].forEach(function (inp) {
      var b = document.createElement('button'); b.type = 'button'; b.className = 'fc-wm'; b.setAttribute('aria-label', V.say);
      b.innerHTML = '<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>';
      inp.parentNode.appendChild(b); b.addEventListener('click', function () { voice(inp, b); });
    });
  }
  document.addEventListener('click', function (e) { var el = e.target.closest && e.target.closest('[data-chat]'); if (el) { e.preventDefault(); open(); } });
  window.FomaChat = { open: open, close: close, isOpen: function () { return document.documentElement.classList.contains('fc-open'); } };
  function openFromLink() { if (location.hash === '#chat-foma') open(); }
  window.addEventListener('hashchange', openFromLink);
  openFromLink();
})();
