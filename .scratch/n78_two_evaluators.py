# -*- coding: utf-8 -*-
"""n+78：查明 `term.py` 與 `term2.py` 為何給出不同的終止判定。

🚨 改判後 term.py 報 pScore 0.012405（跌破 α），term2.py 報 allowedToStop
False。**兩支腳本不一致就不能挑一個回報**——本檔把差異拆成兩個彼此獨立
的成因，各自量出來。

不落地任何文獻內容（n+48 內容制衛生）。
"""
import json
import os
import sys
from pathlib import Path

os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import (  # noqa: E402
    evaluate_termination, p_score)

ROOT = Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
            r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = ROOT / 'standard-full-screen-pass-1'
queue = json.loads((ROOT / 'screening-queue' / 'queue.json')
                   .read_text(encoding='utf-8'))
w = json.loads((OUT / 'worksheet.json').read_text(encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in
      json.loads((OUT / 'judgements.json').read_text(encoding='utf-8'))['entries']}
for f in ('post-ruling-reclassification.json',
          'post-ruling-abstract-rescreen.json'):
    for e in json.loads((OUT / f).read_text(encoding='utf-8'))['entries']:
        op[e['candidateId']] = e['effectiveDecision']

by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
cont = 0
while all(c in op for c in by_page.get(cont + 1, [None])):
    cont += 1
exc = json.loads((OUT / 'p-score-sequence-exclusions.json')
                 .read_text(encoding='utf-8'))
out_perm = {e['candidateId'] for e in exc['entries']
            if e.get('state') == 'out-of-sequence-permanent'}
skip = set(out_perm) | {e['candidateId'] for e in exc['entries']
                        if e.get('state') != 'out-of-sequence-permanent'
                        and e['page'] > cont}

labels = [1 if op[it['candidateId']] in ('advance', 'unclear') else 0
          for it in w['items']
          if it['candidateId'] in op and it['candidateId'] not in skip]

print('=' * 66)
print('成因一：labels 序列的組成（term2 把其他 lane 接進序列尾端）')
print('=' * 66)
other = []
for d in ('safety-full-screen-pass-1', 'critical-harms-sweep',
          'critical-harms-sweep-orphans'):
    p = ROOT / d / 'judgements.json'
    if p.exists():
        for e in json.loads(p.read_text(encoding='utf-8'))['entries']:
            if e['candidateId'] not in op:
                other.append((e['candidateId'], e['opinion']))
tail = [o for _, o in other[-3:]]
print('  其他 lane 併入 %d 筆；其序列尾端三筆意見：%s' % (len(other), tail))
a = p_score(labels, w['itemCount'])
merged = labels + [1 if o in ('advance', 'unclear') else 0 for _, o in other]
print('  只有標準線     n_seen %-5d window %-4d pScore %.6f'
      % (a['screenedCount'], a['windowSize'], a['pScore']))
try:
    b = p_score(merged, w['itemCount'])
    print('  接上其他 lane  window %-4d pScore %.6f' % (b['windowSize'], b['pScore']))
except Exception as e:
    print('  接上其他 lane  n_seen %d → 🚨 以標準線池為分母時程式直接擋下：%s'
          % (len(merged), e))
    b = p_score(merged, len(queue))
    print('  （改用全 lane 池才算得出）window %-4d pScore %.6f'
          % (b['windowSize'], b['pScore']))
print('  🚨 window 由 %d 崩為 %d——因為併入序列的最後幾筆中有 unclear。'
      % (a['windowSize'], b['windowSize']))
print('  ⚠️ 這正是 n+70（二）已認定的語意破壞：把獨立稽核／他線判讀')
print('     接進循序檢定的標籤流，windowSize「尾端連續無命中」的語意就沒了。')
print()

print('=' * 66)
print('成因二：n_total 取哪一個池')
print('=' * 66)
for name, n in (("worksheet itemCount（標準線池）", w['itemCount']),
                ("len(queue)（全 lane 池）", len(queue))):
    r = p_score(labels, n)
    print('  %-28s n_total %-6d window %-4d pScore %.6f'
          % (name, n, r['windowSize'], r['pScore']))
print('  🚨 同一組 labels、同一個 window，只換分母，pScore 由 %.6f 變 %.6f。'
      % (p_score(labels, w['itemCount'])['pScore'],
         p_score(labels, len(queue))['pScore']))
print()

print('=' * 66)
print('兩支腳本各自的實際輸出')
print('=' * 66)
print('  term.py  ：只餵標準線序列，n_total = itemCount 9091')
print('             → window %d、pScore %.6f' % (a['windowSize'], a['pScore']))
res = evaluate_termination(queue,
                           [(it['candidateId'], op[it['candidateId']])
                            for it in w['items'] if it['candidateId'] in op]
                           + other, out_of_sequence=out_perm)
print('  term2.py ：餵全部 lane，n_total = len(queue) 15425')
print('             → window %d、pScore %.6f、allowedToStop %s'
      % (res['windowSize'], res['pScore'], res['allowedToStop']))
print()
print('⚠️ 結論：兩支腳本不是一支對一支錯，是在回答兩個不同的問題。')
print('   term.py 問「標準線這條序列的尾段乾了沒」；')
print('   term2.py 問「把所有 lane 的判讀串成一條序列後，尾段乾了沒」。')
print('🚨 而 term2 的問法有一個已被 n+70（二）認定的缺陷：')
print('   他線判讀不是標準線逐頁篩選的延續，接進去 windowSize 就失去語意。')
print('🚨 故本輪之終止觸發判定，我不自行選定，只把兩者並陳請協調者裁示。')
