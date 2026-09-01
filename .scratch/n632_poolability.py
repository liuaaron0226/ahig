# -*- coding: utf-8 -*-
"""**這 98 項合得起來嗎，以及有兩組是從一道空關卡進來的。**（第 632 輪）

## 🚨 第 628 輪只數了「幾篇」，⚠️ 沒問「合不合得起來」

⚠️ 五篇支持同一個結局，若各自用不同儀器、不同效應量、不同分析集，
**🚨 那不是五份可以合併的證據，是五份各自為政的證據。**

## ✅ 本支問三件事

| | 問題 |
|---|---|
| **甲** | 每個結局的支持篇數，攤到 **(儀器, 效應量, 分析集, 時點)** 組合上剩多少 |
| **乙** | 契約**允許**的值 vs 語料**實際出現**的值——🚨 哪些格子是空的 |
| **丙** | 🚨 腸胃症狀那兩個結局的 `allowedInstruments` 是**空的**——它們是怎麼通過儀器關卡的 |

**⚠️ 乙那一問要小心一件事**：若契約只允許一種值，那「全部都是那一種」是本室
**自己的過濾器保證的**，🚫 不是文獻的性質。✅ 故本支先讀契約，再讀資料。

## 🚫 本支不送外部請求、不改任何產品程式、不改任何清冊
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.scope.matcher import ScopeMatcher  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n632_poolability.json'
CONTRACT = REPO / 'ahig/calibration/b11-carbohydrate/scope-contract.json'


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    allowed_instruments = {
        o['outcomeId']: list(o.get('allowedInstruments') or [])
        for o in contract['inScopeOutcomes']}

    rows = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for outcome in doc.get('reportedOutcomes') or []:
            if not (outcome.get('scopeDecision') or {}).get('inScope'):
                continue
            rows.append({
                'report': doc['report'][-16:],
                'ref': outcome.get('normalisedOutcomeRef'),
                'instrument': outcome.get('instrument'),
                'effectMeasure': outcome.get('effectMeasure'),
                'analysisSet': outcome.get('analysisSet'),
                'timepointDays': outcome.get('timepointDays'),
            })

    # 甲：可合併性。
    papers_by_ref = collections.defaultdict(set)
    cells = collections.defaultdict(lambda: collections.defaultdict(set))
    for row in rows:
        key = (row['instrument'], row['effectMeasure'],
               row['analysisSet'], row['timepointDays'])
        papers_by_ref[row['ref']].add(row['report'])
        cells[row['ref']][key].add(row['report'])

    pooling = []
    for ref, papers in sorted(papers_by_ref.items(),
                              key=lambda kv: -len(kv[1])):
        groups = cells[ref]
        largest = max((len(v) for v in groups.values()), default=0)
        pooling.append({
            'outcome': ref,
            'papers': len(papers),
            'distinctCombinations': len(groups),
            'largestComparableGroup': largest,
            'instrumentRecorded': all(
                r['instrument'] is not None for r in rows if r['ref'] == ref),
        })

    # 乙：契約允許 vs 實際出現。
    def observed(field):
        return sorted({str(r[field]) for r in rows})

    axes = {
        'analysisSet': {'allowed': contract['inScopeAnalysisSets'],
                        'observed': observed('analysisSet')},
        'effectMeasure': {'allowed': contract['inScopeEffectMeasures'],
                          'observed': observed('effectMeasure')},
        'timepointWindow': {
            'allowed': [t['timepointId'] for t in contract['inScopeTimepoints']],
            'observed': observed('timepointDays'),
        },
    }
    unused_analysis = [v for v in axes['analysisSet']['allowed']
                       if v not in axes['analysisSet']['observed']]
    unused_measure = [v for v in axes['effectMeasure']['allowed']
                      if v not in axes['effectMeasure']['observed']]

    # 丙：空的允許清單怎麼判。⚠️ 不看程式碼推論，🚨 直接跑產品的匹配器。
    matcher = ScopeMatcher(contract)
    empty_list_outcomes = [k for k, v in allowed_instruments.items() if not v]
    nonempty_list_outcomes = [k for k, v in allowed_instruments.items() if v]

    # 🚨 第一版是本室**手刻**一筆合成宣告餵進去——⚠️ 而正對照當場亮紅：
    # 連正當儀器都判成 False，代表那筆合成紀錄本身缺欄位，
    # **於是「空清單也擋得住」那個綠燈是假的綠**。
    # ✅ 改成拿語料裡**已被判為在範圍內的真實紀錄**當模板，只改儀器那一欄。
    templates = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for outcome in doc.get('reportedOutcomes') or []:
            if not (outcome.get('scopeDecision') or {}).get('inScope'):
                continue
            templates.setdefault(outcome.get('normalisedOutcomeRef'),
                                 outcome)

    def probe_instrument(ref, instrument):
        """以真實模板改一欄，回傳產品匹配器判不判為在範圍內。"""
        template = templates.get(ref)
        if template is None:
            return 'no-template'
        reported = {k: v for k, v in template.items()
                    if k != 'scopeDecision'}
        reported['instrument'] = instrument
        try:
            return bool(matcher.decide(reported).in_scope)
        except Exception as error:  # noqa: BLE001
            return 'error:%s' % type(error).__name__

    empty_ref = empty_list_outcomes[0] if empty_list_outcomes else None
    nonempty_ref = (nonempty_list_outcomes[0]
                    if nonempty_list_outcomes else None)
    nonsense = 'ZZ-不是儀器-ZZ'
    empty_admits_nonsense = (probe_instrument(empty_ref, nonsense)
                             if empty_ref else None)
    nonempty_rejects_nonsense = (probe_instrument(nonempty_ref, nonsense)
                                 if nonempty_ref else None)
    # ⚠️ 正對照要用**該結局模板原本那一支儀器**，🚨 而非允許清單的第一項：
    # 清單第一項未必是這一篇用的，那樣測到的是別的東西。
    nonempty_admits_real = (
        probe_instrument(nonempty_ref,
                         (templates.get(nonempty_ref) or {}).get('instrument'))
        if nonempty_ref else None)

    no_instrument = [r for r in rows if r['instrument'] is None]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    # 🚨 這三道是同一組雙向控制，⚠️ 走的是**產品匹配器**，不是本室的推論。
    probe('允許清單非空時，正當儀器過得了（必觸發之正對照）',
          nonempty_admits_real is True,
          '🚨 以 %s 的正當儀器試，結果 %r；⚠️ 若過不了，'
          '下面兩道就沒有意義' % (nonempty_ref, nonempty_admits_real))
    probe('允許清單非空時，亂填的儀器被擋（必觸發之反向）',
          nonempty_rejects_nonsense is False,
          '🚨 以亂填的儀器試 %s，結果 %r；⚠️ 若也過得了，'
          '整道儀器關卡都是空的' % (nonempty_ref, nonempty_rejects_nonsense))
    # 🚨 以下三道是本支的發現。
    probe('允許清單為空時，儀器關卡仍然擋得住',
          empty_admits_nonsense is False,
          '🚨 %s 的 allowedInstruments 是空的；⚠️ 以亂填的儀器試，'
          '產品匹配器判定 in_scope=%r——**空清單＝不設限**'
          '（matcher.py:83 的 `if allowed and …`）'
          % (empty_ref, empty_admits_nonsense))
    probe('每一項在範圍內結局都記了儀器',
          not no_instrument,
          '🚨 實得 %d 項（佔 %d 的 %.0f%%）`instrument` 為 None，'
          '集中在 %s；⚠️ 它們通過的是一道**對它們而言空的**關卡'
          % (len(no_instrument), len(rows),
             100 * len(no_instrument) / max(1, len(rows)),
             sorted({r['ref'] for r in no_instrument})))
    probe('每個結局的支持篇數都落在單一可比組合裡',
          all(p['distinctCombinations'] == 1 for p in pooling),
          '🚨 實得：%s'
          % [(p['outcome'], '%d 篇拆成 %d 組，最大一組 %d 篇'
              % (p['papers'], p['distinctCombinations'],
                 p['largestComparableGroup']))
             for p in pooling if p['distinctCombinations'] > 1])

    doc = {
        'schemaVersion': 1,
        'documentType': 'poolability-audit',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inScopeOutcomes': len(rows),
        'pooling': pooling,
        'axes': axes,
        'allowedButNeverObserved': {
            'analysisSet': unused_analysis,
            'effectMeasure': unused_measure,
            'note': ('✅ 契約允許 ITT／mITT 而語料**一項都沒有**——'
                     '🚨 故「全部 complete-case」是文獻的性質，'
                     '🚫 不是本室過濾器造成的。'
                     '⚠️ 同理，契約允許 MD／SMD／RR／RD 四種對比量度，'
                     '**而語料只出現 mean 與 proportion**——'
                     '🚨 即沒有任何一篇以可直接合併的對比形式回報。'),
        },
        'emptyAllowlistOutcomes': empty_list_outcomes,
        'outcomesWithoutInstrument': len(no_instrument),
        'instrumentGateNote': (
            '🚨 `matcher.py:83` 寫的是 `if allowed and reported… not in allowed`'
            '——⚠️ **空的允許清單等於不設限**，不是「什麼都不允許」。'
            '✅ 本支以產品匹配器實跑驗證（非推論）：'
            '空清單的結局，亂填的儀器也判為在範圍內。'),
        'erratumOnN628': (
            '⚠️ 第 628 輪那張表的「儀器種類」欄，對腸胃症狀兩列顯示 **1**——'
            '🚨 而那個 1 是 `None` 被當成一種儀器數進去的。'
            '**⚠️ 正確的說法是「沒有記儀器」，不是「只用一種儀器」。**'
            '🚫 n628 不就地改寫（已上看板），本條即其 errata。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n632 可合併性稽核 ===')
    print('   %-30s %6s %8s %10s %s'
          % ('結局', '篇數', '組合數', '最大可比組', '有記儀器'))
    for entry in pooling:
        print('   %-30s %6d %8d %10d %s'
              % (entry['outcome'], entry['papers'],
                 entry['distinctCombinations'], entry['largestComparableGroup'],
                 '✅' if entry['instrumentRecorded'] else '🚨 否'))
    print('   契約允許卻從未出現：分析集 %s｜效應量 %s'
          % (unused_analysis, unused_measure))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
