# -*- coding: utf-8 -*-
"""n+94（三）：影子 300 筆 vs 正式三個 lane 之全量比對。

## 🚨 要回答的問題（看板 22769 之原始提請）

> **影子回合工作單內，是否還有其他不帶 `critical-harms-signal` 旗標的紀錄
> 同樣落在正式層之外？若有，代表分派存在系統性漏口。**

**已對帳者只有 `standard-screening`**（n+86 三：9,260 − 9,091 ＝ 169，實查為影子樣本）。
**⚠️ n+94 三明載：不把「標準線對得起來」推廣為「三個 lane 都對得起來」**
——**🚨 那會被讀成「已全面驗證無漏口」，而 safety 與 critical-harms 從未做過。**

## 已知之漏口機制（n+94 二）

> **以 lane 分派工作單、以 flag 補救死角，兩套規則的交集處出現漏口。**

孤兒紀錄之特徵：`screeningLane` 為 `standard-screening`、理應進標準線工作單卻不在其中；
同時帶 `critical-harms-signal`、**卻也不在非標準線名單內——因為那份名單以
「lane ≠ standard」為條件。**

## 本檔之做法

對影子 300 筆逐一查：**其 lane 對應之正式工作單是否收錄它**。
**⚠️ 不預設「哪個 lane 對應哪份工作單」**——先列出私有根中所有 worksheet
及其筆數，**再以 lane 分派，並把對應關係寫進產物**（🚨 對應關係本身就是被檢查的對象）。

⚠️ 輸出只有計數與不透明 id，零文獻內容。
"""
import io
import json
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

RUN = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
       'b11-exogenous-cho-endurance/b11-full-run')
DEST = '.scratch/n94_three_lane_reconcile.json'

# ── 先盤出所有正式工作單，不預設 ────────────────────────────────────
sheets = {}
for d in sorted(os.listdir(RUN)):
    p = os.path.join(RUN, d, 'worksheet.json')
    if not os.path.isfile(p):
        continue
    w = json.load(io.open(p, encoding='utf-8'))
    ids = {it['candidateId'] for it in w.get('items', [])}
    sheets[d] = ids
    print('工作單 %-34s %6d 筆' % (d, len(ids)))
print()

queue = {r['candidateId']: r for r in
         json.load(io.open(RUN + '/screening-queue/queue.json',
                           encoding='utf-8'))}
shadow = [e['candidateId'] for e in
          json.load(io.open(RUN + '/screening-shadow-pass-a/judgements.json',
                            encoding='utf-8'))['entries']]
print('影子樣本 %d 筆（pass A judgements）' % len(shadow))
print()

# lane → 應收錄它的正式工作單（依名稱對應，並把對應關係落盤供覆核）
LANE_SHEET = {
    'standard-screening': ['standard-full-screen-pass-1'],
    'safety-review': ['safety-full-screen-pass-1', 'safety-full-screen-pass-2'],
    'animal-signal-review': [],
    'review-source-review': [],
    'registry-review': [],
    'identity-review': [],
}
CH = 'critical-harms-sweep'
has_ch_sheet = CH in sheets

rows, lane_c, missing = [], Counter(), []
for cid in shadow:
    r = queue.get(cid) or {}
    lane = r.get('screeningLane')
    flags = r.get('flags') or []
    lane_c[lane] += 1
    targets = LANE_SHEET.get(lane, [])
    in_any = any(cid in sheets.get(s, set()) for s in targets)
    in_ch = has_ch_sheet and cid in sheets[CH]
    # 🚨 三分類，不是二分類。本檔第一版只分「在／不在」，於是把
    #    ①該 lane 本就沒有人工工作單者、②已由 n+86 解釋之影子樣本
    #    通通算成「落在正式層之外」，得出 242 筆這個看起來很嚴重的假數字。
    # ⚠️ 22769 問的是「分派有沒有系統性漏口」，而
    #    「這個 lane 依設計不建工作單」不是漏口，「已知且已解釋」也不是。
    if not targets:
        cls = 'no-official-sheet-by-design'   # 確定性路由 lane，不建人工工作單
    elif in_any or in_ch:
        cls = 'covered'
    elif lane == 'standard-screening':
        cls = 'explained-shadow-sample'       # n+86 三：9,260−9,091=169
    else:
        cls = 'UNEXPLAINED-GAP'               # 🚨 只有這一類才是 22769 所問者
    rec = {'candidateId': cid, 'lane': lane,
           'criticalHarmsSignal': 'critical-harms-signal' in flags,
           'inLaneSheet': in_any, 'inCriticalHarmsSheet': in_ch,
           'classification': cls, 'covered': cls == 'covered',
           'sheetsChecked': targets + ([CH] if has_ch_sheet else [])}
    rows.append(rec)
    if cls == 'UNEXPLAINED-GAP':
        missing.append(rec)

