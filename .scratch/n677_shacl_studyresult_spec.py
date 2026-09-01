# -*- coding: utf-8 -*-
"""**D25 的規格還缺一半——SHACL 要的東西 `run_all` 完全沒碰。**（第 677 輪）

## ✅ 這是本室上一輪自己寫下的限制

n676 的 `methodLimit`：「🚫 不保證別的下游（報表、**SHACL 形狀**）沒有別的要求」。
**⚠️ 那一條查得動，本輪查它。**

## 🚨 結果：真的有，而且差很多

`shapes/core/ahig-core.shacl.ttl` 對 `StudyResult` 下了約束，
`shapes/canaries/positive/studyresult-complete.ttl` 是一份**完整合法的範例**。

⚠️ 而 SHACL 要的東西**幾乎都不是數字**：可回溯性、連回清冊、
**逐字引文的 CitationAnchor**、確定性檢查報告、預先指定狀態與裁決者……

> **🚨 其中一條直接約束 D25：
> 「量化 StudyResult 必須有點估計與不確定性區間；
> **原文未提供時只能存為缺失事實，🚫 不得建立量化節點**。」**

## ✅ 而本支不只讀形狀——**實際跑 pyshacl 驗兩個對照**

- 正向對照（完整範例）**必須** conforms
- 負向對照（缺範圍契約 hash）**必須不** conforms

⚠️ 沒有這兩道，「本支讀的形狀是有在執行的」就只是本室的說法。

## 🚫 本支不改任何清冊與契約、不送外部請求、不動產品程式
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

import pyshacl  # noqa: E402
import rdflib  # noqa: E402

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n677_shacl_studyresult_spec.py'.replace('.py', '.json')
AHIG = REPO / 'ahig'
CORE = AHIG / 'shapes' / 'core' / 'ahig-core.shacl.ttl'
POSITIVE = (AHIG / 'shapes' / 'canaries' / 'positive'
            / 'studyresult-complete.ttl')
NEGATIVE = (AHIG / 'shapes' / 'canaries' / 'negative'
            / 'studyresult-missing-scope-contract.ttl')
N676 = HERE / 'n676_numeric_field_requirements.json'

SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')
AH = rdflib.Namespace('https://ahig.local/ns/')
TARGETS = {AH.StudyResult, AH.QuantitativeStudyResult}


def local(term):
    text = str(term)
    for sep in ('#', '/'):
        if sep in text:
            text = text.rsplit(sep, 1)[-1]
    return text


def constrained_paths(graph):
    """SHACL 對 StudyResult 這一族限制了哪些屬性。"""
    out = {}
    for shape, _, cls in graph.triples((None, SH.targetClass, None)):
        if cls not in TARGETS:
            continue
        for _, _, prop in graph.triples((shape, SH.property, None)):
            path = graph.value(prop, SH.path)
            if path is None:
                continue
            out.setdefault(local(path), {
                'onShape': local(shape),
                'targetClass': local(cls),
                'minCount': graph.value(prop, SH.minCount),
                'message': graph.value(prop, SH.message),
            })
    return {k: {kk: (str(vv) if vv is not None else None)
                for kk, vv in v.items()} for k, v in sorted(out.items())}


def canary_predicates(graph):
    """完整範例上，StudyResult 節點實際帶了哪些屬性。"""
    out = set()
    for node in graph.subjects(rdflib.RDF.type, AH.StudyResult):
        for pred in graph.predicates(node, None):
            if pred != rdflib.RDF.type:
                out.add(local(pred))
    return sorted(out)


def validate(data_path):
    data = rdflib.Graph().parse(str(data_path), format='turtle')
    shapes = rdflib.Graph().parse(str(CORE), format='turtle')
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, advanced=True, inference='none')
    messages = [line.strip()[len('Message:'):].strip()
                for line in text.splitlines()
                if line.strip().startswith('Message:')]
    return conforms, messages


# ⚠️ SHACL 屬性 → 清冊裡對應的欄位。🚨 對映是**宣告出來的**，
# 才查得動、也才審得動；🚫 本室不用印象說「這個已經有了」。
INVENTORY_MAP = {
    'analysisSet': 'analysisSet',
    'effectMeasure': 'effectMeasure',
    'statisticalModel': 'statisticalModel',
    'outcome': 'normalisedOutcomeRef',
    'timepoint': 'timepointDays',
}


def on_hand():
    """那些 SHACL 屬性，在**在範圍內**的清冊紀錄裡填得有多滿。"""
    from ahig.scope.matcher import ScopeMatcher
    contract = json.loads(
        (AHIG / 'calibration' / 'b11-carbohydrate'
         / 'scope-contract.json').read_text(encoding='utf-8'))
    matcher = ScopeMatcher(contract)
    filled, total = {k: 0 for k in INVENTORY_MAP}, 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        verdict = matcher.decide_inventory(inventory)
        for reported, decision in zip(inventory['reportedOutcomes'],
                                      verdict['decisions']):
            if not decision['inScope']:
                continue
            total += 1
            for shacl_name, field in INVENTORY_MAP.items():
                if reported.get(field) is not None:
                    filled[shacl_name] += 1
    return filled, total


def main():
    core = rdflib.Graph().parse(str(CORE), format='turtle')
    paths = constrained_paths(core)
    canary = canary_predicates(
        rdflib.Graph().parse(str(POSITIVE), format='turtle'))

    from_code = json.loads(N676.read_text(encoding='utf-8'))
    code_fields = set(from_code['requiredTopLevelFields'])

    shacl_only = sorted(set(paths) | set(canary) - code_fields
                        - {'type'})
    shacl_only = [f for f in shacl_only if f not in code_fields]
    both = sorted(set(canary) & code_fields)

    filled, in_scope_total = on_hand()

    pos_ok, pos_msgs = validate(POSITIVE)
    neg_ok, neg_msgs = validate(NEGATIVE)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('SHACL 裡真的抽得到 StudyResult 的約束（必觸發之正對照）',
          len(paths) >= 5 and len(canary) >= 10,
          '🚨 受約束屬性 %d 個；完整範例帶了 %d 個屬性；'
          '⚠️ 太少代表本支讀錯了圖'
          % (len(paths), len(canary)))
    probe('正向對照必須通過驗證（必觸發之正對照）',
          pos_ok,
          '🚨 %s → conforms=%s；⚠️ 連完整範例都過不了，'
          '本支讀的形狀就不是有在執行的那份'
          % (POSITIVE.name, pos_ok))
    probe('負向對照必須驗不過、且說得出原因（必觸發之反向）',
          (not neg_ok) and len(neg_msgs) >= 1,
          '🚨 %s → conforms=%s，訊息 %d 條：%s；'
          '⚠️ 若它也通過，代表這些約束沒有在擋任何東西'
          % (NEGATIVE.name, neg_ok, len(neg_msgs), neg_msgs[:3]))
    probe('捏造的屬性不在抽出的清單裡（必觸發之反向）',
          'property-that-cannot-exist-677' not in paths
          and 'property-that-cannot-exist-677' not in canary,
          '🚨 捏造屬性不在清單；⚠️ 若在，代表抽的不是真的約束')
    # 🚨 這一道是答案。
    probe('第 676 輪抽出的欄位已涵蓋 SHACL 要求的一切',
          not shacl_only,
          '🚨 SHACL／完整範例要、而 `run_all` 完全沒碰的有 %d 個：%s；'
          '⚠️ 每一個都是 D25 那一輪要一起產出的東西'
          % (len(shacl_only), shacl_only))

    doc = {
        'schemaVersion': 1,
        'documentType': 'shacl-studyresult-spec',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n676 → methodLimit（未看 SHACL 形狀）',
        'constrainedPaths': paths,
        'positiveCanaryPredicates': canary,
        'alsoRequiredByCode': both,
        'shaclOnlyNotSeenByRunAll': shacl_only,
        'inventoryMapDeclared': INVENTORY_MAP,
        'alreadyOnHand': {'filled': filled, 'ofInScopeItems': in_scope_total},
        'stillNeedsSomethingElse': sorted(
            set(paths) - set(INVENTORY_MAP)),
        'validation': {
            'positive': {'file': POSITIVE.name, 'conforms': pos_ok},
            'negative': {'file': NEGATIVE.name, 'conforms': neg_ok,
                         'messages': neg_msgs[:6]},
        },
        'twoHardConstraints': {
            '量化節點': ('🚨 「量化 StudyResult 必須有點估計」與'
                         '「必須有不確定性區間；**原文未提供時只能存為缺失事實，'
                         '🚫 不得建立量化節點**」——'
                         '✅ 故第 676 輪那個最小集不只是方便，**是強制的**。'),
            '逐字引文': ('🚨 「每個 StudyResult 至少需一個穩定 CitationAnchor」，'
                         '而完整範例的 anchor 帶著 `exactQuote`。'
                         '**⚠️ 那是逐字的原文——🚫 依 n+195 一不得進 repo，'
                         '只能留在私有根。**'
                         '✅ 這一條第 676 輪完全沒看到。'),
        },
        'whatThisMeansForD25': (
            '⚠️ 第 676 輪算的是「要抽哪些**數字**」。'
            '🚨 本支補上「一份合法的 StudyResult 還要帶什麼」——'
            '**可回溯性（範圍契約 hash、規則 ID）、連回清冊、'
            '逐字引文的 anchor、確定性檢查報告、預先指定狀態與裁決者**。'
            '✅ 換句話說：D25 那一輪的產出**不是一張數字表**，'
            '🚫 而是一組帶出處、可驗證的節點。'),
        'methodLimit': (
            '🚨 本支只讀 `shapes/core`，🚫 沒讀 `shapes/sparql` 的 v2.1 形狀；'
            '⚠️ 也只驗了兩個對照——**通過不代表所有負向情境都擋得住**。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n677 SHACL 對 StudyResult 的要求 ===')
    print('   受約束屬性 %d 個：' % len(paths))
    for name, info in paths.items():
        print('      %-32s minCount=%-4s %s'
              % (name, info['minCount'], (info['message'] or '')[:40]))
    print('   完整範例帶的屬性 %d 個；其中程式也讀的 %d 個：%s'
          % (len(canary), len(both), both))
    print('   🚨 SHACL 要、而 run_all 完全沒碰的 %d 個：' % len(shacl_only))
    for name in shacl_only:
        print('      %s' % name)
    print('   已在清冊裡（依宣告的對映，%d 項在範圍內）：%s'
          % (in_scope_total, filled))
    print('   驗證：正向 conforms=%s｜負向 conforms=%s（訊息 %d 條）'
          % (pos_ok, neg_ok, len(neg_msgs)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
