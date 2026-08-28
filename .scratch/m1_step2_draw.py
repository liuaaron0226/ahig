# -*- coding: utf-8 -*-
"""M1 第 ② 步（其三）：抽出 60 篇校準集。

🚨 種子紀律（n+98 四、n+100 八）：**種子是凍結雜湊的確定性函數，不是記錄下來的隨機值。**

    seed = int.from_bytes(sha256(<用途字串> + <凍結雜湊>).digest()[:8], "big")

**⚠️ 差別很實質**：「記錄種子」靠的是紀律，事後無人能證明沒試過幾次挑一個好看的；
**「由雜湊導出」則使種子無從挑選，且任何人可獨立重算。**
🚨 這正是尾端抽驗最終能成立的原因——協調者用版控裡的母體重跑，逐位相符。

**錨定雜湊取母體清單之 `populationHash`**，涵蓋範圍為
「套用三份 overlay 後之最終判讀狀態（`decisions` 全體 7,631 筆）」
——**⚠️ 本 run 已有三種涵蓋範圍之教訓，故此處明載。**

**每池一個獨立種子**（用途字串含 poolId）：
⚠️ 如此單池若需重抽（例如全文期發現不合格而依 `ineligibleReplacement` 遞補），
**不會擾動其他池**，且每池可各自獨立重算。

抽樣方法照契約 `samplingMethod`：
`random-without-replacement-from-eligible-pool`，池內先 `sorted()` 再抽
——**🚨 排序是必要的：dict 順序不保證跨版本穩定，不排序則「可重現」是假的。**

輸出只有 id 與序位，零文獻內容。
"""
import hashlib
import io
import json
import random
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

DEST = '.scratch/m1_step2_calibration_set.json'
PURPOSE = 'm1-calibration-draw'

a = json.load(io.open('.scratch/m1_step2_assignment.json', encoding='utf-8'))
strata = json.load(io.open('ahig/calibration/b11-carbohydrate/strata.json',
                           encoding='utf-8'))
anchor = a['populationHash']

assert strata['status'] == 'frozen', '🚨 抽樣框非 frozen，不得據以抽樣'
assert strata['totalSampleSize'] == sum(p['quota'] for p in a['pools']), (
    '🚨 池配額合計與契約 totalSampleSize 不符')


def seed_for(pool_id):
    material = ('%s:%s%s' % (PURPOSE, pool_id, anchor)).encode('utf-8')
    return int.from_bytes(hashlib.sha256(material).digest()[:8], 'big')


print('錨定雜湊 %s' % anchor)
print('涵蓋範圍 套用三份 overlay 後之最終判讀狀態（decisions 全體）')
print()
print('%-34s %5s %6s %22s' % ('抽樣池', '配額', '池大小', '種子（前 12 位）'))
print('-' * 74)

draws, all_ids = {}, []
for p in a['pools']:
    pid, quota = p['poolId'], p['quota']
    pool = sorted(p['candidateIds'])
    assert len(pool) >= quota, '🚨 %s 池不足額，不得抽樣' % pid
    seed = seed_for(pid)
    picked = sorted(random.Random(seed).sample(pool, quota))
    draws[pid] = {
        'quota': quota, 'poolSize': len(pool), 'seed': seed,
        'seedMaterial': '%s:%s + populationHash' % (PURPOSE, pid),
        'strata': p['strata'], 'candidateIds': picked,
        'drawHash': content_hash(picked),
    }
    if 'splitNote' in p:
        draws[pid]['splitNote'] = p['splitNote']
    all_ids += picked
    print('%-34s %5d %6d %22d' % (pid, quota, len(pool), seed % 10**12))

print('-' * 74)
print('%-34s %5d %6s   相異 %d' % ('合計', len(all_ids), '', len(set(all_ids))))
assert len(all_ids) == len(set(all_ids)), '🚨 抽出之文獻有重複——互斥性被破壞'
assert len(all_ids) == strata['totalSampleSize'], (
    '🚨 抽出 %d 篇，契約要求 %d 篇' % (len(all_ids), strata['totalSampleSize']))

doc = {
    'schemaVersion': 1,
    'documentType': 'm1-calibration-set',
    'ruling': 'ADR-0010 M1 step 2; rules n+98, pools n+100(2)(3), seed n+98(4)',
    'samplingFrameId': strata['samplingFrameId'],
    'scopeContractHash': strata['scopeContractHash'],
    'anchorHash': anchor,
    'anchorCoverage': ('populationHash of m1_step2_population.json decisions '
                       '(final judgement state for all 7,631 judged records '
                       'after the three overlays)'),
    'seedDerivation': ('int.from_bytes(sha256("%s:<poolId>" + anchorHash)'
                       '.digest()[:8], "big") -- one seed per pool, so a '
                       'single pool can be redrawn without disturbing others'
                       % PURPOSE),
    'samplingMethod': strata['samplingMethod'],
    'totalSampleSize': len(all_ids),
    'draws': draws,
    'pendingFullText': [
        'S5/S6 split by GI primacy (n+100 section 2). Quotas 8+7 unchanged; '
        'if fewer than 8 turn out to have GI as a primary outcome, that is a '
        'finding, not a failure -- record it, do not loosen the criterion.',
        'S1 dose bands: the pool mixes confirmed-moderate with '
        'undetermined-band records (n+100 section 3). Confirm after full '
        'text; if moderate falls short of 12, record it, do not borrow S2.',
    ],
    'contentNote': 'Opaque candidateIds only. No literature content.',
}
doc['calibrationSetHash'] = content_hash(sorted(all_ids))
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('calibrationSetHash %s' % doc['calibrationSetHash'])
print('✅ 已落盤 → %s' % DEST)
print()
print('🚨 可獨立重跑之驗證：任何人取 populationHash 與本檔之 seedDerivation，')
print('   即可重算每池種子並重跑 random.Random(seed).sample(sorted(pool), quota)，')
print('   應逐位相符。⚠️ 這是本檔存在的理由，不是附加說明。')
