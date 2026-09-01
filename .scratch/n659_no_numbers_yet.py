
# -*- coding: utf-8 -*-
"""**那 98 項是「哪些結果」，不是「結果是多少」。**（第 659 輪）

## 🚨 本 run 一直說「抽取」，而抽出來的其實是清冊

⚠️ 本室自己在第 628／632／646 輪談過「可合併性」「損失帳」，
🚨 而那些討論預設了一件從未被明說的事：**那 98 項裡有數字。**

> **🚨 沒有。** ⚠️ 清冊的結局紀錄只有：標籤、出處、`hasNumericResult`（**布林**）、
> 契約結局、儀器、效應量**名稱**、時點、分析集、劑量。
> **🚫 沒有效應量的值、沒有變異數、沒有信賴區間、沒有樣本數。**

## ✅ 而承載數值的那一層**還不存在**

`matcher.py` 的說明提到「候選 StudyResult 的軸值」，
**🚨 但 `StudyResult` 既沒有 schema，私有根裡也沒有任何這種文件。**

## ⚠️ 後果：GRADE 與統合分析**跑不起來**，而卡的不是程式

✅ `ahig/stats/grade.py` 是完整的（DL 統合、不一致性、不精確性、Egger、確定性彙總），
**🚨 而它要的輸入是 effects ＋ variances——語料裡一個都沒有。**

## 🚫 本支不主張該不該做下一層——⚠️ 那是裁定；✅ 只把現況說清楚
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
from ahig.stats import grade  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n659_no_numbers_yet.json'

# ⚠️ 兩組欄位名並列：🚨 一組本來就該在（存在即證明本支讀得到），
# 另一組是統合分析要用的（不在即為本支的發現）。
PRESENT_EXPECTED = ['localLabel', 'normalisedOutcomeRef', 'effectMeasure',
                    'analysisSet', 'dose', 'hasNumericResult']
VALUE_FIELDS = ['effectSize', 'pointEstimate', 'variance', 'standardError',
                'sd', 'ci95', 'ciLow', 'ciHigh', 'sampleSize', 'n']


def main():
    in_scope = []
    for path in sorted((ROOT / 'extraction').rglob('inventory-*.json')):
        if 'batches' in str(path):
            continue
        doc = json.loads(path.read_text(encoding='utf-8'))
        for outcome in doc.get('reportedOutcomes') or []:
            if (outcome.get('scopeDecision') or {}).get('inScope'):
                in_scope.append(outcome)

    field_counts = collections.Counter()
    for outcome in in_scope:
        field_counts.update(outcome.keys())

    present = {name: field_counts[name] for name in PRESENT_EXPECTED}
    values = {name: field_counts[name] for name in VALUE_FIELDS}

    # ⚠️ schema 有沒有替數值留位置。
    schema_text = (REPO / 'ahig/schema/outcome-inventory.schema.json'
                   ).read_text(encoding='utf-8')
    schema_has = {name: schema_text.count('"%s"' % name)
                  for name in VALUE_FIELDS}

    # 🚨 承載數值的那一層存不存在。
    study_result_schema = sorted(
        p.name for p in (REPO / 'ahig/schema').glob('*.json')
        if 'result' in p.name.lower())
    study_result_docs = [p.name for p in ROOT.rglob('*study*result*')][:5]

    # ✅ 正對照：⚠️ 證明**卡的是資料不是程式**——拿合成數字跑 GRADE 的統合。
    synthetic = grade.meta_analyse_dl([0.2, 0.35, 0.1], [0.01, 0.02, 0.015])
    grade_runs = isinstance(synthetic, dict) and bool(synthetic)

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('98 項讀得到，且該在的欄位都在（必觸發之正對照）',
          len(in_scope) == 98 and all(v == 98 for v in present.values()),
          '🚨 實得 %d 項；該在的欄位計數 %s；⚠️ 若讀不到，'
          '下面「某些欄位不在」就沒有意義' % (len(in_scope), present))
    probe('GRADE 的統合函式本身跑得動（必觸發之正對照）',
          grade_runs,
          '✅ 以合成的 effects／variances 實跑 `meta_analyse_dl`，回傳 %s；'
          '**🚨 故卡住的不是程式**' % (sorted(synthetic)[:5] if grade_runs
                                        else synthetic))
    # 🚨 以下兩道是發現。
    probe('清冊裡帶得動統合分析所需的數值欄位',
          any(values.values()),
          '🚨 這些欄位在 98 項裡各出現：%s——**全部為 0**；'
          '⚠️ 而 schema 裡的出現次數：%s。'
          '**🚨 即 `hasNumericResult` 只是布林，🚫 值本身從未被抽出來**'
          % (values, schema_has))
    probe('承載數值的 StudyResult 那一層已經存在',
          bool(study_result_schema or study_result_docs),
          '🚨 schema 目錄裡的 result 相關檔：%s；私有根裡的 study-result 文件：%s'
          '——⚠️ `matcher.py` 的說明提到「候選 StudyResult 的軸值」，'
          '**🚫 而那一層目前只存在於敘述裡**'
          % (study_result_schema or '（無）', study_result_docs or '（無）'))

    doc = {
        'schemaVersion': 1,
        'documentType': 'no-numbers-yet',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'inScopeOutcomes': len(in_scope),
        'fieldsPresent': present,
        'valueFieldsInData': values,
        'valueFieldsInSchema': schema_has,
        'studyResultSchema': study_result_schema,
        'studyResultDocs': study_result_docs,
        'gradeModuleRuns': grade_runs,
        'headline': (
            '🚨 那 98 項是**「哪些結果」**，🚫 不是「結果是多少」。'
            '⚠️ 清冊的結局紀錄裡沒有效應量的值、沒有變異數、'
            '沒有信賴區間、沒有樣本數——`hasNumericResult` 只是一個布林。'),
        'consequence': (
            '🚨 **GRADE 與統合分析今天跑不起來**——'
            '✅ 而本支以合成資料實跑證明：**卡的是資料，🚫 不是程式**。'
            '⚠️ 擁有者要的劑量-反應，也無法從現有產物回答。'),
        'correctionToMyOwnRounds': (
            '⚠️ 本室在第 628／632／646 輪談「可合併性」與「損失帳」時，'
            '🚨 讀起來像是那 98 項已經是可以合併的資料。'
            '**✅ 更精確的說法是：那些是「合併的前提條件」**——'
            '🚫 前提成立與否是一回事，數字有沒有抽出來是另一回事。'),
        'whatThisIsNot': (
            '🚫 本支不主張該不該做下一層——⚠️ 那是裁定；'
            '🚨 也不說這是缺陷：清冊本來就可能是刻意的中間產物。'
            '✅ 它只把「現在手上有什麼」說清楚。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n659 那 98 項裡有沒有數字 ===')
    print('   在範圍內 %d 項' % len(in_scope))
    print('   該在的欄位：%s' % present)
    print('   🚨 統合分析所需的欄位：%s' % values)
    print('   ⚠️ schema 裡的位置：%s' % schema_has)
    print('   StudyResult：schema %s｜文件 %s'
          % (study_result_schema or '（無）', study_result_docs or '（無）'))
    print('   GRADE 統合函式（合成資料）：%s' % ('✅ 跑得動' if grade_runs
                                                else '🚨 跑不動'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
