# -*- coding: utf-8 -*-
"""**有幾篇提供「同一篇之內」的多劑量對比。**（第 710 輪）

## ✅ 為什麼這一格沒人做過

- 第 626 輪算的是**跨篇**的劑量分布，⚠️ 而且刻意**每篇只取一個值**
  （避免同篇多手臂重複計票）。
- 第 632 輪算的是**可合併性**的軸（分析集、效應量測），🚫 不是劑量。

> **🚨 而擁有者要的是劑量-反應。**
> ⚠️ 那需要**同一篇之內的多劑量對比**（最乾淨），
> 🚫 或退而求其次靠跨篇的劑量變異（受混淆影響大得多）。
> **✅ 前者本室從來沒數過。**

## ✅ 本支怎麼數

對**在範圍內**的項目，逐（篇 × 契約結局）數**相異的劑量值**：

- **≥ 2 個** → 該篇對該結局提供了**同篇內的對比**
- **1 個** → 只有單一劑量

⚠️ 對照組（0 g/h）本來就落在帶外、不在範圍內，🚫 故不列入。

## 🚫 本支不改任何清冊與契約、不送外部請求、不輸出標籤文字
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
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n710_within_study_dose_contrast.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')
# ✅ 已知的多手臂正對照（第 663 輪：0／45／90，其中 45 與 90 在範圍內）
KNOWN_MULTI = '307c0dd5b141caed'


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    doses = collections.defaultdict(set)
    units = collections.Counter()
    in_scope = 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        report = inventory['report'][-16:]
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if not decision['inScope']:
                continue
            in_scope += 1
            dose = reported.get('dose')
            if dose is None:
                continue
            units[str(reported.get('doseUnit'))] += 1
            doses[(report, reported['normalisedOutcomeRef'])].add(float(dose))

    by_outcome = collections.defaultdict(
        lambda: {'papersSingleDose': set(), 'papersMultiDose': set(),
                 'doseLevels': set()})
    for (report, ref), values in doses.items():
        bucket = by_outcome[ref]
        bucket['doseLevels'] |= values
        if len(values) >= 2:
            bucket['papersMultiDose'].add(report)
        else:
            bucket['papersSingleDose'].add(report)

    summary = {}
    for ref, bucket in sorted(by_outcome.items()):
        summary[ref] = {
            'papersWithDose': len(bucket['papersSingleDose']
                                  | bucket['papersMultiDose']),
            'papersMultiDose': len(bucket['papersMultiDose']),
            'papersSingleDose': len(bucket['papersSingleDose']),
            'distinctDoseLevels': len(bucket['doseLevels']),
            'doseRange': ([min(bucket['doseLevels']),
                           max(bucket['doseLevels'])]
                          if bucket['doseLevels'] else None),
            'multiDoseReports': sorted(bucket['papersMultiDose']),
        }

    total_multi = len({r for b in by_outcome.values()
                       for r in b['papersMultiDose']})
    outcomes_without_multi = sorted(
        ref for ref, s in summary.items() if s['papersMultiDose'] == 0)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('數到的正是那 98 項在範圍內的（必觸發之正對照）',
          in_scope == 98,
          '🚨 在範圍內 %d 項；⚠️ 對不上就與前幾輪不一致' % in_scope)
    probe('劑量欄真的有值可數（必觸發之反向）',
          sum(units.values()) > 0 and len(doses) > 0,
          '🚨 有劑量的項目 %d 個、單位分佈 %s、（篇×結局）組合 %d 個；'
          '⚠️ 若是 0，本支量的是空氣'
          % (sum(units.values()), dict(units), len(doses)))
    probe('已知的多手臂那一篇被認出來（必觸發之正對照）',
          any(KNOWN_MULTI in s['multiDoseReports']
              for s in summary.values()),
          '🚨 `%s` 出現在多劑量清單裡：%s；'
          '⚠️ 認不出來代表本支的判準沒接上'
          % (KNOWN_MULTI,
             [ref for ref, s in summary.items()
              if KNOWN_MULTI in s['multiDoseReports']] or '無'))
    # 🚨 這一道是答案。
    probe('每個結局都有論文提供同篇內的多劑量對比',
          not outcomes_without_multi,
          '🚨 完全沒有同篇內對比的結局 %d 個：%s；'
          '⚠️ 那些結局的劑量-反應**只能靠跨篇比較**，'
          '**🚨 而跨篇比較受混淆影響大得多**'
          % (len(outcomes_without_multi), outcomes_without_multi))

    doc = {
        'schemaVersion': 1,
        'documentType': 'within-study-dose-contrast',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'whyNotCoveredBefore': (
            '⚠️ 第 626 輪算的是**跨篇**分布且**每篇只取一個值**；'
            '🚫 第 632 輪算的是可合併性的軸，不是劑量。'
            '**✅ 同篇內的多劑量對比，本室從來沒數過。**'),
        'inScopeItems': in_scope,
        'papersWithAnyWithinStudyContrast': total_multi,
        'byOutcome': summary,
        'outcomesWithoutAnyContrast': outcomes_without_multi,
        'whyItMatters': (
            '🚨 劑量-反應最乾淨的證據是**同一篇之內的多劑量對比**——'
            '⚠️ 同一群人、同一套方法、同一個量測。'
            '🚫 跨篇比較則把劑量差異與族群、方法、儀器的差異綁在一起。'
            '**✅ 故「有幾篇提供同篇內對比」是這份審查能不能談劑量-反應的上限之一。**'),
        'whatThisCannotAnswer': (
            '🚫 本支**不看數值**——⚠️ 第 659 輪已證那 98 項沒有效應量。'
            '🚨 故「有對比」只代表**設計上有兩個劑量臂**，'
            '**🚫 不代表算得出劑量-反應**（那要等 `D25`）。'
            '⚠️ 又：劑量空白的項目（第 645 輪那 12 項）在本支裡不算數，'
            '🚨 故這是**下界**。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n710 同一篇之內的多劑量對比 ===')
    print('   在範圍內 %d 項｜有任何同篇內對比的論文 %d 篇'
          % (in_scope, total_multi))
    print('   逐結局（有劑量的篇／其中多劑量／單劑量／相異劑量級數／範圍）：')
    for ref, s in summary.items():
        print('      %-32s %2d ／ %2d ／ %2d ／ %2d ／ %s'
              % (ref, s['papersWithDose'], s['papersMultiDose'],
                 s['papersSingleDose'], s['distinctDoseLevels'],
                 s['doseRange']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
