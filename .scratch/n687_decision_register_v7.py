# -*- coding: utf-8 -*-
"""**決策登記簿 v7——把第 685／686 輪掛進 D25 與 D16。**（第 687 輪）

## ✅ 承接 v6（26 項），🚫 不改寫它

⚠️ 本室在第 685 輪的憑證裡寫過「下一版登記簿會把本支掛進 D25」；
🚨 而第 686 輪那份更正**改動了 D16 的標題數字**。

> **⚠️ 兩筆一起清，🚫 不累積——第 673／674 輪剛示範過，
> 沒被登記的發現只靠「有人提過那一輪」撐著。**

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
OUT = HERE / 'n687_decision_register_v7.json'
V6 = HERE / 'n684_decision_register_v6.json'

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
    v6 = json.loads(V6.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v6['items']}

    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince684', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)
        evidence = str(item['evidence'])
        if source not in evidence:
            item['evidence'] = evidence + '；' + source

    attach('D25',
           '✅ D25 產出物要踩的規則，已證明會亮的條數（21 條全數）',
           len(cite('n685_all_d25_rules_fire.json', 'provenToFire') or []),
           'n685_all_d25_rules_fire.json')
    attach('D25', '⚠️ 本室無策略而仍未觀測的條數',
           len(cite('n685_all_d25_rules_fire.json', 'noStrategy') or []),
           'n685_all_d25_rules_fire.json')
    attach('D16',
           '🚨 同一條線的兩版收成一筆之後，方向分佈（原為 3／2／1）',
           cite('n686_p3_chained_pair_errata.json',
                'afterCollapsing', 'countsByDirection'),
           'n686_p3_chained_pair_errata.json')
    attach('D16', '⚠️ 原文即不存在的檢索截止日（照原文記，🚫 未更正）',
           cite('n686_p3_chained_pair_errata.json',
                'impossibleDatesAsWritten'),
           'n686_p3_chained_pair_errata.json')

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v6 的全部登記（必觸發之正對照）',
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

    promised = {'n685_all_d25_rules_fire.json',
                'n686_p3_chained_pair_errata.json'}
    landed = {c['from'] for c in CITATIONS}
    probe('第 685／686 輪該掛進去的，都掛進去了',
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
        'schemaVersion': 7,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n684_decision_register_v6.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '✅ 當輪清掉兩筆歸屬：n685 → `D25`（21／21 證明會亮）、'
            'n686 → `D16`（同線兩版收成一筆後方向由 3／2／1 變 2／2／1）。'
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

    print('=== n687 決策登記簿 v7 ===')
    print('   合計 %d 項（open %d）｜本版掛上新證據：%s'
          % (len(merged), doc['counts']['open'], updated))
    for did in updated:
        print('   %s：' % did)
        for row in items[did]['newEvidenceSince684']:
            print('      %s ＝ %s' % (row['label'], row['value']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
