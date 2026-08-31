# -*- coding: utf-8 -*-
"""**兩條檢查，各自看不見對方抓到的東西。**（第 609 輪）

## 🚨 補上互補的那一角

n598 用「**來源段落裡有沒有結果標記**」抓到 7 項。
⚠️ 但**方法段本來就有數字**（「100 mm 量表」「12 位受試者」），
🚨 故那條檢查對「有數字的方法段」是盲的。
**✅ 本支補上另一角：來源段落的**標題**本身就是方法類。**

## ✅ 結果：在範圍內的 98 項，一項都沒有

| | |
|---|---|
| 語料相異段落標題 | 591 |
| 🚨 樣式命中的標題 | **38** |
| 🚨 **範圍外**的結局引用方法段 | **13 項**（✅ 證明這條檢查會亮） |
| ✅ **在範圍內**的結局引用方法段 | **0 項** |

## 🚨 而最要緊的一句：**這條檢查抓不到 n598 那 7 項**

⚠️ 那 7 項引用的段落叫 `Gastrointestinal discomfort`——
**🚫 那個標題一點都不像方法段，而它的內容是方法。**

> **🚨 故兩條檢查各自看不見對方抓到的東西：**
> - **標題式**：0 項（⚠️ 對「名字不像方法的方法段」全盲）；
> - **內容式**（n598）：7 項（⚠️ 對「有數字的方法段」全盲）。
>
> **✅ 兩條都要，🚫 而任何一條單獨都會給出「沒事」。**

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

OUT = Path(__file__).resolve().parent / 'n609_methods_title_check.json'
N598 = Path(__file__).resolve().parent / 'n598_source_section_no_result.json'

METHODS = re.compile(
    r'^\s*(?:\d+\.?\d*\.?\s*)?'
    r'(?:methods?|materials and methods|statistical analysis|statistics'
    r'|study design|experimental (?:design|approach|overview|protocol'
    r'|procedures?|trials?)|participants?|subjects?|procedures?'
    r'|measurements?|instruments?|protocol|pre-?testing|preliminary testing'
    r'|familiari[sz]ation|dietary standardisation|nutritional intervention'
    r'|data (?:collection|analysis))\s*$', re.I)


def main():
    titles = set()
    for candidate in corpus.acquired_roster()[0]:
        titles |= {str(s.title or '')
                   for s in corpus.load_document(candidate).sections}
    matched_titles = sorted(t for t in titles if METHODS.match(t))

    in_scope = out_scope = 0
    in_hits, out_hits = [], []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        for item in doc.get('reportedOutcomes') or []:
            scoped = bool((item.get('scopeDecision') or {}).get('inScope'))
            section = ((item.get('sourceLocation') or {}).get('section')) or ''
            if scoped:
                in_scope += 1
            else:
                out_scope += 1
            if METHODS.match(section):
                (in_hits if scoped else out_hits).append(
                    {'report': report, 'section': section})

    # 🚨 n598 抓到的那 7 項，本條標題式檢查抓不抓得到。
    prior = json.loads(N598.read_text(encoding='utf-8'))
    prior_sections = {row['section'] for row in prior['flagged']}
    caught_by_title = sorted(s for s in prior_sections if METHODS.match(s))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('掃到的是那 98 項（必觸發）', in_scope == 98,
          '🚨 對不上就代表本支看的不是同一批；實得 %d 項' % in_scope)
    probe('樣式在真實標題上打得中（必觸發之反向）',
          0 < len(matched_titles) < len(titles),
          '✅ 語料 %d 個相異標題中命中 %d 個；🚨 若為零，'
          '「在範圍內 0 項」只是樣式壞了' % (len(titles), len(matched_titles)))
    probe('這條檢查在真實資料上會亮（必觸發之反向）',
          bool(out_hits),
          '✅ 範圍外的結局有 %d 項引用方法段；🚨 若為零，'
          '「在範圍內 0 項」就可能只是它從不觸發' % len(out_hits))
    probe('在範圍內沒有結局引用方法類標題的段落',
          not in_hits,
          '✅ 實得 %d 項' % len(in_hits))
    # 🚨 這一道會紅，而它是本支真正要說的事。
    probe('標題式檢查抓得到 n598 那一批',
          bool(caught_by_title),
          '🚨 n598 那 7 項引用的段落是 %s——⚠️ 那個標題一點都不像方法段，'
          '而內容是方法。🚫 故標題式檢查對它全盲，'
          '✅ 而內容式檢查對「有數字的方法段」全盲——**兩條都要**'
          % sorted(prior_sections))

    doc = {
        'schemaVersion': 1,
        'documentType': 'methods-title-check',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'distinctSectionTitles': len(titles),
        'titlesMatchingMethods': len(matched_titles),
        'inScopeScanned': in_scope,
        'outOfScopeScanned': out_scope,
        'inScopeCitingMethodsTitle': len(in_hits),
        'outOfScopeCitingMethodsTitle': len(out_hits),
        'outOfScopeByReport': dict(Counter(h['report'] for h in out_hits)),
        'n598SectionsCaughtByTitle': caught_by_title,
        'complementarity': (
            '🚨 兩條檢查各自看不見對方抓到的東西：'
            '⚠️ 標題式對「名字不像方法的方法段」全盲（n598 那 7 項就是）；'
            '⚠️ 內容式對「有數字的方法段」全盲（方法段本來就有數字）。'
            '✅ 兩條都要，🚫 而任何一條單獨都會給出「沒事」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n609 標題式方法段檢查 ===')
    print('   相異標題 %d｜命中 %d｜在範圍內 %d 項｜範圍外 %d 項'
          % (len(titles), len(matched_titles), in_scope, out_scope))
    print('   ✅ 在範圍內引用方法段：%d 項｜🚨 範圍外：%d 項'
          % (len(in_hits), len(out_hits)))
    print('   🚨 n598 那批被標題式抓到的：%s' % (caught_by_title or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
