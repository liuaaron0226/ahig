# -*- coding: utf-8 -*-
"""**決策登記簿 v15——把第 713–716 輪四支一起掛入。**（第 717 輪）

## ✅ 照本室自己訂的節制：累到四支才改版

| 憑證 | 掛到 |
|---|---|
| n713（跨篇劑量-反應矩陣） | `D25`、`D18` |
| n714（`D18` 那 18 篇的年代） | `D18` |
| n715（逐結局可行性計分表） | `D25` |
| n716（`D25` 試點規格） | `D25`、`D17` |

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
OUT = HERE / 'n717_decision_register_v15.json'
V14 = HERE / 'n712_decision_register_v14.json'

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
    v14 = json.loads(V14.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v14['items']}

    updated = []

    def attach(did, label, value, source):
        item = items[did]
        item.setdefault('newEvidenceSince712', []).append(
            {'label': label, 'value': value, 'from': source})
        if did not in updated:
            updated.append(did)
        evidence = str(item['evidence'])
        if source not in evidence:
            item['evidence'] = evidence + '；' + source

    matrix = cite('n713_dose_response_matrix.json', 'rows')
    bands_per_outcome = {r['outcome']: r['bandsWithAnyPaper']
                         for r in (matrix or [])}
    low_band = {r['outcome']: r['papersByBand']['low']
                for r in (matrix or [])}

    attach('D25', '⚠️ 各結局跨篇涵蓋幾個劑量帶（畫曲線至少要三個點）',
           bands_per_outcome, 'n713_dose_response_matrix.json')
    attach('D18', '🚨 各結局在 `low` 帶（10–29.9 g/h）的論文數',
           low_band, 'n713_dose_response_matrix.json')
    attach('D18', '⚠️ 那 18 篇的年份中位數／2000 年前篇數（對照：已取得為 2020）',
           [cite('n714_d18_era_profile.json', 'medianYear'),
            len(cite('n714_d18_era_profile.json', 'pre2000') or [])],
           'n714_d18_era_profile.json')
    attach('D25', '✅ 逐結局可行性（條件最完整者／最沒條件者）',
           [cite('n715_dose_response_scorecard.json', 'bestPositioned'),
            cite('n715_dose_response_scorecard.json', 'worstPositioned')],
           'n715_dose_response_scorecard.json')
    attach('D25', '✅ 試點規格：項數／篇數／工作組數',
           [cite('n716_d25_pilot_spec.json', 'items'),
            cite('n716_d25_pilot_spec.json', 'papers'),
            cite('n716_d25_pilot_spec.json', 'workGroups')],
           'n716_d25_pilot_spec.json')
    attach('D17', '🚨 連試點都會撞到：卡在本決策的試點工作組數',
           cite('n716_d25_pilot_spec.json', 'tier3GroupsBlockedByD17'),
           'n716_d25_pilot_spec.json')

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        if item['status'] == 'open':
            by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v14 的全部登記（必觸發之正對照）',
          len(items) == 27, '🚨 承接 %d 項' % len(items))
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

    promised = {'n713_dose_response_matrix.json',
                'n714_d18_era_profile.json',
                'n715_dose_response_scorecard.json',
                'n716_d25_pilot_spec.json'}
    landed = {c['from'] for c in CITATIONS}
    probe('第 713–716 輪那四支都掛進去了（必觸發之正對照）',
          promised <= landed,
          '🚨 應掛 %d 支，未掛入的：%s' % (len(promised),
                                          sorted(promised - landed) or '無'))
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s' % (len(blockers), blockers))

    doc = {
        'schemaVersion': 15,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n712_decision_register_v14.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '✅ 累到四支才改版（🚫 不每輪出一版）：'
            'n713／n715／n716 → `D25`；n713／n714 → `D18`；n716 → `D17`。'
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

    print('=== n717 決策登記簿 v15 ===')
    print('   合計 %d 項（open %d）｜本版更新：%s'
          % (len(merged), doc['counts']['open'], updated))
    for did in updated:
        print('   %s：' % did)
        for row in items[did]['newEvidenceSince712']:
            print('      %s ＝ %s'
                  % (row['label'],
                     json.dumps(row['value'], ensure_ascii=False)[:120]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
