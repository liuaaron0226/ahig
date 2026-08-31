# -*- coding: utf-8 -*-
"""**`scoped → family／gates` 那個箭頭，在程式裡存在嗎。**（第 545 輪）

## 🚨 為什麼問這個

n+183 畫的圖是：

```
corpus ✅ → draft ← 要模型讀 → scoped（既有 ScopeMatcher）✅ → family／gates（既有）✅
```

**⚠️ 「（既有）✅」說的是那兩個模組存在——那是真的。**
**🚨 但箭頭說的是「清冊會流進去」，而那是另一件事。**

> ⚠️ n+181 查到的正是這一型：**看板寫了八輪的「待萃取期」，實情是東西沒被造出來。**
> **✅ 故本支不讀圖，去問程式。**

## 🚫 本支不主張這是缺陷

⚠️ M1 的四步是 ①篩選 ②校準集 ③取全文 ④**萃取**，
**🚨 而「萃取」的產物是清冊（OutcomeInventory），不是 StudyResult。**
故「沒有人造 StudyResult」**可能完全符合 M1 的範圍**。

> **🚫 那是協調者的判斷，不是本室的。**
> **✅ 本支只把「什麼存在、什麼不存在」量出來**——
> ⚠️ 因為讀那張圖的人會以為判完範圍之後管線自己會接下去，**🚨 而它不會。**

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import ast
import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

PKG = REPO / 'ahig' / 'ahig'
SCHEMA_DIR = REPO / 'ahig' / 'schema'
OUT = Path(__file__).resolve().parent / 'n545_downstream_edge.json'

NAMES = ('studyResultId', 'StudyResult', 'OutcomeInventory',
         'reportedOutcomes', 'scopeDecision', 'build_families')


def main():
    files = sorted(PKG.rglob('*.py'))
    census = {name: [] for name in NAMES}
    inventory_params = []

    for path in files:
        rel = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding='utf-8')
        for name in NAMES:
            hits = text.count(name)
            if hits:
                census[name].append({'file': rel, 'hits': hits})
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            args = [a.arg for a in node.args.args + node.args.kwonlyargs]
            wanted = [a for a in args
                      if 'inventor' in a.lower() or 'scoped' in a.lower()]
            if wanted:
                inventory_params.append(
                    {'file': rel, 'function': node.name, 'params': wanted})

    # family 那一端吃的是什麼——直接讀它的 dataclass 欄位，🚫 不憑印象。
    family_src = (PKG / 'stats' / 'family.py').read_text(encoding='utf-8')
    tree = ast.parse(family_src)
    report_fields = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == 'Report':
            report_fields = [n.target.id for n in node.body
                             if isinstance(n, ast.AnnAssign)
                             and isinstance(n.target, ast.Name)]
    build_families_params = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == 'build_families':
            build_families_params = [a.arg for a in node.args.args
                                     + node.args.kwonlyargs]

    schemas = sorted(p.name for p in SCHEMA_DIR.glob('*.json'))

    outside = [h for h in census['reportedOutcomes']
               if '/extraction/' not in h['file'] and '/scope/' not in h['file']]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('整個套件沒有任何東西造 StudyResult',
          not census['studyResultId'],
          '🚨 `studyResultId` 出現 %d 個檔；⚠️ 有的話代表確實有人在造'
          % len(census['studyResultId']))
    probe('沒有 study-result 的 JSON Schema',
          not any('study-result' in s for s in schemas),
          'schema 目錄：%s' % ', '.join(schemas))
    probe('family 那一端吃的是書目欄位，不是清冊',
          'work_id' in report_fields and not any(
              'inventor' in f.lower() for f in report_fields),
          'Report 欄位：%s' % ', '.join(report_fields))
    probe('清冊只被萃取／範圍兩處消費',
          not outside,
          '🚨 其他地方也讀 reportedOutcomes 的話，那才是箭頭；'
          '實得：%s' % ([h['file'] for h in outside] or '無'))
    # 必觸發：census 本身要找得到東西，否則「都是 0」只是搜壞了。
    probe('搜尋本身有效（必觸發）',
          bool(census['OutcomeInventory']) and bool(inventory_params),
          '🚨 若連 OutcomeInventory 與帶 inventory 參數的函式都找不到，'
          '代表搜壞了；實得 %d 檔／%d 個函式'
          % (len(census['OutcomeInventory']), len(inventory_params)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'downstream-edge-census',
        'ruling': 'n+183 之圖：scoped → family／gates（既有）',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'question': ('⚠️「（既有）」說的是模組存在——那是真的。'
                     '🚨 箭頭說的是清冊會流進去——本支問的是這個。'),
        'filesScanned': len(files),
        'identifierCensus': {k: v for k, v in census.items()},
        'functionsTakingInventory': inventory_params,
        'familyEnd': {
            'buildFamiliesParams': build_families_params,
            'reportFields': report_fields,
            'reading': ('🚨 `build_families` 吃的是 `Report`，'
                        '而 `Report` 的欄位全是書目層（work_id／doi／authors／'
                        'registry_id…）。⚠️ 那是「同一個試驗的多份報告」之歸群，'
                        '🚫 與清冊裡的數值無關。'),
        },
        'gatesEnd': ('⚠️ `gates/quality_gate.evaluate_batch_quality` 吃的是'
                     'sample_size／error_count，🚫 不吃清冊。'),
        'schemas': schemas,
        'finding': (
            '🚨 沒有任何程式碼把 scoped 清冊接到 family 或 gates；'
            '⚠️ 也沒有任何程式碼**造** StudyResult——'
            '而 StudyResult 正是 SHACL 約束最多、`stats/deterministic.py` 在檢查的那一種文件。'
            '✅ `ScopeMatcher` 決定的是「該不該產生 StudyResult」與其上限，'
            '🚫 不是產生它。'),
        'whatThisDoesNotClaim': (
            '🚫 本支不主張這是缺陷。⚠️ M1 第四步的產物是清冊，不是 StudyResult，'
            '故「沒有人造它」可能完全符合 M1 範圍。'
            '🚨 但讀那張圖的人會以為判完範圍之後管線自己會接下去，而它不會——'
            '✅ 該不該接、何時接，請協調者裁。'),
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n545 下游那個箭頭的普查 ===')
    print('   掃描 %d 個 .py' % len(files))
    print('   studyResultId 出現於：%s'
          % ([h['file'] for h in census['studyResultId']] or '🚨 無'))
    print('   讀 reportedOutcomes 者：%s'
          % [h['file'] for h in census['reportedOutcomes']])
    print('   帶 inventory／scoped 參數之函式：%d 個' % len(inventory_params))
    print('   build_families(%s)；Report 欄位 %d 個，皆書目層'
          % (', '.join(build_families_params), len(report_fields)))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
