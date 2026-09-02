# -*- coding: utf-8 -*-
"""**原始檔裡有的表，讀者實際引用到幾張。**（第 693 輪）

## 🚨 第 691 輪露出的缺口

`307c0dd5b141caed` 有 **8 張帶結局詞彙的表**，
⚠️ 但在範圍內指到表的項目只有 **4** 項。

> **🚨 那就要問：GROBID 那 15 篇的原始檔裡有 50 張表，
> 讀的人在清冊裡實際引用到幾個？**

## ✅ 為什麼這是 `D17` 需要的數字

⚠️ 目前對 D17 的效益描述是「那 12 項卡住的會解開」。
🚨 但若原始檔裡還有**從來沒被引用過**的表，
**✅ 修好之後多出來的不只是解開，還有「第一次看得見」。**

## ⚠️ 一個必須先講的限制

🚨 清冊的 `tableOrFigure` **表與圖不分**——⚠️ 引用到的可能是圖。
✅ 故本支拿它跟「表 ＋ 圖」的總數比，🚫 不假裝分得開。

## 🚫 本支不輸出任何表號或圖號文字、不改任何清冊、不送外部請求
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

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n693_uncited_tables_gap.json'
N612 = HERE / 'n612_parse_tei_root_cause.json'


def main():
    n612 = json.loads(N612.read_text(encoding='utf-8'))
    present = {row['report']: {'tables': row.get('tables') or 0,
                               'figures': row.get('figures') or 0}
               for row in n612['perReport']}

    cited = collections.defaultdict(set)
    items_with_pointer = collections.Counter()
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        report = inventory['report'][-16:]
        if report not in present:
            continue
        for reported in inventory['reportedOutcomes']:
            loc = reported.get('sourceLocation')
            if isinstance(loc, dict) and loc.get('tableOrFigure') is not None:
                cited[report].add(str(loc['tableOrFigure']))
                items_with_pointer[report] += 1

    rows = []
    for report, counts in sorted(present.items()):
        total = counts['tables'] + counts['figures']
        used = len(cited.get(report, ()))
        rows.append({
            'report': report,
            'tablesInSource': counts['tables'],
            'figuresInSource': counts['figures'],
            'distinctCited': used,
            'itemsCiting': items_with_pointer.get(report, 0),
            'neverCited': total - used,
        })

    total_tables = sum(r['tablesInSource'] for r in rows)
    total_figures = sum(r['figuresInSource'] for r in rows)
    total_cited = sum(r['distinctCited'] for r in rows)
    with_inventory = [r for r in rows if r['itemsCiting'] or
                      r['report'] in cited]

    # 🚨 比「84% 沒被引用」更硬的訊號：整篇一個表／圖都沒引用的那幾篇。
    zero_citing = sorted(r['report'] for r in rows
                         if r['distinctCited'] == 0)
    zero_with_tables = sorted(r['report'] for r in rows
                              if r['distinctCited'] == 0
                              and r['tablesInSource'] > 0)
    n613 = json.loads((HERE / 'n613_recoverable_from_tables.json')
                      .read_text(encoding='utf-8'))
    outcome_table_reports = {row['report'] for row in n613['rows']
                             if row.get('tablesWithOutcomeTerms')}
    outcome_but_silent = sorted(outcome_table_reports
                                & set(zero_citing))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('接得到第 612 輪那 15 篇與 50 張表（必觸發之正對照）',
          len(rows) == 15 and total_tables == 50,
          '🚨 %d 篇、表 %d 張、圖 %d 張；⚠️ 對不上就與第 612 輪不一致'
          % (len(rows), total_tables, total_figures))
    probe('捏造的報告代號沒有任何引用（必觸發之反向）',
          not cited.get('ffffffffffffffff'),
          '🚨 捏造代號查無引用；⚠️ 若查得到，代表比對是在亂配')
    probe('至少有一些引用可比（必觸發之正對照）',
          total_cited > 0,
          '🚨 清冊裡引用到的相異表／圖共 %d 個（來自 %d 篇）；'
          '⚠️ 若是 0，本支沒有可比的東西'
          % (total_cited, len(cited)))
    # 🚨 這一道是答案。
    probe('原始檔裡的表／圖都被引用到了',
          total_cited >= total_tables + total_figures,
          '🚨 原始檔共 %d 個表／圖，清冊只引用到 %d 個（%.0f%%）；'
          '⚠️ 其餘 %d 個**從來沒有被任何一項引用過**——'
          '**🚨 而讀的人本來就看不到它們**'
          % (total_tables + total_figures, total_cited,
             100.0 * total_cited / (total_tables + total_figures)
             if (total_tables + total_figures) else 0,
             total_tables + total_figures - total_cited))

    doc = {
        'schemaVersion': 1,
        'documentType': 'uncited-tables-gap',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'followsFrom': 'n691（那兩個 12 不是同一個 12）',
        'grobidReports': len(rows),
        'tablesInSource': total_tables,
        'figuresInSource': total_figures,
        'distinctCitedInInventories': total_cited,
        'neverCited': total_tables + total_figures - total_cited,
        'reportsWithAnyCitation': len(cited),
        'reportsCitingNothing': zero_citing,
        'reportsCitingNothingYetHavingTables': zero_with_tables,
        'outcomeTableReportsThatCiteNothing': outcome_but_silent,
        'rows': rows,
        'whyThisMattersForD17': (
            '⚠️ 目前對 `D17` 的效益描述是「那 12 項卡住的會解開」。'
            '🚨 但原始檔裡還有大量**從來沒被引用過**的表與圖——'
            '**✅ 修好之後多出來的不只是解開，還有「第一次看得見」。**'
            '🚫 本支不主張那些看得見之後一定有用。'),
        'methodLimit': (
            '🚨 清冊的 `tableOrFigure` **表與圖不分**——'
            '⚠️ 引用到的可能是圖，故本支拿它跟「表＋圖」的總數比，'
            '🚫 不假裝分得開。'
            '⚠️ 又：「沒被引用」🚫 不等於「有用」——'
            '**一篇論文本來就有很多與本題無關的圖表。**'
            '✅ 第 613 輪才是「那些表裡有沒有我們要的結局」那一題。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n693 原始檔的表／圖 vs 清冊引用到的 ===')
    print('   GROBID %d 篇｜原始檔表 %d 張、圖 %d 張｜清冊引用到相異 %d 個'
          % (len(rows), total_tables, total_figures, total_cited))
    print('   逐篇（原始表／原始圖／引用到／引用它的項數）：')
    for row in rows:
        print('      %s  %3d／%3d ／ 引用 %2d ／ 項 %2d'
              % (row['report'], row['tablesInSource'],
                 row['figuresInSource'], row['distinctCited'],
                 row['itemsCiting']))
    print('   🚨 整篇一個表／圖都沒引用的 %d 篇：%s'
          % (len(zero_citing), zero_citing))
    print('      其中原始檔有表的 %d 篇：%s'
          % (len(zero_with_tables), zero_with_tables))
    print('      🚨 而其中帶結局詞彙表的 %d 篇：%s'
          % (len(outcome_but_silent), outcome_but_silent))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
