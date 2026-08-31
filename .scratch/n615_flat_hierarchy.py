# -*- coding: utf-8 -*-
"""**第二重落差：那 15 篇的段落結構是平的。**（第 615 輪）

## 🚨 量出來的

| 來源 | 各篇最大 `path` 深度 |
|---|---|
| `europe-pmc-jats` | **2–4**（26 篇） |
| **`grobid-tei`** | **🚨 全部 15 篇都是 1** |

⚠️ `parse_tei` 的 `visit()` 會遞迴進巢狀 `<div>`——
**🚨 故深度為 1 代表 GROBID 產出的 div 本身就是平的**，🚫 不是解析器壓平的。
**⚠️ 但對讀的人而言，後果一樣。**

## 🚨 後果：讀的人無從知道一段屬於哪一章

那本博士論文有「Chapter Two: Literature review」與自己的研究章節，
**⚠️ 而所有段落在 `path` 上都是同一層。**

> ✅ 實測那 4 項在範圍內的結局，來源是
> 「Skeletal muscle glycogen concentration」與「Time to exhaustion cycling
> capacity test」——**兩段都確實是它自己的結果**
> （有自己的數據，並引用「Figure 5.7」定位在第五章）。
>
> **🚨 但那個定位來自內文碰巧寫了圖號，🚫 不是來自結構。**
> **⚠️ 那是運氣，不是設計。**

## 🚨 兩重落差加起來：「讀過」對這 15 篇是另一件事

| | JATS | GROBID |
|---|---|---|
| 讀者拿得到表格 | **77%** | **🚨 7%** |
| 段落層級深度 | 2–4 | **🚨 1** |

**⚠️ 而 A1 問的是「全語料同一版請求」——🚨 這比版本更深：內容本身就不對等。**

## ✅ 順帶：D5 那個「對照組被當成劑量不合格」有了實例

⚠️ 該論文 Study 2 的力竭時間有 **0／45／90 g·h⁻¹** 三臂，
**🚨 而 0 g·h⁻¹ 那一臂被判成 `dose-outside-bands`。**
✅ 它是對照組——**🚫 不是劑量不合格。**

## 🚫 本支不入輪次閘門
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

OUT = Path(__file__).resolve().parent / 'n615_flat_hierarchy.json'
THESIS = '307c0dd5b141caed'


def main():
    depths = collections.defaultdict(collections.Counter)
    per_report = {}
    for manifest in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(manifest.read_text(encoding='utf-8'))
        source = doc.get('sourceType')
        if source not in ('grobid-tei', 'europe-pmc-jats'):
            continue
        target = manifest.parent / (doc.get('sectionsFile') or '')
        if not target.is_file():
            continue
        sections = json.loads(target.read_text(encoding='utf-8'))['sections']
        deepest = max((len(s.get('path') or []) for s in sections), default=0)
        depths[source][deepest] += 1
        per_report[doc['candidateId'][-16:]] = {'sourceType': source,
                                                'maxDepth': deepest,
                                                'sections': len(sections)}

    # 🚨 D5 之實例：⚠️ 對照組被判成劑量不合格。
    control_arm = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for item in doc.get('reportedOutcomes') or []:
            decision = item.get('scopeDecision') or {}
            if (decision.get('reasonCode') == 'notExtracted-dose-outside-bands'
                    and item.get('dose') == 0):
                control_arm.append({'report': doc['report'][-16:],
                                    'outcomeId': item.get('normalisedOutcomeRef')})

    jats = depths.get('europe-pmc-jats', collections.Counter())
    tei = depths.get('grobid-tei', collections.Counter())

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩種來源都量到了（必觸發）',
          sum(jats.values()) > 0 and sum(tei.values()) > 0,
          '🚨 少一種就沒有對照；實得 JATS %d 篇、TEI %d 篇'
          % (sum(jats.values()), sum(tei.values())))
    # ✅ 正對照：⚠️ 這條管線**記得住**層級。
    probe('這條管線記得住段落層級（正對照，必觸發）',
          any(d > 1 for d in jats),
          '✅ JATS 各篇最大深度分布 %s；🚨 若全是 1，那就是「本來就不記層級」，'
          '而不是這 15 篇被壓平' % dict(sorted(jats.items())))
    # 🚨 這一道會紅。
    probe('全語料的段落結構深度可比',
          set(jats) == set(tei),
          '🚨 JATS %s 對 TEI %s——⚠️ 那 15 篇全部只有一層，'
          '🚫 讀的人無從知道一段屬於哪一章'
          % (dict(sorted(jats.items())), dict(sorted(tei.items()))))
    # 🚨 D5 之實例。
    probe('沒有把對照組判成劑量不合格的情形',
          not control_arm,
          '🚨 實得 %d 項 dose=0 被判 dose-outside-bands：%s；'
          '⚠️ 它們是對照組，🚫 不是劑量不合格——✅ D5 的實例'
          % (len(control_arm),
             sorted({c['report'] for c in control_arm})))

    doc = {
        'schemaVersion': 1,
        'documentType': 'flat-hierarchy',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'depthBySource': {k: dict(sorted(v.items())) for k, v in depths.items()},
        'perReport': per_report,
        'whoFlattened': (
            '⚠️ `parse_tei` 的 visit() 會遞迴進巢狀 <div>，'
            '🚨 故深度為 1 代表 GROBID 產出的 div 本身就是平的——'
            '🚫 不是解析器壓平的。⚠️ 但對讀的人而言後果一樣。'),
        'consequence': (
            '🚨 那本博士論文有第二章文獻回顧與自己的研究章節，'
            '⚠️ 而所有段落在 path 上都是同一層——'
            '🚫 讀的人無從知道一段屬於哪一章。'),
        'attributionWasLucky': (
            '✅ 實測那 4 項在範圍內的結局，兩段都確實是它自己的結果'
            '（有自己的數據，並引用 Figure 5.7 定位在第五章）。'
            '🚨 但那個定位來自內文碰巧寫了圖號，🚫 不是來自結構——⚠️ 那是運氣。'),
        'twoGapsTogether': (
            '⚠️ 讀者拿得到表格：JATS 77%、GROBID 7%；'
            '段落層級深度：JATS 2–4、GROBID 1。'
            '🚨 「讀過」對那 15 篇是另一件事——'
            '而 A1 問的只是「同一版請求」，**這比版本更深**。'),
        'd5Instance': {'items': control_arm,
                       'why': ('🚨 該論文 Study 2 的力竭時間有 0／45／90 g/h 三臂，'
                               '而 0 g/h 那一臂被判 dose-outside-bands——'
                               '✅ 它是對照組，🚫 不是劑量不合格。')},
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n615 段落結構是平的 ===')
    for source, counter in depths.items():
        print('   %-18s 最大深度分布：%s' % (source, dict(sorted(counter.items()))))
    print('   🚨 dose=0 被判劑量不合格：%d 項（%s）'
          % (len(control_arm), sorted({c['report'] for c in control_arm})))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
