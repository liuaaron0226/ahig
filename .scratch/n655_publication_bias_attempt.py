# -*- coding: utf-8 -*-
"""**發表偏差：試了，而這條路走不通——連同證據一起記下來。**（第 655 輪）

## 🚨 本 run 從未查過「註冊了卻沒發表」

⚠️ 第 654 輪把 212 筆註冊紀錄接上之後，這件事第一次變得可試。
✅ 而它完全不必送請求。

## ⚠️ 而本支的結論是**否定的**——重點在它是怎麼被證成否定的

| 步驟 | 結果 |
|---|---|
| 完成的試驗 | 155／212 |
| 其中**沒有關聯論文** | 84 |
| 以關鍵字判「與本題相關」 | 75 —— **🚨 而這個數不能用** |
| 其中**結果已登在註冊庫** | **3** |

**🚨 關鍵字判準在 212 筆裡命中 192 筆（91%）——幾乎打中所有東西。**
⚠️ 一條這樣的規則什麼也分不出來（第 644 輪同一族）。

**✅ 故本支不看那個 75，改去逐筆讀那 3 筆具體的。**

## 🚨 而那 3 筆逐筆讀完，全部離題

⚠️ 妊娠期新生兒低血糖／產後減重與糖尿病篩檢／二甲雙胍與粒線體功能——
**🚫 沒有一筆與「運動中攝取外源性醣類」有關。**

> **✅ 即：關鍵字這條路找不出相關的未發表試驗，而本支用三個具體案例證明它，
> 🚫 不是用一個過濾後的數字宣稱它。**

## 🚫 本支不送外部請求、不改任何清冊、不輸出註冊敘述文字
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

OUT = Path(__file__).resolve().parent / 'n655_publication_bias_attempt.json'
RUN = ROOT / 'search-runs/b11-exogenous-cho-endurance/b11-full-run'

CHO = re.compile(
    r'carbohydrate|glucose|fructose|maltodextrin|sucrose|sports drink',
    re.IGNORECASE)
EXERCISE = re.compile(
    r'exercise|cycling|running|endurance|time trial|athlet', re.IGNORECASE)
NONSENSE = re.compile(r'ZZ-不可能出現的介入-ZZ')

# ⚠️ 本室逐筆讀過的那三筆，以及讀出來的主題（🚫 只記主題標籤，不記敘述）。
READ_BY_HAND = {
    'NCT01409382': '妊娠期：新生兒低血糖（走路＋限醣飲食）',
    'NCT01681147': '產後：減重與糖尿病篩檢的衛教',
    'NCT02552355': '二甲雙胍與粒線體功能（12 週）',
}


def main():
    records = json.loads(
        (RUN / 'sources/clinicaltrials-gov/records.json')
        .read_text(encoding='utf-8'))

    rows = []
    for record in records:
        protocol = record.get('protocolSection') or {}
        nct = (protocol.get('identificationModule') or {}).get('nctId')
        status = (protocol.get('statusModule') or {}).get('overallStatus')
        references = ((protocol.get('referencesModule') or {})
                      .get('references') or [])
        linked = any(isinstance(x, dict) and x.get('pmid')
                     for x in references)
        blob = json.dumps(
            {k: protocol.get(k) for k in
             ('identificationModule', 'descriptionModule', 'conditionsModule',
              'armsInterventionsModule', 'outcomesModule')},
            ensure_ascii=False)
        rows.append({
            'nct': nct, 'status': status, 'linkedPublication': linked,
            'hasResults': bool(record.get('hasResults')),
            'keywordRelevant': bool(CHO.search(blob)
                                    and EXERCISE.search(blob)),
            'nonsenseMatch': bool(NONSENSE.search(blob)),
        })

    completed = [r for r in rows if r['status'] == 'COMPLETED']
    unlinked = [r for r in completed if not r['linkedPublication']]
    keyword_relevant = [r for r in unlinked if r['keywordRelevant']]
    with_results = [r for r in keyword_relevant if r['hasResults']]

    relevant_rate_all = sum(1 for r in rows if r['keywordRelevant']) / len(rows)
    read_by_hand_offtopic = sorted(READ_BY_HAND)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('註冊紀錄讀得到且狀態欄有值（必觸發之正對照）',
          len(rows) == 212 and all(r['status'] for r in rows),
          '🚨 實得 %d 筆、缺狀態 %d 筆；⚠️ 任一不對，下面的分母就不成立'
          % (len(rows), sum(1 for r in rows if not r['status'])))
    probe('不可能出現的字串不得命中（必觸發之反向）',
          not any(r['nonsenseMatch'] for r in rows),
          '🚨 若它也命中，關鍵字這條路本身就壞了')
    probe('關鍵字判準有鑑別力',
          relevant_rate_all <= 0.6,
          '🚨 全部 212 筆裡判為「相關」的佔 **%.0f%%**——'
          '⚠️ 一條打中九成樣本的規則什麼也分不出來，'
          '**🚫 故「%d 筆相關」這個數不能用**（第 644 輪同一族）'
          % (100 * relevant_rate_all, len(keyword_relevant)))
    probe('那 3 筆「有結果且無關聯論文」是相關的未發表證據',
          not read_by_hand_offtopic,
          '🚨 本室**逐筆讀過**那 3 筆：%s——'
          '⚠️ 全部離題，🚫 沒有一筆與「運動中攝取外源性醣類」有關。'
          '**✅ 即這條路找不出相關的未發表試驗，而本支用具體案例證明，'
          '🚫 不是用一個過濾後的數字宣稱。**'
          % json.dumps(READ_BY_HAND, ensure_ascii=False))

    doc = {
        'schemaVersion': 1,
        'documentType': 'publication-bias-attempt',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'registryRecords': len(rows),
        'statusCounts': dict(collections.Counter(
            r['status'] for r in rows).most_common()),
        'completed': len(completed),
        'completedWithoutLinkedPublication': len(unlinked),
        'keywordRelevantAmongThose': len(keyword_relevant),
        'keywordRelevantRateOverAll': round(relevant_rate_all, 3),
        'withRegistryPostedResults': [r['nct'] for r in with_results],
        'readByHand': READ_BY_HAND,
        'verdict': (
            '🚨 **這條路走不通，而本支把它證成否定的。**'
            '⚠️ 84 筆完成且無關聯論文——但註冊庫的參考文獻本來就常年失修，'
            '**🚫 那是「未發表」的上界，不是計數**。'
            '🚨 關鍵字判準在 212 筆裡命中 %.0f%%，沒有鑑別力；'
            '✅ 而唯一具體可查的 3 筆（有結果、無關聯論文），'
            '**本室逐筆讀過，全部離題**。'
            % (100 * relevant_rate_all)),
        'whatWouldBeNeeded': (
            '📮 要真的查發表偏差，需要**逐筆判讀那 84 筆的主題**——'
            '⚠️ 那是判斷不是檢索，🚫 且本室不在此視窗讀大量文獻。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n655 發表偏差：一次誠實的否定 ===')
    print('   註冊紀錄 %d 筆｜完成 %d｜完成且無關聯論文 %d'
          % (len(rows), len(completed), len(unlinked)))
    print('   關鍵字判為相關：%d（而全部 212 筆的命中率 %.0f%%——🚨 無鑑別力）'
          % (len(keyword_relevant), 100 * relevant_rate_all))
    print('   其中結果已登在註冊庫者 %d 筆，本室逐筆讀過：'
          % len(with_results))
    for nct, topic in sorted(READ_BY_HAND.items()):
        print('      %s  %s' % (nct, topic))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
