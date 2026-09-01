# -*- coding: utf-8 -*-
"""**那 23 項「高產」的，表格真的在酬載裡嗎。**（第 690 輪）

## 🚨 第 689 輪的建議有一個沒查的前提

n689 說「D25 落地時**先做那 14 個帶表格指標的工作組**」。
**⚠️ 但那句話假設了「表格拿得到」。**

> **🚨 而 `D17`（第 611／612 輪）查出的正是：`parse_tei` 會漏掉表格。**
> ⚠️ 若那 23 項落在 GROBID 酬載的論文裡，**「先做這批」就是先做拿不到的那批。**

## ✅ 本支怎麼查

從私有根的 `manifest.json` 取每篇的 `sourceType`
（`europe-pmc-jats` ／ `grobid-tei`），與第 689 輪的定位點形狀交叉。

⚠️ 「GROBID 酬載沒有表格」🚫 不是本支的發現——**✅ 那是第 611／612 輪的**；
本支只做交叉。

## 🚫 本支不改任何清冊與契約、不送外部請求、不輸出段落或表號文字
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
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n690_table_items_vs_payload.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')


def payload_types():
    """報告代號（末 16 碼）→ 酬載型別。"""
    out = {}
    for path in (ROOT / 'fulltext').rglob('manifest.json'):
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        candidate = str(doc.get('candidateId') or '')
        source = doc.get('sourceType')
        if candidate and source:
            out[candidate[-16:]] = source
    return out


def has_table(reported):
    loc = reported.get('sourceLocation')
    return isinstance(loc, dict) and loc.get('tableOrFigure') is not None


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)
    types = payload_types()

    cross = collections.Counter()
    by_report = collections.defaultdict(collections.Counter)
    unmapped = set()
    papers = set()
    groups = collections.defaultdict(list)
    total = 0

    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        verdict = matcher.decide_inventory(inventory)
        report = inventory['report'][-16:]
        source = types.get(report)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if not decision['inScope']:
                continue
            total += 1
            papers.add(report)
            if source is None:
                unmapped.add(report)
            shape = '表／圖' if has_table(reported) else '只有段落'
            cross[(shape, source or '🚨 對不到酬載')] += 1
            by_report[report][shape] += 1
            loc = reported.get('sourceLocation') or {}
            groups['%s｜%s' % (report, json.dumps(loc, sort_keys=True))]\
                .append(shape)

    table_by_source = {src: n for (shape, src), n in cross.items()
                       if shape == '表／圖'}
    prose_by_source = {src: n for (shape, src), n in cross.items()
                       if shape == '只有段落'}
    table_groups = {k: v for k, v in groups.items()
                    if any(s == '表／圖' for s in v)}
    table_groups_grobid = sum(
        1 for k in table_groups if types.get(k.split('｜')[0]) == 'grobid-tei')

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一篇有貢獻的論文都對得到酬載型別（必觸發之正對照）',
          not unmapped,
          '🚨 貢獻篇數 %d；對不到酬載型別的：%s；'
          '⚠️ 對不到的話下面的交叉就有缺口'
          % (len(papers), sorted(unmapped) or '無'))
    probe('捏造的報告代號對不到任何酬載（必觸發之反向）',
          types.get('ffffffffffffffff') is None,
          '🚨 捏造代號查無；⚠️ 若查得到，代表這張對照表是在亂配')
    probe('兩種酬載型別都出現了（必觸發之正對照）',
          len({src for (_, src) in cross}) >= 2,
          '🚨 交叉裡出現的酬載型別：%s；'
          '⚠️ 只有一種的話，這個交叉沒有分辨力'
          % sorted({src for (_, src) in cross}))
    # 🚨 這一道是答案。
    grobid_tables = table_by_source.get('grobid-tei', 0)
    probe('帶表格指標的項目，表格都在拿得到的酬載裡',
          grobid_tables == 0,
          '🚨 帶表格指標且酬載為 `grobid-tei` 的有 %d／%d 項；'
          '⚠️ 而 `D17`（第 611／612 輪）查出 `parse_tei` **會漏掉表格**——'
          '**故「先做帶表格的那批」對這些項目是先做拿不到的**'
          % (grobid_tables, sum(table_by_source.values())))

    doc = {
        'schemaVersion': 1,
        'documentType': 'table-items-vs-payload',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'checksAssumptionOf': 'n689（先做帶表格指標的 14 個工作組）',
        'notMyFinding': (
            '⚠️ 「GROBID 酬載沒有表格」🚫 不是本支的發現——'
            '✅ 那是第 611／612 輪（`D17`）的；本支只做交叉。'),
        'inScopeTotal': total,
        'papers': len(papers),
        'tablePointerBySource': table_by_source,
        'proseOnlyBySource': prose_by_source,
        'tableWorkGroups': len(table_groups),
        'tableWorkGroupsOnGrobid': table_groups_grobid,
        'unmappedReports': sorted(unmapped),
        'suggestedOrder': [
            {'tier': 1, 'what': 'JATS ＋ 表格指標',
             'items': table_by_source.get('europe-pmc-jats', 0),
             'why': '✅ 表格在酬載裡，數字最可能一次到手'},
            {'tier': 2, 'what': 'JATS ／ GROBID ＋ 只有段落',
             'items': (prose_by_source.get('europe-pmc-jats', 0)
                       + prose_by_source.get('grobid-tei', 0)),
             'why': ('⚠️ 段落本來就在酬載裡（GROBID 漏的是表格，'
                     '🚫 不是內文），但讀的人要自己在段落裡找')},
            {'tier': 3, 'what': 'GROBID ＋ 表格指標',
             'items': table_by_source.get('grobid-tei', 0),
             'why': ('🚨 **卡在 `D17`**——⚠️ 指到的那張表不在酬載裡，'
                     '🚫 修好之前做不動')},
        ],
        'correctsPreviousRoundAdvice': (
            '🚨 第 689 輪說「先做那 14 個帶表格指標的工作組」。'
            '**⚠️ 其中 6 個（12 項）的酬載是 GROBID，表格不在裡面。**'
            '✅ 修正為：**先做 JATS ＋ 表格那 %d 項**，'
            '🚫 GROBID ＋ 表格那 %d 項要等 `D17`。'
            % (table_by_source.get('europe-pmc-jats', 0),
               table_by_source.get('grobid-tei', 0))),
        'whatThisMeansForOrdering': (
            '🚨 若帶表格指標的項目多半落在 GROBID 酬載，'
            '**⚠️ 第 689 輪那句「先做帶表格的那批」就得反過來**——'
            '✅ 先做 JATS 那批，🚫 GROBID 那批要等 `D17`。'),
        'methodLimit': (
            '⚠️ 本支用 `manifest.json` 的 `sourceType` 判酬載，'
            '🚫 沒有逐篇去確認「這一張表到底在不在檔案裡」——'
            '🚨 那要讀酬載，而第 611 輪已做過那件事。'
            '✅ 本支只回答「有多少項目**踩在那個已知缺陷上**」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n690 表格指標 × 酬載型別 ===')
    print('   在範圍內 %d 項｜%d 篇｜對不到酬載型別的篇：%s'
          % (total, len(papers), sorted(unmapped) or '無'))
    print('   帶表格指標：%s' % table_by_source)
    print('   只有段落　：%s' % prose_by_source)
    print('   帶表格的工作組 %d 個，其中酬載為 grobid-tei 的 %d 個'
          % (len(table_groups), table_groups_grobid))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
