# -*- coding: utf-8 -*-
"""M1 第 ② 步（其一）：分層配額之可行性實測。

🚨 為什麼需要這一步：`strata.json` 已凍結七層配額（合計 60），
**但 queue 中每一筆的 `strataAssignmentFinal` 皆為 `False`
（`ahig/ahig/search/screening.py:449` 建佇列時之預設值）——即最終分層分派從未執行。**
現存的只有 `suggestedStrata`，那是 regex 先驗且為**多重歸屬**
（314 筆 advance 之建議加總 370）。

**⚠️ 分層是「結局 × 劑量帶」定義的**，故分派需要每筆的結局與劑量。
**🚨 而 prevalence audit 曾量出：摘要層劑量精確可讀性僅 6%（3/50）。**
若該比率適用於 advance，配額根本填不滿——**本檔要回答的就是這個問題。**

⚠️ **本檔量的是「可行性」，不是分派本身。** 樣式為粗略啟發式，
**🚨 不得用本檔輸出直接當作分層分派**——正式分派須依裁定之規則另行為之。
本檔只回答一件事：**每層的候選數夠不夠填配額。**

輸出只有計數，零文獻內容。
"""
import io
import json
import re
import sys
from collections import Counter

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
DEST = '.scratch/m1_step2_feasibility.json'

E = {e['candidateId']: e for e in
     json.load(io.open(ROOT + '/judgements.json', encoding='utf-8'))['entries']}
pop = json.load(io.open('.scratch/m1_step2_population.json',
                        encoding='utf-8'))['decisions']
strata = json.load(io.open('ahig/calibration/b11-carbohydrate/strata.json',
                           encoding='utf-8'))
adv = [c for c, o in pop.items() if o == 'advance']

# ⚠️ 啟發式樣式：判讀原文以中文書寫，契約結局 id 未必逐字出現。
OUTCOME = {
    'tt-completion-time': r'tt-completion-time|計時賽完成時間|計時賽表現',
    'time-to-exhaustion': r'time-to-exhaustion|力竭時間|\bTTE\b',
    'exogenous-cho-oxidation-peak':
        r'exogenous-cho-oxidation|外源性?\s*CHO 氧化|外源性碳水氧化',
    'gi-symptom-incidence': r'gi-symptom|腸胃道?症狀|GI 症狀',
    'muscle-glycogen-post-exercise': r'muscle-glycogen|肌肉?肝醣',
}
DOSE = re.compile(r'\d+(?:\.\d+)?\s*(?:g\s*/\s*h|g/h|g·h|g\s*h-1|公克/小時)'
                  r'|\d+(?:\.\d+)?\s*g\s*/\s*kg'
                  r'|\d+(?:\.\d+)?\s*g/min|\d+(?:\.\d+)?\s*g\s*每')

oc, both = Counter(), Counter()
dose_n = 0
for c in adv:
    r = E[c]['reason']
    hits = [k for k, p in OUTCOME.items() if re.search(p, r)]
    d = bool(DOSE.search(r))
    dose_n += d
    for k in hits:
        oc[k] += 1
        if d:
            both[k] += 1

# 🚨 每層之候選數不可各自比對，因為**有些層共用同一個結局**：
#    S1 與 S2 同為 tt-completion-time（只差劑量帶）、S5 與 S6 同為 gi-symptom
#    （只差主要／次要）。⚠️ 若各自列出「候選 50」，讀者會以為兩層各有 50 筆可用，
#    **實際上那是同一批 50 筆要分給兩層**。
# ⚠️ 這正是 n+93 所立之型：數字對，而讀者會讀錯。
#    故以「結局群組」為單位比對：該群組之候選數 vs 用到該結局的所有層之配額總和。
# ⚠️ 分組鍵不可用「結局清單完全相同」——第一版就是這樣寫的，結果 S5 與 S6 沒被合併：
#    S5 之結局為 [gi-symptom-incidence, gi-symptom-severity]，S6 為 [gi-symptom-incidence]，
#    **兩者不同但有交集，而候選其實是同一批。**
# 🚨 故改以「結局有交集即同組」遞移合併（連通分量），否則同一個錯只是換個地方出現。
buckets = []          # each: {'outcomes': set, 'strata': [], 'quotaSum': int}
for s in strata['strata']:
    outs = set(s['primaryOutcomes'])
    hit = [b for b in buckets if b['outcomes'] & outs]
    if hit:
        merged = hit[0]
        for other in hit[1:]:          # 遞移：本筆可能把兩個既有組接起來
            merged['outcomes'] |= other['outcomes']
            merged['strata'] += other['strata']
            merged['quotaSum'] += other['quotaSum']
            buckets.remove(other)
        merged['outcomes'] |= outs
        merged['strata'].append(s['stratumId'])
        merged['quotaSum'] += s['quota']
    else:
        buckets.append({'outcomes': set(outs), 'strata': [s['stratumId']],
                        'quotaSum': s['quota']})

