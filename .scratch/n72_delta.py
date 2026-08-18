# -*- coding: utf-8 -*-
"""第三態上線前後之差異量測——**回報實際變了什麼，不憑印象**。

⚠️ 上輪（排除清單）與本輪（第三態）之序列長度不同：7025 vs 7021。
差 4 筆——那是 p280／p281 已推進到、原本會「自動納回」的抽驗記錄。
**第三態把它們永久留在外面，故不再納回。**

本檔逐項列出差異並解釋每一項，避免我在心跳裡寫出未經量測的說法。
"""
import io
import json
import os
import sys

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score  # noqa: E402

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
AUDIT = 'n+57 尾端抽驗（200 筆隨機抽樣）'

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
for name in ('post-ruling-reclassification.json',
             'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + name
    if os.path.exists(p):
        for e in json.load(io.open(p, encoding='utf-8'))['entries']:
            op[e['candidateId']] = e['effectiveDecision']

by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
contiguous = 0
while all(c in op for c in by_page.get(contiguous + 1, [None])):
    contiguous += 1

doc = json.load(io.open(OUT + '/p-score-sequence-exclusions.json',
                        encoding='utf-8'))
audit = [e for e in doc['entries'] if e.get('source') == AUDIT]
temp = [e for e in doc['entries'] if e.get('source') != AUDIT]
print('排除清單共 %d 筆：抽驗批 %d、原跳頁補判 %d'
      % (len(doc['entries']), len(audit), len(temp)))
reached = [e for e in audit if e['page'] <= contiguous]
print('抽驗批中，頁碼已被逐頁推進涵蓋者：%d 筆 %s'
      % (len(reached), [e['candidateId'][-8:] for e in reached]))
print('  ⚠️ 舊制（排除清單）會把這 %d 筆納回序列；'
      '第三態則永久留在外面。' % len(reached))
print()

N = w['itemCount']


def seq(skip):
    lab = [1 if op[it['candidateId']] in ('advance', 'unclear') else 0
           for it in w['items']
           if it['candidateId'] in op and it['candidateId'] not in skip]
    return p_score(lab, N)


old_skip = {e['candidateId'] for e in doc['entries']
            if e['page'] > contiguous}
new_skip = {e['candidateId'] for e in audit} | {
    e['candidateId'] for e in temp if e['page'] > contiguous}
o, n = seq(old_skip), seq(new_skip)
print('%-28s %-10s %-10s' % ('', '舊制（排除清單）', '新制（第三態）'))
for k in ('screenedCount', 'relevantFound', 'windowSize', 'pScore'):
    print('  %-24s %-14s %s' % (k, o[k], n[k]))
print()
print('⚠️ 差 %d 筆序列長度，即上列已被涵蓋之抽驗記錄。'
      % (o['screenedCount'] - n['screenedCount']))
print('🚨 方向：pScore %.6f -> %.6f（%s）'
      % (o['pScore'], n['pScore'],
         '上升，更難停' if n['pScore'] > o['pScore'] else '下降，更易停'))
print('   ⚠️ 這不是設計目標，只是本批記錄恰好落在此處之結果；')
print('      第三態之定義理由是語意（獨立稽核 vs 循序篩選），不是方向。')
