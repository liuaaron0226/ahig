# -*- coding: utf-8 -*-
"""**補回空白劑量，能不能讓計時賽從「零同篇內對比」變成有。**（第 711 輪）

## ✅ 接第 710 輪自己寫下的限制

n710：「⚠️ 劑量空白的那 12 項在本支裡不算數，**🚨 故 9 篇是下界**。」

🚨 而第 710 輪最要緊的發現是：**`tt-completion-time` 零篇提供同篇內對比**。
⚠️ 第 645 輪又說：那 12 項空白劑量裡，**7 項正是 `tt-completion-time`**。

> **✅ 於是有一個很具體的問題：
> 若 `D23`（回補空白欄位）裁下去，計時賽會不會從 0 變成有？**

## ✅ 本支能算到哪裡、算不到哪裡

- ✅ **算得到**：那些空白項落在哪一（篇 × 結局），
  以及該組**現在**有沒有已在範圍內、且帶著劑量的項目。
- 🚫 **算不到**：補進來的值是多少——⚠️ 那要讀論文（`n+187`）。

> **🚨 故本支的產出是「補了**就可能**產生同篇內對比」的候選組，
> 🚫 不是「補了就會有」。**

## 🚫 本支不改任何清冊與契約、不送外部請求、不輸出標籤文字
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

OUT = Path(__file__).resolve().parent / \
    'n711_blank_dose_contrast_potential.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')
FOCUS = 'tt-completion-time'


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    in_scope_doses = collections.defaultdict(set)
    blanks = collections.Counter()
    blank_items = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        report = inventory['report'][-16:]
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            ref = reported.get('normalisedOutcomeRef')
            if not ref:
                continue
            if decision['inScope']:
                if reported.get('dose') is not None:
                    in_scope_doses[(report, ref)].add(float(reported['dose']))
            elif decision['reasonCode'] == 'notExtracted-dose-outside-bands' \
                    and reported.get('dose') is None:
                blanks[(report, ref)] += 1
                blank_items.append({'report': report, 'outcome': ref})

    rows = []
    for (report, ref), count in sorted(blanks.items()):
        existing = in_scope_doses.get((report, ref), set())
        # ✅ 補了**可能**產生對比的兩種情形
        via_existing = len(existing) >= 1      # 現有 1 個 ＋ 補進來 1 個
        via_blanks = count >= 2                # 兩個空白各補一個值
        rows.append({
            'report': report, 'outcome': ref,
            'blankItems': count,
            'existingInScopeDoses': sorted(existing),
            'couldCreateContrast': bool(via_existing or via_blanks),
            'route': ('現有劑量 ＋ 補一個' if via_existing
                      else ('兩個空白各補一個' if via_blanks
                            else '🚫 補了也只有一個劑量')),
        })

    # 🚨 單位要講清楚：`rows` 是（篇 × 結局）**組**，而第 645 輪數的是**項**。
    # ⚠️ 本支第一版拿「組數」去跟「項數」比，探針立刻紅——
    # **✅ 又是那一族：兩個數字看起來能比，單位卻不同。**
    items_by_outcome = collections.Counter()
    for row in rows:
        items_by_outcome[row['outcome']] += row['blankItems']
    groups_by_outcome = collections.Counter(r['outcome'] for r in rows)
    by_outcome = items_by_outcome
    could = [r for r in rows if r['couldCreateContrast']]
    focus_rows = [r for r in rows if r['outcome'] == FOCUS]
    focus_could = [r for r in focus_rows if r['couldCreateContrast']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('抓到的正是第 645 輪那 12 項空白（必觸發之正對照）',
          sum(blanks.values()) == 12,
          '🚨 空白劑量項共 %d 項，逐結局 %s；⚠️ 不是 12 就與第 645 輪不一致'
          % (sum(blanks.values()), dict(by_outcome)))
    probe('計時賽那一格是 7 項（必觸發之正對照）',
          by_outcome.get(FOCUS) == 7,
          '🚨 `%s` 的空白 %s 項；⚠️ 對不上就與第 645 輪不一致'
          % (FOCUS, by_outcome.get(FOCUS)))
    probe('捏造的（篇×結局）沒有候選（必觸發之反向）',
          not any(r['report'] == 'ffffffffffffffff' for r in rows),
          '🚨 捏造代號不在表裡；⚠️ 若在，代表本支收錯了東西')
    # 🚨 這一道是答案。
    probe('補回空白劑量，計時賽仍不會有同篇內對比',
          not focus_could,
          '🚨 `%s` 有 %d／%d 組**補了就可能**產生同篇內對比：%s；'
          '⚠️ 而那是**可能**，🚫 不是「會」——'
          '**補進來的值若與現有的相同，仍然沒有對比**'
          % (FOCUS, len(focus_could), len(focus_rows),
             [(r['report'], r['route'], r['existingInScopeDoses'])
              for r in focus_could]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'blank-dose-contrast-potential',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n710（空白劑量不算數，故 9 篇是下界）',
        'blankDoseItems': sum(blanks.values()),
        'blankItemsByOutcome': dict(items_by_outcome.most_common()),
        'blankGroupsByOutcome': dict(groups_by_outcome.most_common()),
        'rows': rows,
        'groupsThatCouldGainContrast': len(could),
        'focusOutcome': FOCUS,
        'focusGroupsThatCouldGain': focus_could,
        'whatThisMeansForD23': (
            '⚠️ `D23`（回補空白欄位）的效益，第 666 輪只算到'
            '「4 項是強漏填訊號」。'
            '**🚨 本支加一層：補回來之後，**哪些（篇×結局）可能因此獲得'
            '同篇內的劑量對比**——⚠️ 而那正是 `tt-completion-time` '
            '目前完全沒有的東西。**'),
        'whatThisCannotAnswer': (
            '🚫 補進來的值是多少，本支**算不到**——⚠️ 那要讀論文（`n+187`）。'
            '🚨 故「可能產生對比」是**上界**：'
            '**⚠️ 補進來的值若與現有的相同，仍然沒有對比。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n711 補回空白劑量的對比潛力 ===')
    print('   空白劑量 %d 項（散在 %d 組）｜逐結局・項數 %s'
          % (sum(blanks.values()), len(rows),
             dict(items_by_outcome.most_common())))
    print('   可能因此獲得同篇內對比的（篇×結局）組：%d／%d'
          % (len(could), len(rows)))
    print('   逐組：')
    for row in rows:
        print('      %s｜%-30s 空白 %d｜現有劑量 %s｜%s'
              % (row['report'], row['outcome'], row['blankItems'],
                 row['existingInScopeDoses'] or '無', row['route']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
