# -*- coding: utf-8 -*-
"""**協調者實際會讀的那個交接檔，38 輪之後還準嗎。**（第 542 輪）

## 🚨 為什麼要查

`.scratch/executor_cells.json` 是 `n154` 逐格讀入的檔，**⚠️ 也是本室唯一一個
協調者會直接消費的產物**。它自報 `isSnapshot: true`，並寫明
「**do not treat these as constants**」。

**🚨 而從第 503 輪產出至今，沒有人查過它有沒有漂。**
⚠️ 一個自稱快照的檔案，若沒有人比對過，它與一個自稱常數的檔案在使用上沒有差別。

## ✅ 做法：拿版控裡的那一份，對現在重跑出來的那一份

`git show HEAD:.scratch/executor_cells.json` ↔ 重跑後的檔案，**逐格比對**。
🚫 排除 `producedAt`／`producedAtRound`／`handoffHash` 三個必然會變的欄位——
⚠️ 但**它們必然會變這件事本身**也要說出來，否則讀的人會以為整份一模一樣。

## 🚫 本支不是機檢

n+181（三）已裁定停止加機檢。**⚠️ 本支不入輪次閘門。**
"""
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

TARGET = '.scratch/executor_cells.json'
OUT = Path(__file__).resolve().parent / 'n542_handoff_drift.json'
VOLATILE = ('producedAt', 'producedAtRound', 'handoffHash')


def main():
    try:
        raw = subprocess.run(['git', 'show', 'HEAD:' + TARGET], cwd=REPO,
                             capture_output=True, check=True).stdout
    except (subprocess.CalledProcessError, FileNotFoundError) as error:
        print('🚨 取不到版控裡的那一份：%s' % error, file=sys.stderr)
        sys.exit(2)

    committed = json.loads(raw.decode('utf-8'))
    current = json.loads((REPO / TARGET).read_text(encoding='utf-8'))

    top_changed = sorted(
        key for key in set(committed) | set(current)
        if key not in VOLATILE and key != 'cells'
        and committed.get(key) != current.get(key))
    cb, ca = committed.get('cells') or {}, current.get('cells') or {}
    cells_changed = sorted(name for name in set(cb) | set(ca)
                           if cb.get(name) != ca.get(name))
    volatile_changed = sorted(k for k in VOLATILE
                              if committed.get(k) != current.get(k))

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('18 格一格都沒漂', not cells_changed,
          '有變者：%s' % (cells_changed or '無'))
    probe('格數與分類未變',
          committed.get('cellCount') == current.get('cellCount')
          and committed.get('measured') == current.get('measured')
          and committed.get('bounded') == current.get('bounded'),
          '格數 %s→%s｜可量測 %s→%s｜可給界 %s→%s'
          % (committed.get('cellCount'), current.get('cellCount'),
             committed.get('measured'), current.get('measured'),
             committed.get('bounded'), current.get('bounded')))
    probe('其餘欄位未變', not top_changed, '有變者：%s' % (top_changed or '無'))
    # 🚨 必觸發：若連時戳都沒變，代表我根本沒有重跑，而「沒漂」會是假的。
    probe('時戳確實變了（必觸發）', 'producedAt' in volatile_changed,
          '🚨 時戳沒變代表比的是同一份檔案，「沒漂」就沒有意義；'
          '實際變動的必變欄位：%s' % volatile_changed)

    doc = {
        'schemaVersion': 1,
        'documentType': 'handoff-drift-check',
        'ruling': 'n+151(1)／n+160：executor_cells.json 是協調者 n154 逐格讀入的檔',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'comparedAgainst': 'git HEAD 版之 ' + TARGET,
        'committedRound': committed.get('producedAtRound'),
        'currentRound': current.get('producedAtRound'),
        'cellsChanged': cells_changed,
        'topLevelChanged': top_changed,
        'volatileChanged': volatile_changed,
        'roundFieldFix': (
            '🚨 重跑時發現 `ROUND` 是寫死的 503：`producedAt` 會更新而它不會，'
            '⚠️ 於是交付日重跑產出的檔會宣稱一個它不是在那時產出的輪次。'
            '✅ 已改為必須由呼叫端指明，未指明即 exit 2。'),
        'whatThisDoesNotProve': [
            '🚨 不證明那 18 格的**值本身**是對的——⚠️ 只證明它沒有變。',
            '🚨 不證明受阻的 3 格之阻礙仍然存在（那要看裁定，不看資料）。',
        ],
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n542 交接檔漂移查核 ===')
    print('   版控 round %s → 本次 round %s'
          % (committed.get('producedAtRound'), current.get('producedAtRound')))
    print('   18 格有變者：%s' % (cells_changed or '無'))
    print('   其餘欄位有變者：%s' % (top_changed or '無'))
    print('   必然會變者：%s' % volatile_changed)
    print('   控制探針：')
    for p in probes:
        print('     %s %s — %s' % ('✅' if p['passed'] else '🚨',
                                   p['probe'], p['detail']))
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
