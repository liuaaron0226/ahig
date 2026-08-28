# -*- coding: utf-8 -*-
"""M1 產物鏈結完整性自檢——無人指派，但該做。

## 🚨 為什麼現在做

第 411–427 輪產出十餘份產物，彼此以雜湊互相引用
（`populationHash` → `assignment` → `calibrationSetHash` → `inventory`／`backfill`…）。
**⚠️ 每一份單獨看都通過，但「A 引用的 B 之雜湊」與「B 自己算出來的雜湊」是否相符，從未整批檢查過。**

**🚨 而本 run 已有兩次教訓指向同一件事**：
n+85（凍結產物之 `anchor.source` 錯標）與本室第 411 輪之發現
（凍結產物未落盤雜湊所涵蓋之全部欄位，致其無法自我驗證）
——**兩者都是「鏈結看起來在，實際驗不動」。**

**⚠️ 交付時才發現鏈斷，與現在發現，代價差很多。**

## 本檔檢查兩件事

1. **自我雜湊可重算**：產物內之 `*Hash` 欄位，以其宣稱涵蓋之子物件重算是否相符。
2. **跨產物鏈結一致**：A 所記之 `xHash` 是否等於 B 自己的 `xHash`。

**🚨 涵蓋範圍不猜**——每一項都寫明「這個雜湊算的是哪個子物件」，
⚠️ 因為本 run 之錯有一半出在「以為它涵蓋整份文件」（n+82／n+85）。
"""
import io
import json
import os
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'


def load(name):
    p = os.path.join(S, name)
    return json.load(io.open(p, encoding='utf-8')) if os.path.isfile(p) else None


# (檔名, 雜湊欄位, 該雜湊所涵蓋之子物件鍵；None 表示整份去掉該欄位)
SELF_HASHES = [
    ('m1_step2_population.json', 'populationHash', 'decisions'),
    ('m1_step2_assignment.json', 'assignmentHash', 'assignment'),
    ('m1_step2_calibration_set.json', 'calibrationSetHash', None),  # 特例，見下
    ('m1_step3_inventory.json', 'inventoryHash', 'records'),
    ('m1_step3_backfill.json', 'backfillHash', 'pools'),
    ('n85_tail_population.json', 'populationHash', 'candidateIds'),
    ('n97_errata_roster.json', 'rosterHash', 'roster'),
    ('n86_errata_originals.json', 'checkHash', 'checked'),
    ('n94_three_lane_reconcile.json', 'reconcileHash', 'records'),
    ('n92_audit_debt_union.json', 'rebuildHash', 'batches'),
    ('m1_step2_feasibility.json', 'reportHash', 'strata'),
]

print('=== 一、自我雜湊可重算 ===')
print('%-38s %-20s %s' % ('產物', '雜湊欄位', '重算'))
print('-' * 74)
self_ok = True
for fn, field, key in SELF_HASHES:
    d = load(fn)
    if d is None:
        print('%-38s %-20s 🚨 檔案不存在' % (fn, field))
        self_ok = False
        continue
    if fn == 'm1_step2_calibration_set.json':
        # ⚠️ 該檔之 hash 算的是「六池抽出之 id 全集排序後」，非任一子物件
        ids = sorted({x for v in d['draws'].values() for x in v['candidateIds']})
        got = content_hash(ids)
    else:
        got = content_hash(d[key])
    ok = got == d.get(field)
    self_ok &= ok
    print('%-38s %-20s %s' % (fn, field, '✅' if ok else '🚨 不符'))

# ── 二、跨產物鏈結 ──────────────────────────────────────────────
LINKS = [
    ('m1_step2_assignment.json', 'populationHash',
     'm1_step2_population.json', 'populationHash'),
    ('m1_step2_calibration_set.json', 'anchorHash',
     'm1_step2_population.json', 'populationHash'),
    ('m1_step3_inventory.json', 'calibrationSetHash',
     'm1_step2_calibration_set.json', 'calibrationSetHash'),
    ('m1_step3_backfill.json', 'calibrationSetHash',
     'm1_step2_calibration_set.json', 'calibrationSetHash'),
    ('m1_step2_feasibility.json', 'populationHash',
     'm1_step2_population.json', 'populationHash'),
    ('n86_errata_originals.json', 'rosterHash',
     'n97_errata_roster.json', 'rosterHash'),
]
print()
print('=== 二、跨產物鏈結一致 ===')
print('%-38s %-22s %s' % ('引用方', '欄位', '被引用方'))
print('-' * 82)
link_ok = True
for src, sf, dst, df in LINKS:
    a, b = load(src), load(dst)
    if a is None or b is None:
        print('%-38s %-22s 🚨 缺檔' % (src, sf))
        link_ok = False
        continue
    ok = a.get(sf) == b.get(df)
    link_ok &= ok
    print('%-38s %-22s %-34s %s'
          % (src, sf, dst, '✅' if ok else '🚨 不符'))

# ── 三、數字之跨產物一致 ────────────────────────────────────────
print()
print('=== 三、關鍵數字跨產物一致 ===')
num_ok = True


def check(label, a, b):
    global num_ok
    ok = a == b
    num_ok &= ok
    print('   %-46s %s vs %s  %s' % (label, a, b, '✅' if ok else '🚨'))


cal = load('m1_step2_calibration_set.json')
inv = load('m1_step3_inventory.json')
bf = load('m1_step3_backfill.json')
asg = load('m1_step2_assignment.json')
pop = load('m1_step2_population.json')

check('校準集篇數 vs 契約 totalSampleSize', cal['totalSampleSize'], 60)
check('盤點涵蓋數 vs 校準集篇數', inv['counts']['total'], cal['totalSampleSize'])
check('遞補配額合計 vs 校準集篇數', bf['totals']['quota'], cal['totalSampleSize'])
check('分派池配額合計 vs 60', sum(p['quota'] for p in asg['pools']), 60)
check('母體 advance 數 vs 分派已分派數',
      sum(1 for v in pop['decisions'].values() if v == 'advance'), 314)
check('盤點狀態合計 vs 60', sum(inv['counts']['byStatus'].values()), 60)

print()
print('=' * 74)
allok = self_ok and link_ok and num_ok
print('自我雜湊 %s｜跨產物鏈結 %s｜關鍵數字 %s'
      % ('✅' if self_ok else '🚨', '✅' if link_ok else '🚨',
         '✅' if num_ok else '🚨'))
print('%s' % ('✅ 全部通過——鏈結完整、可重算、數字一致。'
              if allok else '🚨 有不符項，見上；🚫 交付前須查明。'))
sys.exit(0 if allok else 1)
