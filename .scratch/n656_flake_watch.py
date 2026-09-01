# -*- coding: utf-8 -*-
"""**那個間歇性失敗：它是真的，而本支讓證據累積下去。**（第 656 輪）

## 🚨 四次紅、四次都沒抓到名字

⚠️ 閘門的測試那格在第 622／627／648／655 輪各紅過一次。
✅ 其中第 648 輪查明是本室的掃描改壞了 repo（已還原）；
**🚨 另外三次都沒有重現，也都沒有留下測試名。**

## ✅ 本輪主動追，而它**重現了**

連跑 20 次測試套件：**第 9 次出現 `1 failed, 839 passed`。**
**⚠️ 即它不是幽靈——但那一次的測試名仍然沒被記下來**：
🚨 pytest 的輸出帶 ANSI 顏色碼，那一行其實是 `\x1b[31mFAILED…`，
而本室那支臨時腳本的 `grep "^FAILED"` **沒有先去色**（閘門有，臨時腳本沒有）。

> **🚨 又是同一族：工具沒抓到，不等於沒有東西。**

## ✅ 故本支的設計是「累積」，不是「再追一次」

⚠️ 以本輪 20 次 1 紅估，命中率約 **5%**——**🚫 每輪重跑 20 次不划算**。
✅ 本支每次只跑少量，把結果**追加**到持久紀錄；
**🚨 而紅的那一次會連測試名一起落地**（已去色）。

## ⚠️ 本檔是**紀錄**，不是量測

🚫 故它的內容本來就會隨每次執行增長——⚠️ 拿它去比對 `auditHash` 沒有意義。
"""
import json
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_root import require  # noqa: E402

ROOT, PROV = require('fulltext')

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

S = Path(__file__).resolve().parent
OUT = S / 'n656_flake_watch.json'
PYTEST_DIR = REPO / 'ahig'

ANSI = re.compile(r'\x1b\[[0-9;]*m')
RUNS_PER_INVOCATION = 3

# ⚠️ 第 656 輪之前已觀察到的：🚨 逐次結果，來源為本輪三批追獵的終端輸出。
SEED = {
    'observedRuns': 20,
    'observedFailures': 1,
    'note': ('🚨 本輪三批追獵合計 20 次、紅 1 次（第一批的第 9 次）。'
             '⚠️ 那一次的測試名**沒有被記下來**——'
             '腳本沒去色，`grep "^FAILED"` 接不到帶 ANSI 的那行。'),
}


# ⚠️ 第 657 輪：三個假設各被測過一次，🚨 三個都沒被支持。
# ✅ 記在這裡，🚫 免得下一輪又從頭猜一遍。
HYPOTHESES = [
    {'hypothesis': '與並行負載有關',
     'test': '開 19 個燒 CPU 的行程，加壓下跑 3 回合',
     'result': '🚫 未獲支持：3 回合全綠，且**跑得比閒置時還快**（46–51s vs 52–56s）',
     'power': '⚠️ 3 回合在 4% 下只有約一成機會，**不足以否證**'},
    {'hypothesis': '與雜湊種子（集合迭代順序）有關',
     'test': '固定 PYTHONHASHSEED=0..9 各跑一次',
     'result': '🚫 未獲支持：10 個種子全綠',
     'power': '⚠️ 若有 4% 的種子會敗，10 個約有三成機會撞到'},
    {'hypothesis': '是 test_fulltext.py 裡那幾條並行測試',
     'test': '單獨密集重跑那幾條 60 回合',
     'result': '🚫 未獲支持：60 回合全綠',
     'power': '🚨 **但「單獨跑」不等於「在整套裡跑」**——'
              '⚠️ 只在完整套件情境下才發生的失敗，這樣測不出來'},
    # ✅ 第 659 輪：🚨 閘門新加的 traceback 擷取**第一次實戰就抓到了**。
    {'hypothesis': '⭐ 它就在「發布 vs 掃除」那組並行測試裡'
                   '（第 658 輪加的 traceback 擷取實戰命中）',
     'test': '閘門第 5 次紅時擷取到的失敗段落，內容為 '
             '`publish()`／`sweep()`／`staged.wait(timeout=30)`',
     'result': '✅ **獲支持**：那正是 test_fulltext.py 裡'
               '「掃除者與發布者並行時不得毀掉已提交證據」那一族',
     'power': '🚨 **而確切的斷言仍未知——本室又把輸出截斷了（第三次）**；'
              '⚠️ 且單獨跑 test_fulltext.py 25 回合（每次 1 秒、40 條）全綠，'
              '**故它需要完整套件的情境**'},
    # ⚠️ 第 660 輪：名字有了之後，直接對**那一條**加壓與密集重跑。
    {'hypothesis': '單獨密集重跑那一條就會現形',
     'test': '單獨跑該測試 60＋200 回合（每次 0.11 秒）',
     'result': '🚫 未獲支持：**260 回合全綠**',
     'power': '✅ 功率很高：整套約 4%，而這是 260 次——'
              '**🚨 故它在孤立情境下幾乎不會發生**'},
    {'hypothesis': '對那一條加壓就會現形（時序壓力）',
     'test': '19 個燒 CPU 的行程（**實測存活 19**）下跑該測試 150 回合',
     'result': '🚫 未獲支持：150 回合全綠',
     'power': '🚨 前一次的加壓實驗其實**沒有加到壓**——'
              'Windows 的 multiprocessing 無法從 stdin 重新匯入主模組，'
              '19 個行程全部 spawn 失敗而本室當時沒發現；'
              '✅ 本輪改用檔案並**驗證存活數**才算數'},
]


