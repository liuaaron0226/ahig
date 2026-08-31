# -*- coding: utf-8 -*-
"""**7 項在範圍內的結局，座標指向方法段而不是結果段。**（第 598 輪）

## 🚨 把第 597 輪那個實例做成類——⚠️ 而第一版做錯了

第 597 輪在一篇論文裡找到 4 項「宣稱有數值，而症狀在文中沒有數字」。
✅ 本輪把同一個問題問向**全部 98 項**：**它們宣稱的來源段落裡，有結果嗎。**

**🚨 第一版用「段落裡有沒有數字」來問，flag 了 11 項。⚠️ 而其中 4 項是本室的偽陽性：**

| 漏掉的寫法 | 例 |
|---|---|
| 整數配括號的標準差 | `12 (1)`、`139 (14)` |
| 中點當小數點 | `11•7`、`0•4` |

> **🚨 更根本的問題**：⚠️「有沒有數字」問錯了。
> **方法段也有數字**——`100mm visual analogue scale` 就是一個。
> **✅ 該問的是「有沒有結果標記」**：p 值、檢定統計量、±、百分比。

## ✅ 改用結果標記之後，剩下的是真的

`65dd82a89b2c5340` 有 **7 項**在範圍內的結局，座標寫的是 `Gastrointestinal
discomfort`——⚠️ 而那一段**整段只是方法描述**：
「參與者被要求以 100 mm 視覺類比量表評 …」，🚫 沒有任何結果。

> **✅ 而那篇確實有 GI 結果**——在 `Interaction effects (time x treatment)` 段
> （腹絞痛高 9.3%、飽脹高 9.9%，附 F／t 統計）。
>
> **🚨 故這不是「結果不存在」，是「座標指錯段」。**
> ⚠️ 與第 597 輪那 4 項**性質不同**：那 4 項是**該症狀在整份文件裡沒有數字**。
> **🚫 兩者不可混為一談，也不可相加。**

## ⚠️ 為什麼指錯段仍然要緊

**🚨 任何人照那個座標去查，會看到一段方法描述，而不是他要驗的數字。**
⚠️ 第 590 輪已驗過「來源段落確實存在」（790／790）——
**✅ 存在，🚫 但不保證它是結果段。**

## 🚫 本支不入輪次閘門
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction import corpus  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n598_source_section_no_result.json'

# 🚨 第一版（做錯的那個）：只問有沒有數字。⚠️ 留著是為了報出它多 flag 了幾項。
NAIVE = re.compile(r'\d+\.\d+|\d+\s*(?:±|\+/-)|\d+\s*(?:of|/)\s*\d+|\d+\s*%')
# ✅ 第二版：問有沒有**結果標記**。⚠️ 方法段也有數字，但通常沒有這些。
RESULT = re.compile(
    r'p\s*[<=>]|±|\+/-|\d+\s*%|\bF\s*\(|\bt\s*\(|χ²|\bSD\b|\bSE\b'
    r'|\d+\s*\(\s*\d+\s*\)|\d+•\d+|\d+\.\d+')


def main():
    ids = {c[-16:]: c for c in corpus.acquired_roster()[0]}
    cache = {}

    def sections(report):
        if report not in cache:
            cache[report] = {str(s.title or ''): (s.text or '')
                             for s in corpus.load_document(ids[report]).sections}
        return cache[report]

    scanned = 0
    naive_flags, result_flags = [], []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        for item in doc.get('reportedOutcomes') or []:
            if not (item.get('scopeDecision') or {}).get('inScope'):
                continue
            scanned += 1
            section = ((item.get('sourceLocation') or {}).get('section')) or ''
            text = sections(report).get(section, '')
            row = {'report': report, 'section': section,
                   'sectionChars': len(text),
                   'outcomeId': item.get('normalisedOutcomeRef')}
            if not NAIVE.search(text):
                naive_flags.append(row)
            if not RESULT.search(text):
                result_flags.append(row)

    withdrawn = [r for r in naive_flags if r not in result_flags]
    by_report = Counter(r['report'] for r in result_flags)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('掃到的是那 98 項（必觸發）', scanned == 98,
          '🚨 對不上就代表本支看的不是同一批；實得 %d 項' % scanned)
    # ✅ 正對照：⚠️ 結果標記必須在絕大多數段落裡找得到。
    probe('結果標記在絕大多數來源段落裡找得到（正對照，必觸發）',
          len(result_flags) < scanned * 0.2,
          '✅ 找不到者 %d／%d；🚨 若過半找不到，代表樣式壞了，'
          '而「這幾項有問題」會是假的' % (len(result_flags), scanned))
    # 🚨 必觸發之反向：⚠️ 第二版要真的比第一版少 flag，否則修正沒有生效。
    probe('第二版確實收回了第一版的偽陽性（必觸發之反向）',
          len(withdrawn) > 0,
          '🚨 第一版 flag %d 項、第二版 %d 項，收回 %d 項；'
          '⚠️ 若收回為零，代表本室宣稱的偽陽性並不存在'
          % (len(naive_flags), len(result_flags), len(withdrawn)))
    # 🚨 這一道會紅。
    probe('每一項在範圍內的結局，其來源段落都含結果',
          not result_flags,
          '🚨 實得 %d 項，集中在 %s；⚠️ 它們指向的是方法段——'
          '🚫 照那個座標去查會看到量表怎麼評，而不是要驗的數字'
          % (len(result_flags), dict(by_report)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'source-section-has-no-result',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inScopeScanned': scanned,
        'naivePassFlagged': len(naive_flags),
        'resultMarkerPassFlagged': len(result_flags),
        'withdrawnAsFalsePositive': withdrawn,
        'flagged': result_flags,
        'flaggedByReport': dict(by_report),
        'firstPassWasWrong': (
            '🚨 第一版問「段落裡有沒有數字」，flag 了 %d 項，其中 %d 項是偽陽性：'
            '⚠️ 本室的樣式漏掉整數配括號的標準差（12 (1)）與中點小數（11•7）。'
            '🚨 而更根本的是問錯了——**方法段也有數字**'
            '（100mm visual analogue scale 就是一個）。'
            '✅ 該問的是有沒有結果標記。'
            % (len(naive_flags), len(withdrawn))),
        'notTheSameAsRound597': (
            '⚠️ 第 597 輪那 4 項是「該症狀在整份文件裡沒有數字」；'
            '🚨 本輪這 7 項是「結果存在，但座標指向方法段」。'
            '🚫 兩者性質不同，不可相加。'),
        'evidence': (
            '✅ 該篇的 GI 結果在 Interaction effects (time x treatment) 段，'
            '⚠️ 而 7 項的座標寫的是 Gastrointestinal discomfort——'
            '那一段整段只是「以 100 mm 視覺類比量表評分」的方法描述。'),
        'relationToRound590': (
            '⚠️ 第 590 輪已驗「來源段落確實存在」（790／790）。'
            '✅ 存在，🚫 但不保證它是結果段。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n598 來源段落裡有沒有結果 ===')
    print('   在範圍內 %d 項｜第一版（有沒有數字）flag %d｜'
          '✅ 第二版（有沒有結果標記）flag %d｜收回 %d'
          % (scanned, len(naive_flags), len(result_flags), len(withdrawn)))
    for row in result_flags:
        print('   🚨 %s｜%s｜%s（%d 字）'
              % (row['report'], row['outcomeId'], row['section'][:38],
                 row['sectionChars']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
