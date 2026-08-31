# -*- coding: utf-8 -*-
"""**兩條路徑對同一份契約，給出相反的「有沒有升級」。**（第 593 輪）

## ✅ 先補完第 592 輪自己說的涵蓋缺口

第 592 輪實測了 6 個鍵中的 3 個，並據實記下另外三個未驗證。**✅ 本輪補完。**

| 鍵 | 明寫 `null`／缺席的後果 | 性質 |
|---|---|---|
| `hasNumericResult`（缺席） | ✅ `inScope=True` | **放寬**——⚠️ 漏填會被收進來 |
| `maxStudyResultsPerStudy=null` | 🚨 **TypeError 當場炸開** | ✅ **吵**——這是三者中最好的一種 |
| `onExceedMax=null` | 🚨 見下 | **🚨 最糟** |

> **⚠️ 同一個寫法，三種後果：崩潰、放寬、以及一份自相矛盾的文件。**

## 🚨 `onExceedMax=null`：`decide_inventory` 產出一份自我矛盾的文件

以 13 項（超過上限 12）實測：

| 契約 | `escalated` | `inScopeCount` | 逐項 `inScope=True` |
|---|---|---|---|
| 原樣（`"escalate"`） | True | 0 | **0 項** ✅ 一致 |
| **`onExceedMax=null`** | **True** | **0** | **🚨 13 項** |

> **🚨 摘要說「一項都不在範圍內、已升級」，而逐項全部說「我在範圍內」。**
> ⚠️ 下游若讀 `decisions`，會抽出 13 項；讀 `inScopeCount`，會抽出 0 項。
> **🚫 兩個讀法都不算誤讀——那份文件本身就是兩句話。**

## 🚨 而 `scope_inventory` 走的是另一條路，答案相反

同一份契約、同樣 13 項：

| 方法 | `escalated` | `inScopeCount` |
|---|---|---|
| `decide_inventory` | **True** | 0 |
| `scope_inventory` | **False** | 13 |

⚠️ 成因在兩行程式的**括號位置不同**：
- `decide_inventory`：`exceeded = in_scope > cap`，`onExceedMax` 只影響**要不要標記**；
- `scope_inventory`：`exceeded = (in_scope > cap and onExceedMax == "escalate")`。

> **🚨 故「有沒有超過上限」這件事，在兩條路徑上不是同一個問題。**
> ⚠️ 契約原樣時兩者一致，🚫 而那是因為 `onExceedMax` 剛好等於 `"escalate"`。

## 🚫 本支不入輪次閘門；⚠️ 現行契約值為 `"escalate"`，故無活的損害
"""
import copy
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

OUT = Path(__file__).resolve().parent / 'n593_cap_paths_diverge.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')
SHEET = ROOT / 'extraction-worksheet'

ITEM = {'localLabel': 'x', 'sourceLocation': {'section': 'Results'},
        'normalisedOutcomeRef': 'time-to-exhaustion',
        'instrument': 'cycling-tte-fixed-intensity',
        'timepointDays': 0, 'analysisSet': 'complete-case',
        'effectMeasure': 'mean', 'dose': 60, 'doseUnit': 'g/h',
        'hasNumericResult': True}
OVER_CAP = 13          # 契約上限為 12


def contract_with(**overrides):
    doc = json.loads(CONTRACT.read_text(encoding='utf-8'))
    doc['extractionPolicy'].update(overrides)
    return doc


def run_decide(contract):
    inventory = {'inventoryId': 'probe',
                 'reportedOutcomes': [dict(ITEM) for _ in range(OVER_CAP)]}
    try:
        result = ScopeMatcher(contract).decide_inventory(inventory)
    except Exception as exc:                     # noqa: BLE001
        return {'raised': '%s: %s' % (type(exc).__name__, exc)}
    return {'escalated': result['escalated'],
            'inScopeCount': result['inScopeCount'],
            'itemsSayingInScope': sum(1 for d in result['decisions']
                                      if d['inScope'])}


def run_scope(contract):
    """✅ 以真實 draft 為底，🚨 只換掉 reportedOutcomes——
    ⚠️ 綁定與雜湊必須是真的，否則 assert_scopable 會擋下來而測不到這件事。"""
    draft = json.loads((SHEET / 'drafts' / 'page-009.json')
                       .read_text(encoding='utf-8'))['entries'][0]
    draft = copy.deepcopy(draft)
    draft['reportedOutcomes'] = [dict(ITEM) for _ in range(OVER_CAP)]
    try:
        scoped = ScopeMatcher(contract).scope_inventory(draft)
    except Exception as exc:                     # noqa: BLE001
        return {'raised': '%s: %s' % (type(exc).__name__, exc)}
    summary = scoped.get('scopeDecisionSummary') or {}
    return {'escalated': summary.get('escalated'),
            'inScopeCount': summary.get('inScopeCount'),
            'itemsSayingInScope': sum(
                1 for o in scoped['reportedOutcomes']
                if (o.get('scopeDecision') or {}).get('inScope'))}


