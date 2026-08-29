# -*- coding: utf-8 -*-
"""庚節（harms）四格佔位符之值、產生指令與 file_hash——n+119 現況查詢第二項。

## 交付什麼

| 佔位符 | 值 | 來源 |
|---|---|---|
| `HARMS_S5_QUOTA` | **8** | `ahig/calibration/b11-carbohydrate/strata.json`（**✅ 受追蹤**） |
| `HARMS_S6_QUOTA` | **7** | 同上 |
| `HARMS_COMBINED` | **15** | 上二者之和；並與 `.scratch/m1_step2_assignment.json` 之合併池配額交叉核對 |
| `HARMS_ADJACENT_N` | **🚨 無權威值** | 見下 |

**⚠️ `HARMS_S5_ACTUAL` 不在此列**——它全文取得後才存在（協調者已載明）。

## 🚨 `HARMS_ADJACENT_N`：它從來沒有名冊，只有一個停止維護的累計數

骨架之來源欄寫「harms 相鄰素材名單，交付時現算（本 run 內曾 4→5→6）」。

**⚠️ 兩處都不準確**：
1. **沒有「名單」這個檔案**——⚠️ 已搜遍受追蹤檔與私有根，只有看板散文。
2. **「曾 4→5→6」本身已過期**——🚨 看板實際走到 **10**（第 21985／22276 行）。

**🚨 而累計數自第 22276 行後就沒有再更新**，其後仍有多處記入新的 harms 相鄰觀察。
以「該處前後兩行內出現之 8 碼 candidateId 前綴」為判準，其後另有 **12 個相異 id**。

**故下界為 10 ＋ 12 ＝ 22**，**⚠️ 且這是下界不是值**：
🚨 部分提及可能指同一筆、部分段落未帶 id、部分「harms 相鄰」是形容而非收錄。

**⚠️ 這與第 447 輪之「期望漏失約 10 筆」同型**：
**散文裡的累計數，維護停止時不會有任何訊號。**
**🚨 差別在於前者尚有底數可重算，本項連名冊都沒有，🚫 故本室不給單一數字。**

**建議**：比照 `n97_errata_roster.json` 之作法建一份名冊檔，使其有產生指令；
**⚠️ 收錄判準須先裁定**（「屬 harms 相鄰」在看板上同時被用作**收錄**與**形容**）。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：strata 之配額、其 `file_hash`、看板累計數之最後明載處與其後之相異 id 數。
- 🚨 查不到：**哪些提及構成「收錄」**——⚠️ 那是判準問題，須人讀且須先有判準。
"""
import io
import json
import re
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import file_hash  # noqa: E402

STRATA = 'ahig/calibration/b11-carbohydrate/strata.json'
raw = open(STRATA, 'rb').read()
# 🚨 鍵名以實際傾印為準：本檔初版猜 'id'，實際是 'stratumId'——
#    ⚠️ 而本室前一支探測腳本本來就寫了 `s.get('id') or s.get('stratumId')`，
#    🚨 寫這支時卻只挑了一個。猜鍵名，本 run 第三次。
strata = {s['stratumId']: s for s in json.loads(raw.decode('utf-8'))['strata']}
s5 = strata['S5-gi-harms-primary']['quota']
s6 = strata['S6-gi-harms-secondary-only']['quota']

asg = json.load(io.open('.scratch/m1_step2_assignment.json', encoding='utf-8'))
merged = [p for p in asg['pools'] if p['poolId'] == 'S5+S6-gi-merged'][0]['quota']

print('=== 庚節四格 ===')
print('   HARMS_S5_QUOTA   = %d   ← %s → strata[S5-gi-harms-primary].quota' % (s5, STRATA))
print('   HARMS_S6_QUOTA   = %d   ← 同上 S6-gi-harms-secondary-only' % s6)
print('   HARMS_COMBINED   = %d   ← %d + %d；合併池配額 %d  %s'
      % (s5 + s6, s5, s6, merged, '✅ 交叉核對相符' if s5 + s6 == merged else '🚨 不符'))
print('   file_hash(strata.json) = %s' % file_hash(raw))
print('   ⚠️ 該檔**受版控追蹤**，協調者可自行覆核，🚫 不必倚賴本室量測。')

