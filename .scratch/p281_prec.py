# -*- coding: utf-8 -*-
"""p281 判讀前之族序號量測與先例讀回。"""
import io
import json
import re
import collections

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
ti = {it['candidateId']: (it.get('title') or '') for it in w['items']}
rec = [(e['candidateId'][-8:], e['opinion'], e['reason']) for e in E]
print('涵蓋自報：主篩 %d 筆' % len(E))
print()

SEQ = [('檢索雜訊', r'檢索雜訊累計第 (\d+) 筆'),
       ('gel 詞族', r'gel. 詞族至此 (\d+) 筆'),
       ('cycle 詞族誤命中', r'cycle. 詞族誤命中第 (\d+) 筆'),
       ('健美語料', r'健美語料第 (\d+) 筆'),
       ('足球語料', r'足球語料第 (\d+) 筆'),
       ('立陶宛樣本', r'立陶宛樣本第 (\d+) 筆'),
       ('methodological', r'\[methodological\]. 累計第 (\d+) 筆'),
       ('攝取校準清單', r'攝取校準清單第 (\d+) 項')]
for lab, pat in SEQ:
    v = [int(m.group(1)) for _, _, t in rec for m in re.finditer(pat, t)]
    print('  %-16s 命中 %3d 次，最大號 %s' % (lab, len(v), max(v) if v else '—'))
print()

KEY = [('術前碳水飲 preop', r'術前.{0,6}碳水|preoperative|術前口服'),
       ('櫻桃 tart cherry', r'櫻桃'),
       ('抗氧化補充與訓練適應', r'抗氧化.{0,10}適應|維生素 C 與 E'),
       ('軍人補充品盛行率', r'補充品.{0,8}盛行率|軍人.{0,8}補充'),
       ('紅酒/酒精', r'紅酒|酒精攝取'),
       ('便祕/腸道蠕動', r'便祕|通便'),
       ('含糖飲料兒童', r'含糖飲料.{0,10}兒童|學齡前')]
for lab, pat in KEY:
    h = [r for r in rec if re.search(pat, r[2])]
    print('%-20s %4d 筆 %s' % (lab, len(h),
                              dict(collections.Counter(r[1] for r in h))))
    for s, op, rs in h[-2:]:
        print('     %s %-8s %s' % (s, op, rs[:240].replace('\n', ' ')))
    print()
