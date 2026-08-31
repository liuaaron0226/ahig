# -*- coding: utf-8 -*-
"""**`.get(鍵, 預設)` 這一整類，不只是上一輪那一個實例。**（第 592 輪）

## 🚨 第 433 輪的規矩：**只修實例不修這一類，等於沒修**

第 591 輪證明了 `statisticalModel` 上的不對稱。**✅ 本輪把整類找出來。**

⚠️ `dict.get(鍵, 預設)` 的預設值**只在鍵不存在時生效**；
🚨 鍵存在而值為 `null` 時，拿到的是 `None`，而後續比較會落到哪裡**每一處都不一樣**。

## ✅ 實測三處，方向**不一致**——而那正是最危險的地方

| 位置 | 明寫 `null` 的後果 | 方向 |
|---|---|---|
| `reported.statisticalModel` | 🚨 結局被排除（`model-not-in-scope`） | **收緊** |
| `policy.subgroupPolicy` | 🚨 次群組被排除 | **收緊** |
| **`policy.sensitivityAnalysisPolicy`** | **🚨 敏感度分析變成「在範圍內」** | **🚨 放寬** |

> **🚨 第三列是一條排除規則整個消失。**
> ⚠️ 契約寫的是 `"exclude"`；把它改成 `null`，那條規則**不是報錯，是靜靜地不存在**。
> **🚫 而預設值 `"exclude"` 一次都沒有生效過的機會。**
>
> **⚠️ 同一個寫法，在三個地方給出兩種相反的方向。**
> 🚨 那不是「有一個 bug」，是**沒有人決定過 null 該代表什麼**。

## ⚠️ 目前的曝險：**一個都沒有觸發，而那是資料的運氣**

| 欄位 | 實測 |
|---|---|
| `statisticalModel` | 883 項中鍵缺席 878、明寫 null **0** |
| `hasNumericResult` | 883 項**全部有值**（🚫 預設 `True` 從未生效） |
| `extractionPolicy` 四個鍵 | 契約**全部有值** |

> ✅ 故現在沒有活的損害。
> **🚨 但每一格的安全都來自「碰巧沒有人寫 null」**，🚫 不是來自任何規則。
> ⚠️ 而 schema 對 `statisticalModel` **明文允許 null**——**寫它是合法的。**

## 🚨 `hasNumericResult` 的預設是**放寬**的那一種

`reported.get("hasNumericResult", True)`——⚠️ 鍵缺席就當作**有數值結果**。
🚨 而那一格是把關「`notExtracted-no-numeric-result`」的地方：
**⚠️ 漏填的後果是被收進來，不是被擋下。**

## 🚫 本支不入輪次閘門
"""
import copy
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n592_default_only_when_absent.json'
MATCHER = REPO / 'ahig' / 'ahig' / 'scope' / 'matcher.py'
SCHEMA = REPO / 'ahig' / 'schema' / 'outcome-inventory.schema.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')
SHEET = ROOT / 'extraction-worksheet'

# ⚠️ 只找**帶預設值**的那一種，🚫 不帶預設的沒有這個問題。
CALL = re.compile(r'(reported|self\.policy)\.get\(\s*"([A-Za-z]+)"\s*,\s*'
                  r'([^)]+)\)')

BASE = {'normalisedOutcomeRef': 'time-to-exhaustion',
        'instrument': 'cycling-tte-fixed-intensity',
        'timepointDays': 0, 'analysisSet': 'complete-case',
        'effectMeasure': 'mean', 'dose': 60, 'doseUnit': 'g/h',
        'hasNumericResult': True}


