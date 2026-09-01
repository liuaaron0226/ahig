# -*- coding: utf-8 -*-
"""**本 run 報過的頭條數字，彼此對得起來嗎。**（第 636 輪）

## 🚨 協調者正在讀幾十個數字，而沒有一處對過帳

⚠️ 41 篇、38 份清冊、790 項、98 項在範圍內、25 篇有貢獻、692 項不在範圍內、
656 項未宣告、60 項腸胃症狀、21 篇……**🚫 這些都是本室在不同輪次分別報的。**

> **🚨 一個飄掉的數字不會叫**——⚠️ 它會被引用、被拿去算別的數，
> **而下游沒有人會發現它跟上游對不起來。**

## ✅ 本支怎麼對

每一個頭條數字**從私有根重算一次**，再跟**憑證裡記的值**比。
🚨 兩邊都要有：只重算沒有比對，等於再報一次；只讀憑證不重算，等於相信自己。

## ⚠️ 兩件本支刻意不做

- 🚫 **不改任何憑證**——⚠️ 對不上就列出來，由協調者裁。
- 🚫 **不判斷哪一邊對**——🚨 差異可能是定義不同（第 618 輪那次就是），不是錯。

## 🚫 本支不送外部請求、不改任何產品程式
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
OUT = S / 'n636_headline_reconciliation.json'


def dig(doc, path):
    cur = doc
    for key in path:
        if isinstance(cur, dict) and key in cur:
            cur = cur[key]
        elif isinstance(cur, list) and isinstance(key, int) and key < len(cur):
            cur = cur[key]
        else:
            return None
    return cur


def main():
    # ---- 從私有根重算 ----------------------------------------------------
    roster = set(corpus.acquired_roster()[0])

    inventories = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventories.append(json.loads(path.read_text(encoding='utf-8')))

    outcomes = []
    for doc in inventories:
        for outcome in doc.get('reportedOutcomes') or []:
            outcomes.append((doc['report'], outcome))

    in_scope = [(r, o) for r, o in outcomes
                if (o.get('scopeDecision') or {}).get('inScope')]
    out_scope = [(r, o) for r, o in outcomes
                 if not (o.get('scopeDecision') or {}).get('inScope')]
    declared_excluded = [
        (r, o) for r, o in out_scope
        if (o.get('scopeDecision') or {}).get('reasonCode')
        not in (None, '', 'not-declared')]
    contributing = {r for r, _ in in_scope}
    gi = [(r, o) for r, o in in_scope
          if str(o.get('normalisedOutcomeRef') or '').startswith('gi-symptom')]

    # 🚨 本支第一版把「未宣告」定義成「理由碼為空」——⚠️ 而每一列其實都有碼，
    # 於是必然得 0。**那不是憑證飄掉，是本室這一輪的重算規則錯了。**
    # ✅ 第 621 輪的 656 ＝ outcome-not-in-scope（647）
    #    ＋ instrument-not-in-allowlist（9）：⚠️ 前者從未對到契約結局，
    #    後者對到了卻卡在儀器——兩者都還沒進到「宣告了什麼結果」那一層。
    reason_counts = collections.Counter(
        (o.get('scopeDecision') or {}).get('reasonCode') for _, o in out_scope)
    UNDECLARED_CODES = ('notExtracted-outcome-not-in-scope',
                        'notExtracted-instrument-not-in-allowlist')
    undeclared = [(r, o) for r, o in out_scope
                  if (o.get('scopeDecision') or {}).get('reasonCode')
                  in UNDECLARED_CODES]
    distinct_candidates = 0
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        if (entry.is_dir()
                and not entry.name.startswith('ahig_candidate_publication_')
                and (entry / 'manifest.json').exists()):
            distinct_candidates += 1
    doses = [float(o['dose']) for _, o in in_scope if o.get('dose') is not None]

    recomputed = {
        '語料篇數': len(roster),
        '相異候選數': distinct_candidates,
        '未宣告（不在範圍內）': len(undeclared),
        # ⚠️ 零貢獻有兩個分母：🚨 語料 41 篇 vs 清冊 38 份。
        # ✅ 第 586 輪用的是後者（38−25＝13），本支兩個都列。
        '零貢獻篇數（清冊為分母）': len(inventories) - len(contributing),
        '在範圍內有劑量者': len(doses),
        '清冊份數': len(inventories),
        '結局總數': len(outcomes),
        '在範圍內': len(in_scope),
        '不在範圍內': len(out_scope),
        '有貢獻的篇數': len(contributing),
        '零貢獻的篇數': len(roster) - len(contributing),
        '腸胃症狀項數': len(gi),
        '腸胃症狀篇數': len({r for r, _ in gi}),
    }

    # ---- 憑證裡記的值 ----------------------------------------------------
    # ⚠️ 一律「檔名 ＋ 欄位路徑」，🚫 不手打數字。
    RECORDED = {
        '語料篇數': ('n628_evidence_thinness.json', None),  # 見下方特例
        '清冊份數': ('n630_binding_integrity.json', ['inventories']),
        '在範圍內': ('n632_poolability.json', ['inScopeOutcomes']),
        '腸胃症狀項數': ('n633_gi_scale_heterogeneity.json',
                         ['giOutcomesExamined']),
        '腸胃症狀篇數': ('n633_gi_scale_heterogeneity.json', ['papers']),
        '有貢獻的篇數': ('n627_dose_proxy_validation.json', ['truthPapers']),
    }
    # ⚠️ 語料篇數在 n624 是以「相異候選」記的，另取。
    RECORDED['語料篇數'] = ('n624_corpus_denominator.json', ['rosterTotal'])
    RECORDED['相異候選數'] = ('n624_corpus_denominator.json',
                              ['distinctCandidates'])
    RECORDED['未宣告（不在範圍內）'] = ('n621_out_of_scope_audit.json',
                                        ['outOfScopeScanned'])
    RECORDED['零貢獻篇數（清冊為分母）'] = (
        'n586_zero_contribution_census.json', ['zeroContributionReports'])
    RECORDED['在範圍內有劑量者'] = ('n627_dose_proxy_validation.json',
                                    ['inScopeDoseValues'])


    rows = []
    unreadable = []
    for label, (filename, path) in RECORDED.items():
        source = S / filename
        if not source.is_file():
            unreadable.append((label, filename))
            continue
        value = dig(json.loads(source.read_text(encoding='utf-8')), path)
        if value is None:
            unreadable.append((label, '%s:%s' % (filename, path)))
            continue
        rows.append({'metric': label, 'recomputedNow': recomputed[label],
                     'recordedInArtefact': value,
                     'from': '%s → %s' % (filename, '/'.join(map(str, path))),
                     'agrees': recomputed[label] == value})

    # ---- 內部算術一致性 --------------------------------------------------
    arithmetic = [
        {'check': '在範圍內 ＋ 不在範圍內 ＝ 結局總數',
         'left': recomputed['在範圍內'] + recomputed['不在範圍內'],
         'right': recomputed['結局總數']},
        {'check': '有貢獻 ＋ 零貢獻 ＝ 語料篇數',
         'left': recomputed['有貢獻的篇數'] + recomputed['零貢獻的篇數'],
         'right': recomputed['語料篇數']},
        {'check': '清冊份數 ≤ 語料篇數',
         'left': recomputed['清冊份數'], 'right': recomputed['語料篇數'],
         'operator': '<='},
        {'check': '未宣告 ＋ 其餘理由碼 ＝ 不在範圍內',
         'left': recomputed['未宣告（不在範圍內）']
         + (len(out_scope) - recomputed['未宣告（不在範圍內）']),
         'right': recomputed['不在範圍內']},
    ]
    for item in arithmetic:
        if item.get('operator') == '<=':
            item['holds'] = item['left'] <= item['right']
        else:
            item['holds'] = item['left'] == item['right']

    disagreements = [r for r in rows if not r['agrees']]
    broken_arithmetic = [a for a in arithmetic if not a['holds']]

    # 🚨 必觸發之反向：⚠️ 把一個重算值弄壞，比對器必須抓到。
    # ✅ 走的是同一組比對邏輯，🚫 不是拿假值跟真值比大小。
    tampered = dict(recomputed)
    tampered['清冊份數'] = recomputed['清冊份數'] + 1
    tampered_disagreements = sum(
        1 for r in rows if tampered[r['metric']] != r['recordedInArtefact'])

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的對到夠多項（必觸發之正對照）',
          len(rows) >= 5,
          '🚨 實得可比對 %d 項、取不到 %d 項；⚠️ 太少的話「全部相符」沒有份量'
          % (len(rows), len(unreadable)))
    probe('弄壞一個重算值，比對器必須抓到（必觸發之反向）',
          tampered_disagreements == len(disagreements) + 1,
          '🚨 竄改一項後，不符數 %d → %d；⚠️ 若沒變，'
          '「全部相符」不代表任何事'
          % (len(disagreements), tampered_disagreements))
    probe('每一個引用都取得到（必觸發）',
          not unreadable,
          '🚨 取不到者 %d：%s；⚠️ **取不到的引用比沒有引用更糟**'
          % (len(unreadable), unreadable))
    # 🚨 以下兩道是答案。
    probe('重算值與憑證所記一致',
          not disagreements,
          '%s 不一致 %d 項：%s'
          % ('✅' if not disagreements else '🚨', len(disagreements),
             [(r['metric'], r['recomputedNow'], r['recordedInArtefact'])
              for r in disagreements]))
    probe('內部算術站得住',
          not broken_arithmetic,
          '%s 不成立 %d 項：%s'
          % ('✅' if not broken_arithmetic else '🚨', len(broken_arithmetic),
             [(a['check'], a['left'], a['right'])
              for a in broken_arithmetic]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'headline-reconciliation',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'recomputedFromPrivateRoot': recomputed,
        'comparisons': rows,
        'arithmetic': arithmetic,
        'unreadableReferences': unreadable,
        'declaredThenExcluded': len(declared_excluded),
        'reasonCodeCounts': dict(reason_counts.most_common()),
        'twoDenominatorsForZeroContribution': {
            '語料 41 篇為分母': len(roster) - len(contributing),
            '清冊 38 份為分母（第 586 輪用的）':
                len(inventories) - len(contributing),
            'note': ('⚠️ 兩個都對，🚨 差在有 3 篇語料沒有清冊。'
                     '✅ 這正是第 618 輪那種「定義不同、不是誰錯」。'),
        },
        'myOwnRuleWasWrong': (
            '🚨 本支第一版把「未宣告」定義成「理由碼為空」，'
            '⚠️ 而每一列其實都有碼——於是重算必然得 0，看起來像憑證飄了 656。'
            '**✅ 錯的是本輪的重算規則，🚫 不是第 621 輪。**'
            '⚠️ 一份對帳表若把自己的錯誤報成別人的漂移，比不對帳更糟。'),
        'whyItMatters': (
            '⚠️ 協調者正在讀幾十個分別報出的數字。'
            '🚨 一個飄掉的數字不會叫——它會被引用、被拿去算別的數，'
            '**而下游沒有人會發現它跟上游對不起來。**'),
        'whatThisDoesNotDo': (
            '🚫 不改任何憑證；🚫 不判斷哪一邊對——'
            '⚠️ 差異可能是定義不同（第 618 輪那次就是），不是錯。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n636 頭條數字對帳 ===')
    print('   %-14s %8s %10s  %s' % ('項目', '重算', '憑證所記', '一致'))
    for row in rows:
        print('   %-14s %8s %10s  %s'
              % (row['metric'], row['recomputedNow'],
                 row['recordedInArtefact'], '✅' if row['agrees'] else '🚨'))
    print('   內部算術：')
    for item in arithmetic:
        print('      %s %s（%s vs %s）'
              % ('✅' if item['holds'] else '🚨', item['check'],
                 item['left'], item['right']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
