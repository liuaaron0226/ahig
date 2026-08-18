# -*- coding: utf-8 -*-
"""n+64（三）跨輪引述讀回——**涵蓋兩個來源**。

⚠️ **第 346 輪教訓**：尾端抽驗之判讀寫在 `.scratch/n68_tail_dec_*.json`，
**不在 `judgements.json`**。我第一次只讀後者，於是三筆本輪剛判的記錄
被回報「未命中」——**那是來源找錯，不是引述錯**。

🚨 這與 n+67（八）「誤讀檢查之涵蓋範圍」同型：
**檢查本身沒錯，是我沒問它讀的是哪些檔案。**
故本檔**明列其涵蓋之兩個來源**，並於輸出自報（n+67 二 2）。

用法：python -X utf8 .scratch/n68_xref.py <short:phrase> ...
"""
import glob
import io
import json
import re
import sys

R = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
     r'/b11-exogenous-cho-endurance/b11-full-run'
     r'/standard-full-screen-pass-1')

src = {}
E = json.load(io.open(R + '/judgements.json', encoding='utf-8'))['entries']
for e in E:
    src[e['candidateId'][-8:]] = ('主篩 judgements.json', e['reason'],
                                  e['opinion'])

tail_files = sorted(glob.glob('.scratch/n68_tail_dec_*.json'))
n_tail = 0
for p in tail_files:
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        src[k] = ('尾端抽驗 ' + p.split('/')[-1], v[1], v[0])
        n_tail += 1

pairs = []
for a in sys.argv[1:]:
    short, _, phrase = a.partition(':')
    pairs.append((short, phrase))

print('涵蓋自報：主篩 %d 筆 + 尾端抽驗 %d 筆（%d 檔）= 可查 %d 筆'
      % (len(E), n_tail, len(tail_files), len(src)))
print()
bad = []
for short, phrase in pairs:
    rec = src.get(short)
    if not rec:
        bad.append((short, phrase, '查無此筆'))
        print('%-9s ✗ 查無' % short)
        continue
    where, reason, op = rec
    ok = (op == phrase) if phrase in ('advance', 'unclear', 'exclude') \
        else bool(re.search(re.escape(phrase), reason))
    if not ok:
        bad.append((short, phrase, where))
    print('%-9s %s %-24s 「%s」%s'
          % (short, '✓' if ok else '✗', where, phrase,
             '命中' if ok else '**未命中**'))
print()
print('檢查 %d 筆，未命中 %d 筆' % (len(pairs), len(bad)))
if bad:
    print('⚠️ 未命中明細：%s' % bad)
