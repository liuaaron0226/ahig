# -*- coding: utf-8 -*-
"""**決策登記簿 v6——把第 681／682／683 輪掛進 D25 與 D26。**（第 684 輪）

## ✅ 這一版清的是本室在看板上欠的帳

第 681 與 682 輪都寫過「下一版登記簿會把本支掛進去」。
**🚨 而本室自己的完成定義寫著：任何漏項＝未完成。**

## 🚫 本版不新增決策

⚠️ 三支憑證談的都是**已登記**的兩件事：
`D25`（要不要抽數值、規格長什麼樣）與 `D26`（驗收會不會漏掉）。

## 🚫 本支不改任何清冊與契約、不送外部請求
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
OUT = HERE / 'n684_decision_register_v6.json'
V5 = HERE / 'n680_decision_register_v5.json'

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
    v5 = json.loads(V5.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v5['items']}

    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince680', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)
        evidence = str(item['evidence'])
        if source not in evidence:
            item['evidence'] = evidence + '；' + source

    attach('D26', '🚨 只跑一份 profile 會放過的負向對照數（兩份都跑為 0）',
           cite('n681_single_profile_leak.json', 'leakIfOnlyOneProfile'),
           'n681_single_profile_leak.json')
    attach('D26', '⚠️ 從未被任何對照組點亮的具名規則數',
           cite('n682_rules_never_fired.json', 'totals'),
           'n682_rules_never_fired.json')
    attach('D25', '🚨 從未被點亮、而 D25 產出物會踩到的規則',
           cite('n682_rules_never_fired.json', 'neverFiredOnD25Classes'),
           'n682_rules_never_fired.json')
    attach('D25', '✅ 本室已用突變證明會亮的規則（從「沒人看過」變「看過」）',
           cite('n683_prove_d25_rules_fire.json', 'provenToFire'),
           'n683_prove_d25_rules_fire.json')
    attach('D25', '🚨 對照組裡 `QuantitativeStudyResult` 的實例數',
           cite('n683_prove_d25_rules_fire.json', 'canaryClassInstances'),
           'n683_prove_d25_rules_fire.json')

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v5 的全部登記（必觸發之正對照）',
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

    # 🚨 這一道是本版的答案：看板上欠的那筆帳清了沒有。
    promised = {'n681_single_profile_leak.json',
                'n682_rules_never_fired.json',
                'n683_prove_d25_rules_fire.json'}
    landed = {c['from'] for c in CITATIONS}
    probe('第 681／682 輪在看板上承諾要掛進去的，都掛進去了',
          promised <= landed,
          '🚨 承諾 %d 支，未掛入的：%s；'
          '⚠️ 本室的完成定義寫著：任何漏項＝未完成'
          % (len(promised), sorted(promised - landed) or '無'))

    doc = {
        'schemaVersion': 6,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n680_decision_register_v5.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '✅ 清掉本室在第 681／682 輪看板上欠的帳：'
            '把那三支憑證掛進 `D25` 與 `D26` 的證據。'
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

    print('=== n684 決策登記簿 v6 ===')
    print('   合計 %d 項（open %d）｜本版掛上新證據：%s'
          % (len(merged), doc['counts']['open'], updated))
    for did in updated:
        print('   %s 的新證據：' % did)
        for row in items[did]['newEvidenceSince680']:
            print('      %s ＝ %s' % (row['label'], row['value']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
