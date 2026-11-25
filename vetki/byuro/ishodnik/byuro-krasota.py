#!/usr/bin/env python3
# BYURO_KRASOTA_V1 (25.11): тихая красота стола — латунная кромка шапки, печать мастерской, мягкие карточки. Только CSS.
import sys
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
import re
t = re.sub(r'\n/\* BYURO_KRASOTA_V1 \*/[^\n]*', '', t)
if True:
    a = 'header{background:var(--deep);color:#fffbee;border-radius:0 0 22px 22px;padding:20px 26px;margin:0 -20px 24px;display:flex;align-items:center;gap:14px;box-shadow:0 14px 34px -18px rgba(0,0,0,.5)}'
    if t.count(a) != 1: sys.exit('якорь шапки: %d' % t.count(a))
    add = ('\n/* BYURO_KRASOTA_V1 */header{position:relative;border-bottom:3px solid #b08d57!important}'
           'header::after{content:"Мастерская Гуманет";position:absolute;right:22px;top:-9px;background:#26371f;font:700 10.5px/1 Onest,sans-serif;letter-spacing:.18em;text-transform:uppercase;color:#e9d9b4;border:1.5px solid rgba(233,217,180,.55);border-radius:4px;padding:5px 7px;transform:rotate(2deg);opacity:.8}'
           '.g5{border-color:#ddd3bf;box-shadow:0 1px 0 rgba(255,255,255,.8) inset,0 12px 26px -22px rgba(20,32,25,.5)}.g5 h2{color:#31442a}'
           '@media(max-width:640px){header::after{display:none}}')
    t = t.replace(a, a + add)
open(dst, 'w', encoding='utf-8').write(t)
