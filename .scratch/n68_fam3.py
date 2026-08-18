# -*- coding: utf-8 -*-
"""第三批族計數：RED-S／製造體重、帆船、跳水、低碳水飲食操弄。"""
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

for lab, pat in [('RED-S/低能量可用性', r'RED-S|低能量可用性'),
                 ('製造體重', r'製造體重'),
                 ('該群至此 N 筆（RED-S 相鄰）', r'RED-S 相鄰[^。]{0,20}該群至此 (\d+) 筆'),
                 ('帆船/dinghy', r'帆船|風帆|dinghy'),
                 ('跳水 divers', r'跳水'),
                 ('黑醋栗/blackcurrant', r'黑醋栗|blackcurrant'),
                 ('低碳水飲食操弄', r'低碳水飲食|高脂飲食|生酮')]:
    h = [r for r in rec if re.search(pat, r[2])]
    print('%-26s %4d 筆' % (lab, len(h)))
    for s, op, rs in h[-3:]:
        print('      %s %-8s %s' % (s, op, rs[:150].replace('\n', ' ')))
    print()
