# -*- coding: utf-8 -*-
"""**把 D25 命脈的那幾條規則，從「沒人看過它亮」變成「看過它亮」。**（第 683 輪）

## 🚨 第 682 輪查出

從未被任何對照組點亮的具名規則有 53 條，
**⚠️ 其中 21 條掛在 `StudyResult`／`QuantitativeStudyResult`／`CitationAnchor` 上**——
🚨 也就是 D25 一旦產出東西，會第一次踩到的那些。

> **⚠️ 而第 677／678 輪講的硬規定（必須有點估計、必須有不確定性區間、
> 必須有唯一命中的逐字引文），🚫 目前沒有任何對照組證明它們會亮。**

## ✅ 本支的做法：從**已知合法**的那份改一個地方

拿正向對照 `studyresult-complete.ttl`（實測 conforms），
**一次只拿掉一個屬性**，再驗一次：

- 🚨 必須變成 **不 conforms**
- 🚨 而且亮的必須是**預期的那一條規則**，🚫 不是被別的必填欄位順手擋掉

⚠️ 這與第 640 輪對產品判定器做的突變是同一套。

## ⚠️ 一件要先講的事

`QuantitativeStudyResult` 的兩條規則，在原本的對照上**不會觸發**——
🚨 因為那個節點只宣告成 `StudyResult`。
✅ 故本支對那兩條**先補上型別宣告**（最小構造），⚠️ 並如實記下這一步。

## 🚫 本支不改產品程式、形狀與測試；資料全是本支現造的，🚫 不含任何文獻內容
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

from rdflib import RDF, Graph, URIRef  # noqa: E402

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.gates import shacl as G  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n683_prove_d25_rules_fire.json'
AH = URIRef('https://ahig.local/ns/')
POSITIVE = (AHIG / 'shapes' / 'canaries' / 'positive'
            / 'studyresult-complete.ttl')

# 🚨 D25 命脈的那幾條——第 677／678 輪點名的硬規定
UNDER_TEST = ['PS-pointEstimate', 'PS-uncertaintyInterval',
              'PS-exactQuote', 'PS-uniqueMatch', 'PS-citationAnchor',
              'PS-deterministicCheckReport', 'PS-sourceManifestation']


def short(term):
    return str(term).rsplit('/', 1)[-1]


def rule_index(core):
    """規則名 → （sh:path、擁有它的 node shape 的 targetClass）。"""
    out = {}
    for shape, _, cls in core.triples((None, G.SH.targetClass, None)):
        for _, _, prop in core.triples((shape, G.SH.property, None)):
            if not isinstance(prop, URIRef):
                continue
            path = core.value(prop, G.SH.path)
            if path is not None:
                out[short(prop)] = {'path': path, 'targetClass': cls,
                                    'iri': prop}
    return out


def main():
    core = G.load_shapes(G.CORE_PROFILE)
    index = rule_index(core)
    base = Graph().parse(str(POSITIVE), format='turtle')

    baseline = G.validate_graph(base, core)
    rows = []
    for name in UNDER_TEST:
        info = index.get(name)
        if info is None:
            rows.append({'rule': name, 'status': '🚨 形狀裡找不到這條規則'})
            continue
        mutated = Graph()
        for triple in base:
            mutated.add(triple)

        # ⚠️ 目標類別若不在資料裡，先補上型別宣告（最小構造）。
        typed_added = False
        subjects = list(mutated.subjects(RDF.type, info['targetClass']))
        if not subjects:
            anchor = list(mutated.subjects(
                RDF.type, URIRef(str(AH) + 'StudyResult')))
            if anchor:
                mutated.add((anchor[0], RDF.type, info['targetClass']))
                subjects = [anchor[0]]
                typed_added = True

        removed = 0
        for subject in subjects:
            for obj in list(mutated.objects(subject, info['path'])):
                mutated.remove((subject, info['path'], obj))
                removed += 1

        outcome = G.validate_graph(mutated, core)
        fired = sorted(short(s) for s in outcome.source_shapes
                       if isinstance(s, URIRef))
        rows.append({
            'rule': name,
            'path': short(info['path']),
            'targetClass': short(info['targetClass']),
            'addedTypeDeclaration': typed_added,
            'mutationKind': ('拿掉屬性' if removed
                             else ('補上型別宣告' if typed_added else '🚨 什麼都沒動')),
            'triplesRemoved': removed,
            'conformsAfterMutation': outcome.conforms,
            'firedShapes': fired,
            'expectedFired': name in fired,
        })

    proven = [r for r in rows if r.get('expectedFired')]
    not_proven = [r for r in rows if not r.get('expectedFired')]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('未改動的正向對照必須通過（必觸發之正對照）',
          baseline.conforms,
          '🚨 未改動時 conforms=%s；⚠️ 若它自己就過不了，'
          '底下每一條突變都測不到自己想測的東西' % baseline.conforms)
    # 🚨 本室第一版寫「一次只拿掉一個屬性」，⚠️ 但那兩條量化規則實際上
    # 移除了 **0** 個三元組——它們是靠**補上型別宣告**才亮的。
    # ✅ 這道探針亮紅之後才被抓到，故條件改成「有動到（刪或加型別）」，
    # 🚫 並把兩種突變分開記，不混成一種。
    probe('每一次突變都真的動到了資料（必觸發之正對照）',
          all(r.get('triplesRemoved', 0) > 0 or r.get('addedTypeDeclaration')
              for r in rows if 'triplesRemoved' in r),
          '🚨 突變方式：%s；⚠️ 什麼都沒動的話，那次突變等於沒做'
          % {r['rule']: '%s（刪 %d）' % (r.get('mutationKind'),
                                        r.get('triplesRemoved', 0))
             for r in rows})
    probe('突變之後必須不再 conforms（必觸發之反向）',
          all(not r.get('conformsAfterMutation', True) for r in rows
              if 'conformsAfterMutation' in r),
          '🚨 突變後仍 conforms 的：%s；⚠️ 仍通過就代表那條規則沒在擋'
          % ([r['rule'] for r in rows
              if r.get('conformsAfterMutation')] or '無'))
    # 🚨 這一道是答案。
    probe('每一條受測規則都被證明會亮，且亮的是它自己',
          not not_proven,
          '🚨 證明會亮 %d 條；未證明的 %d 條：%s；'
          '⚠️ 只是「不 conforms」不夠——**必須是預期的那一條擋下來的**，'
          '🚫 否則規則改壞了也測不出來'
          % (len(proven), len(not_proven),
             [(r['rule'], r.get('firedShapes')) for r in not_proven] or '無'))

    # 🚨 而上面那件事指向一個更該講的：對照組裡有沒有量化結果的實例。
    quant = URIRef(str(AH) + 'QuantitativeStudyResult')
    plain = URIRef(str(AH) + 'StudyResult')
    counts = {'QuantitativeStudyResult': 0, 'StudyResult': 0}
    for polarity in ('positive', 'negative'):
        for canary in G.iter_canaries(polarity):
            counts['QuantitativeStudyResult'] += len(
                list(canary.data.subjects(RDF.type, quant)))
            counts['StudyResult'] += len(
                list(canary.data.subjects(RDF.type, plain)))
    probe('對照組裡有量化結果的實例（必觸發之正對照）',
          counts['QuantitativeStudyResult'] > 0,
          '🚨 對照組裡 `StudyResult` 實例 %d 個、'
          '**`QuantitativeStudyResult` 實例 %d 個**；'
          '⚠️ 後者為 0 代表 **D25 要產出的那個類別，正負向對照都沒有**——'
          '✅ 而前者不為 0 證明本支數得到東西，🚫 不是計數壞了'
          % (counts['StudyResult'], counts['QuantitativeStudyResult']))

    doc = {
        'schemaVersion': 1,
        'documentType': 'prove-d25-rules-fire',
        'canaryClassInstances': counts,
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'followsFrom': 'n682（53 條規則從未被點亮，其中 21 條是 D25 要踩的）',
        'baselineConforms': baseline.conforms,
        'rulesUnderTest': UNDER_TEST,
        'rows': rows,
        'provenToFire': [r['rule'] for r in proven],
        'notProven': [r['rule'] for r in not_proven],
        'method': (
            '✅ 從**已知合法**的正向對照出發，**一次只拿掉一個屬性**，'
            '🚨 要求（一）不再 conforms（二）亮的是**預期那一條**。'
            '⚠️ 與第 640 輪對產品判定器做的突變是同一套。'),
        'honestNote': (
            '⚠️ `QuantitativeStudyResult` 的兩條規則在原對照上不會觸發'
            '（那個節點只宣告成 `StudyResult`），'
            '✅ 故本支對它們**先補上型別宣告**——'
            '🚨 這一步已逐條記在 `addedTypeDeclaration` 裡，🚫 不藏。'),
        'whatThisChanges': (
            '✅ 這幾條從「**沒人看過它亮**」變成「**看過它亮**」。'
            '🚫 本支不宣稱其餘 %d 條也沒問題——⚠️ 它們仍未被觀測過。'
            % (21 - len(proven))),
        'contentDiscipline': (
            '✅ 資料全部來自 repo 內的對照檔與本支的刪除操作，'
            '🚫 不含任何文獻內容（n+195 一）。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n683 證明 D25 命脈規則會亮 ===')
    print('   基線（未改動）conforms=%s' % baseline.conforms)
    for row in rows:
        if 'conformsAfterMutation' not in row:
            print('   %-30s %s' % (row['rule'], row.get('status')))
            continue
        print('   %-30s 拿掉 %s×%d｜conforms=%-6s｜亮對=%s%s'
              % (row['rule'], row['path'], row['triplesRemoved'],
                 row['conformsAfterMutation'],
                 '✅' if row['expectedFired'] else '🚨',
                 '｜（補了型別宣告）' if row['addedTypeDeclaration'] else ''))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