def main():
    source = MATCHER.read_text(encoding='utf-8')
    sites = [{'owner': owner, 'key': key, 'default': default.strip()}
             for owner, key, default in CALL.findall(source)]

    schema = json.loads(SCHEMA.read_text(encoding='utf-8'))
    props = schema['$defs']['reportedOutcome']['properties']
    for site in sites:
        spec = props.get(site['key'], {})
        site['schemaAllowsNull'] = (isinstance(spec.get('type'), list)
                                    and 'null' in spec['type'])

    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))

    def decide(policy_key=None, item_extra=None):
        cc = copy.deepcopy(contract)
        if policy_key:
            cc['extractionPolicy'][policy_key] = None
        return ScopeMatcher(cc).decide(dict(BASE, **(item_extra or {})))

    demos = {
        'reported.statisticalModel=null':
            decide(item_extra={'statisticalModel': None}),
        'policy.sensitivityAnalysisPolicy=null':
            decide('sensitivityAnalysisPolicy', {'isSensitivityAnalysis': True}),
        'policy.subgroupPolicy=null':
            decide('subgroupPolicy', {'isSubgroup': True,
                                      'subgroupPrespecified': True}),
    }
    baseline = decide(item_extra={'isSensitivityAnalysis': True})
    demo_rows = {k: {'inScope': v.in_scope, 'reasonCode': v.reason_code}
                 for k, v in demos.items()}
    loosened = [k for k, v in demos.items() if v.in_scope]
    tightened = [k for k, v in demos.items() if not v.in_scope]

    # ⚠️ 目前的曝險：讀的人與契約有沒有真的寫出 null。
    shape = {'statisticalModel': {'absent': 0, 'null': 0, 'value': 0},
             'hasNumericResult': {'absent': 0, 'null': 0, 'value': 0}}
    for path in ([SHEET / 'drafts.json']
                 + sorted((SHEET / 'drafts').glob('page-*.json'))):
        for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
            for item in entry.get('reportedOutcomes') or []:
                for key, counts in shape.items():
                    if key not in item:
                        counts['absent'] += 1
                    elif item[key] is None:
                        counts['null'] += 1
                    else:
                        counts['value'] += 1
    policy = contract.get('extractionPolicy') or {}
    policy_nulls = [k for k, v in policy.items() if v is None]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的掃到帶預設值的呼叫（必觸發）', len(sites) >= 2,
          '🚨 若掃不到，本支對「這一類」的說法就沒有根據；實得 %d 處：%s'
          % (len(sites), [s['key'] for s in sites]))
    # ✅ 正對照：契約原樣時，敏感度分析確實被排除。
    probe('契約原樣時敏感度分析確實被排除（正對照，必觸發）',
          not baseline.in_scope
          and baseline.reason_code
          == 'notExtracted-sensitivity-analysis-excluded-by-policy',
          '✅ 實得 inScope=%s／%s；🚨 若它本來就不排除，'
          '「改成 null 就放進來」便無從比較'
          % (baseline.in_scope, baseline.reason_code))
    # 🚨 必觸發之反向：改成 null 之後真的放進來了。
    probe('policy 寫成 null 之後，那條排除規則確實消失（必觸發之反向）',
          demos['policy.sensitivityAnalysisPolicy=null'].in_scope,
          '🚨 實得 inScope=True；⚠️ 契約寫的是 "exclude"，'
          '而預設值 "exclude" 一次都沒有生效的機會')
    # 🚨 這一道會紅：同一個寫法方向不一致。
    probe('同一個寫法在所有位置的方向一致',
          not (loosened and tightened),
          '🚨 放寬 %s；收緊 %s。⚠️ 那不是「有一個 bug」，'
          '是**沒有人決定過 null 該代表什麼**' % (loosened, tightened))

    doc = {
        'schemaVersion': 1,
        'documentType': 'default-only-when-absent-audit',
        'question': '`.get(鍵, 預設)` 這一類在判定裡有幾處，明寫 null 會怎樣',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'sites': sites,
        'baselineSensitivityAnalysis': {'inScope': baseline.in_scope,
                                        'reasonCode': baseline.reason_code},
        'demonstrations': demo_rows,
        'loosensWhenNull': loosened,
        'tightensWhenNull': tightened,
        'coverage': {
            'distinctKeys': sorted({s['key'] for s in sites}),
            'demonstratedWithMatcher': ['statisticalModel',
                                        'sensitivityAnalysisPolicy',
                                        'subgroupPolicy'],
            'notDemonstrated': ['hasNumericResult', 'maxStudyResultsPerStudy',
                                'onExceedMax'],
            'why': ('⚠️ 未實測的三處要另外佈置情境（超過 12 筆的研究、'
                    '缺席而非 null 的欄位）。'
                    '🚨 故本支對它們只說「同一個寫法」，🚫 不宣稱已驗證方向。'),
        },
        'currentExposure': {
            'readerFields': shape,
            'policyKeysWrittenAsNull': policy_nulls,
            'note': ('✅ 目前一處都沒有觸發。'
                     '🚨 但每一格的安全都來自「碰巧沒有人寫 null」，'
                     '🚫 不是來自任何規則。'
                     '⚠️ 而 schema 對 statisticalModel 明文允許 null。'),
        },
        'permissiveDefault': (
            '🚨 `reported.get("hasNumericResult", True)`：鍵缺席就當作有數值結果。'
            '⚠️ 而那一格正是把關 notExtracted-no-numeric-result 的地方——'
            '**漏填的後果是被收進來，不是被擋下。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n592 `.get(鍵, 預設)` 這一類 ===')
    print('   帶預設值的呼叫 %d 處：%s'
          % (len(sites), [(s['owner'], s['key'], s['default']) for s in sites]))
    print('   契約原樣：敏感度分析 inScope=%s（%s）'
          % (baseline.in_scope, baseline.reason_code))
    for name, row in demo_rows.items():
        print('   %-40s → inScope=%s reason=%s'
              % (name, row['inScope'], row['reasonCode']))
    print('   目前曝險：%s｜policy 寫成 null 者 %s'
          % (shape, policy_nulls or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
