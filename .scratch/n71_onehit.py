# -*- coding: utf-8 -*-
"""補算：以協調者當時看得到的資料（150 筆判畢、1 命中）重跑那張表。

⚠️ 目的不是替他找台階，是**把「他錯了」與「他看的資料不同」分開**。
若用他當時的資料算出來仍與其公布值不符，那才是真的算錯。

本檔看得到：在只併入前 150 筆判讀之情境下的 window 與 pScore。
本檔看不到：他實際跑的程式。
"""
import glob
import io
import json
import os
import sys

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score  # noqa: E402

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
for name in ('post-ruling-reclassification.json',
             'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + name
    if os.path.exists(p):
        for e in json.load(io.open(p, encoding='utf-8'))['entries']:
            op[e['candidateId']] = e['effectiveDecision']

s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
ids = s['sample']['candidateIds']
short2full = {c[-8:]: c for c in ids}
dec = {}
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        dec[short2full[k]] = v[0]

N = w['itemCount']
for n_judged in (150, 200):
    sub = set(ids[:n_judged])
    rest = set(ids) - sub
    lab = [1 if op[it['candidateId']] in ('advance', 'unclear') else 0
           for it in w['items']
           if it['candidateId'] in op and it['candidateId'] not in rest]
    r = p_score(lab, N)
    n_start = N - (r['screenedCount'] - r['windowSize'])
    n_hits = sum(1 for c in sub if dec[c] in ('advance', 'unclear'))
    print('併入前 %3d 筆（其中命中 %d）：n_seen %d  window %4d  '
          'n_start %5d  pScore %.6f'
          % (n_judged, n_hits, r['screenedCount'], r['windowSize'],
             n_start, r['pScore']))

print()
print('🚨 即使只用他當時看得到的 150 筆（1 命中），window 也不是 177。')
print('   `ad555302` 之 seq 為 8702，遠在目前序列尾端（seq 6975）之後，')
print('   一旦併入即成為「最後一筆相關」，window 必然縮短。')
print()
print('⚠️ 故差異不在資訊時間差，在那張表把 window 當成常數。')
print('   **但這不影響他的結論之可用性**——見 n71_reconcile.py 末段：')
print('   n+70（甲）安全的真正理由是「排除清單非空即不得終止」，')
print('   與 p 值大小無關。')
