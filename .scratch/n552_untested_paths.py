# -*- coding: utf-8 -*-
"""**萃取套件裡，哪些函式沒有任何測試走過。**（第 552 輪）

## 🚨 為什麼要系統化地問一次

第 551 輪抓到的缺陷（預設名冊把讀不出來的紀錄濾掉）之所以存在到現在，
**唯一的原因是沒有任何測試走過那條路**——所有測試與演練都明給 `candidate_ids`。

**⚠️ 那不是憑直覺一條一條想得完的。** 本機沒有 `coverage`，
**✅ 但 `sys.settrace` 是標準庫**——夠用來回答「這個函式有沒有被執行過」。

## 🚨 這一支量的是什麼、不是什麼

- ✅ 量得到：**函式層級**——某函式體內是否有任何一行被執行過。
- 🚨 量不到：**分支**。⚠️ 一個函式被走過，不代表它的每個 `if` 都被走過；
  🚨 第 551 輪那個缺陷剛好是「整條路沒走過」，但下一個未必是。
- 🚨 量不到：**斷言得對不對**。⚠️ 走過不等於驗過——
  第 549 輪那個沒接上的計數器就是走過而沒驗到。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import ast
import io
import json
import os
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))
sys.path.insert(0, str(REPO / 'ahig' / 'tests'))

from ahig.contracts.freeze import content_hash  # noqa: E402

PKG = REPO / 'ahig' / 'ahig' / 'extraction'
TEST_MODULES = ('test_extraction_corpus', 'test_extraction_run',
                'test_extraction_worksheet', 'test_extraction_route',
                'test_extraction_bridge', 'test_extraction_chain')
OUT = Path(__file__).resolve().parent / 'n552_untested_paths.json'


def path_text(path):
    return path.read_text(encoding='utf-8').splitlines()


def statements_of(path):
    """可執行敘述的行號。🚫 排除 docstring——它被編成常數，不會有 line 事件，
    留著會變成一堆假的「沒走過」。"""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    lines = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.stmt):
            continue
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
                and isinstance(node.value.value, str)):
            continue
        lines.add(node.lineno)
    return lines


def functions_of(path):
    """(名稱, 起, 迄)。巢狀函式也算——⚠️ 它們一樣可能整段沒被走過。"""
    tree = ast.parse(path.read_text(encoding='utf-8'))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            found.append((node.name, node.lineno, node.end_lineno))
    return found


def main():
    targets = {str(p.resolve()): functions_of(p) for p in sorted(PKG.glob('*.py'))}
    seen = {path: set() for path in targets}

    def tracer(frame, event, arg):
        if event == 'call':
            return tracer
        if event == 'line':
            path = frame.f_code.co_filename
            if path in seen:
                seen[path].add(frame.f_lineno)
        return tracer

    ran, failed = 0, []
    old_root = os.environ.get('AHIG_PRIVATE_ROOT')
    sys.settrace(tracer)
    try:
        for name in TEST_MODULES:
            module = __import__(name)
            for attr in sorted(dir(module)):
                if not attr.startswith('test_'):
                    continue
                function = getattr(module, attr)
                if not callable(function):
                    continue
                try:
                    function()
                    ran += 1
                except Exception as error:  # noqa: BLE001
                    failed.append('%s.%s: %s: %s'
                                  % (name, attr, type(error).__name__,
                                     str(error)[:80]))
    finally:
        sys.settrace(None)
        if old_root is None:
            os.environ.pop('AHIG_PRIVATE_ROOT', None)
        else:
            os.environ['AHIG_PRIVATE_ROOT'] = old_root

    # 行層：分支藏在這裡。函式被走過 ≠ 它的每個 if 都被走過。
    never_run = []
    for path in targets:
        rel = Path(path).relative_to(REPO).as_posix()
        source = path_text(Path(path))
        for line in sorted(statements_of(Path(path)) - seen[path]):
            never_run.append({'file': rel, 'line': line,
                              'source': source[line - 1].strip()[:80]})

    untouched, touched = [], 0
    for path, functions in targets.items():
        rel = Path(path).relative_to(REPO).as_posix()
        for name, start, end in functions:
            hit = any(start <= line <= end for line in seen[path])
            if hit:
                touched += 1
            else:
                untouched.append({'file': rel, 'function': name,
                                  'lines': '%d-%d' % (start, end)})

    probes = []

    def probe(pname, ok, detail):
        probes.append({'probe': pname, 'passed': bool(ok), 'detail': detail})

    probe('測試全部跑得起來', not failed,
          '🚨 有測試在這裡跑不起來的話，未走到的清單會偏大；失敗 %d：%s'
          % (len(failed), failed[:2]))
    probe('追蹤器真的有記到東西（必觸發）', touched > 0,
          '🚨 若一個函式都沒記到，「全部沒走過」會是假的；實得走過 %d 個'
          % touched)
    # 🚨 「一行都不剩」不是本支的標的，也不該是——⚠️ 逼每一個防禦性 raise
    # 都被觸發，會逼出一堆為了覆蓋率而寫的測試，而那些測試不保護任何主張。
    # ✅ 本支挑的是**護住某個主張**的那幾道：它們一道都不許留。
    must_cover = [
        ('每一篇都有下落（送進來的與交回來的要對得上）', '下落與送進來的候選對不上'),
        ('每一篇都有下落', '未知階段'),
        ('每一篇都有下落', '判為成功卻沒有 scoped'),
        ('不默默挑第一份全文', 'artifacts 有'),
        ('指得出被讀的是哪一份', '無從指明被讀的是哪一份'),
        ('清冊要有綁定才存得進去', '無從決定它是誰的'),
        ('批次 id 由內容導出', '同 id 不同內容代表導出方式壞了'),
        ('空工作單與沒有論文要分得出來', '空工作單與'),
        ('工作單上沒有的那一篇不得收', '不在工作單內'),
    ]
    still_open = [claim for claim, needle in must_cover
                  if any(needle in n['source'] for n in never_run)]
    probe('護住主張的那幾道守衛，全部觸發過', not still_open,
          '🚨 一道從沒觸發過的守衛，與一道不存在的守衛，在紀錄上分不出來；'
          '仍未觸發：%s' % (still_open or '無'))
    probe('沒有任何函式整段沒被走過', not untouched,
          '未走過 %d 個：%s' % (len(untouched),
                                [u['function'] for u in untouched]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'extraction-function-coverage',
        'ruling': '第 551 輪之後續：把「沒有測試走過的路」系統化地問一次',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'method': ('sys.settrace 逐行記錄，'
                   '再與 AST 取出的函式行號區間對照。🚫 本機無 coverage。'),
        'testModules': list(TEST_MODULES),
        'testsRun': ran,
        'testFailures': failed,
        'functionsTotal': touched + len(untouched),
        'functionsTouched': touched,
        'functionsUntouched': untouched,
        'statementsNeverRun': never_run,
        'guardsThatMustBeExercised': [claim for claim, _ in must_cover],
        'whyTheRestAreLeft': (
            '🚫 「一行都不剩」不是本支的標的。⚠️ 逼每一個防禦性 raise 都被'
            '觸發，會逼出一堆為了覆蓋率而寫的測試，🚨 而那些測試不保護任何'
            '主張。✅ 留下的多是型別／格式類的防呆（例如「必須是物件」、'
            '「必須是陣列」），它們壞掉會當場拋錯，🚫 不會安靜地錯。'),
        'whatThisDoesNotMeasure': [
            '🚨 分支：函式被走過 ≠ 每個 if 都被走過。'
            '⚠️ 第 551 輪那個缺陷剛好是整條路沒走過，🚫 下一個未必是。',
            '🚨 斷言：走過 ≠ 驗過。'
            '⚠️ 第 549 輪那個沒接上的計數器就是走過而沒驗到。',
        ],
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n552 萃取套件的函式層覆蓋 ===')
    print('   跑了 %d 條測試｜失敗 %d' % (ran, len(failed)))
    for line in failed[:5]:
        print('   🚨 %s' % line)
    print('   函式 %d 個：走過 %d｜未走過 %d'
          % (touched + len(untouched), touched, len(untouched)))
    print('   從未執行的敘述 %d 行' % len(never_run))
    for item in never_run[:20]:
        print('   🚨 %s:%d  %s' % (item['file'].split('/')[-1], item['line'],
                                   item['source']))
    for item in untouched:
        print('   🚨 未走過：%-22s %s（%s）'
              % (item['function'], item['file'], item['lines']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
