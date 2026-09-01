# -*- coding: utf-8 -*-
"""**卡在劑量那一關的，落在哪些結局上。**（第 645 輪）

## ⚠️ 先講本輪差點犯的錯

🚨 本室查到「劑量那一碼其實是三件事：沒報 12／真的帶外 3／對照組 4」，
**⚠️ 而那正是第 588 輪的 headline**——第 589 輪還追過那 12 項救不救得回。
**✅ 本室先查了舊憑證才動筆，🚫 沒有把舊發現當新的講。**

## 🚨 但有一件那兩支都沒說：**那 12 項落在哪些結局上**

⚠️ 第 628／632 輪已量出「計時賽完成時間」是最薄的結局
（5 篇、最大可比組 2 篇）。
**🚨 若卡在門外的那些正好也集中在它身上，那薄的地方就不只是薄，是被自己的資料處理擋住。**

## 🚫 本支不改任何清冊、不送外部請求、不改任何產品程式
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n645_dose_gate_by_outcome.json'


def main():
    blocked = []
    in_scope = collections.Counter()
    in_scope_papers = collections.defaultdict(set)
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        for outcome in doc.get('reportedOutcomes') or []:
            decision = outcome.get('scopeDecision') or {}
            ref = outcome.get('normalisedOutcomeRef')
            if decision.get('inScope'):
                in_scope[ref] += 1
                in_scope_papers[ref].add(report)
            elif decision.get('reasonCode') == 'notExtracted-dose-outside-bands':
                dose = outcome.get('dose')
                blocked.append({
                    'report': report, 'outcome': ref, 'dose': dose,
                    'kind': ('沒有記劑量' if dose is None
                             else ('對照組（0）' if float(dose) == 0
                                   else '真的在帶外')),
                })

    by_kind = collections.Counter(row['kind'] for row in blocked)
    no_dose = [row for row in blocked if row['kind'] == '沒有記劑量']
    no_dose_by_outcome = collections.Counter(row['outcome'] for row in no_dose)
    no_dose_papers = collections.defaultdict(set)
    for row in no_dose:
        no_dose_papers[row['outcome']].add(row['report'])

    comparison = []
    for ref in sorted(set(in_scope) | set(no_dose_by_outcome),
                      key=lambda r: -no_dose_by_outcome[r]):
        comparison.append({
            'outcome': ref,
            'inScopeItems': in_scope[ref],
            'inScopePapers': len(in_scope_papers[ref]),
            'blockedForMissingDose': no_dose_by_outcome[ref],
            'blockedPapers': len(no_dose_papers[ref]),
            'blockedExceedsInScope':
                no_dose_by_outcome[ref] > in_scope[ref],
        })

    worse = [row for row in comparison if row['blockedExceedsInScope']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('三分法與第 588 輪相符（必觸發之正對照）',
          by_kind['沒有記劑量'] == 12 and by_kind['真的在帶外'] == 3
          and by_kind['對照組（0）'] == 4,
          '🚨 實得 %s；⚠️ 與第 588 輪（12／3／4）對不上就代表資料變了，'
          '而本支的新數字也就不能信' % dict(by_kind))
    probe('在範圍內那側數得出來（必觸發之正對照）',
          sum(in_scope.values()) == 98,
          '🚨 在範圍內合計 %d 項；⚠️ 不是 98 就代表本支讀的不是同一批'
          % sum(in_scope.values()))
    # 🚨 這一道是本輪的發現。
    probe('沒有結局「卡在門外的比進來的還多」',
          not worse,
          '🚨 實得 %s'
          % [(r['outcome'], '門外 %d 項 vs 在內 %d 項（%d 篇 vs %d 篇）'
              % (r['blockedForMissingDose'], r['inScopeItems'],
                 r['blockedPapers'], r['inScopePapers']))
             for r in worse])

    doc = {
        'schemaVersion': 1,
        'documentType': 'dose-gate-by-outcome',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'creditsPriorRounds': (
            '✅ 三分法（沒報 12／帶外 3／對照組 4）是**第 588 輪**的發現，'
            '⚠️ 第 589 輪追過那 12 項的可救回性（只有 1 篇在方法段寫明速率）。'
            '**🚫 本支不重複宣稱它們**；🚨 本支新加的只有一件：**逐結局的分布**。'),
        'blockedByKind': dict(by_kind),
        'missingDoseByOutcome': dict(no_dose_by_outcome.most_common()),
        'comparison': comparison,
        'headline': (
            '🚨 那 12 項沒有劑量的，有 **%d 項是 `tt-completion-time`**——'
            '⚠️ 而該結局目前在範圍內只有 %d 項（%d 篇）。'
            '**🚨 即卡在門外的計時賽項目比進得來的還多。**'
            % (no_dose_by_outcome['tt-completion-time'],
               in_scope['tt-completion-time'],
               len(in_scope_papers['tt-completion-time']))),
        'whyItMatters': (
            '⚠️ 第 628／632 輪量出計時賽是最薄的結局（5 篇、最大可比組 2 篇）。'
            '🚨 本支顯示：**薄的地方不只是薄，還有一批同樣的結局卡在門外**，'
            '而擋住它們的不是文獻沒有做，是**清冊裡那一格沒有填**。'
            '✅ 第 589 輪查過：其中 1 篇的方法段寫著 1.8 g/min（＝108 g/h），'
            '⚠️ 讀的人留空——**🚫 而那一篇正是計時賽。**'),
        'whatThisCannotAnswer': (
            '🚫 本支不判斷那 12 項該不該救回——⚠️ 第 589 輪已說明：'
            '單位換算與濃度×體積推算不是同一件事，🚨 本室不逕自換算。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n645 劑量關卡的逐結局分布 ===')
    print('   卡在劑量碼的 %d 項：%s' % (len(blocked), dict(by_kind)))
    print('   %-30s %8s %8s %10s %8s'
          % ('結局', '在內項數', '在內篇數', '門外(沒劑量)', '門外篇數'))
    for row in comparison:
        print('   %-30s %8d %8d %10d %8d %s'
              % (row['outcome'], row['inScopeItems'], row['inScopePapers'],
                 row['blockedForMissingDose'], row['blockedPapers'],
                 '🚨 門外比在內多' if row['blockedExceedsInScope'] else ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
