# -*- coding: utf-8 -*-
"""**692 個被排除的結局，有沒有排錯的。**（第 621 輪）

## 🚨 本 run 從未查過這一塊

⚠️ 本室稽核過：進來的 98 項（n576／n590／n591／n597／n598）、
排除的**理由碼**（n588）、以及零貢獻的**論文**（n586）。
**🚫 但從未問過：那 692 個沒有宣告契約結局的項目，有沒有該宣告而沒宣告的。**

> **🚨 漏掉一個，和多收一個一樣糟——⚠️ 而漏掉的那個不會叫。**

## ✅ 做法：反過來用 n576 的邏輯

n576 問「**已宣告**的結局，標籤有沒有和它矛盾」。
**✅ 本支問相反的一面：⚠️「未宣告任何契約結局」的項目，
其標籤裡有沒有契約結局的**特徵詞**。**

⚠️ 詞彙取自契約六個結局的定義用語，🚫 不是同義詞聯想。

## 🚨 而這種掃描一定會有偽陽性

⚠️ 「muscle glycogen **oxidation**」含 glycogen 卻不是那個結局（第六型）；
🚨 「**mean** exogenous CHO oxidation」含 exogenous 卻不是峰值（第一型）。
**✅ 故本支同時掛上那六型的救援詞——🚫 而剩下的仍是「待人看」，不是「排錯了」。**
"""
import collections
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

OUT = Path(__file__).resolve().parent / 'n621_out_of_scope_audit.json'

# ✅ （契約結局, 特徵詞, 救援詞——命中則不算漏）
SIGNALS = [
    ('tt-completion-time',
     r'time[- ]trial|completion time',
     # 🚨 抽樣後補：⚠️ 提到計時賽的**別的**結局（心率、RPE、相關）不是完成時間。
     r'\bpower\b|work (done|completed)|\bkJ\b|pacing|speed|distance covered'
     r'|familiari[sz]ation|heart rate|perceived exertion|\bRPE\b'
     r'|temperature|correlation|associat'),
    ('time-to-exhaustion',
     r'time to exhaustion|exercise capacity|until exhaustion',
     # 🚨 抽樣後補：⚠️「在力竭當下量的血中代謝物」不是力竭時間。
     r'\bpower output\b|distance|concentration|plasma|blood|lactate'
     r'|glucose|glycerol|NEFA|hydroxybutyrate|order effect|familiari[sz]'),
    ('exogenous-cho-oxidation-peak',
     r'exogenous carbohydrate oxidation|exogenous cho oxidation',
     r'\bmean\b|\baverage\b|total|efficiency|endogenous|absolute'
     r'|time at which|at \d+\s*min|second hour'),
    ('muscle-glycogen-post-exercise',
     r'muscle glycogen|glycogen concentration',
     # 🚨 抽樣後補：⚠️「分肌纖維型別的染色光密度」單位不同，不是濃度；
     # ⚠️「相對百分比下降」與「對總能量的貢獻」是利用量，不是運動後濃度。
     r'oxidation|utilisation|utilization|breakdown|use\b|sparing'
     r'|pre-exercise|before exercise|baseline|depletion protocol'
     r'|optical density|stain|fibre type|fiber type|percentage reduction'
     r'|contribution'),
    ('gi-symptom-severity',
     r'gastrointestinal|stomach|nausea|bloat|cramp|reflux|flatulence',
     r'incidence|number of|proportion|counted|questionnaire administered'),
    ('gi-symptom-incidence',
     r'incidence of|number of (participants|subjects) reporting',
     r'\bscore\b|severity'),
]


