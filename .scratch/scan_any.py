# -*- coding: utf-8 -*-
"""夾雜外文掃描——**吃兩種形狀**：主篩的 list-of-entry 與尾端抽驗的 dict。

⚠️ 第 348 輪：直接把 `.scratch/n68_tail_dec_*.json` 餵給 `scan.py`
會 `TypeError`（它假設元素是 dict 且有 `reason` 鍵）。
**那是形狀不合，不是「掃描通過」**——若我把 traceback 當成沒問題，
就是第 2 型缺陷（吞掉 stderr）。故另立本檔，不改動 `scan.py`。

本檔看得到：判讀理由中夾雜之外文詞（同 scan.py 之字集與白名單）。
本檔看不到：判讀內容對錯、族序號是否正確。
"""
import io
import json
import re
import sys

OK = {'g', 'kg', 'ph', 'vs', 'mg', 'ml', 'mj', 'bmi', 'dxa', 'rm', 'kj',
      'vo', 'iga', 'wgan', 'gp', 'xgboost', 'svr', 'mlp', 'geneactiv',
      'asprosin', 'masld', 'comp', 'nefa', 'dnl', 'ebct', 'cacs', 'chd',
      'vdr', 'er', 'colia', 'paq', 'fitnessgram', 'whr', 'ldl', 'hdl',
      'tc', 'fbg', 'npa', 'ssb', 'who', 'ers', 'nhis', 'nsc', 'ct', 'ci',
      'sd', 'se', 'n'}
PAT = re.compile(r'[Ѐ-ӿ가-힯぀-ヿ]+'
                 r'|[A-Za-z]+(?=[一-鿿])'
                 r'|(?<=[一-鿿])[A-Za-z]{3,}')

d = json.load(io.open(sys.argv[1], encoding='utf-8'))
if isinstance(d, dict) and 'entries' in d:
    items = [(e['candidateId'][-8:], e['reason']) for e in d['entries']]
    shape = 'dict-with-entries'
elif isinstance(d, dict):
    items = [(k, v[1]) for k, v in d.items()]
    shape = 'short -> (opinion, reason)'
else:
    items = [(e['candidateId'][-8:], e['reason']) for e in d]
    shape = 'list-of-entry'
print('形狀自報：%s，%d 筆' % (shape, len(items)))

bad = 0
for short, reason in items:
    m = [x for x in PAT.findall(reason) if x.lower() not in OK]
    if m:
        print(short, m[:6])
        bad += 1
print('entries %d flagged %d' % (len(items), bad))
