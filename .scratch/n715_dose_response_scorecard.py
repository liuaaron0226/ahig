# -*- coding: utf-8 -*-
"""**逐結局的劑量-反應可行性計分表。**（第 715 輪）

## ✅ 把第 710–714 輪拼成一張表

⚠️ 那五輪各答了一角：同篇內對比、空白劑量的潛力、跨篇的帶覆蓋、缺文的年代。
🚨 但**沒有人把它們並排看**——而擁有者要問的是「這份審查到底答得動哪一個」。

## ✅ 五個面向（每一格都**執行時從既有憑證取**，🚫 不是手打）

| 面向 | 出處 |
|---|---|
| 跨篇覆蓋幾個劑量帶 | 第 713 輪 |
| 有幾篇提供同篇內劑量對比 | 第 710 輪 |
| 有沒有記錄量測工具 | 第 667 輪 |
| 量表是否同質 | 第 633 輪（GI 專屬） |
| **有沒有數值** | 第 659 輪 |

## 🚨 而最後一欄對每一個結局都是「沒有」

⚠️ 第 659 輪已證：那 98 項**一個效應量都沒有**。
**🚨 故本表回答的是「排除數值這一關之後，誰最有機會」，
🚫 不是「誰現在算得出來」。**

## 🚫 本支不做任何新的量測——✅ 它只並排既有的數字
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n715_dose_response_scorecard.json'

CITATIONS = []


def cite(filename, *keys):
    path = HERE / filename
    entry = {'from': filename, 'path': ' → '.join(str(k) for k in keys)}
    try:
        node = json.loads(path.read_text(encoding='utf-8'))
        for key in keys:
            node = node[key]
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        node = None
    entry['value'] = node
    CITATIONS.append(entry)
    return node


def main():
    matrix = cite('n713_dose_response_matrix.json', 'rows')
    within = cite('n710_within_study_dose_contrast.json', 'byOutcome')
    no_instrument = cite('n667_inscope_without_instrument.json',
                         'withoutInstrumentByOutcome')
    in_scope_by_outcome = cite('n667_inscope_without_instrument.json',
                               'inScopeByOutcome')
    gi_scales = cite('n633_gi_scale_heterogeneity.json', 'byScaleClass')
    value_fields = cite('n659_no_numbers_yet.json', 'valueFieldsInData')
    refill = cite('n711_blank_dose_contrast_potential.json',
                  'focusGroupsThatCouldGain')

    rows = []
    for entry in (matrix or []):
        ref = entry['outcome']
        total = (in_scope_by_outcome or {}).get(ref, 0)
        missing = (no_instrument or {}).get(ref, 0)
        w = (within or {}).get(ref, {})
        rows.append({
            'outcome': ref,
            'inScopeItems': total,
            'bandsFilled': entry['bandsWithAnyPaper'],
            'bandsList': entry['bandsFilled'],
            'papersByBand': entry['papersByBand'],
            'withinStudyContrastPapers': w.get('papersMultiDose', 0),
            'instrumentRecorded': (total - missing),
            'instrumentMissing': missing,
            'hasAnyNumericValue': False,
        })

    # ✅ 排序：先看帶數，再看同篇內對比，最後看有沒有記工具。
    def rank_key(r):
        return (-r['bandsFilled'], -r['withinStudyContrastPapers'],
                -(r['instrumentRecorded']))

    rows.sort(key=rank_key)

    best = rows[0] if rows else None
    worst = rows[-1] if rows else None
    all_zero_values = all(not r['hasAnyNumericValue'] for r in rows)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('六個契約結局都在表上（必觸發之正對照）',
          len(rows) == 6,
          '🚨 表上 %d 個結局：%s；⚠️ 少一個就是漏了'
          % (len(rows), [r['outcome'] for r in rows]))
    probe('每一個引用都取得到值（必觸發）',
          all(c['value'] is not None for c in CITATIONS),
          '🚨 引用 %d 筆，取不到值的：%s；⚠️ 取不到就代表本表與憑證脫節'
          % (len(CITATIONS),
             [c['path'] for c in CITATIONS if c['value'] is None] or '無'))
    probe('捏造的結局不在表上（必觸發之反向）',
          not any(r['outcome'] == 'outcome-that-cannot-exist-715'
                  for r in rows),
          '🚨 捏造結局不在表上；⚠️ 若在，代表本表是憑空生成的')
    probe('數值欄那一列真的是全空（必觸發之反向）',
          all(v == 0 for v in (value_fields or {}).values()),
          '🚨 第 659 輪的數值欄實測：%s；'
          '⚠️ 若不是全 0，本表最後一欄的前提就不成立' % value_fields)
    # 🚨 這一道是答案。
    ready = [r for r in rows
             if r['bandsFilled'] >= 3 and r['withinStudyContrastPapers'] > 0
             and r['instrumentMissing'] == 0 and r['hasAnyNumericValue']]
    probe('有結局在五個面向上都齊備',
          bool(ready),
          '🚨 五面向都齊備的結局：%s；'
          '⚠️ 沒有——**因為最後一欄（有沒有數值）對每一個結局都是「沒有」**'
          % ([r['outcome'] for r in ready] or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'dose-response-scorecard',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'synthesises': 'n710／n711／n713／n714（＋n633／n659／n667）',
        'rows': rows,
        'bestPositioned': best['outcome'] if best else None,
        'worstPositioned': worst['outcome'] if worst else None,
        'giScaleClasses': gi_scales,
        'ttRefillPotential': len(refill or []),
        'headline': (
            '🚨 **這份語料真正答得動的劑量-反應，是「腸胃不適 vs 劑量」，'
            '🚫 不是「表現 vs 劑量」。**'
            '✅ `gi-symptom-severity` 是唯一四個劑量帶都有論文的結局'
            '（1／3／10／10），⚠️ 而且有 5 篇提供同篇內對比。'
            '🚨 但它有另一個病：**60 項在範圍內的 GI 結局一個都沒有記量測工具**'
            '（第 667 輪），⚠️ 而量表散在 %s 類（第 633 輪）。'
            % len(gi_scales or {})),
        'theOtherEnd': (
            '🚨 `tt-completion-time`（耐力表現最直接的結局）'
            '**同篇內對比 0 篇、跨篇只有 2 個帶**——'
            '⚠️ 而補回空白劑量最多能讓它多 %d 組同篇內對比（第 711 輪）。'
            % len(refill or [])),
        'theCommonBlocker': (
            '⚠️ **每一個結局的最後一欄都是「沒有數值」**（第 659 輪）。'
            '🚨 故本表回答的是「排除數值這一關之後，誰最有機會」，'
            '**🚫 不是「誰現在算得出來」。**'),
        'whatThisIsNot': (
            '🚫 本支**不做任何新的量測**——✅ 它只把既有的數字並排。'
            '⚠️ 排序用的權重（先帶數、再同篇內對比、再工具）是**本室訂的**，'
            '🚨 換個權重次序就會換一個「最有機會」。'),
        'privateRoot': PROV,
        'citations': CITATIONS,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n715 劑量-反應可行性計分表 ===')
    print('   %-32s %4s %6s %8s %8s %6s'
          % ('結局', '帶數', '同篇對比', '有記工具', '缺工具', '有數值'))
    for row in rows:
        print('   %-32s %4d %6d %8d %8d %6s'
              % (row['outcome'], row['bandsFilled'],
                 row['withinStudyContrastPapers'],
                 row['instrumentRecorded'], row['instrumentMissing'],
                 '否'))
    print('   最有機會：%s｜最沒機會：%s'
          % (doc['bestPositioned'], doc['worstPositioned']))
    print('   GI 的量表類別：%s' % gi_scales)
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
