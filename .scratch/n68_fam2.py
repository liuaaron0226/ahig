# -*- coding: utf-8 -*-
"""判讀前之第二批族計數與先例讀回（涵蓋主篩＋尾端抽驗兩來源）。"""
import glob
import io
import json
import re

R = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
     r'/b11-exogenous-cho-endurance/b11-full-run'
     r'/standard-full-screen-pass-1')

E = json.load(io.open(R + '/judgements.json', encoding='utf-8'))['entries']
texts = [e['reason'] for e in E]
n_tail = 0
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        texts.append(v[1])
        n_tail += 1
print('涵蓋自報：主篩 %d ＋ 尾端 %d = %d' % (len(E), n_tail, len(texts)))
print()

for lab, pat in [('gel 詞族第N筆', r'gel. 詞族[^；。]{0,8}第 (\d+) 筆'),
                 ('gel 詞族至此N筆', r'gel. 詞族至此 (\d+) 筆'),
                 ('出版型別與內容不符', r'出版型別[^；。]{0,24}(?:不符|矛盾|與內容)')]:
    v = [m.group(0) for t in texts for m in re.finditer(pat, t)]
    print('%-20s %3d 次；末三：%s' % (lab, len(v), v[-3:]))

print()
# 出版型別標記為 RCT 但內容非隨機——本 lane 是否已登記此型？
pat = re.compile(r'publicationTypes|出版型別|標記為 RCT|型別標記')
h = [e for e in E if pat.search(e['reason'])]
print('提及出版型別之判讀 %d 筆' % len(h))
for e in h[:6]:
    print('  ', e['candidateId'][-8:], e['opinion'], '|',
          e['reason'][:230].replace('\n', ' '))
