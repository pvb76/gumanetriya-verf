/* Корзина в шапке сайта (слово Капитана 25.11): всегда на виду, с числом. Витрина (magazin.js) сама рисует свою плашку. */
(function () {
  try {
    var st = document.createElement('style');
    st.textContent = '.hdr-cart svg{width:20px;height:20px}.hdr-cart .hc-n{min-width:22px;height:22px;border-radius:11px;background:#e2574c;color:#fff;font:700 12.5px/22px system-ui,sans-serif;text-align:center;padding:0 6px;box-sizing:border-box;margin-left:2px}.hdr-cart .hc-n[hidden]{display:none}.hdr-cart.full{background:#6B1F2A;border-color:#6B1F2A}@media(max-width:520px){.hdr .btn.hdr-cart{display:inline-flex;align-items:center;padding:9px 11px}.hdr-cart span{display:none}.hdr-cart .hc-n{margin-left:4px}}';
    document.head.appendChild(st);
    var c = JSON.parse(localStorage.getItem('gum_cart') || 'null'), n = 0;
    if (c && Array.isArray(c.i) && c.i.length) { if (Date.now() - c.t > 7 * 864e5) localStorage.removeItem('gum_cart'); else n = c.i.length; }
    [].forEach.call(document.querySelectorAll('.hdr-cart'), function (el) {
      var b = el.querySelector('.hc-n');
      if (n && b) { b.hidden = false; b.textContent = n; el.classList.add('full'); el.title = 'В корзине: ' + n; } else el.title = 'Корзина пуста';
    });
  } catch (e) {}
})();
