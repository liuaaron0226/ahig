# -*- coding: utf-8 -*-
"""**兩條 cap 路徑，這次真的各跑一次。**（第 638 輪）

## 🚨 第 593 輪是讀程式碼推論的，第 637 輪查明那條路從未跑過

⚠️ 第 593 輪指出 `decide_inventory` 與 `scope_inventory` 對「有沒有超過上限」
算法不同（括號位置差一個），並判斷**現行契約下兩者一致**。
🚨 但那是**讀出來的**；第 637 輪又查明：本 run 最大在範圍內項數 9、上限 12，
**⚠️ 即 escalate 那條路從未真的跑過。**

> **🚨 未跑過的路是缺陷的住所。✅ 本輪把它跑起來。**

## ✅ 三個情境，兩條路各跑一次

| 情境 | 期望 |
|---|---|
| **甲** 未超過上限 | ✅ 兩條路都不升級（正對照） |
| **乙** 超過上限、`onExceedMax=escalate`（**現行契約**） | ✅ 兩條路一致升級 |
| **丙** 超過上限、`onExceedMax` 改成別的值 | **🚨 這裡才是分歧所在** |

⚠️ 合成清冊的作法：拿一份**真實**清冊，把它在範圍內的項目複製到超過上限——
🚨 不手刻紀錄（第 632 輪的教訓：手刻的紀錄連正當儀器都過不了）。

## 🚫 本支不改任何產品程式、不改任何清冊、不送外部請求
"""
import copy
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

