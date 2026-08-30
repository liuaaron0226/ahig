# -*- coding: utf-8 -*-
"""四格「產不出」之複查：**其中三格的阻礙是我推的，不是我查的。**

## 🚨 為什麼要複查自己上一次的結論

`n500` 把四格標為產不出，各附一句阻礙。**⚠️ 而那四句裡有三句是推理**：
「這要讀全文」「這是判讀不是檢索」——**🚨 我沒有真的去看私有根裡有沒有那個欄位。**

**⚠️ 本 session 已經有四次「沒看就斷言」**
（`attempts[].sourceId`、TEI 之 `sourceSha256`、`Untitled` 之判準、`licenceProvenance`）。
**🚨 其中一次的形狀正是這個：我把自己的沒看，寫成了資料的缺陷。**

**✅ 故本檔逐格去看，並把結果分成三種**：

| 判定 | 意思 |
|---|---|
| `verified-blocked` | **去看過了**，確實沒有可據以現算的東西 |
| `bounded` | **算不出那個數，但算得出它的界**——🚨 剩下的差額才是判讀 |
| `needs-ruling` | 資料齊全，**卡在一個裁定** |

> **🚨 `bounded` 是本檔的重點**：⚠️ 「產不出」與「產得出一個界」在交付時是兩件事，
> **而把後者說成前者，等於把一份可用的材料丟掉。**

## 🚨 控制探針

**⚠️ 一個「什麼都比對不到」的樣式，與「真的沒有這種紀錄」，數出來都是 0；
而一個「什麼都比對得到」的樣式，會給出一個看起來很有份量的上界。**
**✅ 故上界之樣式須同時通過兩道**：
① 對**全體**判讀比對得到明顯較大的數（證明它會中）；
② 對 `opinion` 之篩選確實生效（兩個母體之數必須不同）。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：私有根各檔實際有哪些欄位、以及以字樣可界定之上界。
- 🚨 查不到：**「僅卡某一項」之「僅」**——⚠️ 那要逐筆讀理由並判斷有無其他卡點，
  **🚫 本檔不代為判讀，只把它夾在一個區間裡。**
- ⚠️ 上界之樣式以中文字樣認定，**🚨 措辭換了就漏**——故上界是**這個樣式下的上界**。
"""
import io
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
RUNSUB = 'search-runs/b11-exogenous-cho-endurance/b11-full-run'
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require(RUNSUB)
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
RUN = PRIVATE_ROOT / RUNSUB
POP = re.compile(r'族群|population', re.I)


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


entries = []
for p in sorted(RUN.glob('*/judgements.json')):
    for e in (jload(p).get('entries') or []):
        entries.append(e)
by_op = Counter(e.get('opinion') for e in entries)

print('=== 四格「產不出」之複查 ===')
print('   判讀條目 %d｜opinion 分布 %s' % (len(entries), dict(by_op)))
print()

# ── 控制探針 ─────────────────────────────────────────────────────
print('一、控制探針——🚨 未過即不報上界')
all_hits = sum(1 for e in entries if POP.search(e.get('reason') or ''))
unclear = [e for e in entries if e.get('opinion') == 'unclear']
unclear_hits = sum(1 for e in unclear if POP.search(e.get('reason') or ''))
c1 = all_hits > 100
c2 = all_hits != unclear_hits
c3 = unclear_hits < len(unclear)
for name, ok, detail in (
        ('樣式會中（全體命中 > 100）', c1, '全體命中 %d' % all_hits),
        ('opinion 篩選確實生效', c2, '全體 %d ≠ unclear %d' % (all_hits, unclear_hits)),
        ('樣式🚫 不是全中', c3, 'unclear 命中 %d ／ unclear 全體 %d'
         % (unclear_hits, len(unclear)))):
    print('   %s %-28s %s' % ('✅' if ok else '🚨', name, detail))
if not (c1 and c2 and c3):
    sys.exit('🚨 控制探針未過——🚫 不報任何上界。')
print('   ✅ 三道皆過：這個樣式會中、會篩、且不是全中。')
print()

cells = {}

# ── POP_WORDING_UNCLEAR_N ────────────────────────────────────────
cells['POP_WORDING_UNCLEAR_N'] = {
    'verdict': 'bounded',
    'lowerBound': 0,
    'upperBound': unclear_hits,
    'denominator': len(unclear),
    'criterion': 'opinion == unclear 且理由文字含「族群」或 population',
    'whyNotExact': ('該格要的是「**僅**卡族群措辭」者。⚠️ 抽樣讀過之理由多半同時'
                    '寫著對照臂、劑量、摘要缺漏等其他卡點——🚨 「僅」這個字要靠'
                    '逐筆讀理由才判得出來，🚫 不是檢索。'),
    'whyUsefulAnyway': ('⚠️ 「產不出」與「產得出一個界」在交付時是兩件事：'
                        '🚨 上界說得出「至多這麼多」，而那已足以判斷它會不會'
                        '影響結論。'),
    'patternCaveat': '🚨 以中文字樣認定，措辭換了就漏——⚠️ 故這是**該樣式下**之上界。',
}

