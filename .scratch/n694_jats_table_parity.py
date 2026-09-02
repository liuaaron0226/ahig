# -*- coding: utf-8 -*-
"""**JATS 那一支也漏表格嗎。**（第 694 輪）

## 🚨 為什麼問

第 611 輪：JATS 26 篇裡**只有 20 篇有表格節**（77%）。
⚠️ 那 6 篇是**論文本來就沒表**，還是 **`parse_jats` 也漏了**？

> **🚨 `D17` 只講 `parse_tei`。若 JATS 那一支也有缺口，那是新的。**

## ✅ 做法：兩邊都數，原始檔 vs sections

- **JATS 原始檔**：`<table-wrap>` 的出現次數
- **TEI 原始檔**：`<figure type="table">` 的出現次數
- **sections**：`kind == "table"` 的節數

## 🚨 而本支的關鍵是**控制設計**

⚠️ 若這套方法在 **TEI** 那邊看不到**已知的缺陷**（第 611／612 輪已證），
**🚫 它在 JATS 上說「沒事」就不可信。**

> **✅ 故設一道必觸發之正對照：本支必須在 TEI 那邊重現那個落差。**

## 🚫 本支只數標籤與節數，🚫 不輸出任何內容文字；不改任何檔案、不送外部請求
"""
import collections
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n694_jats_table_parity.json'

JATS_TABLE = re.compile(r'<table-wrap[\s>]')
TEI_TABLE = re.compile(r'<figure[^>]*type="table"')
FAKE_TAG = re.compile(r'<tag-that-cannot-exist-694[\s>]')


def _where(text, pos):
    """那個標籤落在文件的哪一段。🚫 只看結構位置，不看內容。"""
    body = text.rfind('<body', 0, pos)
    body_end = text.rfind('</body>', 0, pos)
    back = text.rfind('<back', 0, pos)
    floats = text.rfind('<floats-group', 0, pos)
    if floats > max(body, back, body_end):
        return 'floats-group'
    if back > max(body, body_end):
        return 'back'
    return 'body' if body > body_end else 'other'


