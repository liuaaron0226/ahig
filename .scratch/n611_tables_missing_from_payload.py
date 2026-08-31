# -*- coding: utf-8 -*-
"""**13 篇論文的內文在引用讀者看不到的表格。**（第 611 輪）

## 🚨 這是取得層的缺陷，不是讀的人的

| 來源 | 篇數 | sections 裡有表格段落者 |
|---|---|---|
| `europe-pmc-jats` | 26 | **20（77%）** |
| **`grobid-tei`** | 15 | **🚨 1（7%）** |

⚠️ 而 TEI 檔**本身有表格**（中位數 2、最多 27）——
**🚨 故不是沒抓到，是沒有進到讀的人手上的那份文件。**

## 🚨 更直接的證據：內文指著讀者打不開的東西

**13／15 篇** GROBID 論文的內文寫著「見 Table 2」之類，
**而讀的人手上一張表都沒有。**
⚠️ 那本博士論文尤其極端：**TEI 有 27 張表、內文引用 95 次，一張都看不到。**

## ⚠️ 這軟化了本室自己第 597 輪的指控

n597 說某篇有 4 項「宣稱有數值，而文件裡沒有那個數字」。
**🚨 而那一篇正是 GROBID 來源**，內文引用了 2 次表格而讀者看不到。

> **⚠️ 故那 4 項的數值**可能就在那些表裡**——🚫 而讀的人與本室都看不到。**
> **✅ 指控要改寫**：不是「宣稱了不存在的數字」，
> 🚨 而是「**在一份被削掉表格的文件上，宣稱了看不到的數字**」。
> ⚠️ 兩者都不對，**但責任不在同一層。**

## 🚨 而它影響的不只那 4 項

⚠️ 「沒有數值結果」「劑量沒報」這些排除理由，
**🚨 在這 13 篇上都可能是「表格被削掉」造成的**，🚫 不是論文沒寫。

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

OUT = Path(__file__).resolve().parent / 'n611_tables_missing.json'
TABLE_SECTION = re.compile(r'^\s*table\b', re.I)
TABLE_REF = re.compile(r'\btable\s*\d', re.I)


def sources():
    out = {}
    for path in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))
        key = doc.get('candidateId', '').split(':')[-1][-16:]
        if not doc.get('sourceType'):
            continue
        name = doc.get('teiFile') or doc.get('rawFile') or ''
        target = path.parent / name
        tables = None
        if name and target.is_file() and target.suffix != '.pdf':
            try:
                tables = target.read_text(
                    encoding='utf-8', errors='ignore').lower().count('<table')
            except OSError:
                tables = None
        out[key] = {'sourceType': doc['sourceType'], 'tablesInSource': tables}
    return out


def main():
    meta = sources()
    rows = []
    for candidate in corpus.acquired_roster()[0]:
        key = candidate[-16:]
        info = meta.get(key) or {}
        document = corpus.load_document(candidate)
        has_section = any(TABLE_SECTION.match(str(s.title or ''))
                          for s in document.sections)
        refs = len(TABLE_REF.findall(document.content))
        rows.append({'report': key, 'sourceType': info.get('sourceType'),
                     'tablesInSource': info.get('tablesInSource'),
                     'tableSectionsInPayload': has_section,
                     'inTextTableReferences': refs})

    by_source = {}
    for row in rows:
        entry = by_source.setdefault(row['sourceType'], {'n': 0, 'withTables': 0})
        entry['n'] += 1
        entry['withTables'] += 1 if row['tableSectionsInPayload'] else 0

    blind = [r for r in rows
             if not r['tableSectionsInPayload'] and r['inTextTableReferences']]
    grobid = [r for r in rows if r['sourceType'] == 'grobid-tei']
    grobid_blind = [r for r in blind if r['sourceType'] == 'grobid-tei']
    worst = max(rows, key=lambda r: r['inTextTableReferences'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩種來源都掃到了（必觸發）',
          len(by_source) >= 2 and all(v['n'] for v in by_source.values()),
          '🚨 少一種就沒有對照；實得 %s'
          % {k: v['n'] for k, v in by_source.items()})
    # ✅ 正對照：⚠️ 這條管線**做得到**把表格交給讀的人。
    jats = by_source.get('europe-pmc-jats', {'n': 0, 'withTables': 0})
    probe('這條管線做得到把表格交給讀的人（正對照，必觸發）',
          jats['withTables'] > 0,
          '✅ JATS 來源 %d 篇中 %d 篇的 sections 有表格段落；'
          '🚨 若為零，那就是「本來就不給表格」，而不是這 15 篇被削掉'
          % (jats['n'], jats['withTables']))
    probe('來源檔本身有表格（必觸發之反向）',
          any((r['tablesInSource'] or 0) > 0 for r in grobid),
          '⚠️ GROBID 來源檔的表格數中位數 %s；🚨 若全為零，'
          '那是抓取階段就沒有，而不是後段削掉'
          % sorted((r['tablesInSource'] or 0) for r in grobid)[len(grobid) // 2])
    # 🚨 這一道會紅，而它是本支的主張。
    probe('每一位讀者都看得到論文引用的表格',
          not blind,
          '🚨 實得 %d 篇的內文引用了「Table N」而讀的人手上沒有表格'
          '（其中 GROBID 來源 %d／%d 篇）；'
          '⚠️ 最極端者引用 %d 次、來源檔有 %s 張表'
          % (len(blind), len(grobid_blind), len(grobid),
             worst['inTextTableReferences'], worst['tablesInSource']))

    doc = {
        'schemaVersion': 1,
        'documentType': 'tables-missing-from-payload',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'bySource': {k: {'reports': v['n'],
                         'withTableSections': v['withTables'],
                         'share': '%d%%' % round(100 * v['withTables'] / v['n'])}
                     for k, v in by_source.items()},
        'reportsCitingInvisibleTables': len(blind),
        'grobidReports': len(grobid),
        'grobidCitingInvisibleTables': len(grobid_blind),
        'rows': rows,
        'whereTheLossIs': (
            '🚨 TEI 來源檔本身有表格（中位數 2、最多 27），'
            '⚠️ 而讀的人拿到的 sections 幾乎沒有——'
            '**✅ 故損失發生在做 sections 的那一步，🚫 不是抓取。**'),
        'softensRound597': (
            '⚠️ n597 說某篇有 4 項「宣稱有數值而文件裡沒有」。'
            '🚨 而那一篇正是 GROBID 來源，內文引用了表格而讀者看不到。'
            '✅ 指控要改寫：不是「宣稱了不存在的數字」，'
            '而是「**在一份被削掉表格的文件上，宣稱了看不到的數字**」——'
            '⚠️ 兩者都不對，🚫 但責任不在同一層。'),
        'widerConsequence': (
            '🚨 「沒有數值結果」「劑量沒報」這些排除理由，'
            '⚠️ 在這 13 篇上都可能是表格被削掉造成的，🚫 不是論文沒寫。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n611 讀者手上沒有表格 ===')
    for key, value in by_source.items():
        print('   %-18s %2d 篇｜sections 有表格 %2d 篇（%d%%）'
              % (key, value['n'], value['withTables'],
                 round(100 * value['withTables'] / value['n'])))
    print('   🚨 內文引用表格而讀者看不到：%d 篇（GROBID %d／%d）'
          % (len(blind), len(grobid_blind), len(grobid)))
    print('   ⚠️ 最極端：%s 引用 %d 次、來源檔 %s 張表'
          % (worst['report'], worst['inTextTableReferences'],
             worst['tablesInSource']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
