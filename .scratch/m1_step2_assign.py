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

## ⚠️ 一項本檔自行採取的保守推論，須協調者確認

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
STRATA = strata['strata']          # 契約既有順序即 S1→S7，決勝順序照用
adv = sorted(c for c, o in pop['decisions'].items() if o == 'advance')


def bands_of(cid):
    ds = q[cid].get('doseSignals') or []
    return {d.get('bandHint') for d in ds if d.get('bandHint')}


def eligible(cid):
    """回傳該筆可歸入之層（未套互斥前）。"""
    outs = set(q[cid].get('outcomeHints') or [])
    bands = bands_of(cid)
    out = []
    for s in STRATA:
        if not (outs & set(s['primaryOutcomes'])):
            continue
        sb = set(s['doseBands'])
        if bands:
            if not (bands & sb):
                continue
        else:
            # 劑量帶未定：僅允許涵蓋全四帶之層（見檔頭之保守推論）
            if sb != ALL_BANDS:
                continue
        out.append(s['stratumId'])
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
    # 🚨 n+98(二)：S5 需要正面證據，沒有證據不等於證據支持。
    # ⚠️ 本檔第一版漏了這條——它讓層序決勝（S5 排在 S6 前）把 3 筆 GI 記錄
    #    分進了 S5，等於用「排序位置」冒充「主要性證據」。
    #    n+98 明文要求未明確者一律暫歸 S6，故此處先剔除 S5 再決勝。
    if not gi_primary_evidence(cid):
        el = [s for s in el if s != 'S5-gi-harms-primary']
    if not el:
        unassigned.append(cid)
        continue
    assign[cid] = el[0]            # (3) 契約層序 S1→S7 決勝
    why[cid] = {'eligible': el, 'bands': sorted(bands_of(cid)) or ['未定'],
                'rule': 'contract-stratum-order' if len(el) > 1 else 'single-match'}

counts = Counter(assign.values())
print()
print('%-34s %6s %10s %s' % ('層', '配額', '已分派', '狀態'))
print('-' * 66)
rows = []
for s in STRATA:
    n = counts.get(s['stratumId'], 0)
    ok = n >= s['quota']
    rows.append({'stratumId': s['stratumId'], 'quota': s['quota'],
                 'assigned': n, 'sufficient': ok})
    print('%-34s %6d %10d %s'
          % (s['stratumId'], s['quota'], n, '✅' if ok else '🚨 不足 %d' % (s['quota'] - n)))
print('-' * 66)
print('%-34s %6d %10d' % ('合計', sum(s['quota'] for s in STRATA), sum(counts.values())))
print()
print('未能分派（無契約結局提示，或劑量帶未定而其層不涵蓋全帶）：%d 筆' % len(unassigned))

short = [r for r in rows if not r['sufficient']]
doc = {
    'schemaVersion': 1,
    'documentType': 'm1-step2-strata-assignment',
    'ruling': 'n+98',
    'doseRuleVersion': RULE,
    'doseRuleNote': ('Loaded from queue doseSignals produced by W3 _dose_signals; '
                     'no conversion rewritten here (n+44).'),
    'populationHash': pop['populationHash'],
    'scopeContractHash': strata.get('scopeContractHash'),
    'conservativeInference': (
        'Records with an undetermined dose band are admitted only to strata '
        'whose doseBands cover all four bands (S3, S6). n+98 names S1/S2 '
        'explicitly; this extends the same logic to S4/S5/S7, which exclude '
        '"low" and therefore cannot admit a record not shown to be non-low. '
        'Executor inference, flagged for coordinator confirmation.'),
    'strata': rows,
    'assignedCount': sum(counts.values()),
    'unassignedCount': len(unassigned),
    'shortfalls': [{'stratumId': r['stratumId'], 'quota': r['quota'],
                    'assigned': r['assigned'],
                    'missing': r['quota'] - r['assigned']} for r in short],
    'assignment': assign,
    'rationale': why,
    'contentNote': 'Opaque candidateIds and stratum ids only. No literature content.',
}
doc['assignmentHash'] = content_hash(doc['assignment'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
if short:
    print('🚨 配額不足之層：')
    for r in short:
        print('   %-34s 缺 %d' % (r['stratumId'], r['quota'] - r['assigned']))
    print('⚠️ 依契約 ineligibleReplacement：同層遞補、記錄理由碼、**不得跨層挪用配額**')
    print('   ——故不足者無法以他層補足，須回報而非自行調整。')
print('✅ 已落盤 → %s' % DEST)
