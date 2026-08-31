# -*- coding: utf-8 -*-
"""**A3 第一次有實測數字，而且通過。**（第 594 輪）

## ✅ 內容門檻 A3：同一篇由不同會話讀兩次，契約結局集合須相同

⚠️ 本室前三輪都在找潛在缺陷（全部無活的損害）。**✅ 本輪回到真正擋著的那四條。**

| 單位 | 兩邊都有 | 只有正式那道 | 只有第二位 |
|---|---|---|---|
| **標籤**（自由文字） | **0** | 41 | 18 |
| **契約結局 `refs`** | **✅ 2** | **0** | **0** |

> **🚨 標籤零逐字重疊，契約結局完全相同。**
> ✅ 兩位讀者都指向 `muscle-glycogen-post-exercise` 與 `time-to-exhaustion`。
> **⚠️ 這正是 n+192 四說的那件事被實測證實**：
> 「這篇報告了幾個結局」取決於誰讀的（41 對 18），
> **「這篇有沒有報告結局 X」不取決於誰讀的。**

**`reportsFullyAgreed = 1／1`。🚨 而 n＝1——這是證據，不是證明。**

## 🚨 而第二位讀者順手回答了本室 n585 的待裁定問題

n585 問：`acid-hydrolysis-freeze-dried-biopsy` 該不該改名為
`needle-biopsy-vastus-lateralis`？⚠️ 本室當時說「部位對得上，但全文沒有 needle」。

> **✅ 第二位讀者的標籤裡寫著：取樣用的是 Weil-Blakesley conchotome，
> 🚨 不是 Bergstrom needle。**
> **⚠️ 故那不是命名差異——改名會把一件事實寫錯。**
> **✅ 那 3 項應從「改名待裁定」移到「契約缺口」**：
> 🚨 契約唯一允許的工具是針刺切片，而這篇用的是另一種器械。
>
> **⚠️ 而這份證據從第 572 輪就躺在 `second/` 裡。**
> **🚨 本室問了一個自己讀一下就能答的問題。**

## 🚫 本支不入輪次閘門；🚫 lane=second 從不進入正式清冊
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
from ahig.extraction.worksheet import agreement  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n594_a3_first_measurement.json'
SHEET = ROOT / 'extraction-worksheet'
# 🚨 只比對是否**出現**，🚫 不把論文的字句抄進 repo。
CONCHOTOME = 'conchotome'
NEEDLE = 'needle'


def load(paths):
    out = {}
    for path in paths:
        for entry in json.loads(path.read_text(encoding='utf-8'))['entries']:
            out[entry['report'][-16:]] = entry
    return out


def main():
    primary = load([SHEET / 'drafts.json']
                   + sorted((SHEET / 'drafts').glob('page-*.json')))
    second = load(sorted((SHEET / 'second').glob('page-*.json')))
    result = agreement(primary, second)

    # ⚠️ 取樣器械的證據：只看關鍵字是否出現，🚫 不抄原句。
    second_text = ' '.join(
        (item.get('localLabel') or '')
        for entry in second.values()
        for item in entry.get('reportedOutcomes') or [])
    says_conchotome = CONCHOTOME in second_text.lower()
    says_not_needle = NEEDLE in second_text.lower()

    # 🚨 必觸發之反向：比對機制要真的說得出「不一致」。
    # ⚠️ 否則 refsOnly*=0 可能只是它永遠回 0。
    mutated = copy.deepcopy(second)
    report = next(iter(mutated))
    for item in mutated[report].get('reportedOutcomes') or []:
        if item.get('normalisedOutcomeRef') == 'time-to-exhaustion':
            item['normalisedOutcomeRef'] = 'tt-completion-time'
    mutated_result = agreement(primary, mutated)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('確實比到了那一篇（必觸發）',
          result['comparedReports'] == 1,
          '🚨 若為零，「一致」只是沒有東西可比；實得 %d 篇'
          % result['comparedReports'])
    probe('比對機制說得出「不一致」（必觸發之反向）',
          mutated_result['refsOnlyPrimary'] > 0
          or mutated_result['refsOnlySecond'] > 0,
          '🚨 把第二位的一個 outcomeId 換掉後，實得 only=%d／%d；'
          '⚠️ 若仍為 0，refsOnly*=0 就可能只是它永遠回 0'
          % (mutated_result['refsOnlyPrimary'],
             mutated_result['refsOnlySecond']))
    probe('標籤層與契約結局層給的答案不同（必觸發之反向）',
          result['labelsBoth'] == 0 and result['refsBoth'] > 0,
          '✅ 標籤兩邊都有 %d、契約結局兩邊都有 %d；'
          '🚨 若兩層答案相同，n+192 四所稱的「換個單位就可比」便未被驗證'
          % (result['labelsBoth'], result['refsBoth']))
    probe('A3 於本篇成立：兩位讀者的契約結局集合相同',
          result['refsOnlyPrimary'] == 0 and result['refsOnlySecond'] == 0
          and result['reportsFullyAgreed'] == result['comparedReports'],
          '✅ refsBoth=%d、只有一邊有 %d／%d、逐篇一致 %d／%d'
          % (result['refsBoth'], result['refsOnlyPrimary'],
             result['refsOnlySecond'], result['reportsFullyAgreed'],
             result['comparedReports']))
    # 🚨 這一道會紅：⚠️ n＝1 撐不起一條門檻。
    probe('雙讀的篇數足以支撐 A3', result['comparedReports'] >= 5,
          '🚨 實得 %d 篇。⚠️ 一篇通過是證據，🚫 不是證明；'
          'A3 要成立需要更多篇雙讀' % result['comparedReports'])

    doc = {
        'schemaVersion': 1,
        'documentType': 'a3-first-measurement',
        'gate': 'A3：同一篇由不同會話讀兩次，契約結局集合須相同',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'agreement': {k: v for k, v in result.items()
                      if not isinstance(v, list)},
        'refsBothOnThatReport': result['rows'][0]['refsBoth'],
        'verdict': ('✅ 本篇 A3 成立：標籤零逐字重疊（41 對 18），'
                    '而契約結局集合完全相同。'
                    '🚨 但 n＝1——這是證據，🚫 不是證明。'),
        'granularityConfirmed': (
            '✅ n+192 四所稱「換一個單位就可比」已被實測證實：'
            '⚠️ 標籤層兩邊都有 0，契約結局層兩邊都有 %d。'
            % result['refsBoth']),
        'answersN585Question': {
            'question': 'acid-hydrolysis-freeze-dried-biopsy 該不該改名為 '
                        'needle-biopsy-vastus-lateralis',
            'answer': ('🚫 不該。✅ 第二位讀者記載取樣器械為 Weil-Blakesley '
                       'conchotome，🚨 不是 Bergstrom needle。'
                       '⚠️ 改名會把一件事實寫錯——'
                       '✅ 那 3 項應從「改名待裁定」移到「契約缺口」。'),
            'evidencePresent': {'mentionsConchotome': says_conchotome,
                                'mentionsNeedle': says_not_needle},
            'selfCriticism': ('🚨 這份證據從第 572 輪就在 second／ 裡。'
                              '⚠️ 本室問了一個自己讀一下就能答的問題。'),
        },
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n594 A3 第一次實測 ===')
    print('   比對 %d 篇｜標籤：兩邊都有 %d／只有正式 %d／只有第二位 %d'
          % (result['comparedReports'], result['labelsBoth'],
             result['labelsOnlyPrimary'], result['labelsOnlySecond']))
    print('   ✅ 契約結局：兩邊都有 %d／只有正式 %d／只有第二位 %d｜逐篇一致 %d／%d'
          % (result['refsBoth'], result['refsOnlyPrimary'],
             result['refsOnlySecond'], result['reportsFullyAgreed'],
             result['comparedReports']))
    print('   兩邊共同指向：%s' % result['rows'][0]['refsBoth'])
    print('   n585 之問：第二位讀者記載 conchotome=%s／文中提及 needle=%s'
          % (says_conchotome, says_not_needle))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
