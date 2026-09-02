# -*- coding: utf-8 -*-
"""**修 `D24` 而不裁 `D3`，會不會把同一組人算兩次。**（第 701 輪）

## ✅ 為什麼是這一題

第 699 輪把 `D3`（論文／期刊那一對要不要併成一個 study）排進最前面。
🚨 而第 584 輪早就寫著：

> 「📮 重讀 `7a6ac1559c740fd6` **不能單獨做**：必須與『這兩筆算一個 study』
> 一起決定，⚠️ 否則修好一個缺陷會製造另一個。」

**⚠️ 但那句話沒有數字。本支把數字算出來。**

## ✅ 三種狀態

| | 論文半 `307c0dd5b141caed` | 期刊半 `7a6ac1559c740fd6` |
|---|---|---|
| **現況** | 在範圍內 N 項 | **0 項**（六項宣告全被儀器清單擋掉） |
| **若修 `D24`**（只換儀器名稱） | 不變 | 拿回 M 項 |

🚨 **若那 M 項與論文半的 N 項落在**同一組結局**上，
⚠️ 那就是同一批受試者被算兩次。**

## ✅ 反事實用的是**第 663 輪已證過的那組換名**，🚫 不是本支新編的

## 🚫 本支不改任何清冊與契約（反事實在記憶體副本上做）、不送外部請求
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

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n701_d3_d24_interlock.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

THESIS = '307c0dd5b141caed'
JOURNAL = '7a6ac1559c740fd6'
# ✅ 第 663 輪已證過的那組換名（🚫 本支不新編）
SWAP = {
    'cycling-time-to-exhaustion-fixed-power': 'cycling-tte-fixed-intensity',
    'acid-hydrolysis-freeze-dried-biopsy': 'needle-biopsy-vastus-lateralis',
}


def load(report_suffix):
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        if doc['report'].endswith(report_suffix):
            return doc
    return None


def in_scope_by_outcome(matcher, inventory):
    counts = collections.Counter()
    verdict = matcher.decide_inventory(inventory)
    for reported, decision in zip(inventory['reportedOutcomes'],
                                  verdict['decisions']):
        if decision['inScope']:
            counts[reported['normalisedOutcomeRef']] += 1
    return counts


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    thesis = load(THESIS)
    journal = load(JOURNAL)
    if thesis is None or journal is None:
        print('🚨 那一對的清冊找不到，本支無從算起')
        return 1

    thesis_now = in_scope_by_outcome(matcher, thesis)
    journal_now = in_scope_by_outcome(matcher, journal)

    # ✅ 反事實：只換儀器名稱（第 663 輪那一組）。
    swapped = json.loads(json.dumps(journal))
    swaps = 0
    for reported in swapped['reportedOutcomes']:
        name = reported.get('instrument')
        if name in SWAP:
            reported['instrument'] = SWAP[name]
            swaps += 1
    journal_fixed = in_scope_by_outcome(matcher, swapped)

    overlap = {ref: (thesis_now[ref], journal_fixed[ref])
               for ref in sorted(set(thesis_now) & set(journal_fixed))}
    only_thesis = sorted(set(thesis_now) - set(journal_fixed))
    only_journal = sorted(set(journal_fixed) - set(thesis_now))
    double_counted = sum(min(a, b) for a, b in overlap.values())

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('論文半現在真的有在範圍內的項目（必觸發之正對照）',
          sum(thesis_now.values()) > 0,
          '🚨 論文半在範圍內 %d 項：%s；'
          '⚠️ 若是 0，這一對就沒有重複的風險可談'
          % (sum(thesis_now.values()), dict(thesis_now)))
    probe('期刊半現在是 0 項（必觸發之反向）',
          sum(journal_now.values()) == 0,
          '🚨 期刊半現在 %d 項；⚠️ 若不是 0，第 584 輪的「潛伏」說法就要改'
          % sum(journal_now.values()))
    probe('反事實真的動到了東西（必觸發之正對照）',
          swaps > 0 and sum(journal_fixed.values()) > 0,
          '🚨 換掉 %d 個儀器名稱後，期刊半拿回 %d 項：%s；'
          '⚠️ 若沒變，這個反事實等於沒做'
          % (swaps, sum(journal_fixed.values()), dict(journal_fixed)))
    # 🚨 這一道是答案。
    probe('兩半可回收的項目落在**不同的**結局上',
          not overlap,
          '🚨 落在同一組結局的：%s；'
          '**⚠️ 重疊處共 %d 項會被算兩次**——'
          '而那是同一組受試者（第 584 輪：6 個同群數值逐字相同）'
          % (overlap, double_counted))

    doc = {
        'schemaVersion': 1,
        'documentType': 'd3-d24-interlock',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'putsNumbersOn': ('n584 的那句「重讀期刊那篇不能單獨做」——'
                          '⚠️ 它當時沒有數字。'),
        'pair': {'thesis': THESIS, 'journalArticle': JOURNAL},
        'thesisInScopeNow': dict(thesis_now),
        'journalInScopeNow': dict(journal_now),
        'journalInScopeIfInstrumentsFixed': dict(journal_fixed),
        'instrumentSwapsApplied': swaps,
        'overlappingOutcomes': overlap,
        'itemsAtRiskOfDoubleCount': double_counted,
        'onlyThesis': only_thesis,
        'onlyJournal': only_journal,
        'theInterlock': (
            '🚨 **修 `D24`（把儀器名稱對上契約）而不裁 `D3`（兩筆算一個 study），'
            '會讓同一組受試者的 %d 項結果被算兩次。**'
            '⚠️ 反過來，只裁 D3 而不修 D24，期刊那半仍是 0 項——'
            '**✅ 兩者要一起裁，🚫 順序上不能只做一邊。**'
            % double_counted),
        'whatThisIsNot': (
            '🚫 本支**不主張**那兩半就是同一個試驗——'
            '⚠️ 那是第 584 輪的證據（6 個同群數值逐字相同），'
            '**✅ 而判定是 `D3` 的事。**'
            '🚨 本支只算「若照現有證據合併，數字會怎麼動」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n701 D3 與 D24 的連鎖 ===')
    print('   論文半 %s 現在在範圍內：%s' % (THESIS, dict(thesis_now)))
    print('   期刊半 %s 現在在範圍內：%s' % (JOURNAL, dict(journal_now)))
    print('   期刊半・只換儀器名稱後：%s' % dict(journal_fixed))
    print('   重疊的結局：%s' % (overlap or '無'))
    print('   🚨 會被算兩次的項數：%d' % double_counted)
    print('   只有論文半有的結局：%s｜只有期刊半有的：%s'
          % (only_thesis or '無', only_journal or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
