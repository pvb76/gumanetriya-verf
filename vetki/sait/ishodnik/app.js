/* 3D-робот грузится после страницы (25.11): текст и кнопки доступны сразу. */
let THREE, RoundedBoxGeometry, RoomEnvironment;

const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
const canHover = matchMedia('(hover:hover)').matches;
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const clamp = (v, a, b) => Math.min(b, Math.max(a, v));

/* ---------- scroll: progress, nav, belt ---------- */
const progress = $('#progress'), nav = $('#nav'), belt = $('#belt');
const steps = $$('.step');
let ticking = false;
function onScroll() {
  if (ticking) return; ticking = true;
  requestAnimationFrame(() => {
    const y = scrollY, h = document.documentElement.scrollHeight - innerHeight;
    progress.style.transform = `scaleX(${h > 0 ? y / h : 0})`;
    nav.classList.toggle('is-stuck', y > 40);
    if (belt) {
      const r = belt.getBoundingClientRect();
      const p = clamp((innerHeight * 0.78 - r.top) / (r.height + innerHeight * 0.25), 0, 1);
      belt.style.setProperty('--p', p.toFixed(4));
      steps.forEach((s, i) => s.classList.toggle('is-on', p >= i / steps.length + 0.04));
    }
    ticking = false;
  });
}
addEventListener('scroll', onScroll, { passive: true });
addEventListener('resize', onScroll);
onScroll();

/* ---------- reveals ---------- */
const io = new IntersectionObserver((es) => es.forEach((e) => {
  if (e.isIntersecting) { e.target.classList.add('is-in'); io.unobserve(e.target); }
}), { threshold: 0.12, rootMargin: '0px 0px -6% 0px' });
$$('.rv').forEach((el, i) => { el.style.transitionDelay = `${(i % 4) * 70}ms`; io.observe(el); });

/* ---------- pointer: tilt, magnet, parallax, scene ---------- */
const ptr = { x: innerWidth / 2, y: innerHeight / 2, nx: 0, ny: 0 };
addEventListener('pointermove', (e) => {
  ptr.x = e.clientX; ptr.y = e.clientY; ptr.nx = e.clientX / innerWidth - 0.5; ptr.ny = e.clientY / innerHeight - 0.5;
  if (!reduce && canHover) $$('.par').forEach((el) => { const d = Number(el.dataset.d); el.style.transform = `translate3d(${(-ptr.nx * d).toFixed(1)}px,${(-ptr.ny * d).toFixed(1)}px,0)`; });
}, { passive: true });

if (!reduce && canHover) {
  $$('.tilt').forEach((c) => {
    c.addEventListener('pointermove', (e) => {
      const r = c.getBoundingClientRect();
      const px = (e.clientX - r.left) / r.width, py = (e.clientY - r.top) / r.height;
      c.style.setProperty('--mx', `${px * 100}%`); c.style.setProperty('--my', `${py * 100}%`);
      c.style.transform = `rotateX(${(0.5 - py) * 10}deg) rotateY(${(px - 0.5) * 12}deg) translateZ(8px)`;
    });
    c.addEventListener('pointerleave', () => { c.style.transform = ''; });
  });
  $$('.magnet').forEach((b) => {
    b.addEventListener('pointermove', (e) => {
      const r = b.getBoundingClientRect();
      b.style.transform = `translate(${(e.clientX - r.left - r.width / 2) * 0.22}px,${(e.clientY - r.top - r.height / 2) * 0.3}px)`;
    });
    b.addEventListener('pointerleave', () => { b.style.transform = ''; });
  });
  const frame = $('#frame');
  if (frame) {
    const sc = frame.parentElement;
    sc.addEventListener('pointermove', (e) => {
      const r = frame.getBoundingClientRect();
      const px = clamp((e.clientX - r.left) / r.width, 0, 1), py = clamp((e.clientY - r.top) / r.height, 0, 1);
      frame.style.setProperty('--ry', `${(px - 0.5) * 9}deg`); frame.style.setProperty('--rx', `${(0.5 - py) * 7}deg`);
      frame.style.setProperty('--gx', `${px * 100}%`); frame.style.setProperty('--gy', `${py * 100}%`);
    });
    sc.addEventListener('pointerleave', () => { frame.style.setProperty('--ry', '0deg'); frame.style.setProperty('--rx', '0deg'); });
  }
}

