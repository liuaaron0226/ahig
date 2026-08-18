# -*- coding: utf-8 -*-
"""🚨 更正 n71_seqaudit.py 的框架：我把「該用哪個順序」搞反了。

第一版我寫「編號依 worksheet 順序，故 append 視角下看似倒退」，
**實測結果打臉：worksheet 順序下有 21 處非遞增，比 append 順序的 8 處更多。**

**想清楚之後**：「檢索雜訊**累計**第 N 筆」是一個**寫判讀時遞增的流水號**，
**它的正確檢查順序就是 append 順序**——`n59_counters.py` 用的正是這個，
**它沒錯，錯的是我第一版的框架。**（worksheet 順序下那 12 處 p155–p182
的落差是**跳頁補判**造成的：那些頁的部分記錄早判、部分晚判。）

本檔查真正的問題：**那 200 筆抽驗記錄，我編號時用的是「抽驗樣本順序」，
而 `n70_apply.py` 是依「worksheet 順序」寫出去的**——若兩者不同，
流水號在 append 順序下就會亂。本檔量測這件事。
"""
import glob
import io
import json
import re

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
seq_of = {it['candidateId']: i for i, it in enumerate(w['items'], start=1)}

s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
sample_pos = {c[-8:]: i for i, c in enumerate(s['sample']['candidateIds'])}

PAT = re.compile(r'檢索雜訊累計第 (\d+) 筆')
tail = []
for order, e in enumerate(E):
    short = e['candidateId'][-8:]
    if short not in sample_pos:
        continue
    for m in PAT.finditer(e['reason']):
        tail.append({'short': short, 'appendOrder': order,
                     'samplePos': sample_pos[short],
                     'seq': seq_of[e['candidateId']],
                     'num': int(m.group(1))})
print('抽驗 200 筆中，帶「檢索雜訊累計第 N 筆」者：%d 筆' % len(tail))
print()


def check(items, key, label):
    bad = []
    prev = None
    for r in sorted(items, key=lambda x: x[key]):
        if prev is not None and r['num'] <= prev['num']:
            bad.append((prev, r))
        prev = r
    print('依 %s 排序：非遞增 %d 處' % (label, len(bad)))
    for p, r in bad:
        print('   %s(#%d) -> %s(#%d)'
              % (p['short'], p['num'], r['short'], r['num']))
    return bad


b_sample = check(tail, 'samplePos', '**抽驗樣本順序**（我編號時之依據）')
print()
b_append = check(tail, 'appendOrder', '**append 順序**（n59 之視角）')
print()

if not b_sample and b_append:
    print('🚨 結論：號碼本身連續無誤，是**寫出順序與編號順序不一致**。')
    print('   我在 `n70_apply.py` 依 worksheet 順序輸出（為了與頁面判讀')
    print('   一致、且有 assert 把關），但**編號是逐塊按抽驗樣本順序給的**。')
    print('   ⚠️ 兩個決定各自都對，**放在一起才出問題**——')
    print('      這與第 337 輪頁 273 之 off-by-one **不同型**：')
    print('      那次是號碼真的錯，這次是號碼對而順序被重排。')
    print()
    print('   🚨 但後果一樣需要登記：M1 稽核若照 judgements.json 順序讀，')
    print('      會看到 7 處倒退。**judgements.json 為 append-only，不重寫。**')
elif b_sample:
    print('🚨 抽驗樣本順序下也非遞增——**那是真錯號**，需逐筆登記。')
