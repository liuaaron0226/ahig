# -*- coding: utf-8 -*-
"""**D25 要抽哪些欄位——從既有的消費端反推，🚫 不是本室設計的。**（第 676 輪）

## ✅ 為什麼是這一題

第 675 輪新增 D25：「要不要開一輪數值抽取」，並建議排最前面。
🚨 而一道裁定若不知道「要抽什麼、抽多少」，就很難裁。

> **✅ 但這件事不必猜：產品裡**已經有消費端**——
> `stats/deterministic.run_all(sr)` 直接吃一份 StudyResult，
> `stats/grade.meta_analyse_dl(effects, variances)` 吃效應量與變異數。**
> **🚨 故「要抽哪些欄位」是**從程式讀得出來的**，🚫 不是本室設計的。**

## ✅ 做法

1. **用 AST** 從 `run_all` 抽出它實際讀的 `sr` 欄位（🚫 不是手打清單），
   ⚠️ 連「先 `sr.get(...)` 存成變數、再取子欄位」的那些也一起抽。
2. 對照**清冊現有欄位**：哪些已經有、哪些沒有。
3. **實跑證明最小欄位集**：只填最小集，看 `run_all` 與 `meta_analyse_dl`
   跑不跑得動。

## 🚨 而最小集比想像的小

⚠️ 產品裡有 `se_from_ci(ci_low, ci_high, measure)`——
**🚨 故變異數不必另外抽，信賴區間就推得出來。**

## 🚫 本支不改任何清冊與契約、不送外部請求、不動產品程式
"""
import ast
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
from ahig.stats import grade  # noqa: E402

OUT = Path(__file__).resolve().parent / 'n676_numeric_field_requirements.json'
SOURCE = REPO / 'ahig' / 'ahig' / 'stats' / 'deterministic.py'
CONTRACT = (REPO / 'ahig' / 'calibration' / 'b11-carbohydrate'
            / 'scope-contract.json')

# 🚨 只填這些，看跑不跑得動。⚠️ 這一組是本支要**證明**的，不是宣稱的。
MINIMAL = {
    'effectMeasure': 'MD',
    'pointEstimate': 2.0,
    'ciLow': 0.5,
    'ciHigh': 3.5,
    'nSubjects': 12,
}


class Reader(ast.NodeVisitor):
    """抽出 `run_all` 讀了 sr 的哪些欄位（含存成變數後再取的子欄位）。"""

    def __init__(self):
        self.top = set()
        self.alias = {}          # 變數名 → 它來自 sr 的哪個欄位
        self.nested = collections.defaultdict(set)

    @staticmethod
    def _key(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        return None

    def visit_Assign(self, node):
        value = node.value
        key = None
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) \
                and value.func.attr == 'get' \
                and isinstance(value.func.value, ast.Name) \
                and value.func.value.id == 'sr' and value.args:
            key = self._key(value.args[0])
        elif isinstance(value, ast.Subscript) \
                and isinstance(value.value, ast.Name) and value.value.id == 'sr':
            key = self._key(value.slice)
        if key:
            self.top.add(key)
            for target in node.targets:
                if isinstance(target, ast.Name):
                    self.alias[target.id] = key
        self.generic_visit(node)

    def visit_Call(self, node):
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'get' \
                and node.args:
            base = node.func.value
            key = self._key(node.args[0])
            if key and isinstance(base, ast.Name):
                if base.id == 'sr':
                    self.top.add(key)
                elif base.id in self.alias:
                    self.nested[self.alias[base.id]].add(key)
        self.generic_visit(node)

    def visit_Subscript(self, node):
        key = self._key(node.slice)
        if key and isinstance(node.value, ast.Name):
            if node.value.id == 'sr':
                self.top.add(key)
            elif node.value.id in self.alias:
                self.nested[self.alias[node.value.id]].add(key)
        self.generic_visit(node)

    def visit_For(self, node):
        # ⚠️ `for arm in sr.get("armAccounting", [])` 之類：迴圈變數也要接上。
        value = node.iter
        key = None
        if isinstance(value, ast.Call) and isinstance(value.func, ast.Attribute) \
                and value.func.attr == 'get' \
                and isinstance(value.func.value, ast.Name) \
                and value.func.value.id == 'sr' and value.args:
            key = self._key(value.args[0])
        if key and isinstance(node.target, ast.Name):
            self.top.add(key)
            self.alias[node.target.id] = key
        self.generic_visit(node)


def inventory_fields():
    """在範圍內那些項目，現在有哪些欄位。"""
    from ahig.scope.matcher import ScopeMatcher
    matcher = ScopeMatcher(json.loads(CONTRACT.read_text(encoding='utf-8')))
    present, total = collections.Counter(), 0
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
            for key, value in reported.items():
                if value is not None:
                    present[key] += 1
    return present, total