/* ---------- tabs ---------- */
const tabs = $$('[role="tab"]');
function pick(t) {
  tabs.forEach((x) => { const on = x === t; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; $('#' + x.getAttribute('aria-controls')).hidden = !on; });
}
tabs.forEach((t, i) => {
  t.addEventListener('click', () => pick(t));
  t.addEventListener('keydown', (e) => {
    if (e.key !== 'ArrowRight' && e.key !== 'ArrowLeft') return;
    const n = tabs[(i + (e.key === 'ArrowRight' ? 1 : tabs.length - 1)) % tabs.length]; n.focus(); pick(n);
  });
});

/* ================= РОБОТ-СПУТНИК ================= */
const bot = { ready: false, face: 'idle', text: '', faceUntil: 0, hopV: 0, hop: 0, spin: 0, spinV: 0, wave: 0, say() {} };

function buildBot() {
  const canvas = $('#bot');
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true, powerPreference: 'high-performance' });
  renderer.setPixelRatio(Math.min(devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
  const scene = new THREE.Scene();
  scene.environment = new THREE.PMREMGenerator(renderer).fromScene(new RoomEnvironment(), 0.04).texture;
  const FOV = 28, DIST = 12;
  const cam = new THREE.PerspectiveCamera(FOV, 1, 0.1, 60); cam.position.set(0, 0, DIST);
  const key = new THREE.DirectionalLight(0xffe2bd, 2.4); key.position.set(3, 5, 6);
  const rim = new THREE.DirectionalLight(0xbfe08a, 2.6); rim.position.set(-5, 2, -4);
  scene.add(key, rim, new THREE.HemisphereLight(0xf5f2e3, 0x26331c, 0.55));

  const M = (color, o = {}) => new THREE.MeshPhysicalMaterial({ color, roughness: 0.34, metalness: 0.04, clearcoat: 0.7, clearcoatRoughness: 0.25, envMapIntensity: 0.9, ...o });
  const shell = M(0xf4efdc), olive = M(0x7f9147, { roughness: 0.42 }), dark = M(0x161c12, { roughness: 0.18, clearcoat: 1 }), apricot = M(0xf0a868, { emissive: 0xf0a868, emissiveIntensity: 0.35 });
  const glow = new THREE.MeshBasicMaterial({ color: 0xffd6a8, toneMapped: false });

  const root = new THREE.Group(); scene.add(root);          // позиция и масштаб по слоту
  const body = new THREE.Group(); root.add(body);           // парение, поворот
  const mesh = (g, m, x = 0, y = 0, z = 0, p = body) => { const o = new THREE.Mesh(g, m); o.position.set(x, y, z); p.add(o); return o; };

  // корпус: мягкая «капля» со срезом
  const torso = mesh(new THREE.SphereGeometry(0.66, 48, 36), olive, 0, -0.42, 0); torso.scale.set(1, 1.08, 0.86);
  const bib = mesh(new THREE.SphereGeometry(0.5, 40, 28, 0, Math.PI * 2, 0, Math.PI * 0.52), shell, 0, -0.5, 0.2); bib.scale.set(0.86, 0.9, 0.62); bib.rotation.x = Math.PI * 0.5;
  mesh(new THREE.TorusGeometry(0.33, 0.07, 16, 48), dark, 0, 0.2, 0).rotation.x = Math.PI / 2;
  const heart = mesh(new THREE.SphereGeometry(0.075, 20, 16), glow, 0, -0.34, 0.58);

  // голова: скруглённый блок со стеклянным визором
  const head = new THREE.Group(); head.position.set(0, 0.78, 0); body.add(head);
  mesh(new RoundedBoxGeometry(1.42, 0.98, 1.02, 10, 0.36), shell, 0, 0, 0, head);
  mesh(new RoundedBoxGeometry(1.16, 0.62, 0.3, 8, 0.15), dark, 0, 0, 0.4, head);
  const fc = document.createElement('canvas'); fc.width = 512; fc.height = 256;
  const fx = fc.getContext('2d');
  const ftex = new THREE.CanvasTexture(fc); ftex.colorSpace = THREE.SRGBColorSpace; ftex.anisotropy = 4;
  mesh(new THREE.PlaneGeometry(1.02, 0.51), new THREE.MeshBasicMaterial({ map: ftex, transparent: true, toneMapped: false }), 0, 0, 0.556, head);
  for (const sx of [-1, 1]) {
    const ear = mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.14, 40), apricot, sx * 0.76, 0, 0, head); ear.rotation.z = Math.PI / 2;
    const cap = mesh(new THREE.CylinderGeometry(0.11, 0.11, 0.16, 32), dark, sx * 0.78, 0, 0, head); cap.rotation.z = Math.PI / 2;
  }
  const ant = new THREE.Group(); ant.position.set(0.34, 0.47, 0); head.add(ant);
  mesh(new THREE.CylinderGeometry(0.022, 0.022, 0.34, 12), dark, 0, 0.17, 0, ant);
  const tip = mesh(new THREE.SphereGeometry(0.07, 20, 16), glow, 0, 0.37, 0, ant);

  // руки: парящие капсулы
  const arms = [-1, 1].map((sx) => {
    const g = new THREE.Group(); g.position.set(sx * 0.86, -0.12, 0.04); body.add(g);
    mesh(new THREE.CapsuleGeometry(0.115, 0.34, 8, 20), olive, 0, -0.28, 0, g);
    mesh(new THREE.SphereGeometry(0.15, 28, 20), shell, 0, -0.58, 0.02, g);
    g.userData.sx = sx; return g;
  });

  // подвес: светящееся кольцо и мягкая тень
  const ring = mesh(new THREE.TorusGeometry(0.4, 0.05, 16, 64), glow, 0, -1.24, 0); ring.rotation.x = Math.PI / 2;
  const ring2 = mesh(new THREE.TorusGeometry(0.26, 0.025, 12, 48), glow, 0, -1.38, 0); ring2.rotation.x = Math.PI / 2;
  const sc = document.createElement('canvas'); sc.width = sc.height = 128; const sx2 = sc.getContext('2d');
  const gr = sx2.createRadialGradient(64, 64, 4, 64, 64, 62); gr.addColorStop(0, 'rgba(0,0,0,.55)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); sx2.fillStyle = gr; sx2.fillRect(0, 0, 128, 128);
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(2.2, 0.62), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(sc), transparent: true, depthWrite: false }));
  shadow.position.set(0, -1.72, 0); root.add(shadow);

  /* --- лицо на визоре --- */
  const EYE = '#eaffc4';
  let blink = 0, nextBlink = 2.5, lastKey = '';
  function drawFace(t) {
    const now = performance.now();
    let mode = bot.face; if (bot.faceUntil && now > bot.faceUntil) { bot.faceUntil = 0; bot.face = mode = 'idle'; }
    const lx = clamp(bot.lookX, -1, 1), ly = clamp(bot.lookY, -1, 1);
    const k = `${mode}|${bot.text}|${lx.toFixed(2)}|${ly.toFixed(2)}|${blink.toFixed(2)}`;
    if (k === lastKey) return; lastKey = k;
    fx.clearRect(0, 0, 512, 256);
    fx.shadowColor = 'rgba(214,255,150,.9)'; fx.shadowBlur = 26; fx.fillStyle = EYE; fx.strokeStyle = EYE; fx.lineCap = 'round';
    if (mode === 'price' && bot.text) {
      fx.shadowBlur = 18; fx.textAlign = 'center'; fx.textBaseline = 'middle';
      let size = 124; fx.font = `800 ${size}px Onest, system-ui, sans-serif`;
      while (fx.measureText(bot.text).width > 452 && size > 40) { size -= 6; fx.font = `800 ${size}px Onest, system-ui, sans-serif`; }
      fx.fillText(bot.text, 256, 136); return;
    }
    const ox = lx * 34, oy = ly * 20, cy = 128 + oy;
    for (const s of [-1, 1]) {
      const cx = 256 + s * 104 + ox;
      if (mode === 'happy') { fx.lineWidth = 26; fx.beginPath(); fx.arc(cx, cy + 26, 46, Math.PI * 1.14, Math.PI * 1.86); fx.stroke(); }
      else if (mode === 'wow') { fx.beginPath(); fx.arc(cx, cy, 44, 0, Math.PI * 2); fx.fill(); }
      else if (mode === 'wink' && s === 1) { fx.lineWidth = 24; fx.beginPath(); fx.moveTo(cx - 44, cy); fx.lineTo(cx + 44, cy); fx.stroke(); }
      else { const h = Math.max(10, 104 * (1 - blink)); fx.beginPath(); fx.roundRect(cx - 34, cy - h / 2, 68, h, 30); fx.fill(); }
    }
  }
  bot.lookX = 0; bot.lookY = 0;
  bot.say = (face, text = '', ms = 0) => { bot.face = face; bot.text = text; bot.faceUntil = ms ? performance.now() + ms : 0; };

  /* --- слоты и размеры --- */
  const slots = $$('[data-slot]');
  let W = 1, H = 1, visH = 1, visW = 1;
  function resize() {
    W = innerWidth; H = canvas.clientHeight || innerHeight;
    renderer.setSize(W, H, false); cam.aspect = W / H; cam.updateProjectionMatrix();
    visH = 2 * DIST * Math.tan(THREE.MathUtils.degToRad(FOV / 2)); visW = visH * cam.aspect;
  }
  addEventListener('resize', resize); resize();
  const MODEL_H = 3.25;                       // высота фигуры в единицах сцены (с кольцом и антенной)
  const cur = { x: 0, y: 0, s: 0.001 }, scr = { x: W * 0.7, y: H * 0.5, h: 300 };
  function target() {
    let best = null, bestV = 0;
    for (const el of slots) {
      const r = el.getBoundingClientRect(); if (!r.width) continue;
      const v = Math.max(0, Math.min(r.bottom, H) - Math.max(r.top, 0)) / r.height;
      if (v > bestV) { bestV = v; best = r; }
    }
    if (best && bestV > 0.42) { const hh = Math.min(best.height, best.width * 1.25) * 0.88; return { cx: best.left + best.width / 2, cy: best.top + best.height / 2 + hh * 0.05, h: hh, docked: false }; }
    const h = W < 700 ? 104 : 168;
    return { cx: W - h * 0.5 - (W < 700 ? 6 : 26), cy: H - h * 0.56 - (W < 700 ? 8 : 20), h, docked: true };
  }

  /* --- взаимодействие --- */
  const stage = $('#stage'); let drag = false, lastX = 0;
  if (stage) {
    stage.addEventListener('pointerdown', (e) => { drag = true; lastX = e.clientX; });
    addEventListener('pointermove', (e) => { if (!drag) return; bot.spinV = (e.clientX - lastX) * 0.012; lastX = e.clientX; bot.spin += bot.spinV; });
    addEventListener('pointerup', () => { drag = false; });
  }
  addEventListener('pointerdown', (e) => {
    const d = Math.hypot(e.clientX - scr.x, e.clientY - scr.y);
    if (d < scr.h * 0.45 && !e.target.closest('.fc-panel')) { bot.hopV = 0.16; bot.wave = 1; bot.say(['happy', 'wink', 'wow'][Math.floor(Math.random() * 3)], '', 1400); if (docked && window.FomaChat) window.FomaChat.open(); }
  });

  /* --- цикл --- */
  let t = 0, last = performance.now(), docked = false, visible = !document.hidden;
  document.addEventListener('visibilitychange', () => { visible = !document.hidden; last = performance.now(); });
  function frame(now) {
    requestAnimationFrame(frame);
    if (!visible) return;
    const dt = Math.min(0.05, (now - last) / 1000); last = now; t += dt;
    const tg = target(); docked = tg.docked;
    const k = reduce ? 1 : 1 - Math.pow(0.0012, dt);
    scr.x += (tg.cx - scr.x) * k; scr.y += (tg.cy - scr.y) * k; scr.h += (tg.h - scr.h) * k;
    const s = (scr.h / H) * visH / MODEL_H;
    cur.x = (scr.x / W - 0.5) * visW; cur.y = -(scr.y / H - 0.5) * visH; cur.s = s;
    root.position.set(cur.x, cur.y + 0.12 * s, 0); root.scale.setScalar(s);

    // взгляд за курсором
    const dx = clamp((ptr.x - scr.x) / (W * 0.5), -1, 1), dy = clamp((ptr.y - (scr.y - scr.h * 0.2)) / (H * 0.5), -1, 1);
    bot.lookX += (dx - bot.lookX) * 0.12; bot.lookY += (dy - bot.lookY) * 0.12;
    head.rotation.y = bot.lookX * 0.3; head.rotation.x = bot.lookY * 0.3; head.rotation.z = -bot.lookX * 0.06;
    if (!drag) { bot.spin += bot.spinV; bot.spinV *= 0.94; bot.spin *= 0.985; }
    body.rotation.y = bot.spin + bot.lookX * 0.14;
    body.rotation.z = Math.sin(t * 1.1) * 0.03 - bot.lookX * 0.04;

    // парение, прыжок
    bot.hopV += (0 - bot.hop) * 0.14; bot.hopV *= 0.8; bot.hop += bot.hopV;
    const bob = reduce ? 0 : Math.sin(t * 1.7) * 0.06;
    body.position.y = bob + Math.max(-0.05, bot.hop);
    shadow.scale.setScalar(1 - clamp(bob + bot.hop, -0.2, 0.6) * 0.5); shadow.material.opacity = docked ? 0 : 0.8;
    ring.scale.setScalar(1 + Math.sin(t * 4) * 0.05); ring2.scale.setScalar(1 + Math.sin(t * 4 + 1.4) * 0.09);
    ring2.position.y = -1.38 - (Math.sin(t * 4) + 1) * 0.03;
    tip.scale.setScalar(1 + Math.sin(t * 3) * 0.18); ant.rotation.z = Math.sin(t * 2.2) * 0.12 - bot.spinV * 2;
    heart.scale.setScalar(1 + Math.max(0, Math.sin(t * 2.6)) * 0.35);

    // руки
    bot.wave *= 0.972;
    arms.forEach((g) => {
      const sx = g.userData.sx;
      const base = sx * (0.16 + Math.sin(t * 1.7 + sx) * 0.05);
      const wav = sx === 1 ? bot.wave * (2.3 + Math.sin(t * 16) * 0.45) : 0;
      g.rotation.z = base + wav; g.rotation.x = Math.sin(t * 1.3 + sx * 2) * 0.1 - bot.hop * 1.2;
    });

    // моргание
    nextBlink -= dt; if (nextBlink < 0) { blink = 1; nextBlink = 2.2 + Math.random() * 3.5; }
    blink = Math.max(0, blink - dt * 7);
    drawFace(t); ftex.needsUpdate = true;
    renderer.render(scene, cam);
  }
  bot.ready = true; bot.hopV = 0.14; bot.wave = 1; bot.say('happy', '', 1600);
  requestAnimationFrame(frame);
  window.__bot = { face: () => bot.face, scr, docked: () => docked };
  document.body.classList.add('has-bot'); window.__botSay = (f) => { bot.hopV = 0.1; bot.say(f, '', 1400); };
}
const start3d = () => Promise.all([import('three'), import('three/addons/geometries/RoundedBoxGeometry.js'), import('three/addons/environments/RoomEnvironment.js')])
  .then(([a, g, r]) => { THREE = a; RoundedBoxGeometry = g.RoundedBoxGeometry; RoomEnvironment = r.RoomEnvironment; buildBot(); })
  .catch(() => { document.body.classList.add('no-3d'); $('#bot')?.remove(); });
