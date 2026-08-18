# -*- coding: utf-8 -*-
"""p282 判讀前之族序號量測與先例讀回。"""
import io
import json
import re
import collections

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
rec = [(e['candidateId'][-8:], e['opinion'], e['reason']) for e in E]
print('涵蓋自報：主篩 %d 筆' % len(E))
print()

SEQ = [('檢索雜訊', r'檢索雜訊累計第 (\d+) 筆'),
       ('gel 詞族', r'gel. 詞族至此 (\d+) 筆'),
       ('cycle 詞族誤命中', r'cycle. 詞族誤命中第 (\d+) 筆'),
       ('非人類生物體', r'非人類生物體第 (\d+) 例'),
       ('健美語料', r'健美語料第 (\d+) 筆'),
       ('立陶宛樣本', r'立陶宛樣本第 (\d+) 筆'),
       ('帆船／風浪板語料', r'帆船／風浪板語料第 (\d+) 筆'),
       ('安慰劑載體是CHO', r'安慰劑載體是 CHO.{0,12}第 (\d+) 例')]
for lab, pat in SEQ:
    v = [int(m.group(1)) for _, _, t in rec for m in re.finditer(pat, t)]
    print('  %-16s 命中 %3d 次，最大號 %s' % (lab, len(v), max(v) if v else '—'))
print()

KEY = [('肌酸 creatine', r'肌酸'),
       ('游泳 swimming（n+66 後）', r'游泳'),
       ('左旋肉鹼 carnitine', r'肉鹼'),
       ('高蛋白與腎功能', r'腎功能|高蛋白.{0,8}腎'),
       ('月經週期', r'月經週期|黃體期'),
       ('抗疲勞多醣動物模型', r'抗疲勞'),
       ('臥床 bed rest', r'臥床'),
       ('葡萄糖耐受測驗 OGTT', r'口服葡萄糖耐受|OGTT')]
for lab, pat in KEY:
    h = [r for r in rec if re.search(pat, r[2])]
    print('%-24s %4d 筆 %s' % (lab, len(h),
                              dict(collections.Counter(r[1] for r in h))))
    for s, op, rs in h[-2:]:
        print('     %s %-8s %s' % (s, op, rs[:230].replace('\n', ' ')))
    print()
