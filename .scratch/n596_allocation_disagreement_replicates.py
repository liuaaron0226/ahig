# -*- coding: utf-8 -*-
"""**A3 到 3／3；而那個「看不見的不一致」複現了，且有方向。**（第 596 輪）

## ✅ 本室再讀第三篇：`a9012191142e7e02`（外源碳水氧化家族，至此才有雙讀）

| 篇 | 標籤兩邊都有 | 契約結局兩邊都有 | 只有一邊有 |
|---|---|---|---|
| `7a6ac1559c740fd6` | 0 | 2 | 0 |
| `1105537918c174c9` | 0 | 3 | 0 |
| **`a9012191142e7e02`** | **0** | **3** | **0** |

**✅ `reportsFullyAgreed = 3／3`；標籤逐字重疊仍是 0（86 對 62）。**

## 🚨 三篇**全部**有配置差異——但**只有一篇是界線位移**

| 篇 | 差異 | 性質 |
|---|---|---|
| `1105537918c174c9` | 嚴重度 **6／2**、發生率 **1／5**（兩邊各 9 項） | **🚨 界線位移** |
| `a9012191142e7e02` | 嚴重度 2／3、發生率 2／4（正式 6 項、第二位 9 項） | ⚠️ **顆粒度** |
| `7a6ac1559c740fd6` | 力竭時間 3／2、肝醣 3／2 | ⚠️ **顆粒度** |

> **🚨 本支初稿寫的是「兩篇同方向」。⚠️ 那是說過頭了**——
> 第二篇本室是**兩個結局都記得更細**，🚫 不是把句子從嚴重度搬到發生率。
> **✅ 是本支自己的探針把這句話擋下來的**
> （「GI 那一對的配置差異沒有系統性方向」那一道判為綠）。

⚠️ 兩篇論文報的都是「**某分數以上的計次**」，但**分母不同**：
一篇是**時點**（8 人 × 6 時點 ＝ 48），一篇是**人數**（12 人）。
🚨 契約對 `gi-symptom-incidence` 沒有說分母是什麼。

## 🚨 而 `adjudicate()` 對這三篇都回報「沒有不一致」

⚠️ 它只收 `refsOnly*` 非空者；三篇的結局集合都完全相同，**佇列恆為 0。**
**🚫 A2「每一處不一致都要判明成因」因此對這一族是盲的。**

## ✅ 第三篇另外證實了一件事：**峰值那一型讀對了**

⚠️ 該篇同時報「整段平均」與「100 分鐘的峰值」，
✅ **論文自己寫明後者是 peak**；🚨 而兩位讀者都只映射了峰值，
**🚫 沒有人把平均當成峰值**——⚠️ 那正是第 557 輪立的第一型。

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

OUT = Path(__file__).resolve().parent / 'n596_allocation_replicates.json'
SHEET = ROOT / 'extraction-worksheet'
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

    rows, gi_direction = [], []
    for row in result['rows']:
        key = row['report']
        a, b = allocation(primary[key]), allocation(second[key])
        differs = {ref: [a.get(ref, 0), b.get(ref, 0)]
                   for ref in sorted(set(a) | set(b))
                   if a.get(ref, 0) != b.get(ref, 0)}
        rows.append({'report': key, 'refsBoth': row['refsBoth'],
                     'labelsBoth': row['both'],
                     'primaryAllocation': dict(a), 'secondAllocation': dict(b),
                     'allocationDiffers': differs})
        # 🚨 只看 GI 那一對，⚠️ 且只在兩者都出現時才算方向。
        if all(ref in a or ref in b for ref in GI):
            gi_direction.append({
                'report': key,
                'severity': [a.get(GI[0], 0), b.get(GI[0], 0)],
                'incidence': [a.get(GI[1], 0), b.get(GI[1], 0)],
                'secondLeansIncidence': (b.get(GI[1], 0) - a.get(GI[1], 0)) > 0
                and (b.get(GI[0], 0) - a.get(GI[0], 0)) < 0,
            })

    verdict = adjudicate(result, {})

    # 🚨 必觸發之反向：真有 refs 差異時，裁決機制會要求判成因。
    mutated = copy.deepcopy(second)
    victim = result['rows'][0]['report']
    for item in mutated[victim].get('reportedOutcomes') or []:
        if item.get('normalisedOutcomeRef'):
            item['normalisedOutcomeRef'] = 'muscle-glycogen-post-exercise'
            break
    try:
        adjudicate(agreement(primary, mutated), {})
        queue_fires = False
    except Exception:                            # noqa: BLE001
        queue_fires = True

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('雙讀已到 3 篇（必觸發）', result['comparedReports'] == 3,
          '🚨 少於 3 篇代表本輪的讀沒交回；實得 %d 篇'
          % result['comparedReports'])
    probe('A3 於三篇皆成立',
          result['refsOnlyPrimary'] == 0 and result['refsOnlySecond'] == 0
          and result['reportsFullyAgreed'] == result['comparedReports'],
          '✅ refsBoth=%d、只有一邊 %d／%d、逐篇一致 %d／%d'
          % (result['refsBoth'], result['refsOnlyPrimary'],
             result['refsOnlySecond'], result['reportsFullyAgreed'],
             result['comparedReports']))
    probe('裁決機制在真有 refs 差異時會動（必觸發之反向）', queue_fires,
          '🚨 換掉第二位的一個 outcomeId 後，adjudicate 確實要求判成因；'
          '⚠️ 否則「佇列為 0」可能只是它從不觸發')
    # 🚨 這一道會紅。
    differing = [r['report'] for r in rows if r['allocationDiffers']]
    probe('兩位讀者的配置一致', not differing,
          '🚨 三篇全部有配置差異：%s；⚠️ 而三篇的結局集合都相同，'
          '故 adjudicate() 的佇列是 0 —— **這一族它看不見**' % differing)
    # 🚨 這一道也會紅，而它問的是方向。
    leaning = [d['report'] for d in gi_direction if d['secondLeansIncidence']]
    probe('GI 那一對的配置差異沒有系統性方向',
          not (len(leaning) == len(gi_direction) and gi_direction),
          '🚨 %d 篇含 GI 的雙讀，%d 篇是同一方向（第二位偏發生率、'
          '正式偏嚴重度）；⚠️ 兩篇的正式讀者分屬不同頁，'
          '🚫 故這比較像契約沒把界線畫清楚，不像個別失誤'
          % (len(gi_direction), len(leaning)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'allocation-disagreement-replicates',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'agreement': {k: v for k, v in result.items()
                      if not isinstance(v, list)},
        'rows': rows,
        'giDirection': gi_direction,
        'adjudicationQueue': verdict,
        'blindSpot': (
            '🚨 adjudicate() 只收「一邊宣告了某契約結局，另一邊沒有」者。'
            '⚠️ 三篇的結局集合都完全相同，故佇列恆為 0，'
            '🚫 而三篇都有配置差異。'),
        'denominatorGap': (
            '⚠️ 兩篇論文報的都是「某分數以上的計次」，但分母不同：'
            '一篇是**時點**（8 人 × 6 時點 ＝ 48），一篇是**人數**（12 人）。'
            '🚨 契約對 gi-symptom-incidence 沒有說分母是什麼。'),
        'peakTypeReadCorrectly': (
            '✅ 第三篇同時報整段平均與 100 分鐘的峰值，而論文自己寫明後者是 peak；'
            '🚨 兩位讀者都只映射峰值，🚫 沒有人把平均當成峰值'
            '——⚠️ 那正是第 557 輪立的第一型。'),
        'independence': '✅ 本室三次動筆前都未看正式那道的清冊。',
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n596 配置不一致複現 ===')
    print('   比對 %d 篇｜refs 兩邊都有 %d／只有一邊 %d／%d｜逐篇一致 %d'
          % (result['comparedReports'], result['refsBoth'],
             result['refsOnlyPrimary'], result['refsOnlySecond'],
             result['reportsFullyAgreed']))
    for row in rows:
        print('   %s｜差異 %s' % (row['report'], row['allocationDiffers']))
    print('   GI 方向：%s' % gi_direction)
    print('   裁決佇列 disagreements=%s' % verdict.get('disagreements'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
