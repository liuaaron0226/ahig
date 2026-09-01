# -*- coding: utf-8 -*-
"""**41 篇進來，98 項出去——中間掉在哪裡。**（第 643 輪）

## 🚨 「16 篇零貢獻」這件事散在好幾輪，從沒有合起來

⚠️ 第 586 輪數過 13 篇零貢獻（分母是 38 份清冊）；
🚨 而語料是 41 篇——**另外 3 篇連清冊都沒有**（第 585 輪的 blockedReports）。
**⚠️ 兩個數放在不同輪次、用不同分母，於是「有幾篇沒貢獻」要自己拼。**

> **✅ 本支把整條漏斗攤成一張表：每一跳掉了幾篇、為什麼。**

## ⚠️ 第 639 輪做過結局層級的漏斗，本支做的是**論文層級**

🚨 兩者不同：結局層級回答「790 項怎麼變成 98 項」，
✅ 論文層級回答「**41 篇裡有幾篇最後什麼都沒給**」。

## 🚫 本支不改任何清冊、不送外部請求、不改任何產品程式
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
from ahig.extraction import corpus  # noqa: E402

S = Path(__file__).resolve().parent
OUT = S / 'n643_corpus_to_evidence_funnel.json'


def main():
    roster = set(corpus.acquired_roster()[0])

    inventories = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        inventories[doc['report']] = doc

    no_inventory = sorted(roster - set(inventories))

    declared_nothing = []
    declared_all_rejected = []
    contributing = []
    rejection_profile = {}
    for report, doc in inventories.items():
        outcomes = doc.get('reportedOutcomes') or []
        in_scope = [o for o in outcomes
                    if (o.get('scopeDecision') or {}).get('inScope')]
        if in_scope:
            contributing.append(report)
            continue
        if not outcomes:
            declared_nothing.append(report)
            continue
        declared_all_rejected.append(report)
        rejection_profile[report[-16:]] = dict(collections.Counter(
            (o.get('scopeDecision') or {}).get('reasonCode')
            for o in outcomes).most_common())

    # ⚠️ 那 3 篇沒有清冊的，第 585 輪記為 blockedReports——✅ 對一次，
    # 🚨 因為「兩個名單剛好一樣」與「本室記得它們一樣」是兩回事。
    blocked = []
    errata = S / 'n585_blocked_drafts_errata.json'
    if errata.is_file():
        blocked = sorted(json.loads(errata.read_text(encoding='utf-8'))
                         .get('blockedReports') or [])
    blocked_matches = sorted(x[-16:] for x in no_inventory) == blocked

    # 🚨 與第 586 輪對帳：⚠️ 該輪記「zeroBecauseNothingDeclared: 5」，
    # 而本支算出「宣告了零個結局」是 **0 篇**。✅ 逐一比對後對得起來：
    # 第 586 輪分家族時**排除了** outcome-not-in-scope 與 no-numeric-result，
    # 於是「其餘理由碼為空」的那 5 篇被標成 nothing-declared。
    # **🚨 但那個標籤名不副實**——那 5 篇各自宣告了 10–37 個結局。
    only_soft = []
    SOFT = {'notExtracted-outcome-not-in-scope',
            'notExtracted-no-numeric-result'}
    for report in declared_all_rejected:
        codes = {(o.get('scopeDecision') or {}).get('reasonCode')
                 for o in inventories[report].get('reportedOutcomes') or []}
        if codes <= SOFT:
            only_soft.append({
                'report': report[-16:],
                'declaredOutcomes': len(
                    inventories[report].get('reportedOutcomes') or []),
            })

    total_in_scope = sum(
        1 for doc in inventories.values()
        for o in doc.get('reportedOutcomes') or []
        if (o.get('scopeDecision') or {}).get('inScope'))

    funnel = [
        {'stage': '已取得全文', 'papers': len(roster), 'lost': 0,
         'why': '—'},
        {'stage': '有清冊', 'papers': len(inventories),
         'lost': len(no_inventory),
         'why': '🚨 草稿被守衛擋下（第 585 輪 blockedReports）'},
        {'stage': '清冊裡宣告了結局', 'papers': len(inventories)
         - len(declared_nothing),
         'lost': len(declared_nothing),
         'why': '⚠️ 讀完後一個結局都沒宣告'},
        {'stage': '至少一項進到範圍內', 'papers': len(contributing),
         'lost': len(declared_all_rejected),
         'why': '⚠️ 宣告了，但全部被判在範圍外'},
    ]

    contributes_nothing = (len(no_inventory) + len(declared_nothing)
                           + len(declared_all_rejected))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('漏斗每一跳都結算得回去（必觸發之正對照）',
          len(roster) == len(contributing) + contributes_nothing,
          '🚨 %d ＝ %d 有貢獻 ＋ %d 沒貢獻？%s；'
          '⚠️ 對不上代表本支漏了一種掉法'
          % (len(roster), len(contributing), contributes_nothing,
             len(roster) == len(contributing) + contributes_nothing))
    probe('沒有清冊指向名冊外的論文（必觸發之反向）',
          not (set(inventories) - roster),
          '🚨 清冊有而名冊無者：%s；⚠️ 若有，代表兩邊的「這批」不是同一批'
          % sorted(x[-16:] for x in (set(inventories) - roster)))
    probe('那 3 篇無清冊者，正是第 585 輪記下的 blockedReports',
          blocked_matches,
          '%s 無清冊 %s vs 第 585 輪 %s；'
          '⚠️ 本室**對一次**而不是憑記憶說它們一樣'
          % ('✅' if blocked_matches else '🚨',
             sorted(x[-16:] for x in no_inventory), blocked))
    # 🚨 這一道是現況。
    probe('語料裡每一篇都對證據有貢獻',
          contributes_nothing == 0,
          '🚨 %d／%d 篇（%.0f%%）什麼都沒給：'
          '無清冊 %d、宣告了零個結局 %d、宣告後全被排除 %d'
          % (contributes_nothing, len(roster),
             100 * contributes_nothing / max(1, len(roster)),
             len(no_inventory), len(declared_nothing),
             len(declared_all_rejected)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'corpus-to-evidence-funnel',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'unit': '論文（🚫 不是結局——結局層級的漏斗在第 639 輪）',
        'funnel': funnel,
        'inScopeOutcomes': total_in_scope,
        'papersContributingNothing': contributes_nothing,
        'noInventory': [x[-16:] for x in no_inventory],
        'declaredNothing': [x[-16:] for x in declared_nothing],
        'declaredAllRejected': [x[-16:] for x in declared_all_rejected],
        'rejectionProfileOfThoseWhoDeclared': rejection_profile,
        'blockedMatchesN585': blocked_matches,
        'n586Reconciliation': {
            'n586Label': 'zeroBecauseNothingDeclared: 5',
            'recomputedDeclaredNothing': len(declared_nothing),
            'papersMatchingN586Family': only_soft,
            'diagnosis': (
                '✅ 兩邊對得起來：第 586 輪分家族時**排除了** '
                'outcome-not-in-scope 與 no-numeric-result 兩個碼，'
                '於是「其餘理由碼為空」的 %d 篇被標成 nothing-declared。'
                '**🚨 而那個標籤名不副實**——那幾篇各自宣告了 %s 個結局，'
                '⚠️ 不是「什麼都沒宣告」，是**「宣告了一堆、一個都沒對上契約」**。'
                '🚨 這正是本 run 反覆抓到的同一族：**一種失敗長得像另一種。**'
                '🚫 n586 不就地改寫（已上看板），本條即其 errata。'
                % (len(only_soft),
                   '／'.join(str(x['declaredOutcomes']) for x in only_soft))),
        },
        'readingNote': (
            '⚠️ 第 586 輪的「13 篇零貢獻」分母是 **38 份清冊**；'
            '🚨 本支的 %d 篇分母是 **41 篇語料**——'
            '**✅ 兩個都對，差在那 3 篇連清冊都沒有。**'
            '⚠️ 這正是第 636 輪查出的同一種定義落差。'
            % contributes_nothing),
        'whatThisIsNot': (
            '🚫 本支不判斷那 %d 篇「應該」有貢獻——⚠️ 一篇論文與本題無關而'
            '零貢獻是正常的；🚨 但把「無清冊」「宣告了零個」「全被排除」'
            '混成一個數字，會讓三種很不一樣的成因看起來像同一件事。'
            % contributes_nothing),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n643 從語料到證據的漏斗（論文層級）===')
    print('   %-20s %6s %6s  %s' % ('階段', '剩下', '掉了', '為什麼'))
    for row in funnel:
        print('   %-20s %6d %6d  %s'
              % (row['stage'], row['papers'], row['lost'], row['why']))
    print('   最終在範圍內結局 %d 項' % total_in_scope)
    print('   🚨 什麼都沒給的 %d／%d 篇：無清冊 %s｜宣告零個 %s｜全被排除 %s'
          % (contributes_nothing, len(roster),
             [x[-16:] for x in no_inventory],
             [x[-16:] for x in declared_nothing],
             [x[-16:] for x in declared_all_rejected]))
    print('   🚨 第 586 輪「nothing-declared: %d」那一族，實際各宣告了：%s'
          % (len(only_soft),
             ', '.join('%s=%d' % (x['report'], x['declaredOutcomes'])
                       for x in only_soft)))
    print('   宣告後全被排除者的理由碼：')
    for report, profile in rejection_profile.items():
        print('      %s  %s' % (report, profile))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
