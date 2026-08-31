# -*- coding: utf-8 -*-
"""**同一份讀法，「不寫」會過，「明寫不知道」會被排除。**（第 591 輪）

## 🚨 前幾輪都在查被排除的東西——⚠️ 而通過的東西比被擋的東西更少被看

✅ 故本輪稽核**在範圍內的那 98 項**：契約各軸有沒有空欄位。

| 軸 | 98 項中為空 |
|---|---|
| **`statisticalModel`** | **🚨 98 項全空** |
| `instrument` | 60 項（⚠️ 全是 GI 兩個結局，其 `allowedInstruments` 是空的） |
| `outcomeRoleAsStated` | 32 項 |

## 🚨 而 `statisticalModel` 那一格，藏著一個實測得出來的不對稱

`matcher.py` 寫的是 `reported.get("statisticalModel", "unadjusted")`。
**⚠️ 而 `.get(鍵, 預設)` 的預設值只在「鍵不存在」時生效**——
🚨 鍵存在而值為 `null` 時，拿到的是 `None`，不是 `"unadjusted"`。

✅ 拿 matcher 實測同一份讀法的兩種寫法：

| 寫法 | 結果 |
|---|---|
| **鍵缺席** | ✅ `inScope=True` |
| **明寫 `null`** | 🚨 `inScope=False`，理由 `notExtracted-model-not-in-scope` |

> **🚨 而 schema 明文允許寫 null**（`"type": ["string", "null"]`）。
> ⚠️ 也就是說：**一個讀的人若誠實地寫下「這篇沒說用什麼模型」，
> 他的結局會被丟掉，而理由碼會說「模型不在範圍內」——那是一句假話。**
> ✅ **省略不寫的人反而過關。**
>
> **⚠️ 本 run 第二次撞到「認真的人被罰」**：第 576 輪是本室的規則罰了
> 把分辨寫清楚的讀者；🚨 這一次是判定本身。

## ⚠️ 現在沒有活的損害，但那是運氣

實測 883 項裡：**鍵缺席 878、明寫 null 0、有值 5**。
✅ 故目前無人受害。**🚨 但那是因為沒有人選擇誠實地寫 null。**

> ⚠️ 另一件要記：**這一軸從未約束過任何東西**——
> 878 項都吃了 `"unadjusted"` 這個**沒有人聲明過的預設**。
> 🚨 契約碰巧三種模型全收，故它不會改變結果；
> **⚠️ 但那份清冊記的是「沒說」，判定記的是「unadjusted」——那是兩句不同的話。**

## 🚨 順帶量出來的一件事：證據池是 GI 症狀主導的

在範圍內 98 項中：**GI 症狀 60 項（61%）**；
⚠️ 表現類（完成時間 6 ＋ 力竭時間 10）只有 **16 項**。

> 🚨 而第 588 輪已查明：契約的 `inScopeEffectMeasures` **不收 median**，
> ⚠️ 而 median 正是 GI 嚴重度分數的自然統計量。
> **📮 契約對這個佔六成的家族，一端最寬鬆（工具清單留空）、一端最嚴（不收 median）。**

## 🚫 本支不入輪次閘門
"""
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n591_absent_vs_null_axis.json'
SHEET = ROOT / 'extraction-worksheet'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

AXES = ('normalisedOutcomeRef', 'instrument', 'timepointDays', 'analysisSet',
        'effectMeasure', 'dose', 'doseUnit', 'statisticalModel',
        'hasNumericResult', 'outcomeRoleAsStated')
AXIS = 'statisticalModel'

