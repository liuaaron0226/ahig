# -*- coding: utf-8 -*-
"""**決策登記簿 v13——把本室自己重複登記的 `D24` 併回 `D2`。**（第 707 輪）

## 🚨 這一版處理的是**本室自己造成的錯誤**

第 706 輪查出兩件事：

1. **`D24` 是重複登記**——`n585`（`D2` 的證據）早就有那條改名
   （`cycling-time-to-exhaustion-fixed-power` → `cycling-tte-fixed-intensity`）。
2. **`D24` 的前提也錯**——本室從**機械性突變**推出「同義字問題」，
   🚨 但 `n585` 是**讀過論文**後分類的：`298c` 與 `9a3b` 是 **`contract-gap`**
   （契約沒有滑雪類工具），🚫 不是同義字。

> **⚠️ 自己造成的錯誤不等批次。**

## ✅ 而還有一件 `n585` 早就寫著、登記簿卻沒有的事

> `n585`：「📮 故改名與『這兩筆算一個 study』是同一個決定，🚫 不可分開做。」

**🚨 那是 `D2`／`D3` 的連鎖——⚠️ 而登記簿兩邊都沒寫。**

## 🚫 本版不刪除任何決定（`D24` 改狀態、保留全文）、不送外部請求
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
OUT = HERE / 'n707_decision_register_v13.json'
V12 = HERE / 'n702_decision_register_v12.json'

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
    v12 = json.loads(V12.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v12['items']}

    coverage = cite('n706_d24_was_already_covered.json', 'errataCoverage')
    gaps = cite('n706_d24_was_already_covered.json', 'contractGapReports')
    renames = cite('n706_d24_was_already_covered.json', 'erratraRenameTable')

    # 🚨 `D24` 改狀態，🚫 不刪除——⚠️ 刪掉就看不見本室曾經錯過。
    d24 = items['D24']
    d24['status'] = 'merged-into-D2'
    d24['mergedBecause'] = (
        '🚨 **本室重複登記。** `n585`（`D2` 的證據）早就有那條改名'
        '（`cycling-time-to-exhaustion-fixed-power` → '
        '`cycling-tte-fixed-intensity`，`rename-safe`）。'
        '⚠️ 且本項的**前提也錯**：本室從機械性突變推出「同義字問題」，'
        '🚨 而 `n585` 讀過論文後把 %s 分類為 `contract-gap`'
        '（契約沒有滑雪類工具）——**🚫 那不是同義字。**'
        '✅ 故本項併回 `D2`；🚫 條目保留，讓這個錯誤看得見。' % gaps)
    d24['evidence'] = str(d24['evidence']) + \
        '；n706_d24_was_already_covered.json'

    d2 = items['D2']
    d2.setdefault('newEvidenceSince702', []).append(
        {'label': '✅ 更正表的改名對照（`D24` 併入後由本項涵蓋）',
         'value': renames, 'from': 'n706_d24_was_already_covered.json'})
    d2.setdefault('newEvidenceSince702', []).append(
        {'label': '🚨 更正表對 `D24` 那三篇的分類',
         'value': coverage, 'from': 'n706_d24_was_already_covered.json'})
    d2['absorbed'] = '✅ 已併入 `D24`（第 707 輪）。'
    d2['evidence'] = str(d2['evidence']) + \
        '；n706_d24_was_already_covered.json'

    # 🚨 `n585` 早就寫著 D2／D3 是同一個決定——⚠️ 登記簿兩邊都沒寫。
    interlock = (
        '🚨 **`D2` 與 `D3` 是同一個決定，🚫 不可分開做。**'
        '⚠️ `n585` 原文：「rename-safe 會讓 `7a6ac1559c740fd6` 從'
        '「在範圍內 0 項」變回 9 項，而其中的肌肉肝醣正是 `n584` 那本'
        '博士論文 Study 2 的同一批 8 人。」'
        '✅ 這句話 `n585` 早就寫著——**⚠️ 而登記簿到第 707 輪才記上。**')
    for did in ('D2', 'D3'):
        items[did]['interlockWithErrata'] = interlock
        if 'n585_blocked_drafts_errata.json' not in str(items[did]['evidence']):
            items[did]['evidence'] = str(items[did]['evidence']) + \
                '；n585_blocked_drafts_errata.json'

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        if item['status'] == 'open':
            by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v12 的全部登記（必觸發之正對照）',
          len(items) == 27, '🚨 承接 %d 項' % len(items))
    probe('每一個新引用都取得到值（必觸發）',
          all(c['value'] is not None for c in CITATIONS),
          '🚨 引用 %d 筆，取不到值的：%s'
          % (len(CITATIONS),
             [c['path'] for c in CITATIONS if c['value'] is None] or '無'))
    probe('`D24` 只改狀態、🚫 沒有被刪掉（必觸發之反向）',
          'D24' in items and items['D24'].get('ask'),
          '🚨 D24 仍在簿子裡、狀態 `%s`、原問句保留：%s；'
          '⚠️ 刪掉就看不見本室曾經錯過'
          % (items['D24']['status'], bool(items['D24'].get('ask'))))
    probe('`D2`／`D3` 兩邊都寫了更正表的連鎖（必觸發之反向）',
          all('interlockWithErrata' in items[d] for d in ('D2', 'D3')),
          '🚨 有連鎖說明的：%s'
          % [d for d in ('D2', 'D3') if 'interlockWithErrata' in items[d]])
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s（`D24` 併入後少一項）'
          % (len(blockers), blockers))

    doc = {
        'schemaVersion': 13,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n702_decision_register_v12.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '🚨 處理**本室自己造成的錯誤**：`D24` 是重複登記、且前提有誤，'
            '✅ 併回 `D2`（🚫 條目保留）。'
            '⚠️ 並補上 `n585` 早就寫著、登記簿卻沒有的 `D2`／`D3` 連鎖。'),
        'counts': {'total': len(merged),
                   'open': sum(1 for i in merged if i['status'] == 'open'),
                   'mergedThisRound': ['D24']},
        'openByBlocking': dict(by_blocking),
        'items': merged,
        'citations': CITATIONS,
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n707 決策登記簿 v13 ===')
    print('   合計 %d 項（open %d）｜本版把 D24 併入 D2'
          % (len(merged), doc['counts']['open']))
    print('   D24 的處置：%s' % d24['mergedBecause'][:150])
    print('   D2／D3 的連鎖：%s' % interlock[:120])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
