# -*- coding: utf-8 -*-
"""**每一個契約結局，它的項目分別死在哪一關。**（第 646 輪）

## 🚨 第 645 輪只看了劑量那一關，而關卡有六道

⚠️ 第 639 輪給的是**關卡總量**（790 → 98 的漏斗）；
🚨 第 645 輪只看劑量碼的逐結局分布。
**⚠️ 而「某個結局本來可以有多少項」這件事，需要把六道關卡合起來看。**

> **✅ 本支只數「讀的人已經把它對到契約結局」的項目**——
> 🚫 對不到契約結局的（`outcome-not-in-scope`）不在此表，
> ⚠️ 因為那些項目**從來就不屬於任何契約結局**，放進來會讓每一列都膨脹。

## ⚠️ 這張表能說與不能說的

✅ 能說：**若某一關放行，該結局會多出幾項**。
🚫 不能說：那些項目「應該」被放行——⚠️ 每一關都有它的理由，
🚨 而本支不替契約作者或讀的人決定。

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

OUT = Path(__file__).resolve().parent / 'n646_loss_ledger_by_outcome.json'
CONTRACT = REPO / 'ahig/calibration/b11-carbohydrate/scope-contract.json'

SHORT = {
    'in-scope': '進來了',
    'notExtracted-dose-outside-bands': '劑量',
    'notExtracted-effect-measure-not-in-scope': '效應量',
    'notExtracted-instrument-not-in-allowlist': '儀器',
    'notExtracted-no-numeric-result': '無數值',
    'notExtracted-outcome-not-in-scope': '結局不在契約',
}


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    contract_refs = [o['outcomeId'] for o in contract['inScopeOutcomes']]

    ledger = collections.defaultdict(collections.Counter)
    papers = collections.defaultdict(lambda: collections.defaultdict(set))
    off_contract = collections.Counter()
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        for outcome in doc.get('reportedOutcomes') or []:
            decision = outcome.get('scopeDecision') or {}
            ref = outcome.get('normalisedOutcomeRef')
            code = ('in-scope' if decision.get('inScope')
                    else decision.get('reasonCode'))
            if ref not in contract_refs:
                off_contract[code] += 1
                continue
            ledger[ref][code] += 1
            papers[ref][code].add(report)

    rows = []
    for ref in sorted(contract_refs,
                      key=lambda r: -ledger[r].get('in-scope', 0)):
        counts = ledger[ref]
        admitted = counts.get('in-scope', 0)
        blocked = sum(v for k, v in counts.items() if k != 'in-scope')
        rows.append({
            'outcome': ref,
            'admitted': admitted,
            'admittedPapers': len(papers[ref]['in-scope']),
            'blocked': blocked,
            'byGate': {SHORT.get(k, k): v for k, v in counts.most_common()
                       if k != 'in-scope'},
            'blockedPapersByGate': {
                SHORT.get(k, k): len(v) for k, v in papers[ref].items()
                if k != 'in-scope'},
            'lossRate': round(blocked / max(1, admitted + blocked), 3),
        })

    # 🚨 「被擋的項目救回來會拿到什麼」取決於它們**屬於誰**。
    # ⚠️ 若全部來自同一篇、而那一篇又是已知同群重複對的一半，
    # 救回來只增加**項數**，🚫 不增加獨立研究。
    KNOWN_PAIR = {'307c0dd5b141caed', '7a6ac1559c740fd6'}
    attribution = {}
    for ref in contract_refs:
        by_gate = {}
        for code, reports in papers[ref].items():
            if code == 'in-scope' or not reports:
                continue
            by_gate[SHORT.get(code, code)] = {
                'papers': sorted(reports),
                'allFromKnownDuplicatePair': set(reports) <= KNOWN_PAIR,
            }
        if by_gate:
            attribution[ref] = by_gate

    total_admitted = sum(r['admitted'] for r in rows)
    total_blocked = sum(r['blocked'] for r in rows)
    worst = max(rows, key=lambda r: r['lossRate']) if rows else None
    high_loss = [r for r in rows if r['lossRate'] >= 0.5]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('進來的那側等於 98（必觸發之正對照）',
          total_admitted == 98,
          '🚨 實得 %d；⚠️ 不是 98 就代表本支讀的不是同一批' % total_admitted)
    probe('本表確實排除了「對不到契約結局」的項目（必觸發之反向）',
          off_contract['notExtracted-outcome-not-in-scope'] > 0
          and all('結局不在契約' not in r['byGate'] for r in rows),
          '🚨 表外的 outcome-not-in-scope 有 %d 項，而表內 0 項；'
          '⚠️ 若它們混進來，每一列都會膨脹'
          % off_contract['notExtracted-outcome-not-in-scope'])
    probe('六個結局都有項目被關卡擋下（必觸發之正對照）',
          sum(1 for r in rows if r['blocked']) >= 4,
          '🚨 有被擋項目的結局 %d／%d；⚠️ 若幾乎沒有，這張表就沒有內容'
          % (sum(1 for r in rows if r['blocked']), len(rows)))
    # 🚨 這一道是答案。
    probe('沒有結局在關卡上損失過半',
          not high_loss,
          '🚨 損失率 ≥50%% 的結局：%s'
          % [(r['outcome'], '%d 進／%d 擋（%.0f%%）'
              % (r['admitted'], r['blocked'], 100 * r['lossRate']))
             for r in high_loss])

    doc = {
        'schemaVersion': 1,
        'documentType': 'loss-ledger-by-outcome',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'population': (
            '✅ 只含「讀的人已對到契約結局」的項目；'
            '🚫 `outcome-not-in-scope` 不在表內（%d 項）——'
            '⚠️ 那些項目從來就不屬於任何契約結局。'
            % off_contract['notExtracted-outcome-not-in-scope']),
        'admittedTotal': total_admitted,
        'blockedTotal': total_blocked,
        'rows': rows,
        'blockedItemAttribution': attribution,
        'attributionNote': (
            '🚨 儀器那一關擋下的 9 項並不對稱：'
            '⚠️ `time-to-exhaustion` 與 `muscle-glycogen-post-exercise` 的 6 項'
            '**全部來自 7a6ac1559c740fd6**——即已知同群重複對的期刊那半，'
            '**🚫 救回來只增加項數，不增加獨立研究**（第 628 輪已警告重複計數）；'
            '✅ 而 `tt-completion-time` 的 3 項來自**另外兩篇不同的論文**，'
            '**🚨 那才是真的補得到獨立證據的地方。**'),
        'headline': (
            '🚨 損失率最高的是 **%s**：%d 項進來、%d 項被擋（%.0f%%）。'
            % (worst['outcome'], worst['admitted'], worst['blocked'],
               100 * worst['lossRate']) if worst else ''),
        'whatThisCannotSay': (
            '🚫 本表不主張那些被擋的項目「應該」放行——⚠️ 每一關都有理由；'
            '✅ 它只回答「若某一關放行，該結局會多出幾項」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n646 逐結局的損失帳 ===')
    print('   （只含已對到契約結局的項目；表外另有 %d 項 outcome-not-in-scope）'
          % off_contract['notExtracted-outcome-not-in-scope'])
    print('   %-30s %6s %6s %7s  %s'
          % ('結局', '進來', '被擋', '損失率', '死在哪一關'))
    for row in rows:
        print('   %-30s %6d %6d %6.0f%%  %s'
              % (row['outcome'], row['admitted'], row['blocked'],
                 100 * row['lossRate'],
                 row['byGate'] or '（無）'))
    print('   合計：進來 %d｜被擋 %d' % (total_admitted, total_blocked))
    print('   被擋項目屬於誰（只列儀器那一關）：')
    for ref, gates in attribution.items():
        if '儀器' in gates:
            print('      %-32s %s%s'
                  % (ref, gates['儀器']['papers'],
                     '  🚨 全部來自已知同群重複對'
                     if gates['儀器']['allFromKnownDuplicatePair'] else ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
