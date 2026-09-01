# -*- coding: utf-8 -*-
"""**規格補完：v2.1 形狀，以及「只驗一份形狀會放東西過去」。**（第 678 輪）

## ✅ 這一條是本室上一輪自己寫下的限制

n677 的 `methodLimit`：「🚫 只讀 `shapes/core`，沒讀 `shapes/sparql` 的 v2.1 形狀」。

## 🚨 而 v2.1 對 D25 的影響落在 **CitationAnchor** 上

n677 已證：**每個 StudyResult 至少需一個 `CitationAnchor`**。
⚠️ 而 v2.1 對 anchor 又下了四條——**🚨 於是那四條直接變成 D25 的成本**：

- 🚨 多重命中**不得**建立正式 anchor（不得取第一筆）
- ⚠️ fuzzy anchor 未經人工確認**不得**支撐 Approved Claim
- ⚠️ 來源 manifestation hash 變了就得標 `requiresReanchoring`
- 🚨 anchor **不得**引用 NotebookLM 執行期座標

## 🚨 而本輪查到一件更該講的事

**`studyresult-missing-scope-contract`（負向對照）拿去對 v2.1 驗，是 `conforms=True`。**

> **⚠️ 那不是 v2.1 壞掉——那條約束住在 core。**
> **🚨 但它代表：只驗一份形狀，會把該擋的放過去。**

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
OUT = HERE / 'n678_shacl_v21_anchor_spec.json'
AHIG = REPO / 'ahig'
CORE = AHIG / 'shapes' / 'core' / 'ahig-core.shacl.ttl'
V21 = AHIG / 'shapes' / 'sparql' / 'ahig-v2.1.shacl.ttl'
CANARIES = AHIG / 'shapes' / 'canaries'

SH = rdflib.Namespace('http://www.w3.org/ns/shacl#')
AH = rdflib.Namespace('https://ahig.local/ns/')
OF_INTEREST = {AH.StudyResult, AH.CitationAnchor}


def local(term):
    text = str(term)
    for sep in ('#', '/'):
        if sep in text:
            text = text.rsplit(sep, 1)[-1]
    return text


def messages_for(graph):
    """v2.1 對這兩個類別下了哪些具名約束。"""
    out = []
    for shape, _, cls in graph.triples((None, SH.targetClass, None)):
        if cls not in OF_INTEREST:
            continue
        for _, _, node in graph.triples((shape, SH.sparql, None)):
            msg = graph.value(node, SH.message)
            if msg:
                out.append({'targetClass': local(cls),
                            'shape': local(shape), 'message': str(msg)})
        for _, _, node in graph.triples((shape, SH.property, None)):
            msg = graph.value(node, SH.message)
            if msg:
                out.append({'targetClass': local(cls),
                            'shape': local(shape), 'message': str(msg)})
    return sorted(out, key=lambda r: (r['targetClass'], r['message']))


def validate(data_path, shape_path):
    data = rdflib.Graph().parse(str(data_path), format='turtle')
    shapes = rdflib.Graph().parse(str(shape_path), format='turtle')
    conforms, _, text = pyshacl.validate(
        data_graph=data, shacl_graph=shapes, advanced=True, inference='none')
    msgs = [line.strip()[len('Message:'):].strip()
            for line in text.splitlines()
            if line.strip().startswith('Message:')]
    return conforms, msgs


def main():
    v21 = rdflib.Graph().parse(str(V21), format='turtle')
    constraints = messages_for(v21)

    positive = CANARIES / 'positive' / 'studyresult-complete.ttl'
    anchors = sorted((CANARIES / 'negative').glob('citation-anchor-*.ttl'))
    missing_scope = (CANARIES / 'negative'
                     / 'studyresult-missing-scope-contract.ttl')

    results = []
    pos_core, _ = validate(positive, CORE)
    pos_v21, _ = validate(positive, V21)
    results.append({'canary': positive.name, 'kind': '正向',
                    'coreConforms': pos_core, 'v21Conforms': pos_v21})

    anchor_rows = []
    for path in anchors:
        conforms, msgs = validate(path, V21)
        anchor_rows.append({'canary': path.name, 'v21Conforms': conforms,
                            'firstMessage': msgs[0] if msgs else None})

    ms_core, ms_core_msgs = validate(missing_scope, CORE)
    ms_v21, _ = validate(missing_scope, V21)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('v2.1 裡真的抽得到這兩個類別的約束（必觸發之正對照）',
          len(constraints) >= 4,
          '🚨 抽到 %d 條具名約束：%s；⚠️ 太少代表本支讀錯了圖'
          % (len(constraints),
             sorted({c['targetClass'] for c in constraints})))
    probe('正向對照對**兩份**形狀都必須通過（必觸發之正對照）',
          pos_core and pos_v21,
          '🚨 %s：core=%s／v2.1=%s；⚠️ 任一不過，本支讀的形狀就不是有在執行的'
          % (positive.name, pos_core, pos_v21))
    bad_anchor = [r['canary'] for r in anchor_rows if r['v21Conforms']]
    probe('三個 anchor 負向對照對 v2.1 都必須驗不過（必觸發之反向）',
          anchor_rows and not bad_anchor,
          '🚨 %d 個負向對照，通過的（＝沒被擋住）：%s；'
          '⚠️ 若有通過的，代表那條約束沒有在擋任何東西'
          % (len(anchor_rows), bad_anchor or '無'))
    # 🚨 這一道是答案。
    probe('只驗一份形狀就夠了',
          ms_v21 is False,
          '🚨 `%s` 對 core 驗不過（訊息 %d 條）、**對 v2.1 卻是 conforms=%s**；'
          '⚠️ 那不是 v2.1 壞掉——那條約束住在 core；'
          '**🚨 但它代表只驗一份形狀會把該擋的放過去。**'
          % (missing_scope.name, len(ms_core_msgs), ms_v21))

    doc = {
        'schemaVersion': 1,
        'documentType': 'shacl-v21-anchor-spec',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'closesLimitDeclaredBy': 'n677 → methodLimit（未讀 v2.1 形狀）',
        'v21ConstraintsOnStudyResultAndAnchor': constraints,
        'positiveCanary': {'file': positive.name,
                           'core': pos_core, 'v21': pos_v21},
        'anchorNegativeCanaries': anchor_rows,
        'crossGraphDemo': {
            'canary': missing_scope.name,
            'coreConforms': ms_core,
            'coreMessages': ms_core_msgs[:4],
            'v21Conforms': ms_v21,
            'reading': ('⚠️ 同一份資料在 core 驗不過、在 v2.1 卻通過——'
                        '🚨 **兩份形狀檢查的不是同一組東西，'
                        '驗收時必須兩份都跑。**'),
        },
        'whatThisMeansForD25': (
            '🚨 n677 已證每個 StudyResult 必須帶 `CitationAnchor`；'
            '⚠️ 而 v2.1 又規定 anchor **不得多重命中取第一筆**、'
            '**fuzzy 未經人工確認不得支撐已核可主張**、'
            '**來源 hash 變了要標重新錨定**、**不得引用 NotebookLM 座標**。'
            '✅ 換句話說：D25 那一輪抽的每一個數字，'
            '**都要配一段在原文中唯一命中的逐字引文**——'
            '🚨 命中不唯一就得走人工確認，🚫 不能自己挑一個。'),
        'methodLimit': (
            '⚠️ 本支只驗了 5 個對照檔，🚫 不是全部的 canary；'
            '🚨 且「通過」只代表**這些**約束沒被違反，'
            '**🚫 不代表資料是對的**——形狀管的是結構，不是內容真偽。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n678 v2.1 形狀與跨圖驗證 ===')
    print('   v2.1 對 StudyResult／CitationAnchor 的具名約束 %d 條：'
          % len(constraints))
    for row in constraints:
        print('      [%s] %s' % (row['targetClass'], row['message'][:62]))
    print('   正向對照：core=%s／v2.1=%s' % (pos_core, pos_v21))
    print('   anchor 負向對照（對 v2.1）：')
    for row in anchor_rows:
        print('      %-46s conforms=%-6s %s'
              % (row['canary'], row['v21Conforms'],
                 (row['firstMessage'] or '')[:40]))
    print('   🚨 跨圖示範：%s → core=%s／v2.1=%s'
          % (missing_scope.name, ms_core, ms_v21))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
