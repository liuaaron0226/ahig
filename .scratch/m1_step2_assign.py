# -*- coding: utf-8 -*-
"""M1 第 ② 步（其二）：依 n+98 之三項規則做互斥分層分派。

🚨 規則來源一律為 n+98，不自創：

**一、劑量帶**：載入 W3 之 `_dose_signals`（`RULE_VERSION b11-screening/1.5.0`）
之產物，即 queue 中既有之 `doseSignals[].bandHint`
——**⚠️ 依 n+44「判準即產物，重算一律載入原件、不得重打」，本檔不另寫換算。**
（已核對 `screening-queue/manifest.json` 之 `screeningRuleVersion` 確為 1.5.0。）
**換算不出者列為「劑量帶未定」。**

**二、S5 vs S6**：摘要**未明確**將 GI 列為主要或共同主要者，**一律暫歸 S6**
——**🚨 S5 是較強的主張，需要正面證據；沒有證據不等於證據支持。**
⚠️ 題摘層之 `outcomeHints` 不帶「主要性」資訊，故本階段**無任何記錄可正面歸入 S5**。

**三、互斥**：`totalSampleSize` 60 ＝ 七層配額合計 60 → 須為 60 篇相異文獻。
優先序（依契約 rationale，非依池況）：
  (1) GI 為主要或共同主要 → 優先 S5；
  (2) 其餘依自身主要結果歸層；
  (3) 仍無法分辨 → **以契約既有之層序 S1→S7 決勝**。

## n+100 之調整（本版）

1. **S5／S6 合併為一個抽樣池，配額 15（＝8＋7）**——n+100（二）採（丙）：
   **⚠️ S5 的 8 個名額不是缺額，是分派時機錯了。**
   契約 `ineligibleReplacement` 禁的是「跨層挪用配額」，
   **🚨 沒有禁「同一筆記錄在資訊足夠後歸到正確的層」**；
   全文取得後依 GI 之主要性再分為 S5／S6。
   **🚫 不得為了填滿 8 篇而放寬主要性判準**——若全文期發現 GI 為主要者不足 8 篇，
   **那不是失敗，那正是 S5 被設計出來要量到的事實。**
2. **S1 之候選池擴大為「已定 moderate ∪ 劑量帶未定之 TT」**——n+100（三）：
   其不足屬「資訊未解析」而非「欄位不存在」，**全文期解析劑量帶後確認歸屬**。
   **🚫 若解析後 moderate 不足 12，如實記載，不得自 S2 挪用。**
3. **各池落盤 `candidateIds` 清單**——n+100（一）：
   **🚨 前一版只存筆數，協調者因此驗不到互斥性。**
   ⚠️ 與尾端抽樣當初同型：產物記錄了結果，卻不足以讓別人重驗結果。

## ⚠️ 一項本檔自行採取的保守推論（n+100 四已照准）

n+98 明文只說「換算不出者**不得歸入 S1／S2**」。
**🚨 但同樣的道理及於任何 `doseBands` 不涵蓋全部四帶的層**：
S4／S5／S7 之 `doseBands` 不含 `low`，**而「未定」不能證明它不是 low**。
**故本檔將「劑量帶未定」者僅允許歸入 doseBands 涵蓋全四帶之層（S3、S6）。**
⚠️ 這是本室的推論而非裁定，**已在看板列為待確認**；
若協調者認為未定者亦可歸 S4／S5／S7，改一個常數即可重跑。

輸出只有 id 與層別，零文獻內容。
"""
import io
import json
import sys
from collections import Counter, defaultdict

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run')
DEST = '.scratch/m1_step2_assignment.json'

pop = json.load(io.open('.scratch/m1_step2_population.json', encoding='utf-8'))
q = {r['candidateId']: r for r in
     json.load(io.open(ROOT + '/screening-queue/queue.json', encoding='utf-8'))}
manifest = json.load(io.open(ROOT + '/screening-queue/manifest.json',
                             encoding='utf-8'))
strata = json.load(io.open('ahig/calibration/b11-carbohydrate/strata.json',
                           encoding='utf-8'))

