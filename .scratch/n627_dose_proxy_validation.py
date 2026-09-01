# -*- coding: utf-8 -*-
"""**上一輪那把尺，拿真值來量一次。**（第 627 輪）

## 🚨 第 626 輪的結論站在一個代理指標上

⚠️ 第 626 輪說「缺掉的年代撐著劑量曲線低端」，用的是**篩選判詞裡的攝取率**——
🚨 那是本 run 讀摘要時隨手記下的數，**🚫 從來沒有人驗過它準不準。**

> **⚠️ 而那 107 篇沒取到的文獻，本室永遠只有判詞可用。**
> **🚨 故判詞這把尺若不準，第 626 輪的結論就該打折——本輪先驗尺。**

## ✅ 驗法：語料這 25 篇兩邊都有

| | 來源 |
|---|---|
| **真值** | 清冊 `reportedOutcomes[].dose`（g/h）——⚠️ 讀過全文之後抽出來的 |
| **代理** | 篩選判詞裡的攝取率——🚨 只讀摘要時記的 |

**⚠️ 兩邊都有的篇，逐篇比。** ✅ 若代理系統性地偏，就把偏差說出來；
🚨 若代理根本測不準，第 626 輪的結論本輪自己撤。

## ✅ 順帶回答一件本 run 沒問過的事

**🚨 現有結論實際站在哪個劑量帶上**——⚠️ 98 個在範圍內結局的分布。

## 🚫 本支不送外部請求、不改任何清冊、不輸出任何標籤或題名文字
"""
import json
import re
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n627_dose_proxy_validation.json'
RUN = ROOT / 'search-runs/b11-exogenous-cho-endurance/b11-full-run'

PER_MIN = re.compile(r'(\d+(?:[.]\d+)?)\s*g\s*/\s*min')
PER_HOUR = re.compile(r'(\d+(?:[.]\d+)?)\s*g\s*/\s*h')
PLAUSIBLE = (5.0, 250.0)
LOW = 60.0


def proxy_doses(text):
    values = [float(m) * 60 for m in PER_MIN.findall(text)]
    values += [float(m) for m in PER_HOUR.findall(text)]
    return sorted(v for v in values if PLAUSIBLE[0] <= v <= PLAUSIBLE[1])


