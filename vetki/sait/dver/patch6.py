#!/usr/bin/env python3
# Витрина v6 (25.11): дверь (вход по записи), слой красоты, склад коробочек по профессиям. Идемпотентно (VITRINA6_V1).
import glob, os, re, sys
R = sys.argv[1]
SKIP = {'vhod.html', 'kabinet.html'}
SKLAD = '''<section class="sklad" id="sklad" aria-labelledby="sk-h"><div class="wrap"><!-- VITRINA6_V1 -->
<div class="sk-head"><div><p class="eyebrow">Склад</p><h2 id="sk-h">Коробочки по <em>профессиям</em></h2></div>
<p>Подберите полку под своё дело: на ней лежит то, что уже помогает людям этой работы. Цена и срок известны заранее. Коробочки с пометкой «на сборке» соберём под вас: напишите Фоме.</p></div>
<div id="sk-shelves"></div></div></section>
<script>(function(){var S=[
["Бухгалтер и офис","бумаги",["scan","k1c"]],["Продавец на WB и Ozon","маркетплейсы",["video","wb"]],
["Мастер и сервис: слесарь, автосервис, ремонт","клиенты",["ai","n8n"]],["Автор канала и блогер","подписчики",["kanal"]],
["Владелец сайта и магазина","порядок",["kstor","sopr"]],["Инженер и проектировщик","чертежи",["scan","chas"]],
["Водитель и перевозчик","рейсы",[["Учёт рейсов и путевых листов","Таблица и бот: рейс, пробег, топливо, выплаты. Без ручного переписывания."]]],
["Художник и 3D-печатник","работы",[["Витрина работ и приём заказов","Страница с работами, ценами и кнопкой заказа. Заявки приходят в Telegram."],["Модели и печать на заказ","Приём файлов, расчёт цены печати и статус заказа для клиента."]]]];
function esc(s){return String(s||'').replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function cut(s,n){s=String(s||'');return s.length>n?s.slice(0,n).replace(/\\s+\\S*$/,'')+'…':s}
function draw(K){var o='';S.forEach(function(sh){o+='<div class="shelf"><h3>'+esc(sh[0])+' <span class="tag">'+esc(sh[1])+'</span></h3><div class="row">';
sh[2].forEach(function(k){if(typeof k!=='string'){o+='<a class="kor soon" href="#chat-foma" data-chat><span class="lbl">на сборке</span><b>'+esc(k[0])+'</b><span class="in">'+esc(k[1])+'</span><span class="pr"><em>по задаче</em><span>Собрать мне</span></span></a>';return}
var s=K[k];if(!s)return;var p=Math.min.apply(null,s.plans.map(function(x){return x.p}));
o+='<a class="kor" href="oplata.html#u='+k+'"><b>'+esc(s.t)+'</b><span class="in">'+esc(cut(s.x,96))+'</span><span class="pr"><em>от '+p.toLocaleString('ru-RU')+' ₽'+(s.sub?'/мес':'')+'</em><span>Открыть</span></span></a>'});o+='</div></div>'});
document.getElementById('sk-shelves').innerHTML=o}
fetch('https://n8n.gumanetriya.ru/webhook/sait-katalog').then(function(r){return r.json()}).then(function(j){var K={};(j.items||[]).forEach(function(s){K[s.k]=s});draw(K)}).catch(function(){draw({})})})();</script>
'''
n = 0
for f in sorted(glob.glob(os.path.join(R, '*.html'))):
    p = os.path.basename(f)
    if p in SKIP or p.startswith('served-'): continue
    h = open(f, encoding='utf-8').read(); o = h
    if p != 'index.html' and 'krasota.css' not in h:
        h = h.replace('</head>', '<link rel="stylesheet" href="/krasota.css?v=2">\n</head>', 1)
    if 'dver.js' not in h:
        h = h.replace('</body>', '<script src="/dver.js?v=2" defer></script>\n</body>', 1)
    h = re.sub(r'dver\.js\?v=\d+', 'dver.js?v=' + os.environ.get('DVER_V', '2'), h); h = re.sub(r'krasota\.css\?v=\d+', 'krasota.css?v=' + os.environ.get('KRASOTA_V', '2'), h)
    if p == 'korobochki.html' and 'VITRINA6_V1' not in h:
        a = '<section style="padding-top:0"><div class="wrap"><div class="box-grid">'
        if a not in h: sys.exit('нет якоря склада')
        h = h.replace(a, SKLAD + a, 1)
    if h != o:
        t = f + '.v6tmp'; open(t, 'w', encoding='utf-8').write(h); os.replace(t, f); n += 1
print('витрина v6: изменено html', n)
