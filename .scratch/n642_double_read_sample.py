# -*- coding: utf-8 -*-
"""**那「3/3 全一致」有多少份量。**（第 642 輪）

## 🚨 第 641 輪報了一個漂亮的數字，而漂亮的數字最該被追問

⚠️ 三篇雙讀在契約結局層級**全部一致**。🚨 但那是 **n=3**，而且沒有人問過：
**抽到的是不是剛好好讀的三篇。**

> **⚠️ 一個從簡單樣本得到的滿分，看起來跟一個從代表性樣本得到的滿分一模一樣。**

## ✅ 本支問兩件事

| | 問題 |
|---|---|
| **甲** | 那三篇跟另外 35 篇比，**在可量的軸上有沒有系統性不同** |
| **乙** | 3/3 一致這件事，**統計上能撐到哪裡** |

⚠️ 乙原本打算用**三法則**（3/n）。🚨 但 n=3 時它退化成 100%——**等於什麼都沒說**；
✅ 故改用**精確二項上界**：(1-p)^n = 0.05 ⇒ 上界 ≈ 63%。

**🚨 而甲那一問本支第一版只測了三個數值軸**——⚠️ 抽樣真正偏斜的是**來源型別**，
於是那道探針**為了錯的理由判綠**。✅ 已補上類別軸的檢定。

## 🚫 本支不改任何清冊或工作簿、不送外部請求、不改任何產品程式
"""
import collections
import json
import random
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n642_double_read_sample.json'
WORKSHEET = ROOT / 'extraction-worksheet'

TRIALS = 20000
SEED = 20260901


