# -*- coding: utf-8 -*-
"""**決策登記簿 v10——把 `D27` 的份量補上，免得它被讀得太重。**（第 698 輪）

## 🚨 為什麼這一次不等批次

⚠️ 本室的節制是「附掛證據可以累積幾輪再改版」。
**🚨 但第 697 輪查出的東西會改變 `D27` 讀起來的份量**——
✅ v9 的 D27 只寫了缺陷與修的代價，🚫 沒寫「修好能救回多少」。

> **⚠️ 而答案是：不多。**
> 那 4 篇裡 3 篇零貢獻，🚨 但可由「表格被削掉」解釋的被擋項目**只有 2 項**；
> **⚠️ 那 3 篇的零貢獻是「結局根本沒對上」，🚫 與表格無關。**

**✅ 讓一則只寫了成本、沒寫效益的登記留在簿子裡，會誤導裁定。**

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
OUT = HERE / 'n698_decision_register_v10.json'
V9 = HERE / 'n695_decision_register_v9.json'

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
    v9 = json.loads(V9.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v9['items']}

    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince695', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)
        evidence = str(item['evidence'])
        if source not in evidence:
            item['evidence'] = evidence + '；' + source

    in_scope = cite('n697_d27_consequences.json', 'inScopeFromAffected')
    zero = cite('n697_d27_consequences.json', 'zeroContributionAmongAffected')
    explicable = cite('n697_d27_consequences.json',
                      'tableExplicableBlockedItems')
    fidelity = cite('n696_table_section_fidelity.json', 'digitRatioMedian')

    attach('D27', '⚠️ 受影響 4 篇目前的在範圍內項數／其中零貢獻篇數',
           [in_scope, len(zero or [])], 'n697_d27_consequences.json')
    attach('D27', '🚨 **可由「表格被削掉」解釋的被擋項目數**（效益上限的線索）',
           explicable, 'n697_d27_consequences.json')
    attach('D27', '✅ 走得到的表格內容完整（數字保留率中位數）',
           fidelity, 'n696_table_section_fidelity.json')
    attach('D17', '✅ 走得到的表格內容完整（數字保留率中位數）——效益不必打折',
           fidelity, 'n696_table_section_fidelity.json')

    items['D27']['sizeNote'] = (
        '🚨 **本項的效益比 `D17` 小得多。**'
        '⚠️ 受影響 4 篇目前只貢獻 %s 項，其中 %d 篇零貢獻；'
        '🚨 但可由「表格被削掉」解釋的被擋項目**只有 %s 項**——'
        '**⚠️ 那 3 篇的零貢獻是「結局根本沒對上」，🚫 與表格無關。**'
        '✅ 故本室的「與 D17 一起裁」建議**維持**（同一支病、同一種代價），'
        '🚫 但**不要期待它救回可觀的證據**。'
        % (in_scope, len(zero or []), explicable))

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v9 的全部登記（必觸發之正對照）',
          len(items) == 27,
          '🚨 承接 %d 項；⚠️ 少接一項就是把待裁定弄丟了' % len(items))
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
    # 🚨 這一道是本版的重點：只寫成本沒寫效益的登記，會誤導裁定。
    probe('`D27` 已同時載明成本**與**效益',
          'sizeNote' in items['D27']
          and any('可由' in str(e.get('label'))
                  for e in items['D27'].get('newEvidenceSince695', [])),
          '🚨 D27 的份量說明：%s'
          % items['D27'].get('sizeNote', '🚨 缺')[:120])
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s' % (len(blockers), blockers))

    doc = {
        'schemaVersion': 10,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n695_decision_register_v9.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '✅ 不等批次就改版——🚨 因為 v9 的 `D27` 只寫了成本、沒寫效益，'
            '**⚠️ 而效益不大。讓那樣的登記留著會誤導裁定。**'),
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

    print('=== n698 決策登記簿 v10 ===')
    print('   合計 %d 項（open %d）｜本版更新：%s'
          % (len(merged), doc['counts']['open'], updated))
    print('   D27 的份量說明：')
    print('      %s' % items['D27']['sizeNote'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
