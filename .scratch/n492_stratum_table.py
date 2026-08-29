# -*- coding: utf-8 -*-
"""層別筆數之常設產生指令——兩個母體並列，每個數字自帶來源。

## 🚨 為什麼要有這支

本室在同一個層（S5+S6）之筆數上**連續兩輪出錯**：

- 第 490 輪寫「在手 6」——⚠️ 該數出自第 466 輪之表（母體乙），
  而同句所引之版本數出自 `n489`（母體甲），**🚨 分子與分母不同母體。**
- 且「6」在母體乙內**亦已過期**（登錄後為 7）——**⚠️ 狀態變了而描述沒跟著變。**

**🚨 兩次都是臨時手算，而臨時手算不會自己指出它用了哪個母體。**
n+142 據此立為義務：**報告中每一個層別筆數須註明其取自哪一份產物。**

**⚠️ 本檔即為履行該義務之機制**：一次算出兩個母體，並在輸出中標明各欄之來源檔。

## 兩個母體之定義（🚫 不可互代）

| 欄 | 母體 | 來源 |
|---|---|---|
| **甲** | **原始校準集 60** | `.scratch/m1_step3_inventory.json` 之 `records` |
| **乙** | **校準集 60 ＋ n+103 遞補** | 校準集抽出 ＋ backfill 之 accepted，逐筆現查 manifest |

**⚠️ 甲之分母是契約所定之 60；乙之分母是遞補後實際處理之集合。**
**🚨 版本分布（`n489`）之母體是甲——故任何「版本 ÷ 在手」之比例，分母只能取甲欄。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：兩個母體下各層之 `acquired` 筆數，及甲欄之版本細分。
- 🚨 查不到：**乙欄之版本細分**——⚠️ `n489` 只涵蓋甲，本檔不外推。
- ⚠️ 乙欄以 manifest 現查，**🚨 故其值會隨登錄而變；甲欄則隨盤點重跑而變。**
  **兩者皆非凍結值，引用時須併記查取輪次。**
"""
import io
import json
import os
import sys
from collections import Counter

sys.path.insert(0, 'ahig')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
from ahig.search.fulltext import _artifact_dir  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
inv = json.load(io.open(S + 'm1_step3_inventory.json', encoding='utf-8'))
bf = json.load(io.open(S + 'm1_step3_backfill.json', encoding='utf-8'))
cal = json.load(io.open(S + 'm1_step2_calibration_set.json', encoding='utf-8'))
ver = {r['idFrag']: r['version'] for r in
       json.load(io.open(S + 'n489_calibration_versions.json',
                         encoding='utf-8'))['records']}

# ── 甲：原始校準集 60 ────────────────────────────────────────────
a = Counter(r.get('poolId') for r in inv['records'] if r['status'] == 'acquired')
a_ver = {}
for r in inv['records']:
    if r['status'] != 'acquired':
        continue
    v = ver.get(r['candidateId'].split(':')[-1][:16], '不明')
    a_ver.setdefault(r.get('poolId'), Counter())[v] += 1

# ── 乙：校準集 60 ＋ n+103 遞補 ──────────────────────────────────
pool = {}
for pid, d in cal['draws'].items():
    for c in d['candidateIds']:
        pool[c] = pid
for p in bf['pools']:
    for r in (p.get('backfilled') or []):
        if r.get('accepted'):
            pool[r['candidateId']] = p['poolId']
b = Counter()
for cid, pid in pool.items():
    m = _artifact_dir(cid) / 'manifest.json'
    if m.exists() and json.load(io.open(m, encoding='utf-8')).get('status') == 'acquired':
        b[pid] += 1

quota = {p['poolId']: p['quota'] for p in bf['pools']}
order = [p['poolId'] for p in bf['pools']]

print('=== 層別 acquired：兩個母體並列（🚫 不可互代）===')
print('甲 ← .scratch/m1_step3_inventory.json（原始校準集 60）')
print('乙 ← 校準集抽出 ＋ backfill accepted，逐筆現查 manifest（60 ＋ 遞補）')
print()
print('%-32s %6s %6s %6s   %s' % ('層', '配額', '甲', '乙', '甲欄之版本細分'))
print('-' * 96)
rows = []
for pid in order:
    vs = a_ver.get(pid, Counter())
    detail = '／'.join('%s %d' % (k.replace('Version', ''), n)
                       for k, n in sorted(vs.items())) or '—'
    print('%-32s %6d %6d %6d   %s' % (pid, quota[pid], a.get(pid, 0), b.get(pid, 0), detail))
    rows.append({'pool': pid, 'quota': quota[pid],
                 'acquiredCalibration60': a.get(pid, 0),
                 'acquiredWithBackfill': b.get(pid, 0),
                 'versionsCalibration60': dict(vs)})
print('-' * 96)
print('%-32s %6d %6d %6d' % ('合計', sum(quota.values()), sum(a.values()), sum(b.values())))
print()
usable = sum(n for pid in order for k, n in a_ver.get(pid, Counter()).items()
             if k != 'submittedVersion')
marked = sum(n for pid in order for k, n in a_ver.get(pid, Counter()).items()
             if k == 'acceptedVersion')
print('🚨 甲欄之可數值萃取者 %d 筆（🚫 扣除 submittedVersion）；'
      '其中 %d 筆須逐值標記為作者稿（n+138 三）。' % (usable, marked))
print('⚠️ 乙欄無版本細分——🚨 `n489` 只涵蓋甲，本檔不外推。')

doc = {
    'schemaVersion': 1,
    'documentType': 'per-stratum-acquired-two-populations',
    'ruling': 'n+142: every per-stratum figure must name the artefact it comes from',
    'population': 'two, deliberately kept apart',
    'countingUnit': 'record',
    'criterion': {
        'calibration60': "status acquired among m1_step3_inventory.json records",
        'withBackfill': 'status acquired, read live from each manifest, over the '
                        'calibration draw plus accepted backfill',
    },
    'rows': rows,
    'totals': {'quota': sum(quota.values()), 'calibration60': sum(a.values()),
               'withBackfill': sum(b.values())},
    'numericallyUsableCalibration60': usable,
    'requiringPerValueMarking': marked,
    'whyThisExists': 'The same stratum was misreported in two consecutive rounds, '
                     'both times by computing the table by hand: once mixing the '
                     'two populations in a single sentence, once quoting a figure '
                     'that registration had already moved. A hand computation does '
                     'not say which population it used.',
    'coverageStatement': 'Version detail exists only for the calibration 60, so no '
                         'ratio may take its numerator from the version counts and '
                         'its denominator from the backfill column. Neither column '
                         'is frozen -- the first moves when the inventory is '
                         're-run, the second when records are registered -- so '
                         'cite the round alongside the number.',
    'contentNote': 'Pool ids and counts only.',
}
doc['tableHash'] = content_hash(doc['rows'])
io.open(S + 'n492_stratum_table.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn492_stratum_table.json' % S)
