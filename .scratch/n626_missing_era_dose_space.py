# -*- coding: utf-8 -*-
"""**缺掉的那個年代，落在證據空間的哪個位置。**（第 626 輪）

## 🚨 承第 625 輪：「缺一個年代」還不夠，要說出缺口打在哪

⚠️ 第 625 輪量出語料對 2000 年以前零代表。**🚫 但那還是一句人口統計。**
🚨 擁有者要的是劑量-反應；**⚠️ 若缺的正好是曲線的某一端，那不是「少幾篇」，
是那一端沒有錨。**

## ✅ 本支怎麼量

篩選判詞 (`reason`) 是**本 run 自己寫的結構化註記**，其中常帶攝取率
（`g/min`、`g/h`）。本支從中抽出數字，**⚠️ 只輸出彙總分布**，
🚫 不輸出任何判詞文字、不輸出題名。

**⚠️ 抽得到的才算，抽不到的照數列出**——🚨 「沒抽到」與「劑量為零」不是同一件事，
而本支若把它們混起來，得到的分布會憑空多出一堆低劑量。

## ✅ 兩個必要的對照

| | 為什麼 |
|---|---|
| **甲：抽取器的正對照** | 🚨 若抽不出幾個數，任何「分布不同」都是抽取器的失敗，不是資料的性質 |
| **乙：置換零假設** | ⚠️ 兩組中位數不同很容易是抽樣雜訊；🚨 故以隨機重分組跑 2000 次，看實際差距在零分布的哪裡 |

## 🚫 本支不送任何外部請求、不改任何產品程式
"""
import json
import random
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

OUT = Path(__file__).resolve().parent / 'n626_missing_era_dose_space.json'
RUN = ROOT / 'search-runs/b11-exogenous-cho-endurance/b11-full-run'

# ⚠️ 兩種寫法都收，並各自轉成 g/h：g/min 乘 60。
# 🚨 樣式字面裡不得出現控制字元（第 576／583 輪各踩過一次）。
PER_MIN = re.compile(r'(\d+(?:[.]\d+)?)\s*g\s*/\s*min')
PER_HOUR = re.compile(r'(\d+(?:[.]\d+)?)\s*g\s*/\s*h')

PLAUSIBLE = (5.0, 250.0)  # g/h：⚠️ 超出此域者視為抽錯，不納入


def doses(text):
    """判詞裡所有可信的攝取率，一律換算成 g/h。"""
    values = [float(m) * 60 for m in PER_MIN.findall(text)]
    values += [float(m) for m in PER_HOUR.findall(text)]
    return [v for v in values if PLAUSIBLE[0] <= v <= PLAUSIBLE[1]]


