# -*- coding: utf-8 -*-
"""第五批：自選補給型序號、以及「補液量為自變項」型先例。"""
import glob
import io
import json
import re

R = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
     r'/b11-exogenous-cho-endurance/b11-full-run'
     r'/standard-full-screen-pass-1')
E = json.load(io.open(R + '/judgements.json', encoding='utf-8'))['entries']
rec = [(e['candidateId'][-8:], e['opinion'], e['reason']) for e in E]
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        rec.append((k, v[0], v[1]))

for lab, pat in [('自選補給型第N筆', r'自選補給型第 (\d+) 筆'),
                 ('無訓練程度形容詞該型第N', r'無訓練程度形容詞[^；。]{0,12}第 (\d+) 筆'),
                 ('補液量為自變項', r'補液量|水合狀態為自變項|脫水程度')]:
    v = [m.group(0) for _, _, t in rec for m in re.finditer(pat, t)]
    print('%-24s %3d 次；末三：%s' % (lab, len(v), v[-3:]))
print()

pat = re.compile(r'自選補給型|自主飲水|自由飲用|ad libitum')
h = [r for r in rec if pat.search(r[2])]
print('自選補給／自由飲用族 %d 筆' % len(h))
import collections
print(collections.Counter(r[1] for r in h))
for s, op, rs in h[-4:]:
    print('  %s %-8s %s' % (s, op, rs[:300].replace('\n', ' ')))
