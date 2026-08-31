# -*- coding: utf-8 -*-
"""**閘門那七道樣式，喊得出來嗎。**（第 553 輪）

## 🚨 閘門已有的與還缺的

`round_gate.py` 做得很紮實：樣式與看板公告的原件逐字比對（`board_provenance`）、
期待為空者各配一個「必定命中」的控制探針並設下限、掃描一律用 `re.M`。

**⚠️ 但控制探針用的是另外的樣式**（`candidateId`／`import`／`^## `）——
**🚨 它們證明的是「讀得到、比對得動」，🚫 不是「那七道樣式打得中它們要打的東西」。**

而閘門自己記著一個更弱的地方：

> 「🚨 n+54 三式無法比對——看板只公告了三式中的一式，另兩式以『等三式』帶過。
>  ⚠️ 故那三式在本檔仍是重打，未經原件驗證。」

**🚨 那三式既沒有原件比對，也沒有自己的正向對照**——
⚠️ 若其中一式打錯（例如少一個空白），它會每輪回報 ✅ 而永遠打不中任何東西。

## ✅ 做法：把閘門**實際在用**的樣式取出來，🚫 不重打一份

重打就是這一題本身的病。**✅ 故本支以 AST 從 `round_gate.py` 取出
`CARET`／`LT`／`GT`／`EQ`／`PASS1`／`CONFLICT`／`PAT`／`INNER` 的字面值再求值**——
🚫 不匯入該模組（它是腳本，一匯入就整個跑起來）。

每一道配：**必中的正樣本** ＋ **必不中的近似樣本**。
⚠️ 近似樣本不是為了好看——**🚨 一個什麼都打得中的樣式，正樣本一樣會過。**

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import ast
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

GATE = Path(__file__).resolve().parent / 'round_gate.py'
OUT = Path(__file__).resolve().parent / 'n553_gate_pattern_controls.json'

WANTED = ('CARET', 'LT', 'GT', 'EQ', 'PASS1', 'CONFLICT', 'PAT', 'INNER')


def patterns_from_gate():
    """從閘門原始碼取出它**實際在用**的樣式。🚫 不匯入、🚫 不重打。"""
    tree = ast.parse(GATE.read_text(encoding='utf-8'))
    namespace = {'chr': chr, 're': re}
    got = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        names = [t.id for t in node.targets if isinstance(t, ast.Name)]
        tupled = [e.id for t in node.targets if isinstance(t, ast.Tuple)
                  for e in t.elts if isinstance(e, ast.Name)]
        if not (set(names + tupled) & set(WANTED)):
            continue
        exec(compile(ast.Module(body=[node], type_ignores=[]), '<gate>', 'exec'),
             namespace)
        for name in names + tupled:
            if name in WANTED:
                got[name] = namespace[name]
    missing = [name for name in WANTED if name not in got]
    if missing:
        print('🚨 從閘門取不到：%s——🚫 拒絕以重打的樣式代替' % missing,
              file=sys.stderr)
        sys.exit(2)
    return got


def main():
    g = patterns_from_gate()
    caret, lt, gt, eq = g['CARET'], g['LT'], g['GT'], g['EQ']

    # 正樣本＝必中；近似樣本＝必不中。⚠️ 近似樣本刻意「差一點」。
    cases = []
    for pat, name in g['PASS1'] + g['CONFLICT']:
        cases.append({'pattern': name, 'regex': pat})

    samples = {
        'title-line': ('TITLE: Carbohydrate ingestion during exercise',
                       ' TITLE: 前面多一個空白'),
        'abstract-line': ('ABS: Background Carbohydrate…',
                          'XABS: 前面多一個字'),
        'europepmc-field': ('{"abstract' + 'Text": "…"}',
                            '{"abstract' + '_text": "…"}'),
        'indented-title': ('   T: Carbohydrate ingestion',
                           '  T: 只縮排兩格'),
        'merge-begin': (lt + ' HEAD', lt + 'HEAD'),
        'merge-end': (gt + ' branch', gt + 'branch'),
        'merge-sep': (eq, eq + '='),
    }

    results, missed_positive, matched_negative = [], [], []
    for case in cases:
        name = case['pattern']
        positive, negative = samples[name]
        # ⚠️ 前面補一行，才是真的在測 re.M；🚨 貼在檔頭連沒有 re.M 也會過。
        rx = re.compile(case['regex'], re.M)
        hit_pos = bool(rx.search('前置一行，用來逼出 re.M\n' + positive + '\n'))
        hit_neg = bool(rx.search('前置一行\n' + negative + '\n'))
        if not hit_pos:
            missed_positive.append(name)
        if hit_neg:
            matched_negative.append(name)
        results.append({'pattern': name, 'regex': case['regex'],
                        'catchesTheThingItIsFor': hit_pos,
                        'alsoCatchesTheNearMiss': hit_neg,
                        'nearMiss': negative})

    probes = []

    def probe(pname, ok, detail):
        probes.append({'probe': pname, 'passed': bool(ok), 'detail': detail})

    probe('七道樣式全部打得中它們要打的東西',
          not missed_positive,
          '🚨 打不中的樣式會每輪回報 ✅ 而永遠抓不到任何東西；'
          '打不中者：%s' % (missed_positive or '無'))
    probe('近似樣本一個都不中（必觸發之反向）',
          not matched_negative,
          '🚨 什麼都打得中的樣式，正樣本一樣會過；誤中者：%s'
          % (matched_negative or '無'))
    probe('樣式是從閘門取出的，🚫 不是重打的',
          len(cases) == 7 and all(c['regex'] for c in cases),
          '取到 %d 道（PASS1 四 ＋ CONFLICT 三）' % len(cases))
    probe('行首錨定真的靠 re.M（必觸發）',
          not re.compile(g['PASS1'][0][0]).search('x\nTITLE: y'),
          '🚨 若不加 re.M 也打得中，代表這個正樣本沒有在測錨定')

    doc = {
        'schemaVersion': 1,
        'documentType': 'gate-pattern-positive-controls',
        'ruling': 'n+112（二）：期待為空之檢查無法自證——閘門的控制探針用的是別的樣式',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'why': ('⚠️ 閘門的控制探針證明「讀得到、比對得動」，'
                '🚫 不證明那七道樣式打得中它們要打的東西。'
                '🚨 而 n+54 三式既沒有原件比對（看板只公告一式），'
                '也沒有自己的正向對照——打錯一個空白就會永遠回報 ✅。'),
        'source': ('以 AST 從 round_gate.py 取出實際在用的字面值，'
                   '🚫 不匯入（它是腳本）、🚫 不重打（重打正是這一題的病）。'),
        'cases': results,
        'missedPositive': missed_positive,
        'matchedNearMiss': matched_negative,
        'coverageFactMeasured': (
            '⚠️ 近似樣本順帶量到一件事：`^TITLE:` 打的是**零縮排**，'
            '而 `^   T: ` 打的是**恰好三格縮排**。'
            '🚨 故「兩格縮排的 TITLE:」兩道都打不中。'
            '🚫 本室不主張改樣式（那是看板公告的原件），'
            '✅ 只把這個涵蓋事實記下來——⚠️ 它先前沒有被寫在任何地方。'),
        'whatThisDoesNotProve': [
            '🚨 不證明樣式**該**長這樣——那是原件比對的事，'
            '⚠️ 而 n+54 三式的原件看板上沒有完整公告。',
            '🚨 不證明沒有文獻內容：閘門自己的涵蓋範圍聲明已載明'
            '「不加標記的英文題名」抓不到。',
        ],
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n553 閘門樣式的正向對照 ===')
    print('   取出 %d 道（🚫 非重打）' % len(cases))
    for item in results:
        print('   %s %-18s 正樣本%s｜近似樣本%s'
              % ('✅' if item['catchesTheThingItIsFor']
                 and not item['alsoCatchesTheNearMiss'] else '🚨',
                 item['pattern'],
                 '中' if item['catchesTheThingItIsFor'] else '**不中**',
                 '誤中' if item['alsoCatchesTheNearMiss'] else '不中'))
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
