# -*- coding: utf-8 -*-
"""p280 之關鍵先例：外文標題學位論文（無摘要）之判法，與環糊精補充試驗。"""
import io
import json
import re
import collections

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
ti = {it['candidateId']: (it.get('title') or '') for it in w['items']}
by = {e['candidateId'][-8:]: e for e in E}

print('== 學位論文 + title-only + advance/unclear 之寫法 ==')
h = [e for e in E
     if re.search(r'dissertation|學位論文', e['reason'])
     and re.search(r'title-only-judged|無摘要', e['reason'])]
print('共 %d 筆 %s' % (len(h), dict(collections.Counter(
    e['opinion'] for e in h))))
for e in h[-3:]:
    print('--', e['candidateId'][-8:], e['opinion'])
    print('  ', e['reason'][:700].replace('\n', ' '))
    print()

print('== 環狀糊精／支鏈環糊精（HBCD）作為受測補給品 ==')
h2 = [e for e in E if re.search(r'支鏈環糊精|高分子量碳水|HBCD|cluster ?dextrin',
                                e['reason'], re.I)]
print('共 %d 筆 %s' % (len(h2), dict(collections.Counter(
    e['opinion'] for e in h2))))
for e in h2[:4]:
    print('--', e['candidateId'][-8:], e['opinion'], '|',
          ti[e['candidateId']][:70])
    print('  ', e['reason'][:330].replace('\n', ' '))
