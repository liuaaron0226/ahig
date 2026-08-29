# -*- coding: utf-8 -*-
"""丙節對照表其餘各列：pScore 是否同一定義，以及第二次觸發之前置條件記在哪裡。

## 承接

第 443 輪查出「抽驗母體」一列兩側算式不同，並載明**未查**其餘各列，
**🚨 尤指「第二次之 pScore 出自改判後之窗口合併，與第一次是否為同一定義下之量」。**
本輪查那件事。

## 一、✅ pScore 兩次為同一定義——以生產程式之式子逐位重現

`p_score()`（`statistical_termination.py:46`）之核心：

```
k_target = floor(rho / target_recall) + 1          （精確十進位分數，非浮點）
k_remaining_min = k_target − rho
n_start = n_total − (n_seen − window)
p = hypergeom.cdf(0, n_start, k_remaining_min, window)
```

**以兩次各自記錄之彙總值重算，兩次皆逐位重現**（連 `h0MinTotalRelevant` 亦重現）。
**⚠️ 故該列沒有「抽驗母體」那一列的毛病，可照原樣並列。**

## 二、✅ 第三態之引入，方向是保守的

第二次之序列**排除**了 200 筆 `outOfSequence`。若改為併入序列：

```
現行（排除 200，n_seen 7431）   n_start 1861   p = 0.01240489
假設併入（n_seen 7631）        n_start 1661   p = 0.00700878
```

**⚠️ 排除使 n_start 變大 → p 變大 → 更難通過 α。**
**✅ 即定義變更對第二次觸發是保守方向，🚨 不是讓它更容易通過。**

**⚠️ 這點須與 n+115（三.1）分開講**：那裡指出兩次之雜湊覆蓋不對稱，
且**方向是不利的那一邊**；**🚨 本項方向相反，讀者不可混為一談。**

## 🚨 三、新發現：第二次觸發之「前置條件」不記在作成決策的那個區塊裡

| | 第一次（`n68`，`terminationResult`） | 第二次（`n78`，`standardLaneSequence`） |
|---|---|---|
| `pScore` | ✅ | ✅ |
| `windowSize` | ✅ | ✅ |
| **`mandatoryLanesFullyScreened`** | **✅ True** | **🚨 無** |
| **`allowedToStop`** | **✅ True** | **🚨 無**（只有 `crossesAlpha: True`） |
| `reason` | ✅ | 🚨 無 |
| 自身雜湊 | ✅ | 🚨 無（n+115 三.1 已指出） |

**全檔唯一記載 `mandatoryLanesFullyScreened: True` 之處，是
`evaluateTerminationStandardBasis`**——**🚨 而該區塊之 `poolSize` 為 15,425（全 queue），
不是標準線之 9,091，且其自身 `allowedToStop` 為 False。**

**⚠️ 本室不主張該事實有誤**：安全線／critical-harms 是否全篩畢是**跨 lane 的事實**，
**很可能確實可通用**。**🚨 本室主張的是「記載位置」**：
**產物從未就標準線這個基準陳述過 ADR-0008 的完整合取**，
**⚠️ 稽核者要重建「第二次為何允許終止」，必須向另一個母體、且自身結論為 False 的區塊借一個欄位。**

**🚨 這與 n+115（三.1）是同一個缺口的另一面**：那裡是「唯一的雜湊掛在不是決策的區塊上」，
**這裡是「唯一的前置條件旗標也掛在同一個不是決策的區塊上」。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：pScore 是否可由記錄之彙總值以生產式子重現；欄位在哪些區塊出現。
- 🚨 查不到：**`mandatoryLanesFullyScreened` 這個事實本身於第二次觸發當下是否為真**
  ——⚠️ 那要重跑當時之 lane 狀態，本檔未做，🚫 不以「很可能通用」代替查核。
"""
import io
import json
import sys
from fractions import Fraction

from scipy import stats

S = '.scratch/'
n68 = json.load(io.open(S + 'n68_termination_evidence.json', encoding='utf-8'))
n78 = json.load(io.open(S + 'n78_termination_evidence.json', encoding='utf-8'))
t1 = n68['terminationResult']
t2 = n78['standardLaneSequence']


def recompute(rho, n_seen, window, n_total, target_recall):
    tau = Fraction(str(target_recall))
    k_target = (rho * tau.denominator) // tau.numerator + 1
    n_start = n_total - (n_seen - window)
    p = float(stats.hypergeom.cdf(0, n_start, k_target - rho, window))
    return p, k_target, n_start