# ✅ 第 661 輪：**診斷完成**。🚨 下面三件是實證，不是推論。
DIAGNOSIS = {
    'failingAssertion': "assert errors == []  →  ['sweep:PermissionError']",
    'location': 'tests/test_fulltext.py:441',
    'cheapRepro': (
        '✅ **9.5 秒的重現配方**：只跑字母序前 16 個測試檔'
        '（`ls tests/test_*.py | sed -n "1,16p"`，含 test_fulltext.py）——'
        '🚨 實測 30 回合紅 1 次，而整套要 54 秒。'),
    'whatIsRuledOut': (
        '🚫 單獨跑那一條：260 回合全綠｜🚫 加壓下單獨跑：150 回合全綠｜'
        '🚫 全蒐集但只跑那一條（模組全部匯入）：120 回合全綠。'
        '**🚨 故觸發條件是「前面的測試真的執行過」，'
        '🚫 不是時序壓力、也不是匯入期的狀態。**'),
    'mechanismMostLikely': (
        '⚠️ `_sweep_orphans_locked` 對未被 manifest 引用的 staged 檔做 '
        '`path.unlink()`；🚨 **而 Windows 上刪除「正被開啟」的檔案會拋 '
        'PermissionError**（POSIX 不會——程式碼註解裡正好寫著那個假設）。'
        '⚠️ 掃除者**是持鎖之後**才 unlink 的，故最合理的解釋是'
        '**寫入者的檔案控制代碼在釋放鎖之後仍未關閉**。'
        '**🚫 但這是推論，不是實證**——本室未再往下驗。'),
    'notMyCallToFix': (
        '📮 這是產品程式：**要讓掃除容忍 PermissionError（重試／略過），'
        '還是視為測試在 Windows 上的脆弱**，是裁定，🚫 不是本室的判斷。'
        '⚠️ 而它不是純測試問題：`sweep_orphans` 是產品的對外入口，'
        '🚨 產線上同樣可能在別的寫入者尚未收手時撞上這個例外。'),
}


def run_once():
    result = subprocess.run(
        [sys.executable, '-X', 'utf8', '-m', 'pytest', '-q', '-rf',
         '--color=no', '-p', 'no:cacheprovider'],
        cwd=str(PYTEST_DIR), capture_output=True, text=True,
        encoding='utf-8', errors='ignore')
    text = ANSI.sub('', result.stdout or '')
    summary = [l.strip() for l in text.splitlines()
               if 'passed' in l or 'failed' in l]
    failed = [l.strip() for l in text.splitlines()
              if l.strip().startswith('FAILED')]
    passed = re.search(r'(\d+) passed', summary[-1] if summary else '')
    # 🚨 第 659 輪：⚠️ 有名字仍不夠——**四個斷言都在同一段**
    # （`_verify_committed_artifacts`／`errors == []`／`status`／殘留鎖檔），
    # 🚫 不知道是哪一個失敗就查不出成因。✅ 故連失敗段落一起存。
    traceback_lines = []
    if failed:
        lines = text.splitlines()
        start = next((i for i, l in enumerate(lines)
                      if 'FAILURES' in l and l.strip().startswith('=')), None)
        if start is not None:
            traceback_lines = [l.rstrip() for l in lines[start:start + 60]
                               if l.strip()]
    return {
        'summary': summary[-1] if summary else '（無摘要行）',
        'passed': int(passed.group(1)) if passed else None,
        'failedTests': failed,
        'traceback': traceback_lines,
        'returncode': result.returncode,
    }


