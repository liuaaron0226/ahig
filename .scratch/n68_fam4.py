# -*- coding: utf-8 -*-
"""查證第三批之疑點：帆船族之 4 筆命中是否含跨輪引述（假命中）。"""
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

CITATION = re.compile(r'第 \d+ 輪[^；。]{0,80}')
pat = re.compile(r'帆船|風帆|dinghy')
print('帆船族：原始命中 vs 去除跨輪引述後')
for s, op, rs in rec:
    if pat.search(rs):
        stripped = CITATION.sub('', rs)
        m = pat.search(stripped)
        print('  %s %-8s 原始命中=是  去引述後=%s'
              % (s, op, '是' if m else '**否（跨輪引述所致之假命中）**'))
        seg = pat.search(rs)
        print('      前後文：…%s…' % rs[max(0, seg.start() - 40):seg.end() + 40])
