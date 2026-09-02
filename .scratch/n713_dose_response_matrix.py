# -*- coding: utf-8 -*-
"""**跨篇的劑量-反應設計矩陣：每個結局在每個劑量帶上有幾篇。**（第 713 輪）

## ✅ 補上第 710 輪的另一半

第 710／711 輪算的是**同一篇之內**的劑量對比。
⚠️ 但劑量-反應也可以靠**跨篇**——🚨 而那需要「不同的劑量帶上各有研究」。

> **🚨 一條曲線至少要三個點。**
> ⚠️ 若某個結局只在一個帶上有研究，**🚫 跨篇也畫不出劑量-反應**。

## ✅ 契約的四個帶（逐字取自契約，🚫 非手打）

`low` 10–29.9｜`moderate` 30–59.9｜`high` 60–89.9｜`very-high` 90–150（g/h）

## ⚠️ 單位是**篇**，🚫 不是項

🚨 同一篇在同一帶上有兩項，那還是一篇——**⚠️ 項數會高估證據量。**
✅ 而已知的同群重複對（`D3`）本支另外標記。

## 🚫 本支不看數值（第 659 輪已證沒有效應量）、不改任何清冊、不送外部請求
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

OUT = Path(__file__).resolve().parent / 'n713_dose_response_matrix.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')
DUPLICATE_PAIR = ('307c0dd5b141caed', '7a6ac1559c740fd6')
MIN_POINTS = 3


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)
    bands = contract['researchQuestion']['interventionOrExposure']['doseBands']
    band_ids = [b['bandId'] for b in bands]

    def band_of(dose):
        for band in bands:
            if band['min'] <= dose <= band['max']:
                return band['bandId']
        return None

    matrix = collections.defaultdict(lambda: collections.defaultdict(set))
    items = collections.Counter()
    unbanded = 0
    total = 0
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
            total += 1
            dose = reported.get('dose')
            band = band_of(float(dose)) if dose is not None else None
            if band is None:
                unbanded += 1
                continue
            ref = reported['normalisedOutcomeRef']
            matrix[ref][band].add(report)
            items[(ref, band)] += 1

    rows = []
    for ref in sorted(matrix):
        filled = [b for b in band_ids if matrix[ref][b]]
        rows.append({
            'outcome': ref,
            'papersByBand': {b: len(matrix[ref][b]) for b in band_ids},
            'itemsByBand': {b: items[(ref, b)] for b in band_ids},
            'bandsWithAnyPaper': len(filled),
            'bandsFilled': filled,
            'enoughForACurve': len(filled) >= MIN_POINTS,
            'duplicatePairBothPresent': sorted(
                b for b in band_ids
                if set(DUPLICATE_PAIR) <= matrix[ref][b]),
        })

    too_few = [r['outcome'] for r in rows if not r['enoughForACurve']]
    single_paper_cells = sum(
        1 for r in rows for b in band_ids if r['papersByBand'][b] == 1)
    filled_cells = sum(
        1 for r in rows for b in band_ids if r['papersByBand'][b] > 0)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('數到的正是那 98 項（必觸發之正對照）',
          total == 98,
          '🚨 在範圍內 %d 項、落不進任何帶的 %d 項；'
          '⚠️ 對不上就與前幾輪不一致' % (total, unbanded))
    probe('帶的定義取自契約（必觸發之正對照）',
          band_ids == ['low', 'moderate', 'high', 'very-high'],
          '🚨 契約的帶：%s；⚠️ 對不上代表本支讀錯了契約' % band_ids)
    probe('捏造的帶沒有任何論文（必觸發之反向）',
          band_of(9999.0) is None,
          '🚨 9999 g/h 落不進任何帶；⚠️ 若落得進，代表分帶邏輯壞了')
    # 🚨 這一道是答案。
    probe('每個結局至少在 %d 個劑量帶上有論文（畫得出曲線）' % MIN_POINTS,
          not too_few,
          '🚨 不足 %d 個帶的結局 %d 個：%s；'
          '⚠️ 只在一兩個帶上有研究的結局，**跨篇也畫不出劑量-反應**'
          % (MIN_POINTS, len(too_few),
             [(r['outcome'], r['bandsFilled']) for r in rows
              if not r['enoughForACurve']]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'dose-response-matrix',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'complements': 'n710／n711（同一篇之內的對比）',
        'bands': bands,
        'unit': '篇（🚫 不是項——同一篇在同一帶上的多項只算一篇）',
        'inScopeItems': total,
        'itemsOutsideAnyBand': unbanded,
        'rows': rows,
        'outcomesWithTooFewBands': too_few,
        'cells': {'filled': filled_cells,
                  'filledBySinglePaperOnly': single_paper_cells,
                  'total': len(rows) * len(band_ids)},
        'whyPapersNotItems': (
            '🚨 同一篇在同一帶上有兩項，那還是一篇——'
            '**⚠️ 用項數會高估證據量。**'),
        'whatThisCannotAnswer': (
            '🚫 本支**不看數值**（第 659 輪已證那 98 項沒有效應量）——'
            '⚠️ 故它回答的是「**設計上**有沒有足夠的劑量點」，'
            '**🚫 不是「算得出劑量-反應」**（那要等 `D25`）。'
            '🚨 又：只有一篇的格子，跨篇比較等於沒有變異可用。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n713 跨篇的劑量-反應設計矩陣（單位：篇）===')
    print('   在範圍內 %d 項｜落不進任何帶 %d 項' % (total, unbanded))
    print('   %-32s %8s %10s %8s %11s  帶數'
          % ('結局', 'low', 'moderate', 'high', 'very-high'))
    for row in rows:
        p = row['papersByBand']
        print('   %-32s %8d %10d %8d %11d   %d%s'
              % (row['outcome'], p['low'], p['moderate'], p['high'],
                 p['very-high'], row['bandsWithAnyPaper'],
                 '' if row['enoughForACurve'] else '  🚨'))
    print('   有論文的格子 %d／%d，其中只有一篇的 %d 格'
          % (filled_cells, len(rows) * len(band_ids), single_paper_cells))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