def main():
    plain = json.loads(CONTRACT.read_text(encoding='utf-8'))
    null_exceed = contract_with(onExceedMax=None)
    null_cap = contract_with(maxStudyResultsPerStudy=None)

    rows = {
        'as-written|decide_inventory': run_decide(plain),
        'as-written|scope_inventory': run_scope(plain),
        'onExceedMax=null|decide_inventory': run_decide(null_exceed),
        'onExceedMax=null|scope_inventory': run_scope(null_exceed),
        'maxStudyResultsPerStudy=null|decide_inventory': run_decide(null_cap),
    }
    matcher = ScopeMatcher(plain)
    without_flag = {k: v for k, v in ITEM.items() if k != 'hasNumericResult'}
    absent_numeric = matcher.decide(without_flag)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    a = rows['as-written|decide_inventory']
    b = rows['as-written|scope_inventory']
    probe('契約原樣時兩條路徑一致且都升級（正對照，必觸發）',
          a.get('escalated') is True and b.get('escalated') is True
          and a.get('itemsSayingInScope') == 0
          and b.get('itemsSayingInScope') == 0,
          '✅ 實得 %s／%s；🚨 若原樣就不一致，後面的比較無從說起' % (a, b))
    probe('上限為 null 時當場炸開（必觸發之反向）',
          'raised' in rows['maxStudyResultsPerStudy=null|decide_inventory'],
          '✅ 實得 %s；⚠️ 這是三種後果裡**最好**的一種——'
          '🚨 吵的失敗看得見，安靜的看不見'
          % rows['maxStudyResultsPerStudy=null|decide_inventory'].get('raised'))
    probe('hasNumericResult 缺席時是放寬方向（必觸發之反向）',
          absent_numeric.in_scope,
          '🚨 實得 inScope=True；⚠️ 而那一格正是把關 no-numeric-result 的地方，'
          '🚫 漏填的後果是被收進來')
    c = rows['onExceedMax=null|decide_inventory']
    d = rows['onExceedMax=null|scope_inventory']
    # 🚨 這兩道會紅。
    probe('decide_inventory 的輸出不會自相矛盾',
          not (c.get('escalated') and c.get('itemsSayingInScope')),
          '🚨 實得 escalated=%s、inScopeCount=%s，而逐項有 %s 項說自己在範圍內；'
          '⚠️ 下游讀 decisions 會抽出 %s 項，讀 inScopeCount 會抽出 %s 項'
          % (c.get('escalated'), c.get('inScopeCount'),
             c.get('itemsSayingInScope'), c.get('itemsSayingInScope'),
             c.get('inScopeCount')))
    probe('兩條路徑對「有沒有升級」給相同答案',
          c.get('escalated') == d.get('escalated'),
          '🚨 decide_inventory=%s、scope_inventory=%s；'
          '⚠️ 成因是兩行程式的括號位置不同——'
          '🚫 「有沒有超過上限」在兩條路徑上不是同一個問題'
          % (c.get('escalated'), d.get('escalated')))

    doc = {
        'schemaVersion': 1,
        'documentType': 'cap-paths-divergence',
        'question': '第 592 輪未實測的三個鍵，以及上限在兩條路徑上是否一致',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'capInContract': (plain['extractionPolicy']
                          .get('maxStudyResultsPerStudy')),
        'onExceedMaxInContract': plain['extractionPolicy'].get('onExceedMax'),
        'itemsUsed': OVER_CAP,
        'results': rows,
        'hasNumericResultAbsent': {'inScope': absent_numeric.in_scope,
                                   'reasonCode': absent_numeric.reason_code},
        'threeOutcomesOfOneConstruct': (
            '⚠️ 同一個 `.get(鍵, 預設)` 寫法，三種後果：'
            '🚨 `maxStudyResultsPerStudy=null` 當場炸開（✅ 最好）、'
            '`hasNumericResult` 缺席就放寬、'
            '🚨 `onExceedMax=null` 產出一份自相矛盾的文件（最糟）。'),
        'divergence': (
            '🚨 `decide_inventory` 算的是 `exceeded = in_scope > cap`，'
            '`onExceedMax` 只影響要不要標記；'
            '而 `scope_inventory` 算的是 '
            '`exceeded = (in_scope > cap and onExceedMax == "escalate")`。'
            '⚠️ 括號位置不同，故「有沒有超過上限」在兩條路徑上不是同一個問題。'),
        'noLiveHarm': ('✅ 現行契約 onExceedMax="escalate"，兩條路徑一致；'
                       '🚨 而那是契約值剛好對，🚫 不是程式一致。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n593 上限在兩條路徑上的分歧 ===')
    for name, row in rows.items():
        print('   %-46s %s' % (name, row))
    print('   hasNumericResult 缺席 → inScope=%s' % absent_numeric.in_scope)
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
