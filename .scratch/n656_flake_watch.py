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
    return {
        'summary': summary[-1] if summary else '（無摘要行）',
        'passed': int(passed.group(1)) if passed else None,
        'failedTests': failed,
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
    probe('那個間歇性失敗的測試名已經抓到',
          bool(named),
          '🚨 至今累計 %d 回合、紅 %d 次（約 %.0f%%），'
          '而**測試名仍未抓到**：%s；'
          '⚠️ 本支每次只跑 %d 回合並累積——🚫 不再每輪重跑二十次'
          % (total, failures, 100 * failures / max(1, total),
             named or '（尚無）', RUNS_PER_INVOCATION))

    doc = {
        'schemaVersion': 1,
        'documentType': 'flake-watch-log',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'isALogNotAMeasurement': (
            '⚠️ 本檔是**紀錄**，內容本來就會隨每次執行增長——'
            '🚫 拿它去比對 auditHash 沒有意義（第 648 輪那支掃描應略過它）。'),
        'seed': SEED,
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
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
