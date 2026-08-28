# -*- coding: utf-8 -*-
"""交付清單之「看板型」六項——逐一查其是否真的只有看板可依。

## 🚨 為什麼做這一輪

第 440 輪把同樣的檢查套在「不可及八項」上，查出**五項其實在版控裡**。
**⚠️ 那不是運氣**——分類是憑印象填的，而印象不會自己更新。
故本檔把同一把尺量向「看板型」那六項。

## 結果摘要（詳見下方輸出）

| 佔位符 | 原分類 | 實況 |
|---|---|---|
| `DEBT_B4`／`DEBT_CUMULATIVE`／`DEBT_OUTSTANDING`／`DEBT_SETTLED` | 看板 | **✅ 有產物與產生腳本**（`n92_audit_debt_union`），應改為產物型 |
| `ORPHAN_N` | 看板 | ⚠️ 應為**不可及型**：值 5 出自私有根工作單，有 `file_hash` |
| `SEX_REPRESENTATION` | 看板・**凍結** | **🚨 無有效來源——見下** |

## 🚨 `SEX_REPRESENTATION`：兩個候選來源，量的都不是它要的東西

骨架 `m1-b-screening-limits-skeleton.md:90` 定義它為 **「男性佔比區間」**。

**候選一（清單現行所引）看板 49702**：
「菁英層級之補給規劃率 81%，男女差異顯著（91–93% vs 67–72%）」
——**🚨 那是單一研究中「各性別各自的補給規劃率」，不是「參與者的男性佔比」。**
**⚠️ 量的是不同的東西，不是同一個東西的不同精度。**

**候選二 看板 46659–46672**：`04b680d2`（2023）之 281 篇標準化稽核，
總參與者 3,735 名、**僅約 16% 為女性**（→ 男性約 84%）、純男性世代 217 篇（約 77%）。
**✅ 量的是對的東西**，**🚨 惟母體不同**——看板 46676 自己就寫明
「其標的為**慢性**碳水策略（**非契約之急性運動中補給**）」，
**⚠️ 該處只主張「代表性缺口之結論可外推」，🚫 未主張其數字可代用。**

**故本 review 納入研究之男性佔比區間，今日無來源可填**
——**🚨 它要由納入研究之全文萃取而來，即 M1 第 ④ 步，而 ④ 尚未起跑。**

**⚠️ 而它在清單上被標為「凍結」**（＝已定案、交付時不需再算）。
**🚨 一個尚未產生的數字被標成已凍結，是清單裡最容易矇混過關的一格。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：各佔位符是否存在可執行的產生路徑，及其值與雜湊。
- 🚨 查不到：**骨架對每個佔位符的語意界定是否恰當**——⚠️ 那要人讀。
  本檔只指出「引用的來源量的不是骨架所定義的量」，🚫 不代為重新界定。
- ⚠️ 搜尋範圍已載明（n+106 二）：`COORDINATION.md` 全文，
  以及受追蹤之 `docs/` 與 `.scratch/`；兩處皆無「男性佔比」之語料級量測。
"""
import io
import json
import os
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash, file_hash  # noqa: E402

RUN = (os.environ.get('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private') +
       '/search-runs/b11-exogenous-cho-endurance/b11-full-run')

debt = json.load(io.open('.scratch/n92_audit_debt_union.json', encoding='utf-8'))
u = debt['union']
DEBT = [('DEBT_CUMULATIVE', 22, u['cumulativeUnion']),
        ('DEBT_OUTSTANDING', 16, u['outstandingUnion']),
        ('DEBT_SETTLED', 6, len(u['mainFrameSettled'])),
        ('DEBT_B4', 11, len(u['shadowOutstanding']))]

print('=== 一、四項 DEBT_*：看板值 vs 產物值 ===')
ok = True
for k, board, art in DEBT:
    ok &= board == art
    print('   %-20s 看板 %-4s 產物 %-4s %s'
          % (k, board, art, '✅ 相符' if board == art else '🚨 不符'))
print('   產物 `.scratch/n92_audit_debt_union.json`，rebuildHash %s'
      % debt['rebuildHash'][:24] + '…')
print('   ⚠️ 故此四項應由「看板型」改為「產物型」——🚨 它們本來就有產生腳本。')

