# -*- coding: utf-8 -*-
"""**決策登記簿 v9——新增 D27：`parse_jats` 也漏表格。**（第 695 輪）

## ✅ 承接 v8（26 項），🚫 不改寫它

⚠️ 本室的節制是「附掛證據可以累積幾輪再改版」，
**🚨 但新的缺陷不累積——第 680 輪的 D26 就是當輪登記的。**

## 🚨 這一件為什麼是新的

`D17` 講的是 `parse_tei` 漏掉 `<figure type="table">`。
**⚠️ 而第 694 輪查出 `parse_jats` 也有同構的缺口**：
PMC 把表格放在 `<floats-group>`（`<body>` 的兄弟節點），解析器只走 `<body>`。

## 🚫 本版不改任何清冊與契約、不送外部請求
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
OUT = HERE / 'n695_decision_register_v9.json'
V8 = HERE / 'n692_decision_register_v8.json'

CITATIONS = []


def cite(filename, *keys):
    path = HERE / filename
    entry = {'from': filename, 'path': ' → '.join(str(k) for k in keys)}
    try:
        node = json.loads(path.read_text(encoding='utf-8'))
        for key in keys:
            node = node[key]
    except (OSError, KeyError, IndexError, TypeError, ValueError):
        node = None
    entry['value'] = node
    CITATIONS.append(entry)
    return node


def main():
    v8 = json.loads(V8.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v8['items']}

    jats = cite('n694_jats_table_parity.json', 'summary', 'europe-pmc-jats')
    placement = cite('n694_jats_table_parity.json', 'tableWrapPlacement')
    affected = (jats or {}).get('reportsWithTablesButNoTableSection') or []
    lost = (jats or {}).get('rawTables', 0) - (jats or {}).get(
        'sectionTables', 0)

    new_items = [{
        'id': 'D27', 'round': 694, 'status': 'open',
        'blocks': '酬載品質',
        'ask': '要不要一併修 `parse_jats`？（它也漏表格，成因與 `parse_tei` 同構）',
        'evidence': 'n694_jats_table_parity.json',
        'recommend': (
            '⚠️ 建議與 `D17` **一起裁**，🚫 不要分兩次。'
            '🚨 實測：JATS 原始檔 %s 張表 → sections 只有 %s 個表格節（少 %s 張）；'
            '**其中 %d 篇原始檔有表卻一個表格節都沒有**：%s。'
            '✅ 根因與 `D17` 同構——PMC 把表格放在 `<floats-group>`'
            '（`<body>` 的兄弟節點），而解析器只走 `<body>`；'
            '🚨 對照篇的 `<table-wrap>` 全在 `<body>` 裡，'
            '**故不是「那幾篇沒有表」。**'
            '⚠️ 而修它同樣會改變雜湊（與 `D17` 的 `fixMakesA1Harder` 同一個代價）。'
            % ((jats or {}).get('rawTables'), (jats or {}).get('sectionTables'),
               lost, len(affected), affected)),
        'notADuplicateOf': (
            '🚨 `D17` 只涵蓋 `parse_tei`（GROBID 那 15 篇）。'
            '⚠️ 本項是 **`parse_jats`**（Europe PMC 那 26 篇）——'
            '**✅ 兩支不同的程式、不同的論文，只是病因同構。**'),
    }]

    merged = list(items.values()) + new_items
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v8 的全部登記（必觸發之正對照）',
          len(items) == 26,
          '🚨 承接 %d 項｜新增 %d 項｜合計 %d 項'
          % (len(items), len(new_items), len(merged)))
    probe('每一個新引用都取得到值（必觸發）',
          all(c['value'] is not None for c in CITATIONS),
          '🚨 引用 %d 筆，取不到值的：%s'
          % (len(CITATIONS),
             [c['path'] for c in CITATIONS if c['value'] is None] or '無'))

    def evidence_resolves(item):
        parts = str(item['evidence']).replace('；', ';').split(';')
        return all((HERE / part.split('→')[0].strip()).exists()
                   for part in parts if part.strip())

    dangling = [item['id'] for item in merged if not evidence_resolves(item)]
    probe('每一項的每一個證據檔都存在（必觸發）',
          not dangling,
          '🚨 檢查 %d 項；有指不到檔的：%s' % (len(merged), dangling or '無'))
    probe('新增項聲明了它與最近既有項的關係（必觸發之反向）',
          all(item.get('notADuplicateOf') for item in new_items),
          '🚨 新增 %d 項，未聲明者：%s'
          % (len(new_items),
             [i['id'] for i in new_items
              if not i.get('notADuplicateOf')] or '無'))
    probe('新增項的證據裡真的有「對照篇在 body 裡」那一格（必觸發之反向）',
          any(v.get('isControl') for v in (placement or {}).values()),
          '🚨 位置證據：%s；'
          '⚠️ 沒有對照篇的話，「那幾篇的表不在 body」就沒有比較基準'
          % json.dumps(placement, ensure_ascii=False)[:220])
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s' % (len(blockers), blockers))

    doc = {
        'schemaVersion': 9,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n692_decision_register_v8.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '✅ 當輪登記 `D27`（`parse_jats` 也漏表格）——'
            '⚠️ 附掛證據可以累積，🚨 **新的缺陷不累積**。'),
        'counts': {'total': len(merged),
                   'open': sum(1 for i in merged if i['status'] == 'open')},
        'openByBlocking': dict(by_blocking),
        'items': merged,
        'citations': CITATIONS,
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n695 決策登記簿 v9 ===')
    print('   合計 %d 項（open %d）' % (len(merged), doc['counts']['open']))
    for item in new_items:
        print('   %s 阻擋 %s' % (item['id'], item['blocks']))
        print('      問：%s' % item['ask'])
        print('      建議：%s' % item['recommend'])
        print('      不是重複：%s' % item['notADuplicateOf'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
