# -*- coding: utf-8 -*-
"""**守著「配對設計誤用獨立樣本公式」的那道檢查，現在形同不設防。**（第 718 輪）

## 🚨 為什麼要查這一道

⚠️ 這個領域的研究**幾乎都是交叉設計**（同一群人做完 A 再做 B）。
🚨 而交叉設計若誤用獨立樣本公式，**變異數會被高估、信賴區間會被灌大**——
✅ 產品裡本來就有一道檢查在守它：`check_paired_design_formula`。

> **⚠️ 但 `run_all` 是這樣呼叫它的：`sr.get("studyDesign", "")`。
> 🚨 而清冊裡**沒有任何一項**記了 `studyDesign`。**

## ✅ 兩件事本支都實測，🚫 不從程式碼推論

1. **守衛本身有沒有效**（正對照：用對詞，它會不會亮）
2. **現況下它是什麼結果**（反向：欄位空著時）

## 🚨 而它的詞彙是**逐字比對**

`{"RCT-crossover", "repeated-measures", "within-subject", "matched-pairs"}`

⚠️ 連 `crossover` 這種自然拼法都**不算**配對設計——
**🚨 與儀器允許清單（`D2`／`D24`）是同一族的病。**

## 🚫 本支不改產品程式、不改任何清冊、不送外部請求
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.stats import deterministic as det  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n718_paired_design_guard_inert.py'\
    .replace('.py', '.json')

CASES = [
    ('✅ 正對照・用對詞且宣告獨立樣本', ('RCT-crossover', 'independent-groups',
                                        None, 12), 'FAIL'),
    ('✅ 正對照・自由度用成 2n−2', ('RCT-crossover', 'paired t-test', 22, 12),
     'FAIL'),
    ('✅ 正對照・自由度正確（n−1）', ('RCT-crossover', 'paired t-test', 11, 12),
     'PASS'),
    ('✅ 正對照・另一個配對詞', ('repeated-measures', 'unpaired', None, 10),
     'FAIL'),
    ('🚨 自然拼法 `crossover`', ('crossover', 'independent-groups', None, 12),
     'NOT_APPLICABLE'),
    ('🚨 現況：欄位空著', ('', '', None, None), 'NOT_APPLICABLE'),
]


def main():
    # ✅ 詞彙從產品原始碼取，🚫 不手打
    import inspect
    source = inspect.getsource(det.check_paired_design_formula)
    # ⚠️ 原始碼裡那個集合跨行，🚨 故要先把換行與空白清掉再拆。
    raw = source.split('paired_designs = {')[1].split('}')[0]
    vocab = sorted(w for w in
                   (part.strip().strip('"\'').strip()
                    for part in raw.replace('\n', ' ').split(','))
                   if w)

    results = []
    for label, args, expected in CASES:
        check = det.check_paired_design_formula(*args)
        results.append({'case': label, 'args': list(args),
                        'verdict': check.verdict, 'expected': expected,
                        'asExpected': check.verdict == expected})

    # 🚨 清冊裡到底有沒有 studyDesign
    fields = collections.Counter()
    items = 0
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        inventory = json.loads(path.read_text(encoding='utf-8'))
        for reported in inventory['reportedOutcomes']:
            items += 1
            for key in ('studyDesign', 'analysisReported', 'nSubjects'):
                if reported.get(key) is not None:
                    fields[key] += 1

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('守衛本身有效——用對詞時會亮（必觸發之正對照）',
          all(r['asExpected'] for r in results if r['case'].startswith('✅')),
          '🚨 正對照 %s；⚠️ 若不亮，本支的「不設防」就沒有對比基準'
          % [(r['case'], r['verdict']) for r in results
             if r['case'].startswith('✅')])
    probe('詞彙是從產品原始碼取的（必觸發之正對照）',
          len(vocab) == 4 and 'RCT-crossover' in vocab,
          '🚨 抽出的配對設計詞彙：%s；⚠️ 抽不到就代表本支在手打' % vocab)
    probe('自然拼法 `crossover` 會被靜默略過（必觸發之反向）',
          next(r['verdict'] for r in results
               if '自然拼法' in r['case']) == 'NOT_APPLICABLE',
          '🚨 `crossover` → NOT_APPLICABLE；'
          '⚠️ 這與儀器允許清單是同一族：**逐字比對、沒有同義字**')
    # 🚨 這一道是答案。
    probe('清冊裡有記 `studyDesign`',
          fields.get('studyDesign', 0) > 0,
          '🚨 %d 項報告結局中，記了 `studyDesign` 的 %d 項、'
          '`analysisReported` %d 項、`nSubjects` %d 項；'
          '⚠️ 都是 0 就代表那道守衛**現在對每一項都是 NOT_APPLICABLE**'
          % (items, fields.get('studyDesign', 0),
             fields.get('analysisReported', 0), fields.get('nSubjects', 0)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'paired-design-guard-inert',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'guard': 'ahig/stats/deterministic.py → check_paired_design_formula',
        'ruleId': 'STAT-012-paired-vs-independent',
        'vocabularyFromSource': vocab,
        'cases': results,
        'inventoryFieldCoverage': {'reportedOutcomes': items,
                                   **{k: fields.get(k, 0) for k in
                                      ('studyDesign', 'analysisReported',
                                       'nSubjects')}},
        'whyItMatters': (
            '🚨 這個領域幾乎都是**交叉設計**——'
            '⚠️ 而交叉設計誤用獨立樣本公式會**高估變異數、灌大信賴區間**。'
            '✅ 產品有一道檢查在守它（且實測會亮：宣告獨立樣本 → FAIL；'
            '自由度用成 2n−2 → FAIL）。'
            '**🚨 但清冊裡沒有任何一項記了設計，故它現在對每一項都是'
            '`NOT_APPLICABLE`——形同不設防。**'),
        'consequenceForD25': (
            '⚠️ `D25` 若只抽「數值」而不抽**設計、分析方式、樣本數**，'
            '🚨 這道守衛**還是不會亮**。'
            '✅ 而且詞彙是逐字比對：**必須用 %s 之一**，'
            '🚫 寫 `crossover` 沒有用。'
            '**⚠️ 那與 `D2`／`D24` 的儀器名稱是同一族的病。**' % vocab),
        'whatThisIsNot': (
            '🚫 本支**不主張**產品該收同義字——⚠️ 那是裁定。'
            '✅ 它只指出：**現況下這道檢查對每一項都不適用**，'
            '而那件事在 `D25` 的規格裡沒有被寫下來。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n718 配對設計守衛的現況 ===')
    print('   規則 %s｜詞彙（取自原始碼）：%s'
          % (doc['ruleId'], vocab))
    print('   實測：')
    for row in results:
        print('      %-28s %-46s → %-16s %s'
              % (row['case'], str(row['args']), row['verdict'],
                 '✅' if row['asExpected'] else '🚨 與預期不符'))
    print('   清冊欄位覆蓋（%d 項報告結局）：studyDesign %d｜'
          'analysisReported %d｜nSubjects %d'
          % (items, fields.get('studyDesign', 0),
             fields.get('analysisReported', 0), fields.get('nSubjects', 0)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
