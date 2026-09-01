# -*- coding: utf-8 -*-
"""**讀者挑的儀器名稱，單獨決定了那篇在不在範圍內嗎。**（第 663 輪）

## 🚨 第 662 輪查到的事

同一篇（`7a6ac1559c740fd6`）兩位讀者都說有「運動至衰竭時間」與
「運動後肌肝醣」，**✅ 結局層級完全一致**，🚨 但儀器名稱各寫各的：

| 結局 | 第一線寫的 | 第二線寫的 |
|---|---|---|
| time-to-exhaustion | `cycling-time-to-exhaustion-fixed-power` | `cycling-tte-fixed-intensity` |
| muscle-glycogen-post-exercise | `acid-hydrolysis-freeze-dried-biopsy` | `needle-biopsy-vastus-lateralis` |

> **🚨 而第二線寫的那兩個，逐字就是契約允許清單裡的名字；第一線寫的兩個都不在。**

## ✅ 本支問的是「所以呢」

把兩份**都餵進產品的 `ScopeMatcher.decide_inventory`**，看在範圍內的數量差多少。

⚠️ 但兩份還差一件事：第一線多寫了 `dose=0` 的**對照臂**。
**🚨 故只比兩份會分不清是「儀器名稱」還是「對照臂」造成的差異。**

✅ 於是加一道**反事實**：拿第一線的清冊，**只把儀器名稱換成第二線的**，
其餘一字不動，再判一次——**這樣才隔離得出儀器名稱單獨的效果**。

## 🚫 本支不改磁碟上任何清冊（全部在記憶體裡做副本）、不送外部請求
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

OUT = Path(__file__).resolve().parent / 'n663_reader_vocabulary.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')
WORKSHEET = ROOT / 'extraction-worksheet'
TARGET = '7a6ac1559c740fd6'

SWAP = {
    'cycling-time-to-exhaustion-fixed-power': 'cycling-tte-fixed-intensity',
    'acid-hydrolysis-freeze-dried-biopsy': 'needle-biopsy-vastus-lateralis',
}


def load_primary():
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        if doc['report'].endswith(TARGET):
            return doc
    return None


def load_second():
    for path in sorted((WORKSHEET / 'second').glob('page-*.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))
        for entry in doc.get('entries') or []:
            if entry['report'].endswith(TARGET):
                return entry
    return None


def summarise(matcher, inventory):
    """判定並依理由碼分類。"""
    verdict = matcher.decide_inventory(inventory)
    reasons = {}
    for decision in verdict['decisions']:
        if decision['inScope']:
            continue
        reasons[decision['reasonCode']] = reasons.get(
            decision['reasonCode'], 0) + 1
    return {
        'inScopeCount': verdict['inScopeCount'],
        'candidateCount': verdict['candidateCount'],
        'escalated': verdict['escalated'],
        'outOfScopeReasons': dict(sorted(reasons.items())),
    }


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)

    primary = load_primary()
    second = load_second()
    if primary is None or second is None:
        print('🚨 找不到雙讀的兩份，無法比')
        return 1

    as_is_primary = summarise(matcher, primary)
    as_is_second = summarise(
        matcher, {'inventoryId': 'second-read',
                  'reportedOutcomes': second['reportedOutcomes']})

    # ✅ 反事實：**只**換儀器名稱，其餘一字不動。
    swapped = copy.deepcopy(primary)
    swaps_made = 0
    for outcome in swapped['reportedOutcomes']:
        name = outcome.get('instrument')
        if name in SWAP:
            outcome['instrument'] = SWAP[name]
            swaps_made += 1
    counterfactual = summarise(matcher, swapped)

    # ⚠️ 另一個候選成因：第一線多寫的對照臂（dose=0）。
    no_control = copy.deepcopy(primary)
    dropped = 0
    kept = []
    for outcome in no_control['reportedOutcomes']:
        if outcome.get('normalisedOutcomeRef') and outcome.get('dose') == 0:
            dropped += 1
            continue
        kept.append(outcome)
    no_control['reportedOutcomes'] = kept
    without_control = summarise(matcher, no_control)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    # ✅ 正對照：判定器真的會判「在範圍內」——否則零全都不算數。
    positive = None
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        got = summarise(matcher, doc)
        if got['inScopeCount'] > 0:
            positive = (doc['report'][-16:], got['inScopeCount'])
            break
    probe('判定器在別篇上真的判得出「在範圍內」（必觸發之正對照）',
          positive is not None,
          '🚨 正對照篇 %s 判出 %s 項在範圍內；⚠️ 若一篇都判不出，'
          '本支的「0」就只是判定器壞了'
          % (positive[0] if positive else '—',
             positive[1] if positive else 0))

    # ✅ 必觸發之負對照：換成一個保證不在清單裡的名字，必須掉出範圍。
    bogus = copy.deepcopy(swapped)
    for outcome in bogus['reportedOutcomes']:
        if outcome.get('instrument') in SWAP.values():
            outcome['instrument'] = 'instrument-that-cannot-exist-663'
    bogus_result = summarise(matcher, bogus)
    probe('把命中的名字改成不存在的名字後，必須掉出範圍（必觸發之負對照）',
          bogus_result['inScopeCount'] < counterfactual['inScopeCount'],
          '🚨 反事實 %d 項 → 亂改名字後 %d 項；⚠️ 若沒掉，'
          '代表儀器根本沒被檢查，本支的因果歸屬就不成立'
          % (counterfactual['inScopeCount'], bogus_result['inScopeCount']))

    probe('反事實真的動到了東西（必觸發之正對照）',
          swaps_made > 0,
          '🚨 換掉 %d 個儀器名稱、丟掉 %d 個對照臂項；⚠️ 若是 0，'
          '反事實就只是把原件重判一次' % (swaps_made, dropped))

    # 🚨 這一道是答案。
    instrument_effect = (counterfactual['inScopeCount']
                         - as_is_primary['inScopeCount'])
    control_effect = (without_control['inScopeCount']
                      - as_is_primary['inScopeCount'])
    probe('儀器名稱的用字，🚫 不足以單獨改變在不在範圍內',
          instrument_effect == 0,
          '🚨 只換儀器名稱：%d 項 → %d 項（差 %+d）；'
          '⚠️ 只丟對照臂：%d 項 → %d 項（差 %+d）'
          % (as_is_primary['inScopeCount'], counterfactual['inScopeCount'],
             instrument_effect, as_is_primary['inScopeCount'],
             without_control['inScopeCount'], control_effect))

    doc = {
        'schemaVersion': 1,
        'documentType': 'reader-vocabulary-scope-effect',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'report': TARGET,
        'asIsPrimary': as_is_primary,
        'asIsSecond': as_is_second,
        'counterfactualInstrumentSwapped': counterfactual,
        'counterfactualControlArmDropped': without_control,
        'instrumentSwaps': SWAP,
        'instrumentSwapsMade': swaps_made,
        'controlArmItemsDropped': dropped,
        'instrumentEffect': instrument_effect,
        'controlArmEffect': control_effect,
        'whatThisShows': (
            '🚨 兩位讀者對**同一篇的同一個結局**，寫出不同的儀器名稱，'
            '✅ 而契約用的是**逐字比對的允許清單**——'
            '⚠️ 故「讀者挑哪個字」會直接進到範圍判定裡。'
            '🚫 本支不主張這一篇的結果就是全體的結果：**樣本是 1 篇**。'),
        'methodLimit': (
            '⚠️ 反事實是在**記憶體副本**上做的，🚫 磁碟上的清冊一字未改。'
            '🚨 且本支只證得了「換字之後判定會不會變」，'
            '🚫 證不出「哪一位讀者寫的才是對的」——'
            '那要回到全文，而那是讀論文的視窗的事（n+187）。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n663 讀者用字對範圍判定的效果（%s）===' % TARGET)
    print('   第一線原樣          ：在範圍 %d｜候選 %d｜%s'
          % (as_is_primary['inScopeCount'], as_is_primary['candidateCount'],
             as_is_primary['outOfScopeReasons']))
    print('   第二線原樣          ：在範圍 %d｜候選 %d｜%s'
          % (as_is_second['inScopeCount'], as_is_second['candidateCount'],
             as_is_second['outOfScopeReasons']))
    print('   反事實・只換儀器名稱：在範圍 %d（差 %+d）｜%s'
          % (counterfactual['inScopeCount'], instrument_effect,
             counterfactual['outOfScopeReasons']))
    print('   反事實・只丟對照臂  ：在範圍 %d（差 %+d）｜%s'
          % (without_control['inScopeCount'], control_effect,
             without_control['outOfScopeReasons']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
