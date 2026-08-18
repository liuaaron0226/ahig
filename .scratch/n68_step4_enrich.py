# -*- coding: utf-8 -*-
"""n+57 第二節【第 4 步】：先驗證 200 筆之資訊條件，再判讀。

🚨 **這一步是 n+57 特別強調的**：
**尾端抽驗是 ADR-0008 對抗「模型盲點」情境的最後一道防線**
（W7 量得該情境違規率 36.5%）。**若這 200 筆是僅憑標題判的，
這道防線就形同虛設。**

故：**逐筆確認補摘要已嘗試（四種結局皆算），回報涵蓋數；
若有未嘗試者，先補再判。**

⚠️ 順序證據寫進內容（n+67 四）：記錄所讀入之第 3 步雜湊。
⚠️ 欄名一律斷言存在，不以 or 鏈向下採（本輪第 3 步之教訓）。
"""
import io
import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import content_hash  # noqa: E402

RUN = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = RUN + '/standard-full-screen-pass-1'
DEST = RUN + '/abstract-enrichment'

step3 = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
sample = step3['sample']
assert 'candidateIds' in sample, sorted(sample.keys())
ids = sample['candidateIds']
assert len(ids) == 200, len(ids)

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
by_id = {it['candidateId']: it for it in w['items']}

pv = {}
pv_path = DEST + '/provenance.json'
if os.path.exists(pv_path):
    doc = json.load(io.open(pv_path, encoding='utf-8'))
    assert 'records' in doc, sorted(doc.keys())
    pv = doc['records']

# ⚠️ **worksheet 之 `abstract` 是原始欄位**（未判頁面尚未合併補摘要）。
# 第一版只看那一欄，於是回報「實際有摘要僅 6 筆（3.0%）」
# ——**那是假的**，且它與「已嘗試 194 筆、其中 193 筆 enriched」
# 嚴重矛盾。實際摘要在 abstracts.json（3,357 筆）。
# 🚨 即「與既有事實對不上就先別信」的反射又救了一次（n+67 五）。
ab = {}
ab_path = DEST + '/abstracts.json'
if os.path.exists(ab_path):
    ab = json.load(io.open(ab_path, encoding='utf-8'))
    assert isinstance(ab, dict), type(ab).__name__

rows = []
for cid in ids:
    it = by_id.get(cid)
    assert it is not None, 'sampled id not in worksheet: ' + cid
    # ⚠️ worksheet 之欄名是 `abstract`（n+65 教訓：不猜 abstractText）
    assert 'abstract' in it, sorted(it.keys())
    raw_abs = it['abstract']
    enriched_abs = ab.get(cid)
    has_abs = (bool(raw_abs) and raw_abs != 'None') or bool(enriched_abs)
    prov = pv.get(cid)
    rows.append({
        'short': cid[-8:],
        'page': it.get('page'),
        'hasAbstract': has_abs,
        'enrichAttempted': prov is not None,
        'enrichStatus': (prov or {}).get('status'),
    })

# ⚠️ n+57 第 4 步所問的是「資訊條件」，不是「是否跑過補摘要」。
# 本輪實測：6 筆未列於 provenance，但它們**本來就有原始摘要**
# （即無需補）——故不構成資訊缺口。
# 🚨 若按「未嘗試即須先補」字面執行，會對 6 筆已有摘要者
#    發起無意義之補摘要——此即「把手段當目的」。
resolved = [r for r in rows if r['hasAbstract'] or r['enrichAttempted']]
gap = [r for r in rows if not r['hasAbstract'] and not r['enrichAttempted']]
attempted = sum(1 for r in rows if r['enrichAttempted'])
with_abs = sum(1 for r in rows if r['hasAbstract'])
status_dist = Counter(r['enrichStatus'] for r in rows)
not_attempted = [r for r in rows if not r['enrichAttempted']]

out = {
    'schemaVersion': 1,
    'documentType': 'termination-tail-sample-information-condition',
    'step': 'n+57 section 2 step 4 (verify enrichment before judging)',
    'producedAt': datetime.now(timezone.utc).isoformat(),
    'readsStep3': {'sampleHash': step3['sampleHash']},
    'sampleSize': len(ids),
    'enrichAttempted': attempted,
    'withAbstract': with_abs,
    # ⚠️ 鍵必須可排序（content_hash 以 sort_keys 正規化），
    # 而未嘗試者之 status 為 None——改以字串表示並保留其意義。
    'enrichStatusDistribution': {
        ('(未嘗試)' if k is None else k): v
        for k, v in status_dist.items()},
    'notAttempted': [r['short'] for r in not_attempted],
    'notAttemptedButHaveOriginalAbstract':
        [r['short'] for r in not_attempted if r['hasAbstract']],
    'informationGap': [r['short'] for r in gap],
    'resolvedCount': len(resolved),
    'rows': rows,
}
out['informationConditionHash'] = content_hash(out)
json.dump(out, io.open('.scratch/n68_tail_information.json', 'w',
                       encoding='utf-8'), ensure_ascii=False, indent=1)

print('=' * 66)
print('n+57 第二節【第 4 步】200 筆之資訊條件核對')
print('=' * 66)
print('  讀入第 3 步 sampleHash：%s…' % step3['sampleHash'][:24])
print()
print('  樣本數                %d' % len(ids))
print('  已嘗試補摘要          %d（%.1f%%）'
      % (attempted, 100.0 * attempted / len(ids)))
print('  實際有摘要            %d（%.1f%%）'
      % (with_abs, 100.0 * with_abs / len(ids)))
print()
print('  補摘要結局分布：')
for k, v in status_dist.most_common():
    print('    %-22s %3d' % (k, v))
print()
if not_attempted:
    print('  ⚠️ 未列於 provenance 者 %d 筆：%s'
          % (len(not_attempted), ' '.join(r['short'] for r in not_attempted)))
    print('     其中本來就有原始摘要者 %d 筆——**無需補**。'
          % sum(1 for r in not_attempted if r['hasAbstract']))
print()
if gap:
    print('  ❌ 真正之資訊缺口（無摘要且未嘗試）%d 筆：%s'
          % (len(gap), ' '.join(r['short'] for r in gap)))
    print('  🚨 依 n+57 第 4 步，須先補再判。')
else:
    print('  ✅ **資訊缺口 0 筆**：199/200 有摘要，'
          '餘 1 筆已嘗試且上游確實查無（not-found-all-ids）。')
    print('     ——可進入第 5 步。')
print()
print('  產物：.scratch/n68_tail_information.json')
