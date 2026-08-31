# -*- coding: utf-8 -*-
"""**在範圍內的那 98 項，標籤與它宣告的結局互相矛盾嗎。**（第 576 輪）

## 🚨 為什麼要掃

第 575 輪那道驗收守衛擋下三篇，其中一篇是**對應錯**而不是命名錯：
它把「**Mean power output** during the 30 min self-paced time trial」宣告成
`tt-completion-time`。⚠️ 那一次是**碰巧**被抓到的——
**🚨 守衛查的是儀器名，而它剛好也沒有允許的儀器可填。**

> **⚠️ 若同一種錯誤發生在一個「儀器名剛好填對」的項目上，它會一路通過。**
> **🚨 而 41 篇裡有 37 篇不是本室讀的。**

## ✅ 掃什麼：本 run 已經立過的那幾條分辨

| 宣告的結局 | 🚨 標籤裡出現這些字就矛盾 |
|---|---|
| `tt-completion-time`（完成**時間**） | power／work done／作功量 |
| `time-to-exhaustion`（力竭**時間**） | power output／distance covered |
| `exogenous-cho-oxidation-peak`（**峰值**） | mean／average（且無 peak／maximal／highest） |
| `muscle-glycogen-post-exercise`（**濃度**） | oxidation／utilisation／breakdown |
| `gi-symptom-incidence`（**發生率**） | score（且無 incidence／prevalence／proportion／%） |
| `gi-symptom-severity`（**嚴重度**） | incidence／prevalence／proportion of participants |

## 🚨 第一版命中的七項，全部是偽陽性——而那個型態本身要記下來

⚠️ 第一版規則沒有救援詞，七項全中而**一項都不是真的矛盾**：
「Time-trial **completion time** for a fixed 6 kJ/kg of **work**」被 work 打中；
「**Number of participants** reporting a … **score** of 5 or above」被 score 打中。

> **🚨 更要緊的是：被打中的七項裡有三項，正是讀的人**明白寫出那個分辨**才中的**——
> 例如「fixed amount of work completed as quickly as possible, **not a fixed
> distance**」、「the paper calls this an 'incidence' but reports it as a
> **score**」。
> **⚠️ 也就是說：這種關鍵字掃描會罰認真標註的人，而放過寫得含糊的人。**
> ✅ 已補救援詞；🚨 但那個型態是本支的固有限制，不是可以修掉的東西。

## 🚨 補救援詞時，本支自己犯了一次同一族的錯

⚠️ 改規則的那一步，word boundary 被塌成 **0x08（backspace）**，
三條規則的邊界成了看不見的控制字元，**🚫 它們一次都沒真的跑過**。
🚨 而畫面上命中數從 7 掉到 1，**看起來像是修好了**。
> ✅ 已補一道**當初就會亮紅燈**的探針：`每條規則的字面都乾淨且編得起來`。
> **⚠️ 舊的 canary 只試第一條規則，而第一條剛好沒有反斜線——故它抓不到。**

## 🚨 這一支能做什麼、不能做什麼

- ✅ 能：把**明白寫在標籤裡**的矛盾找出來，逐項列出待人看。
- 🚨 不能：判定對錯。⚠️ 標籤是自由文字，**一個沒寫「mean」的平均值它抓不到**；
  **🚫 故「零命中」不代表沒有對應錯誤。**
- 🚨 不能：看論文。⚠️ 它只讀清冊。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n576_mapping_contradictions.json'

# (宣告的結局, 矛盾詞, 若標籤另含這些字則不算矛盾, 說明)
RULES = [
    ('tt-completion-time', r'\bpower\b', None,
     '完成時間 vs 功率——第 566 輪之第五型'),
    # 🚨 第一版此條無救援詞——「fixed 6 kJ/kg of work 的計時賽」被 work 打中。
    ('tt-completion-time', r'work (done|completed)|\bkJ\b',
     r'completion time|time to complete',
     '完成時間 vs 作功量——第 561 輪之第四型'),
    ('time-to-exhaustion', r'\bpower output\b|distance covered', None,
     '力竭時間 vs 功率／距離'),
    ('exogenous-cho-oxidation-peak', r'\bmean\b|\baverage\b',
     r'\bpeak\b|\bmaximal\b|\bhighest\b',
     '峰值 vs 平均——第 557 輪之第一型'),
    ('muscle-glycogen-post-exercise', r'oxidation|utilisation|utilization|breakdown',
     None, '濃度 vs 氧化／利用——第 568 輪之第六型'),
    ('muscle-glycogen-post-exercise', r'pre-exercise|before exercise|baseline',
     None, '運動**後** vs 運動前'),
    ('gi-symptom-incidence', r'\bscore',
     r'incidence|prevalence|proportion|%|number of'
     r'|participants experiencing|counted',
     '發生率 vs 分數'),
    ('gi-symptom-severity', r'incidence|prevalence|proportion of participants',
     r'\bscore|\bscale\b', '嚴重度 vs 發生率'),
]


def main():
    root = ROOT / 'extraction'
    files = sorted(p for p in root.rglob('inventory-*.json')
                   if 'batches' not in str(p))

    in_scope, flags = 0, []
    for path in files:
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        for item in doc.get('reportedOutcomes') or []:
            decision = item.get('scopeDecision') or {}
            if not decision.get('inScope'):
                continue
            in_scope += 1
            ref = item.get('normalisedOutcomeRef')
            label = item.get('localLabel') or ''
            for outcome_id, bad, rescue, why in RULES:
                if ref != outcome_id:
                    continue
                if not re.search(bad, label, re.I):
                    continue
                if rescue and re.search(rescue, label, re.I):
                    continue
                flags.append({'report': report, 'outcomeId': ref,
                              'label': label[:130], 'matched': bad, 'why': why})

    by_report = sorted({f['report'] for f in flags})
    by_rule = {}
    for f in flags:
        by_rule[f['why']] = by_rule.get(f['why'], 0) + 1

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的掃到在範圍內的項目（必觸發）', in_scope > 0,
          '🚨 若為零，代表篩選條件寫錯，而「無矛盾」會是假的；實得 %d 項'
          % in_scope)
    # 🚨 這道探針是**第 576 輪自己觸發的**，不是預想出來的：
    # ⚠️ 補救援詞時，heredoc 把 word boundary 塌成了 **0x08（backspace）**，
    # 三條規則的邊界變成一個看不見的控制字元，**🚫 於是它們一次都沒真的跑過**——
    # 而輸出看起來完全正常（命中數還「變少」了，像是修好了）。
    # 🚨 舊的 canary 只試 RULES[0]（該條沒有反斜線），**故它抓不到**。
    malformed = []
    for outcome_id, bad, rescue, _why in RULES:
        for pattern in (bad, rescue):
            if pattern and any(ord(c) < 32 for c in pattern):
                malformed.append((outcome_id, repr(pattern)))
        try:
            re.compile(bad)
            if rescue:
                re.compile(rescue)
        except re.error as exc:
            malformed.append((outcome_id, 'compile: %s' % exc))
    probe('每條規則的字面都乾淨且編得起來（必觸發之反向）', not malformed,
          '🚨 控制字元會讓規則永遠不命中，而「零命中」看起來像是沒問題；'
          '實得壞掉的規則 %d 條%s'
          % (len(malformed),
             ''.join('｜%s %s' % m for m in malformed)))

    # 必觸發之反向：拿一個一定會命中的樣本試規則本身。
    canary = re.search(RULES[0][1], 'Mean power output during the time trial',
                       re.I)
    probe('規則本身打得中（必觸發之反向）', bool(canary),
          '🚨 以合成樣本「Mean power output…」試第一條規則；打不中代表規則壞了')
    probe('沒有任何在範圍內的項目與其宣告矛盾', not flags,
          '待人看的有 %d 項／%d 篇' % (len(flags), len(by_report)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'mapping-contradiction-scan',
        'ruling': '第 575 輪：守衛碰巧抓到一個對應錯，而它不是為此設計的',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inventories': len(files),
        'inScopeItemsScanned': in_scope,
        'rules': [{'outcomeId': o, 'contradictoryPattern': b,
                   'rescuePattern': r, 'why': w} for o, b, r, w in RULES],
        'flagged': flags,
        'flaggedByRule': by_rule,
        'flaggedReports': by_report,
        'whatThisCannotDo': [
            '🚨 判定對錯——⚠️ 這是待人看的清單，不是錯誤數。',
            '🚨 抓到沒寫在標籤裡的矛盾。⚠️ 標籤是自由文字；'
            '一個沒寫 mean 的平均值它抓不到，🚫 故零命中不代表沒有對應錯誤。',
            '🚨 看論文——⚠️ 它只讀清冊。',
        ],
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n576 在範圍內項目之對應矛盾掃描 ===')
    print('   清冊 %d 份｜掃過在範圍內 %d 項' % (len(files), in_scope))
    print('   🚨 待人看：%d 項，分布 %d 篇' % (len(flags), len(by_report)))
    for f in flags:
        print('\n   🚨 %s｜宣告 %s' % (f['report'], f['outcomeId']))
        print('      %s' % f['why'])
        print('      標籤：%s' % f['label'])
    print('\n   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
