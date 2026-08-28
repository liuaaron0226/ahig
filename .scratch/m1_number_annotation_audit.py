# -*- coding: utf-8 -*-
"""依 n+109（三）自檢：本室產物之關鍵數字，是否附了母體／計數單位／判準。

## 🚨 為什麼要自檢

n+109 三立下新要求：**「報數之附註須擴為三項：母體、計數單位、判準。」**
其依據是同型錯誤已發生五次：
```
① 45 可得 vs 12 在手      母體不同
② 勘誤 7 / 8 / 4          母體不同
③ 影子 11 vs 12           母體不同
④ 抽查債 22 / 16 / 6      計數單位不同（項目 vs 文獻）
⑤ 技能方向 2 vs 4         判準不同
```
**⚠️ 而本室多數產物產於該裁定之前**，故其附註未必齊備。
**🚨 交付時才被問「這個數字在數什麼」，比現在自己補上代價高。**

## 本檔檢查什麼

對每一份產物之**關鍵數字欄位**，逐一問三個問題：
1. **母體**：這個數是從哪個集合數出來的？產物內是否寫明？
2. **計數單位**：數的是文獻、項目、段落、還是別的？
3. **判準**：納入該數的條件是什麼？

**⚠️ 本檔判定「有沒有附註」，不判定「附註對不對」**
——**🚨 後者需要人讀，機器只能查欄位在不在。**（涵蓋範圍聲明，n+80 三之紀律。）

## 🚨 本檔第一版之弱點，記在這裡

**期待欄位清單是人工對照各產物後訂的，不是自動推導。**
第一版把 `n86` 檔的欄位名（`method`／`verificationNote`）套到 `n92` 檔上，
**於是把「兩份產物用了不同的欄位名」誤報成「後者缺說明」。**

**⚠️ 即本檔查的是「欄位名對不對得上」，不是「說明在不在」。**
**🚨 兩者不同，而前者會產生偽陽性——修正後仍請以此理解本檔之輸出。**
"""
import io
import json
import os

S = '.scratch/'

# (檔名, 關鍵數字欄位, 應載明母體/單位/判準之欄位)
TARGETS = [
    ('m1_step2_population.json', 'counts',
     ['derivation', 'applicationOrder', 'purpose']),
    ('m1_step2_assignment.json', 'pools',
     ['doseRuleVersion', 'conservativeInference', 'mutualExclusivity',
      'ruling']),
    ('m1_step2_calibration_set.json', 'totalSampleSize',
     ['anchorCoverage', 'seedDerivation', 'samplingMethod', 'pendingFullText']),
    ('m1_step3_inventory.json', 'counts',
     ['wordingConstraint', 'purpose', 'blockReasons']),
    ('m1_step3_backfill.json', 'totals',
     ['obtainableDefinition', 'obtainableDefinitionNote', 'replacementRule']),
    ('n85_tail_population.json', 'count',
     ['derivation', 'anchor', 'purpose']),
    ('n97_errata_roster.json', 'count',
     ['authoritativeSource', 'authoritativeSourceNote', 'reconciliation',
      'sevenVsEightResolved']),
    ('n86_errata_originals.json', 'inPool',
     ['method', 'verificationNote']),
    ('n94_three_lane_reconcile.json', 'classificationCounts',
     ['classificationNote', 'question', 'laneToSheetNote']),
    # ⚠️ 本列第一版期待 method／verificationNote，那是 n86 檔的欄位名，
    #    被我套到這一份上，於是把「命名不同」誤報成「缺說明」。
    # 🚨 該檔實有等效說明：unionGate（門檻與 pilot 之排除理由）、
    #    batches（含 positions／boardLine／prefixesMatch 等重建依據）。
    ('n92_audit_debt_union.json', 'union',
     ['unionGate', 'batches', 'threeColumnFormat', 'pilotNature']),
    ('m1_step2_feasibility.json', 'strata',
     ['comparisonNote', 'unresolved', 'purpose']),
    ('n107_pilot_provenance.json', 'verifiedFromData',
     ['provenance']),
]

print('=== n+109（三）三項附註之齊備度自檢 ===')
print('⚠️ 只查「附註欄位在不在」，不查「附註對不對」——後者需人讀。')
print()
print('%-38s %-22s %8s %s' % ('產物', '關鍵數字欄位', '附註欄位', '缺少者'))
print('-' * 92)

missing_any = []
for fn, numfield, notes in TARGETS:
    p = os.path.join(S, fn)
    if not os.path.isfile(p):
        print('%-38s %-22s %8s %s' % (fn, numfield, '—', '🚨 檔案不存在'))
        missing_any.append((fn, 'file-missing'))
        continue
    d = json.load(io.open(p, encoding='utf-8'))
    has_num = numfield in d
    lack = [k for k in notes if k not in d]
    mark = '✅' if (has_num and not lack) else '🚨'
    print('%-38s %-22s %5d/%-2d %s %s'
          % (fn, numfield + ('' if has_num else ' 🚨缺'),
             len(notes) - len(lack), len(notes), mark,
             ('缺 ' + '／'.join(lack)) if lack else ''))
    if lack or not has_num:
        missing_any.append((fn, lack))

print('-' * 92)
print()
if missing_any:
    print('🚨 %d 份產物之附註不齊，見上。' % len(missing_any))
else:
    print('✅ 全部產物之關鍵數字皆附有母體／單位／判準之說明欄位。')

print()
print('⚠️ 本檔之涵蓋範圍聲明（n+80 三之紀律）：')
print('   ✅ 查得到：宣稱之附註欄位是否存在於產物內。')
print('   🚨 查不到：①該附註之內容是否正確；②三項是否真的都被說清楚')
print('      （一個欄位可能只寫了母體而沒寫判準）；③產物之外的看板敘述。')
print('   ⚠️ 故本檔通過**不代表**「數字已可被正確理解」，只代表「說明欄位在」。')
