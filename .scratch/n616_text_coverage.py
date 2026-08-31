# -*- coding: utf-8 -*-
"""**第三個面向：讀的人少看了多少字。**（第 616 輪）

## 🚨 把「跳過 225 個 figure」換成一個看得懂的數

第 612 輪算的是**元素個數**；⚠️ 而元素個數不告訴人「少看了多少」。
**✅ 本支比 TEI body 的全部文字與讀者拿到的 sections 內容，量出差額。**

## ⚠️ 這個差額不全是缺陷

🚨 圖說（figure caption）本來就不一定要進正文；
**✅ 但表格內容是資料，而它也在這個差額裡。**
⚠️ 故本支把差額**分開歸屬**：`figure[type=table]` 與其他 figure、note。

## 🚫 本支不改任何東西
"""
import collections
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402


def local(tag):
    return tag.rsplit('}', 1)[-1]


def text_of(node):
    return ' '.join(''.join(node.itertext()).split())


OUT = Path(__file__).resolve().parent / 'n616_text_coverage.json'


def main():
    rows, totals = [], collections.Counter()
    for manifest in sorted((ROOT / 'fulltext').rglob('manifest.json')):
        doc = json.loads(manifest.read_text(encoding='utf-8'))
        source = doc.get('sourceType')
        if source not in ('grobid-tei', 'europe-pmc-jats'):
            continue
        # 🚨 對照組：⚠️ 沒有 JATS 那一邊的數字，「85%」不知道算不算低。
        tei_path = manifest.parent / (doc.get('teiFile')
                                      or doc.get('rawFile') or '')
        sec_path = manifest.parent / (doc.get('sectionsFile') or '')
        if not tei_path.is_file() or not sec_path.is_file():
            continue
        try:
            body = next(n for n in ET.parse(tei_path).getroot().iter()
                        if local(n.tag) == 'body')
        except (ET.ParseError, StopIteration):
            continue
        body_chars = len(text_of(body))
        payload = json.loads(sec_path.read_text(encoding='utf-8'))
        payload_chars = len(payload.get('content') or '')

        table_chars = sum(len(text_of(c)) for c in body
                          if local(c.tag) == 'figure'
                          and (c.get('type') or '') == 'table')
        other_fig = sum(len(text_of(c)) for c in body
                        if local(c.tag) == 'figure'
                        and (c.get('type') or '') != 'table')
        note_chars = sum(len(text_of(c)) for c in body
                         if local(c.tag) == 'note')

        report = doc['candidateId'][-16:]
        share = round(100 * payload_chars / body_chars) if body_chars else 0
        rows.append({'report': report, 'sourceType': source,
                     'bodyChars': body_chars,
                     'payloadChars': payload_chars, 'coveragePct': share,
                     'tableChars': table_chars, 'otherFigureChars': other_fig,
                     'noteChars': note_chars})
        totals[source + ':body'] += body_chars
        totals[source + ':payload'] += payload_chars
        totals['body'] += body_chars
        totals['payload'] += payload_chars
        totals['table'] += table_chars
        totals['otherFigure'] += other_fig
        totals['note'] += note_chars

    tei_rows = [r for r in rows if r['sourceType'] == 'grobid-tei']
    jats_rows = [r for r in rows if r['sourceType'] == 'europe-pmc-jats']
    def share(items):
        b = sum(r['bodyChars'] for r in items); p = sum(r['payloadChars'] for r in items)
        return round(100 * p / b) if b else 0
    tei_share, jats_share = share(tei_rows), share(jats_rows)
    worst = min(tei_rows, key=lambda r: r['coveragePct']) if tei_rows else None
    overall = (round(100 * totals['payload'] / totals['body'])
               if totals['body'] else 0)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩種來源都量到了（必觸發）', len(tei_rows) == 15 and len(jats_rows) == 26,
          '🚨 少一邊就沒有對照；實得 TEI %d 篇、JATS %d 篇'
          % (len(tei_rows), len(jats_rows)))
    probe('15 篇 TEI 都量到了（必觸發）', len(tei_rows) == 15,
          '🚨 少一篇就低估了差額；實得 %d 篇' % len(tei_rows))
    probe('讀者拿到的字數不多於原文（必觸發）',
          all(r['payloadChars'] <= r['bodyChars'] for r in rows),
          '🚨 若有超過，代表本支比錯了東西')
    # 🚨 必觸發之反向：⚠️ 表格文字必須真的佔一部分，否則「表格被丟掉」無關痛癢。
    probe('表格文字確實佔可觀比例（必觸發之反向）',
          totals['table'] > 0,
          '✅ 表格文字合計 %d 字，占被丟掉總量的 %d%%；🚨 若為零，'
          '那 50 張表就只是空殼'
          % (totals['table'],
             round(100 * totals['table']
                   / max(totals['table'] + totals['otherFigure']
                         + totals['note'], 1))))
    # 🚨 這一道會紅。
    probe('讀者看到了原文的全部',
          tei_share >= 99,
          '🚨 TEI 覆蓋率 %d%%，而 JATS 對照是 %d%%——⚠️ 少的 %d 字裡，表格占 %d、'
          '其他圖說占 %d、註腳占 %d；最低的一篇只有 %d%%（%s）'
          % (tei_share, jats_share, totals['grobid-tei:body'] - totals['grobid-tei:payload'], totals['table'],
             totals['otherFigure'], totals['note'],
             worst['coveragePct'] if worst else 0,
             worst['report'] if worst else '—'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'text-coverage',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'reports': len(rows),
        'totals': dict(totals),
        'coverageBySource': {'grobid-tei': tei_share, 'europe-pmc-jats': jats_share},
        'rows': sorted(rows, key=lambda r: r['coveragePct']),
        'notAllOfItIsADefect': (
            '⚠️ 圖說本來就不一定要進正文；'
            '✅ 但**表格內容是資料**，而它也在這個差額裡——'
            '🚨 故本支把差額分開歸屬。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n616 讀的人少看了多少 ===')
    print('   ✅ 覆蓋率：GROBID %d%%｜JATS %d%%（對照）' % (tei_share, jats_share))
    print('   少掉的部分：表格 %d 字｜其他圖說 %d 字｜註腳 %d 字'
          % (totals['table'], totals['otherFigure'], totals['note']))
    print('   覆蓋率最低的三篇：')
    for row in sorted(rows, key=lambda r: r['coveragePct'])[:3]:
        print('      %s｜%d%%（原文 %d／拿到 %d；表格 %d 字）'
              % (row['report'], row['coveragePct'], row['bodyChars'],
                 row['payloadChars'], row['tableChars']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
