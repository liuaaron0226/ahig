# -*- coding: utf-8 -*-
"""末塊 [175:200] 判讀前之族計數與先例讀回（涵蓋主篩＋尾端七檔）。"""
import glob
import io
import json
import re

R = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
     r'/b11-exogenous-cho-endurance/b11-full-run'
     r'/standard-full-screen-pass-1')
E = json.load(io.open(R + '/judgements.json', encoding='utf-8'))['entries']
rec = [(e['candidateId'][-8:], e['opinion'], e['reason']) for e in E]
n_tail = 0
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        rec.append((k, v[0], v[1]))
        n_tail += 1
print('涵蓋自報：主篩 %d ＋ 尾端 %d = %d' % (len(E), n_tail, len(rec)))
print()

SEQ = [('檢索雜訊', r'檢索雜訊累計第 (\d+) 筆'),
       ('gel 詞族', r'gel. 詞族至此 (\d+) 筆'),
       ('運動飲料與口腔/知識', r'知識與攝取')]
for lab, pat in SEQ:
    v = [m.group(1) if m.groups() else m.group(0)
         for _, _, t in rec for m in re.finditer(pat, t)]
    nums = [int(x) for x in v if str(x).isdigit()]
    print('  %-20s 命中 %3d 次，最大號 %s'
          % (lab, len(v), max(nums) if nums else '（無編號）'))
print()

KEY = [('反禁藥/檢測方法', r'禁藥|doping|反興奮劑'),
       ('甘油/超水合', r'甘油'),
       ('網球', r'網球'),
       ('乳癌/癌症存活者', r'癌症|乳癌'),
       ('青少年運動員每日攝取', r'青少年.{0,6}運動員|青年選手'),
       ('系統性文獻回顧計畫書', r'系統性文獻回顧|統合分析')]
for lab, pat in KEY:
    h = [r for r in rec if re.search(pat, r[2])]
    print('%-18s %4d 筆' % (lab, len(h)))
    for s, op, rs in h[-2:]:
        print('     %s %-8s %s' % (s, op, rs[:170].replace('\n', ' ')))
    print()
