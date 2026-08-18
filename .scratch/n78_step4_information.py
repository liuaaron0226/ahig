# -*- coding: utf-8 -*-
"""n+57 第 4 步：判讀前先驗證這 200 筆的資訊條件（第二次觸發）。

n+57 第 4 步之理由：**尾端抽驗是 ADR-0008 對抗「模型盲點」情境的最後一道
防線**（W7 量得該情境違規率 36.5%）。**若這 200 筆是僅憑標題判的，這道
防線就形同虛設。** 故先逐筆確認補摘要已嘗試（四種結局皆算），有未嘗試者
先補再判。

⚠️ 本檔與第 3 步之連結寫在內容裡（`readsStep3.sampleHash`），不靠檔名或
執行順序——n+68 之教訓。
不落地任何摘要內容，只記布林值與狀態碼（n+48 內容制衛生）。
"""
import collections
import io
import json
import sys
from pathlib import Path

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

ROOT = Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
            r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = ROOT / 'standard-full-screen-pass-1'

step3 = json.load(io.open('.scratch/n78_tail_sample.json', encoding='utf-8'))
ids = step3['sample']['candidateIds']
assert len(ids) == 200, len(ids)

w = json.loads((OUT / 'worksheet.json').read_text(encoding='utf-8'))
by_id = {it['candidateId']: it for it in w['items']}

# 🚨 第一版我把補摘要來源猜成 abstract-enrichment/*.json 的 `entries`，
# 量到「已嘗試 0、有摘要 5、資訊缺口 195」。與第一次觸發同一步驟所量之
# 「已嘗試 194、有摘要 199」嚴重矛盾——**矛盾就先別信自己這一版**（n+67 五）。
# 查 `.scratch/n68_step4_enrich.py`：正確來源是
#   provenance.json 的 `records`（補摘要嘗試紀錄）
#   abstracts.json（補到的摘要本體）
# 且 worksheet 之 `abstract` 欄是**原始欄位**，未判頁面尚未合併補摘要，
# 只看它會低估。三個來源缺一不可。
DEST = ROOT / 'abstract-enrichment'
pv_doc = json.loads((DEST / 'provenance.json').read_text(encoding='utf-8'))
assert 'records' in pv_doc, sorted(pv_doc.keys())
pv = pv_doc['records']
ab = json.loads((DEST / 'abstracts.json').read_text(encoding='utf-8'))
assert isinstance(ab, dict), type(ab).__name__

rows = []
for cid in ids:
    it = by_id.get(cid)
    assert it is not None, 'sampled id not in worksheet: ' + cid
    assert 'abstract' in it, sorted(it.keys())
    raw_abs = it['abstract']
    has_abs = ((bool(raw_abs) and raw_abs != 'None') or bool(ab.get(cid)))
    prov = pv.get(cid)
    rows.append({
        'short': cid[-8:],
        'page': it.get('page'),
        'hasAbstract': has_abs,
        'enrichAttempted': prov is not None,
        'enrichStatus': ((prov or {}).get('status') or '(未嘗試)'),
    })

dist = collections.Counter(r['enrichStatus'] for r in rows)
attempted = sum(1 for r in rows if r['enrichAttempted'])
with_abs = sum(1 for r in rows if r['hasAbstract'])
not_attempted = [r for r in rows if not r['enrichAttempted']]
# ⚠️ n+57 第 4 步所問的是「資訊條件」，不是「是否跑過補摘要」。
# 未嘗試但本來就有摘要者無需補，不構成資訊缺口；照字面執行會對已有摘要者
# 發起無意義之補摘要——把手段當目的（第一次觸發時已立此判準）。
na_but_have = [r for r in not_attempted if r['hasAbstract']]
gap = [r for r in not_attempted if not r['hasAbstract']]

doc = {
    'schemaVersion': 1,
    'documentType': 'termination-tail-sample-information-condition',
    'occurrence': 2,
    'step': 'n+57 section 2 step 4 (verify enrichment before judging)',
    'readsStep3': {
        'sampleHash': step3['sampleHash'],
        'seed': step3['sample']['seed'],
        'anchorValue': step3['anchor']['value'],
        'overlapWithOccurrence1': step3['previousOccurrence'][
            'overlapWithThisSample'],
    },
    'sampleSize': len(rows),
    'enrichAttempted': attempted,
    'withAbstract': with_abs,
    'enrichStatusDistribution': dict(dist),
    'notAttempted': [r['short'] for r in not_attempted],
    'notAttemptedButHaveOriginalAbstract': [r['short'] for r in na_but_have],
    'informationGap': [r['short'] for r in gap],
    'resolvedCount': len(rows) - len(gap),
    'rows': rows,
}
doc['informationConditionHash'] = content_hash(
    {'rows': rows, 'sampleHash': step3['sampleHash']})

io.open('.scratch/n78_tail_information.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))

print('✅ 第 4 步：資訊條件已驗證並落盤')
print('   樣本 %d 筆' % len(rows))
print('   有摘要        %d' % with_abs)
print('   補摘要已嘗試   %d' % attempted)
print('   狀態分布      %s' % dict(dist))
print('   未嘗試但原有摘要 %d' % len(na_but_have))
print()
if gap:
    print('🚨 資訊缺口 %d 筆（無摘要且未嘗試補）：%s'
          % (len(gap), [r['short'] for r in gap]))
    print('⚠️ 依 n+57 第 4 步，須先補再判。')
else:
    print('✅ 資訊缺口 0 筆——200 筆皆非「僅憑標題可判」之狀態，可進入第 5 步。')
