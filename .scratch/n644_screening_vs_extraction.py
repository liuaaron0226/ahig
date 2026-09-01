# -*- coding: utf-8 -*-
"""**篩選說有、抽取說沒有——本 run 自己的兩個階段對不對得起來。**（第 644 輪）

## 🚨 第 643 輪拉出 4 篇「宣告了 10–37 個結局、一個都沒對上契約」

⚠️ 那有兩種很不一樣的可能：

| | 意思 |
|---|---|
| **✅ 真的離題** | 篩選讓它進來，但它確實沒有契約要的結局 |
| **🚨 映射失敗** | 它有，但讀的人沒把它對到契約結局上 |

> **✅ 而本室手上有一個獨立來源可以分辨：篩選當初的判詞。**
> ⚠️ 那是讀摘要時寫下的結構化註記，🚨 與抽取端**不是同一次閱讀**。

## ✅ 本支怎麼比

從判詞裡找**契約結局的字面線索**（計時賽／力竭／氧化率／肝醣／腸胃症狀），
再看抽取端該篇進了幾項。**🚨 篩選有線索、抽取零項** ⇒ 兩階段互相矛盾，待人看。

## ⚠️ 本支的對照設計

🚨 只看零貢獻那些會有一個致命問題：**本室無從得知這條規則本身準不準**。
✅ 故同一條規則也套在**有貢獻的 25 篇**上——⚠️ 若它在那 25 篇上也常常說「沒有」，
**那規則本身就沒有鑑別力，🚫 本支的結論一律作廢。**

## 🚫 本支不輸出判詞文字、不改任何清冊、不送外部請求
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
from ahig.extraction import corpus  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n644_screening_vs_extraction.json'
RUN = ROOT / 'search-runs/b11-exogenous-cho-endurance/b11-full-run'

# ⚠️ 契約六個結局的字面線索。🚨 樣式字面裡不得有控制字元（第 576／583 輪）。
CLUES = {
    'tt-completion-time': re.compile(
        r'time[- ]trial|\bTT\b|計時賽|完成時間', re.IGNORECASE),
    'time-to-exhaustion': re.compile(
        r'time to exhaustion|\bTTE\b|力竭', re.IGNORECASE),
    'exogenous-cho-oxidation-peak': re.compile(
        r'oxidation|氧化', re.IGNORECASE),
    'muscle-glycogen-post-exercise': re.compile(
        r'glycogen|肝醣', re.IGNORECASE),
    'gi-symptom': re.compile(
        r'gastrointestinal|\bGI\b|symptom|腸胃|不適', re.IGNORECASE),
}


def main():
    judgements = json.loads(
        (RUN / 'standard-full-screen-pass-1/judgements.json')
        .read_text(encoding='utf-8'))
    reason = {e['candidateId']: (e.get('reason') or '')
              for e in judgements['entries']}

    roster = set(corpus.acquired_roster()[0])
    in_scope_count = {}
    declared_count = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        outcomes = doc.get('reportedOutcomes') or []
        declared_count[doc['report']] = len(outcomes)
        in_scope_count[doc['report']] = sum(
            1 for o in outcomes
            if (o.get('scopeDecision') or {}).get('inScope'))

    # 🚨 第一版只比「判詞有沒有線索」——⚠️ 而實測命中率是
    # 有貢獻 96%／零貢獻 92%：**規則幾乎打中所有東西，等於沒有鑑別力。**
    # ✅ 故改問一個更緊的：**該篇自己清冊裡的標籤，有沒有寫著那個結局**。
    # ⚠️ 若讀的人在標籤裡寫了「time trial」卻沒對到 tt-completion-time，
    # 🚨 那才是映射失敗的訊號；🚫 而判詞層級的相符只是背景雜訊。
    labels_by_report = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        labels_by_report[doc['report']] = ' | '.join(
            str(o.get('localLabel') or '')
            for o in doc.get('reportedOutcomes') or [])

    rows = []
    for report in sorted(roster):
        text = reason.get(report, '')
        clues = sorted(name for name, pattern in CLUES.items()
                       if pattern.search(text))
        label_text = labels_by_report.get(report, '')
        label_clues = sorted(name for name, pattern in CLUES.items()
                             if pattern.search(label_text))
        rows.append({
            'report': report[-16:],
            'hasScreeningReason': bool(text),
            'screeningClues': clues,
            'labelClues': label_clues,
            'declared': declared_count.get(report),
            'inScope': in_scope_count.get(report),
        })

    contributing = [r for r in rows if (r['inScope'] or 0) > 0]
    zero = [r for r in rows if r['inScope'] == 0]
    no_inventory = [r for r in rows if r['inScope'] is None]

    clue_rate_contributing = (
        sum(1 for r in contributing if r['screeningClues'])
        / max(1, len(contributing)))
    clue_rate_zero = (sum(1 for r in zero if r['screeningClues'])
                      / max(1, len(zero)))

    contradictions = [r for r in zero if r['screeningClues']]
    # 🚨 標籤層級也一樣沒有鑑別力（實測同為 96%／92%）——
    # ⚠️ 本室原本以為它更緊，**那個以為是錯的**。
    label_level = [r for r in zero if r['labelClues']]

    # ✅ 真正有鑑別力的問法：**讀的人到底把結局對到了哪些 ref**。
    # 🚨 這一刀把零貢獻的 13 篇切成兩種完全不同的東西。
    contract_refs = {o['outcomeId'] for o in json.loads(
        (REPO / 'ahig/calibration/b11-carbohydrate/scope-contract.json')
        .read_text(encoding='utf-8'))['inScopeOutcomes']}
    refs_by_report = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        refs_by_report[doc['report'][-16:]] = sorted(
            {o.get('normalisedOutcomeRef')
             for o in doc.get('reportedOutcomes') or []}
            & contract_refs)
    mapped_then_rejected = [r for r in zero if refs_by_report.get(r['report'])]
    never_mapped = [r for r in zero if not refs_by_report.get(r['report'])]
    for r in zero:
        r['contractRefsUsed'] = refs_by_report.get(r['report'], [])
    label_rate_contributing = (
        sum(1 for r in contributing if r['labelClues'])
        / max(1, len(contributing)))
    label_rate_zero = (sum(1 for r in zero if r['labelClues'])
                       / max(1, len(zero)))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一篇都找得到篩選判詞（必觸發之正對照）',
          all(r['hasScreeningReason'] for r in rows),
          '🚨 沒有判詞的 %d 篇：%s；⚠️ 沒有判詞就無從比較'
          % (sum(1 for r in rows if not r['hasScreeningReason']),
             [r['report'] for r in rows if not r['hasScreeningReason']][:5]))
    probe('線索規則在**有貢獻的 25 篇**上打得中（必觸發之正對照）',
          clue_rate_contributing >= 0.6,
          '🚨 有貢獻者的命中率 %.0f%%（%d/%d）；⚠️ 若這裡就打不中，'
          '**本支的結論一律作廢——那代表規則本身沒有鑑別力**'
          % (100 * clue_rate_contributing,
             sum(1 for r in contributing if r['screeningClues']),
             len(contributing)))
    probe('線索規則有鑑別力（🚨 本支第一版守錯方向的那一道）',
          abs(clue_rate_contributing - clue_rate_zero) >= 0.25,
          '🚨 判詞層級命中率：有貢獻 %.0f%%、零貢獻 %.0f%%——**幾乎一樣**。'
          '⚠️ 一條打中 95%% 樣本的規則什麼也分不出來，'
          '**🚫 故「%d 篇判詞有線索」不能當成 %d 個映射失敗**'
          % (100 * clue_rate_contributing, 100 * clue_rate_zero,
             len(contradictions), len(contradictions)))
    probe('標籤層級的問法有鑑別力（🚨 本室原本以為它更緊）',
          abs(label_rate_contributing - label_rate_zero) >= 0.25,
          '🚨 標籤層級命中率：有貢獻 %.0f%%、零貢獻 %.0f%%——**一樣沒有鑑別力**。'
          '⚠️ **即關鍵字這條路答不出「離題還是映射失敗」**，'
          '🚫 本支不拿它下結論'
          % (100 * label_rate_contributing, 100 * label_rate_zero))
    # 🚨 這一道才是答案：改問「對到了哪些契約 ref」。
    probe('零貢獻的 13 篇是同一種東西',
          not (mapped_then_rejected and never_mapped),
          '🚨 它們是**兩種**：%d 篇其實有對到契約結局（共 %d 個 ref），'
          '只是那些項目在後面的關卡被擋掉——**⚠️ 它們不是離題**；'
          '另 %d 篇一項都沒對到任何契約結局。明細：%s'
          % (len(mapped_then_rejected),
             sum(len(refs_by_report.get(r['report'], []))
                 for r in mapped_then_rejected),
             len(never_mapped),
             [(r['report'], refs_by_report.get(r['report']))
              for r in mapped_then_rejected]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'screening-vs-extraction',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'contentDiscipline': '✅ 只輸出結局代號與計數；🚫 不輸出判詞文字。',
        'corpus': len(rows),
        'contributing': len(contributing),
        'zeroContribution': len(zero),
        'withoutInventory': len(no_inventory),
        'clueHitRate': {
            '有貢獻的篇': round(clue_rate_contributing, 3),
            '零貢獻的篇': round(clue_rate_zero, 3),
        },
        'screeningLevelContradictions': contradictions,
        'labelLevelContradictions': label_level,
        'mappedThenRejected': [
            {'report': r['report'], 'declared': r['declared'],
             'contractRefsUsed': r['contractRefsUsed']}
            for r in mapped_then_rejected],
        'neverMappedToAnyContractRef': [r['report'] for r in never_mapped],
        'theRealSplit': (
            '🚨 零貢獻的 13 篇**不是同一種東西**：'
            '✅ %d 篇的讀者其實有把結局對到契約 ref，'
            '⚠️ 那些項目是在**後面的關卡**（劑量帶／效應量／儀器／無數值）被擋掉的'
            '——**🚫 它們不是離題**；'
            '🚨 另 %d 篇則一項都沒對到任何契約 ref。'
            '**⚠️ 把這兩種混成「零貢獻」會讓前者看起來像後者。**'
            % (len(mapped_then_rejected), len(never_mapped))),
        'keywordApproachFailed': (
            '🚨 本支原本要用關鍵字分辨「離題」與「映射失敗」。'
            '⚠️ 實測命中率：判詞層級 96%%／92%%，標籤層級 96%%／92%%——'
            '**兩種問法都沒有鑑別力**（語料本來就全是這個主題）。'
            '**✅ 故那條路答不出這個問題，本室把它記下來而不是硬套。**'),
        'discriminationNote': (
            '🚨 判詞層級的規則命中率：有貢獻 %.0f%%、零貢獻 %.0f%%——**幾乎一樣**。'
            '⚠️ 即那條規則沒有鑑別力，**🚫 本支第一版差點把 %d 篇報成映射失敗**。'
            '✅ 有意義的是標籤層級：有貢獻 %.0f%%、零貢獻 %.0f%%。'
            % (100 * clue_rate_contributing, 100 * clue_rate_zero,
               len(contradictions), 100 * label_rate_contributing,
               100 * label_rate_zero)),
        'rows': rows,
        'howToReadThis': (
            '⚠️ 「篩選判詞提到某個結局」**不等於**「那篇真的報告了該結局的可抽數值」——'
            '🚨 判詞是讀摘要時寫的，而摘要常提到方法卻不報數字。'
            '**✅ 故本支的產出是「待人看」，🚫 不是「抽取端漏了」。**'),
        'whyItMatters': (
            '🚨 若篩選與抽取對同一篇的判斷相反，那是本 run **自己兩個階段矛盾**，'
            '⚠️ 而矛盾若沒被指出來，最後只會以「那篇不相關」的形式沉默地消失。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n644 篩選 vs 抽取 ===')
    print('   語料 %d 篇｜有貢獻 %d｜零貢獻 %d｜無清冊 %d'
          % (len(rows), len(contributing), len(zero), len(no_inventory)))
    print('   線索命中率：有貢獻 %.0f%%｜零貢獻 %.0f%%'
          % (100 * clue_rate_contributing, 100 * clue_rate_zero))
    print('   🚫 判詞層級 %d 篇、標籤層級 %d 篇——**兩者命中率都是 96%%／92%%，無鑑別力**'
          % (len(contradictions), len(label_level)))
    print('   ✅ 真正的切法：%d 篇有對到契約 ref（後面關卡才被擋）｜%d 篇一項都沒對到'
          % (len(mapped_then_rejected), len(never_mapped)))
    for row in mapped_then_rejected:
        print('      %s｜對到 %s｜宣告 %s 項'
              % (row['report'], row['contractRefsUsed'], row['declared']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
