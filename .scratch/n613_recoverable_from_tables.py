# -*- coding: utf-8 -*-
"""**修好之後救得回多少：那 50 張表裡有多少是結局表。**（第 613 輪）

## 🚨 D17 要能裁，得先知道它值多少

第 612 輪指出修 `parse_tei` 會製造新的版本分歧（A1 更難）。
**⚠️ 而「值不值得」取決於一件沒人算過的事：那些表裡到底有沒有我們要的結局。**

## ✅ 做法：本室**唯讀**地自己解析那些被跳過的 figure

🚫 不改解析器、🚫 不重新產生任何 sections——
**✅ 只把 `<figure type="table">` 的文字取出來，看裡面有沒有契約結局的詞彙與數字。**

## 🚨 而這一支只能說「看起來像」

⚠️ 表格文字被 GROBID 攤平之後很難判讀；
**🚫 故本支給的是「該去看的表」，不是「可以直接抽的結局」。**
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

OUT = Path(__file__).resolve().parent / 'n613_recoverable_from_tables.json'
ZERO = Path(__file__).resolve().parent / 'n586_zero_contribution_census.json'

# ⚠️ 詞彙取自契約的結局，🚫 不是本室另想的。
VOCAB = {
    'tt-completion-time': r'time[- ]trial|completion time',
    'time-to-exhaustion': r'time to exhaustion|exercise capacity',
    'exogenous-cho-oxidation-peak': r'exogenous',
    'muscle-glycogen-post-exercise': r'glycogen',
    'gi-symptom': r'nausea|bloat|cramp|fullness|reflux|flatulence'
                  r'|gastrointestinal|GI ',
}
NUMBER = re.compile(r'\d+\.\d+|\d+\s*(?:±|\+/-)|\d+\s*\(\s*\d+\s*\)')


def local(tag):
    return tag.rsplit('}', 1)[-1]


def table_text(node):
    return ' '.join(''.join(node.itertext()).split())


def main():
    zero_reports = set()
    if ZERO.exists():
        census = json.loads(ZERO.read_text(encoding='utf-8'))
        zero_reports = {r['report'] for r in census.get('zeroRows', [])}

    rows, totals = [], collections.Counter()
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
        tables = [c for c in body
                  if local(c.tag) == 'figure' and (c.get('type') or '') == 'table']
        hits = collections.Counter()
        outcome_tables = 0
        for table in tables:
            text = table_text(table)
            if not NUMBER.search(text):
                continue
            matched = [name for name, pattern in VOCAB.items()
                       if re.search(pattern, text, re.I)]
            if matched:
                outcome_tables += 1
                for name in matched:
                    hits[name] += 1
        report = doc['candidateId'][-16:]
        totals['tables'] += len(tables)
        totals['outcomeTables'] += outcome_tables
        for name, count in hits.items():
            totals['vocab:' + name] += count
        rows.append({'report': report, 'tables': len(tables),
                     'tablesWithOutcomeTerms': outcome_tables,
                     'terms': dict(hits),
                     'contributesZeroInScope': report in zero_reports})

    zero_with_tables = [r for r in rows
                        if r['contributesZeroInScope']
                        and r['tablesWithOutcomeTerms']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('讀到了 15 篇的表格（必觸發）',
          len(rows) == 15 and totals['tables'] > 0,
          '🚨 少一篇就低估了代價；實得 %d 篇／%d 張表'
          % (len(rows), totals['tables']))
    # 🚨 必觸發之反向：⚠️ 詞彙要真的在某些表上命中，否則零命中沒有意義。
    probe('結局詞彙在表格裡確實命中（必觸發之反向）',
          totals['outcomeTables'] > 0,
          '✅ %d／%d 張表同時含數字與結局詞彙；🚨 若為零，'
          '代表這些表與結局無關——那樣 D17 就不值得修'
          % (totals['outcomeTables'], totals['tables']))
    # ⚠️ 不是每張表都該命中，否則詞彙太寬。
    probe('詞彙沒有寬到每張表都命中',
          totals['outcomeTables'] < totals['tables'],
          '⚠️ 實得 %d／%d；🚨 若全部命中，代表詞彙沒有分辨力'
          % (totals['outcomeTables'], totals['tables']))
    # 🚨 這一道會紅：⚠️ 目前貢獻為零的論文裡，有表格看起來帶著結局。
    probe('沒有「貢獻為零卻有結局表」的論文',
          not zero_with_tables,
          '🚨 實得 %d 篇：%s；⚠️ 它們現在被記為沒有可用結局，'
          '而它們的表裡有結局詞彙與數字——🚫 讀的人看不到那些表'
          % (len(zero_with_tables),
             [(r['report'], r['tablesWithOutcomeTerms']) for r in zero_with_tables]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'recoverable-from-tables',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'readOnly': '🚫 未改解析器、未重新產生任何 sections。',
        'reports': len(rows),
        'totals': dict(totals),
        'rows': rows,
        'zeroContributionWithOutcomeTables':
            [r['report'] for r in zero_with_tables],
        'whatThisCanSay': (
            '✅ 「該去看的表」有多少。'
            '🚫 不是「可以直接抽的結局」——⚠️ 表格文字被攤平後很難判讀。'),
        'whyItMattersForD17': (
            '🚨 第 612 輪說修 parse_tei 會製造新的版本分歧。'
            '⚠️ 而值不值得，取決於那些表裡有沒有我們要的結局——'
            '✅ 本支把那個數字算出來了。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n613 那些表裡有什麼 ===')
    print('   15 篇｜表格 %d 張｜✅ 同時含數字與結局詞彙者 %d 張'
          % (totals['tables'], totals['outcomeTables']))
    print('   詞彙命中：%s'
          % {k[6:]: v for k, v in totals.items() if k.startswith('vocab:')})
    print('   🚨 目前貢獻為零、卻有結局表的論文：%d 篇'
          % len(zero_with_tables))
    for row in sorted(rows, key=lambda r: -r['tablesWithOutcomeTerms'])[:6]:
        print('      %s｜表 %2d 張｜結局表 %d｜零貢獻 %s｜%s'
              % (row['report'], row['tables'], row['tablesWithOutcomeTerms'],
                 row['contributesZeroInScope'], row['terms']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
