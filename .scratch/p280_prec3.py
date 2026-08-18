# -*- coding: utf-8 -*-
"""p280 第三批族序號量測（凡本輪要寫「第 N 筆」者一律先量）。"""
import io
import json
import re
import collections

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
rec = [(e['candidateId'][-8:], e['opinion'], e['reason']) for e in E]

SEQ = [('學位論文累計', r'學位論文累計第 (\d+) 筆'),
       ('標題指向入局型', r'「標題指向入局」型第 (\d+) 筆'),
       ('無訓練程度形容詞', r'無訓練程度形容詞[^；。]{0,10}第 (\d+) 筆'),
       ('葡萄牙文文獻', r'葡萄牙文文獻第 (\d+) 筆'),
       ('蜂蜜語料', r'蜂蜜語料第 (\d+) 筆'),
       ('橄欖球語料', r'橄欖球語料第 (\d+) 筆'),
       ('碳水漱口案例', r'碳水漱口案例累計第 (\d+) 筆'),
       ('多醣作為工程材料', r'多醣作為工程材料'),
       ('methodological 累計', r'`\[methodological\]` 累計第 (\d+) 筆')]
for lab, pat in SEQ:
    v = [int(m.group(1)) for _, _, t in rec for m in re.finditer(pat, t)
         if m.groups()]
    n = sum(1 for _, _, t in rec if re.search(pat, t))
    print('  %-20s 出現於 %3d 筆，最大號 %s'
          % (lab, n, max(v) if v else '（無編號）'))

print()
for lab, pat in [('泰文文獻', r'泰文'), ('芬蘭文文獻', r'芬蘭文'),
                 ('咖啡因劑量反應', r'咖啡因.{0,10}劑量反應|劑量反應.{0,10}咖啡因'),
                 ('學校肥胖防治', r'學童.{0,8}肥胖|校園.{0,8}介入'),
                 ('淚液/眼科', r'淚液|眼科'),
                 ('兒童運動表現試驗', r'兒童.{0,12}運動表現|學童.{0,8}騎乘')]:
    h = [r for r in rec if re.search(pat, r[2])]
    print('%-16s %4d 筆 %s' % (lab, len(h),
                              dict(collections.Counter(r[1] for r in h))))
    for s, op, rs in h[-2:]:
        print('     %s %-8s %s' % (s, op, rs[:200].replace('\n', ' ')))