def main():
    scanned = 0
    flagged = []
    by_report = collections.Counter()
    by_outcome = collections.Counter()
    labels = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        report = doc['report'][-16:]
        for item in doc.get('reportedOutcomes') or []:
            if item.get('normalisedOutcomeRef'):
                continue          # ⚠️ 已宣告者不在本支範圍
            scanned += 1
            label = item.get('localLabel') or ''
            labels.append(label)
            for outcome_id, signal, rescue in SIGNALS:
                if not re.search(signal, label, re.I):
                    continue
                if rescue and re.search(rescue, label, re.I):
                    continue
                flagged.append({'report': report, 'outcomeId': outcome_id,
                                'label': label[:120]})
                by_report[report] += 1
                by_outcome[outcome_id] += 1
                break

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    # 🚨 第一版寫 692，探針立刻亮紅——⚠️ 而 692 是「不在範圍內」的總數，
    # 其中 656 項**完全未宣告**、另 36 項**宣告了但被排除**。
    # ✅ 本支要查的是前者：🚫「宣告了但被排除」已由 n588 的理由碼稽核涵蓋。
    probe('掃到的是「完全未宣告」那 656 項（必觸發）', scanned == 656,
          '🚨 對不上就代表本支看的不是同一批；實得 %d 項'
          '（⚠️ 692 ＝ 656 未宣告 ＋ 36 宣告後被排除）' % scanned)
    # 🚨 必觸發之反向：⚠️ 特徵詞必須真的在某些標籤上命中。
    raw_hits = sum(1 for label in labels
                   for _o, signal, _r in SIGNALS
                   if re.search(signal, label, re.I))
    probe('特徵詞在未宣告的標籤上打得中（必觸發之反向）',
          raw_hits > 0,
          '✅ 未套救援詞前命中 %d 次；🚨 若為零，代表詞彙壞了，'
          '而「沒有漏掉」會是假的' % raw_hits)
    # ⚠️ 救援詞必須真的擋掉一部分，否則它沒有作用。
    probe('救援詞確實擋掉了一部分（必觸發之反向）',
          len(flagged) < raw_hits,
          '⚠️ 命中 %d 次 → 救援後剩 %d 項；🚨 若一項都沒擋掉，'
          '代表那六型的救援詞沒有生效' % (raw_hits, len(flagged)))
    # 🚨 這一道的紅綠就是答案。
    probe('沒有「未宣告卻帶著契約結局特徵詞」的項目',
          not flagged,
          '🚨 實得 %d 項，分布 %d 篇；按結局：%s；'
          '⚠️ 這是**待人看**的清單，🚫 不是「排錯了」的清單'
          % (len(flagged), len(by_report), dict(by_outcome)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'out-of-scope-audit',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'outOfScopeScanned': scanned,
        'rawSignalHits': raw_hits,
        'flaggedAfterRescue': len(flagged),
        'byOutcome': dict(by_outcome),
        'byReport': dict(by_report.most_common(10)),
        'flagged': flagged[:40],
        'whatThisIsNot': (
            '🚫 不是「排錯了」的清單——⚠️ 這種掃描一定有偽陽性：'
            '「muscle glycogen oxidation」含 glycogen 卻不是那個結局（第六型），'
            '「mean exogenous oxidation」含 exogenous 卻不是峰值（第一型）。'
            '✅ 六型的救援詞已掛上，🚨 而剩下的仍要人看。'),
        'whyItMatters': (
            '🚨 本 run 稽核過進來的 98 項、排除的理由碼、零貢獻的論文，'
            '🚫 但從未問過那 692 項有沒有該宣告而沒宣告的。'
            '⚠️ 漏掉一個和多收一個一樣糟——**而漏掉的那個不會叫。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n621 被排除的那 692 項 ===')
    print('   掃描 %d 項｜特徵詞命中 %d 次｜✅ 救援後待人看 %d 項'
          % (scanned, raw_hits, len(flagged)))
    print('   按結局：%s' % dict(by_outcome))
    print('   最多的幾篇：%s' % dict(by_report.most_common(5)))
    for row in flagged[:8]:
        print('   🚨 %s｜%s｜%s' % (row['report'], row['outcomeId'],
                                   row['label'][:70]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
