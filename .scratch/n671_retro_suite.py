# -*- coding: utf-8 -*-
"""**驗證上一輪自己講的那句限制——結果它講得太滿。**（第 671 輪）

## 🚨 第 670 輪本室寫進憑證與看板的一句話

> 「它只索引識別字……**故這支救得了 D4 那次，🚫 救不了 D6 那次。**」

**⚠️ 那句話本室沒有驗過就寫上去了。本輪驗它。**

## ✅ 驗出來的結果：**一半對，一半錯**

| 查法 | D4 那次 | D6 那次 |
|---|---|---|
| 只用**實體**識別字（報告代號、契約結局） | ⬇️ 見結果 | **🚨 查不到（n588 得 0 分）** |
| 加上**爭點**識別字（儀器名稱／理由碼） | ⬇️ 見結果 | **✅ 查得到，且連得到 D5／D6** |

> **🚨 故限制不在「識別字 vs 散文」，而在「查詢帶不帶爭點的識別字」。**
> **✅ 這是可以照著做的規矩，🚫 而上一輪那句話會讓人乾脆不查。**

## ✅ 兩種查法的差別必須自己證明

⚠️ 若兩種查法結果一樣，本支就什麼也沒說。
🚨 故設一道**必觸發之反向**：D6 那次的「只用實體」必須**查不到**。

## 🚫 本支不改任何清冊與契約、不送外部請求
"""
import collections
import json
import math
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

HERE = Path(__file__).resolve().parent
OUT = HERE / 'n671_retro_suite.json'
REGISTER = HERE / 'n669_decision_register_v3.json'

ROUND_RE = re.compile(r'^n(\d+)_')
REPORT_RE = re.compile(r'(?<![0-9a-f])[0-9a-f]{16}(?![0-9a-f])')
REASON_RE = re.compile(r'\b(?:notExtracted|escalated)-[a-z0-9-]+\b')
KEBAB_RE = re.compile(r'\b[a-z][a-z0-9]*(?:-[a-z0-9]+){2,}\b')
TOP_N = 5

CASES = [
    {
        'case': 'D4 那次（切片器械）',
        'cutoff': 663,
        'target': 'n594_a3_first_measurement.json',
        'decision': 'D4',
        # ⚠️ 誰、哪個結局
        'entity': ['7a6ac1559c740fd6', 'muscle-glycogen-post-exercise'],
        # 🚨 這一題真正在吵的東西
        'issue': ['needle-biopsy-vastus-lateralis',
                  'acid-hydrolysis-freeze-dried-biopsy'],
    },
    {
        'case': 'D6 那次（median 與 GI 家族）',
        'cutoff': 664,
        'target': 'n588_reason_code_conflation.json',
        'decision': 'D6',
        'entity': ['gi-symptom-severity', 'gi-symptom-incidence'],
        'issue': ['notExtracted-effect-measure-not-in-scope',
                  'notExtracted-dose-outside-bands'],
    },
]


def artefacts():
    for path in sorted(HERE.glob('n*.json')):
        m = ROUND_RE.match(path.name)
        if m:
            yield int(m.group(1)), path


def identifiers(text):
    return (set(REPORT_RE.findall(text)) | set(REASON_RE.findall(text))
            | set(KEBAB_RE.findall(text)))


def build(cutoff):
    index = collections.defaultdict(set)
    per_file = {}
    for round_no, path in artefacts():
        if round_no >= cutoff:
            continue
        try:
            found = identifiers(path.read_text(encoding='utf-8'))
        except OSError:
            continue
        per_file[path.name] = found
        for ident in found:
            index[ident].add(path.name)
    return index, per_file


def decisions_by_file():
    register = json.loads(REGISTER.read_text(encoding='utf-8'))
    mapping = collections.defaultdict(set)
    for item in register['items']:
        for part in str(item['evidence']).replace('；', ';').split(';'):
            name = part.split('→')[0].strip()
            if name:
                mapping[name].add(item['id'])
    return mapping


def run(query, index, per_file, to_decision, target):
    corpus = len(per_file) or 1
    weight = {i: math.log(corpus / len(f))
              for i, f in index.items() if f}
    scores = collections.Counter()
    for ident in query:
        for name in index.get(ident, ()):
            scores[name] += weight.get(ident, 0.0)
    ranked = scores.most_common()
    rank = next((i + 1 for i, (name, _) in enumerate(ranked)
                 if name == target), None)
    top = ranked[:TOP_N]
    reached = sorted({d for name, _ in top
                      for d in to_decision.get(name, set())})
    return {
        'query': list(query),
        'queryWeights': {i: round(weight.get(i, 0.0), 2) for i in query},
        'candidates': len(ranked),
        'top': [{'artefact': n, 'score': round(s, 2)} for n, s in top],
        'rankOfTarget': rank,
        'targetScore': round(scores.get(target, 0.0), 2),
        'decisionsReached': reached,
    }


