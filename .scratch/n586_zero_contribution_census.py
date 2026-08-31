# -*- coding: utf-8 -*-
"""**41 篇裡有幾篇其實一項證據都沒貢獻，為什麼。**（第 586 輪）

## 🚨 數字：38 份清冊、98 項在範圍內——**而 13 篇貢獻 0 項**

⚠️ 「41 篇讀完」這句話一直被拿來當進度。**🚨 但實際在供給證據的只有 25 篇。**

| 貢獻 0 項的原因 | 篇數 |
|---|---|
| **🚨 一個契約結局都沒宣告** | **5** |
| 劑量不在帶內（含「論文沒報劑量」） | 5 |
| 效應量不在範圍 | 2 |
| 儀器名不在允許清單 | 1 |

## 🚨 那 5 篇「什麼都沒宣告」的，論文裡**都有那些字**

⚠️ 讀的人為它們記了 10–37 個結局，**卻一個都沒對應到契約**。
✅ 本支對它們做一件便宜的事：**去全文裡找在範圍內結局的詞彙**。

> **🚨 五篇全部命中，而其中三篇的段落標題本身就是在範圍內的結局。**
> ⚠️ 一篇有 31 處提到肌肉肝醣，另一篇有 26 處提到計時賽。

**🚫 這不證明它們該有結局。** ⚠️ 本 run 已經立過六種「差一點」，
🚨 而它們每一種都會讓一篇滿是那些字的論文**正當地**貢獻 0 項：

- 肌肉肝醣的**氧化率**不是運動後**濃度**（第 568 輪之第六型）
- 外源碳水氧化的**平均**不是**峰值**（第 557 輪之第一型）
- 計時賽可能只是**熟悉化**，或報的是功率不是時間（第 566 輪之第五型）

> **✅ 故本支給的是「該有人看一眼」的清單，🚫 不是「讀錯了」的清單。**
> **🚨 但零宣告 ＋ 段落標題就是結局，這個組合不該沒人問過。**

## ✅ 這個詞彙篩選必須有正對照，否則它自證不了

⚠️ 若詞彙樣式根本打不中東西，「五篇都命中」與「樣式壞了」畫面一樣——
🚨 **反過來也一樣**：若它對**每一篇**都命中，那它什麼都沒說。
**✅ 故本支同時量：有貢獻的那 25 篇裡，有幾篇也命中。**

## 🚫 本支不入輪次閘門
"""
import json
import re
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction import corpus  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n586_zero_contribution_census.json'

# ⚠️ 詞彙取自契約的結局名稱，🚫 不是本室另想的同義詞。
VOCAB = {
    'tt-completion-time': r'time[- ]trial',
    'time-to-exhaustion': r'time to exhaustion|exercise capacity|until exhaustion',
    'exogenous-cho-oxidation-peak': r'exogenous carbohydrate oxidation',
    'muscle-glycogen-post-exercise': r'muscle glycogen',
    'gi-symptom': r'gastrointestinal|GI symptom',
}


def screen(candidate):
    doc = corpus.load_document(candidate)
    text = doc.content
    hits = {name: len(re.findall(pattern, text, re.I))
            for name, pattern in VOCAB.items()}
    titles = [str(section.title) for section in doc.sections
              if any(re.search(pattern, str(section.title or ''), re.I)
                     for pattern in VOCAB.values())]
    return {k: v for k, v in hits.items() if v}, titles


