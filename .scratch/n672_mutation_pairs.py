# -*- coding: utf-8 -*-
"""**兩個排除條件同時成立時，理由碼會不會騙人。**（第 672 輪）

## ✅ 這一輪是索引擋下來的

本室原本要問「契約裡有哪幾道門從來沒擋過東西」。
🚨 照第 671 輪立的規矩，動手前用**爭點識別字**（那六個沒走過的理由碼）查了一次——
**✅ `n639_decision_space_coverage` 與 `n640_branch_reachability` 就是那一題**，
⚠️ 而且 n640 已經用突變證明每條沒走過的分支都驅動得起來。

> **🚨 那一輪本來會是整輪重工。**

## ✅ 於是接 n640 自己寫下的缺口

n640 的 `whatThisCannotAnswer` 寫著：

> 「🚫 本支只驅動單一欄位的突變——⚠️ **多欄位交互未受檢**。」

## 🚨 為什麼這件事要緊

`decide()` **依序短路**，理由碼只是**第一道**擋下它的門
（第 665 輪已在真實資料上吃過這個虧）。
⚠️ 那麼當兩個排除條件同時成立時：

1. 亮的是不是**程式順序上比較早**的那一道（可預測）
2. **🚨 有沒有哪一對會互相遮蔽，讓它反而留在範圍內**（那才是缺陷）

## ✅ 做法

拿語料裡**第一筆在範圍內**的紀錄當模板（🚫 非手刻），
先確認**每個單一突變自己會擋**，再跑**所有兩兩配對**。

## 🚫 本支不改任何清冊與契約、不送外部請求
"""
import itertools
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

OUT = Path(__file__).resolve().parent / 'n672_mutation_pairs.json'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

# 🚨 程式裡的判定順序（`decide()` 由上而下），⚠️ 用來預測配對時該亮哪一條。
CODE_ORDER = [
    'SCOPE-000-no-numeric-result',
    'SCOPE-001b-instrument',
    'SCOPE-002-timepoint',
    'SCOPE-002c-multiple-measurements',
    'SCOPE-003-analysis-set',
    'SCOPE-004-effect-measure',
    'SCOPE-005-model',
    'SCOPE-006-subgroup',
    'SCOPE-007-sensitivity',
    'SCOPE-008-dose',
]

MUTATIONS = {
    '沒有數值': ({'hasNumericResult': False}, 'SCOPE-000-no-numeric-result'),
    '儀器不在清單': ({'instrument': 'instrument-not-real-672'},
                     'SCOPE-001b-instrument'),
    '時點在窗外': ({'timepointDays': 9999.0, 'timepointSessions': None},
                   'SCOPE-002-timepoint'),
    '同窗多測量點': ({'multipleMeasurementsInWindow': True},
                     'SCOPE-002c-multiple-measurements'),
    '分析集不在範圍': ({'analysisSet': 'analysis-set-not-real-672'},
                       'SCOPE-003-analysis-set'),
    '效應量測不在範圍': ({'effectMeasure': 'effect-measure-not-real-672'},
                         'SCOPE-004-effect-measure'),
    '統計模型不在範圍': ({'statisticalModel': 'model-not-real-672'},
                         'SCOPE-005-model'),
    '未預先指定的次群': ({'isSubgroup': True, 'subgroupPrespecified': False},
                         'SCOPE-006-subgroup'),
    '敏感度分析': ({'isSensitivityAnalysis': True},
                   'SCOPE-007-sensitivity'),
    '劑量在帶外': ({'dose': 9999.0}, 'SCOPE-008-dose'),
}

# ✅ 必觸發之反向用：judge() 根本不看這兩欄。
HARMLESS = {'localLabel': 'ZZ-672-harmless-ZZ',
            'sourceLocation': {'section': 'ZZ-672-ZZ'}}


def template(matcher):
    """語料裡第一筆在範圍內的紀錄。🚫 非手刻。"""
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if decision['inScope']:
                return dict(reported), inventory['report'][-16:]
    return None, None


def apply(base, *patches):
    item = dict(base)
    for patch in patches:
        item.update(patch)
    return item


