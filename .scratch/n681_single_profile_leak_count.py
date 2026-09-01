# -*- coding: utf-8 -*-
"""**只跑一份 profile，會放過幾個？**（第 681 輪）

## ✅ 補上第 679 輪自己寫下的限制

n679：「🚫 本支只比**類別層級**的守備，沒有比『同一個類別上，兩邊的規則是否等價』」。

⚠️ 規則等價**沒辦法用語法判**——Core 用 property shape 與 `sh:or`，
SPARQL 用 `sh:sparql`，寫法本來就不同。

> **✅ 但有一個行為上的精確做法：把**每一個負向對照**對**兩份 profile 都驗一次**。**
> **🚨 「只跑一份會放過幾個」是一個數得出來的數字。**

## 🚨 而現行測試量不到這件事

`test_every_negative_canary_is_blocked` 只跑 `canary.profiles`——
⚠️ 也就是**每個對照自己宣告的那幾份**。
🚨 故「某個對照在另一份 profile 下會通過」這件事，**現行測試看不到**。

## 🚫 本支不改產品程式與測試、不送外部請求
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
AHIG = REPO / 'ahig'
sys.path.insert(0, str(AHIG))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.gates import shacl as G  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n681_single_profile_leak.json'
PROFILES = (G.CORE_PROFILE, G.SPARQL_PROFILE)


def main():
    shapes = {p: G.load_shapes(p) for p in PROFILES}
    combined = G.load_combined_shapes()

    negatives, positives = [], []
    for canary in G.iter_canaries('negative'):
        blocked = {}
        for profile in PROFILES:
            outcome = G.validate_graph(canary.data, shapes[profile])
            blocked[str(profile)] = not outcome.conforms
        both = G.validate_graph(canary.data, combined)
        negatives.append({
            'canary': canary.name,
            'declaredProfiles': [str(p) for p in canary.profiles],
            'blockedBy': blocked,
            'blockedByCombined': not both.conforms,
        })
    for canary in G.iter_canaries('positive'):
        conforms = {}
        for profile in PROFILES:
            conforms[str(profile)] = G.validate_graph(
                canary.data, shapes[profile]).conforms
        positives.append({'canary': canary.name, 'conforms': conforms,
                          'combined': G.validate_graph(
                              canary.data, combined).conforms})

    leak = collections.Counter()
    leaked_by = collections.defaultdict(list)
    for row in negatives:
        for profile, is_blocked in row['blockedBy'].items():
            if not is_blocked:
                leak[profile] += 1
                leaked_by[profile].append(row['canary'])
    blocked_by_neither = [r['canary'] for r in negatives
                          if not any(r['blockedBy'].values())]
    not_blocked_combined = [r['canary'] for r in negatives
                            if not r['blockedByCombined']]
    misjudged_positive = [r['canary'] for r in positives if not r['combined']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('對照組載得進來、兩份 profile 也載得進來（必觸發之正對照）',
          len(negatives) >= 15 and len(positives) >= 4
          and all(len(g) > 0 for g in shapes.values()),
          '🚨 負向 %d 個、正向 %d 個；⚠️ 太少代表本支沒讀到 canary'
          % (len(negatives), len(positives)))
    probe('正向對照在合併形狀下必須全部通過（必觸發之反向）',
          not misjudged_positive,
          '🚨 被誤擋的正向對照：%s；'
          '⚠️ 若正向也被擋，「擋得住」就只是因為什麼都擋'
          % (misjudged_positive or '無'))
    probe('兩份都跑時，每個負向對照都擋得住（必觸發之正對照）',
          not not_blocked_combined and not blocked_by_neither,
          '🚨 合併形狀下仍通過的負向對照：%s；兩份都擋不住的：%s；'
          '⚠️ 有的話就是真的破洞，🚫 不只是「該跑哪一份」的問題'
          % (not_blocked_combined or '無', blocked_by_neither or '無'))
    # 🚨 這一道是答案。
    probe('只跑一份 profile 就擋得住全部負向對照',
          not leak,
          '🚨 只跑 core 放過 %d 個：%s；只跑 sparql 放過 %d 個：%s；'
          '⚠️ 這就是「只驗一份形狀會放東西過去」的**數字版本**'
          % (leak.get(str(G.CORE_PROFILE), 0),
             leaked_by.get(str(G.CORE_PROFILE), []) or '無',
             leak.get(str(G.SPARQL_PROFILE), 0),
             leaked_by.get(str(G.SPARQL_PROFILE), []) or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'single-profile-leak-count',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n679 → methodLimit（只比類別層級）',
        'strengthensDecision': (
            '📮 D26（第 680 輪登記）。⚠️ 本支**不新增決策**——'
            '🚨 它給的是 D26 需要的那個數字：只跑一份會放過幾個。'
            '✅ 下一版登記簿會把本支掛進 D26 的證據；'
            '⚠️ 本室把這句寫在這裡，🚫 免得它變成沒人接的紅燈。'),
        'negativeCanaries': len(negatives),
        'positiveCanaries': len(positives),
        'leakIfOnlyOneProfile': {k: v for k, v in leak.items()},
        'leakedCanaries': {k: sorted(v) for k, v in leaked_by.items()},
        'blockedByNeither': blocked_by_neither,
        'stillConformingUnderCombined': not_blocked_combined,
        'rows': negatives,
        'positives': positives,
        'whyCurrentTestsCannotSeeThis': (
            '⚠️ `test_every_negative_canary_is_blocked` 只跑'
            '**每個對照自己宣告的 profile**；'
            '🚨 故「某個對照在另一份 profile 下會通過」這件事，'
            '**現行測試看不到**。'
            '✅ 本支對每一個都跑**兩份**，才量得出這個數字。'),
        'readingNote': (
            '🚨 「只跑 core 放過 N 個」🚫 不等於 Core 有缺陷——'
            '⚠️ 那些規則本來就設計成住在 SPARQL 那一份（跨實體稽核）。'
            '**✅ 本支要說的是：驗收流程若只跑一份，就會漏掉這 N 個。**'),
        'methodLimit': (
            '⚠️ 本支量的是**對照組覆蓋得到的那些規則**，'
            '🚫 量不到「沒有對照組的規則」——'
            '🚨 一條沒有 canary 的規則，兩份 profile 都不會在這裡現形。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n681 只跑一份 profile 會放過幾個 ===')
    print('   負向對照 %d 個｜正向 %d 個' % (len(negatives), len(positives)))
    for profile in PROFILES:
        key = str(profile)
        print('   只跑 %-8s 放過 %d 個：%s'
              % (key, leak.get(key, 0), sorted(leaked_by.get(key, [])) or '無'))
    print('   兩份都擋不住的：%s' % (blocked_by_neither or '無'))
    print('   合併形狀下仍通過的：%s' % (not_blocked_combined or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
