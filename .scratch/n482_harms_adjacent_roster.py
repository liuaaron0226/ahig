# -*- coding: utf-8 -*-
"""n+129（四）派工：harms 相鄰素材之三欄名冊。

## 判準照抄裁定，不重述、不擴張

| 類別 | 判準 |
|---|---|
| **收錄** | ①有 `candidateId`；②看板有明確之納入動作；③**累計數因它而前進**（「增至 N 筆」） |
| **候補** | 明載為候補或「不計入正式清單」者，**另立一欄，🚫 不併入收錄數** |
| **僅為形容** | 稱某筆「屬 harms 相鄰」而**無納入動作或無 `candidateId`** |

**🚨 判準之核心是第三項**：累計數的移動就是「接受」的紀錄。
**⚠️ 「建議納入」是執行室的動作，「接受」是協調者的動作，兩者不同。**

## 🚨 本檔不做的事

**🚫 不給任何合計數。** n+129 明訂：累計數自 10 之後停止維護
（看板 21985 為最後一次「增至 N 筆」），**故其後各筆無累計數移動可查，
一律歸候補，待協調者逐筆裁定後方能進收錄數。**
**⚠️ 本檔給的是三欄之內容，不是三欄之數字。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：看板上每一處「harms 相鄰」之行號、其鄰近之 `candidateId`、
  以及該處是否伴隨累計數移動或候補字樣。
- 🚨 查不到：**某筆是否「實質上」屬於 harms 相鄰**——⚠️ 那是判讀，不是檢索。
  **🚫 本檔只依紀錄之形式分欄，不代為判斷內容。**
- ⚠️ 前綴取自看板行文中之 8 碼短碼，**🚨 未回查 queue 驗證其存在**
  （該驗證需私有根，且不影響分欄）。
"""
import io
import json
import re
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

BOARD = 'COORDINATION.md'
L = open(BOARD, 'rb').read().decode('utf-8').replace('\r\n', '\n').split('\n')
ID = re.compile(r'`([0-9a-f]{8})`')
# 累計數「移動」之樣式——🚨 必須含「增至」。
# ⚠️ 初版把「增至」設為選用，於是把複述（「harms 相鄰素材 10 筆」）
#    也算成移動，連 n+129 自己引用歷史的那一行都被算進去，
#    使「最後一次移動」由 21985 誤判為 68130。
# ✅ 收緊後之結果與 n+129 四所載一致：最後一次移動為看板 21985。
BUMP = re.compile(r'harms 相鄰素材\s*(?:由\s*\d+\s*筆\s*)?增至\s*(\d+)\s*筆')
RESERVE = re.compile(r'候補|不計入正式清單')

mentions = [(k + 1, l) for k, l in enumerate(L) if 'harms 相鄰' in l]
bumps = [(n, int(BUMP.search(t).group(1))) for n, t in mentions if BUMP.search(t)]
last_bump_line = max(n for n, _ in bumps) if bumps else 0
last_bump_val = dict(bumps).get(last_bump_line)

included, reserve, descriptive = [], [], []
seen = set()
for n, text in mentions:
    ctx = '\n'.join(L[max(0, n - 4):n + 3])
    ids = [i for i in ID.findall(ctx)]
    bumped = bool(BUMP.search(text))
    is_reserve = bool(RESERVE.search(ctx))
    for cid in ids:
        key = (cid, n)
        if key in seen:
            continue
        seen.add(key)
        rec = {'idPrefix': cid, 'boardLine': n,
               'excerpt': text.strip()[:110]}
        if is_reserve:
            rec['why'] = 'board marks it 候補 / 不計入正式清單'
            reserve.append(rec)
        elif bumped and n <= last_bump_line:
            rec['why'] = 'running total advanced at this line'
            included.append(rec)
        elif n > last_bump_line:
            rec['why'] = ('after the last running-total advance (line %d); '
                          'no advance to attribute it to' % last_bump_line)
            reserve.append(rec)
        else:
            rec['why'] = 'no inclusion action and no running-total advance'
            descriptive.append(rec)
    if not ids:
        descriptive.append({'idPrefix': None, 'boardLine': n,
                            'excerpt': text.strip()[:110],
                            'why': 'no candidateId in context'})

print('=== harms 相鄰素材：三欄名冊（🚫 不給合計數，n+129 四）===')
print('看板提及「harms 相鄰」之行：%d' % len(mentions))
print('累計數移動之處：%s' % [f'{n}行→{v}筆' for n, v in bumps])
print('最後一次移動：第 %d 行（%s 筆）——🚨 其後各筆一律歸候補' % (last_bump_line, last_bump_val))
print()
for name, rows in (('✅ 收錄', included), ('⏸ 候補', reserve), ('🚫 僅為形容', descriptive)):
    print('%s（%d 項）' % (name, len(rows)))
    for r in rows[:8]:
        print('   %-10s 第 %5s 行  %s' % (r['idPrefix'] or '（無 id）',
                                          r['boardLine'], r['why'][:52]))
    if len(rows) > 8:
        print('   …另 %d 項，見產物' % (len(rows) - 8))
    print()
print('🚨 三欄之項數不得相加為「harms 相鄰素材共 N 筆」——')
print('   ⚠️ 候補須待協調者逐筆裁定後方能進收錄數（n+129 四）。')

doc = {
    'schemaVersion': 1,
    'documentType': 'harms-adjacent-roster',
    'ruling': 'n+129(4): three columns, criterion quoted verbatim, no total',
    'population': 'every line of COORDINATION.md containing "harms 相鄰"',
    'countingUnit': 'mention (an id may appear at several lines)',
    'criterion': {
        'included': 'has a candidateId, an explicit inclusion action, and the '
                    'running total advances at that line',
        'reserve': 'marked 候補 or 不計入正式清單, or appearing after the last '
                   'running-total advance so no advance can be attributed',
        'descriptive': 'called harms-adjacent with no inclusion action or no '
                       'candidateId',
    },
    'lastRunningTotal': {'line': last_bump_line, 'value': last_bump_val},
    'runningTotalAdvances': [{'line': n, 'value': v} for n, v in bumps],
    'included': included,
    'reserve': reserve,
    'descriptive': descriptive,
    'noTotalNote': 'n+129(4) forbids any total until the coordinator rules on '
                   'the reserve column record by record. The three column '
                   'lengths must not be added together and presented as a count '
                   'of harms-adjacent material.',
    'coverageStatement': 'Classifies by the form of the record, not by whether a '
                         'record is substantively harms-adjacent, which is a '
                         'judgement rather than a search. Id prefixes are taken '
                         'from board prose and not verified against the queue.',
    'contentNote': 'Id prefixes, line numbers and short excerpts of coordination '
                   'prose. No literature content.',
}
doc['rosterHash'] = content_hash({'included': included, 'reserve': reserve})
io.open('.scratch/n482_harms_adjacent_roster.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → .scratch/n482_harms_adjacent_roster.json')
