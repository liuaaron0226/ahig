# -*- coding: utf-8 -*-
"""**在範圍內的證據裡，有多少根本沒有儀器紀錄。**（第 667 輪）

## 🚨 第 666 輪算母體空白率時撞到的

已對上契約結局的 134 項裡，**儀器欄空白 68 項**——⚠️ 而它們幾乎都沒有被擋。

> **🚨 因為擋不擋得看契約：`_match_outcome` 是 `if allowed and ...`，
> ✅ 而 `allowedInstruments` 留空的結局，這道門根本不檢查。**

## 🚨 而留空的那兩個，正好是 GI 症狀

| 結局 | 允許清單長度 |
|---|---|
| tt-completion-time | 3 |
| time-to-exhaustion | 2 |
| exogenous-cho-oxidation-peak | 1 |
| muscle-glycogen-post-exercise | 1 |
| **gi-symptom-incidence** | **0 🚨** |
| **gi-symptom-severity** | **0 🚨** |

⚠️ 而 GI 症狀嚴重度本來就是各家量表各自為政（第 633 輪已看過這一族）。

## ✅ 本支要釘死三件事

1. **在範圍內**的項目裡，沒有儀器紀錄的到底幾項、佔多少
2. **這是不是真的由空清單造成**——✅ 反事實：給那兩個結局隨便一個非空清單，看它們掉不掉出去
3. ⚠️ 這對可合併性代表什麼——🚫 本支只給數字，**不做合併與否的判斷**

## 🚫 本支不改磁碟上的契約與清冊（反事實全在記憶體副本）、不送外部請求
"""
import collections
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

OUT = Path(__file__).resolve().parent / 'n667_inscope_without_instrument.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')
NO_ALLOWLIST = ['gi-symptom-incidence', 'gi-symptom-severity']


def inventories():
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        yield json.loads(path.read_text(encoding='utf-8'))


def tally(matcher):
    """在範圍內的項目：總數、無儀器數、各結局明細。"""
    in_scope = collections.Counter()
    no_instrument = collections.Counter()
    papers_no_instrument = collections.defaultdict(set)
    for inventory in inventories():
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if not decision['inScope']:
                continue
            ref = reported['normalisedOutcomeRef']
            in_scope[ref] += 1
            if reported.get('instrument') is None:
                no_instrument[ref] += 1
                papers_no_instrument[ref].add(inventory['report'][-16:])
    return in_scope, no_instrument, papers_no_instrument


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    in_scope, no_instrument, papers = tally(matcher)
    total_in_scope = sum(in_scope.values())
    total_blank = sum(no_instrument.values())

    empty_lists = [o['outcomeId'] for o in contract['inScopeOutcomes']
                   if not (o.get('allowedInstruments') or [])]

    # ✅ 反事實：給那兩個結局一個**非空**清單（放一個不可能存在的名字），
    #    🚨 若空清單真的是原因，它們必須整批掉出範圍。
    forced = copy.deepcopy(contract)
    touched = 0
    for outcome in forced['inScopeOutcomes']:
        if outcome['outcomeId'] in NO_ALLOWLIST:
            outcome['allowedInstruments'] = ['instrument-placeholder-667']
            touched += 1
    forced_in_scope, _, _ = tally(ScopeMatcher(forced))
    lost = {ref: in_scope[ref] - forced_in_scope.get(ref, 0)
            for ref in in_scope if in_scope[ref] != forced_in_scope.get(ref, 0)}

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('判定器真的判出了在範圍內的項目（必觸發之正對照）',
          total_in_scope > 0,
          '🚨 在範圍內 %d 項，分佈 %s；⚠️ 若是 0，本支的比例沒有分母'
          % (total_in_scope, dict(in_scope.most_common())))
    probe('留空清單的結局就是 GI 那兩個（必觸發之正對照）',
          sorted(empty_lists) == sorted(NO_ALLOWLIST),
          '🚨 實得留空者：%s；⚠️ 若對不上，本支後面的歸因就是錯的'
          % sorted(empty_lists))
    probe('把空清單改成非空之後，那些項目必須掉出範圍（必觸發之反向）',
          touched == len(NO_ALLOWLIST)
          and sorted(lost) == sorted(NO_ALLOWLIST),
          '🚨 改了 %d 個結局；掉出範圍的分佈：%s；'
          '⚠️ 若沒掉，代表放行不是空清單造成的，本支的因果歸屬不成立'
          % (touched, lost))
    # 🚨 這一道是答案。
    probe('在範圍內的項目都有儀器紀錄',
          total_blank == 0,
          '🚨 在範圍內卻沒有儀器紀錄的有 %d／%d 項（%.0f%%），分佈 %s；'
          '⚠️ 它們能進來，是因為契約對那兩個結局沒設允許清單'
          % (total_blank, total_in_scope,
             100.0 * total_blank / total_in_scope if total_in_scope else 0,
             dict(no_instrument.most_common())))

    doc = {
        'schemaVersion': 1,
        'documentType': 'in-scope-without-instrument',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inScopeTotal': total_in_scope,
        'inScopeByOutcome': dict(in_scope.most_common()),
        'inScopeWithoutInstrument': total_blank,
        'withoutInstrumentByOutcome': dict(no_instrument.most_common()),
        'papersAffected': {ref: sorted(v) for ref, v in papers.items()},
        'outcomesWithEmptyAllowlist': sorted(empty_lists),
        'counterfactualLostIfAllowlistNonEmpty': lost,
        'whatThisMeans': (
            '🚨 在範圍內的證據裡有 %d／%d 項**完全沒有記錄用什麼量的**，'
            '✅ 而它們能進來不是因為通過了檢查，'
            '**是因為契約對那兩個結局根本沒設檢查**（空清單＝門全開，第 665 輪已實測）。'
            '⚠️ 而那兩個正好是 GI 症狀——**各家量表各自為政的那一族**（第 633 輪）。'
            % (total_blank, total_in_scope)),
        'whatThisIsNot': (
            '🚫 本支不主張這些項目應該被排除，也不主張契約錯了——'
            '⚠️ 「GI 症狀不設儀器限制」可能是刻意的決定。'
            '📮 本支只指出：**那個決定的後果是 %d 項證據沒有儀器資訊**，'
            '而可合併性要靠這一欄。' % total_blank),
        'methodLimit': (
            '⚠️ 「沒有儀器紀錄」指的是清冊裡這一欄為空，'
            '🚫 不代表論文沒寫——**可能是讀者沒填**（第 666 輪同一族）。'
            '🚨 分不出這兩者要看全文（n+187 的視窗）。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n667 在範圍內卻沒有儀器紀錄 ===')
    print('   在範圍內共 %d 項；其中無儀器 %d 項（%.0f%%）'
          % (total_in_scope, total_blank,
             100.0 * total_blank / total_in_scope if total_in_scope else 0))
    print('   各結局：在範圍內／其中無儀器／允許清單長度')
    lengths = {o['outcomeId']: len(o.get('allowedInstruments') or [])
               for o in contract['inScopeOutcomes']}
    for ref in sorted(in_scope, key=lambda r: -in_scope[r]):
        print('      %-32s %3d ／ %3d ／ 清單 %d%s'
              % (ref, in_scope[ref], no_instrument.get(ref, 0), lengths[ref],
                 '  🚨' if not lengths[ref] else ''))
    print('   反事實・給 GI 兩個結局非空清單後掉出範圍：%s' % lost)
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