# ✅ 一份完全合法、各軸齊備的讀法。🚨 兩個變體只差在這一個鍵怎麼寫。
SPECIMEN = {'normalisedOutcomeRef': 'time-to-exhaustion',
            'instrument': 'cycling-tte-fixed-intensity',
            'timepointDays': 0, 'analysisSet': 'complete-case',
            'effectMeasure': 'mean', 'dose': 60, 'doseUnit': 'g/h',
            'hasNumericResult': True}


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    blanks, refs, scanned = Counter(), Counter(), 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for item in doc.get('reportedOutcomes') or []:
            if not (item.get('scopeDecision') or {}).get('inScope'):
                continue
            scanned += 1
            refs[item.get('normalisedOutcomeRef')] += 1
            for axis in AXES:
                if item.get(axis) is None:
                    blanks[axis] += 1

    # 🚨 讀的人到底怎麼寫這個鍵：缺席、明寫 null、還是有值。
    shape = Counter()
    for path in ([SHEET / 'drafts.json']
                 + sorted((SHEET / 'drafts').glob('page-*.json'))):
        for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
            for item in entry.get('reportedOutcomes') or []:
                if AXIS not in item:
                    shape['key-absent'] += 1
                elif item[AXIS] is None:
                    shape['key-present-null'] += 1
                else:
                    shape['has-value'] += 1

    absent = matcher.decide(dict(SPECIMEN))
    explicit_null = matcher.decide(dict(SPECIMEN, **{AXIS: None}))

    gi = sum(v for k, v in refs.items() if k and k.startswith('gi-symptom'))
    performance = refs.get('tt-completion-time', 0) + refs.get(
        'time-to-exhaustion', 0)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('掃到的是那 98 項（必觸發）', scanned == 98,
          '🚨 對不上就代表本支看的不是同一批；實得 %d 項' % scanned)
    # ✅ 正對照：省略不寫的那一種，確實會過。
    probe('鍵缺席的那種寫法確實會過（正對照，必觸發）',
          absent.in_scope,
          '✅ 實得 inScope=%s；🚨 若它也不過，本支所稱的不對稱就不存在'
          % absent.in_scope)
    # 🚨 必觸發之反向：明寫 null 的那一種，確實會被排除。
    probe('明寫 null 的那種寫法確實被排除（必觸發之反向）',
          not explicit_null.in_scope
          and explicit_null.reason_code == 'notExtracted-model-not-in-scope',
          '🚨 實得 inScope=%s／理由=%s；⚠️ 兩種寫法出自同一份讀法，'
          '只差在這一個鍵怎麼寫'
          % (explicit_null.in_scope, explicit_null.reason_code))
    # 🚨 這一道會紅，而它是本支的主張。
    probe('同一份讀法不會因為寫法不同而得到相反結果',
          absent.in_scope == explicit_null.in_scope,
          '🚨 缺席 → inScope=%s；明寫 null → inScope=%s（%s）。'
          '⚠️ 而 schema 明文允許寫 null，'
          '🚫 故誠實寫下「這篇沒說模型」的人，結局會被丟掉，'
          '而理由碼會說「模型不在範圍內」——那是一句假話'
          % (absent.in_scope, explicit_null.in_scope,
             explicit_null.reason_code))

    doc = {
        'schemaVersion': 1,
        'documentType': 'absent-vs-null-axis-audit',
        'question': '在範圍內那 98 項的契約各軸，有沒有空欄位；空的那一格意味著什麼',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inScopeScanned': scanned,
        'blankAxes': dict(blanks),
        'howReadersWroteTheAxis': dict(shape),
        'asymmetry': {
            'axis': AXIS,
            'matcherLine': 'reported.get("statisticalModel", "unadjusted")',
            'keyAbsent': {'inScope': absent.in_scope,
                          'reasonCode': absent.reason_code},
            'keyPresentNull': {'inScope': explicit_null.in_scope,
                               'reasonCode': explicit_null.reason_code},
            'schemaAllowsNull': True,
            'why': ('⚠️ `.get(鍵, 預設)` 的預設值只在鍵不存在時生效；'
                    '🚨 鍵存在而值為 null 時拿到的是 None。'),
        },
        'noLiveHarmButThatIsLuck': (
            '✅ 實測 883 項裡鍵缺席 878、明寫 null 0，故目前無人受害。'
            '🚨 但那是因為沒有人選擇誠實地寫 null。'),
        'axisNeverConstrainedAnything': (
            '⚠️ 878 項都吃了 "unadjusted" 這個沒有人聲明過的預設。'
            '🚨 契約碰巧三種模型全收，故它不改變結果；'
            '⚠️ 但清冊記的是「沒說」、判定記的是「unadjusted」——那是兩句不同的話。'),
        'poolComposition': {
            'byOutcome': dict(refs),
            'giSymptoms': gi, 'performance': performance,
            'note': ('🚨 在範圍內 98 項中 GI 症狀佔 %d 項（%d%%），'
                     '⚠️ 表現類只有 %d 項。'
                     '📮 而第 588 輪已查明契約不收 median——'
                     'median 正是 GI 嚴重度的自然統計量。'
                     % (gi, round(100 * gi / scanned), performance)),
        },
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n591 缺席 vs 明寫 null ===')
    print('   在範圍內 %d 項｜空欄位：%s' % (scanned, dict(blanks)))
    print('   讀的人怎麼寫 %s：%s' % (AXIS, dict(shape)))
    print('   🚨 鍵缺席 → inScope=%s｜明寫 null → inScope=%s（%s）'
          % (absent.in_scope, explicit_null.in_scope,
             explicit_null.reason_code))
    print('   證據池：GI %d 項／表現類 %d 項（共 %d）' % (gi, performance, scanned))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