def main():
    previous = {}
    if OUT.is_file():
        try:
            previous = json.loads(OUT.read_text(encoding='utf-8'))
        except json.JSONDecodeError:
            previous = {}
    history = list(previous.get('history') or [])

    fresh = [run_once() for _ in range(RUNS_PER_INVOCATION)]
    history.extend(fresh)

    total = SEED['observedRuns'] + len(history)
    failures = SEED['observedFailures'] + sum(
        1 for r in history if r['passed'] != 840)
    named = sorted({name for r in history for name in r['failedTests']})

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('本次真的跑了測試（必觸發之正對照）',
          all(r['passed'] is not None for r in fresh),
          '🚨 本次 %d 回合的 passed 數：%s；⚠️ 若讀不到，本紀錄就是空的'
          % (len(fresh), [r['passed'] for r in fresh]))
    probe('去色之後抓得到 FAILED 行（必觸發之反向）',
          ANSI.sub('', '\x1b[31mFAILED x\x1b[0m').startswith('FAILED'),
          '🚨 以帶 ANSI 的字串試；⚠️ **第一批追獵就是敗在這裡**——'
          '紅了卻沒留下測試名')
    # 🚨 這一道是狀態：⚠️ 它會一直紅，直到那個名字被抓到為止。
    # 🚨 這道探針的說明原本只為「還沒抓到」寫，抓到之後仍印著
    # 「測試名仍未抓到」而後面接著名字——⚠️ **自相矛盾的一行**。
    # ✅ 兩種情況分開寫。
    probe('那個間歇性失敗的測試名已經抓到',
          bool(named),
          ('✅ **已抓到**：%s（累計 %d 回合、紅 %d 次，約 %.0f%%）'
           % (named, total, failures, 100 * failures / max(1, total)))
          if named else
          ('🚨 至今累計 %d 回合、紅 %d 次（約 %.0f%%），'
           '而**測試名仍未抓到**；⚠️ 本支每次只跑 %d 回合並累積'
           % (total, failures, 100 * failures / max(1, total),
              RUNS_PER_INVOCATION)))

    doc = {
        'schemaVersion': 1,
        'documentType': 'flake-watch-log',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'isALogNotAMeasurement': (
            '⚠️ 本檔是**紀錄**，內容本來就會隨每次執行增長——'
            '🚫 拿它去比對 auditHash 沒有意義（第 648 輪那支掃描應略過它）。'),
        'seed': SEED,
        'hypothesesTested': HYPOTHESES,
        'diagnosis': DIAGNOSIS,
        'whereTheTriggerIsNot': (
            '✅ 第 660 輪：名字有了之後直接對**那一條**下手——'
            '單獨跑 **260 回合**全綠、19 個負載行程下再跑 **150 回合**全綠。'
            '⚠️ 而整套約 49 回合就紅 2 次。'
            '**🚨 故觸發條件在「完整套件的情境」裡，🚫 不是時序壓力本身。**'
            '⚠️ 那條測試會 patch `_write_committed_manifest`、改 '
            '`AHIG_PRIVATE_ROOT`、開兩條執行緒；'
            '🚫 而本室**不從機制推論成因**——等 traceback 落地。'),
        'localisation': (
            '✅ 第 659 輪：閘門第 5 次紅時，第 658 輪新加的 traceback 擷取'
            '**第一次實戰就抓到了**——內容為 `publish()`／`sweep()`／'
            '`staged.wait(timeout=30)`，即 test_fulltext.py 裡'
            '「掃除者與發布者並行時不得毀掉已提交證據」那一族。'
            '🚨 **而確切的斷言仍未知：本室又把閘門輸出截斷了（第三次）。**'
            '⚠️ 另：單獨跑 test_fulltext.py 25 回合全綠（每次 1 秒、40 條），'
            '**故它需要完整套件的情境**；本輪再跑 10 次整套亦全綠。'),
        'extraRunsOutsideThisLog': (
            '⚠️ 另有 3 回合（加壓）＋10 回合（固定種子）＋60 回合'
            '（單獨跑並行測試）全綠，🚫 未計入下方累計——'
            '✅ 因為它們跑的條件與本紀錄不同。'),
        'runsThisInvocation': len(fresh),
        'cumulativeRuns': total,
        'cumulativeFailures': failures,
        'observedRate': round(failures / max(1, total), 4),
        'failedTestNames': named,
        'history': history,
        'whyItMatters': (
            '⚠️ 閘門紅過四次，其中三次沒重現、也沒留下名字。'
            '✅ 本輪證明它**是真的**（20 次裡重現 1 次）；'
            '🚨 但只要名字沒抓到，就無從判斷是哪一條測試、'
            '**也無從判斷它是不是與負載有關**。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n656 間歇性失敗守望 ===')
    for index, row in enumerate(fresh, 1):
        print('   本次第 %d 回合：%s%s'
              % (index, row['summary'],
                 ('｜🚨 ' + '；'.join(row['failedTests']))
                 if row['failedTests'] else ''))
    print('   累計 %d 回合｜紅 %d 次｜約 %.0f%%'
          % (total, failures, 100 * failures / max(1, total)))
    print('   已抓到的測試名：%s' % (named or '（尚無）'))
    print('   ✅ 診斷：%s（%s）' % (DIAGNOSIS['failingAssertion'],
                                    DIAGNOSIS['location']))
    print('   ✅ 便宜重現：%s' % DIAGNOSIS['cheapRepro'])
    print('   已否證的假設：')
    for h in HYPOTHESES:
        print('      🚫 %s → %s' % (h['hypothesis'], h['result']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