def main():
    judgements = json.loads(
        (RUN / 'standard-full-screen-pass-1/judgements.json')
        .read_text(encoding='utf-8'))
    reason = {e['candidateId']: (e.get('reason') or '')
              for e in judgements['entries']}
    advance = {e['candidateId'] for e in judgements['entries']
               if e['opinion'] == 'advance'}

    pool = {r['candidateId']: r for r in json.loads(
        (RUN / 'candidate-pool/candidates.json').read_text(encoding='utf-8'))}

    status = {}
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        if not entry.is_dir() or entry.name.startswith(
                'ahig_candidate_publication_'):
            continue
        path = entry / 'manifest.json'
        if path.exists():
            doc = json.loads(path.read_text(encoding='utf-8'))
            status[doc['candidateId']] = doc.get('status')

    def year(cid):
        raw = pool.get(cid, {}).get('publicationYear')
        return int(raw) if raw else None

    # 🚨 這裡必須 sorted：`advance` 是 set，而字串雜湊每個行程都不同，
    # ⚠️ 於是值的**順序**每次執行都不一樣——洗牌切出來的分割跟著變，
    # **🚨 「固定種子故可重現」那句話就是假的**（實測 p 在 0.0034/0.0036 間晃）。
    # ✅ 排序之後，同一份資料每次得到同一個 p。
    groups = {
        '語料（已取得）': sorted(c for c in advance
                                if status.get(c) == 'acquired'),
        '未取得・2000 年前': sorted(c for c in advance
                                    if status.get(c) != 'acquired'
                                    and year(c) is not None and year(c) < 2000),
        '未取得・2000 年後': sorted(c for c in advance
                                    if status.get(c) != 'acquired'
                                    and year(c) is not None
                                    and year(c) >= 2000),
    }

    # 🚨 第一版以「值」為分析單位——⚠️ 同一篇的多個手臂被當成獨立樣本，
    # 一篇三臂的研究就這樣有了三票。**✅ 改為每篇一個值。**
    # ⚠️ 取該篇的**最低**攝取率：本支問的是「曲線的低端有沒有錨」，
    # 🚨 而一篇同時有 30 與 120 g/h 的研究，是有支撐低端的。
    summary = {}
    per_group_values = {}
    for label, ids in groups.items():
        values = []
        with_dose = 0
        for cid in ids:
            found = doses(reason.get(cid, ''))
            if found:
                with_dose += 1
                values.append(min(found))
        per_group_values[label] = values
        summary[label] = {
            'records': len(ids),
            'recordsWithDose': with_dose,
            'doseExtractionRate': round(100 * with_dose / len(ids), 1)
            if ids else None,
            'doseValuesRecordLevel': len(values),
            'medianGPerHour': round(statistics.median(values), 1)
            if values else None,
            'p10GPerHour': round(sorted(values)[len(values) // 10], 1)
            if len(values) >= 10 else None,
            'p90GPerHour': round(sorted(values)[-max(1, len(values) // 10)], 1)
            if len(values) >= 10 else None,
            'below60GPerHour': sum(1 for v in values if v < 60),
            'atOrAbove90GPerHour': sum(1 for v in values if v >= 90),
        }

    corpus_values = per_group_values['語料（已取得）']
    pre2000_values = per_group_values['未取得・2000 年前']

    # 乙：⚠️ 置換零假設。
    #
    # 🚨 第一版把合併清單「旋轉」當成置換——⚠️ 那只走得到 len(merged) 種
    # **連續切分**，相鄰的值永遠黏在一起，零分布是假的。
    # ✅ 真的置換要打散；而固定種子的洗牌本來就可重現——
    # ⚠️ 第一版那句「不得用 random」是本室自己矯枉過正。
    LOW = 60.0  # g/h：⚠️ 低端門檻，與 summary 的分箱一致
    trials = 5000
    seed = 20260901

    def permutation_p(stat, left, right):
        observed_value = stat(left, right)
        merged = list(left) + list(right)
        cut = len(left)
        rng = random.Random(seed)
        extreme = 0
        for _ in range(trials):
            rng.shuffle(merged)
            if abs(stat(merged[:cut], merged[cut:])) >= abs(observed_value):
                extreme += 1
        return observed_value, round(extreme / trials, 4)

    def median_diff(left, right):
        return statistics.median(left) - statistics.median(right)

    def low_share_diff(left, right):
        return (sum(1 for v in left if v < LOW) / len(left)
                - sum(1 for v in right if v < LOW) / len(right))

    observed = p_value = None
    observed_low = p_low = None
    if corpus_values and pre2000_values:
        observed, p_value = permutation_p(
            median_diff, corpus_values, pre2000_values)
        observed_low, p_low = permutation_p(
            low_share_diff, corpus_values, pre2000_values)

    # 丙：⚠️ 抽取率兩組不同（77% vs 61%）——🚨 若「抽不到」的那些系統性地
    # 不一樣，這場比較就是在一個偏斜的子樣本上做的。本支把它量出來。
    CHO_WORDS = re.compile(
        r'carbohydrate|glucose|fructose|maltodextrin|醣|葡萄糖|果糖',
        re.IGNORECASE)
    coverage = {}
    for label, ids in groups.items():
        lengths = [len(reason.get(c, '')) for c in ids]
        missed = [c for c in ids if not doses(reason.get(c, ''))]
        still_cho = sum(1 for c in missed if CHO_WORDS.search(reason.get(c, '')))
        coverage[label] = {
            'medianReasonLength': int(statistics.median(lengths))
            if lengths else None,
            'withoutDose': len(missed),
            'withoutDoseButStillCarbohydrate': still_cho,
            'share': round(100 * still_cho / len(missed), 1) if missed else None,
        }

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    total_with = sum(v['recordsWithDose'] for v in summary.values())
    probe('抽取器真的抽得到劑量（必觸發之正對照）',
          total_with >= 40,
          '🚨 三組合計 %d 筆判詞抽出劑量；⚠️ 若這個數很小，'
          '「分布不同」就是抽取器的失敗，不是資料的性質' % total_with)
    probe('抽不到的沒有被當成零（必觸發之反向）',
          all(0 not in per_group_values[k] for k in per_group_values),
          '🚨 三組的值裡都沒有 0；⚠️ 若「沒抽到」被記成 0，'
          '低劑量端會憑空多出一堆')
    probe('可信域真的擋掉了東西（必觸發）',
          any(doses('999 g/min') == [] for _ in (0,)),
          '🚨 以 999 g/min 試：被 %s g/h 的可信域擋下；'
          '⚠️ 若擋不下，任何極端值都會混進中位數' % (PLAUSIBLE,))
    probe('⚠️ 語料與缺掉那個年代的**中位劑量**沒有差異',
          p_value is None or p_value > 0.05,
          '語料中位 %s g/h、2000 年前未取得者中位 %s g/h，差 %s；'
          '置換 %d 次之 **p=%s**'
          % (summary['語料（已取得）']['medianGPerHour'],
             summary['未取得・2000 年前']['medianGPerHour'],
             round(observed, 1) if observed is not None else None,
             trials, p_value))
    probe('⚠️ 兩組落在**低端（<60 g/h）的比例**沒有差異',
          p_low is None or p_low > 0.05,
          '🚨 語料 %.0f%% 的篇落在低端、2000 年前未取得者 %.0f%%，'
          '差 %s 個百分點；置換 %d 次之 **p=%s**'
          % (100 * sum(1 for v in corpus_values if v < LOW)
             / max(1, len(corpus_values)),
             100 * sum(1 for v in pre2000_values if v < LOW)
             / max(1, len(pre2000_values)),
             round(100 * observed_low, 1) if observed_low is not None else None,
             trials, p_low))

    doc = {
        'schemaVersion': 1,
        'documentType': 'missing-era-dose-space',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'unit': 'g/h（g/min 一律乘 60 換算）',
        'plausibleRange': list(PLAUSIBLE),
        'groups': summary,
        'extractionCoverage': coverage,
        'coverageLimit': (
            '⚠️ 判詞長度三組幾乎相同（中位 196–200 字元），'
            '🚫 故抽取失敗不是「該組判詞比較短」造成的。'
            '🚨 但 2000 年前那組沒抽到劑量的 42 篇裡，**52% 的判詞仍寫著醣類**'
            '（另兩組只有 24–25%）——⚠️ 即該年代有較多「有做但判詞沒記劑量」者。'
            '**🚫 故本支的 65 篇樣本不等於該年代全貌。**'),
        'analysisUnit': (
            '✅ 每篇一個值（該篇的最低攝取率）——'
            '🚨 第一版以「值」為單位，同一篇的多手臂會重複計票。'),
        'permutation': {
            'trials': trials, 'seed': seed,
            'medianDiff': observed, 'medianDiffP': p_value,
            'lowShareDiff': observed_low, 'lowShareP': p_low,
            'note': ('✅ 真置換（固定種子的洗牌），故可重現；'
                     '🚨 第一版用的是「旋轉」——⚠️ 那只走得到連續切分，'
                     '零分布是假的。')},
        'contentDiscipline': (
            '✅ 本支只輸出數字分布；🚫 不輸出判詞文字、不輸出題名'
            '（n+195 一）。'),
        'whatThisCannotAnswer': (
            '🚫 判詞裡沒寫劑量的那些，本支一無所知——⚠️ 抽取率就是它的上限。'
            '🚫 也不判斷相關性：低劑量不等於不重要，'
            '⚠️ 它只是說「曲線的那一端目前由誰支撐」。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n626 缺掉的年代落在證據空間何處 ===')
    header = ('組', 'n', '抽到劑量', '抽取率', '中位 g/h', '<60', '≥90')
    print('   %-18s %4s %8s %7s %9s %5s %5s' % header)
    for label, value in summary.items():
        print('   %-18s %4d %8d %6s%% %9s %5d %5d'
              % (label, value['records'], value['recordsWithDose'],
                 value['doseExtractionRate'], value['medianGPerHour'],
                 value['below60GPerHour'], value['atOrAbove90GPerHour']))
    print('   置換檢定（每篇一值、固定種子、%d 次）：' % trials)
    print('      中位數差 %s g/h｜p=%s'
          % (round(observed, 1) if observed is not None else None, p_value))
    print('      低端(<%.0f g/h)佔比差 %s 個百分點｜p=%s'
          % (LOW,
             round(100 * observed_low, 1) if observed_low is not None else None,
             p_low))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