def main():
    tree = ast.parse(SOURCE.read_text(encoding='utf-8'))
    func = next((n for n in ast.walk(tree)
                 if isinstance(n, ast.FunctionDef) and n.name == 'run_all'),
                None)
    if func is None:
        print('🚨 找不到 run_all，本支無從抽起')
        return 1
    reader = Reader()
    reader.visit(func)
    required = sorted(reader.top)
    nested = {k: sorted(v) for k, v in sorted(reader.nested.items())}

    present, total = inventory_fields()
    already = sorted(f for f in required if present.get(f))
    missing = sorted(f for f in required if not present.get(f))

    # ✅ 實跑：只填最小集。
    ran = det.run_all(dict(MINIMAL))
    se = det.se_from_ci(MINIMAL['ciLow'], MINIMAL['ciHigh'],
                        MINIMAL['effectMeasure'])
    pooled = grade.meta_analyse_dl([MINIMAL['pointEstimate']] * 3,
                                   [se ** 2] * 3)

    # 🚨 必觸發之反向：把信賴區間拿掉，統合分析就不該推得出變異數。
    crippled = dict(MINIMAL)
    crippled.pop('ciLow')
    crippled.pop('ciHigh')
    crippled_checks = det.run_all(crippled)['n_checks']

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('從產品程式真的抽出了欄位（必觸發之正對照）',
          len(required) >= 10,
          '🚨 抽出 %d 個頂層欄位、%d 個有子欄位；⚠️ 太少代表 AST 抽取失敗'
          % (len(required), len(nested)))
    probe('捏造的欄位名不在抽出的清單裡（必觸發之反向）',
          'field-that-cannot-exist-676' not in required,
          '🚨 捏造欄位不在清單；⚠️ 若在，代表抽的不是真的讀取點')
    probe('只填最小集就跑得動（必觸發之正對照）',
          ran['n_checks'] > 0 and pooled.get('k') == 3,
          '🚨 `run_all` 跑出 %d 道檢查、判定 %s；'
          '`se_from_ci` 得 SE=%.4f；`meta_analyse_dl` 得 k=%s、pooled=%.3f；'
          '⚠️ 跑不動的話「最小集」只是本室的說法'
          % (ran['n_checks'], ran['verdict'], se, pooled.get('k'),
             pooled.get('pooled', float('nan'))))
    probe('拿掉信賴區間之後，檢查數必須變少（必觸發之反向）',
          crippled_checks < ran['n_checks'],
          '🚨 完整最小集 %d 道 → 拿掉信賴區間 %d 道；'
          '⚠️ 若沒變少，代表那三道檢查根本沒吃到信賴區間，'
          '本支的「最小集」就沒有根據'
          % (ran['n_checks'], crippled_checks))
    # 🚨 這一道是答案。
    probe('清冊現有的欄位已足以跑統合分析',
          not missing,
          '🚨 消費端要 %d 個欄位，清冊已有 %s，**缺 %s**；'
          '⚠️ 缺的每一個都得靠數值抽取那一輪補'
          % (len(required), already, missing))

    doc = {
        'schemaVersion': 1,
        'documentType': 'numeric-field-requirements',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'derivedFrom': 'ahig/stats/deterministic.py → run_all（AST，🚫 非手打）',
        'requiredTopLevelFields': required,
        'nestedFields': nested,
        'inScopeItems': total,
        'fieldsAlreadyInInventory': {f: present.get(f, 0) for f in required},
        'alreadyPresent': already,
        'missing': missing,
        'minimalSetProven': sorted(MINIMAL),
        'minimalSetRun': {'checks': ran['n_checks'], 'verdict': ran['verdict'],
                          'seFromCi': round(se, 4),
                          'metaAnalysis': {k: pooled.get(k)
                                           for k in ('k', 'pooled', 'tau2')}},
        'headline': (
            '✅ 只要抽 **%s** 這幾欄，`run_all` 與 `meta_analyse_dl` 就跑得動——'
            '**🚨 變異數不必另外抽**，產品裡的 `se_from_ci` 從信賴區間推得出來。'
            % '／'.join(sorted(MINIMAL))),
        'twoTiers': {
            '第一層・合併得動': {
                'fields': sorted(MINIMAL),
                'unlocks': '✅ `meta_analyse_dl` 與 `rate_imprecision` 跑得動',
                'note': '🚨 變異數不必另抽——`se_from_ci` 從信賴區間推得出來',
            },
            '第二層・驗得動數字對不對': {
                'fields': sorted(set(required) - set(MINIMAL)),
                'unlocks': ('⚠️ `run_all` 的完整確定性檢查'
                            '（信賴區間對稱、p 與區間相符、'
                            'GRIM／GRIMMER、2×2 一致性）'),
                'note': ('🚨 最小集實跑的判定是 `INCONCLUSIVE`——'
                         '**那不是失敗，是資料不夠讓檢查下結論**。'
                         '⚠️ 第二層的欄位只在論文有報時才抽得到，'
                         '🚫 不是每一項都適用。'),
            },
        },
        'whatThisMeansForD25': (
            '⚠️ D25 問「要不要開一輪數值抽取」。'
            '✅ 本支把它的**規格**先算出來：在範圍內 %d 項，'
            '每一項要補的是 %s；🚫 其餘欄位（事件數、臂別描述、檢定統計量）'
            '**只在做得到時才加值**，🚨 不是跑統合分析的必要條件。'
            % (total, missing)),
        'methodLimit': (
            '🚨 本支只看 `run_all` 與 `grade` 這兩個消費端，'
            '🚫 不保證別的下游（報表、SHACL 形狀）沒有別的要求；'
            '⚠️ 也**不評估那些數字抽不抽得到**——'
            '**那要讀論文，而讀是 n+187 的視窗。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n676 數值抽取要抽哪些欄位（從消費端反推）===')
    print('   消費端要的頂層欄位 %d 個：' % len(required))
    for field in required:
        mark = '✅ 清冊已有 %d/%d' % (present.get(field, 0), total) \
            if present.get(field) else '🚨 清冊沒有'
        sub = ('｜子欄位 %s' % nested[field]) if field in nested else ''
        print('      %-26s %s%s' % (field, mark, sub))
    print('   最小集實跑：%s' % doc['minimalSetRun'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
