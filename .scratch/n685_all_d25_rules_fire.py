# -*- coding: utf-8 -*-
"""**把 D25 那三個類別的 21 條規則全部證明一次。**（第 685 輪）

## ✅ 補上第 683 輪自己寫下的限制

n683：「🚫 本支不宣稱其餘 14 條也沒問題——⚠️ 它們仍未被觀測過。」

## 🚨 而這一輪要先解一個問題：**不是每條規則都靠「拿掉」觸發**

⚠️ n683 對 7 條都用「拿掉屬性」，🚨 但那只對**必填**規則有效。
**⚠️ 禁止型的規則（例如「不得引用 NotebookLM 座標」）要靠「加上去」才會亮。**

> **🚨 用同一招打所有規則，會把「觸發不了」誤讀成「規則壞了」——
> 又是那一族：一種失敗長得像另一種。**

## ✅ 故本支照**形狀自己宣告的約束**決定怎麼突變

| 形狀宣告 | 突變方式 |
|---|---|
| `sh:minCount ≥ 1` | 🚨 **拿掉**該屬性 |
| `sh:maxCount = 0` | 🚨 **加上**一個值 |
| `sh:in` | ⚠️ 換成清單外的值 |
| `sh:pattern` | ⚠️ 換成不符樣式的字串 |
| `sh:datatype` | ⚠️ 換成型別不對的值 |
| 以上皆無 | 🚫 記為「本支無策略」，**不假裝測過** |

## 🚫 本支不改產品程式、形狀與測試；資料全是本支現造，🚫 不含文獻內容
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

from rdflib import RDF, XSD, Graph, Literal, URIRef  # noqa: E402

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.gates import shacl as G  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n685_all_d25_rules_fire.json'
N682 = Path(__file__).resolve().parent / 'n682_rules_never_fired.json'
AH = 'https://ahig.local/ns/'
POSITIVE = (AHIG / 'shapes' / 'canaries' / 'positive'
            / 'studyresult-complete.ttl')


def short(term):
    return str(term).rsplit('/', 1)[-1]


def rule_index(core):
    out = {}
    for shape, _, cls in core.triples((None, G.SH.targetClass, None)):
        for _, _, prop in core.triples((shape, G.SH.property, None)):
            if not isinstance(prop, URIRef):
                continue
            path = core.value(prop, G.SH.path)
            if path is None:
                continue
            out[short(prop)] = {
                'iri': prop, 'path': path, 'targetClass': cls,
                'minCount': core.value(prop, G.SH.minCount),
                'maxCount': core.value(prop, G.SH.maxCount),
                'hasIn': core.value(prop, getattr(G.SH, 'in')) is not None,
                'pattern': core.value(prop, G.SH.pattern),
                'datatype': core.value(prop, G.SH.datatype),
            }
    return out


def mutate(graph, info):
    """依形狀自己宣告的約束決定怎麼動。回傳（做法, 有沒有真的動到）。"""
    cls, path = info['targetClass'], info['path']
    subjects = list(graph.subjects(RDF.type, cls))
    added_type = False
    if not subjects:
        anchors = list(graph.subjects(RDF.type, URIRef(AH + 'StudyResult')))
        if not anchors:
            return '🚫 圖裡沒有這個類別的節點', False, False
        graph.add((anchors[0], RDF.type, cls))
        subjects = [anchors[0]]
        added_type = True

    minc = int(info['minCount']) if info['minCount'] is not None else None
    maxc = int(info['maxCount']) if info['maxCount'] is not None else None

    if maxc == 0:
        for subject in subjects:
            graph.add((subject, path, Literal('ZZ-685-forbidden-ZZ')))
        return '加上被禁止的值', True, added_type

    if minc and minc >= 1:
        removed = 0
        for subject in subjects:
            for obj in list(graph.objects(subject, path)):
                graph.remove((subject, path, obj))
                removed += 1
        return '拿掉必填屬性', bool(removed or added_type), added_type

    if info['hasIn'] or info['pattern'] is not None:
        touched = False
        for subject in subjects:
            for obj in list(graph.objects(subject, path)):
                graph.remove((subject, path, obj))
                touched = True
            graph.add((subject, path, Literal('ZZ-685-not-allowed-ZZ')))
        return '換成不合規的值', touched, added_type

    if info['datatype'] is not None:
        touched = False
        for subject in subjects:
            for obj in list(graph.objects(subject, path)):
                graph.remove((subject, path, obj))
                touched = True
            graph.add((subject, path,
                       Literal('ZZ-685-wrong-type-ZZ', datatype=XSD.string)
                       if info['datatype'] != XSD.string
                       else Literal(685)))
        return '換成型別不對的值', touched, added_type

    return '🚫 本支無策略', False, added_type


def main():
    core = G.load_shapes(G.CORE_PROFILE)
    index = rule_index(core)
    base = Graph().parse(str(POSITIVE), format='turtle')
    baseline = G.validate_graph(base, core)

    targets = json.loads(N682.read_text(encoding='utf-8'))[
        'neverFiredOnD25Classes']

    rows = []
    for name in targets:
        info = index.get(name)
        if info is None:
            rows.append({'rule': name, 'strategy': '🚨 形狀裡找不到這條'})
            continue
        graph = Graph()
        for triple in base:
            graph.add(triple)
        strategy, touched, added_type = mutate(graph, info)
        outcome = G.validate_graph(graph, core)
        fired = sorted(short(s) for s in outcome.source_shapes
                       if isinstance(s, URIRef))
        rows.append({
            'rule': name, 'strategy': strategy,
            'targetClass': short(info['targetClass']),
            'path': short(info['path']),
            'graphChanged': touched, 'addedTypeDeclaration': added_type,
            'conformsAfter': outcome.conforms,
            'expectedFired': name in fired,
            'firedShapes': fired[:6],
        })

    proven = [r for r in rows if r.get('expectedFired')]
    no_strategy = [r for r in rows if '無策略' in str(r.get('strategy'))]
    failed = [r for r in rows
              if not r.get('expectedFired') and r not in no_strategy]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('未改動的正向對照必須通過（必觸發之正對照）',
          baseline.conforms,
          '🚨 未改動時 conforms=%s；⚠️ 它自己過不了的話底下都測不準'
          % baseline.conforms)
    probe('受測的是第 682 輪點名的那 21 條（必觸發之正對照）',
          len(targets) == 21 and len(rows) == 21,
          '🚨 點名 %d 條、實測 %d 條；⚠️ 對不上就與上一輪不一致'
          % (len(targets), len(rows)))
    probe('每一次突變都真的動到了圖（必觸發之正對照）',
          all(r.get('graphChanged') for r in rows
              if 'graphChanged' in r and '無策略' not in str(r['strategy'])),
          '🚨 沒動到的：%s；⚠️ 沒動到就等於沒測'
          % ([r['rule'] for r in rows
              if 'graphChanged' in r and not r['graphChanged']
              and '無策略' not in str(r['strategy'])] or '無'))
    probe('🚫 本支對每一條都有策略，沒有跳過的',
          not no_strategy,
          '🚨 無策略而未測的 %d 條：%s；'
          '⚠️ 本室**不假裝測過**——那些仍是未觀測'
          % (len(no_strategy), [r['rule'] for r in no_strategy] or '無'))
    # 🚨 這一道是答案。
    probe('那 21 條都被證明會亮，且亮的是它自己',
          not failed and not no_strategy,
          '🚨 證明會亮 %d 條；有策略卻沒亮對的 %d 條：%s；'
          '⚠️ 有策略卻不亮的才可能是**規則真的有問題**'
          % (len(proven), len(failed),
             [(r['rule'], r.get('firedShapes')) for r in failed] or '無'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'all-d25-rules-fire',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n683（其餘 14 條仍未被觀測過）',
        'strengthensDecision': (
            '📮 D25。⚠️ 本支**不新增決策**，也**沒有紅燈**——'
            '✅ 它是把 D25 產出物要踩的那 21 條規則，'
            '從「沒人看過它亮」變成「21／21 看過它亮」。'
            '⚠️ 下一版登記簿會把本支掛進 D25 的證據。'),
        'baselineConforms': baseline.conforms,
        'targets': targets,
        'rows': rows,
        'provenToFire': [r['rule'] for r in proven],
        'noStrategy': [r['rule'] for r in no_strategy],
        'hadStrategyButDidNotFire': [r['rule'] for r in failed],
        'whyStrategyMatters': (
            '🚨 n683 對 7 條都用「拿掉屬性」，⚠️ 但那只對**必填**規則有效；'
            '**禁止型的規則要靠「加上去」才會亮**。'
            '⚠️ 用同一招打所有規則，會把「觸發不了」誤讀成「規則壞了」——'
            '✅ 故本支照**形狀自己宣告的約束**決定怎麼突變。'),
        'methodLimit': (
            '⚠️ 「亮對了」只證明那條規則在**這一種**違規下會亮，'
            '🚫 不證明它涵蓋所有違規樣態；'
            '🚨 且本支只在 core profile 上做，🚫 沒有跨 profile。'),
        'contentDiscipline': (
            '✅ 資料來自 repo 內的對照檔與本支現造的佔位值，'
            '🚫 不含任何文獻內容（n+195 一）。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n685 D25 三個類別的 21 條規則 ===')
    print('   基線 conforms=%s｜受測 %d 條' % (baseline.conforms, len(rows)))
    for row in rows:
        if 'conformsAfter' not in row:
            print('   %-32s %s' % (row['rule'], row.get('strategy')))
            continue
        print('   %-32s %-14s conforms=%-6s 亮對=%s%s'
              % (row['rule'], row['strategy'], row['conformsAfter'],
                 '✅' if row['expectedFired'] else '🚨',
                 '｜補型別' if row['addedTypeDeclaration'] else ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
