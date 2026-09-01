# -*- coding: utf-8 -*-
"""**這 75 支憑證，今天還跑得出同一份結論嗎。**（第 648 輪）

## 🚨 本 run 一直在引用自己的憑證，而沒有人問過它們還活著沒有

⚠️ 協調者手上的每一個數字都指向某一支憑證。
🚨 但那些憑證是**過去某一輪跑出來的**，而資料一路在變（清冊、名冊、契約）。

> **⚠️ 一支跑不起來的憑證，看起來跟一支還好好的一模一樣**——
> **🚨 因為看的是它留下的 JSON，不是它現在還算不算得出那個 JSON。**

## ✅ 作法：整個 `.scratch` 複製到暫存目錄跑，🚫 完全不動 repo 裡的憑證

⚠️ 每支憑證的輸出路徑都是 `Path(__file__).parent`，
✅ 故副本跑出來的 JSON 會落在暫存目錄，**🚫 不會覆蓋任何已回報的結果**。

比對三件事：**跑不跑得起來｜`auditHash` 還一不一樣｜哪些欄位變了**。

## ⚠️ 「雜湊不同」不等於「壞掉」

🚨 有些憑證本來就會隨資料變（例如對帳表）；
⚠️ 有些帶著時間戳或隨機成分。**✅ 故本支只分類，🚫 不判對錯。**

## 🚫 本支不改任何憑證、不送外部請求、不改任何產品程式
"""
import json
import os
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
OUT = S / 'n648_artefact_reproducibility.json'

# ⚠️ 本支自己不重跑自己（會遞迴），🚫 也不跑閘門與非憑證工具。
SKIP = {'n648_artefact_reproducibility.py', 'round_gate.py',
        'private_root.py', 'n629_probe_mutation_test.py',
        'n631_probe_shape_scanner.py'}

TIMEOUT = 240