orph_p = RUN + '/critical-harms-sweep-orphans/worksheet.json'
raw = open(orph_p, 'rb').read()
w = json.loads(raw.decode('utf-8'))
orphan_n = len(w.get('items') or [])
print()
print('=== 二、ORPHAN_N ===')
print('   worksheet items %d｜itemCount 欄 %s｜兩者相符 %s'
      % (orphan_n, w.get('itemCount'), orphan_n == w.get('itemCount')))
print('   file_hash %s' % file_hash(raw))
print('   ⚠️ 應為「不可及型」（私有根），🚨 非「看板型」——值有確定來源與雜湊。')

print()
print('=== 三、SEX_REPRESENTATION ===')
print('   骨架定義：男性佔比區間（m1-b-screening-limits-skeleton.md:90）')
print('   候選一 看板 49702：單一研究之各性別補給規劃率 91–93% vs 67–72%')
print('      🚨 量的不是參與者男性佔比——⚠️ 是不同的量，不是精度差異。')
print('   候選二 看板 46666：281 篇稽核，3,735 人中約 16% 女性（→ 男性約 84%）')
print('      ✅ 量對，🚨 惟母體為**慢性**碳水策略研究，非本 review 之納入研究；')
print('      ⚠️ 看板 46676 自載「結論可外推」，🚫 未主張數字可代用。')
print('   🚨 結論：本 review 之男性佔比區間今日無來源，須由 ④ 步全文萃取產生。')
print('   ⚠️ 而清單標其為「凍結」——🚨 尚未產生的數字被標成已定案。')

doc = {
    'schemaVersion': 1,
    'documentType': 'board-sourced-placeholder-audit',
    'ruling': 'self-initiated; extends the round-440 check to the board-sourced six',
    'population': "the six placeholders whose 來源型態 is 看板 in docs/m1-e-delivery-checklist.md",
    'countingUnit': 'placeholder',
    'criterion': 'whether an executable producing path exists, and whether the '
                 'cited source measures the quantity the skeleton defines',
    'debtHaveProducer': {k: {'board': b, 'artefact': a, 'match': b == a}
                         for k, b, a in DEBT},
    'debtProducer': '.scratch/n92_audit_debt_union.py',
    'debtArtefactHash': debt['rebuildHash'],
    'debtReclassify': '看板 → 產物',
    'orphanN': {'value': orphan_n,
                'source': 'critical-harms-sweep-orphans/worksheet.json',
                'fileHash': file_hash(raw),
                'reclassify': '看板 → 不可及（executor-measured, hashed）'},
    'sexRepresentation': {
        'skeletonDefinition': 'male-proportion range (m1-b skeleton line 90)',
        'citedSource': 'board 49702',
        'citedSourceMeasures': 'per-sex supplementation planning rates in one '
                               'study (91-93% vs 67-72%)',
        'citedSourceVerdict': 'MEASURES A DIFFERENT QUANTITY, not a coarser '
                              'version of the same one',
        'betterCandidate': 'board 46666',
        'betterCandidateMeasures': '281-study audit: 3,735 participants, ~16% '
                                   'female, so ~84% male; 217 male-only cohorts',
        'betterCandidateVerdict': 'right quantity, WRONG POPULATION -- chronic '
                                  'carbohydrate strategy research, which board '
                                  '46676 itself marks as outside this '
                                  "contract's acute during-exercise scope, and "
                                  'where only the conclusion is said to '
                                  'extrapolate, not the figures',
        'conclusion': 'No source exists today for the male-proportion range of '
                      "this review's included studies. It has to come from "
                      'full-text extraction, which is M1 step 4, not started.',
        'severity': 'The checklist marks this placeholder 凍結, i.e. already '
                    'settled and not to be recomputed at delivery. A figure '
                    'that does not exist yet is labelled as final.',
    },
    'searchRangeDeclared': ['COORDINATION.md in full',
                            'tracked docs/ and .scratch/'],
    'contentNote': 'Counts, hashes and board line numbers only.',
}
doc['auditHash'] = content_hash(doc['debtHaveProducer'])
io.open('.scratch/n441_board_sourced.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → .scratch/n441_board_sourced.json')
sys.exit(0 if ok else 1)
