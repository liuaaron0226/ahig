# -*- coding: utf-8 -*-
"""**那 5 篇「什麼都沒宣告」的，本室逐篇看過了。**（第 587 輪）

## ✅ 結論：**五篇全部是正當的零，讀的人都對**

第 586 輪點名 5 篇零宣告的論文，並說「該有人看一眼」。
**✅ 本輪本室自己看了**，🚫 沒有再把它推成一個待裁定事項。

| 報告 | 論文實際報的是什麼 | 對應到哪一型「差一點」 |
|---|---|---|
| `b9ab2f27317a6a2b` | 肌肉肝醣以**任意單位（AU）**分肌纖維型別報，且講的是**淨下降量** | **第六型**：利用量 ≠ 運動後濃度 |
| `4103c4b52bbf21e6` | **15 分鐘**全力計時賽，報**作功（kJ）／距離／平均速度** | **第四＋五型**：固定時間，報的不是完成時間 |
| `c97d2ed84b0d1057` | **15 分鐘**計時賽，報**總作功（kJ）** | **第四型**：固定時間報作功量 |
| `97c2233f7e60c801` | 外源碳水氧化以**第二小時的總克數／速率**報，🚫 未報峰值 | **第一型**：平均 ≠ 峰值 |
| `44243ac624c9b5e0` | 表現測驗是 **5 分鐘平均功率**測驗 | **第五型**：平均功率 ≠ 完成時間 |

> **🚨 也就是說：98 這個數字不因這五篇而偏低。**
> ✅ 五個讀的人各自遇到一種「差一點」，**五個都正確地沒有宣告。**

## 🚨 而第 586 輪那個警報，本支要自己收回一半

⚠️ 第 586 輪說「五篇全部命中結局詞彙」。**🚨 而 `44243ac624c9b5e0` 的 8 處
`time trial` 全部在參考文獻裡**——⚠️ 那正是全文詞彙底率會是 41／41 的原因。
**✅ 教訓：全文詞彙篩選必須排除參考文獻段落**，🚫 否則它量的是「這個領域引用了誰」。

## 🚨 而查這五篇時，撞到一件對 A2／A3 有用的事

`4103c4b52bbf21e6`（15 分鐘全力計時賽，報作功）→ **✅ 讀的人不宣告。**
`65d459b9129da800`（30 分鐘自訂配速計時賽，報平均功率）→ **🚨 讀的人宣告成
`tt-completion-time`**（n585 之「撤回」類，5 項）。

> **⚠️ 兩個視窗遇到同一種情形，給了相反的答案。**
> **✅ 而正確的那一個，產出的是一個「零」。**
> 🚨 這是本 run 第一個**跨視窗、同情境、可判定對錯**的一致性資料點——
> ⚠️ 它說的是：**產出為零的那次，比產出非零的那次更可信。**

## 🚫 本支不入輪次閘門；🚫 不引論文逐字
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n587_zero_declared_adjudication.json'

# ✅ 本 run 已立的六型（第 557／561／566／568 輪）。🚨 引用時只能用這六個鍵。
NEAR_MISS = {
    'mean-not-peak': '第一型：平均 ≠ 峰值（第 557 輪）',
    'three-min-all-out': '第二型：三分鐘全力測驗既不固定距離也不固定強度',
    'allowed-instrument-reports-power': '第三型：允許的工具，但報的是功率不是時間',
    'fixed-time-reports-work': '第四型：固定時間的試驗報作功量（第 561 輪）',
    'fixed-time-reports-power': '第五型：固定時間的試驗報功率（第 566 輪）',
    'glycogen-utilisation-not-concentration':
        '第六型：肝醣氧化／利用率 ≠ 運動後濃度（第 568 輪）',
}

ADJUDICATION = {
    'b9ab2f27317a6a2b': {
        'whatThePaperReports': '肌肉肝醣以任意單位（AU）分肌纖維型別呈現，'
                              '且陳述的是運動造成的**淨下降量**與試驗間差異。',
        'nearMiss': ['glycogen-utilisation-not-concentration'],
        'zeroIsCorrect': True,
        'alsoNote': '⚠️ 單位是 AU（組織化學），🚫 不是契約所要的濃度單位。',
    },
    '4103c4b52bbf21e6': {
        'whatThePaperReports': '兩小時騎乘後接 **15 分鐘**全力計時賽，'
                              '紀錄作功（kJ）、距離（km）與平均速度。',
        'nearMiss': ['fixed-time-reports-work', 'fixed-time-reports-power'],
        'zeroIsCorrect': True,
        'alsoNote': '🚨 固定的是**時間**，故沒有「完成時間」這個結果。',
    },
    'c97d2ed84b0d1057': {
        'whatThePaperReports': '**15 分鐘**計時賽，報三個條件的**總作功（kJ）**。',
        'nearMiss': ['fixed-time-reports-work'],
        'zeroIsCorrect': True,
        'alsoNote': None,
    },
    '97c2233f7e60c801': {
        'whatThePaperReports': '外源碳水氧化以**第二小時的總克數與速率**呈現；'
                              '⚠️ 全文出現「peak」之處是討論別人的研究，'
                              '🚫 不是本篇自己報的峰值。',
        'nearMiss': ['mean-not-peak'],
        'zeroIsCorrect': True,
        'alsoNote': '⚠️ 論文自述只取第二小時，因為該時段速率穩定——'
                    '🚨 那正是「不是峰值」的原因。',
    },
    '44243ac624c9b5e0': {
        'whatThePaperReports': '表現測驗是 **5 分鐘平均功率**測驗。',
        'nearMiss': ['fixed-time-reports-power'],
        'zeroIsCorrect': True,
        'alsoNote': '🚨 它的 8 處 `time trial` **全部在參考文獻裡**——'
                    '⚠️ 那正是全文詞彙底率會是 41／41 的原因。',
    },
}

# 🚨 同情境、相反答案：兩個視窗對「固定時間的計時賽」給了不同的處理。
CONTRADICTION = ('4103c4b52bbf21e6', '65d459b9129da800')


def main():
    in_scope = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        outcomes = doc.get('reportedOutcomes') or []
        in_scope[doc['report'][-16:]] = sum(
            1 for o in outcomes if (o.get('scopeDecision') or {}).get('inScope'))

    still_zero = {k: in_scope.get(k) for k in ADJUDICATION}
    unknown_types = sorted({t for v in ADJUDICATION.values()
                            for t in v['nearMiss'] if t not in NEAR_MISS})

    # 🚨 要比的是**讀的人宣告了什麼**，故來源是工作單的 draft，🚫 不是清冊——
    # ⚠️ 被擋在門口的那一筆根本沒有清冊，從清冊讀會得到 None，
    # ✅ 而那正是本支第三道探針第一次跑出來時抓到的事。
    sheet = ROOT / 'extraction-worksheet'
    declared = {}
    for path in ([sheet / 'drafts.json']
                 + sorted((sheet / 'drafts').glob('page-*.json'))):
        for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
            key = entry['report'][-16:]
            if key in CONTRADICTION:
                declared[key] = sum(
                    1 for o in (entry.get('reportedOutcomes') or [])
                    if o.get('normalisedOutcomeRef'))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('這五篇現在仍然是零（必觸發）',
          all(v == 0 for v in still_zero.values()),
          '🚨 若已經不是零，本份判讀就過期了，⚠️ 而過期的判讀看起來跟有效的一樣；'
          '實得 %s' % still_zero)
    probe('引用的「差一點」型別都在已立的六型裡（必觸發之反向）',
          not unknown_types,
          '🚨 打錯一個鍵就等於發明一個沒立過的型別；實得未知 %s' % (unknown_types or '無'))
    # 🚨 同情境相反答案：⚠️ 一個宣告了、一個沒有。若兩個都零或都非零，本節就不成立。
    left, right = CONTRADICTION
    probe('同情境相反答案確實存在（必觸發之反向）',
          declared.get(left) == 0 and (declared.get(right) or 0) > 0,
          '⚠️ %s 宣告 %s 項、%s 宣告 %s 項；🚨 若兩者相同，'
          '本支所稱的一致性資料點就不存在'
          % (left, declared.get(left), right, declared.get(right)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'zero-declared-adjudication',
        'question': '第 586 輪點名的 5 篇零宣告論文，零是不是正確的',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'answer': ('✅ 五篇全部是正當的零，讀的人都對。'
                   '🚨 故 98 這個數字不因這五篇而偏低。'),
        'nearMissVocabulary': NEAR_MISS,
        'adjudication': ADJUDICATION,
        'inScopeNow': still_zero,
        'retraction': (
            '🚨 第 586 輪說「五篇全部命中結局詞彙」——⚠️ 而其中一篇的命中'
            '**全部在參考文獻裡**。✅ 全文詞彙篩選必須排除參考文獻段落，'
            '🚫 否則它量的是「這個領域引用了誰」。'),
        'consistencyDatapoint': {
            'pair': list(CONTRADICTION),
            'situation': '固定**時間**的計時賽（15 分鐘／30 分鐘），'
                        '報的是作功或平均功率',
            'outcome': '⚠️ 一個視窗不宣告（✅ 正確），'
                       '🚨 另一個宣告成 tt-completion-time（❌ 錯，n585 之撤回類）',
            'lesson': '🚨 本 run 第一個跨視窗、同情境、可判定對錯的一致性資料點：'
                      '**產出為零的那一次，比產出非零的那一次更可信。**',
            'declaredCounts': declared,
        },
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n587 五篇零宣告論文之判讀 ===')
    print('   ✅ 結論：五篇全部是正當的零，讀的人都對')
    for key, item in ADJUDICATION.items():
        print('   %s｜%s' % (key, '／'.join(NEAR_MISS[t].split('：')[0]
                                            for t in item['nearMiss'])))
    print('   ── 同情境相反答案 ──')
    print('   %s 宣告 %s 項（✅ 正確地零）｜%s 宣告 %s 項（❌ 撤回類）'
          % (CONTRADICTION[0], declared.get(CONTRADICTION[0]),
             CONTRADICTION[1], declared.get(CONTRADICTION[1])))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
