# -*- coding: utf-8 -*-
"""**A3 到 n＝2 都通過；而第一個真的不一致，裁決機制看不見。**（第 595 輪）

## ✅ 本室自己做了第二篇雙讀

⚠️ A3 前一輪只有 1 篇。**✅ 本輪本室獨立讀了 `1105537918c174c9`**
（🚨 動筆前未看正式那道的清冊——否則比對沒有意義），交進 `lane=second`。

| 篇 | 標籤兩邊都有 | 契約結局兩邊都有 | 只有一邊有 |
|---|---|---|---|
| `7a6ac1559c740fd6` | 0（41 對 18） | 2 | 0 |
| **`1105537918c174c9`** | **0（21 對 22）** | **3** | **0** |

**✅ `reportsFullyAgreed = 2／2`。**

## ✅ 而細軸也完全相同——**這比 refs 一致更強**

兩份各 9 項在範圍內宣告，且：

| | 正式那道 | 第二位 |
|---|---|---|
| 儀器 | `cycling-time-trial-fixed-work` | **相同** |
| 劑量 | 68 g/h | **相同** |
| 效應量 | mean／proportion | **相同** |

## 🚨 但兩份把**同一批句子**配到不同的結局上

| | `gi-symptom-severity` | `gi-symptom-incidence` |
|---|---|---|
| 正式那道 | **6 項** | 1 項 |
| 第二位（本室） | 2 項 | **5 項** |

⚠️ 論文報了兩種東西：**症狀的平均評分**（0–10）與
**評為嚴重（>5/10）的次數**（分母是**時點** 48＝8 人 × 6 時點，🚫 不是人數）。
✅ 而**論文自己用的字是「incidence」**來講那些次數。

> **🚨 兩邊的契約結局集合一模一樣，配置卻是 6＋1 對 2＋5。**

## 🚨 而 `adjudicate()` **看不見這件事**

`adjudicate()` 只收 `refsOnlyPrimary` 或 `refsOnlySecond` 非空的項目——
**⚠️ 也就是「一邊宣告了某個契約結局，另一邊沒有」。**
🚨 本例兩邊都宣告了兩者，故 `refsOnly*` 皆為 0，**裁決佇列是空的。**

> **⚠️ 於是 A2「每一處不一致都要判明成因」會回報「沒有不一致」——**
> **🚫 而不一致確實存在。**
>
> 🚨 這正是本 run 一再抓到的那一族：
> **量到的東西（結局集合的成員），不是結論所依賴的東西（哪些句子放進了哪個結局）。**
> ⚠️ 而這兩個結局合起來佔在範圍內 98 項的 **61%**（第 591 輪）。

📮 **本室建議的成因是 `contract-ambiguous`**：⚠️ 契約沒有說清楚
「把嚴重評分計次」該算發生率還是嚴重度。🚫 本室不逕自判自己是對的。

## 🚫 本支不入輪次閘門；🚫 lane=second 從不進入正式清冊
"""
import copy
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction.worksheet import adjudicate, agreement  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n595_second_read_invisible.json'
SHEET = ROOT / 'extraction-worksheet'
REPORT = '1105537918c174c9'
GI = ('gi-symptom-severity', 'gi-symptom-incidence')


def load(paths):
    out = {}
    for path in paths:
        for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
            out[entry['report'][-16:]] = entry
    return out


def allocation(entry):
    return Counter(o.get('normalisedOutcomeRef')
                   for o in entry.get('reportedOutcomes') or []
                   if o.get('normalisedOutcomeRef'))