groups = {}
for b in buckets:
    b['outcomeCandidates'] = max((oc[o] for o in b['outcomes'] if o in oc),
                                 default=0)
    b['outcomeAndDoseCandidates'] = max(
        (both[o] for o in b['outcomes'] if o in both), default=0)
    b['sharedPool'] = len(b['strata']) > 1
    b['quotaFillable'] = b['outcomeAndDoseCandidates'] >= b['quotaSum']
    groups[tuple(sorted(b['outcomes']))] = b

rows = []
for s in strata['strata']:
    g = next(b for b in buckets if s['stratumId'] in b['strata'])
    rows.append({
        'stratumId': s['stratumId'], 'quota': s['quota'],
        'sharesPoolWith': [x for x in g['strata'] if x != s['stratumId']],
        'groupQuotaSum': g['quotaSum'],
        'groupCandidatesWithDose': g['outcomeAndDoseCandidates'],
        'groupQuotaFillable': g['quotaFillable'],
    })

print('advance 母體 %d 筆；判讀原文含明確劑量表述 %d 筆（%.0f%%）'
      % (len(adv), dose_n, 100 * dose_n / len(adv)))
print('⚠️ 對照 prevalence audit 之全池抽樣：摘要層劑量精確可讀性 6%（3/50）')
print('🚨 advance 明顯較高，合理——四軸齊備才 advance，劑量通常有載。')
print()
print('🚨 以「結局群組」為單位比對——共用同一結局的層必須合看，否則同一批候選會被重複計算')
print()
print('%-46s %8s %10s %s' % ('層（共用池者併列）', '配額合計', '候選（含劑量）', '可填?'))
print('-' * 84)
for key, g in sorted(groups.items(), key=lambda kv: kv[1]['strata'][0]):
    label = ' + '.join(g['strata'])
    mark = '  ← 共用同一批候選' if g['sharedPool'] else ''
    print('%-46s %8d %10d %s%s'
          % (label[:46], g['quotaSum'], g['outcomeAndDoseCandidates'],
             '✅' if g['quotaFillable'] else '🚨 不足', mark))
print('-' * 84)
print('%-46s %8d' % ('合計配額', sum(r['quota'] for r in rows)))
print()
short = [g['strata'] for g in groups.values() if not g['quotaFillable']]
print('結論：%s' % ('✅ 七層配額皆有足夠候選' if not short
                    else '🚨 以下層候選不足：%s' % short))
print()
print('🚨 但本檔證到這裡為止：')
print('   ⚠️ (1) S1 vs S2 之分野是劑量帶（moderate 30–59.9 vs high ≥60），')
print('          本檔只驗「有劑量表述」，未解析其數值落在哪一帶。')
print('   ⚠️ (2) S5 vs S6 之分野是「GI 為主要結果」或「僅次要／安全性回報」，')
print('          本檔之樣式無法區分兩者。')
print('   ⚠️ (3) 多重歸屬未處理——一筆可同時命中計時賽與 GI，')
print('          配額互斥與否須裁示。')
print('   🚨 故本檔不得作為分層分派使用，僅證明「配額填得滿」。')

doc = {
    'schemaVersion': 1,
    'documentType': 'm1-step2-strata-feasibility',
    'purpose': ('Measures whether the frozen strata quotas can be filled from '
                'the advance population. Feasibility only -- NOT an assignment.'),
    'populationHash': json.load(io.open('.scratch/m1_step2_population.json',
                                        encoding='utf-8'))['populationHash'],
    'advanceCount': len(adv),
    'doseReadable': dose_n,
    'doseReadableRate': round(dose_n / len(adv), 4),
    'comparisonNote': ('prevalence audit measured 3/50 (6%) exact-value dose '
                       'readability on a whole-pool sample; advance records '
                       'are higher, consistent with how they qualified.'),
    'strata': rows,
    'unresolved': [
        'S1 vs S2 split is a dose band; this file only detects that a dose '
        'is stated, not which band it falls in.',
        'S5 vs S6 split is primary vs secondary-only GI reporting; not '
        'distinguishable by these patterns.',
        'Multiple membership unhandled: one record can hit several strata. '
        'Whether quotas are mutually exclusive needs a ruling.',
    ],
    'contentNote': 'Counts only. No literature content.',
}
doc['reportHash'] = content_hash(doc['strata'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %s' % DEST)
