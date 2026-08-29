# -*- coding: utf-8 -*-
"""丙節兩次觸發對照表：釘死兩格未指明之欄位，並拆解「抽驗母體」那一列的落差。

## 🚨 本輪要補的那一類

第 442 輪把 33 格佔位符的**路徑**掃完，並載明本室的自動檢查**抓不到**這一型：
**路徑有效、取得到值，但取到的不是該格語意上要的量。**
⚠️ 那一型只能人讀骨架——本檔即為此而作，標的是丙節之兩次觸發對照表。

## 一、兩格「清單未指明確切欄位」，其實兩格都指得出來

| 佔位符 | 精確路徑 | 值 |
|---|---|---|
| `OCC1_HITS` | `n68_tail_result.json` → `result.relevantOrUnclearFound` **之長度** | **2** |
| `OCC1_POP` | `n68_termination_evidence.json` → `counts.notScreenedCount` | **2116** |

**✅ `OCC1_HITS` 與 `OCC2_HITS` 用的是同一個欄位名**（`result.relevantOrUnclearFound`）
——⚠️ 兩次其實對稱，清單標「未指明」是抄寫時漏掉，不是資料真的缺。
🚨 並以另一路徑交叉核對：`decisionCounts` 之 `unclear 1 + advance 1 = 2`，相符。

## 🚨 二、真正的發現：同一列的兩個數，用的是不同的閉合式

骨架 `m1-c-termination-skeleton.md:61` 把兩者並列於「抽驗母體」同一列：

```
第一次 2116        第二次 1460
```

**⚠️ 但兩者來自不同名稱的欄位，且由不同算式得出**：

```
OCC1  9091 − 6975                = 2116     （無 outOfSequence 項）
OCC2  9091 − 7431 − 200          = 1460     （有 outOfSequence 項）
```

**🚨 落差 656 之組成**：
- **456** 為兩次之間**真正推進的判讀**（judged 6975 → screened 7431）
- **200** 為 **n+72 才引入之第三態**（`outOfSequenceCount`），**⚠️ 是定義變更，不是篩選進度**

**⚠️ 而對照表不給讀者任何提示。** 讀者看到「2116 → 1460」會全數讀成篩選進度，
**🚨 而其中 200 筆是換了算法造成的。**

**⚠️ 這與 n+115（三.3）所指的是同一件事**（11 欄 vs 12 欄、版本號卻相同），
**🚨 只是那裡出現在雜湊原像，這裡出現在要交付給讀者的表格裡。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：兩格之精確路徑、閉合式是否成立、落差之組成。
- 🚨 查不到：**該對照表其餘各列是否也有同型問題**——⚠️ 本檔只讀「抽驗母體」與「命中」兩列。
  🚨 其餘各列（觸發點、pScore／window、結果）尚未逐列比對其兩側定義是否同一。
"""
import io
import json
import sys

S = '.scratch/'
n68r = json.load(io.open(S + 'n68_tail_result.json', encoding='utf-8'))
n68e = json.load(io.open(S + 'n68_termination_evidence.json', encoding='utf-8'))
n78r = json.load(io.open(S + 'n78_tail_result.json', encoding='utf-8'))
n78e = json.load(io.open(S + 'n78_termination_evidence.json', encoding='utf-8'))

occ1_hits = len(n68r['result']['relevantOrUnclearFound'])
occ1_hits_xcheck = (n68r['decisionCounts']['unclear']
                    + n68r['decisionCounts']['advance'])
occ2_hits = len(n78r['result']['relevantOrUnclearFound'])
c1 = n68e['counts']
s2 = n78e['standardLaneSequence']
occ1_pop = c1['notScreenedCount']
occ2_pop = n78e['tailSpotCheckPopulation']['count']

print('=== 一、兩格「未指明欄位」之釘定 ===')
print('   OCC1_HITS = %d  ← n68_tail_result.json result.relevantOrUnclearFound 之長度'
      % occ1_hits)
