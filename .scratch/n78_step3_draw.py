# -*- coding: utf-8 -*-
"""n+57 第 3 步：抽取 200 筆尾端抽驗樣本（第二次觸發）。

⚠️ 錨定值須用 `content_hash(worksheet)`，**不是 worksheet 檔案的裸 sha256**
——我在第 1 步腳本裡先算了裸雜湊，與上次抽樣所用者不同。上次是
`content_hash`，本檔照舊。**此值不是 queueHash，報告中不得如此稱呼**
（n+51 等效替代、n+57 第 3 步）。

🚨 工作單自上次抽樣以來未變，故錨定值相同、種子相同。母體則已由 2,116
縮為 1,460。`draw_tail_spot_check` 以 `sorted(ids)` 後同一 seed 取樣，
**母體變了樣本就會不同，但不保證零重疊**——n+78 稱「與第一次零重疊已實測」，
本檔自行重測，不引用該說法。
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
w = json.loads((OUT / 'worksheet.json').read_text(encoding='utf-8'))
op = {e['candidateId'] for e in
      json.loads((OUT / 'judgements.json').read_text(encoding='utf-8'))['entries']}

ws_ids = {it['candidateId'] for it in w['items']}
not_screened = sorted(ws_ids - op)

freeze = json.load(io.open('.scratch/n78_termination_evidence.json',
                           encoding='utf-8'))
assert freeze['tailSpotCheckPopulation']['count'] == len(not_screened), \
    ('母體與第 1 步凍結證據不符：%d vs %d'
     % (freeze['tailSpotCheckPopulation']['count'], len(not_screened)))

anchor = content_hash(w)
prev = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
assert anchor == prev['anchor']['value'], \
    '錨定值與上次不同——工作單已變，須先查明原因'

sample = draw_tail_spot_check(not_screened, queue_hash=anchor, n=200)

prev_ids = set(prev['sample']['candidateIds'])
now_ids = set(sample['candidateIds'])
overlap = sorted(prev_ids & now_ids)

doc = {
    'schemaVersion': 1,
    'documentType': 'termination-tail-spot-check-sample',
    'occurrence': 2,
    'step': 'n+57 section 2 step 3 (draw 200-record tail spot check)',
    'readsStep1': {
        'terminationEvidenceHash':
            freeze['evaluateTerminationStandardBasis'][
                'terminationEvidenceHash'],
        'standardLanePScore': freeze['standardLaneSequence']['pScore'],
        'standardLaneWindowSize': freeze['standardLaneSequence']['windowSize'],
        'triggerCauseCandidateId': freeze['triggerCause']['candidateId'],
    },
    'anchor': {
        'value': anchor,
        'source': 'content_hash(worksheet.json)',
        'note': ('This lane has no queueHash. Per n+51 the worksheet hash is '
                 'the approved equivalent seed anchor. It is NOT a queueHash '
                 'and must not be called one (n+57 step 3). Same value as '
                 'occurrence 1 because the worksheet has not changed.'),
    },
    'notScreenedCount': len(not_screened),
    'previousOccurrence': {
        'notScreenedCount': prev['notScreenedCount'],
        'anchorValue': prev['anchor']['value'],
        'overlapWithThisSample': len(overlap),
        'overlapCandidateIds': overlap[:10],
        'note': ('Same seed, different population (2116 -> 1460), so the draw '
                 'differs. Overlap measured here rather than taken from the '
                 'ruling text.'),
    },
    'sample': sample,
}
doc['sampleHash'] = content_hash(sample)

io.open('.scratch/n78_tail_sample.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))

print('✅ 第 3 步：樣本已抽出並落盤 → .scratch/n78_tail_sample.json')
print('   母體 %d 筆、抽出 %d 筆' % (len(not_screened), sample['sampleSize']))
print('   錨定值 %s（content_hash，非裸 sha256、非 queueHash）' % anchor[:40])
print('   seed %d' % sample['seed'])
print('   sampleHash %s' % doc['sampleHash'][:40])
print()
print('🚨 與第一次抽樣之重疊：**%d 筆**（實測，未引用裁定說法）' % len(overlap))
if overlap:
    print('   重疊短碼：%s' % [c[-8:] for c in overlap[:10]])
