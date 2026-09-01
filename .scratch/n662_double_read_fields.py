# -*- coding: utf-8 -*-
"""**兩位讀者同意「有這個結局」之後，欄位也一致嗎。**（第 662 輪）

## 🚨 第 641 輪只比到「同一組契約結局」

⚠️ 產品的 `agreement()` 比兩種單位：自由標籤（不可比）與契約結局 `refs`（可比），
✅ 而三篇雙讀在 refs 層級 **3/3 全一致**。

> **🚨 但兩位讀者可以同意「這篇有計時賽完成時間」，
> 而對它的劑量、儀器、分析集各寫各的。**
> **⚠️ 而劑量正是決定它在不在範圍內的那一欄**（第 645 輪：12 項因劑量空白被擋在門外）。

## ✅ 本支比什麼

對兩邊都宣告了的**同一個契約結局**，逐欄位比：
`dose`／`doseUnit`／`instrument`／`effectMeasure`／`analysisSet`／`timepointDays`
／`hasNumericResult`。

## ⚠️ 一個必須先講的限制

🚨 同一篇可能對同一個結局宣告**多項**（不同劑量臂）。
⚠️ 故本支比的是**該結局在該篇的欄位集合**，🚫 不是逐項配對——
**因為兩邊的項目順序沒有可靠的對應關係**（第 641 輪已證標籤零逐字重疊）。

## 🚫 本支不改任何清冊、不送外部請求、不輸出標籤文字
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

OUT = Path(__file__).resolve().parent / 'n662_double_read_fields.json'
WORKSHEET = ROOT / 'extraction-worksheet'

FIELDS = ['dose', 'doseUnit', 'instrument', 'effectMeasure',
          'analysisSet', 'timepointDays', 'hasNumericResult']


def field_sets(inventory):
    """該篇每個契約結局的欄位值集合。"""
    out = collections.defaultdict(lambda: collections.defaultdict(set))
    for outcome in inventory.get('reportedOutcomes') or []:
        ref = outcome.get('normalisedOutcomeRef')
        if not ref:
            continue
        for field in FIELDS:
            out[ref][field].add(repr(outcome.get(field)))
    return out


def main():
    primary = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        primary[doc['report']] = doc

    second = {}
    for path in sorted((WORKSHEET / 'second').glob('page-*.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))
        for entry in doc.get('entries') or []:
            second[entry['report']] = entry

    shared = sorted(set(primary) & set(second))
    rows = []
    disagreements = []
    for report in shared:
        left = field_sets(primary[report])
        right = field_sets(second[report])
        common_refs = sorted(set(left) & set(right))
        for ref in common_refs:
            for field in FIELDS:
                a, b = left[ref][field], right[ref][field]
                if a != b:
                    disagreements.append({
                        'report': report[-16:], 'outcome': ref,
                        'field': field,
                        'primary': sorted(a), 'second': sorted(b),
                    })
        rows.append({'report': report[-16:],
                     'commonRefs': common_refs,
                     'refsOnlyPrimary': sorted(set(left) - set(right)),
                     'refsOnlySecond': sorted(set(right) - set(left))})

    compared_pairs = sum(len(r['commonRefs']) for r in rows) * len(FIELDS)
    by_field = collections.Counter(d['field'] for d in disagreements)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('三篇雙讀都讀得到、且有共同的契約結局（必觸發之正對照）',
          len(shared) == 3 and all(r['commonRefs'] for r in rows),
          '🚨 共同篇 %d 篇；各篇的共同結局：%s；⚠️ 若沒有共同結局，'
          '逐欄位比就無從比起'
          % (len(shared), {r['report']: r['commonRefs'] for r in rows}))
    probe('比對真的走過夠多格（必觸發之正對照）',
          compared_pairs >= 20,
          '🚨 比了 %d 格（共同結局數 × %d 個欄位）；⚠️ 太少就沒有份量'
          % (compared_pairs, len(FIELDS)))
    # 🚨 這一道是答案。
    probe('兩位讀者在欄位層級也一致',
          not disagreements,
          '🚨 不一致 %d 處，分布於：%s'
          % (len(disagreements), dict(by_field.most_common())))

    doc = {
        'schemaVersion': 1,
        'documentType': 'double-read-field-agreement',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'comparedReports': len(shared),
        'fields': FIELDS,
        'cellsCompared': compared_pairs,
        'rows': rows,
        'disagreements': disagreements,
        'byField': dict(by_field.most_common()),
        'whyThisGoesBeyondN641': (
            '⚠️ 第 641 輪比的是「兩位讀者是否指向同一組契約結局」，'
            '✅ 而那是 3/3 全一致。'
            '🚨 本支往下一層：**同意有這個結局之後，欄位也一致嗎**——'
            '而**劑量正是決定它在不在範圍內的那一欄**'
            '（第 645 輪：12 項因劑量空白被擋在門外）。'),
        'methodLimit': (
            '🚨 同一篇可能對同一結局宣告多項（不同劑量臂），'
            '⚠️ 而兩邊的項目順序沒有可靠對應（第 641 輪已證標籤零逐字重疊）。'
            '✅ 故本支比的是**欄位值的集合**，🚫 不是逐項配對——'
            '⚠️ 這會讓「兩邊都有 60 與 90，只是配到不同項」被判為一致。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n662 雙讀的逐欄位一致性 ===')
    for row in rows:
        print('   %s｜共同結局 %s' % (row['report'], row['commonRefs']))
        if row['refsOnlyPrimary'] or row['refsOnlySecond']:
            print('      只有一邊有：第一線 %s／第二線 %s'
                  % (row['refsOnlyPrimary'], row['refsOnlySecond']))
    print('   比了 %d 格｜🚨 不一致 %d 處' % (compared_pairs,
                                              len(disagreements)))
    for d in disagreements[:12]:
        print('      %s｜%s｜%s：第一線 %s／第二線 %s'
              % (d['report'], d['outcome'], d['field'],
                 d['primary'], d['second']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
