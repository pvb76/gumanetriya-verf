/* Дверь Гуманетрии: кто вошёл (шапка), подпись дома (подвал), привязка номера заказа. DVER_JS_V2 */
(function () {
  var css = '.dv-chip{display:inline-flex;align-items:center;gap:8px;min-height:44px;padding:6px 14px 6px 6px;border-radius:999px;text-decoration:none;font:600 14px/1.1 Onest,system-ui,sans-serif;white-space:nowrap;border:1.5px solid rgba(176,141,87,.55);background:rgba(255,251,238,.08);color:inherit;margin-right:8px}' +
    '.dv-chip i{width:30px;height:30px;border-radius:50%;display:grid;place-items:center;font:700 14px/1 Literata,serif;font-style:normal;background:#31442a;color:#f0a868;border:1.5px solid #b08d57}' +
    '.dv-chip small{display:block;font-weight:500;font-size:11.5px;opacity:.75;letter-spacing:.02em}' +
    '.hdr .dv-chip{background:#fffbee;color:#31442a}' +
    '.dv-sign{display:flex;flex-wrap:wrap;align-items:center;gap:10px 18px;margin:18px 0 0;padding:14px 0 0;border-top:1px solid rgba(127,127,100,.25);font:14px/1.45 Onest,system-ui,sans-serif;opacity:.92}' +
    '.dv-sign b{font-family:Literata,serif;letter-spacing:.04em}.dv-sign a{color:inherit;text-underline-offset:3px}' +
    '.nav .hdr-cart,.hdr .hdr-cart{background:#f0a868!important;color:#142019!important}' +
    '@media (max-width:700px){.dv-chip span{display:none}.dv-chip{padding:6px;margin-right:4px}}@media (max-width:430px){.hdr .lang{display:none!important}.hdr .brand b{font-size:15px;letter-spacing:.08em}}';
  var st = document.createElement('style'); st.textContent = css; document.head.appendChild(st);
  function esc(s) { return String(s || '').replace(/[&<>"]/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]; }); }

  fetch('/dver/ya', { credentials: 'same-origin' }).then(function (r) { return r.json(); }).then(function (j) {
    window.DVER = j;
    if (!j.ok) return;
    var cart = document.querySelector('.hdr-cart');
    if (cart && !document.querySelector('.dv-chip')) {
      var a = document.createElement('a'); a.className = 'dv-chip'; a.href = '/kabinet.html';
      a.title = 'Мой кабинет'; a.setAttribute('aria-label', 'Мой кабинет: ' + (j.name || ''));
      a.innerHTML = '<i aria-hidden="true">' + esc((j.name || '?').charAt(0).toUpperCase()) + '</i><span>' + esc(j.name) + '<small>' + esc(j.role_ru) + '</small></span>';
      cart.parentNode.insertBefore(a, cart);
    }
    // номер заказа из адреса (страница после оплаты, «Мой заказ») — к учётке
    var o = new URLSearchParams(location.search).get('o');
    if (o && j.kind === 'user' && (j.orders || []).indexOf(o) < 0) {
      fetch('/dver/zakaz', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ o: o }) });
    }
  }).catch(function () {});

  // подпись дома в подвале: кто хозяин
  function sign() {
    var ws = document.querySelectorAll('footer .wrap'); var f = ws.length ? ws[ws.length - 1] : document.querySelector('footer');
    if (!f || document.querySelector('.dv-sign')) return;
    var d = document.createElement('div'); d.className = 'dv-sign';
    d.innerHTML = '<span><b>Мастерская Гуманет</b></span><span>Хозяин дома — Капитан Владимир</span><span>Помощник — Фома</span><a href="/kabinet.html">Мой кабинет</a><a href="/dver/vyhod">Выйти</a>';
    f.appendChild(d);
  }
  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', sign); else sign();
})();
