# -*- coding: utf-8 -*-
"""**SHACL 那一層對本鏈的產物到底說了什麼——在跑不動 SHACL 的機器上。**（第 544 輪）

## 🚨 本室環境跑不動 SHACL

`rdflib` 與 `pyshacl` **兩個都不在**。⚠️ 故本機不只是「26 條測試沒被收集」，
**🚨 是 `gates/shacl.py` 與 `verify.py` 整層都跑不起來。**
（本室閘門原本只寫「缺 pyshacl」——⚠️ 那句話操作上沒錯（pyshacl 會帶 rdflib），
🚨 但它讓人以為只差一個套件，而實情是整個 RDF 堆疊都不在。）

## ✅ 於是先量盲區有多大，🚫 而不是先去裝東西

TTL 是文字，**⚠️ 數 `sh:targetClass` 不需要 rdflib。** 實測：

- **core 層有 8 個 targetClass，其中以 `ahig:OutcomeInventory` 為目標的只有 1 條。**
- **sparql 層 7 個 targetClass，🚨 一條都不以 OutcomeInventory 為目標。**

而那唯一一條的內容是兩項：`reportedOutcome` 至少一項、
`registryComparisonStatus` 必為五個列舉值之一。

## 🚨 這一支證什麼、不證什麼

- ✅ 證得了：**那兩項約束，本鏈的產物在 41 篇上都滿足**，且兩項各自在鏈上還有別的地方在擋。
- ✅ 證得了：SHACL 的列舉與 JSON Schema 的列舉**逐字相同**——
  🚨 兩層若不同，就會有文件過得了一層過不了另一層。
- 🚨 **證不了「SHACL 會放行」**——⚠️ 本支是**逐條照文字核對**，🚫 不是跑了 SHACL。
  兩者差在：**🚨 我只核對了以 OutcomeInventory 為目標的那一條**，
  而真的跑 SHACL 會連圖結構、資料型別、其他 shape 的間接影響一起看。
- 🚨 證不了 `StudyResult` 那一側——⚠️ 那是清冊的**下游**（`derivedFromOutcomeInventory`），
  **🚫 而本階段不產出 StudyResult。**

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import importlib
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.extraction import inventory_draft as bridge  # noqa: E402
from ahig.extraction.corpus import iter_acquired, reading_request_for  # noqa: E402

from n537_chain_rehearsal import stub_reader  # noqa: E402

CORE = REPO / 'ahig' / 'shapes' / 'core' / 'ahig-core.shacl.ttl'
SPARQL = REPO / 'ahig' / 'shapes' / 'sparql' / 'ahig-v2.1.shacl.ttl'
SCHEMA_PATH = REPO / 'ahig' / 'schema' / 'outcome-inventory.schema.json'
CONTRACT_PATH = REPO / 'ahig' / 'calibration' / 'b11-carbohydrate' / 'scope-contract.json'
OUT = Path(__file__).resolve().parent / 'n544_shacl_coverage.json'


def targets(path):
    text = path.read_text(encoding='utf-8')
    found = {}
    for name in re.findall(r'sh:targetClass\s+(ahig:[A-Za-z]+)', text):
        found[name] = found.get(name, 0) + 1
    return found


def main():
    stack = {}
    for name in ('rdflib', 'pyshacl'):
        try:
            importlib.import_module(name)
            stack[name] = 'present'
        except ImportError:
            stack[name] = 'absent'

    core_targets, sparql_targets = targets(CORE), targets(SPARQL)
    core_text = CORE.read_text(encoding='utf-8')
    shacl_enum = re.findall(
        r'"([^"]+)"',
        re.search(r'PS-registryComparisonStatus.*?sh:in \((.*?)\)',
                  core_text, re.S).group(1))

    schema = json.loads(SCHEMA_PATH.read_text(encoding='utf-8'))
    schema_enum = (schema['$defs']['registryComparison']['properties']['status']
                   .get('enum') or [])

    contract = json.loads(CONTRACT_PATH.read_text(encoding='utf-8'))

    empty_outcomes, bad_status, checked = [], [], 0
    for name, document, _error in iter_acquired():
        if document is None:
            continue
        request = reading_request_for(document.candidate_id, contract)
        scoped = bridge.draft_to_scoped(
            bridge.validate_draft(stub_reader(request), request), contract,
            now='2026-08-31T00:00:00Z')
        checked += 1
        if not (scoped.get('reportedOutcomes') or []):
            empty_outcomes.append(name[-16:])
        status = (scoped.get('registryComparison') or {}).get('status')
        if status not in shacl_enum:
            bad_status.append((name[-16:], status))

    # 必觸發：這兩項在鏈上還有別的地方在擋嗎——真的送一份壞的進去看。
    a_request = None
    for _n, document, _e in iter_acquired():
        if document is not None:
            a_request = reading_request_for(document.candidate_id, contract)
            break
    empty_rejected = False
    try:
        bad = stub_reader(a_request)
        bad['reportedOutcomes'] = []
        bridge.validate_draft(bad, a_request)
    except bridge.DraftRejected:
        empty_rejected = True

    probes = []

    def probe(pname, ok, detail):
        probes.append({'probe': pname, 'passed': bool(ok), 'detail': detail})

    probe('以 OutcomeInventory 為目標的 shape 只有一條',
          core_targets.get('ahig:OutcomeInventory') == 1
          and 'ahig:OutcomeInventory' not in sparql_targets,
          'core %s 條｜sparql %s 條'
          % (core_targets.get('ahig:OutcomeInventory'),
             sparql_targets.get('ahig:OutcomeInventory', 0)))
    probe('SHACL 與 JSON Schema 的列舉逐字相同',
          shacl_enum == schema_enum,
          '🚨 兩層不同就會有文件過得了一層過不了另一層；'
          '只在 schema %s｜只在 shacl %s'
          % (sorted(set(schema_enum) - set(shacl_enum)),
             sorted(set(shacl_enum) - set(schema_enum))))
    probe('41 篇的產物都有至少一項 reportedOutcome',
          not empty_outcomes, '空者 %d 篇' % len(empty_outcomes))
    probe('41 篇的 registryComparisonStatus 都在列舉內',
          not bad_status, '不在列舉者：%s' % (bad_status or '無'))
    probe('空清冊在鏈上真的會被擋（必觸發）', empty_rejected,
          '🚨 若擋不下來，代表「41 篇都非空」只是替身剛好沒送空的')

    doc = {
        'schemaVersion': 1,
        'documentType': 'shacl-coverage-of-inventory',
        'ruling': 'n+183「scoped → family/gates（既有）」之另一半：SHACL 那一層',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'rdfStack': stack,
        'environmentNote': (
            '🚨 rdflib 與 pyshacl 兩個都不在，故本機不只是「26 條測試沒被收集」，'
            '⚠️ 是 gates/shacl.py 與 verify.py 整層都跑不起來。'
            '🚫 本支未安裝任何東西——先量盲區，不先動環境。'),
        'targetClasses': {'core': core_targets, 'sparql': sparql_targets},
        'inventoryConstraints': [
            'PS-reportedOutcome：sh:minCount 1',
            'PS-registryComparisonStatus：minCount 1／maxCount 1／sh:in（五值）',
        ],
        'enums': {'shacl': shacl_enum, 'jsonSchema': schema_enum,
                  'identical': shacl_enum == schema_enum},
        'checkedRecords': checked,
        'violations': {'emptyReportedOutcomes': empty_outcomes,
                       'statusOutsideEnum': bad_status},
        'whatThisIsNot': (
            '🚨 這是**逐條照文字核對**，🚫 不是跑了 SHACL。'
            '⚠️ 差別在於：本支只核對了以 OutcomeInventory 為目標的那一條，'
            '而真的跑 SHACL 會連圖結構、資料型別、其他 shape 的間接影響一起看。'),
        'notInScopeHere': (
            '⚠️ SHACL 對 StudyResult 說的話多得多（scopeContractHash、scopeRuleId、'
            'derivedFromOutcomeInventory…），🚫 但 StudyResult 是清冊的下游，'
            '🚨 而本階段不產出 StudyResult。'),
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n544 SHACL 對本鏈產物之覆蓋 ===')
    print('   RDF 堆疊：%s' % stack)
    print('   targetClass：core %d 類｜sparql %d 類；'
          '以 OutcomeInventory 為目標者 core %s／sparql %s'
          % (len(core_targets), len(sparql_targets),
             core_targets.get('ahig:OutcomeInventory'),
             sparql_targets.get('ahig:OutcomeInventory', 0)))
    print('   該條之約束：reportedOutcome ≥1｜registryComparisonStatus ∈ 五值')
    print('   列舉與 JSON Schema：%s' % ('逐字相同' if shacl_enum == schema_enum
                                          else '🚨 不同'))
    print('   41 篇核對：空清冊 %d｜狀態不在列舉 %d'
          % (len(empty_outcomes), len(bad_status)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