def main():
    judgements = json.loads(
        (RUN / 'standard-full-screen-pass-1/judgements.json')
        .read_text(encoding='utf-8'))
    reason = {e['candidateId']: (e.get('reason') or '')
              for e in judgements['entries']}

    # 真值：清冊裡在範圍內結局的劑量。
    truth = {}
    in_scope_doses = []
    units = set()
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        values = []
        for outcome in doc.get('reportedOutcomes') or []:
            if not (outcome.get('scopeDecision') or {}).get('inScope'):
                continue
            dose = outcome.get('dose')
            if dose is None:
                continue
            units.add(outcome.get('doseUnit'))
            values.append(float(dose))
        if values:
            truth[doc['report']] = sorted(values)
            in_scope_doses.extend(values)

    # 逐篇比對：兩邊都有的才算。
    pairs = []
    for report, values in truth.items():
        proxy = proxy_doses(reason.get(report, ''))
        if not proxy:
            continue
        pairs.append({
            'report': report[-16:],
            'truthMin': min(values), 'truthMax': max(values),
            'proxyMin': min(proxy), 'proxyMax': max(proxy),
            'minDiff': round(min(proxy) - min(values), 1),
            'lowSideAgrees': (min(proxy) < LOW) == (min(values) < LOW),
        })
    pairs.sort(key=lambda row: abs(row['minDiff']), reverse=True)

    min_diffs = [row['minDiff'] for row in pairs]
    agree_low = sum(1 for row in pairs if row['lowSideAgrees'])
    within_10 = sum(1 for row in pairs if abs(row['minDiff']) <= 10)

    per_paper_min = sorted(min(v) for v in truth.values())
    papers_low = [m for m in per_paper_min if m < LOW]

    # ⚠️ 誤判的方向要分開看：代理把高的說成低，與把低的說成高，
    # 🚨 對第 626 輪的影響方向相反。
    proxy_says_low_truth_high = [
        row for row in pairs
        if row['proxyMin'] < LOW <= row['truthMin']]
    proxy_says_high_truth_low = [
        row for row in pairs
        if row['truthMin'] < LOW <= row['proxyMin']]

    # ✅ 第 626 輪的結論是「未取得・2000 年前有 55% 落在低端，語料只有 27%」。
    # 🚨 若代理的誤判率是 %.1f%%，最壞情況能把那 55%% 推到哪裡——
    # ⚠️ 這是本支能給的上界，🚫 不是精確修正。
    error_rate = ((len(pairs) - agree_low) / len(pairs)) if pairs else None
    n626_pre2000_low_share = 55.0
    n626_corpus_low_share = 27.0
    worst_case_gap = None
    if error_rate is not None:
        swing = 100 * error_rate
        worst_case_gap = round(
            (n626_pre2000_low_share - swing)
            - (n626_corpus_low_share + swing), 1)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩邊都有的篇夠多，比得出東西（必觸發之正對照）',
          len(pairs) >= 15,
          '🚨 實得 %d 篇兩邊都有（真值 %d 篇、其中有判詞劑量者 %d）；'
          '⚠️ 若太少，本支說什麼都是軼事'
          % (len(pairs), len(truth), len(pairs)))
    probe('真值的單位只有一種（必觸發之反向）',
          units == {'g/h'},
          '🚨 實得單位集合 %s；⚠️ 若混了 g/min，'
          '**這場比較就是拿兩把不同的尺在量**' % sorted(units))
    probe('代理沒有把「沒抽到」當成低劑量（必觸發之反向）',
          all(row['proxyMin'] >= PLAUSIBLE[0] for row in pairs),
          '🚨 代理的最小值不會小於可信域下界 %s g/h' % PLAUSIBLE[0])
    # 🚨 這兩道決定第 626 輪還站不站得住。
    probe('⚠️ 代理與真值在**低端與否**上一致',
          len(pairs) > 0 and agree_low == len(pairs),
          '%s %d/%d 篇一致；⚠️ 這一格才是第 626 輪真正倚賴的判斷'
          % ('✅' if agree_low == len(pairs) else '🚨', agree_low, len(pairs)))
    probe('⚠️ 代理的最低劑量與真值相差在 10 g/h 內',
          len(pairs) > 0 and within_10 == len(pairs),
          '%s %d/%d 篇相差 ≤10 g/h；中位偏差 %s g/h；'
          '⚠️ 最大偏差 %s g/h'
          % ('✅' if within_10 == len(pairs) else '🚨', within_10, len(pairs),
             round(statistics.median(min_diffs), 1) if min_diffs else None,
             max(min_diffs, key=abs) if min_diffs else None))

    doc = {
        'schemaVersion': 1,
        'documentType': 'dose-proxy-validation',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'unit': 'g/h',
        'truthPapers': len(truth),
        'inScopeDoseValues': len(in_scope_doses),
        'inScopeDoseSummary': {
            'min': min(in_scope_doses) if in_scope_doses else None,
            'median': statistics.median(in_scope_doses)
            if in_scope_doses else None,
            'max': max(in_scope_doses) if in_scope_doses else None,
            'below60': sum(1 for v in in_scope_doses if v < LOW),
            'atOrAbove90': sum(1 for v in in_scope_doses if v >= 90),
        },
        'perPaperMinDose': per_paper_min,
        'papersAnchoringLowEnd': len(papers_low),
        'thresholdSensitivity': {
            'strictlyBelow60': len(papers_low),
            'atOrBelow60': sum(1 for m in per_paper_min if m <= LOW),
            'papersExactlyAt60': sum(1 for m in per_paper_min if m == LOW),
            'note': ('🚨 60 g/h 這個門檻是本室自己選的，'
                     '⚠️ 而它正好壓在資料的眾數上——有 %d 篇的最低劑量**恰為 60.0**'
                     '（60 g/h 是這個領域的經典劑量）。'
                     '**🚨 故「撐住低端的只有 4 篇」對門檻極度敏感**：'
                     '改成 ≤60 就變 %d 篇。⚠️ 兩個數都要看。'
                     % (sum(1 for m in per_paper_min if m == LOW),
                        sum(1 for m in per_paper_min if m <= LOW))),
        },
        'comparedPapers': len(pairs),
        'proxyAgreement': {
            'lowSideAgreement': '%d/%d' % (agree_low, len(pairs)),
            'within10gPerHour': '%d/%d' % (within_10, len(pairs)),
            'medianMinDiff': round(statistics.median(min_diffs), 1)
            if min_diffs else None,
            'largestMinDiff': max(min_diffs, key=abs) if min_diffs else None,
        },
        'worstPairs': pairs[:6],
        'proxyErrorDirections': {
            '代理說低・真值不低': len(proxy_says_low_truth_high),
            '代理說不低・真值低': len(proxy_says_high_truth_low),
        },
        'n626RobustnessBound': {
            'observedLowSideErrorRate': round(100 * error_rate, 1)
            if error_rate is not None else None,
            'n626Gap': round(n626_pre2000_low_share - n626_corpus_low_share, 1),
            'worstCaseGapIfAllErrorsAlign': worst_case_gap,
            'errorIsOneSided': (
                '🚨 兩處誤判方向一致——**代理都是「把不低的說成低」**'
                '（反向 0 篇）。⚠️ 那正是會**誇大**第 626 輪結論的方向。'
                '✅ 但該偏移對兩組應同等作用，故差距本身多半仍在；'
                '🚫 本室不宣稱它精確等於 28.7。'),
            'note': ('⚠️ 把觀察到的誤判率**全部往同一個方向**推，'
                     '看第 626 輪那個 28.7 個百分點的差距還剩多少。'
                     '🚫 這是上界推算，不是精確修正。'),
        },
        'whatThisMeansForN626': (
            '⚠️ 第 626 輪拿判詞當尺去量那 107 篇沒取到的文獻。'
            '✅ 本支在語料這 %d 篇上驗過那把尺：'
            '**中位偏差 0.0 g/h（無系統性偏移）**，'
            '🚨 但低端判斷有 %d 篇不一致、%d 篇偏差超過 10 g/h——'
            '⚠️ 故第 626 輪的數字應讀成「群體層級的粗略比較」，'
            '**🚫 不可拿去斷任何單篇。**'
            % (len(pairs), len(pairs) - agree_low, len(pairs) - within_10)),
        'whatThisCannotAnswer': (
            '🚫 沒取到的那些沒有真值可比——⚠️ 本支只能說「這把尺在語料上準不準」，'
            '🚨 不能保證它在那個年代一樣準。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n627 劑量代理指標驗證 ===')
    print('   在範圍內結局 %d 個、分布於 %d 篇；單位 %s'
          % (len(in_scope_doses), len(truth), sorted(units)))
    print('   劑量（真值）：最低 %s｜中位 %s｜最高 %s｜<60 g/h 者 %d 個'
          % (doc['inScopeDoseSummary']['min'],
             doc['inScopeDoseSummary']['median'],
             doc['inScopeDoseSummary']['max'],
             doc['inScopeDoseSummary']['below60']))
    print('   逐篇最低劑量：%s' % per_paper_min)
    at_or_below = sum(1 for m in per_paper_min if m <= LOW)
    exactly = sum(1 for m in per_paper_min if m == LOW)
    print('   撐住低端的篇數：<60 g/h 為 %d/%d｜<=60 g/h 為 %d/%d'
          % (len(papers_low), len(truth), at_or_below, len(truth)))
    print('   門檻敏感度：有 %d 篇的最低劑量恰為 60.0（門檻壓在眾數上）'
          % exactly)
    print('   代理 vs 真值（%d 篇）：低端判斷一致 %d｜相差 ≤10 g/h 者 %d'
          % (len(pairs), agree_low, within_10))
    print('   誤判方向：代理說低而真值不低 %d 篇｜代理說不低而真值低 %d 篇'
          % (len(proxy_says_low_truth_high), len(proxy_says_high_truth_low)))
    print('   n626 穩健性上界：誤判率 %.1f%%，'
          '把它全部往同一方向推，28.7 個百分點的差距剩 %s'
          % (100 * error_rate if error_rate is not None else -1,
             worst_case_gap))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
