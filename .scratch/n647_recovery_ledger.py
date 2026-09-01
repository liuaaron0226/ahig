# -*- coding: utf-8 -*-
"""**每一件待裁定，施行之後實際拿回什麼。**（第 647 輪）

## 🚨 第 643–646 輪量出了損失，而協調者要決定的是「值不值得動」

⚠️ 目前登記簿上寫的是「建議施行／建議修」，**🚫 但沒有一件附著「拿回多少」。**
🚨 而第 646 輪剛示範過：**同樣是 3 項，來自兩篇不同論文與來自同一篇重複對，
價值差很多。**

> **✅ 故本支的每一列都要回答三件事：拿回幾項、多幾篇獨立研究、落在哪個結局。**

## ⚠️ 「多一篇獨立研究」怎麼算

**✅ 該篇目前零貢獻，且不屬於已知同群重複對** ⇒ 算一篇。
🚨 若它是重複對的一半，**🚫 不算**——⚠️ 那不是新研究，是同一批受試者。

## 🚫 本支不主張任何一件該不該施行——✅ 只把價碼放上來
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

OUT = Path(__file__).resolve().parent / 'n647_recovery_ledger.json'
CONTRACT = REPO / 'ahig/calibration/b11-carbohydrate/scope-contract.json'

KNOWN_PAIR = {'307c0dd5b141caed', '7a6ac1559c740fd6'}


def main():
    contract_refs = {o['outcomeId'] for o in json.loads(
        CONTRACT.read_text(encoding='utf-8'))['inScopeOutcomes']}

    items = []
    in_scope_by_paper = collections.Counter()
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        for outcome in doc.get('reportedOutcomes') or []:
            decision = outcome.get('scopeDecision') or {}
            ref = outcome.get('normalisedOutcomeRef')
            if decision.get('inScope'):
                in_scope_by_paper[report] += 1
                continue
            if ref not in contract_refs:
                continue
            items.append({
                'report': report, 'ref': ref,
                'code': decision.get('reasonCode'),
                'dose': outcome.get('dose'),
                'effectMeasure': outcome.get('effectMeasure'),
            })

    # ⚠️ 每個結局目前有哪幾篇在貢獻——🚨 用來算「那個結局會多幾篇」。
    papers_by_outcome = collections.defaultdict(set)
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for outcome in doc.get('reportedOutcomes') or []:
            if (outcome.get('scopeDecision') or {}).get('inScope'):
                papers_by_outcome[outcome.get('normalisedOutcomeRef')].add(
                    doc['report'][-16:])

    def bucket(predicate):
        chosen = [i for i in items if predicate(i)]
        papers = {i['report'] for i in chosen}
        # ✅ 目前零貢獻、且不屬於已知重複對 ⇒ 真的多一篇獨立研究。
        newly = {p for p in papers
                 if in_scope_by_paper[p] == 0 and p not in KNOWN_PAIR}
        from_pair = {p for p in papers if p in KNOWN_PAIR}
        return {
            'items': len(chosen),
            'papers': sorted(papers),
            'newIndependentStudies': len(newly),
            'newIndependentStudyIds': sorted(newly),
            'papersFromKnownDuplicatePair': sorted(from_pair),
            'byOutcome': dict(collections.Counter(
                i['ref'] for i in chosen).most_common()),
            # 🚨 本室第一版只算「該篇從零貢獻變有貢獻」——
            # ⚠️ 但對最薄的結局，真正要問的是「**那個結局**多幾篇」：
            # 一篇已在別的結局有貢獻的論文，補進計時賽仍是計時賽的新一篇。
            'newPapersPerOutcome': {
                ref: len({i['report'] for i in chosen if i['ref'] == ref}
                         - papers_by_outcome[ref])
                for ref in {i['ref'] for i in chosen}},
        }

    buckets = {
        'D5：dose=0（對照組）不走排除路徑': bucket(
            lambda i: i['code'] == 'notExtracted-dose-outside-bands'
            and i['dose'] is not None and float(i['dose']) == 0),
        'D6：接受 median 這個效應量': bucket(
            lambda i: i['code'] == 'notExtracted-effect-measure-not-in-scope'
            and i['effectMeasure'] == 'median'),
        'D2／D3：儀器清單（改名／合併）': bucket(
            lambda i: i['code']
            == 'notExtracted-instrument-not-in-allowlist'),
        '（未登記）讀的人沒填劑量': bucket(
            lambda i: i['code'] == 'notExtracted-dose-outside-bands'
            and i['dose'] is None),
        '（未登記）讀的人沒填效應量': bucket(
            lambda i: i['code'] == 'notExtracted-effect-measure-not-in-scope'
            and i['effectMeasure'] is None),
        '🚫 真的在帶外（180 g/h）': bucket(
            lambda i: i['code'] == 'notExtracted-dose-outside-bands'
            and i['dose'] is not None and float(i['dose']) > 150),
        # 🚨 第一版漏了這一桶，於是桶內 35／被擋 36——**探針當場抓到**。
        '（未登記）宣稱無數值結果': bucket(
            lambda i: i['code'] == 'notExtracted-no-numeric-result'),
    }

    total_items = sum(b['items'] for b in buckets.values())
    total_new = sum(b['newIndependentStudies'] for b in buckets.values())
    tt_gain = sum(b['byOutcome'].get('tt-completion-time', 0)
                  for b in buckets.values())

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一項被擋的都落進恰好一個桶（必觸發之正對照）',
          total_items == len(items),
          '🚨 桶內合計 %d／被擋合計 %d；⚠️ 對不上代表有桶重疊或漏接'
          % (total_items, len(items)))
    probe('在範圍內那側等於 98（必觸發之正對照）',
          sum(in_scope_by_paper.values()) == 98,
          '🚨 實得 %d；⚠️ 不是 98 就代表本支讀的不是同一批'
          % sum(in_scope_by_paper.values()))
    probe('重複對的篇有被單獨標出（必觸發之反向）',
          any(b['papersFromKnownDuplicatePair'] for b in buckets.values()),
          '🚨 若一篇重複對的論文都沒出現在被擋項目裡，'
          '「不算新研究」這條規則就沒被測到')
    # 🚨 這兩道是現況。
    probe('每一件待裁定都至少多帶回一篇獨立研究',
          all(b['newIndependentStudies'] > 0
              for name, b in buckets.items()
              if name.startswith('D')),
          '🚨 帶不回獨立研究的：%s'
          % [name for name, b in buckets.items()
             if name.startswith('D') and b['newIndependentStudies'] == 0])
    probe('最薄的結局拿不回東西',
          tt_gain == 0,
          '🚨 全部桶加起來，`tt-completion-time` 可拿回 %d 項；'
          '⚠️ 而它目前在範圍內只有 6 項' % tt_gain)

    doc = {
        'schemaVersion': 1,
        'documentType': 'recovery-ledger',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'howIndependenceIsCounted': (
            '✅ 「多一篇獨立研究」＝該篇目前零貢獻、且不屬於已知同群重複對；'
            '🚨 若它是重複對的一半就不算——⚠️ 那不是新研究，是同一批受試者。'),
        'buckets': buckets,
        'totals': {'items': total_items,
                   'newIndependentStudies': total_new,
                   'ttCompletionTimeItems': tt_gain},
        'whatThisIsFor': (
            '⚠️ 登記簿目前每一件都寫著「建議施行」，🚫 卻沒有附上「拿回多少」。'
            '✅ 本支補上價碼——🚫 但不主張任何一件該不該施行。'),
        'whatThisCannotSay': (
            '🚫 「拿回幾項」不等於「那些項可以合併」——'
            '⚠️ 第 632／633 輪已量出可合併性另有問題（儀器沒記、量表不同）。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n647 待裁定的回收帳 ===')
    print('   %-34s %5s %8s  %s' % ('待裁定', '項數', '新獨立研究', '落在哪個結局'))
    for name, row in buckets.items():
        print('   %-34s %5d %8d  %s'
              % (name, row['items'], row['newIndependentStudies'],
                 row['byOutcome']))
        gains = {k: v for k, v in row['newPapersPerOutcome'].items() if v}
        if gains:
            print('        ✅ 各結局會多幾篇：%s' % gains)
        if row['papersFromKnownDuplicatePair']:
            print('        🚨 其中來自已知同群重複對：%s'
                  % row['papersFromKnownDuplicatePair'])
        if row['newIndependentStudyIds']:
            print('        ✅ 會從零貢獻變成有貢獻：%s'
                  % row['newIndependentStudyIds'])
    print('   合計：項數 %d｜新獨立研究 %d｜其中計時賽 %d 項'
          % (total_items, total_new, tt_gain))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
