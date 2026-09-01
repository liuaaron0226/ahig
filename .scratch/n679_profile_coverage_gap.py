# -*- coding: utf-8 -*-
"""**一條測試的名字承諾了它沒有做的事——而那個承諾本身是假的。**（第 679 輪）

## ✅ 從第 678 輪那個「只驗一份形狀會放東西過去」追下來

⚠️ 那一輪的示範是用 canary 做的。🚨 本輪問的是：**現行測試擋不擋得住這件事**。

## 🚨 找到 `tests/test_shacl_gates.py` 這一條

```
def test_sparql_profile_still_targets_every_class_core_targets():
    \"\"\"兩個 profile 的守備範圍必須一致；SPARQL 是稽核，不是縮編。\"\"\"
    core = G.targeted_classes(G.load_shapes(G.CORE_PROFILE))
    sparql = G.targeted_classes(G.load_shapes(G.SPARQL_PROFILE))
    assert core, "Core 沒有 target 任何類別"
    assert sparql, "SPARQL 沒有 target 任何類別"
```

> **🚨 函式名與註解都說「守備範圍必須一致」，
> ⚠️ 但主體只斷言兩者非空——**從頭到尾沒有比較過**。**

## 🚨 而那個承諾實測是假的

`OutcomeInventory` 與 **`QuantitativeStudyResult`** **只有 core 守備**。
⚠️ 而後者正是第 677 輪那條規則的所在：
**「量化 StudyResult 必須有點估計」「必須有不確定性區間」。**

> **🚨 也就是說：只用 SPARQL（稽核）profile 驗，
> 一個沒有信賴區間的量化結果會通過。**

## ⚠️ 本室不指控哪一邊錯

✅ 兩種讀法都成立：**要嘛測試名不副實，要嘛註解寫錯了**。
🚨 但兩者都會讓讀者相信一件沒發生的事——**📮 而哪一邊該改，是裁定。**

## 🚫 本支不改產品程式、不改測試、不送外部請求
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
AHIG = REPO / 'ahig'
sys.path.insert(0, str(AHIG))

import rdflib  # noqa: E402

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.gates import shacl as G  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n679_profile_coverage_gap.json'
SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')

TEST_FILE = AHIG / 'tests' / 'test_shacl_gates.py'
TEST_NAME = 'test_sparql_profile_still_targets_every_class_core_targets'


def short(term):
    return str(term).rsplit('/', 1)[-1]


def rules_on(graph, classes):
    """那些只有一邊守備的類別上，掛著哪些具名規則。"""
    out = []
    for shape, _, cls in graph.triples((None, SH.targetClass, None)):
        if cls not in classes:
            continue
        for pred in (SH.property, SH.sparql):
            for _, _, node in graph.triples((shape, pred, None)):
                msg = graph.value(node, SH.message)
                if msg:
                    out.append({'class': short(cls), 'shape': short(shape),
                                'message': str(msg)})
    return sorted(out, key=lambda r: (r['class'], r['message']))


def mutation_still_passes():
    """🚨 突變證明：把 sparql 換成一個與 core 完全不相交的集合，
    那條測試的**斷言主體**照樣通過——⚠️ 即它偵測不到縮編。
    """
    core = {'A', 'B'}
    sparql = {'Z'}          # 🚨 與 core 完全不相交
    try:
        assert core, 'Core 沒有 target 任何類別'
        assert sparql, 'SPARQL 沒有 target 任何類別'
        return True
    except AssertionError:
        return False


def main():
    core_graph = G.load_shapes(G.CORE_PROFILE)
    sparql_graph = G.load_shapes(G.SPARQL_PROFILE)
    core = set(G.targeted_classes(core_graph))
    sparql = set(G.targeted_classes(sparql_graph))

    core_only = sorted(core - sparql, key=short)
    sparql_only = sorted(sparql - core, key=short)
    orphan_rules = rules_on(core_graph, set(core_only))

    source = TEST_FILE.read_text(encoding='utf-8')
    start = source.find('def %s' % TEST_NAME)
    body = source[start:source.find('\n\n\n', start)] if start >= 0 else ''
    compares = ('<=' in body or 'issubset' in body
                or ('core' in body and 'sparql' in body and '==' in body))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩個 profile 都讀得到、也都守備得到東西（必觸發之正對照）',
          len(core) >= 5 and len(sparql) >= 5,
          '🚨 core 守備 %d 類、sparql 守備 %d 類；⚠️ 太少代表本支讀錯了圖'
          % (len(core), len(sparql)))
    probe('捏造的類別不在任一 profile 的守備裡（必觸發之反向）',
          not any(short(c) == 'ClassThatCannotExist679'
                  for c in core | sparql),
          '🚨 捏造類別不在守備清單；⚠️ 若在，代表抽的不是真的 target')
    probe('那條測試的主體真的沒有比較兩個集合（必觸發之正對照）',
          start >= 0 and not compares,
          '🚨 在 %s 找到該測試；主體有無集合比較：%s；'
          '⚠️ 找不到或其實有比較的話，本支的指控就不成立'
          % (TEST_FILE.name, compares))
    probe('把 sparql 換成與 core 完全不相交後，該測試的斷言必須失敗'
          '（必觸發之反向・突變）',
          not mutation_still_passes(),
          '🚨 突變後斷言仍通過＝%s；'
          '⚠️ 仍通過就證明那條測試**偵測不到縮編**'
          % mutation_still_passes())
    # 🚨 這一道是答案。
    probe('兩個 profile 的守備類別一致',
          not core_only and not sparql_only,
          '🚨 core 有而 sparql 沒有：%s；sparql 有而 core 沒有：%s；'
          '⚠️ 而前者裡的 `QuantitativeStudyResult` 正是'
          '「必須有點估計／不確定性區間」那條規則的所在'
          % ([short(c) for c in core_only], [short(c) for c in sparql_only]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'shape-profile-coverage-gap',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'followsFrom': 'n678（只驗一份形狀會放東西過去）',
        'coreTargets': sorted(short(c) for c in core),
        'sparqlTargets': sorted(short(c) for c in sparql),
        'coreOnly': [short(c) for c in core_only],
        'sparqlOnly': [short(c) for c in sparql_only],
        'rulesLivingOnlyInCore': orphan_rules,
        'theTest': {'file': str(TEST_FILE.relative_to(REPO)),
                    'name': TEST_NAME,
                    'bodyComparesTheTwoSets': compares},
        'twoReadings': (
            '✅ 兩種讀法都成立：'
            '**（一）測試名不副實**——名字與註解說「守備範圍必須一致」，'
            '主體卻只斷言非空；'
            '**（二）註解寫錯了**——也許 Core 管結構、SPARQL 管跨實體稽核，'
            '本來就不該一致。'
            '🚨 但兩者都會讓讀者相信一件沒發生的事。**📮 哪一邊該改是裁定。**'),
        'consequenceForD25': (
            '🚨 「量化 StudyResult 必須有點估計／不確定性區間」'
            '**只掛在 core 守備的 `QuantitativeStudyResult` 上**。'
            '⚠️ 若驗收只跑 SPARQL（稽核）profile，'
            '**一個沒有信賴區間的量化結果會通過**——'
            '✅ 這正是第 678 輪那個示範的具名版本。'),
        'methodLimit': (
            '⚠️ 本支只比**類別層級**的守備，'
            '🚫 沒有比「同一個類別上，兩邊的規則是否等價」——'
            '🚨 故 `sparqlOnly` 與 `coreOnly` 為空也不代表兩邊一樣嚴。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n679 兩個 profile 的守備落差 ===')
    print('   core   守備 %d 類：%s' % (len(core), doc['coreTargets']))
    print('   sparql 守備 %d 類：%s' % (len(sparql), doc['sparqlTargets']))
    print('   🚨 只有 core 守備：%s' % doc['coreOnly'])
    print('      sparql 獨有：%s' % doc['sparqlOnly'])
    print('   那些類別上只存在於 core 的具名規則 %d 條：' % len(orphan_rules))
    for rule in orphan_rules:
        print('      [%s] %s' % (rule['class'], rule['message'][:58]))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