# ── SEX_SAMPLE_COMPOSITION：去看私有根到底有什麼 ──────────────────
q = jload(RUN / 'screening-queue' / 'queue.json')
qkeys = sorted({k for i in q[:500] for k in i.keys()})
abstracts = jload(RUN / 'abstract-enrichment' / 'abstracts.json')
part_fields = [k for k in qkeys
               if re.search(r'sex|gender|female|male|participant|sample', k, re.I)]
cells['SEX_SAMPLE_COMPOSITION'] = {
    'verdict': 'verified-blocked',
    'queueFields': qkeys,
    'participantFieldsFound': part_fields,
    'abstractsAvailable': len(abstracts),
    'whatWasChecked': ('逐一列出 queue 條目之欄位聯集，並清點 abstract-enrichment '
                       '之涵蓋筆數。'),
    'finding': ('🚨 queue 之欄位裡**沒有任何一個**與受試者組成有關'
                '（僅題名、識別碼、分數、旗標、分層）；'
                '⚠️ 摘要另存 %d 筆，🚨 但由摘要判定性別組成仍是閱讀，'
                '🚫 不是取欄位。' % len(abstracts)),
    'correction': ('⚠️ `n500` 原記其阻礙為 needs-extraction——**結論不變，'
                   '但當時是推的**；🚨 本檔實查後改記為 verified-blocked，'
                   '並附所查之欄位清單。'),
}

# ── 其餘兩格：確認其阻礙型別 ──────────────────────────────────────
cells['TITLE_ONLY_EXPECTED_GAP'] = {
    'verdict': 'needs-ruling',
    'finding': ('⚠️ 資料齊全（名冊 175 筆在手），🚨 卡的是「該用哪個率去推導」——'
                'n+121 已裁定舊率不得直接套用，而新率尚未指定。'),
}
cells['HARMS_S5_ACTUAL'] = {
    'verdict': 'needs-extraction',
    'finding': ('🚨 該值須萃取判讀後才存在；⚠️ 且 n+147 明訂「GI 是否為主要結局」'
                '正是 S5 要量的東西，🚫 不得由取得端順手做掉。'),
}

print('二、逐格')
for name, c in sorted(cells.items()):
    tag = {'bounded': '📐 可給界', 'verified-blocked': '✅ 已實查確認擋住',
           'needs-ruling': '⏸ 待裁定', 'needs-extraction': '⏸ 待萃取'}[c['verdict']]
    print('   %-28s %s' % (name, tag))
    if c['verdict'] == 'bounded':
        print('      區間 [%d, %d]，分母 %d（unclear 全體）'
              % (c['lowerBound'], c['upperBound'], c['denominator']))
        print('      🚨 %s' % c['whyNotExact'][:88])
    else:
        print('      %s' % c['finding'][:92])
print()
print('🚨 四格之中，1 格由「產不出」改為「可給界」，1 格由推論改為實查確認；')
print('   ⚠️ 另兩格維持——一格等裁定、一格等萃取，🚫 皆非本室可解。')

doc = {
    'schemaVersion': 1,
    'documentType': 'blocked-cell-review',
    'ruling': 'self-initiated: three of the four blockers n500 recorded were '
              'reasoned rather than looked up, and this run has already turned '
              "one of my own failures to look into a claimed defect in the data.",
    'population': 'the four cells n500 reports as not producible',
    'countingUnit': 'cell',
    'criterion': 'verified-blocked / bounded / needs-ruling / needs-extraction, '
                 'each with what was actually inspected',
    'judgementEntries': len(entries),
    'opinionCounts': dict(by_op),
    'controlProbes': {'patternHitsAcrossAll': all_hits,
                      'patternHitsAmongUnclear': unclear_hits,
                      'unclearTotal': len(unclear),
                      'why': 'A pattern that matches nothing and a corpus that '
                             'contains nothing both count zero; a pattern that '
                             'matches everything yields an impressive-looking '
                             'upper bound. Both directions are checked before '
                             'any bound is reported.'},
    'cells': cells,
    'rootProvenance': ROOT_PROVENANCE,
    'coverageStatement': 'The bound is a bound under one Chinese wording pattern; '
                         'differently worded reasons are missed, so it bounds '
                         'what that pattern can see. The word "only" in "blocked '
                         'only by population wording" is a reading of each reason '
                         'and is left to a reader rather than approximated.',
    'contentNote': 'Counts and field names only. No reason text is stored.',
}
doc['reviewHash'] = content_hash({k: v['verdict'] for k, v in cells.items()})
io.open(S + 'n507_blocked_cells_review.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn507_blocked_cells_review.json' % S)
