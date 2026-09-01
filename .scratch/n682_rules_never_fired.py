# -*- coding: utf-8 -*-
"""**哪些具名規則從來沒有被任何對照組點亮過。**（第 682 輪）

## ✅ 補上第 681 輪自己寫下的限制

n681：「🚫 量不到『沒有對照組的規則』——🚨 一條沒有 canary 的規則，
兩份 profile 都不會在這裡現形。」

## 🚨 而這正是本室自己那套紀律的產品版

⚠️ 本室的探針掃描器（第 631 輪）有一道：**「所有哨兵探針都已被證明會亮」**。
**🚨 同一條標準套到產品的形狀上，就是本支。**

> **✅ 一條沒有對照組讓它亮過的規則，🚫 沒有人知道它壞了沒有。**

## ✅ 怎麼數

- **Core**：帶 `sh:message` 的**具名節點**（property shape 也算），共數十條
- **SPARQL**：帶 `sh:sparql` 的**具名節點形狀**
- **點亮**：某個負向對照的違規報告裡出現過它

## ⚠️ 兩邊的解析度不一樣，先講清楚

🚨 Core 報得到**規則層**（property shape 各自具名）；
⚠️ SPARQL 只報得到 **shape 層**——**一個 shape 可能裝了好幾條 `sh:sparql`**，
**🚫 shape 亮了不代表它裡面每一條都亮過。**

## 🚫 本支不改產品程式與測試、不送外部請求
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

from rdflib import URIRef  # noqa: E402

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.gates import shacl as G  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n682_rules_never_fired.json'

# ✅ 必觸發之正對照要用的已知配對
KNOWN = ('citation-anchor-fuzzy-unconfirmed',
         'CitationAnchorFuzzyConfirmationShape')


def short(term):
    return str(term).rsplit('/', 1)[-1]


def named_rules(graph, predicate):
    return {s for s, _, _ in graph.triples((None, predicate, None))
            if isinstance(s, URIRef)}


def main():
    core = G.load_shapes(G.CORE_PROFILE)
    sparql = G.load_shapes(G.SPARQL_PROFILE)

    rules = {
        str(G.CORE_PROFILE): named_rules(core, G.SH.message),
        str(G.SPARQL_PROFILE): named_rules(sparql, G.SH.sparql),
    }
    graphs = {str(G.CORE_PROFILE): core, str(G.SPARQL_PROFILE): sparql}

    fired = {k: set() for k in rules}
    by_canary = {}
    for canary in G.iter_canaries('negative'):
        row = {}
        for profile, graph in graphs.items():
            outcome = G.validate_graph(canary.data, graph)
            shapes = {s for s in outcome.source_shapes
                      if isinstance(s, URIRef)}
            fired[profile] |= shapes
            row[profile] = sorted(short(s) for s in shapes)
        by_canary[canary.name] = row

    never = {p: sorted(short(r) for r in rules[p] - fired[p]) for p in rules}
    covered = {p: sorted(short(r) for r in rules[p] & fired[p])
               for p in rules}
    totals = {p: {'named': len(rules[p]),
                  'everFired': len(rules[p] & fired[p]),
                  'neverFired': len(rules[p] - fired[p])} for p in rules}

    # ⚠️ 那些從未點亮的規則，掛在哪個類別上——🚨 D25 的產出會踩到哪些。
    d25_classes = {'StudyResult', 'QuantitativeStudyResult', 'CitationAnchor'}
    owner = {}
    for shape, _, cls in core.triples((None, G.SH.targetClass, None)):
        for _, _, prop in core.triples((shape, G.SH.property, None)):
            if isinstance(prop, URIRef):
                owner[short(prop)] = short(cls)
    d25_untested = sorted(
        name for name in never[str(G.CORE_PROFILE)]
        if owner.get(name) in d25_classes)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩份 profile 都數得到具名規則（必觸發之正對照）',
          all(t['named'] > 0 for t in totals.values()),
          '🚨 %s；⚠️ 任一為 0 就代表本支的列舉方式對那一份無效'
          % {p: t['named'] for p, t in totals.items()})
    probe('已知會亮的那一條真的出現在報告裡（必觸發之正對照）',
          KNOWN[1] in by_canary.get(KNOWN[0], {}).get(
              str(G.CORE_PROFILE), []),
          '🚨 `%s` 在 core 下觸發 %s；⚠️ 對不上代表本支的比對根本沒接上'
          % (KNOWN[0],
             by_canary.get(KNOWN[0], {}).get(str(G.CORE_PROFILE), [])))
    probe('捏造的規則名不在點亮清單裡（必觸發之反向）',
          all('ShapeThatCannotExist682' not in c
              for lst in covered.values() for c in lst),
          '🚨 捏造規則不在清單；⚠️ 若在，代表比對是在亂配')
    # 🚨 這一道是答案。
    total_never = sum(t['neverFired'] for t in totals.values())
    probe('每一條具名規則都有對照組讓它亮過',
          total_never == 0,
          '🚨 從未被點亮的具名規則共 %d 條（%s）；'
          '⚠️ 一條沒被點亮過的規則，🚫 沒有人知道它壞了沒有'
          % (total_never,
             {p: t['neverFired'] for p, t in totals.items()}))

    doc = {
        'schemaVersion': 1,
        'documentType': 'rules-never-fired',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n681 → methodLimit（量不到沒有對照組的規則）',
        'sameDisciplineAs': (
            '✅ 本室探針掃描器（第 631 輪）的「所有哨兵探針都已被證明會亮」——'
            '🚨 同一條標準套到產品的形狀上。'),
        'totals': totals,
        'neverFired': never,
        'neverFiredOnD25Classes': d25_untested,
        'ruleOwnerClass': owner,
        'everFired': covered,
        'perCanary': by_canary,
        'resolutionCaveat': (
            '🚨 Core 報得到**規則層**（property shape 各自具名）；'
            '⚠️ SPARQL 只報得到 **shape 層**——'
            '**一個 shape 可能裝了好幾條 `sh:sparql`，'
            '🚫 shape 亮了不代表它裡面每一條都亮過。**'
            '✅ 故 SPARQL 那一欄的「已點亮」是**上界**。'),
        'whatThisIsNot': (
            '🚫 「沒被點亮」不等於「壞掉」——⚠️ 那些規則可能只是沒有對照組。'
            '**✅ 但那正是問題：沒有對照組，就沒有人證明過它會亮。**'
            '🚨 而第 638／640 輪已示範過：沒走過的分支裡確實藏著東西。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n682 從未被點亮的具名規則 ===')
    for profile, t in totals.items():
        print('   %-8s 具名 %d 條｜曾點亮 %d｜🚨 從未點亮 %d'
              % (profile, t['named'], t['everFired'], t['neverFired']))
    for profile, names in never.items():
        if not names:
            continue
        print('   %s 從未點亮的（前 24 條）：' % profile)
        for name in names[:24]:
            print('      %s' % name)
        if len(names) > 24:
            print('      …… 另有 %d 條' % (len(names) - 24))
    print('   🚨 其中掛在 D25 產出物那三個類別上的 %d 條：' % len(d25_untested))
    for name in d25_untested:
        print('      %-34s [%s]' % (name, owner.get(name)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
