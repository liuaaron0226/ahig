# -*- coding: utf-8 -*-
"""n+85／擁有者裁示：把第二次尾端抽驗之母體清單入版控。

🚨 這是**唯一擋住終止裁決**的項目（擁有者裁示第 394 輪）。
n+85 第二節指出：四道檢查已證「被判讀的 200 筆＝被抽中的 200 筆」，
**但協調者無法重跑抽樣本身**，因為 `draw_tail_spot_check` 需要那 1,460 筆
母體 id 清單，而它不在版控內。
**⚠️ 故目前仍能通過全部檢查的失效只剩一種：把一組自選的 200 筆寫進抽樣產物。**

本檔補上最後一環。依擁有者裁示所訂之規格：

| 項目 | 要求 |
|---|---|
| 內容 | 第二次抽驗母體之 1,460 筆 candidateId 全集 |
| 形態 | 純 id，零文獻內容 |
| 順序 | 落盤即排序（`draw_tail_spot_check` 內部亦自行 sorted） |
| 自驗 | 附清單之 content_hash，並附所讀之 terminationEvidenceHash |
| 一致性 | 筆數須等於凍結證據之 tailSpotCheckPopulation.count |

**🚨 母體之定義不從敘述取，一律照 `.scratch/n78_step3_draw.py` 之原式重算**：
`sorted(ws_ids - judged)`——⚠️ 若與凍結證據之 count 不符即當場擋下，
**不調整定義去湊數字**。

落盤後自跑協調者於裁示中先行公布的兩道 assert，通過才算完成。
"""
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.search.statistical_termination import (  # noqa: E402
    draw_tail_spot_check)

ROOT = Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
            r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = ROOT / 'standard-full-screen-pass-1'
DEST = '.scratch/n85_tail_population.json'

w = json.loads((OUT / 'worksheet.json').read_text(encoding='utf-8'))
judged = {e['candidateId'] for e in
          json.loads((OUT / 'judgements.json').read_text(
              encoding='utf-8'))['entries']}
ws_ids = {it['candidateId'] for it in w['items']}

# ── 母體：與第 3 步同一個算式，不另立定義 ──────────────────────────
not_screened = sorted(ws_ids - judged)

freeze = json.load(io.open('.scratch/n78_termination_evidence.json',
                           encoding='utf-8'))
expected = freeze['tailSpotCheckPopulation']['count']
assert expected == len(not_screened), (
    '🚨 母體筆數與凍結證據不符：凍結 %d vs 現算 %d——'
    '在查明原因之前不得落盤' % (expected, len(not_screened)))

anchor = content_hash(w)
prev = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
assert anchor == prev['anchor']['value'], \
    '🚨 錨定值與第一次不同——工作單已變，須先查明原因'

doc = {
    'schemaVersion': 1,
    'documentType': 'termination-tail-spot-check-population',
    'occurrence': 2,
    'purpose': ('Makes the occurrence-2 draw independently reproducible from '
                'version control. Filed per the owner ruling of round 394, '
                'which named this as the only item blocking the termination '
                'decision.'),
    'readsStep1': {
        'terminationEvidenceHash':
            freeze['evaluateTerminationStandardBasis'][
                'terminationEvidenceHash'],
    },
    'anchor': {
        'value': anchor,
        'source': 'content_hash(worksheet.json)',
        'note': ('Not the raw SHA-256 of that file, and not a queueHash. '
                 'See .scratch/n82_anchor_source_errata.json.'),
    },
    'derivation': ("sorted(worksheet candidateIds - judged candidateIds), "
                   "identical to .scratch/n78_step3_draw.py"),
    'count': len(not_screened),
    'contentNote': ('Opaque candidateIds only. No titles, abstracts or any '
                    'other literature content.'),
    'candidateIds': not_screened,
}
doc['populationHash'] = content_hash(doc['candidateIds'])

io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))

print('✅ 母體清單已落盤 → %s' % DEST)
print('   筆數 %d（凍結證據 %d）' % (len(not_screened), expected))
print('   populationHash %s' % doc['populationHash'])
print()

# ── 協調者公布之覆核方式，先自跑一次 ──────────────────────────────
print('=== 自跑協調者於擁有者裁示中公布之兩道 assert ===')
pop = json.load(io.open(DEST, encoding='utf-8'))['candidateIds']
s = draw_tail_spot_check(pop, queue_hash=anchor, n=200)
sample_doc = json.load(io.open('.scratch/n78_tail_sample.json',
                               encoding='utf-8'))
want = sample_doc['sample']['candidateIds']

ok_ids = (s['candidateIds'] == want)
ok_seed = (s['seed'] == 2559117538934593219)
print('  (1) candidateIds 逐位、含順序相同 : %s' % ok_ids)
print('  (2) seed == 2559117538934593219   : %s  (實得 %d)'
      % (ok_seed, s['seed']))
assert ok_ids, '🚨 重跑抽樣與已入版控之樣本不符——終止不成案，須立即回報'
assert ok_seed, '🚨 種子不符'
print()
print('✅ 兩道全過：抽樣現在可由版控內容完整重現。')
