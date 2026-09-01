# -*- coding: utf-8 -*-
"""**把「恆真的假控制」交給工具認，不要交給記性。**（第 631 輪）

## 🚨 三輪之內本室寫壞了兩次反向控制

⚠️ 第 628 輪查出四支憑證各有一道恆真的探針，並記了 errata。
**🚨 第 630 輪本室又寫了一次**——`假值 != 真值`，其中假值就是真值加兩個字。
**⚠️ 隔一輪就再犯，代表這件事靠記性擋不住。**

> **✅ 跟第 627 輪一樣：改形狀，不是改習慣。**

## ✅ 本支怎麼認

用 AST 掃過本室每一支憑證的 `probe(名稱, 條件, 說明)`，認**三種本室已經犯過的形狀**：

| 代號 | 形狀 | 例 |
|---|---|---|
| **甲** | 條件是**字面常數** | `probe(..., True, ...)` |
| **乙** | 條件把**自己加工過的值**跟自己比 | `real + 'ZZ' != real` |
| **丙** | 條件只倚賴一個**不可能出現的哨兵字面** | `counter['ZZ-不存在-ZZ'] == 0` |

**🚨 這支工具只認得本室已經犯過的三種。⚠️ 它證明不了「沒有別種恆真」。**

## ⚠️ 丙不是「錯」，是「未證明」

哨兵探針**可能**是真的控制（例如它其實走過真正的比對路徑）。
**✅ 故丙一律標成「待證明」，🚫 不標成缺陷**——⚠️ 要證明就照第 629 輪：讓它亮一次。

## 🚫 本支不送外部請求、不改任何產品程式、不改任何憑證
"""
import ast
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

S = Path(__file__).resolve().parent
OUT = S / 'n631_probe_shape_scanner.json'

SENTINEL = re.compile(r'ZZ|不存在|竄改|假結局|改過名的')

# ⚠️ 給工具自己驗身用的樣本：🚨 三種壞形狀各一、好形狀一種。
SELF_TEST = '''
def f(data, real):
    probe('甲：恆真常數', True, '')
    probe('丁：恆假常數', False, '')
    probe('乙：自己跟自己比', real + 'ZZ' != real, '')
    probe('丙：哨兵', data['ZZ-不存在-ZZ'] == 0, '')
    probe('好的：真的看資料', len(data) == 38, '')
'''


def classify(node):
    """回傳 (代號, 說明)；不是已知壞形狀則回 None。"""
    if isinstance(node, ast.Constant):
        # 🚨 第一版把所有常數條件一律標成壞形狀——⚠️ 而實掃出來的三道全是
        # `False`：那是本室**刻意寫死的紅旗**，用來記錄一個已知的紅。
        # **✅ 關鍵的不對稱：永遠亮紅的探針不會掩蓋問題，永遠綠的才會。**
        # 🚫 故只有恆真（恆綠）算壞形狀；恆假另立一類，不算缺陷。
        if node.value:
            return ('甲', '條件是恆真的字面常數——🚨 永遠綠，會掩蓋問題')
        return ('丁', '條件是恆假的字面常數——✅ 刻意的紅旗，🚫 不算缺陷')
    if isinstance(node, ast.Compare) and len(node.comparators) == 1:
        left, right = node.left, node.comparators[0]

        def stripped_add(side, other):
            """side 是不是「other 加上一個常數」。"""
            if not isinstance(side, ast.BinOp) or not isinstance(
                    side.op, ast.Add):
                return False
            for half in (side.left, side.right):
                if isinstance(half, ast.Constant):
                    continue
                if ast.dump(half) == ast.dump(other):
                    return True
            return False

        if stripped_add(left, right) or stripped_add(right, left):
            return ('乙', '把自己加工過的值跟自己比，兩邊必不相等')
    literals = [n.value for n in ast.walk(node)
                if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    if any(SENTINEL.search(v) for v in literals):
        return ('丙', '倚賴不可能出現的哨兵字面——⚠️ 未證明它會亮')
    return None


def scan(source, label):
    rows = []
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == 'probe'
                and len(node.args) >= 2):
            continue
        name = (node.args[0].value
                if isinstance(node.args[0], ast.Constant) else '（非字面）')
        verdict = classify(node.args[1])
        rows.append({
            'artefact': label,
            'probe': str(name)[:60],
            'shape': verdict[0] if verdict else '✅ 未觸及已知壞形狀',
            'why': verdict[1] if verdict else '',
            'condition': (ast.get_source_segment(source, node.args[1])
                          or '')[:120],
        })
    return rows