OUT = Path(__file__).resolve().parent / 'n638_cap_paths_executed.json'
CONTRACT = REPO / 'ahig/calibration/b11-carbohydrate/scope-contract.json'


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    cap = (contract['extractionPolicy'].get('maxStudyResultsPerStudy') or 12)

    # ⚠️ 找在範圍內項數最多的那份真實清冊當種子。
    seed = None
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        count = sum(1 for o in doc.get('reportedOutcomes') or []
                    if (o.get('scopeDecision') or {}).get('inScope'))
        if seed is None or count > seed[1]:
            seed = (doc, count)
    inventory, seed_in_scope = seed

    def build(target_in_scope):
        """把真實清冊的在範圍內項目複製到指定數量。"""
        draft = copy.deepcopy(inventory)
        in_scope_items = [o for o in draft['reportedOutcomes']
                          if (o.get('scopeDecision') or {}).get('inScope')]
        others = [o for o in draft['reportedOutcomes']
                  if not (o.get('scopeDecision') or {}).get('inScope')]
        clones = []
        while len(clones) < target_in_scope:
            clones.append(copy.deepcopy(
                in_scope_items[len(clones) % len(in_scope_items)]))
        draft['reportedOutcomes'] = clones + others
        for item in draft['reportedOutcomes']:
            item.pop('scopeDecision', None)
        draft.pop('scopeDecisionSummary', None)
        draft.pop('scopedAt', None)
        draft['lifecycle'] = 'draft'
        return draft

    def run_both(draft, contract_variant):
        matcher = ScopeMatcher(contract_variant)
        decided = matcher.decide_inventory(copy.deepcopy(draft))
        try:
            scoped = matcher.scope_inventory(copy.deepcopy(draft),
                                             now='2026-01-01T00:00:00Z')
            summary = scoped['scopeDecisionSummary']
            still_in_scope = sum(
                1 for o in scoped['reportedOutcomes']
                if (o.get('scopeDecision') or {}).get('inScope'))
            scoped_view = {'escalated': summary['escalated'],
                           'inScopeCount': summary['inScopeCount'],
                           'itemsStillInScope': still_in_scope}
        except Exception as error:  # noqa: BLE001
            scoped_view = {'error': '%s: %s' % (type(error).__name__, error)}
        decided_view = {
            'escalated': decided['escalated'],
            'inScopeCount': decided['inScopeCount'],
            'itemsStillInScope': sum(1 for d in decided['decisions']
                                     if d.get('inScope')),
        }
        return decided_view, scoped_view

    variant = copy.deepcopy(contract)
    variant['extractionPolicy'] = dict(variant['extractionPolicy'])
    variant['extractionPolicy']['onExceedMax'] = 'truncate'

    under = build(min(seed_in_scope, cap - 1))
    over = build(cap + 1)

    scenarios = {
        '甲 未超過上限（現行契約）': run_both(under, contract),
        '乙 超過上限（現行契約 escalate）': run_both(over, contract),
        '丙 超過上限（onExceedMax=truncate）': run_both(over, variant),
    }

    def agree(pair):
        left, right = pair
        if 'error' in right:
            return False
        return (left['escalated'] == right['escalated']
                and left['inScopeCount'] == right['inScopeCount']
                and left['itemsStillInScope'] == right['itemsStillInScope'])

    agreement = {name: agree(pair) for name, pair in scenarios.items()}
    # 🚨 自我矛盾＝摘要說 0 項在範圍內，逐項卻還留著 in-scope。
    contradictions = {}
    for name, (left, right) in scenarios.items():
        contradictions[name] = {
            'decide_inventory':
                left['inScopeCount'] == 0 and left['itemsStillInScope'] > 0,
            'scope_inventory':
                ('error' not in right
                 and right['inScopeCount'] == 0
                 and right['itemsStillInScope'] > 0),
        }

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('合成清冊真的做出超過上限的量（必觸發之正對照）',
          scenarios['乙 超過上限（現行契約 escalate）'][0]['escalated'],
          '🚨 上限 %d、合成 %d 項；⚠️ 若沒超過，本支三個情境全都白跑'
          % (cap, cap + 1))
    probe('未超過上限時兩條路一致（必觸發之正對照）',
          agreement['甲 未超過上限（現行契約）'],
          '🚨 甲情境：%s；⚠️ 若這裡就不一致，分歧與上限無關'
          % json.dumps(scenarios['甲 未超過上限（現行契約）'],
                       ensure_ascii=False))
    # 🚨 這兩道是答案。
    probe('現行契約下、超過上限時兩條路一致',
          agreement['乙 超過上限（現行契約 escalate）'],
          '%s 乙情境：%s'
          % ('✅' if agreement['乙 超過上限（現行契約 escalate）'] else '🚨',
             json.dumps(scenarios['乙 超過上限（現行契約 escalate）'],
                        ensure_ascii=False)))
    probe('換掉 onExceedMax 之後兩條路仍一致',
          agreement['丙 超過上限（onExceedMax=truncate）'],
          '🚨 丙情境：%s；⚠️ **這是第 593 輪讀出來、本輪跑出來的分歧**'
          % json.dumps(scenarios['丙 超過上限（onExceedMax=truncate）'],
                       ensure_ascii=False))
    probe('沒有情境產出自我矛盾的文件',
          not any(v['decide_inventory'] or v['scope_inventory']
                  for v in contradictions.values()),
          '🚨 自我矛盾（摘要說 0 項、逐項卻還留著 in-scope）：%s'
          % json.dumps({k: v for k, v in contradictions.items()
                        if v['decide_inventory'] or v['scope_inventory']},
                       ensure_ascii=False))

    doc = {
        'schemaVersion': 1,
        'documentType': 'cap-paths-executed',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'seedReport': inventory['report'][-16:],
        'seedInScope': seed_in_scope,
        'cap': cap,
        'scenarios': {k: {'decide_inventory': v[0], 'scope_inventory': v[1]}
                      for k, v in scenarios.items()},
        'agreement': agreement,
        'selfContradiction': contradictions,
        'howThisDiffersFromN593': (
            '⚠️ 第 593 輪是**讀程式碼**推出「現行契約下兩者一致」。'
            '✅ 本支是**真的各跑一次**，並且多跑了一個 onExceedMax 被換掉的情境——'
            '🚨 那正是第 593 輪指出、卻沒有人執行過的分歧點。'),
        'whatThisCannotAnswer': (
            '🚫 本支不主張該把 onExceedMax 改成別的值——⚠️ 那是契約作者的事；'
            '✅ 它只回答「若有人改了，兩條路會不會給出不同的東西」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n638 兩條 cap 路徑實跑 ===')
    print('   種子清冊 %s｜原在範圍內 %d｜上限 %d'
          % (inventory['report'][-16:], seed_in_scope, cap))
    for name, (left, right) in scenarios.items():
        print('   %s' % name)
        print('      decide_inventory ：%s' % json.dumps(left, ensure_ascii=False))
        print('      scope_inventory  ：%s' % json.dumps(right, ensure_ascii=False))
        print('      一致＝%s' % agreement[name])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