def main():
    contract = json.loads(CONTRACT.read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)
    base, source = template(matcher)
    if base is None:
        print('🚨 語料裡找不到在範圍內的紀錄，本支無從測起')
        return 1

    baseline = matcher.decide(base)
    order = {rule: i for i, rule in enumerate(CODE_ORDER)}

    singles = {}
    for label, (patch, expected) in MUTATIONS.items():
        got = matcher.decide(apply(base, patch))
        singles[label] = {'expectedRule': expected, 'gotRule': got.rule_id,
                          'inScope': got.in_scope,
                          'asExpected': (not got.in_scope
                                         and got.rule_id == expected)}

    pairs, surprises, masked = [], [], []
    for a, b in itertools.combinations(sorted(MUTATIONS), 2):
        patch_a, rule_a = MUTATIONS[a]
        patch_b, rule_b = MUTATIONS[b]
        got = matcher.decide(apply(base, patch_a, patch_b))
        expected = min([rule_a, rule_b],
                       key=lambda r: order.get(r, len(CODE_ORDER)))
        row = {'pair': [a, b], 'expectedRule': expected,
               'gotRule': got.rule_id, 'inScope': got.in_scope}
        if got.in_scope:
            masked.append(row)
        elif got.rule_id != expected:
            surprises.append(row)
        pairs.append(row)

    harmless = matcher.decide(apply(base, HARMLESS))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('模板本身判為在範圍內（必觸發之正對照）',
          baseline.in_scope,
          '🚨 模板取自 %s，判定 in_scope=%s／rule=%s；'
          '⚠️ 模板自己就過不了的話，底下每一條都測不到自己想測的東西'
          % (source, baseline.in_scope, baseline.rule_id))
    bad_singles = [k for k, v in singles.items() if not v['asExpected']]
    probe('每個單一突變都擋得下、且亮的是自己那一條（必觸發之正對照）',
          not bad_singles,
          '🚨 %d 個單一突變，未如預期者：%s；'
          '⚠️ 單一都不準的話，配對的結果沒有意義'
          % (len(singles),
             {k: singles[k] for k in bad_singles} or '無'))
    probe('只改判定用不到的欄位時，必須仍在範圍內（必觸發之反向）',
          harmless.in_scope,
          '🚨 只改 localLabel／sourceLocation：in_scope=%s；'
          '⚠️ 若這樣也被擋，代表本支的「改動」本身就會讓它掉出去，'
          '配對結論全部作廢' % harmless.in_scope)
    probe('🚨 沒有任何一對會互相遮蔽而讓它留在範圍內（必觸發之反向）',
          not masked,
          '🚨 配對 %d 組，遮蔽者 %d 組：%s；'
          '⚠️ 這才是真缺陷——**兩個各自都該擋的條件湊在一起反而放行**'
          % (len(pairs), len(masked), masked or '無'))
    # 🚨 這一道是答案。
    probe('配對時亮的都是程式順序較早的那一道（可預測）',
          not surprises,
          '🚨 %d 組不如預期：%s；'
          '⚠️ 不可預測代表「這一項為什麼被擋」在報表上說不清楚'
          % (len(surprises), surprises or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'mutation-pair-interaction',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesGapDeclaredBy': 'n640_branch_reachability.json → '
                               'whatThisCannotAnswer（多欄位交互未受檢）',
        'foundByIndex': (
            '✅ 本輪原訂的題目（哪幾道門從未擋過東西）'
            '被第 670／671 輪的索引擋下——**🚨 n639 與 n640 已經做過**。'
            '⚠️ 那是索引第一次在**真實情境**下擋下重工，🚫 不是回溯測試。'),
        'templateFrom': source,
        'baseline': {'inScope': baseline.in_scope,
                     'ruleId': baseline.rule_id},
        'singles': singles,
        'pairsTested': len(pairs),
        'pairs': pairs,
        'maskedPairs': masked,
        'unexpectedRulePairs': surprises,
        'harmlessControl': {'inScope': harmless.in_scope,
                            'ruleId': harmless.rule_id},
        'whatThisCannotAnswer': (
            '🚫 本支只跑**兩兩**配對，⚠️ 三個以上同時成立未受檢；'
            '🚨 且模板只有一筆——**亮得對不表示在別的紀錄上也亮得對**。'
            '⚠️ 又：`SCOPE-002b` 與 `SCOPE-100` 不在本支的突變表裡，'
            '前者要靠重疊時窗（n640 已證在合法契約裡到不了），'
            '後者要靠整份清冊而非單筆紀錄。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n672 兩個排除條件同時成立時 ===')
    print('   模板取自 %s｜基線 in_scope=%s'
          % (source, baseline.in_scope))
    print('   單一突變 %d 個｜未如預期 %d 個'
          % (len(singles), len(bad_singles)))
    for label in sorted(singles):
        v = singles[label]
        print('      %-20s %-34s %s'
              % (label, v['gotRule'], '✅' if v['asExpected'] else '🚨'))
    print('   兩兩配對 %d 組｜遮蔽 %d 組｜亮錯條 %d 組'
          % (len(pairs), len(masked), len(surprises)))
    for row in surprises[:10]:
        print('      🚨 %s：預期 %s／實得 %s'
              % (row['pair'], row['expectedRule'], row['gotRule']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