def main():
    self_rows = scan(SELF_TEST, '（自驗樣本）')
    # 🚨 第一版用 r['probe'][:2] 當鍵——⚠️ 那把全形冒號也切了進去，
    # 於是查表全部落空，**工具判對了而本室的斷言是錯的**。
    self_shapes = {r['probe'].split('：')[0]: r['shape'] for r in self_rows}

    rows = []
    for path in sorted(S.glob('n*.py')):
        try:
            rows.extend(scan(path.read_text(encoding='utf-8'), path.name))
        except SyntaxError as error:
            rows.append({'artefact': path.name, 'probe': '（解析失敗）',
                         'shape': '🚨 解析失敗', 'why': str(error)[:80],
                         'condition': ''})

    # ⚠️ 丁（恆假紅旗）不列入標記——🚫 它不會掩蓋問題。
    flagged = [r for r in rows if r['shape'] in ('甲', '乙', '丙')]
    deliberate_red = [r for r in rows if r['shape'] == '丁']
    by_shape = {}
    for row in flagged:
        by_shape.setdefault(row['shape'], []).append(
            '%s｜%s' % (row['artefact'], row['probe']))

    # ⚠️ 第 629 輪已用突變證明會亮的那幾道，不再算「未證明」。
    proven = {'n624_corpus_denominator.py', 'n625_corpus_era_bias.py',
              'n626_missing_era_dose_space.py',
              'n627_dose_proxy_validation.py',
              'n628_evidence_thinness.py'}
    # ⚠️ 剩下的哨兵探針不留成「待證明」——🚨 那等於把問題記在紙上就算完。
    # ✅ 就地照第 629 輪的手法讓它亮一次：對程式碼副本注入故障，看它變不變紅。
    MUTATION = {
        'n622_attestation_audit.py': {
            'find': "            cache[report] = {str(s.title or '')\n"
                    "                             for s in corpus.load_document"
                    "(ids[report]).sections}",
            'replace': "            cache[report] = {'ZZ-不存在-ZZ'}",
            'expect': '段落存在查核說得出',
            'fault': '讓段落標題集合含有那個哨兵，'
                     '🚨 該探針必須說「它存在」而變紅',
        },
    }
    mutation_results = []
    for artefact, case in MUTATION.items():
        source = (S / artefact).read_text(encoding='utf-8')
        applied = case['find'] in source
        fired = None
        if applied:
            workdir = Path(tempfile.mkdtemp(prefix='ahig-probe-shape-'))
            env = dict(os.environ)
            env['PYTHONPATH'] = os.pathsep.join(
                [str(REPO / 'ahig'), env.get('PYTHONPATH', '')])
            env['PYTHONIOENCODING'] = 'utf-8'
            shutil.copy2(S / 'private_root.py', workdir / 'private_root.py')
            target = workdir / artefact
            target.write_text(source.replace(case['find'], case['replace']),
                              encoding='utf-8')
            result = subprocess.run(
                [sys.executable, '-X', 'utf8', str(target)], cwd=str(workdir),
                capture_output=True, text=True, encoding='utf-8',
                errors='ignore', env=env)
            for line in (result.stdout or '').split('\n'):
                stripped = line.strip()
                if case['expect'] in stripped:
                    fired = stripped.startswith('🚨')
            shutil.rmtree(workdir, ignore_errors=True)
        mutation_results.append({'artefact': artefact, 'fault': case['fault'],
                                 'faultApplied': applied, 'probeFired': fired})
        if fired:
            proven.add(artefact)

    unproven = [r for r in flagged
                if r['shape'] == '丙' and r['artefact'] not in proven]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    # 🚨 工具自己要先驗身：⚠️ 認不出已知的壞形狀，掃出來的「乾淨」毫無意義。
    probe('三種壞形狀都認得出來（必觸發之正對照）',
          (self_shapes.get('甲') == '甲' and self_shapes.get('乙') == '乙'
           and self_shapes.get('丙') == '丙'
           and self_shapes.get('丁') == '丁'),
          '🚨 自驗樣本判定：%s；⚠️ 少認一種，本支的「乾淨」就是假的'
          % self_shapes)
    probe('好的探針不會被誤判（必觸發之反向）',
          self_shapes.get('好的') == '✅ 未觸及已知壞形狀',
          '🚨 樣本裡那道 len(data) == 38 判為 %s；'
          '⚠️ 若它也被標紅，本支只是在亂噴'
          % self_shapes.get('好的'))
    probe('真的掃到東西（必觸發之正對照）',
          len(rows) >= 100,
          '🚨 掃出 %d 道探針、%d 支憑證；⚠️ 若很少，代表掃描器沒認出呼叫點'
          % (len(rows), len({r['artefact'] for r in rows})))
    # 🚨 以下兩道是結果。
    probe('沒有甲、乙兩種確定恆真的形狀',
          not [r for r in flagged if r['shape'] in ('甲', '乙')],
          '🚨 實得：%s'
          % ([(r['artefact'], r['probe']) for r in flagged
              if r['shape'] in ('甲', '乙')] or '無'))
    probe('所有哨兵探針都已被證明會亮',
          not unproven,
          '🚨 尚未證明會亮的哨兵探針 %d 道：%s'
          % (len(unproven),
             [(r['artefact'], r['probe']) for r in unproven][:8]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'probe-shape-scan',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'probesScanned': len(rows),
        'artefactsScanned': len({r['artefact'] for r in rows}),
        'flaggedCount': len(flagged),
        'deliberateRedFlags': [
            {'artefact': r['artefact'], 'probe': r['probe']}
            for r in deliberate_red],
        'asymmetryNote': (
            '✅ 恆假的探針（刻意紅旗）不列為缺陷——'
            '🚨 永遠亮紅不會掩蓋問題，⚠️ 永遠綠才會。'
            '🚨 本支第一版沒分這兩者，把 n608／n612 三道刻意的紅旗誤標成假控制。'),
        'byShape': by_shape,
        'unprovenSentinelProbes': [
            {'artefact': r['artefact'], 'probe': r['probe'],
             'condition': r['condition']} for r in unproven],
        'provenByMutation': sorted(proven),
        'mutationRunThisRound': mutation_results,
        'limits': (
            '🚨 本支只認得本室**已經犯過**的三種形狀——'
            '⚠️ 它證明不了「沒有別種恆真」。'
            '✅ 丙一律標成「待證明」而非缺陷：'
            '哨兵探針**可能**是真控制，要證明就照第 629 輪讓它亮一次。'),
        'whyItExists': (
            '⚠️ 第 628 輪記了 errata，🚨 第 630 輪本室又寫了一次同族的恆真控制。'
            '**✅ 故改形狀而非改習慣：交給工具認，不要交給記性。**'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n631 探針形狀掃描 ===')
    print('   掃過 %d 支憑證、%d 道探針｜標記 %d 道｜刻意紅旗 %d 道（不算缺陷）'
          % (len({r['artefact'] for r in rows}), len(rows), len(flagged),
             len(deliberate_red)))
    for shape, items in sorted(by_shape.items()):
        print('   形狀 %s：%d 道' % (shape, len(items)))
        for item in items[:6]:
            print('      %s' % item)
        if len(items) > 6:
            print('      …另 %d 道' % (len(items) - 6))
    for m in mutation_results:
        print('   突變驗證 %s：注入=%s｜該探針亮了=%s'
              % (m['artefact'], m['faultApplied'], m['probeFired']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
