# -*- coding: utf-8 -*-
"""🚨 n+59 檢索雜訊族之告警由 4 處增為 8 處——查是真錯號還是排序假象。

⚠️ `n59_counters.py` 依 **judgements.json 之 append 順序**檢查遞增性。
上輪併入的 200 筆抽驗是**隨機抽樣順序**，而我編號時用的是
**worksheet 順序**（`n70_apply.py` 依 worksheet 排序輸出）。
**兩者不同，故序號在 append 順序下看起來會亂跳。**

🚨 但「看起來會亂跳」不等於「沒有真錯號」。本檔把兩者分開：
  （甲）**排序假象**：號碼在 worksheet 順序下是遞增的；
  （乙）**真錯號**：在 worksheet 順序下也不遞增。

⚠️ 第 337 輪教訓：頁 273 的 off-by-one 就是真錯號，
**不能因為「這次有排序因素」就假設全部都是假象。**
"""
import io
import json
import re

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
seq_of = {it['candidateId']: i for i, it in enumerate(w['items'], start=1)}
page_of = {it['candidateId']: it['page'] for it in w['items']}

PAT = re.compile(r'檢索雜訊累計第 (\d+) 筆')
rows = []
for order, e in enumerate(E):
    for m in PAT.finditer(e['reason']):
        rows.append({'short': e['candidateId'][-8:],
                     'appendOrder': order,
                     'seq': seq_of[e['candidateId']],
                     'page': page_of[e['candidateId']],
                     'num': int(m.group(1))})
print('檢索雜訊族共 %d 筆編號' % len(rows))
print()


def nonmono(items, key):
    bad = []
    prev = None
    for r in sorted(items, key=lambda x: x[key]):
        if prev is not None and r['num'] <= prev['num']:
            bad.append((prev, r))
        prev = r
    return bad


a = nonmono(rows, 'appendOrder')
b = nonmono(rows, 'seq')
print('依 **append 順序**（n59_counters 之視角）非遞增：%d 處' % len(a))
for p, r in a:
    print('   %s(p%d,seq%d,#%d) -> %s(p%d,seq%d,#%d)'
          % (p['short'], p['page'], p['seq'], p['num'],
             r['short'], r['page'], r['seq'], r['num']))
print()
print('依 **worksheet 順序**（編號時之實際依據）非遞增：%d 處' % len(b))
for p, r in b:
    print('   🚨 %s(p%d,seq%d,#%d) -> %s(p%d,seq%d,#%d)'
          % (p['short'], p['page'], p['seq'], p['num'],
             r['short'], r['page'], r['seq'], r['num']))
print()
if len(b) < len(a):
    print('⚠️ 差額 %d 處為**排序假象**：抽驗 200 筆以隨機順序 append，'
          % (len(a) - len(b)))
    print('   而編號依 worksheet 順序，故 append 視角下看似倒退。')
print('🚨 worksheet 順序下仍非遞增者才是真錯號，需逐筆登記。')