RULE = manifest.get('screeningRuleVersion')
assert RULE == 'b11-screening/1.5.0', (
    '🚨 queue 之 screeningRuleVersion 為 %s，非 n+98 指定之 1.5.0——'
    '在查明前不得沿用其 doseSignals' % RULE)
print('✅ queue 之 screeningRuleVersion = %s（n+98 指定者）' % RULE)

ALL_BANDS = {'low', 'moderate', 'high', 'very-high'}
BY_ID = {s['stratumId']: s for s in strata['strata']}
adv = sorted(c for c, o in pop['decisions'].items() if o == 'advance')

# 抽樣池：順序即契約層序 S1→S7（合併池置於 S5 之位），決勝順序照用。
# `undetermined` 表示該池是否收「劑量帶未定」者。
POOLS = [
    {'poolId': 'S1-tt-moderate-dose', 'quota': 12,
     'outcomes': {'tt-completion-time'}, 'bands': {'moderate'},
     'undetermined': True,          # n+100(三)
     'strata': ['S1-tt-moderate-dose']},
    {'poolId': 'S2-tt-high-and-very-high-dose', 'quota': 10,
     'outcomes': {'tt-completion-time'}, 'bands': {'high', 'very-high'},
     'undetermined': False,
     'strata': ['S2-tt-high-and-very-high-dose']},
    {'poolId': 'S3-tte', 'quota': 8,
     'outcomes': {'time-to-exhaustion'}, 'bands': set(ALL_BANDS),
     'undetermined': True,
     'strata': ['S3-tte']},
    {'poolId': 'S4-exogenous-oxidation', 'quota': 10,
     'outcomes': {'exogenous-cho-oxidation-peak'},
     'bands': {'moderate', 'high', 'very-high'}, 'undetermined': False,
     'strata': ['S4-exogenous-oxidation']},
    {'poolId': 'S5+S6-gi-merged', 'quota': 15,
     'outcomes': {'gi-symptom-incidence', 'gi-symptom-severity'},
     'bands': set(ALL_BANDS), 'undetermined': True,
     'strata': ['S5-gi-harms-primary', 'S6-gi-harms-secondary-only'],
     'splitNote': ('Merged per n+100(2). Split into S5/S6 after full text, '
                   'by whether GI is a primary/co-primary outcome. '
                   'Quotas 8+7 unchanged; no cross-stratum borrowing.')},
    {'poolId': 'S7-glycogen', 'quota': 5,
     'outcomes': {'muscle-glycogen-post-exercise'},
     'bands': {'moderate', 'high'}, 'undetermined': False,
     'strata': ['S7-glycogen']},
]


def bands_of(cid):
    ds = q[cid].get('doseSignals') or []
    return {d.get('bandHint') for d in ds if d.get('bandHint')}


def eligible(cid):
    """回傳該筆可歸入之池（未套互斥前），順序即契約層序。"""
    outs = set(q[cid].get('outcomeHints') or [])
    bands = bands_of(cid)
    out = []
    for p in POOLS:
        if not (outs & p['outcomes']):
            continue
        if bands:
            if not (bands & p['bands']):
                continue
        elif not p['undetermined']:
            continue          # 劑量帶未定，而本池不收未定者
        out.append(p['poolId'])
    return out


def gi_primary_evidence(cid):
    """題摘層是否有「GI 為主要或共同主要結果」之**正面**證據。

    🚨 本函式恆回傳 False，而那是裁定的結果，不是偷懶：
    n+98(二) 明示「摘要**未明確**將 GI 列為主要或共同主要者，**一律暫歸 S6**」，
    且 `outcomeHints` 只記「有沒有提到這個結局」，**不帶主要性資訊**。
    ⚠️ 故題摘層不存在可據以正面歸 S5 的欄位。
    🚨 保留本函式而非直接刪除 S5 分支，是為了讓全文期複核時有明確的接點。
    """
    return False