const later = () => (window.requestIdleCallback ? requestIdleCallback(start3d, { timeout: 2500 }) : setTimeout(start3d, 600));
if (document.readyState === 'complete') later(); else addEventListener('load', later, { once: true });

const CUR = document.documentElement.dataset.cur || '₽';
const CURF = (v) => CUR === '$' ? '$' + v : v + ' ₽';
/* ---------- робот реагирует на страницу ---------- */
$$('[data-price]').forEach((c) => {
  c.addEventListener('pointerenter', () => bot.say('price', CURF(c.dataset.price)));
  c.addEventListener('pointerleave', () => { if (bot.face === 'price') bot.say(total ? 'price' : 'idle', total ? CURF(fmt(total)) : ''); });
  c.addEventListener('focusin', () => bot.say('price', CURF(c.dataset.price), 2500));
});
const poster = $('#afisha');
if (poster) new IntersectionObserver((es) => { if (es[0].isIntersecting) { bot.say('wow', '', 2200); bot.hopV = 0.12; } }, { threshold: 0.5 }).observe(poster);
$$('.btn').forEach((b) => b.addEventListener('pointerenter', () => { if (bot.face !== 'price') bot.say('happy', '', 900); }));

/* ---------- калькулятор ---------- */
const sumEl = $('#sum'), listEl = $('#list'), send = $('#send'), bill = $('.bill');
let shown = 0, raf = 0, total = 0;
function fmt(n) { return Math.round(n).toLocaleString('ru-RU').replace(/\u00a0|\u202f|,/g, ' '); }
function countTo(target) {
  cancelAnimationFrame(raf);
  const from = shown, t0 = performance.now(), d = reduce ? 1 : 650;
  const tick = (t) => { const k = Math.min(1, (t - t0) / d), e = 1 - Math.pow(1 - k, 4); shown = from + (target - from) * e; sumEl.textContent = fmt(shown); if (k < 1) raf = requestAnimationFrame(tick); };
  raf = requestAnimationFrame(tick);
}
$$('.pick').forEach((b) => b.addEventListener('click', () => {
  b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') !== 'true');
  const on = $$('.pick[aria-pressed="true"]');
  total = on.reduce((s, x) => s + Number(x.dataset.p), 0);
  countTo(total);
  listEl.textContent = on.length ? on.map((x) => x.textContent.trim()).join(' · ') : (listEl.dataset.empty || 'Пока ничего не выбрано');
  bill.classList.toggle('is-bump');
  if (!reduce) { bot.hopV = 0.13; bot.wave = 0.6; }
  bot.say(total ? 'price' : 'idle', total ? CURF(fmt(total)) : '');
}));
