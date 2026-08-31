# -*- coding: utf-8 -*-
"""**兩個理由碼各自把好幾件不同的事記成同一件。**（第 588 輪）

## 🚨 本室問了三次「劑量理由碼要不要拆成兩碼」——⚠️ 而它其實是**三**件事

✅ 數過之後：`notExtracted-dose-outside-bands` 共 19 項，分成三種：

| 實情 | 項數 | 該做的事 |
|---|---|---|
| **🚨 論文根本沒報劑量**（`dose=None`） | **12 項／6 篇** | ⚠️ 資料缺漏，🚫 不是「劑量不合格」 |
| 真的超出帶外（180 g/h） | 3 項 | ✅ 正當排除 |
| **🚨 對照組（0 g/h）** | **4 項** | ⚠️ **那是比較組，不是一個超出範圍的暴露** |

> **🚨 第三種是分類上的錯**：劑量帶描述的是**介入**，
> ⚠️ 而安慰劑組**依定義沒有劑量**。
> 🚫 把對照組記成「劑量不在帶內」，等於說「這組因為劑量不合格而被排除」——
> **⚠️ 而它本來就不該有劑量。**

## 🚨 而同一個毛病，在第二個理由碼上原封不動

`notExtracted-effect-measure-not-in-scope` 共 7 項：

| 實情 | 項數 |
|---|---|
| **有填，但契約不收：`median`** | 3 項／1 篇 |
| **🚨 根本沒填（`None`）** | **4 項／2 篇** |

⚠️ 「讀的人沒填」與「論文用了契約不收的統計量」是兩件事，
**🚫 而它們現在共用一個理由碼。**

## 🚨 而那個 `median` 指向一個契約層的缺口

契約的 `inScopeEffectMeasures` 是 `MD／SMD／RR／RD／mean／proportion`——**沒有 median**。
⚠️ 而腸胃道症狀分數是**次序尺度**，🚨 **median（配 IQR）本來就是它的自然統計量。**

> **📮 故這不是那篇論文報錯了，是契約收不下那個結局家族實際被報告的方式。**

## 🚫 本支不入輪次閘門
"""
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n588_reason_code_conflation.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

DOSE = 'notExtracted-dose-outside-bands'
EFFECT = 'notExtracted-effect-measure-not-in-scope'


def classify_dose(item):
    dose = item.get('dose')
    if dose is None:
        return 'not-reported'
    if dose == 0:
        return 'control-arm'
    return 'genuinely-out-of-band'


def classify_effect(item):
    measure = item.get('effectMeasure')
    return 'not-filled-in' if measure is None else 'reported-but-not-in-contract'


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    allowed_measures = contract.get('inScopeEffectMeasures') or []

    buckets = {DOSE: defaultdict(lambda: {'items': 0, 'reports': set(),
                                          'values': Counter()}),
               EFFECT: defaultdict(lambda: {'items': 0, 'reports': set(),
                                            'values': Counter()})}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        for item in doc.get('reportedOutcomes') or []:
            reason = (item.get('scopeDecision') or {}).get('reasonCode')
            if reason == DOSE:
                key, value = classify_dose(item), item.get('dose')
            elif reason == EFFECT:
                key, value = classify_effect(item), item.get('effectMeasure')
            else:
                continue
            bucket = buckets[reason][key]
            bucket['items'] += 1
            bucket['reports'].add(report)
            if value is not None:
                bucket['values'][str(value)] += 1

    summary = {}
    for reason, kinds in buckets.items():
        summary[reason] = {
            'totalItems': sum(v['items'] for v in kinds.values()),
            'situations': {k: {'items': v['items'],
                               'reports': len(v['reports']),
                               'values': dict(v['values'])}
                           for k, v in sorted(kinds.items())},
        }

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩個理由碼都真的有東西可分（必觸發）',
          all(s['totalItems'] > 0 for s in summary.values()),
          '🚨 若其中一個為零，本支對它的說法就沒有根據；實得 %s'
          % {r: s['totalItems'] for r, s in summary.items()})
    # 🚨 必觸發之反向：分類器要真的分得出**每一種**，
    # ⚠️ 否則某一種只是寫在文件裡而從未發生。
    missing = ([k for k in ('not-reported', 'control-arm',
                            'genuinely-out-of-band')
                if k not in summary[DOSE]['situations']]
               + [k for k in ('not-filled-in', 'reported-but-not-in-contract')
                  if k not in summary[EFFECT]['situations']])
    probe('五種情形全部真的出現在資料裡（必觸發之反向）', not missing,
          '⚠️ 沒出現的那一種代表本支對它的描述從未被驗證；實得缺 %s'
          % (missing or '無'))
    probe('median 確實不在契約的效應量清單裡',
          'median' not in allowed_measures,
          '⚠️ 契約收的是 %s；🚨 而腸胃道症狀分數是次序尺度，'
          'median 本來就是它的自然統計量' % allowed_measures)
    # 🚨 這兩道會紅，而它們問的是確定的事：一個理由碼應該只對應一種實情。
    for reason in (DOSE, EFFECT):
        kinds = summary[reason]['situations']
        probe('%s 只對應一種實情' % reason, len(kinds) == 1,
              '🚨 實得 %d 種：%s；⚠️ 共用一個理由碼，'
              '會讓「資料缺漏」與「正當排除」在報表上長得一樣'
              % (len(kinds), {k: v['items'] for k, v in kinds.items()}))

    doc = {
        'schemaVersion': 1,
        'documentType': 'reason-code-conflation-census',
        'question': '兩個理由碼各自把幾件不同的事記成同一件',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'contractEffectMeasures': allowed_measures,
        'summary': summary,
        'headline': (
            '🚨 劑量那一碼是**三**件事，不是本室先前說的兩件：'
            '沒報（12 項／6 篇）、真的帶外 180 g/h（3 項）、'
            '**對照組 0 g/h（4 項）**。'
            '⚠️ 第三種是分類上的錯——劑量帶描述介入，而安慰劑組依定義沒有劑量。'),
        'secondFinding': (
            '🚨 同一個毛病在 notExtracted-effect-measure-not-in-scope 上原封不動：'
            '「讀的人沒填」4 項與「論文用了 median」3 項共用一個碼。'),
        'contractGap': (
            '📮 median 不在 inScopeEffectMeasures 裡，'
            '⚠️ 而腸胃道症狀分數是次序尺度，median 配 IQR 本來就是自然寫法。'
            '🚨 故那不是論文報錯，是契約收不下那個結局家族實際被報告的方式。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n588 理由碼把幾件事記成同一件 ===')
    for reason, item in summary.items():
        print('   %s（共 %d 項）' % (reason, item['totalItems']))
        for kind, stat in item['situations'].items():
            print('      %-28s %2d 項／%d 篇 %s'
                  % (kind, stat['items'], stat['reports'],
                     stat['values'] or ''))
    print('   契約效應量：%s' % allowed_measures)
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
