# -*- coding: utf-8 -*-
"""**根因：`parse_tei` 只走 `<div>`，而 TEI 把表格放在 `<div>` 旁邊。**（第 612 輪）

## 🚨 不對稱在程式裡，不在來源

| | JATS 那一支 | **TEI 那一支** |
|---|---|---|
| 表格處理 | ✅ 有 `append_table`，明白處理 `table-wrap` | **🚫 沒有任何一行** |
| 走訪範圍 | 節點與其中的 `table-wrap` | **⚠️ 只走 `<body>` 底下的 `<div>`** |

⚠️ 而 GROBID 把表格放在 **`<figure type="table">`**，
**🚨 它是 `<body>` 的直接子元素、與 `<div>` 平行**——
✅ 實測某篇：`table` 的祖先鏈是 `figure[type=table] → body`，
**🚫 而 `div` 內含 figure 數為 0。**

> **✅ 故 `visit()` 從來不會走到它們。**

## 🚨 掉了多少（15 篇 TEI）

| 被跳過的 `<body>` 直接子元素 | 數量 |
|---|---|
| `<figure>` | **225** |
| 其中 `type="table"` | **50** |
| `<note>` | 19 |

⚠️ 那本博士論文一篇就佔 **115 個 figure、27 張表**。

## 🚨 修它會讓 A1 更難，而這件事要先講

⚠️ 重新解析會改變 `contentSha256` 與 `sectionsSha256`——
**🚨 那 15 篇的綁定與每一份 draft 的 `manifestation` 雜湊都會變。**

> **⚠️ 也就是說：修好之後，那 15 篇是「另一版的文件」。**
> 🚨 而 A1 問的正是「全語料是不是同一版請求」——
> **✅ 修這個缺陷會製造一次新的版本分歧，🚫 而不修則有 13 篇的讀者看不到表格。**
> **📮 兩害相權是協調者的事，🚫 不是本室逕自改一支解析器。**

## 🚫 本支只診斷，不修改
"""
import collections
import json
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n612_parse_tei_root_cause.json'
SOURCE = REPO / 'ahig' / 'ahig' / 'search' / 'fulltext.py'


def local(tag):
    return tag.rsplit('}', 1)[-1]


def function_body(text, name):
    start = text.index('def %s(' % name)
    nxt = text.find('\ndef ', start + 1)
    return text[start:nxt if nxt > 0 else len(text)]


def main():
    source = SOURCE.read_text(encoding='utf-8')
    tei_body = function_body(source, 'parse_tei')
    jats_body = function_body(source, 'parse_jats') if 'def parse_jats(' in source else ''

    tei_mentions = {word: tei_body.lower().count(word)
                    for word in ('table', 'figure')}
    jats_mentions = {word: jats_body.lower().count(word)
                     for word in ('table', 'figure')}

    counts = collections.Counter()
    per_report = []
    for manifest in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(manifest.read_text(encoding='utf-8'))
        if doc.get('sourceType') != 'grobid-tei':
            continue
        target = manifest.parent / (doc.get('teiFile') or '')
        if not target.is_file():
            continue
        try:
            root = ET.parse(target).getroot()
        except ET.ParseError:
            continue
        body = next((n for n in root.iter() if local(n.tag) == 'body'), None)
        if body is None:
            continue
        figures = [c for c in body if local(c.tag) == 'figure']
        tables = [c for c in figures if (c.get('type') or '') == 'table']
        notes = [c for c in body if local(c.tag) == 'note']
        counts['figure'] += len(figures)
        counts['figure-table'] += len(tables)
        counts['note'] += len(notes)
        per_report.append({'report': doc['candidateId'][-16:],
                           'figures': len(figures), 'tables': len(tables)})

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('讀到了 15 篇 TEI（必觸發）',
          len(per_report) == 15,
          '🚨 少一篇診斷就不完整；實得 %d 篇' % len(per_report))
    # ✅ 正對照：⚠️ JATS 那一支確實處理表格——🚨 故不對稱在程式裡。
    probe('JATS 那一支確實處理表格（正對照，必觸發）',
          jats_mentions.get('table', 0) > 0,
          '✅ parse_jats 內提到 table %d 次；🚨 若為零，'
          '那就是「這條管線本來就不收表格」，而不是 TEI 那支漏了'
          % jats_mentions.get('table', 0))
    # 🚨 這一道會紅：⚠️ TEI 那一支一個字都沒提。
    probe('TEI 那一支有處理表格的分支',
          tei_mentions.get('table', 0) > 0,
          '🚨 parse_tei 內提到 table %d 次、figure %d 次——'
          '⚠️ 它只走 <body> 底下的 <div>，而 GROBID 把表格放在 '
          '<figure type="table">，那是 <div> 的兄弟節點'
          % (tei_mentions.get('table', 0), tei_mentions.get('figure', 0)))
    # 🚨 這一道也會紅：⚠️ 修它會製造新的版本分歧。
    probe('修好之後語料仍是同一版', False,
          '🚨 重新解析會改變 contentSha256 與 sectionsSha256——'
          '⚠️ 那 15 篇的綁定與每一份 draft 的 manifestation 雜湊都會變；'
          '✅ 而 A1 問的正是「全語料是不是同一版請求」')

    doc = {
        'schemaVersion': 1,
        'documentType': 'parse-tei-root-cause',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'rootCause': (
            '🚨 `parse_tei` 只走 `<body>` 底下的 `<div>`；'
            '⚠️ 而 GROBID 把表格放在 `<figure type="table">`，'
            '它是 `<body>` 的直接子元素、與 `<div>` 平行。'
            '✅ 故 visit() 從來不會走到它們。'),
        'asymmetryInCode': {'parse_tei': tei_mentions,
                            'parse_jats': jats_mentions,
                            'note': '🚨 JATS 有 append_table，TEI 一行都沒有。'},
        'droppedAcross15Reports': dict(counts),
        'perReport': per_report,
        'proposedMinimalFix': (
            '✅ 在 TEI 那一支比照 JATS 的 append_table：'
            '把 `<body>` 直接子元素中的 `<figure type="table">`（以及 div 內的）'
            '收成 kind=table 的節。'
            '⚠️ 本室**不逕自施行**——🚨 它會改變雜湊。'),
        'fixMakesA1Harder': (
            '🚨 重新解析會改變 contentSha256／sectionsSha256，'
            '⚠️ 那 15 篇的綁定與 draft 的 manifestation 都會變——'
            '✅ 修好之後那 15 篇是「另一版的文件」。'
            '📮 而 A1 問的正是全語料同版與否：'
            '**修會製造新的版本分歧，不修則 13 篇的讀者看不到表格。**'
            '🚫 兩害相權是協調者的事。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n612 parse_tei 根因 ===')
    print('   parse_tei 提到 table/figure：%s' % tei_mentions)
    print('   parse_jats 提到 table/figure：%s' % jats_mentions)
    print('   🚨 15 篇 TEI 被跳過：%s' % dict(counts))
    top = sorted(per_report, key=lambda r: -r['figures'])[:3]
    print('   最多者：%s' % [(r['report'], r['figures'], r['tables']) for r in top])
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
