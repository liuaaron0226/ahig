# -*- coding: utf-8 -*-
"""**第四篇雙讀：獨立證實 n598，並撞出兩件新的。**（第 608 輪）

## ✅ 挑這一篇是為了檢驗本室自己的指控

n598 說 `65dd82a89b2c5340` 有 **7 項**在範圍內的結局，座標指向**方法段**。
**⚠️ 那是本室對另一個視窗的指控。✅ 故本輪獨立再讀一次同一篇。**

## 🚨 一、獨立讀的結果證實了它

| | 正式那道 | **第二位（本室）** |
|---|---|---|
| 契約結局 | `gi-symptom-severity` ×7 | `gi-symptom-severity` ×4 |
| **宣告項的來源段落** | **`Gastrointestinal discomfort` ×7** | **`Interaction effects (time x treatment)` ×4** |

> **✅ refs 集合相同**（A3 再次成立）；
> **🚨 而兩位讀者去拿數字的地方完全不同。**
> ⚠️ 那 199 字的 `Gastrointestinal discomfort` 是**方法**：
> 「以 100 mm 視覺類比量表評 …」，🚫 沒有任何結果。

## 🚨 二、撞出一個新的契約缺口：**論文報的是「條件間的百分比差」**

⚠️ 該篇寫的是「腹絞痛高 **9.3%**」「飽脹高 **9.9%**」——
**🚨 而契約的 `inScopeEffectMeasures`（MD／SMD／RR／RD／mean／proportion）
沒有一個詞是「條件間的百分比差」。**

> ⚠️ 正式那道填 `mean`；本室填 `MD`。**🚫 兩者都不精確，而兩者都通過了判定。**
> **🚨 也就是說：那一軸把一個表達不出來的東西安靜地吸收掉了。**

⚠️ 劑量也不同：正式那道逐臂記（60 與 90 g/h），本室記暴露臂（90）並在標籤註明對照臂。
**✅ 兩者都說得通**——🚨 但合成時它們不是同一種東西。

## 🚨 三、守衛擋下了一次**合法的新增**

`write_page_drafts` 拒絕「同頁異容」。⚠️ 而本次是**新增第二篇**，
**既有那一筆逐位元組未動**——🚫 守衛分不出「新增」與「改寫」。

> ⚠️ 而第二線本來就是**一次讀一篇**，而一頁最多五篇。
> **🚫 本室不繞過守衛**：✅ 讀出來的那份暫存於私有根
> `extraction-worksheet/second-pending/`，📮 待裁定。

## 🚫 本支不入輪次閘門
"""
import json
import os
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n608_fourth_double_read.json'
SHEET = ROOT / 'extraction-worksheet'
PENDING = (SHEET / 'second-pending'
           / 'page-014-with-65dd82a89b2c5340.json')
REPORT = '65dd82a89b2c5340'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')


def declared(entry):
    return [o for o in entry['reportedOutcomes'] if o.get('normalisedOutcomeRef')]