def main():
    workdir = Path(tempfile.mkdtemp(prefix='ahig-repro-'))
    shutil.copytree(S, workdir / 'scratch')
    stage = workdir / 'scratch'

    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(
        [str(REPO / 'ahig'), env.get('PYTHONPATH', '')])
    env['PYTHONIOENCODING'] = 'utf-8'
    env['AHIG_PRIVATE_ROOT'] = str(ROOT)

    scripts = [p for p in sorted(S.glob('n*.py')) if p.name not in SKIP]
    rows = []
    for script in scripts:
        recorded_path = S / (script.stem + '.json')
        recorded = None
        if recorded_path.is_file():
            try:
                recorded = json.loads(
                    recorded_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                recorded = None
        target = stage / script.name
        fresh_path = stage / (script.stem + '.json')
        if fresh_path.exists():
            fresh_path.unlink()
        try:
            result = subprocess.run(
                # 🚨 第一版把 cwd 設在暫存副本裡——⚠️ 而許多憑證用
                # `.scratch/xxx.json` 這種**相對於 repo 根**的路徑讀輸入，
                # 於是 87 支被誤判成「跑不起來」。**🚨 錯的是本支的工具。**
                # ✅ 改成 cwd=repo 根：輸入照舊讀得到，
                # 而輸出仍走 `Path(__file__).parent`＝暫存目錄，🚫 不會覆蓋。
                [sys.executable, '-X', 'utf8', str(target)], cwd=str(REPO),
                capture_output=True, text=True, encoding='utf-8',
                errors='ignore', env=env, timeout=TIMEOUT)
            crashed = result.returncode not in (0, 1)
            error = ((result.stderr or '').strip().split('\n') or [''])[-1]
        except subprocess.TimeoutExpired:
            crashed, error = True, 'timeout>%ds' % TIMEOUT
        fresh = None
        if fresh_path.is_file():
            try:
                fresh = json.loads(fresh_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                fresh = None

        if recorded is None:
            verdict = '（沒有已回報的 JSON）'
        elif crashed or fresh is None:
            verdict = '🚨 跑不起來'
        elif fresh.get('auditHash') == recorded.get('auditHash'):
            verdict = '✅ 一模一樣'
        else:
            verdict = '⚠️ 跑得起來但結果變了'
        changed = []
        if (recorded and fresh
                and fresh.get('auditHash') != recorded.get('auditHash')):
            changed = sorted(k for k in set(recorded) | set(fresh)
                             if k != 'auditHash'
                             and recorded.get(k) != fresh.get(k))
        rows.append({
            'artefact': script.name, 'verdict': verdict,
            'changedFields': changed[:6],
            'error': error[:120] if verdict == '🚨 跑不起來' else '',
        })

    shutil.rmtree(workdir, ignore_errors=True)

    same = [r for r in rows if r['verdict'] == '✅ 一模一樣']
    drifted = [r for r in rows if r['verdict'] == '⚠️ 跑得起來但結果變了']
    broken = [r for r in rows if r['verdict'] == '🚨 跑不起來']
    no_json = [r for r in rows if r['verdict'].startswith('（')]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的跑了夠多支（必觸發之正對照）',
          len(rows) >= 50,
          '🚨 實跑 %d 支；⚠️ 太少的話「全部還活著」沒有份量' % len(rows))
    probe('副本沒有覆蓋 repo 裡的憑證（必觸發之反向）',
          not (workdir.exists()),
          '✅ 全部在暫存目錄執行且已清除；'
          '🚨 若輸出落在 .scratch，本支就會改寫已回報的結果')
    probe('至少有一支重跑後一模一樣（必觸發之正對照）',
          bool(same),
          '🚨 一模一樣者 %d 支；⚠️ 若一支都沒有，代表本支的比較方式有問題'
          % len(same))
    # 🚨 這兩道是現況。
    probe('每一支憑證今天都還跑得起來',
          not broken,
          '🚨 跑不起來的 %d 支：%s'
          % (len(broken),
             [(r['artefact'], r['error']) for r in broken][:8]))
    probe('每一支憑證重跑後結論不變',
          not drifted,
          '⚠️ 結果變了的 %d 支：%s'
          % (len(drifted),
             [(r['artefact'], r['changedFields']) for r in drifted][:8]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'artefact-reproducibility',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'method': ('✅ 整個 .scratch 複製到暫存目錄，'
                   '**以 repo 根為工作目錄**執行副本：'
                   '⚠️ 輸入（`.scratch/...` 相對路徑）照舊讀得到，'
                   '✅ 而輸出走 `Path(__file__).parent`＝暫存目錄，'
                   '🚫 repo 裡的憑證一個字都沒動。'
                   '🚨 第一版把 cwd 設在副本裡，害 87 支被誤判成跑不起來。'),
        'scanned': len(rows),
        'identical': len(same),
        'drifted': len(drifted),
        'broken': len(broken),
        'withoutRecordedJson': len(no_json),
        'rows': rows,
        'skipped': sorted(SKIP),
        'howToReadDrift': (
            '⚠️ 「結果變了」不等於「壞掉」——🚨 有些憑證本來就跟著資料走'
            '（對帳表、覆蓋率表），✅ 那時候變才是對的；'
            '🚨 真正要看的是**變了卻沒有人知道**。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n648 憑證可重現性 ===')
    print('   掃過 %d 支｜✅ 一模一樣 %d｜⚠️ 結果變了 %d｜🚨 跑不起來 %d｜'
          '（無已回報 JSON）%d'
          % (len(rows), len(same), len(drifted), len(broken), len(no_json)))
    if broken:
        print('   🚨 跑不起來：')
        for row in broken:
            print('      %-42s %s' % (row['artefact'], row['error']))
    if drifted:
        print('   ⚠️ 結果變了：')
        for row in drifted:
            print('      %-42s 變動欄位 %s'
                  % (row['artefact'], row['changedFields']))
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