def main():
    to_decision = decisions_by_file()
    results = []
    for case in CASES:
        index, per_file = build(case['cutoff'])
        entity = run(case['entity'], index, per_file, to_decision,
                     case['target'])
        both = run(case['entity'] + case['issue'], index, per_file,
                   to_decision, case['target'])
        results.append({
            'case': case['case'], 'cutoffRound': case['cutoff'],
            'target': case['target'], 'decision': case['decision'],
            'corpusSize': len(per_file),
            'targetIndexed': case['target'] in per_file,
            'entityOnly': entity,
            'entityPlusIssue': both,
        })

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('兩個目標憑證都在各自的截止語料裡（必觸發之正對照）',
          all(r['targetIndexed'] for r in results),
          '🚨 %s；⚠️ 不在的話「查不到」只是因為它還沒存在，🚫 不是查法的問題'
          % {r['case']: r['targetIndexed'] for r in results})

    # 🚨 必觸發之反向：兩種查法必須**真的不一樣**。
    d6 = next(r for r in results if r['decision'] == 'D6')
    probe('D6 那次「只用實體識別字」必須查不到（必觸發之反向）',
          d6['entityOnly']['targetScore'] == 0
          and 'D6' not in d6['entityOnly']['decisionsReached'],
          '🚨 只用實體：n588 得分 %.2f、名次 %s、連到 %s；'
          '⚠️ 若這樣就查得到，兩種查法沒有差別，本支等於沒說話'
          % (d6['entityOnly']['targetScore'],
             d6['entityOnly']['rankOfTarget'] or '未進榜',
             d6['entityOnly']['decisionsReached'] or '無'))

    probe('加上爭點識別字之後，兩次都連得到對應決策（必觸發之正對照）',
          all(r['decision'] in r['entityPlusIssue']['decisionsReached']
              for r in results),
          '🚨 %s；⚠️ 連不到就代表這個查法也救不了'
          % {r['case']: r['entityPlusIssue']['decisionsReached']
             for r in results})

    # 🚨 這一道是答案。
    entity_enough = all(r['decision'] in r['entityOnly']['decisionsReached']
                        for r in results)
    probe('只用實體識別字就查得到——🚫 不必特別帶爭點',
          entity_enough,
          '🚨 只用實體時連到的決策：%s；'
          '⚠️ 有一次連不到，就代表「查詢必須帶爭點的識別字」是硬規矩'
          % {r['case']: r['entityOnly']['decisionsReached'] or '無'
             for r in results})

    doc = {
        'schemaVersion': 1,
        'documentType': 'retro-lookup-suite',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'corrects': (
            '🚨 第 670 輪本室寫「這支救得了 D4 那次，救不了 D6 那次」——'
            '**⚠️ 那句話沒驗過，而且太滿**。'
            '✅ 實測：D6 那次只用實體識別字確實查不到（n588 得 0 分），'
            '🚨 但**加上理由碼就查得到，且連得到 D5／D6**。'),
        'refinedLimit': (
            '✅ 真正的限制不是「識別字 vs 散文」，'
            '**🚨 是「查詢帶不帶爭點的識別字」**——'
            '⚠️ 實體識別字（誰、哪個結局）不夠，'
            '**必須帶上這一題真正在吵的那個記號**（儀器名稱、理由碼）。'),
        'cases': results,
        'howToUse': (
            '✅ 開一輪之前，把手上的識別字丟進 n670 的索引查，'
            '**🚨 而查詢一定要包含爭點的識別字（理由碼、儀器名稱），'
            '🚫 不要只丟報告代號與結局代號。**'),
        'methodLimit': (
            '⚠️ 本支只有 **2** 個回溯案例，🚫 不足以說「這個規矩永遠成立」；'
            '✅ 但它足以說「上一輪那句話講得太滿」——'
            '🚨 因為只要一個反例就夠了，而 D6 那次正是反例。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n671 回溯測試組（驗上一輪自己講的限制）===')
    for r in results:
        print('   %s｜截止第 %d 輪｜語料 %d 支｜目標 %s'
              % (r['case'], r['cutoffRound'], r['corpusSize'], r['target']))
        for mode, label in (('entityOnly', '只用實體  '),
                            ('entityPlusIssue', '實體＋爭點')):
            m = r[mode]
            print('      %s：候選 %d｜目標名次 %s｜得分 %.2f｜連到 %s'
                  % (label, m['candidates'], m['rankOfTarget'] or '未進榜',
                     m['targetScore'], m['decisionsReached'] or '無'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
