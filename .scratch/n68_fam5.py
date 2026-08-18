# -*- coding: utf-8 -*-
"""第四批：本輪要引用的族序號一律先由資料量測，並讀回關鍵先例。

⚠️ n+67（七）教訓：族名切分可能過寬或過窄，故對每個要引用的號碼
**列出其正規式**，讓協調者能看出我量的是什麼。
"""
import glob
import io
import json
import re

R = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
     r'/b11-exogenous-cho-endurance/b11-full-run'
     r'/standard-full-screen-pass-1')
E = json.load(io.open(R + '/judgements.json', encoding='utf-8'))['entries']
w = json.load(io.open(R + '/worksheet.json', encoding='utf-8'))
ti = {it['candidateId']: (it.get('title') or '') for it in w['items']}
rec = [(e['candidateId'][-8:], e['opinion'], e['reason']) for e in E]
n_tail = 0
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        rec.append((k, v[0], v[1]))
        n_tail += 1
print('涵蓋自報：主篩 %d ＋ 尾端 %d = %d' % (len(E), n_tail, len(rec)))
print()

SEQ = [
    ('檢索雜訊', r'檢索雜訊累計第 (\d+) 筆'),
    ('gel 詞族', r'gel. 詞族至此 (\d+) 筆'),
    ('黑醋栗語料', r'黑醋栗語料第 (\d+) 筆'),
    ('帆船／風浪板語料', r'帆船／風浪板語料第 (\d+) 筆'),
    ('安慰劑載體是CHO', r'安慰劑載體是 CHO.{0,12}第 (\d+) 例'),
    ('glucose 詞族', r'glucose. 詞族[^；。]{0,10}第 (\d+) 筆'),
]
print('== 族序號（下一號 = 最大號 + 1）==')
for lab, pat in SEQ:
    v = [int(m.group(1)) for _, _, t in rec for m in re.finditer(pat, t)]
    print('  %-18s 命中 %3d 次，最大號 %s   /%s/'
          % (lab, len(v), max(v) if v else '—', pat))

print()
print('== 先例讀回：自選補液／自選強度型 ==')
for s in ['df30d5a7', '77c4298c', '189352a7']:
    hit = [r for r in rec if r[0] == s]
    if not hit:
        print('  %s **未判**  題名：%s'
              % (s, next((t for c, t in ti.items() if c[-8:] == s), '?')[:90]))
        continue
    _, op, rs = hit[0]
    print('  %s %-8s %s' % (s, op, rs[:420].replace('\n', ' ')))
    print()