print('              交叉核對 decisionCounts unclear+advance = %d  %s'
      % (occ1_hits_xcheck, '✅ 相符' if occ1_hits == occ1_hits_xcheck else '🚨 不符'))
print('   OCC1_POP  = %d  ← n68_termination_evidence.json counts.notScreenedCount'
      % occ1_pop)
print('   ⚠️ OCC1_HITS 與 OCC2_HITS(%d) 用的是同一個欄位名——🚨 兩次本來就對稱。'
      % occ2_hits)

print()
print('=== 二、「抽驗母體」一列之落差拆解 ===')
prog = s2['screenedCount'] - c1['judgedCount']
oos = s2['outOfSequenceCount']
gap = occ1_pop - occ2_pop
print('   OCC1  %d − %d = %d          （無 outOfSequence 項）'
      % (c1['poolSize'], c1['judgedCount'], occ1_pop))
print('   OCC2  %d − %d − %d = %d    （有 outOfSequence 項）'
      % (s2['nTotal'], s2['screenedCount'], oos, occ2_pop))
print('   落差 %d = 判讀推進 %d ＋ 第三態新增 %d   %s'
      % (gap, prog, oos, '✅ 帳平' if prog + oos == gap else '🚨 帳不平'))
print('   🚨 即落差之 %d/%d（%.0f%%）不是篩選進度，是 n+72 引入第三態所致。'
      % (oos, gap, 100.0 * oos / gap))

ok = (occ1_hits == occ1_hits_xcheck and prog + oos == gap
      and c1['poolSize'] - c1['judgedCount'] == occ1_pop)
doc = {
    'schemaVersion': 1,
    'documentType': 'occurrence-comparison-semantics',
    'ruling': 'self-initiated; covers the class round 442 said only a reader catches',
    'population': "the two rows 抽驗母體 and 命中 of the 丙 skeleton's "
                  'two-occurrence comparison table',
    'countingUnit': 'placeholder / record',
    'criterion': 'whether the two sides of a row are defined the same way',
    'pinned': {
        'OCC1_HITS': {'value': occ1_hits,
                      'path': 'n68_tail_result.json → len(result.relevantOrUnclearFound)',
                      'crossCheck': 'decisionCounts unclear+advance = %d' % occ1_hits_xcheck,
                      'note': 'same field name as OCC2_HITS; the checklist marked '
                              'it unspecified, but the two occurrences are '
                              'symmetric and the path exists'},
        'OCC1_POP': {'value': occ1_pop,
                     'path': 'n68_termination_evidence.json → counts.notScreenedCount',
                     'closure': '%d - %d = %d' % (c1['poolSize'], c1['judgedCount'], occ1_pop)},
    },
    'populationRowAsymmetry': {
        'occ1Field': 'counts.notScreenedCount',
        'occ2Field': 'tailSpotCheckPopulation.count',
        'occ1Formula': 'poolSize - judgedCount',
        'occ2Formula': 'nTotal - screenedCount - outOfSequenceCount',
        'gap': gap,
        'fromScreeningProgress': prog,
        'fromNewThirdState': oos,
        'note': ('The skeleton prints 2116 and 1460 side by side under one '
                 'heading. A reader takes the drop for screening progress, but '
                 '%d of the %d comes from the out-of-sequence term that n+72 '
                 'introduced between the two occurrences -- a change of '
                 'definition, not of state. Same asymmetry n+115(3.3) raised '
                 'about the 11 versus 12 hash fields, surfacing here in the '
                 'table that goes to the reader.' % (oos, gap)),
        'recommendation': ('Footnote the row with both formulas, or decompose '
                           'the drop in the text.'),
    },
    'coverageStatement': ('Only the 抽驗母體 and 命中 rows were read. The other '
                          'rows of the same table have not been checked for the '
                          'same defect.'),
    'contentNote': 'Counts and field paths only.',
}
io.open(S + 'n443_occ_symmetry.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn443_occ_symmetry.json' % S)
sys.exit(0 if ok else 1)
