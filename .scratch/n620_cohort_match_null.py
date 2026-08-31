# -*- coding: utf-8 -*-
"""**那對 6／6 全中，隨機撞得出來嗎？**（第 620 輪）

## 🚨 這是本 run 影響最大的一個發現，而它最該被檢驗

第 582 輪找到一對論文，受試者特徵 **6 個值全部逐字相同**，
✅ 而它支撐著 **D3**（那兩筆要不要合併成一個 study）。

⚠️ 當時量過**經驗巧合率**（820 對裡只有 3 對共用 1 個值）——
**🚫 但沒有做過虛無模型。**

> 🚨 受試者特徵裡有很多「好撞」的值（例如 `3±1`、`8±2`）。
> **⚠️ 若把數值隨機打散也能撞出「≥2 個相同且佔小者一半以上」，那個發現就不牢。**

## ✅ 做法：把數值打散，保持每篇的個數

保持每篇的特徵值**個數**不變，把全部值洗牌重新分配，
重跑第 583 輪的同一條判準（**相同 ≥2 個 且 佔較小者 ≥50%**），
數出「可能同一批」的配對數。⚠️ 固定種子、可複驗。
"""
import collections
import itertools
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n620_cohort_match_null.json'
VALUES = ROOT / 'extraction' / 'n582-cohort-values.json'
SEED = 20260903
TRIALS = 400
MIN_SHARED = 2
MIN_RATIO = 0.5


def same_cohort_pairs(values):
    """✅ 第 583 輪那條判準：⚠️ 相同 ≥2 個，且佔較小那一方 ≥50%。"""
    keys = sorted(values)
    hits = []
    for a, b in itertools.combinations(keys, 2):
        shared = len(values[a] & values[b])
        smaller = min(len(values[a]), len(values[b]))
        if not smaller:
            continue
        if shared >= MIN_SHARED and shared / smaller >= MIN_RATIO:
            hits.append((a, b, shared, round(shared / smaller, 2)))
    return hits