print('=== 一、pScore 以生產式子重算 ===')
ok = True
recomp = {}
for tag, t, ntot in (('OCC1', t1, t1['poolSize']), ('OCC2', t2, t2['nTotal'])):
    p, kt, ns = recompute(t['relevantFound'], t['screenedCount'],
                          t['windowSize'], ntot, t['targetRecall'])
    same = (p == t['pScore'] and kt == t['h0MinTotalRelevant'])
    ok &= same
    recomp[tag] = {'p': p, 'recorded': t['pScore'], 'kTarget': kt,
                   'recordedKTarget': t['h0MinTotalRelevant'], 'nStart': ns,
                   'match': same}
    print('   %-6s 重算 %.17g｜檔內 %.17g｜k_target %d/%d  %s'
          % (tag, p, t['pScore'], kt, t['h0MinTotalRelevant'],
             '✅ 逐位相符' if same else '🚨 不符'))

print()
print('=== 二、第三態之方向 ===')
oos = t2['outOfSequenceCount']
p_ex, _, ns_ex = recompute(t2['relevantFound'], t2['screenedCount'],
                           t2['windowSize'], t2['nTotal'], t2['targetRecall'])
p_in, _, ns_in = recompute(t2['relevantFound'], t2['screenedCount'] + oos,
                           t2['windowSize'], t2['nTotal'], t2['targetRecall'])
print('   現行（排除 %d）  n_start %d  p %.8f' % (oos, ns_ex, p_ex))
print('   假設併入序列     n_start %d  p %.8f' % (ns_in, p_in))
print('   ✅ 排除使 p 變大（更保守）：%s' % (p_ex > p_in))

print()
print('=== 三、前置條件與結論欄位之所在 ===')
FIELDS = ['mandatoryLanesFullyScreened', 'allowedToStop', 'reason']
basis = n78['evaluateTerminationStandardBasis']
for f in FIELDS:
    print('   %-32s OCC1 %-6s｜OCC2 標準線 %-6s｜OCC2 全queue基準 %s'
          % (f, t1.get(f, '🚨 無'), t2.get(f, '🚨 無'), basis.get(f, '🚨 無')))
print('   ⚠️ 全 queue 基準之 poolSize %d（非標準線之 %d），其 allowedToStop %s。'
      % (basis['poolSize'], t2['nTotal'], basis['allowedToStop']))

doc = {
    'schemaVersion': 1,
    'documentType': 'occurrence-pscore-definition-check',
    'ruling': 'self-initiated; continues round 443, which left this row unread',
    'population': 'the pScore/window row of the 丙 two-occurrence table, and '
                  'the precondition fields of both occurrences',
    'countingUnit': 'field / record',
    'criterion': 'whether the recorded aggregates reproduce the recorded pScore '
                 'under the production formula, and where each ADR-0008 '
                 'condition is recorded',
    'pScoreReproduces': recomp,
    'pScoreVerdict': 'Both reproduce digit for digit, including '
                     'h0MinTotalRelevant, so the two pScores are the same '
                     'quantity under the same definition. That row needs no '
                     'footnote, unlike the population row in round 443.',
    'thirdStateDirection': {
        'excludedNStart': ns_ex, 'excludedP': p_ex,
        'includedNStart': ns_in, 'includedP': p_in,
        'conservative': p_ex > p_in,
        'note': 'Holding the 200 out-of-sequence records out of the sequence '
                'raises n_start and therefore raises p, making the second '
                'trigger harder to pass, not easier. This must be stated apart '
                'from n+115(3.1), whose asymmetry ran the unfavourable way.',
    },
    'preconditionRecording': {
        'occ1HasAll': all(f in t1 for f in FIELDS),
        'occ2StandardLaneHas': {f: (f in t2) for f in FIELDS},
        'onlyRecordedIn': 'evaluateTerminationStandardBasis',
        'thatBlockPoolSize': basis['poolSize'],
        'standardLanePoolSize': t2['nTotal'],
        'thatBlockAllowedToStop': basis['allowedToStop'],
        'claim': 'Not that the fact is wrong -- whether the safety and '
                 'critical-harms lanes were fully screened is a cross-lane '
                 'fact and may well carry over. The claim is about where it is '
                 'recorded: the artefact never states the full ADR-0008 '
                 'conjunction for the standard-lane basis, so reconstructing '
                 'why occurrence 2 was allowed to stop means borrowing a field '
                 'from a block computed on a different pool whose own verdict '
                 'is False.',
        'relationToN115': 'Same gap seen from another side. n+115(3.1) found '
                          'the only evidence hash sits on the block that did '
                          'not decide; the only precondition flag sits there '
                          'too.',
    },
    'coverageStatement': 'Whether mandatoryLanesFullyScreened was in fact true '
                         'at the second trigger is not checked here; that needs '
                         'replaying the lane state. Not substituted with '
                         '"probably carries over".',
    'contentNote': 'Field names and numeric values only.',
}
io.open(S + 'n444_pscore_definition.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn444_pscore_definition.json' % S)
sys.exit(0 if ok else 1)
