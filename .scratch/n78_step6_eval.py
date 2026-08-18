# -*- coding: utf-8 -*-
"""n+57 第 6 步：跑 `evaluate_tail_spot_check` 並回報——**不宣告終止**。

🚨 n+57 第 6 步明定：**執行室不得宣告終止**，僅回報抽驗結果與評估器輸出。
終止與否由協調者裁定，並須先呈擁有者。

⚠️ 順序證據寫進內容（n+67 四）：記錄所讀入之第 3、4 步雜湊。
⚠️ 八個分塊之順序與完整性逐項斷言，不靠檔名排序推定（n+68 教訓）。
不落地任何文獻內容（n+48 內容制衛生）。
"""
import glob
import io
import json
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.search.statistical_termination import (  # noqa: E402
    evaluate_tail_spot_check)

step3 = json.load(io.open('.scratch/n78_tail_sample.json', encoding='utf-8'))
step4 = json.load(io.open('.scratch/n78_tail_information.json',
                          encoding='utf-8'))
assert step4['readsStep3']['sampleHash'] == step3['sampleHash'], \
    '第 4 步所讀之 sampleHash 與第 3 步不符'
assert step4['informationGap'] == [], \
    '資訊條件未滿足，不得進入第 6 步：%s' % step4['informationGap'][:5]

ids = step3['sample']['candidateIds']
by_short = {c[-8:]: c for c in ids}
assert len(by_short) == len(ids) == 200, (len(by_short), len(ids))

# 八個分塊：逐檔讀入並斷言其涵蓋範圍與樣本順序一致
decisions = {}
chunk_report = []
for lo in range(0, 200, 25):
    path = '.scratch/n78_tail_dec_%03d.json' % lo
    d = json.load(io.open(path, encoding='utf-8'))
    expect = [c[-8:] for c in ids[lo:lo + 25]]
    assert list(d.keys()) == expect, \
        ('%s 之順序與樣本不符' % path, list(d.keys())[:3], expect[:3])
    hits_here = [s for s, v in d.items() if v[0] in ('advance', 'unclear')]
    chunk_report.append((lo, len(d), len(hits_here)))
    for short, (op, _reason) in d.items():
        decisions[by_short[short]] = op

assert len(decisions) == 200, len(decisions)
found = sorted(glob.glob('.scratch/n78_tail_dec_*.json'))
assert len(found) == 8, ('分塊檔數不為 8：%s' % found)

res = evaluate_tail_spot_check(step3['sample'], decisions)

doc = {
    'schemaVersion': 1,
    'documentType': 'termination-tail-spot-check-result',
    'occurrence': 2,
    'step': 'n+57 section 2 step 6 (evaluate and report, do NOT declare)',
    'readsStep3': {'sampleHash': step3['sampleHash'],
                   'seed': step3['sample']['seed'],
                   'anchorValue': step3['anchor']['value'],
                   'overlapWithOccurrence1':
                       step3['previousOccurrence']['overlapWithThisSample']},
    'readsStep4': {'informationConditionHash':
                   step4['informationConditionHash'],
                   'enrichAttempted': step4['enrichAttempted'],
                   'withAbstract': step4['withAbstract'],
                   'informationGapCount': len(step4['informationGap'])},
    'chunks': [{'offset': lo, 'count': n, 'hits': h}
               for lo, n, h in chunk_report],
    'result': res,
    'executorDeclaration': (
        'None. Per n+57 step 6 the executor reports the evaluator output and '
        'does not declare termination; that decision is the coordinator’s '
        'and must go to the owner first.'),
}
doc['resultHash'] = content_hash(res)
io.open('.scratch/n78_tail_result.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))

print('✅ 第 6 步：評估器已執行，結果落盤 → .scratch/n78_tail_result.json')
print()
print('分塊完整性（八檔，順序逐檔斷言）：')
for lo, n, h in chunk_report:
    print('  [%3d:%3d]  %d 筆  命中 %d' % (lo, lo + 25, n, h))
print()
print('評估器輸出（生產程式 `evaluate_tail_spot_check`）：')
print('  sampleSize            %d' % res['sampleSize'])
print('  relevantOrUnclearFound %d 筆 %s'
      % (len(res['relevantOrUnclearFound']),
         [c[-8:] for c in res['relevantOrUnclearFound']]))
print('  resumeScreening       %s' % res['resumeScreening'])
print('  verdict               %s' % res['verdict'])
print('  resultHash            %s' % doc['resultHash'][:40])
print()
print('🚨 依 n+57 第 6 步：執行室只回報，不宣告終止。')
print('   終止與否由協調者裁定，且須先呈擁有者（ADR-0010：宣告篩選完成')
print('   屬研究結論層級，非操作決定）。')
