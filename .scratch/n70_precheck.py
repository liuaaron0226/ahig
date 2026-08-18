# -*- coding: utf-8 -*-
"""n+70（甲）寫入前之四項前置檢查——**不寫任何檔**。

1. 200 筆是否確實**都未判過**（append-only，重覆會被寫入器擋，但要先知道）；
2. 併入後 `contiguous` 是否會被意外推進（若某頁剛好整頁被抽中就會）；
3. 排除清單目前是否為空、schema 需要哪些欄位；
4. 200 筆是否確實都不在既有排除清單中。
"""
import glob
import io
import json
import os

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}

s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
ids = s['sample']['candidateIds']
short2full = {c[-8:]: c for c in ids}
dec = {}
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        dec[short2full[k]] = v
assert len(dec) == 200, len(dec)

dup = sorted(c for c in ids if c in op)
print('1. 已判過者：%d 筆 %s' % (len(dup), dup[:3]))

page_of = {it['candidateId']: it['page'] for it in w['items']}
by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
contiguous = 0
while all(c in op for c in by_page.get(contiguous + 1, [None])):
    contiguous += 1
op2 = dict(op)
op2.update({k: v[0] for k, v in dec.items()})
c2 = 0
while all(c in op2 for c in by_page.get(c2 + 1, [None])):
    c2 += 1
print('2. contiguous：%d -> %d（%s）'
      % (contiguous, c2, '未推進 ✅' if c2 == contiguous else '🚨 被推進了'))
from collections import Counter  # noqa: E402
per = Counter(page_of[c] for c in ids)
worst = per.most_common(3)
print('   單頁最多被抽中 %d 筆（頁大小 25），前三：%s' % (worst[0][1], worst))

ep = OUT + '/p-score-sequence-exclusions.json'
doc = json.load(io.open(ep, encoding='utf-8'))
print('3. 排除清單現有 %d 筆；entry 欄位：%s'
      % (len(doc['entries']), sorted(doc['entries'][0])))
existing = {e['candidateId'] for e in doc['entries']}
print('4. 200 筆與既有清單之交集：%d 筆' % len(existing & set(ids)))

seq_of = {}
for i, it in enumerate(w['items'], start=1):
    seq_of[it['candidateId']] = i
print()
print('可寫入之 entry 範例：%s'
      % json.dumps({'candidateId': ids[0], 'page': page_of[ids[0]],
                    'seq': seq_of[ids[0]]}, ensure_ascii=False))
print('AHIG_PRIVATE_ROOT 設定：%s'
      % os.environ.get('AHIG_PRIVATE_ROOT', '(未設，寫入時須設)'))
