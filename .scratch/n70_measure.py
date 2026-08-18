# -*- coding: utf-8 -*-
"""n+70（甲）執行前之影響量測——**不寫任何檔**。

⚠️ 既有習慣（n+62 三段式）：先核對實質判準、再量測影響、影響清楚才動手。
本檔量測「把 200 筆抽驗判讀併入判讀集並列入 p 值排除清單」之後：
  1. `windowSize` 會怎麼變；
  2. `pScore` 會怎麼變；
  3. 這 200 筆分布在哪些頁、最遠一頁是第幾頁（＝何時才會全部納回）。

🚨 本檔不呼叫 `evaluate_termination`（那要整份 queue），而是重現
`.scratch/term.py` 之 labels 建法——**故本檔看得到的是 p 值那一半，
看不到前置條件與 allowedToStop**。那由 term.py 於實際寫入後量。
"""
import glob
import io
import json
import os
import sys

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score  # noqa: E402

RUN = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = RUN + '/standard-full-screen-pass-1'

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}

for name in ('post-ruling-reclassification.json',
             'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + name
    if os.path.exists(p):
        for e in json.load(io.open(p, encoding='utf-8'))['entries']:
            op[e['candidateId']] = e['effectiveDecision']

by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
contiguous = 0
while all(c in op for c in by_page.get(contiguous + 1, [None])):
    contiguous += 1

exc = set()
ep = OUT + '/p-score-sequence-exclusions.json'
if os.path.exists(ep):
    for e in json.load(io.open(ep, encoding='utf-8'))['entries']:
        if e['page'] > contiguous:
            exc.add(e['candidateId'])

labels = [1 if op[it['candidateId']] in ('advance', 'unclear') else 0
          for it in w['items']
          if it['candidateId'] in op and it['candidateId'] not in exc]
before = p_score(labels, w['itemCount'])
print('【現況】連續判畢至 page %d；序列長度 %d；排除中 %d'
      % (contiguous, len(labels), len(exc)))
print('  pScore %.6f  windowSize %d  relevantFound %d'
      % (before['pScore'], before['windowSize'], before['relevantFound']))
print()

# 抽驗 200 筆
s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
ids = s['sample']['candidateIds']
short2full = {c[-8:]: c for c in ids}
dec = {}
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        dec[short2full[k]] = v[0]
assert len(dec) == 200

page_of = {it['candidateId']: it['page'] for it in w['items']}
pages = sorted(page_of[c] for c in ids)
print('【抽驗 200 筆之頁分布】最小 p%d，中位 p%d，最大 p%d'
      % (pages[0], pages[100], pages[-1]))
print('  ⚠️ 即須逐頁推進至 p%d，最後一筆才會納回 p 值序列。' % pages[-1])
print('  總頁數 %d，目前 p%d，尚餘 %d 頁'
      % (max(by_page), contiguous, max(by_page) - contiguous))
print()

# 併入後（200 筆全部列入排除清單 → labels 不變）
op2 = dict(op)
op2.update(dec)
exc2 = set(exc) | set(ids)
labels2 = [1 if op2[it['candidateId']] in ('advance', 'unclear') else 0
           for it in w['items']
           if it['candidateId'] in op2 and it['candidateId'] not in exc2]
after = p_score(labels2, w['itemCount'])
print('【併入後（200 筆全列排除清單）】序列長度 %d；排除中 %d'
      % (len(labels2), len(exc2)))
print('  pScore %.6f  windowSize %d  relevantFound %d'
      % (after['pScore'], after['windowSize'], after['relevantFound']))
print('  Δ序列長度 %+d   Δwindow %+d   ΔpScore %+.6f'
      % (len(labels2) - len(labels),
         after['windowSize'] - before['windowSize'],
         after['pScore'] - before['pScore']))
print()

# 對照：若**不排除**、直接接進序列（n+70 二所述之壞情況）
labels3 = [1 if op2[it['candidateId']] in ('advance', 'unclear') else 0
           for it in w['items']
           if it['candidateId'] in op2 and it['candidateId'] not in exc]
bad = p_score(labels3, w['itemCount'])
print('【對照：若直接接進序列（不採排除清單）】')
print('  序列長度 %d  pScore %.6f  windowSize %d'
      % (len(labels3), bad['pScore'], bad['windowSize']))
print('  🚨 windowSize 由 %d 變 %d——**這正是 n+70 二所述之語意破壞**，'
      % (before['windowSize'], bad['windowSize']))
print('     故不採此路。')