def main():
    source_type = {}
    for entry in sorted((ROOT / 'fulltext').iterdir()):
        if not entry.is_dir() or entry.name.startswith(
                'ahig_candidate_publication_'):
            continue
        path = entry / 'manifest.json'
        if path.exists():
            manifest = json.loads(path.read_text(encoding='utf-8'))
            source_type[manifest['candidateId']] = manifest.get('sourceType')

    features = {}
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        outcomes = doc.get('reportedOutcomes') or []
        features[doc['report']] = {
            'declared': len(outcomes),
            'inScope': sum(1 for o in outcomes
                           if (o.get('scopeDecision') or {}).get('inScope')),
            'sectionsScanned': len(
                (doc.get('completenessAttestation') or {})
                .get('sectionsScanned') or []),
            'sourceType': source_type.get(doc['report']),
        }

    sampled = set()
    for path in sorted((WORKSHEET / 'second').glob('page-*.json')):
        doc = json.loads(path.read_text(encoding='utf-8'))
        for entry in doc.get('entries') or []:
            if entry['report'] in features:
                sampled.add(entry['report'])
    rest = [r for r in features if r not in sampled]

    def values(reports, key):
        return [features[r][key] for r in reports]

    # 甲：⚠️ 三個可量的軸，各做一次置換檢定。
    rng_seed = SEED

    def permutation_p(reports_a, reports_b, key):
        """⚠️ 抽到的那幾篇平均值，跟隨機抽同樣張數比起來有多極端。"""
        pool = sorted(reports_a) + sorted(reports_b)  # 🚨 排序：可重現
        observed = statistics.mean(values(reports_a, key))
        cut = len(reports_a)
        rng = random.Random(rng_seed)
        extreme = 0
        overall = statistics.mean(values(pool, key))
        for _ in range(TRIALS):
            rng.shuffle(pool)
            if abs(statistics.mean(values(pool[:cut], key)) - overall) \
                    >= abs(observed - overall):
                extreme += 1
        return observed, round(extreme / TRIALS, 4)

    axes = {}
    for key, label in (('declared', '宣告的結局數'),
                       ('inScope', '在範圍內項數'),
                       ('sectionsScanned', '掃過的段落數')):
        observed, p_value = permutation_p(sorted(sampled), rest, key)
        axes[label] = {
            'sampledMean': round(observed, 2),
            'restMean': round(statistics.mean(values(rest, key)), 2),
            'pValue': p_value,
        }

    sampled_sources = collections.Counter(
        features[r]['sourceType'] for r in sampled)
    rest_sources = collections.Counter(
        features[r]['sourceType'] for r in rest)

    # 🚨 本支第一版只測了三個**數值**軸，⚠️ 而抽樣在**來源型別**上明顯偏斜
    # （抽到的三篇全是 grobid-tei）——**那道探針因此為了錯的理由判綠。**
    # ✅ 補上：以超幾何機率算「隨機抽 3 篇全是 grobid」有多罕見。
    grobid_total = sum(1 for r in features
                       if features[r]['sourceType'] == 'grobid-tei')
    total = len(features)
    picked = len(sampled)
    sampled_all_grobid = all(features[r]['sourceType'] == 'grobid-tei'
                             for r in sampled)
    probability_all_grobid = 1.0
    for i in range(picked):
        probability_all_grobid *= (grobid_total - i) / (total - i)

    # 乙：⚠️ 三法則在 n=3 退化成 3/3 ＝ 100%，**等於什麼都沒說**。
    # ✅ 故改用精確的二項上界：(1-p)^n = 0.05 ⇒ p = 1 - 0.05^(1/n)。
    n = len(sampled)
    rule_of_three = round(3.0 / n, 3) if n else None
    exact_upper = round(1 - 0.05 ** (1.0 / n), 3) if n else None

    unusual = [label for label, row in axes.items() if row['pValue'] < 0.05]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('抽樣與其餘都數得出來（必觸發之正對照）',
          len(sampled) == 3 and len(rest) == 35,
          '🚨 抽樣 %d 篇、其餘 %d 篇；⚠️ 對不上代表本支讀的不是同一批'
          % (len(sampled), len(rest)))
    probe('置換檢定可重現（必觸發之正對照）',
          all(row['pValue'] is not None for row in axes.values()),
          '🚨 三個軸都算得出 p；⚠️ 池子先排序過，故同一份資料每次同一個 p')
    # 🚨 以下兩道是答案。
    probe('抽到的三篇在三個**數值**軸上不特別',
          not unusual,
          '%s 與其餘 35 篇有顯著差異的數值軸：%s；明細：%s'
          % ('✅' if not unusual else '🚨', unusual or '無',
             json.dumps(axes, ensure_ascii=False)))
    probe('抽樣在**來源型別**上也不特別',
          not (sampled_all_grobid and probability_all_grobid < 0.05),
          '🚨 抽到的 %d 篇**全是 grobid-tei**，而全庫 %d/%d 是 grobid；'
          '⚠️ 隨機抽到這種組合的機率 **%.3f**——'
          '**🚨 即 24 篇 europe-pmc-jats 從未被雙讀過。**'
          '⚠️ 本支第一版只測數值軸，那道探針因此**為了錯的理由判綠**'
          % (picked, grobid_total, total, probability_all_grobid))
    probe('3/3 一致足以支撐「不一致率很低」',
          False,
          '🚨 **三法則在 n=3 退化成 3/3 ＝ %.0f%%，等於什麼都沒說**——'
          '⚠️ 故改用精確二項上界：(1-p)^%d = 0.05 ⇒ '
          '真實不一致率的 95%% 單側上界 ≈ **%.0f%%**。'
          '🚫 這不是說結果不好，✅ 是說 n=3 撐不起「很低」這個詞'
          % (100 * rule_of_three, n, 100 * exact_upper))

    doc = {
        'schemaVersion': 1,
        'documentType': 'double-read-sample-quality',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'sampled': sorted(r[-16:] for r in sampled),
        'sampledCount': len(sampled),
        'restCount': len(rest),
        'axes': axes,
        'sourceTypeMix': {'sampled': dict(sampled_sources),
                          'rest': dict(rest_sources)},
        'sourceTypeSkew': {
            'sampledAllGrobid': sampled_all_grobid,
            'grobidInCorpus': '%d/%d' % (grobid_total, total),
            'probabilityIfRandom': round(probability_all_grobid, 4),
            'consequence': ('🚨 24 篇 europe-pmc-jats **從未被雙讀過**——'
                            '⚠️ 而那是語料的多數。'),
        },
        'ruleOfThree': {
            'n': n,
            'ruleOfThreeUpperBound': rule_of_three,
            'ruleOfThreeIsDegenerateHere': (
                '🚨 3/n 在 n=3 時等於 1.0——**⚠️ 那個上界什麼都沒說**；'
                '✅ 故本支改用精確二項上界。'),
            'exactUpperBound95': exact_upper,
            'reading': ('✅ 精確上界：(1-p)^%d = 0.05 ⇒ 真實不一致率的 '
                        '95%% 單側上界 ≈ **%.0f%%**。'
                        '⚠️ 即現有證據容得下相當高的不一致率——'
                        '🚫 不是說結果不好，是說 n=3 撐不起「很低」這個詞。'
                        % (n, 100 * exact_upper)),
        },
        'permutation': {'trials': TRIALS, 'seed': SEED,
                        'note': '✅ 池子先排序，故可重現。'},
        'whatThisIsNot': (
            '🚫 本支不是說第 641 輪的 3/3 有錯——⚠️ 那個數字是對的。'
            '🚨 本支說的是它**能撐多重**：'
            '✅ 抽樣在三個數值軸上不特別，'
            '🚨 但在**來源型別**上明顯偏斜（3 篇全是 grobid-tei，機率 0.043），'
            '⚠️ 且 n=3 這個量體本身就限制了結論的強度。'),
        'whatThisCannotAnswer': (
            '🚫 「可量的軸」只有三個——⚠️ 論文的難讀程度（表格複雜度、'
            '報告品質）本支量不到；🚨 故「抽樣不特別」只在這三軸上成立。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n642 雙讀抽樣的份量 ===')
    print('   抽樣 %d 篇｜其餘 %d 篇' % (len(sampled), len(rest)))
    print('   %-14s %10s %10s %8s' % ('軸', '抽樣平均', '其餘平均', 'p'))
    for label, row in axes.items():
        print('   %-14s %10s %10s %8s'
              % (label, row['sampledMean'], row['restMean'], row['pValue']))
    print('   來源型別：抽樣 %s｜其餘 %s'
          % (dict(sampled_sources), dict(rest_sources)))
    print('   來源型別偏斜：抽樣全 grobid=%s｜隨機抽到的機率 %.3f'
          % (sampled_all_grobid, probability_all_grobid))
    print('   不一致率 95%% 上界：三法則 %.0f%%（退化）｜精確二項 %.0f%%'
          % (100 * rule_of_three, 100 * exact_upper))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
