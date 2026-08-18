# -*- coding: utf-8 -*-
"""p283 判讀前之族序號量測與先例讀回。"""
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
       ('非人類生物體', r'非人類生物體第 (\d+) 例'),
       ('學位論文累計', r'學位論文累計第 (\d+) 筆'),
       ('標題指向入局型', r'「標題指向入局」型第 (\d+) 筆'),
       ('足球語料', r'足球語料第 (\d+) 筆'),
       ('自選補給型', r'自選補給型.{0,4}第 (\d+) 筆')]
for lab, pat in SEQ:
    v = [int(m.group(1)) for _, _, t in rec for m in re.finditer(pat, t)]
    print('  %-16s 命中 %3d 次，最大號 %s' % (lab, len(v), max(v) if v else '—'))
print()

KEY = [('模擬自行車賽 simulated race', r'模擬.{0,4}(?:自行車|公路)|模擬賽'),
       ('斯洛維尼亞/南斯拉夫語系', r'斯洛維尼亞|克羅埃西亞|塞爾維亞'),
       ('葡萄糖電解質溶液 vs 水', r'右旋糖.{0,10}電解質|葡萄糖電解質'),
       ('熱環境田野訓練', r'熱環境.{0,10}訓練|熱適應'),
       ('急性營養介入 acute nutritional', r'急性營養介入'),
       ('咖啡 coffee', r'咖啡(?!因)'),
       ('英超足球日內分布', r'英超|英格蘭超級聯賽')]
for lab, pat in KEY:
    h = [r for r in rec if re.search(pat, r[2])]
    print('%-30s %4d 筆 %s' % (lab, len(h),
                               dict(collections.Counter(r[1] for r in h))))
    for s, op, rs in h[-2:]:
        print('     %s %-8s %s' % (s, op, rs[:230].replace('\n', ' ')))
    print()
