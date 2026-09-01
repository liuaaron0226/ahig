# -*- coding: utf-8 -*-
"""**那 16 項空白，是「這篇填不出來」還是「這一項漏填」。**（第 666 輪）

## 🚨 第 665 輪報了「16 項純因欄位沒填被擋，是最大的一族」

⚠️ 但那句話要站得住，得先分清楚兩種空白：

| | 意思 | 能不能回收 |
|---|---|---|
| **這一項漏填** | 同一篇的別項填得出來 | ✅ 很可能可以 |
| **整篇該欄全空** | 這一篇從頭到尾都沒有這一欄 | 🚨 可能是論文真的沒報，也可能是整篇漏填 |

> **✅ 這一題用結構就查得到，🚫 不必碰全文。**

## ✅ 本支怎麼分

對每一個「已對上契約結局、卻因該欄空白被擋」的項目，看同一篇裡：

1. **同一個契約結局**的別項，這一欄填了嗎
2. 退一步，**整篇任何一項**，這一欄填了嗎

## ✅ 順帶給出母體的空白率

🚨 只看被擋的 16 項會看不出比例尺——⚠️ 若整份語料的劑量欄本來就有一半是空的，
那 16 項就不是「漏填」而是**整套流程沒在填**。
✅ 故一併算出全部 790 項的各欄空白率，並分成「有對上契約結局」與「沒對上」兩群。

## 🚫 本支不輸出任何標籤文字、不改任何清冊、不送外部請求
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

OUT = Path(__file__).resolve().parent / 'n666_blank_field_provenance.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

# 被擋的空白只出現在這兩欄（第 665 輪：12 項劑量、4 項效應量測）
WATCHED = {
    'notExtracted-dose-outside-bands': 'dose',
    'notExtracted-effect-measure-not-in-scope': 'effectMeasure',
}
SURVEY_FIELDS = ['dose', 'doseUnit', 'instrument', 'effectMeasure',
                 'analysisSet', 'timepointDays', 'hasNumericResult']


def inventories():
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        yield json.loads(path.read_text(encoding='utf-8'))


def classify(paper_items, ref, field):
    """同結局有人填得出來？整篇有人填得出來？"""
    same_outcome = [i for i in paper_items
                    if i.get('normalisedOutcomeRef') == ref]
    if any(i.get(field) is not None for i in same_outcome):
        return '同結局內別項填得出來'
    if any(i.get(field) is not None for i in paper_items):
        return '同篇別的結局填得出來'
    return '整篇該欄全空'


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    blanks, verdicts = [], collections.Counter()
    survey = {'mapped': collections.Counter(), 'unmapped': collections.Counter()}
    totals = collections.Counter()
    filled_anywhere = collections.Counter()

    for inventory in inventories():
        items = inventory['reportedOutcomes']
        decisions = matcher.decide_inventory(inventory)['decisions']
        for field in SURVEY_FIELDS:
            if any(i.get(field) is not None for i in items):
                filled_anywhere[field] += 1

        for reported, decision in zip(items, decisions):
            group = 'mapped' if reported.get('normalisedOutcomeRef') \
                else 'unmapped'
            totals[group] += 1
            for field in SURVEY_FIELDS:
                if reported.get(field) is None:
                    survey[group][field] += 1

            if decision['inScope']:
                continue
            field = WATCHED.get(decision['reasonCode'])
            ref = reported.get('normalisedOutcomeRef')
            if not field or not ref or reported.get(field) is not None:
                continue
            verdict = classify(items, ref, field)
            verdicts[verdict] += 1
            blanks.append({'report': inventory['report'][-16:], 'ref': ref,
                           'field': field, 'verdict': verdict})

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的抓到第 665 輪那 16 項空白（必觸發之正對照）',
          len(blanks) == 16,
          '🚨 抓到 %d 項（劑量 %d／效應量測 %d）；⚠️ 不是 16 就與上一輪對不上'
          % (len(blanks),
             sum(1 for b in blanks if b['field'] == 'dose'),
             sum(1 for b in blanks if b['field'] == 'effectMeasure')))

    # ✅ 必觸發之反向：偽造一個空白，塞進一篇明明填得出劑量的清冊裡，
    #    分類必須說「填得出來」——🚨 否則本支的分類根本沒在看同篇。
    donor_items, donor_ref = None, None
    for inventory in inventories():
        for reported in inventory['reportedOutcomes']:
            if reported.get('dose') is not None \
                    and reported.get('normalisedOutcomeRef'):
                donor_items = inventory['reportedOutcomes']
                donor_ref = reported['normalisedOutcomeRef']
                break
        if donor_items:
            break
    forged = classify(donor_items or [], donor_ref, 'dose')
    probe('把空白放進一篇填得出劑量的清冊，必須判為「填得出來」（必觸發之反向）',
          forged == '同結局內別項填得出來',
          '🚨 偽造樣本判為「%s」；⚠️ 若判成「整篇該欄全空」，'
          '代表分類沒有真的在看同一篇' % forged)

    probe('母體的空白率算得出來（必觸發之正對照）',
          totals['mapped'] > 0 and totals['unmapped'] > 0,
          '🚨 有對上契約結局 %d 項／沒對上 %d 項；⚠️ 任一為 0，比例尺就沒有意義'
          % (totals['mapped'], totals['unmapped']))

    # 🚨 這一道是答案。
    recoverable = verdicts.get('同結局內別項填得出來', 0) \
        + verdicts.get('同篇別的結局填得出來', 0)
    probe('那些空白都是「整篇該欄全空」，🚫 沒有一項是同篇漏填',
          recoverable == 0,
          '🚨 同篇填得出來的有 %d 項（%s）；'
          '⚠️ 這些**最像漏填**，也最可能回收得到'
          % (recoverable, dict(verdicts.most_common())))

    rates = {}
    for group in ('mapped', 'unmapped'):
        rates[group] = {
            field: '%d/%d' % (survey[group][field], totals[group])
            for field in SURVEY_FIELDS}

    doc = {
        'schemaVersion': 1,
        'documentType': 'blank-field-provenance',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'blankBlockedItems': len(blanks),
        'verdicts': dict(verdicts.most_common()),
        'rows': blanks,
        'blankRateByGroup': rates,
        'papersWithFieldFilledSomewhere': dict(filled_anywhere.most_common()),
        'totals': dict(totals),
        'whyThisMatters': (
            '⚠️ 第 665 輪說「16 項純因欄位沒填被擋」，'
            '🚨 但那句話沒分清楚「這一項漏填」與「整篇該欄全空」——'
            '✅ 只有前者是**回全文補一格就好**的東西。'),
        'methodLimit': (
            '🚨 本支只用**結構**分辨，🚫 分不出「整篇該欄全空」是'
            '「論文真的沒報」還是「整篇漏填」——⚠️ 那要看全文（n+187 的視窗）。'
            '✅ 而「同篇填得出來」是**比較強**的漏填訊號，'
            '🚫 仍不是證明：同一篇的不同結局本來就可能報法不同。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n666 空白欄位的來歷 ===')
    print('   被空白擋掉 %d 項｜分類：%s'
          % (len(blanks), dict(verdicts.most_common())))
    for row in blanks:
        print('      %s｜%-30s %-14s → %s'
              % (row['report'], row['ref'], row['field'], row['verdict']))
    print('   母體空白率（空白數／該群總項數）：')
    for group in ('mapped', 'unmapped'):
        label = '有對上契約結局' if group == 'mapped' else '沒對上契約結局'
        print('      %s（%d 項）' % (label, totals[group]))
        for field in SURVEY_FIELDS:
            print('         %-18s %s' % (field, rates[group][field]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
