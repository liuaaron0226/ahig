# -*- coding: utf-8 -*-
"""n+58（四）所指之期內變異：p222–242 vs p243–249（皆在補摘要之後）。

⚠️ 協調者已先寫明：**這是補摘要期內部的頁次變異，不是補摘要效果，
不得拿來當補摘要有效的證據。** 本檔只是把該變異量出來，
並檢查它是否大到足以動搖第一節之三分層結論。

唯讀，不寫任何檔案。
"""
import json
import math
import os
import re

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
OUT = (ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
       + '/standard-full-screen-pass-1')

CHO = re.compile(
    r'carbohydrate|glucose|sucrose|fructose|maltodextrin|dextrin|'
    r'starch|honey|glycogen|sports drink|CHO\b', re.I)

w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
for f in ('post-ruling-reclassification.json',
          'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + f
    if os.path.exists(p):
        for e in json.load(open(p, encoding='utf-8'))['entries']:
            op[e['candidateId']] = e['effectiveDecision']

HIT = {'advance', 'unclear'}


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    q = k / n
    den = 1 + z * z / n
    ctr = (q + z * z / (2 * n)) / den
    half = z * math.sqrt(q * (1 - q) / n + z * z / (4 * n * n)) / den
    return (max(0.0, ctr - half), min(1.0, ctr + half))


def seg(lo, hi):
    g = [it for it in w['items']
         if lo <= it['page'] <= hi and it['candidateId'] in op]
    n = len(g)
    h = sum(1 for it in g if op[it['candidateId']] in HIT)
    s = sum(1 for it in g if CHO.search(it.get('title') or ''))
    return n, h, s, wilson(h, n)


print('=== 補摘要期內部之頁次變異（全段皆在補摘要之後）===')
rows = []
for lo, hi, lab in [(222, 242, 'p222-242'), (243, 249, 'p243-249')]:
    n, h, s, ci = seg(lo, hi)
    rows.append((lab, n, h, s, ci))
    print('%-10s n=%-4d 命中 %2d (%4.1f%%, CI %4.1f-%4.1f%%)  '
          '標題碳水訊號 %3d (%4.1f%%)'
          % (lab, n, h, 100.0 * h / n, 100 * ci[0], 100 * ci[1],
             s, 100.0 * s / n))

(l1, n1, h1, s1, c1), (l2, n2, h2, s2, c2) = rows
overlap = not (c1[1] < c2[0] or c2[1] < c1[0])
print()
print('兩段命中率區間 %s' % ('重疊' if overlap else '**不重疊**'))
print('兩段標題碳水訊號密度：%.1f%% vs %.1f%%（比值 %.2f 倍）'
      % (100.0 * s1 / n1, 100.0 * s2 / n2, (s2 / n2) / (s1 / n1)))
print()
print('⚠️ 依 n+58（四）：此為期內頁次變異，**不得作為補摘要有效之證據**。')
print('   本檔量測之用途僅在於：確認該變異不足以動搖三分層之結論。')