def main():
    stored = json.loads(VALUES.read_text(encoding='utf-8'))['values']
    values = {k: set(v) for k, v in stored.items()}
    observed = same_cohort_pairs(values)

    pool = [value for group in values.values() for value in group]
    sizes = {k: len(v) for k, v in values.items()}
    rng = random.Random(SEED)
    null = []
    for _ in range(TRIALS):
        shuffled = pool[:]
        rng.shuffle(shuffled)
        cursor, fake = 0, {}
        for key, size in sizes.items():
            fake[key] = set(shuffled[cursor:cursor + size])
            cursor += size
        null.append(len(same_cohort_pairs(fake)))
    # 🚨 光看「幾對」還不夠：⚠️ 觀察那一對是 **6 個值全中**。
    # ✅ 故也量虛無曾撞到的**最大共用值數**——那才比得出量級。
    rng3 = random.Random(SEED)
    max_shared = collections.Counter()
    for _ in range(TRIALS):
        shuffled = pool[:]
        rng3.shuffle(shuffled)
        cursor, fake = 0, {}
        for key, size in sizes.items():
            fake[key] = set(shuffled[cursor:cursor + size])
            cursor += size
        best = 0
        for a, b in itertools.combinations(sorted(fake), 2):
            best = max(best, len(fake[a] & fake[b]))
        max_shared[best] += 1

    null.sort()
    mean = sum(null) / len(null)
    at_or_above = sum(1 for n in null if n >= len(observed))
    p_value = (at_or_above + 1) / (TRIALS + 1)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('取到了第 582 輪那批數值（必觸發）',
          len(values) == 41 and sum(sizes.values()) > 0,
          '🚨 對不上就代表本支比的不是同一批；實得 %d 篇／%d 個值'
          % (len(values), sum(sizes.values())))
    probe('觀察值與第 583 輪一致（必觸發）',
          len(observed) == 1,
          '🚨 對不上代表判準寫得不一樣；實得 %d 對 %s'
          % (len(observed), [(a, b, s, r) for a, b, s, r in observed]))
    # 🚨 必觸發之反向：⚠️ 打散後要真的還撞得出「相同的值」，否則比較是空的。
    shared_any = 0
    rng2 = random.Random(SEED + 1)
    shuffled = pool[:]
    rng2.shuffle(shuffled)
    cursor, sample = 0, {}
    for key, size in sizes.items():
        sample[key] = set(shuffled[cursor:cursor + size])
        cursor += size
    for a, b in itertools.combinations(sorted(sample), 2):
        shared_any += 1 if sample[a] & sample[b] else 0
    probe('打散後仍會撞到相同的值（必觸發之反向）',
          shared_any > 0,
          '✅ 單次打散後有 %d 對至少共用一個值；🚨 若為零，'
          '代表數值太獨特而虛無無效，🚫 那樣本輪的比較沒有意義' % shared_any)
    # 🚨 這一道的紅綠就是答案。
    observed_shared = max((s for _a, _b, s, _r in observed), default=0)
    null_best = max(max_shared)
    probe('虛無撞不到觀察那個量級（必觸發之反向）',
          null_best < observed_shared,
          '🚨 虛無 400 次中單次最大共用值數的分布 %s——最多只到 %d，'
          '而觀察那一對是 **%d 個**；⚠️ 故它不只是「不是偶然」，'
          '✅ 量級也是虛無達不到的'
          % (dict(sorted(max_shared.items())), null_best, observed_shared))
    probe('觀察到的同批配對超出偶然',
          p_value < 0.05,
          '⚠️ 觀察 %d 對；虛無平均 %.2f、範圍 %d–%d；'
          '🚨 %d／%d 次隨機達到或超過，p ≈ %.3f'
          % (len(observed), mean, null[0], null[-1], at_or_above, TRIALS,
             p_value))

    doc = {
        'schemaVersion': 1,
        'documentType': 'cohort-match-null',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'seed': SEED, 'trials': TRIALS,
        'criterion': {'minShared': MIN_SHARED, 'minRatioOfSmaller': MIN_RATIO},
        'reports': len(values),
        'observedPairs': [{'pair': [a, b], 'shared': s, 'ratio': r}
                          for a, b, s, r in observed],
        'nullMean': round(mean, 3),
        'nullRange': [null[0], null[-1]],
        'nullZeroTrials': sum(1 for n in null if n == 0),
        'timesNullReachedObserved': at_or_above,
        'pValue': round(p_value, 4),
        'nullMaxSharedDistribution': dict(sorted(max_shared.items())),
        'observedSharedValues': observed_shared,
        'pairsSharingAnyValueInOneShuffle': shared_any,
        'whyThisMatters': (
            '🚨 這一對支撐著 D3（那兩筆是否合併成一個 study）。'
            '⚠️ 而受試者特徵裡有很多好撞的值——'
            '✅ 故必須問：隨機打散撞不撞得出來。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n620 同批配對的虛無分布 ===')
    print('   %d 篇／%d 個值｜觀察 %d 對：%s'
          % (len(values), sum(sizes.values()), len(observed),
             [(a, b, '%d 個／%.0f%%' % (s, r * 100)) for a, b, s, r in observed]))
    print('   虛無（%d 次、種子 %d）：平均 %.2f｜範圍 %d–%d｜為零者 %d 次'
          % (TRIALS, SEED, mean, null[0], null[-1],
             sum(1 for n in null if n == 0)))
    print('   🚨 虛無單次最大共用值數：%s（最多 %d）｜觀察那一對是 %d 個'
          % (dict(sorted(max_shared.items())), max(max_shared), observed_shared))
    print('   🚨 隨機達到或超過觀察值：%d／%d（p ≈ %.3f）'
          % (at_or_above, TRIALS, p_value))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
