# -*- coding: utf-8 -*-
"""p280 判讀前之先例讀回與族計數（涵蓋主篩，尾端 200 筆已併入主篩）。"""
import io
import json
import re

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
ti = {it['candidateId']: (it.get('title') or '') for it in w['items']}
rec = [(e['candidateId'][-8:], e['opinion'], e['reason']) for e in E]
print('涵蓋自報：主篩 %d 筆（尾端抽驗 200 筆已於上輪併入）' % len(E))
print()

SEQ = [('檢索雜訊', r'檢索雜訊累計第 (\d+) 筆'),
       ('gel 詞族', r'gel. 詞族至此 (\d+) 筆'),
       ('cycle 詞族誤命中', r'cycle. 詞族誤命中第 (\d+) 筆'),
       ('安慰劑載體是CHO', r'安慰劑載體是 CHO.{0,12}第 (\d+) 例'),
       ('自選補給型', r'自選補給型.{0,4}第 (\d+) 筆'),
       ('Preprint 累計', r'Preprint. 累計第 (\d+) 筆')]
for lab, pat in SEQ:
    v = [int(m.group(1)) for _, _, t in rec for m in re.finditer(pat, t)]
    print('  %-18s 命中 %3d 次，最大號 %s' % (lab, len(v), max(v) if v else '—'))
print()

KEY = [('外文學位論文', r'學位論文|dissertation|博士論文|碩士論文'),
       ('環糊精 cyclodextrin', r'環糊精'),
       ('划船/賽艇 rowing', r'賽艇|划船'),
       ('橄欖球 rugby', r'橄欖球'),
       ('電競 eSports', r'電競|遊戲玩家'),
       ('健美 bodybuilder', r'健美'),
       ('褐藻醣膠 fucoidan', r'褐藻|海藻'),
       ('蜂蜜 honey', r'蜂蜜')]
for lab, pat in KEY:
    h = [r for r in rec if re.search(pat, r[2])]
    import collections
    print('%-22s %4d 筆 %s' % (lab, len(h),
                              dict(collections.Counter(r[1] for r in h))))
    for s, op, rs in h[-2:]:
        print('     %s %-8s %s' % (s, op, rs[:230].replace('\n', ' ')))
    print()