assign, why, unassigned = {}, {}, []
for cid in adv:
    el = eligible(cid)
    # 🚨 n+98(二) 之 S5 問題，於本版已由 n+100(二) 之合併池吸收：
    #    S5 與 S6 併為一池，主要性之判定整個移到全文期。
    # ⚠️ 保留 gi_primary_evidence() 不刪，是為了讓全文期複核有明確接點——
    #    屆時它會回傳真值，而合併池即依其結果拆分。
    if not el:
        unassigned.append(cid)
        continue
    assign[cid] = el[0]            # 契約層序決勝（合併池置於 S5 之位）
    why[cid] = {'eligible': el, 'bands': sorted(bands_of(cid)) or ['未定'],
                'rule': 'contract-stratum-order' if len(el) > 1 else 'single-match'}

members = defaultdict(list)
for cid, pid in assign.items():
    members[pid].append(cid)
for pid in members:
    members[pid].sort()

# 🚨 互斥性：本檔自證一次，不要協調者代勞發現問題。
seen = set()
dupes = []
for pid, ids in members.items():
    for cid in ids:
        if cid in seen:
            dupes.append(cid)
        seen.add(cid)
assert not dupes, '🚨 同一筆出現在多個池：%s' % dupes[:5]
print('✅ 互斥性自證：%d 筆分派、%d 筆相異，無重複' % (len(assign), len(seen)))

print()
print('%-34s %6s %10s %s' % ('抽樣池', '配額', '可用', '狀態'))
print('-' * 68)
rows = []
for pmeta in POOLS:
    pid = pmeta['poolId']
    ids = members.get(pid, [])
    ok = len(ids) >= pmeta['quota']
    rows.append({
        'poolId': pid, 'quota': pmeta['quota'], 'available': len(ids),
        'sufficient': ok, 'strata': pmeta['strata'],
        'candidateIds': ids,
        'candidateIdsHash': content_hash(ids),
        'coverage': ('all advance records assigned to this pool under the '
                     'n+98/n+100 rules; mutually exclusive across pools'),
    })
    print('%-34s %6d %10d %s'
          % (pid, pmeta['quota'], len(ids),
             '✅' if ok else '🚨 不足 %d' % (pmeta['quota'] - len(ids))))
print('-' * 68)
print('%-34s %6d %10d' % ('合計', sum(p['quota'] for p in POOLS), len(assign)))
print()
print('未能分派：%d 筆（無契約結局提示，或劑量帶未定而其池不收未定者）' % len(unassigned))

short = [r for r in rows if not r['sufficient']]
doc = {
    'schemaVersion': 1,
    'documentType': 'm1-step2-strata-assignment',
    'ruling': 'n+98; pools adjusted per n+100(2)(3)',
    'doseRuleVersion': RULE,
    'doseRuleNote': ('Loaded from queue doseSignals produced by W3 _dose_signals; '
                     'no conversion rewritten here (n+44).'),
    'populationHash': pop['populationHash'],
    'scopeContractHash': strata.get('scopeContractHash'),
    'mutualExclusivity': {
        'verifiedInThisScript': True,
        'assigned': len(assign), 'distinct': len(seen),
        'note': ('Each advance record appears in at most one pool. '
                 'candidateIds are filed per pool so this is independently '
                 'checkable (n+100 section 1).'),
    },
    'conservativeInference': (
        'Records with an undetermined dose band are admitted only to pools '
        'that accept them (S1 and S3 and the merged GI pool). Pools whose '
        'doseBands exclude "low" cannot admit a record not shown to be '
        'non-low. Approved by n+100 section 4, with the cost to be stated in '
        'M1: a small candidate pool here reflects missing information, not '
        'the distribution of the literature.'),
    'pools': rows,
    'assignedCount': len(assign),
    'unassignedCount': len(unassigned),
    'shortfalls': [{'poolId': r['poolId'], 'quota': r['quota'],
                    'available': r['available'],
                    'missing': r['quota'] - r['available']} for r in short],
    'assignment': assign,
    'rationale': why,
    'contentNote': 'Opaque candidateIds and pool ids only. No literature content.',
}
doc['assignmentHash'] = content_hash(doc['assignment'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
if short:
    print('🚨 配額不足之池：')
    for r in short:
        print('   %-34s 缺 %d' % (r['poolId'], r['quota'] - r['available']))
else:
    print('✅ 六個抽樣池全部足額，可執行抽樣。')
print('✅ 已落盤 → %s' % DEST)