def main():
    primary = load([SHEET / 'drafts.json']
                   + sorted((SHEET / 'drafts').glob('page-*.json')))
    second = load(sorted((SHEET / 'second').glob('page-*.json')))
    result = agreement(primary, second)

    alloc_a = allocation(primary[REPORT])
    alloc_b = allocation(second[REPORT])
    differs = {ref: [alloc_a.get(ref, 0), alloc_b.get(ref, 0)]
               for ref in sorted(set(alloc_a) | set(alloc_b))
               if alloc_a.get(ref, 0) != alloc_b.get(ref, 0)}

    # ✅ 裁決佇列：⚠️ 只吃 refsOnly* 非空者。
    verdict = adjudicate(result, {})

    # 🚨 必觸發之反向：把第二位的一個 outcomeId 換掉，
    # ⚠️ 讓 refsOnly* 非空，證明裁決機制在真的有這種不一致時會動。
    mutated = copy.deepcopy(second)
    for item in mutated[REPORT].get('reportedOutcomes') or []:
        if item.get('normalisedOutcomeRef') == 'tt-completion-time':
            item['normalisedOutcomeRef'] = 'time-to-exhaustion'
    mutated_result = agreement(primary, mutated)
    try:
        adjudicate(mutated_result, {})
        queue_fires = False
    except Exception:                            # noqa: BLE001
        queue_fires = True

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('雙讀已到 2 篇（必觸發）', result['comparedReports'] == 2,
          '🚨 若仍是 1 篇，本輪的第二次讀沒有交回；實得 %d 篇'
          % result['comparedReports'])
    probe('A3 於兩篇皆成立',
          result['refsOnlyPrimary'] == 0 and result['refsOnlySecond'] == 0
          and result['reportsFullyAgreed'] == result['comparedReports'],
          '✅ refsBoth=%d、只有一邊有 %d／%d、逐篇一致 %d／%d'
          % (result['refsBoth'], result['refsOnlyPrimary'],
             result['refsOnlySecond'], result['reportsFullyAgreed'],
             result['comparedReports']))
    probe('裁決機制在真有 refs 差異時會動（必觸發之反向）', queue_fires,
          '🚨 把第二位的一個 outcomeId 換掉後，adjudicate 確實要求判成因；'
          '⚠️ 若不會動，「沒有不一致」就可能只是它從不觸發')
    # 🚨 這一道會紅，而它是本支的主張。
    probe('兩位讀者把同一批句子配到相同的結局上', not differs,
          '🚨 實得配置差異 %s（severity 對 incidence）；'
          '⚠️ 而兩邊的契約結局集合完全相同，故 refsOnly*=0，'
          '🚫 adjudicate() 的佇列是空的——**這處不一致它看不見**' % differs)

    doc = {
        'schemaVersion': 1,
        'documentType': 'second-read-and-invisible-inconsistency',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'agreement': {k: v for k, v in result.items()
                      if not isinstance(v, list)},
        'perReport': [{'report': r['report'], 'refsBoth': r['refsBoth'],
                       'labelsBoth': r['both'],
                       'labelsOnlyPrimary': len(r['onlyPrimary']),
                       'labelsOnlySecond': len(r['onlySecond'])}
                      for r in result['rows']],
        'allocation': {'report': REPORT,
                       'primary': {k: v for k, v in alloc_a.items()},
                       'second': {k: v for k, v in alloc_b.items()},
                       'differs': differs},
        'adjudicationQueue': verdict,
        'blindSpot': (
            '🚨 adjudicate() 只收「一邊宣告了某契約結局，另一邊沒有」的項目。'
            '⚠️ 本例兩邊都宣告了 gi-symptom-severity 與 gi-symptom-incidence，'
            '故 refsOnly* 皆為 0，裁決佇列是空的——'
            '🚫 而配置差異（6＋1 對 2＋5）確實存在且無人判。'
            '⚠️ 這兩個結局合起來佔在範圍內 98 項的 61%。'),
        'proposedCause': {
            'cause': 'contract-ambiguous',
            'why': ('⚠️ 契約沒有說清楚「把嚴重評分計次」該算發生率還是嚴重度。'
                    '✅ 論文自己用的字是 incidence；'
                    '🚨 且其分母是**時點**（8 人 × 6 時點 ＝ 48），🚫 不是人數。'
                    '🚫 本室不逕自判自己是對的。'),
        },
        'independence': ('✅ 本室動筆前未看正式那道的清冊。'
                         '🚨 否則這次比對沒有意義。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n595 第二篇雙讀，與看不見的不一致 ===')
    print('   比對 %d 篇｜契約結局兩邊都有 %d／只有一邊 %d／%d｜逐篇一致 %d'
          % (result['comparedReports'], result['refsBoth'],
             result['refsOnlyPrimary'], result['refsOnlySecond'],
             result['reportsFullyAgreed']))
    print('   %s 的配置：正式 %s｜第二位 %s' % (REPORT, dict(alloc_a), dict(alloc_b)))
    print('   🚨 配置差異：%s' % differs)
    print('   裁決佇列：%s' % {k: v for k, v in verdict.items()
                              if not isinstance(v, (list, dict))})
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
