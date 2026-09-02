# -*- coding: utf-8 -*-
"""**那兩個 12 不是同一個 12。**（第 691 輪）

## 🚨 一個很容易被讀錯的巧合

- **第 613 輪**：GROBID 那 15 篇被削掉的表格裡，**帶契約結局詞彙的有 12 張**。
- **第 690 輪**：在範圍內、定位點指到表、而酬載是 GROBID 的，**有 12 項**。

> **⚠️ 兩個都是 12。🚨 而它們數的**不是同一種東西**：
> 一個數**表格**，一個數**項目**。**

⚠️ 一張表可以撐起好幾個項目；🚨 一個項目指到的表也可能**沒有**結局詞彙。
**✅ 若有人把這兩個 12 當成同一批，D17 的效益就會被高估或低估——而看不出來。**

## ✅ 本支做的事

把兩邊的**報告代號集合**攤開來比。
🚨 若集合不同，那個巧合就只是巧合。

## 🚫 本支不改任何清冊與契約、不送外部請求、不輸出表格文字
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

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n691_two_twelves.json'
N613 = HERE / 'n613_recoverable_from_tables.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')


def payload_types():
    out = {}
    for path in (ROOT / 'fulltext').rglob('manifest.json'):
        try:
            doc = json.loads(path.read_text(encoding='utf-8'))
        except (OSError, ValueError):
            continue
        candidate = str(doc.get('candidateId') or '')
        if candidate and doc.get('sourceType'):
            out[candidate[-16:]] = doc['sourceType']
    return out


def main():
    n613 = json.loads(N613.read_text(encoding='utf-8'))
    outcome_tables = {row['report']: row['tablesWithOutcomeTerms']
                      for row in n613['rows']
                      if row.get('tablesWithOutcomeTerms')}
    tables_total = sum(outcome_tables.values())

    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)
    types = payload_types()

    items = collections.Counter()
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        report = inventory['report'][-16:]
        if types.get(report) != 'grobid-tei':
            continue
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if not decision['inScope']:
                continue
            loc = reported.get('sourceLocation')
            if isinstance(loc, dict) and loc.get('tableOrFigure') is not None:
                items[report] += 1
    items_total = sum(items.values())

    set_tables = set(outcome_tables)
    set_items = set(items)
    both = sorted(set_tables & set_items)
    only_tables = sorted(set_tables - set_items)
    only_items = sorted(set_items - set_tables)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩邊各自都重算得到 12（必觸發之正對照）',
          tables_total == 12 and items_total == 12,
          '🚨 第 613 輪的結局表重算 %d 張（%d 篇）；'
          '第 690 輪的項目重算 %d 項（%d 篇）；'
          '⚠️ 對不上就代表本支比錯了對象'
          % (tables_total, len(set_tables), items_total, len(set_items)))
    probe('捏造的報告代號不在任一集合（必觸發之反向）',
          'ffffffffffffffff' not in set_tables | set_items,
          '🚨 捏造代號不在兩個集合裡；⚠️ 若在，代表集合是亂湊的')
    # 🚨 這一道是答案。
    probe('那兩個 12 指的是同一批東西',
          set_tables == set_items,
          '🚨 兩邊都有的 %d 篇：%s；只有「結局表」那邊的 %d 篇：%s；'
          '只有「在範圍內項目」那邊的 %d 篇：%s；'
          '⚠️ 集合不同就代表那個 12 對 12 只是巧合'
          % (len(both), both, len(only_tables), only_tables,
             len(only_items), only_items))

    doc = {
        'schemaVersion': 1,
        'documentType': 'two-twelves-disambiguation',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'theCoincidence': (
            '⚠️ 第 613 輪「帶結局詞彙的表格 12 張」與'
            '第 690 輪「GROBID 酬載中指到表的在範圍內項目 12 項」——'
            '🚨 兩個都是 12，**但一個數表格、一個數項目**。'),
        'outcomeTablesByReport': outcome_tables,
        'inScopeTablePointingItemsByReport': dict(items.most_common()),
        'reportsInBoth': both,
        'reportsOnlyWithOutcomeTables': only_tables,
        'reportsOnlyWithInScopeTableItems': only_items,
        'whyThisMatters': (
            '🚨 一張表可以撐起好幾個項目；'
            '⚠️ 一個項目指到的表也可能**沒有**結局詞彙。'
            '**✅ 若把這兩個 12 當成同一批，`D17` 的效益就會被高估或低估，'
            '🚫 而且看不出來。**'),
        'whatThisDoesNotSay': (
            '🚫 本支不主張哪一個數字比較重要，'
            '⚠️ 也不重新評估 `D17` 值不值得修——'
            '✅ 它只把兩個長得一樣的數字分開。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n691 兩個 12 ===')
    print('   第 613 輪「帶結局詞彙的表格」：%d 張，分佈 %s'
          % (tables_total, outcome_tables))
    print('   第 690 輪「在範圍內且指到表」：%d 項，分佈 %s'
          % (items_total, dict(items.most_common())))
    print('   兩邊都有的篇：%s' % (both or '無'))
    print('   只有表格那邊：%s' % (only_tables or '無'))
    print('   只有項目那邊：%s' % (only_items or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
