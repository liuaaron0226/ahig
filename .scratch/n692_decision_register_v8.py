# -*- coding: utf-8 -*-
"""**決策登記簿 v8——把第 688–691 輪四支一起掛入。**（第 692 輪）

## ✅ 承接 v7（26 項），🚫 不改寫它

⚠️ 本室說過「不每輪都出一版登記簿，那是噪音」，✅ 故累到四支才做一次：

| 憑證 | 掛到 |
|---|---|
| n688（D25 工作清單：98 項／50 組） | `D25` |
| n689（定位點形狀：23／98 指到表） | `D25` |
| n690（表格指標 × 酬載：12 項卡在 D17） | `D25`、`D17` |
| n691（兩個 12 不是同一個 12） | `D17` |

## 🚫 本版不新增決策、不改任何清冊與契約、不送外部請求
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
OUT = HERE / 'n692_decision_register_v8.json'
V7 = HERE / 'n687_decision_register_v7.json'

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
    v7 = json.loads(V7.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v7['items']}

    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince687', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)
        evidence = str(item['evidence'])
        if source not in evidence:
            item['evidence'] = evidence + '；' + source

    attach('D25', '✅ 落地工作清單：在範圍內項數／工作組數／無定位點項數',
           [cite('n688_d25_worklist.json', 'inScopeItems'),
            cite('n688_d25_worklist.json', 'workGroups'),
            cite('n688_d25_worklist.json', 'itemsWithoutLocator')],
           'n688_d25_worklist.json')
    attach('D25', '⚠️ 定位點形狀（指到表／只有段落）',
           cite('n689_locator_yield_shape.json', 'inScopeByShape'),
           'n689_locator_yield_shape.json')
    attach('D25', '🚨 建議的落地順序（第 3 層卡在 D17）',
           cite('n690_table_items_vs_payload.json', 'suggestedOrder'),
           'n690_table_items_vs_payload.json')
    attach('D17', '🚨 卡在本決策的在範圍內項數（GROBID ＋ 表格指標）',
           cite('n690_table_items_vs_payload.json',
                'tablePointerBySource', 'grobid-tei'),
           'n690_table_items_vs_payload.json')
    attach('D17', '⚠️ 「12 張結局表」與「12 項卡住的項目」**不是同一批**',
           {'兩邊都有的篇': cite('n691_two_twelves.json', 'reportsInBoth'),
            '只有表格那邊': cite('n691_two_twelves.json',
                                 'reportsOnlyWithOutcomeTables'),
            '只有項目那邊': cite('n691_two_twelves.json',
                                 'reportsOnlyWithInScopeTableItems')},
           'n691_two_twelves.json')

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v7 的全部登記（必觸發之正對照）',
          len(items) == 26,
          '🚨 承接 %d 項；⚠️ 少接一項就是把待裁定弄丟了' % len(items))
    probe('每一個新引用都取得到值（必觸發）',
          all(c['value'] is not None for c in CITATIONS),
          '🚨 引用 %d 筆，取不到值的：%s；⚠️ 取不到就代表登記簿與憑證脫節'
          % (len(CITATIONS),
             [c['path'] for c in CITATIONS if c['value'] is None] or '無'))

    def evidence_resolves(item):
        parts = str(item['evidence']).replace('；', ';').split(';')
        return all((HERE / part.split('→')[0].strip()).exists()
                   for part in parts if part.strip())

    dangling = [item['id'] for item in merged if not evidence_resolves(item)]
    probe('每一項的**每一個**證據檔都存在（必觸發）',
          not dangling,
          '🚨 檢查 %d 項；有指不到檔的：%s；⚠️ 指到不存在的檔就是空頭支票'
          % (len(merged), dangling or '無'))

    promised = {'n688_d25_worklist.json', 'n689_locator_yield_shape.json',
                'n690_table_items_vs_payload.json', 'n691_two_twelves.json'}
    landed = {c['from'] for c in CITATIONS}
    probe('第 688–691 輪那四支都掛進去了',
          promised <= landed,
          '🚨 應掛 %d 支，未掛入的：%s；⚠️ 本室的完成定義：任何漏項＝未完成'
          % (len(promised), sorted(promised - landed) or '無'))
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s；⚠️ 這些不決定，A 系列過不了'
          % (len(blockers), blockers))

    doc = {
        'schemaVersion': 8,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n687_decision_register_v7.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '✅ 累到四支才改版（🚫 不每輪出一版）：'
            'n688／n689／n690 → `D25`，n690／n691 → `D17`。'
            '🚫 本版不新增決策。'),
        'counts': {'total': len(merged),
                   'open': sum(1 for i in merged if i['status'] == 'open')},
        'decisionsUpdatedThisRound': updated,
        'openByBlocking': dict(by_blocking),
        'items': merged,
        'citations': CITATIONS,
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n692 決策登記簿 v8 ===')
    print('   合計 %d 項（open %d）｜本版掛上新證據：%s'
          % (len(merged), doc['counts']['open'], updated))
    for did in updated:
        print('   %s：' % did)
        for row in items[did]['newEvidenceSince687']:
            print('      %s ＝ %s'
                  % (row['label'], json.dumps(row['value'],
                                              ensure_ascii=False)[:150]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