print('=== 影子 300 筆之 lane 分布 ===')
for k, v in lane_c.most_common():
    print('   %-28s %4d' % (k, v))
print()
print('=== 分類（🚨 只有最後一欄是 22769 所問之漏口）===')
CLS = ['covered', 'explained-shadow-sample', 'no-official-sheet-by-design',
       'UNEXPLAINED-GAP']
by_lane = defaultdict(Counter)
for r in rows:
    by_lane[r['lane']][r['classification']] += 1
print('%-26s %8s %10s %12s %10s'
      % ('lane', '在單內', '影子樣本', '該lane無單', '未解釋漏口'))
print('-' * 72)
for lane in sorted(by_lane, key=lambda k: -sum(by_lane[k].values())):
    c = by_lane[lane]
    print('%-26s %8d %10d %12d %10d'
          % (lane, c['covered'], c['explained-shadow-sample'],
             c['no-official-sheet-by-design'], c['UNEXPLAINED-GAP']))
print('-' * 72)
tot = Counter(r['classification'] for r in rows)
print('%-26s %8d %10d %12d %10d'
      % ('合計', tot['covered'], tot['explained-shadow-sample'],
         tot['no-official-sheet-by-design'], tot['UNEXPLAINED-GAP']))

print()
if missing:
    ch_yes = sum(1 for m in missing if m['criticalHarmsSignal'])
    print('🚨 落在正式層之外者 %d 筆；其中帶 critical-harms-signal 者 %d 筆、'
          '不帶者 %d 筆' % (len(missing), ch_yes, len(missing) - ch_yes))
    print('⚠️ 22769 問的正是「不帶旗標而落在正式層之外」者——本檔算得 %d 筆。'
          % (len(missing) - ch_yes))
else:
    print('✅ 影子 300 筆全部落在正式層之內。')

doc = {
    'schemaVersion': 1,
    'documentType': 'shadow-vs-official-lane-reconcile',
    'ruling': 'n+94(3); original question at board line 22769',
    'question': ('Are there records in the shadow worksheet, without the '
                 'critical-harms-signal flag, that also fall outside the '
                 'official layer? If so, dispatch has a systematic gap.'),
    'worksheets': {k: len(v) for k, v in sheets.items()},
    'laneToSheet': LANE_SHEET,
    'laneToSheetNote': ('Mapping is recorded because it is itself under test: '
                        'the known gap mechanism is that lane-based dispatch '
                        'and flag-based rescue leave a hole at their '
                        'intersection.'),
    'criticalHarmsSheetPresent': has_ch_sheet,
    'shadowSize': len(rows),
    'laneDistribution': dict(lane_c),
    'classificationCounts': dict(Counter(r['classification'] for r in rows)),
    'classificationNote': (
        'Four classes, not two. The first version of this file compared only '
        'in-sheet versus not-in-sheet, which counted lanes that build no '
        'human worksheet by design, and the 169 shadow records n+86 already '
        'explained, as gaps -- producing a 242-record figure that looked '
        'alarming and meant nothing. Only UNEXPLAINED-GAP answers line 22769.'),
    'unexplainedGaps': missing,
    'unexplainedGapsWithoutFlag': [m for m in missing
                                   if not m['criticalHarmsSignal']],
    'records': rows,
    'contentNote': 'Opaque ids, lanes and coverage booleans only.',
}
doc['reconcileHash'] = content_hash(doc['records'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %s' % DEST)
