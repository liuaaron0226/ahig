# -*- coding: utf-8 -*-
"""**儀器用字擋掉的量，全語料的上界是多少。**（第 664 輪）

## 🚨 第 663 輪只證了 1 篇

`7a6ac1559c740fd6` 的零貢獻，**單獨由儀器名稱造成**
（只換名字 0→4 項；只丟對照臂 0→0）。
**⚠️ 但那是 1 篇，🚫 不是語料的結論。**

## ✅ 本支把它推到全部 38 份清冊

對每一份跑產品的 `ScopeMatcher.decide_inventory`，然後問兩件事：

1. **在「讀者已經對上契約結局」的項目裡**，理由碼怎麼分佈——
   ⚠️ 沒對上結局的（`outcome-not-in-scope`）不算，那是真的不在範圍。
2. **上界**：把契約的 `allowedInstruments` 全部清空再判一次。
   🚨 產品第 83 行是 `if allowed and ...`，**空清單等於不設限**
   （第 620 輪已證），✅ 故這一跑就是「儀器檢查關掉」的世界。

> **✅ 兩者之差＝「儀器用字」這一項最多擋掉多少。**
> **🚫 這是上界，不是可回收量**——⚠️ 因為關掉檢查會連真的不該進來的也放進來。

## ⚠️ 一個必須先講的陷阱

放寬之後，某些篇的在範圍項數會**衝破 `maxStudyResultsPerStudy` 上限**
而被 escalate，🚨 於是 `inScopeCount` 反而歸零。
✅ 故單調性要用 `candidateCount` 比，**而 escalate 要另外數**。

## 🚫 本支不改磁碟上的契約與清冊（全部在記憶體副本上做）、不送外部請求
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

OUT = Path(__file__).resolve().parent / 'n664_vocabulary_upper_bound.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')


def inventories():
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        yield json.loads(path.read_text(encoding='utf-8'))


def judge(matcher, inventory):
    verdict = matcher.decide_inventory(inventory)
    mapped_blocked = collections.Counter()
    for reported, decision in zip(inventory['reportedOutcomes'],
                                  verdict['decisions']):
        if decision['inScope']:
            continue
        if not reported.get('normalisedOutcomeRef'):
            continue          # ⚠️ 讀者根本沒對上契約結局，不是欄位擋的
        mapped_blocked[decision['reasonCode']] += 1
    return verdict, mapped_blocked


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    strict = ScopeMatcher(contract)

    relaxed_contract = copy.deepcopy(contract)
    cleared = 0
    for outcome in relaxed_contract['inScopeOutcomes']:
        if outcome.get('allowedInstruments'):
            cleared += 1
            outcome['allowedInstruments'] = []
    relaxed = ScopeMatcher(relaxed_contract)

    rows = []
    blocked_total = collections.Counter()
    for inventory in inventories():
        strict_verdict, blocked = judge(strict, inventory)
        relaxed_verdict, _ = judge(relaxed, inventory)
        blocked_total.update(blocked)
        rows.append({
            'report': inventory['report'][-16:],
            'strictInScope': strict_verdict['inScopeCount'],
            'strictCandidates': strict_verdict['candidateCount'],
            'relaxedCandidates': relaxed_verdict['candidateCount'],
            'relaxedEscalated': relaxed_verdict['escalated'],
            'strictEscalated': strict_verdict['escalated'],
            'instrumentBlocked': blocked.get(
                'notExtracted-instrument-not-in-allowlist', 0),
            'mappedBlocked': dict(sorted(blocked.items())),
        })

    zero = [r for r in rows if r['strictInScope'] == 0]
    zero_with_instrument = [r for r in zero if r['instrumentBlocked'] > 0]
    gained_items = sum(r['relaxedCandidates'] - r['strictCandidates']
                       for r in rows)
    gained_papers = [r['report'] for r in rows
                     if r['strictCandidates'] == 0
                     and r['relaxedCandidates'] > 0]
    regressed = [r['report'] for r in rows
                 if r['relaxedCandidates'] < r['strictCandidates']]
    newly_escalated = [r['report'] for r in rows
                       if r['relaxedEscalated'] and not r['strictEscalated']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('放寬版契約真的清掉了允許清單（必觸發之正對照）',
          cleared > 0,
          '🚨 清空了 %d 個結局的 allowedInstruments；⚠️ 若是 0，'
          '「放寬」那一跑就只是嚴格版重跑一次' % cleared)
    probe('嚴格版真的擋過人（必觸發之正對照）',
          blocked_total.get(
              'notExtracted-instrument-not-in-allowlist', 0) > 0,
          '🚨 已對上結局卻被擋的項目：%s；⚠️ 若儀器那一格是 0，'
          '本支就沒有可談的現象'
          % dict(blocked_total.most_common()))
    probe('放寬只會放進來、🚫 不會擠掉既有的（以 candidateCount 比）',
          not regressed,
          '🚨 放寬後候選變少的篇：%s；⚠️ 若有，代表放寬還動到了別的東西，'
          '因果歸屬不成立' % (regressed or '無'))
    # 🚨 這一道是答案。
    probe('儀器用字 🚫 沒有擋住任何項目',
          gained_items == 0,
          '🚨 關掉儀器檢查後多出 %d 項候選、%d 篇從零貢獻變成有貢獻'
          '（%s）；⚠️ 另有 %d 篇因此衝破上限被 escalate（%s）'
          % (gained_items, len(gained_papers), gained_papers or '無',
             len(newly_escalated), newly_escalated or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'instrument-vocabulary-upper-bound',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inventories': len(rows),
        'zeroContributionPapers': len(zero),
        'zeroContributionWithInstrumentBlock': len(zero_with_instrument),
        'zeroContributionWithInstrumentBlockIds': [
            r['report'] for r in zero_with_instrument],
        'mappedButBlockedByReason': dict(blocked_total.most_common()),
        'upperBoundExtraCandidates': gained_items,
        'upperBoundPapersUnblocked': gained_papers,
        'newlyEscalatedIfRelaxed': newly_escalated,
        'rows': rows,
        'whatThisIs': (
            '✅ 這是**上界**：關掉儀器檢查最多能放進來多少。'
            '🚫 不是可回收量——⚠️ 關掉檢查會連真的量錯東西的也放進來，'
            '🚨 而契約設允許清單正是為了擋那些。'
            '✅ 真正的問題是：**被擋的那些，是「讀者寫了別的字」還是'
            '「真的量了別的東西」**——'
            '🚫 而那要回到全文才分得出來（n+187 的視窗）。'),
        'methodLimit': (
            '⚠️ 本支用「已對上契約結局」當過濾條件，'
            '🚨 故完全漏掉「讀者連結局都沒對上」的那些——'
            '那一族第 643 輪已另計。'
            '⚠️ 且放寬版契約只在記憶體裡，🚫 磁碟上的契約一字未改。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n664 儀器用字擋掉的量・全語料上界 ===')
    print('   清冊 %d 份｜零貢獻 %d 篇｜其中有儀器被擋的 %d 篇'
          % (len(rows), len(zero), len(zero_with_instrument)))
    print('   已對上結局卻被擋，理由碼分佈：')
    for reason, count in blocked_total.most_common():
        print('      %-46s %d' % (reason, count))
    print('   關掉儀器檢查：候選 %+d 項｜%d 篇從零變有'
          % (gained_items, len(gained_papers)))
    for row in sorted(rows, key=lambda r: -r['instrumentBlocked'])[:8]:
        if row['instrumentBlocked']:
            print('      %s｜儀器擋 %d 項｜嚴格候選 %d → 放寬 %d'
                  % (row['report'], row['instrumentBlocked'],
                     row['strictCandidates'], row['relaxedCandidates']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
