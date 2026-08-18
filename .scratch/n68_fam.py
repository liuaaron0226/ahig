# -*- coding: utf-8 -*-
"""判讀前先由資料算出族計數（不得憑印象寫「第 N 筆」）。

涵蓋自報：主篩 judgements.json ＋ 尾端抽驗 n68_tail_dec_*.json 兩個來源
（第 346 輪教訓：尾端判讀不在 judgements.json）。
本檔看不到：族名切分是否正確（見 n59_counters.py 之自報）。
"""
import glob
import io
import json
import re

R = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
     r'/b11-exogenous-cho-endurance/b11-full-run'
     r'/standard-full-screen-pass-1')

texts = []
E = json.load(io.open(R + '/judgements.json', encoding='utf-8'))['entries']
for e in E:
    texts.append(e['reason'])
n_tail = 0
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        texts.append(v[1])
        n_tail += 1
print('涵蓋自報：主篩 %d ＋ 尾端抽驗 %d = 可查文本 %d'
      % (len(E), n_tail, len(texts)))
print()

PATS = [
    ('檢索雜訊累計第N筆', r'檢索雜訊累計第 (\d+) 筆'),
    ('動物研究類第N筆', r'動物研究類第 (\d+) 筆'),
    ('安慰劑載體是CHO第N例', r'安慰劑載體是 CHO[^；。]{0,12}第 (\d+) 例'),
    ('cycle詞族誤命中第N筆', r'cycle. 詞族誤命中第 (\d+) 筆'),
    ('carbohydrate詞族誤命中第N', r'carbohydrate. 詞族誤命中第 (\d+) 筆'),
]
for lab, pat in PATS:
    v = [int(m.group(1)) for t in texts for m in re.finditer(pat, t)]
    print('%-26s 出現 %4d 次，最大號 %s' % (lab, len(v), max(v) if v else '—'))

print()
KEY = [
    ('gel/凝膠', r'凝膠|gel'),
    ('划船/舟艇', r'划船|獨木舟|輕艇|舟艇|kayak'),
    ('帆船/風帆', r'帆船|風帆|dinghy|sail'),
    ('潛水/跳水', r'跳水|潛水|divers?'),
    ('柔道/格鬥', r'柔道|格鬥|judo'),
    ('核糖', r'核糖'),
    ('軍事/新兵', r'軍事|新兵|士兵|soldier'),
    ('思覺失調/精神科', r'思覺失調|精神'),
]
for lab, pat in KEY:
    n = sum(1 for t in texts if re.search(pat, t))
    print('%-14s 出現於 %4d 筆判讀理由' % (lab, n))