def scan():
    rows = []
    for manifest in (ROOT / 'fulltext').rglob('manifest.json'):
        try:
            doc = json.loads(manifest.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        source = doc.get('sourceType')
        candidate = str(doc.get('candidateId') or '')
        if not source or not candidate:
            continue
        # 🚨 rawFile／sectionsFile 可能是空的——⚠️ 那時路徑會落回**目錄本身**，
        # 而讀目錄在 Windows 上會拋 PermissionError。✅ 故要求它是**檔案**。
        raw_name = str(doc.get('rawFile') or '')
        sec_name = str(doc.get('sectionsFile') or '')
        raw_path = manifest.parent / raw_name if raw_name else None
        # 🚨 grobid-tei 的 `rawFile` 是 **PDF**——⚠️ TEI 在同目錄的 `*.tei.xml`。
        # ✅ 第一版在 PDF 裡找 XML 標籤，數到 0 張表；
        # **🚨 那是本支的必觸發正對照擋下來的**，🚫 不是本室自己看出來的。
        if source == 'grobid-tei':
            tei = sorted(manifest.parent.glob('*.tei.xml'))
            raw_path = tei[0] if tei else None
        sec_path = manifest.parent / sec_name if sec_name else None
        raw_tables = fake_hits = None
        if raw_path is not None and raw_path.is_file():
            text = raw_path.read_text(encoding='utf-8', errors='replace')
            pattern = JATS_TABLE if source == 'europe-pmc-jats' else TEI_TABLE
            raw_tables = len(pattern.findall(text))
            fake_hits = len(FAKE_TAG.findall(text))
        sec_tables = None
        if sec_path is not None and sec_path.is_file():
            try:
                sections = json.loads(sec_path.read_text(encoding='utf-8'))
                sec_tables = sum(
                    1 for s in (sections.get('sections') or [])
                    if str(s.get('kind')).lower() == 'table')
            except (OSError, ValueError):
                sec_tables = None
        rows.append({'report': candidate[-16:], 'sourceType': source,
                     'rawTables': raw_tables, 'sectionTables': sec_tables,
                     'fakeTagHits': fake_hits,
                     'rawPresent': bool(raw_path and raw_path.is_file()),
                     'sectionsPresent': bool(sec_path
                                             and sec_path.is_file())})
    return rows


def main():
    rows = scan()
    by_source = collections.defaultdict(list)
    for row in rows:
        by_source[row['sourceType']].append(row)

    summary = {}
    for source, group in by_source.items():
        usable = [r for r in group
                  if r['rawTables'] is not None
                  and r['sectionTables'] is not None]
        raw_total = sum(r['rawTables'] for r in usable)
        sec_total = sum(r['sectionTables'] for r in usable)
        gap = [r['report'] for r in usable
               if r['rawTables'] > 0 and r['sectionTables'] == 0]
        summary[source] = {
            'reports': len(group), 'comparable': len(usable),
            'rawTables': raw_total, 'sectionTables': sec_total,
            'reportsWithTablesButNoTableSection': gap,
        }

    jats = summary.get('europe-pmc-jats', {})
    tei = summary.get('grobid-tei', {})

    # 🚨 那 4 篇的 `<table-wrap>` 到底在文件的哪一段——⚠️ 與 TEI 的根因同構嗎。
    suspects = set(jats.get('reportsWithTablesButNoTableSection') or [])
    control = next((r['report'] for r in by_source.get('europe-pmc-jats', [])
                    if r['report'] not in suspects
                    and (r['rawTables'] or 0) > 0
                    and (r['sectionTables'] or 0) > 0), None)
    placement = {}
    for row in by_source.get('europe-pmc-jats', []):
        if row['report'] not in suspects and row['report'] != control:
            continue
        manifest = next(
            (m for m in (ROOT / 'fulltext').rglob('manifest.json')
             if json.loads(m.read_text(encoding='utf-8'))
             .get('candidateId', '').endswith(row['report'])), None)
        if manifest is None:
            continue
        doc_m = json.loads(manifest.read_text(encoding='utf-8'))
        raw = manifest.parent / str(doc_m.get('rawFile') or '')
        if not raw.is_file():
            continue
        text = raw.read_text(encoding='utf-8', errors='replace')
        counts = collections.Counter(
            _where(text, m.start()) for m in JATS_TABLE.finditer(text))
        placement[row['report']] = {
            'isControl': row['report'] == control,
            'tableWrapPlacement': dict(counts)}

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩種來源都掃得到、也比得動（必觸發之正對照）',
          jats.get('comparable', 0) >= 10 and tei.get('comparable', 0) >= 10,
          '🚨 JATS 可比 %s 篇、TEI 可比 %s 篇；'
          '⚠️ 太少代表檔案指標讀不到，本支就沒有分母'
          % (jats.get('comparable'), tei.get('comparable')))
    # 🚨 這一道最重要：方法必須重現**已知的**缺陷。
    probe('本支在 TEI 那邊重現得出已知的落差（必觸發之正對照）',
          tei.get('rawTables', 0) > 0 and tei.get('sectionTables', 1) == 0,
          '🚨 TEI：原始檔 %s 張表 → sections %s 個表格節；'
          '⚠️ 若這裡看不到落差，本支在 JATS 上說「沒事」就不可信'
          % (tei.get('rawTables'), tei.get('sectionTables')))
    probe('捏造的標籤在任何檔案裡都是 0 次（必觸發之反向）',
          all((r['fakeTagHits'] or 0) == 0 for r in rows),
          '🚨 捏造標籤命中總數 %d；⚠️ 若不是 0，代表比對是在亂數'
          % sum(r['fakeTagHits'] or 0 for r in rows))
    ctrl = placement.get(control, {}).get('tableWrapPlacement', {})
    probe('對照篇（有表格節那一篇）的 table-wrap 在 `<body>` 裡'
          '（必觸發之正對照）',
          ctrl.get('body', 0) > 0,
          '🚨 對照篇 %s 的位置分佈：%s；'
          '⚠️ 若它也不在 body，本支的根因說法就不成立' % (control, ctrl))
    off_body = {r: v['tableWrapPlacement'] for r, v in placement.items()
                if not v['isControl']}
    probe('那幾篇的 table-wrap 也在 `<body>` 裡',
          all(v.get('body', 0) > 0 for v in off_body.values()),
          '🚨 位置分佈：%s；⚠️ 全落在 `<floats-group>` 的話，'
          '**根因與 `parse_tei` 同構：解析器只走 `<body>`**' % off_body)
    # 🚨 這一道是答案。
    probe('JATS 那一支沒有同樣的落差',
          not jats.get('reportsWithTablesButNoTableSection'),
          '🚨 JATS：原始檔 %s 張表 → sections %s 個表格節；'
          '**原始檔有表卻一個表格節都沒有的 %d 篇：%s**；'
          '⚠️ 有的話就是 `parse_jats` 也有缺口，🚨 而 `D17` 沒有涵蓋它'
          % (jats.get('rawTables'), jats.get('sectionTables'),
             len(jats.get('reportsWithTablesButNoTableSection') or []),
             jats.get('reportsWithTablesButNoTableSection') or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'jats-table-parity',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'question': ('第 611 輪：JATS 26 篇只有 20 篇有表格節。'
                     '⚠️ 那 6 篇是論文本來沒表，還是 `parse_jats` 也漏了？'),
        'summary': summary,
        'tableWrapPlacement': placement,
        'rows': sorted(rows, key=lambda r: (r['sourceType'], r['report'])),
        'controlDesign': (
            '🚨 本支的關鍵是控制：若這套方法在 **TEI** 那邊'
            '看不到第 611／612 輪已證的缺陷，'
            '**🚫 它在 JATS 上說「沒事」就不可信。**'),
        'methodLimit': (
            '⚠️ 本支數的是**標籤出現次數**，🚫 不是「表格內容有沒有被保留」——'
            '🚨 一個表格節可能只留了標題而沒有內容。'
            '✅ 又：JATS 的 `<table-wrap>` 與 TEI 的 `<figure type="table">` '
            '不必然一一對應，故**跨來源的絕對數不可直接相比**，'
            '🚫 本支只比**同一來源內**的原始檔與 sections。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n694 原始檔的表 vs sections 的表格節 ===')
    for source, info in sorted(summary.items()):
        print('   %-18s 篇 %d（可比 %d）｜原始表 %d → 表格節 %d｜'
              '有表卻無節的 %d 篇'
              % (source, info['reports'], info['comparable'],
                 info['rawTables'], info['sectionTables'],
                 len(info['reportsWithTablesButNoTableSection'])))
        gap = info['reportsWithTablesButNoTableSection']
        if gap:
            print('      %s' % gap)
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
