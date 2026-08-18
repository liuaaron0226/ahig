# -*- coding: utf-8 -*-
"""第 369 輪：實測「再幾筆無命中會使 pScore 跌破 α」。

⚠️ 不推估，直接沿用 term.py 的序列組法，往後接 k 筆 exclude（label 0）
逐次呼叫 `p_score`，看 pScore 何時 < 0.05。

🚨 依 n+57，執行室不得宣告終止；本檔只算距離，供心跳預告。
⚠️ 本檔算的是「若後續全部無命中」之最快情形，**不是預測**——
只要中間出現一筆 advance/unclear，windowSize 歸零、距離重算。
不落地任何文獻內容（n+48 內容制衛生）。
"""
import json
import os
import sys
from collections import Counter

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score  # noqa: E402

RUN = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs/'
       r'b11-exogenous-cho-endurance/b11-full-run')
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}

for path, field in ((OUT + '/post-ruling-reclassification.json', 1),
                    (OUT + '/post-ruling-abstract-rescreen.json', 2)):
    if os.path.exists(path):
        for e in json.load(open(path, encoding='utf-8'))['entries']:
            op[e['candidateId']] = e['effectiveDecision']

by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
contiguous = 0
while all(c in op for c in by_page.get(contiguous + 1, [None])):
    contiguous += 1

skip = set()
exc_path = OUT + '/p-score-sequence-exclusions.json'
if os.path.exists(exc_path):
    for e in json.load(open(exc_path, encoding='utf-8'))['entries']:
        state = e.get('state', 'pending-reintegration')
        if state == 'out-of-sequence-permanent' or e['page'] > contiguous:
            skip.add(e['candidateId'])

labels = [1 if op[it['candidateId']] in ('advance', 'unclear') else 0
          for it in w['items']
          if it['candidateId'] in op and it['candidateId'] not in skip]

base = p_score(labels, w['itemCount'])
print('目前：序列 %d 筆、windowSize %d、pScore %.6f'
      % (len(labels), base['windowSize'], base['pScore']))
print()

ALPHA = 0.05
prev = None
for k in range(0, 200):
    r = p_score(labels + [0] * k, w['itemCount'])
    if prev is None or k % 10 == 0 or r['pScore'] < ALPHA:
        print('  +%3d 筆無命中 → windowSize %3d、pScore %.6f%s'
              % (k, r['windowSize'], r['pScore'],
                 '  ← 跌破 α' if r['pScore'] < ALPHA else ''))
    if r['pScore'] < ALPHA:
        need = k
        break
    prev = r
else:
    raise AssertionError('200 筆內未跌破 α，本檔前提需重寫')

print()
print('🚨 若自本頁起全部無命中，再 **%d 筆** pScore 即跌破 α = %s' % (need, ALPHA))
pages = need / 23.0
print('   以近期每頁約 23 筆計，約當 **%.1f 頁**' % pages)
print()
print('⚠️ 這是最快情形，不是預測：只要中途出現一筆 advance/unclear，')
print('   windowSize 歸零、距離重算。上次觸發後尾端抽驗抓到 2 筆命中而失敗，')
print('   即為此故。')
print('🚨 依 n+57，觸發時執行室只跑六步程序並回報，不自行宣告終止。')
