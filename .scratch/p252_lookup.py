# -*- coding: utf-8 -*-
"""page 252 判讀前之累計編號查核（唯讀）。

依 n+59 第四節：**呈現為結果的字串必須現算。** 判讀理由裡要寫的
累計編號一律由本檔查出，不憑印象。
"""
import io
import json
import re

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']

PATS = [
    ('carbohydrate 詞族誤命中', r'`carbohydrate` 詞族誤命中第 (\d+) 筆'),
    ('學位論文累計', r'學位論文，累計第 (\d+) 筆'),
    ('無摘要處置標準累計適用', r'該標準累計適用第 (\d+) 筆'),
    ('標題指向入局型', r'標題指向入局」型第 (\d+) 筆'),
    ('Patent 累計', r'累計第 (\d+) 筆\*\*）。內容'),
    ('攝取校準清單', r'攝取校準清單第 (\d+) 項'),
    ('格鬥項目語料', r'格鬥項目語料第 (\d+) 筆'),
    ('非人類生物體', r'非人類生物體第 (\d+) 例'),
    ('預印本累計', r'預印本累計第 (\d+) 筆'),
    ('自選補給型累計', r'自選補給型累計第 (\d+) 筆'),
    ('檢索雜訊累計', r'檢索雜訊累計第 (\d+) 筆'),
    ('[methodological] 累計', r'\[methodological\] 累計第 (\d+) 筆'),
    ('診斷性葡萄糖負荷型', r'診斷性葡萄糖負荷型增至 (\d+) 筆'),
    ('游泳選手語料', r'游泳選手語料第 (\d+) 筆'),
    ('第 45 項活躍案例', r'第 45 項(?:待裁之)?活躍案例第 (\d+) 筆'),
]

for name, pat in PATS:
    rx = re.compile(pat)
    hits = [(e['candidateId'][-8:], int(m.group(1)))
            for e in E for m in [rx.search(e.get('reason', '') or '')] if m]
    if hits:
        print('%-26s 明寫 %3d 筆，最後一筆 %s → 第 %d 筆（下一筆應為 %d）'
              % (name, len(hits), hits[-1][0], hits[-1][1], hits[-1][1] + 1))
    else:
        print('%-26s （無明寫編號）' % name)

# Patent 之樣式較不固定，另以型別欄位直接數
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
judged = {e['candidateId'] for e in E}
pat_n = sum(1 for it in w['items']
            if it['candidateId'] in judged
            and 'Patent' in (it.get('publicationTypes') or []))
print()
print('Patent 型別（依 worksheet 欄位直接數，已判讀者）：%d 筆' % pat_n)