def main():
    primary = None
    for path in ([SHEET / 'drafts.json']
                 + sorted((SHEET / 'drafts').glob('page-*.json'))):
        for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
            if entry['report'][-16:] == REPORT:
                primary = entry
    second = [e for e in json.loads(PENDING.read_text(encoding='utf-8'))['entries']
              if e['report'][-16:] == REPORT][0]

    a, b = declared(primary), declared(second)
    refs_a = Counter(o['normalisedOutcomeRef'] for o in a)
    refs_b = Counter(o['normalisedOutcomeRef'] for o in b)
    sec_a = Counter((o.get('sourceLocation') or {}).get('section') for o in a)
    sec_b = Counter((o.get('sourceLocation') or {}).get('section') for o in b)
    measures = {'primary': sorted({o.get('effectMeasure') for o in a}),
                'second': sorted({o.get('effectMeasure') for o in b})}
    doses = {'primary': sorted({o.get('dose') for o in a}),
             'second': sorted({o.get('dose') for o in b})}

    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    allowed_measures = contract.get('inScopeEffectMeasures') or []

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩份都讀到了同一篇（必觸發）',
          bool(a) and bool(b),
          '🚨 少一邊就沒有比較；實得正式 %d 項、第二位 %d 項' % (len(a), len(b)))
    probe('A3 於本篇成立：契約結局集合相同',
          set(refs_a) == set(refs_b),
          '✅ 正式 %s｜第二位 %s' % (dict(refs_a), dict(refs_b)))
    # 🚨 這一道會紅，而它獨立證實了 n598。
    probe('兩位讀者的來源段落一致',
          set(sec_a) == set(sec_b),
          '🚨 正式全部指向 %s（方法段），第二位全部指向 %s（結果段）；'
          '⚠️ 一位獨立的讀者去拿數字時，去的是另一個地方——'
          '✅ 這獨立證實了 n598'
          % (list(sec_a), list(sec_b)))
    # 🚨 這一道也會紅：⚠️ 契約沒有這個詞。
    probe('論文所報的效應量在契約詞彙裡有對應',
          False,
          '🚨 該篇報的是「條件間的百分比差」，而契約收的是 %s——'
          '⚠️ 沒有一個詞是它。正式那道填 %s、本室填 %s，'
          '🚫 兩者都不精確而兩者都通過了判定'
          % (allowed_measures, measures['primary'], measures['second']))
    # 🚨 守衛擋下合法新增。
    probe('第二線的讀已交回', False,
          '🚨 write_page_drafts 拒絕同頁異容，⚠️ 而本次是**新增一篇**、'
          '既有那一筆逐位元組未動；🚫 本室不繞過守衛，'
          '✅ 暫存於 %s' % PENDING.parent.name)

    doc = {
        'schemaVersion': 1,
        'documentType': 'fourth-double-read',
        'report': REPORT,
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'refs': {'primary': dict(refs_a), 'second': dict(refs_b),
                 'setsEqual': set(refs_a) == set(refs_b)},
        'sourceSections': {'primary': dict(sec_a), 'second': dict(sec_b)},
        'effectMeasures': measures,
        'doses': doses,
        'contractEffectMeasures': allowed_measures,
        'confirmsN598': (
            '✅ 一位獨立讀者去拿 GI 數字時，去的是 Interaction effects 段，'
            '🚨 而正式那道的 7 項全部指向 199 字的方法段。'
            '⚠️ 那一段只描述量表，🚫 沒有任何結果。'),
        'newContractGap': (
            '🚨 該篇把 GI 差異報成**條件間的百分比差**，'
            '⚠️ 而契約的效應量詞彙沒有一個是它。'
            '🚫 兩位讀者各填了 mean 與 MD，兩者都不精確而都通過了判定——'
            '✅ 那一軸把一個表達不出來的東西安靜地吸收掉了。'),
        'doseConventionDiffers': (
            '⚠️ 正式那道逐臂記（60 與 90 g/h），本室記暴露臂（90）並註明對照臂。'
            '✅ 兩者都說得通，🚨 但合成時它們不是同一種東西。'),
        'guardBlockedLegitimateAppend': (
            '🚨 write_page_drafts 拒絕同頁異容——⚠️ 而本次是新增第二篇，'
            '既有那一筆逐位元組未動。🚫 守衛分不出「新增」與「改寫」，'
            '而第二線本來就是一次讀一篇、一頁最多五篇。'
            '✅ 本室不繞過，讀出來的那份暫存待裁定。'),
        'pendingFile': str(PENDING),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n608 第四篇雙讀 ===')
    print('   契約結局：正式 %s｜第二位 %s（集合相同 %s）'
          % (dict(refs_a), dict(refs_b), set(refs_a) == set(refs_b)))
    print('   🚨 來源段落：正式 %s｜第二位 %s' % (list(sec_a), list(sec_b)))
    print('   效應量：正式 %s｜第二位 %s｜契約 %s'
          % (measures['primary'], measures['second'], allowed_measures))
    print('   劑量：正式 %s｜第二位 %s' % (doses['primary'], doses['second']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
