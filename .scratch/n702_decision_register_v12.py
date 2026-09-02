# -*- coding: utf-8 -*-
"""**決策登記簿 v12——把 `D3` 與 `D24` 的連鎖寫進兩邊。**（第 702 輪）

## 🚨 為什麼又不等批次

⚠️ 本室的節制是「附掛證據可以累積」，
**🚨 但例外是：不掛會讓既有條目讀起來是錯的。**

`D24` 現在的建議只寫「回全文判定儀器名稱」，
**⚠️ 完全沒提「只修這一項會讓同一組受試者被算兩次」。**

> **🚨 第 701 輪算出來了：完全重疊，4 項。**
> 論文半在範圍內 `TTE 2 ／ 肌肝醣 2`；期刊半修好儀器名稱後也是 `TTE 2 ／ 肌肝醣 2`。

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
OUT = HERE / 'n702_decision_register_v12.json'
V11 = HERE / 'n700_decision_register_v11.json'

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
    v11 = json.loads(V11.read_text(encoding='utf-8'))
    items = {item['id']: dict(item) for item in v11['items']}

    at_risk = cite('n701_d3_d24_interlock.json', 'itemsAtRiskOfDoubleCount')
    overlap = cite('n701_d3_d24_interlock.json', 'overlappingOutcomes')
    source = 'n701_d3_d24_interlock.json'

    updated = []
    note = (
        '🚨 **`D3` 與 `D24` 連在一起，不能只做一邊。**'
        '⚠️ 論文半目前在範圍內 `TTE 2／肌肝醣 2`；'
        '而期刊半只要把儀器名稱對上契約，拿回的也正是 `TTE 2／肌肝醣 2`——'
        '**🚨 完全重疊，%s 項會被算兩次，而那是同一組受試者**'
        '（第 584 輪：6 個同群數值逐字相同）。'
        '⚠️ 反過來，只裁 `D3` 而不修 `D24`，期刊半仍是 0 項。'
        '**✅ 故兩者要一起裁。**' % at_risk)

    for did in ('D3', 'D24'):
        item = items[did]
        item.setdefault('newEvidenceSince700', []).append(
            {'label': '🚨 只做一邊會被重複計數的項數', 'value': at_risk,
             'from': source})
        item.setdefault('newEvidenceSince700', []).append(
            {'label': '⚠️ 重疊的結局（論文半, 期刊半修好後）', 'value': overlap,
             'from': source})
        item['interlock'] = note
        evidence = str(item['evidence'])
        if source not in evidence:
            item['evidence'] = evidence + '；' + source
        updated.append(did)

    merged = list(items.values())
    by_blocking = collections.defaultdict(list)
    for item in merged:
        by_blocking[item['blocks']].append(item['id'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('承接得到 v11 的全部登記（必觸發之正對照）',
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
    # 🚨 這一道是本版的重點：連鎖必須寫在**兩邊**。
    probe('`D3` 與 `D24` **兩邊**都寫了連鎖（必觸發之反向）',
          all('interlock' in items[d] for d in ('D3', 'D24')),
          '🚨 有連鎖說明的：%s；'
          '⚠️ 只寫一邊的話，讀到另一邊的人仍會以為它可以單獨裁'
          % [d for d in ('D3', 'D24') if 'interlock' in items[d]])
    # 🚨 這一道是答案。
    blockers = [i['id'] for i in merged
                if i['status'] == 'open' and str(i['blocks']).startswith('A')]
    probe('沒有待裁定卡著內容關卡',
          not blockers,
          '🚨 卡著內容關卡的待裁定共 %d 項：%s' % (len(blockers), blockers))

    doc = {
        'schemaVersion': 12,
        'documentType': 'pending-decision-register',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'supersedes': 'n700_decision_register_v11.json（🚫 不改寫該檔）',
        'whatThisRoundDid': (
            '🚨 `D24` 原本的建議只寫「回全文判定儀器名稱」，'
            '**⚠️ 沒提只修這一項會讓同一組受試者被算兩次**。'
            '✅ 第 701 輪把數字算出來（完全重疊、%s 項），'
            '本版把連鎖寫進 `D3` 與 `D24` **兩邊**。' % at_risk),
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

    print('=== n702 決策登記簿 v12 ===')
    print('   合計 %d 項（open %d）｜本版更新：%s'
          % (len(merged), doc['counts']['open'], updated))
    print('   連鎖說明：%s' % note)
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