# ── HARMS_ADJACENT_N ────────────────────────────────────────────
L = open('COORDINATION.md', 'rb').read().decode('utf-8').replace('\r\n', '\n').split('\n')
ID = re.compile(r'`([0-9a-f]{8})`')
totals = [(i + 1, l.strip()) for i, l in enumerate(L)
          if re.search(r'harms 相鄰素材\s*(增至\s*)?\d+\s*筆', l)]
last_line, last_text = totals[-1]
# 🚨 初版以 r'(\d+)\s*筆' 取數，而該行為「EAH 素材 2 筆、harms 相鄰素材 10 筆」，
#    ⚠️ 於是取到行內第一個數字 2 而非 10。改為錨定在「harms 相鄰素材」之後。
last_n = int(re.search(r'harms 相鄰素材\s*(?:增至\s*)?(\d+)\s*筆',
                       last_text).group(1))
after = {}
for i, l in enumerate(L):
    if i + 1 <= last_line or 'harms 相鄰' not in l:
        continue
    for m in ID.findall(' '.join(L[max(0, i - 2):i + 3])):
        after.setdefault(m, i + 1)

print()
print('=== HARMS_ADJACENT_N ===')
print('   累計數最後明載：第 %d 行「%d 筆」' % (last_line, last_n))
print('   其後仍提及 harms 相鄰之處，帶有相異 candidateId 前綴 %d 個' % len(after))
print('   🚨 下界 = %d + %d = %d（⚠️ 下界不是值）' % (last_n, len(after), last_n + len(after)))
print('   🚨 無名冊檔——已搜遍受追蹤檔與私有根，只有看板散文。')

doc = {
    'schemaVersion': 1,
    'documentType': 'harms-section-placeholder-values',
    'ruling': 'n+119 status query item 2; values, producing commands and hashes',
    'population': 'the 庚 (harms) skeleton placeholders the coordinator listed',
    'countingUnit': 'placeholder',
    'criterion': 'value read from the named field of a tracked file, or, where '
                 'no file exists, a stated lower bound with its method',
    'values': {
        'HARMS_S5_QUOTA': {'value': s5, 'source': STRATA,
                           'path': 'strata[S5-gi-harms-primary].quota',
                           'tracked': True, 'fileHash': file_hash(raw)},
        'HARMS_S6_QUOTA': {'value': s6, 'source': STRATA,
                           'path': 'strata[S6-gi-harms-secondary-only].quota',
                           'tracked': True, 'fileHash': file_hash(raw)},
        'HARMS_COMBINED': {'value': s5 + s6, 'derivation': 'S5 + S6',
                           'crossCheck': 'm1_step2_assignment.json pool '
                                         'S5+S6-gi-merged quota = %d' % merged,
                           'matches': s5 + s6 == merged},
        'HARMS_ADJACENT_N': {
            'value': None,
            'lowerBound': last_n + len(after),
            'lastStatedTotal': {'line': last_line, 'value': last_n},
            'distinctIdsAfter': len(after),
            'idsAfter': after,
            'why': 'There is no roster file. The count existed only as a '
                   'running total in board prose, and that total stopped being '
                   'updated after the line above while further harms-adjacent '
                   'observations kept being recorded.',
            'skeletonNoteStale': 'The skeleton source column says the run went '
                                 '4 to 5 to 6; the board actually reached 10.',
            'sameFamilyAs': 'round 447, the expected-miss figure -- a prose '
                            'running total gives no signal when maintenance '
                            'stops. Worse here: that one still had a base to '
                            'recompute from; this has no roster at all.',
            'recommendation': 'Build a roster file as was done for the errata '
                              'roster, so the count has a producing command. '
                              'The inclusion criterion needs ruling first: '
                              '"harms-adjacent" is used on the board both to '
                              'admit a record and merely to describe one.',
        },
    },
    'notProvided': {'HARMS_S5_ACTUAL': 'exists only after full text is '
                                       'obtained; the coordinator excluded it'},
    'coverageStatement': 'Quotas are read from a tracked file and can be '
                         'checked independently. The adjacent count is a lower '
                         'bound with its method stated, not a value.',
    'contentNote': 'Quotas, counts, id prefixes and line numbers only.',
}
io.open('.scratch/n451_harms_placeholders.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → .scratch/n451_harms_placeholders.json')
sys.exit(0 if s5 + s6 == merged else 1)