def main():
    ids = {c[-16:]: c for c in corpus.acquired_roster()[0]}

    rows = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        key = doc['report'][-16:]
        outcomes = doc.get('reportedOutcomes') or []
        declared = [o for o in outcomes if o.get('normalisedOutcomeRef')]
        in_scope = [o for o in outcomes
                    if (o.get('scopeDecision') or {}).get('inScope')]
        reasons = Counter((o.get('scopeDecision') or {}).get('reasonCode')
                          for o in declared
                          if not (o.get('scopeDecision') or {}).get('inScope'))
        rows.append({'report': key, 'inScope': len(in_scope),
                     'declared': len(declared), 'outcomes': len(outcomes),
                     'reasons': dict(reasons)})

    zero = [r for r in rows if r['inScope'] == 0]
    nothing_declared = [r for r in zero if r['declared'] == 0]
    contributing = [r for r in rows if r['inScope'] > 0]

    for row in nothing_declared:
        hits, titles = screen(ids[row['report']])
        row['vocabularyHits'] = hits
        # 🚨 段落標題本身就是在範圍內的結局——⚠️ 那比全文出現次數強得多。
        row['sectionTitlesMatching'] = len(titles)

    # ✅ 正對照與特異度：有貢獻的那些，命中率是多少。
    control_hits = 0
    for row in contributing:
        hits, _ = screen(ids[row['report']])
        if hits:
            control_hits += 1

    flagged = [r for r in nothing_declared if r['vocabularyHits']]
    with_titles = [r for r in nothing_declared if r['sectionTitlesMatching']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    total_in_scope = sum(r['inScope'] for r in rows)
    probe('清冊與在範圍內總數與既有紀錄相符（必觸發）',
          len(rows) == 38 and total_in_scope == 98,
          '🚨 對不上就代表本支讀到的不是同一批資料；實得清冊 %d 份／在範圍內 %d 項'
          % (len(rows), total_in_scope))
    probe('詞彙樣式在有貢獻的論文上打得中（正對照，必觸發）',
          control_hits > 0,
          '✅ 有貢獻的 %d 篇裡 %d 篇也命中；🚨 若為零，代表樣式壞了，'
          '而「五篇都命中」會是假的' % (len(contributing), control_hits))
    # 🚨 全文詞彙在這種語料裡幾乎人人都有，⚠️ 故「五篇都命中」本身分辨力很低。
    # ✅ 真正較強的訊號是**段落標題就是結局**。
    # 🚨 而那要成立，它就必須比全文詞彙**更少見**——⚠️ 否則它什麼都沒多說。
    text_rate = sum(1 for k in ids if screen(ids[k])[0])
    title_rate = sum(1 for k in ids if screen(ids[k])[1])
    probe('段落標題這個較強的訊號，確實比全文詞彙少見',
          title_rate < text_rate,
          '⚠️ 41 篇中全文命中 %d 篇、段落標題命中 %d 篇。'
          '🚨 若兩者相同，標題這一條就沒有增添任何分辨力，'
          '✅ 而本支的結論正是靠它'
          % (text_rate, title_rate))
    # 🚨 這一道會紅，而它問的是一件確定的事。
    probe('沒有「零宣告卻滿是結局詞彙」的論文', not flagged,
          '🚨 實得 %d 篇零宣告者全部命中結局詞彙，其中 %d 篇的**段落標題**'
          '本身就是在範圍內的結局；⚠️ 這個組合不該沒人問過'
          % (len(flagged), len(with_titles)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'zero-contribution-census',
        'question': '41 篇裡有幾篇其實一項證據都沒貢獻，為什麼',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inventories': len(rows),
        'inScopeTotal': total_in_scope,
        'contributingReports': len(contributing),
        'zeroContributionReports': len(zero),
        'zeroBecauseNothingDeclared': len(nothing_declared),
        'zeroReasonFamilies': dict(Counter(
            '+'.join(sorted(r['reasons'])) or 'nothing-declared'
            for r in zero)),
        'vocabularyScreen': {
            'whatItIs': ('✅ 去全文找在範圍內結局的詞彙。🚫 不是判定——'
                         '⚠️ 本 run 立過的六種「差一點」，每一種都會讓'
                         '一篇滿是那些字的論文**正當地**貢獻 0 項。'),
            'controlHitsAmongContributing': control_hits,
            'contributingReports': len(contributing),
            'flagged': len(flagged),
            'flaggedWithMatchingSectionTitles': len(with_titles),
            # 🚨 底率必須跟著結論一起走，⚠️ 否則「五篇全部命中」會被讀成強證據。
            'baseRateFullTextHits': '%d/41' % text_rate,
            'baseRateSectionTitleHits': '%d/41' % title_rate,
            'howToReadThis': (
                '🚨 全文詞彙是 41／41——⚠️ 故「五篇全部命中」本身幾乎沒有訊息量。'
                '⚠️ 段落標題是 %d／41，也不算罕見。'
                '✅ 真正該看一眼的理由是那個**組合**：'
                '讀的人為這篇記了 10–37 個結局，🚨 卻一個契約結局都沒對應。'
                '🚫 本支分不出「正當地零」與「漏掉了」——'
                '⚠️ 本 run 立過的六種「差一點」每一種都會造成正當的零。'
                % title_rate),
        },
        'zeroRows': zero,
        'allRows': rows,
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n586 貢獻為零的論文 ===')
    print('   清冊 %d 份｜在範圍內 %d 項｜✅ 有貢獻 %d 篇｜🚨 貢獻 0 項 %d 篇'
          % (len(rows), total_in_scope, len(contributing), len(zero)))
    print('   零貢獻之原因分布：%s' % doc['zeroReasonFamilies'])
    print('   ── 零宣告的那幾篇，論文裡有沒有那些字 ──')
    for row in nothing_declared:
        print('   🚨 %s｜宣告 0／結局 %2d｜詞彙 %s｜段落標題命中 %d'
              % (row['report'], row['outcomes'], row['vocabularyHits'],
                 row['sectionTitlesMatching']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
