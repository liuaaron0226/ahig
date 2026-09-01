# -*- coding: utf-8 -*-
"""**那些有判定、卻沒人看得到的舊檢查，今天說什麼。**（第 653 輪）

## 🚨 第 652 輪查明：124 支憑證只印到標準輸出，不留 JSON

⚠️ 其中 **19 支看起來是「檢查」**（帶反向對照／必觸發／控制探針）。
🚨 而 `n141` 已示範：**其中至少有一支今天完全健康、全清、反向對照會亮——
而沒有任何人知道。**

> **⚠️ 一個沒有人讀的檢查，與一個不存在的檢查，效果完全一樣。**

## ✅ 本支做什麼

把那些**真的是檢查**的（🚫 排除 7 支報告產生器與 1 支儲存格產生器）
在**假的 repo 根**裡跑一次，把**結束碼與最後幾行判定**記下來。

⚠️ 而本支自己**留 JSON**——🚨 否則它就是它所稽核的那個毛病的第 20 個案例。

## 🚫 本支不改任何文件、不送外部請求、不改任何產品程式
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
OUT = S / 'n653_invisible_checks.json'

# ⚠️ 第 652 輪掃出的 19 支裡，扣掉會**產生文件**的那些——
# 🚨 報告產生器不是檢查，把它們算進來會讓「檢查有幾支」膨脹。
GENERATORS = {
    'n154_cell_producer.py', 'n157_section_c_report.py',
    'n159_section_g_report.py', 'n160_section_f_report.py',
    'n161_section_d_report.py', 'n163_section_a_report.py',
    'n164_section_b_report.py', 'n165_section_e_report.py',
}
CHECKS = [
    'n85_population_freeze.py',
    'n116_anchor_rules.py',
    'n116_obligation_crosscheck.py',
    'n131_cross_consistency.py',
    'n141_literal_numbers.py',
    'n153_wording_audit_check.py',
    'n158_report_lint.py',
    'n166_report_cell_coverage.py',
    'n172_root_population.py',
    'n174_generator_literals.py',
    'n179_p1_contract_state.py',
]

TIMEOUT = 90


def stage_fake_root():
    """假的 repo 根。

    🚨 前幾版是**挑目錄**複製（ahig/ahig、calibration、schema、docs），
    ⚠️ 於是漏掉 `ahig/domains`，`n179_p1_contract_state` 因此判紅——
    **而那個紅是本室的假根缺東西造成的，不是那支檢查的發現。**
    ✅ 這已經是第三次「假根不完整 ⇒ 假的失敗」，
    🚫 故不再補單一目錄——**整個 `ahig/` 與 `docs/` 一起複製**（約 9 MB，可接受）。
    """
    root = Path(tempfile.mkdtemp(prefix='ahig-invisible-'))
    shutil.copytree(S, root / '.scratch')
    for relative in ('ahig', 'docs'):
        source = REPO / relative
        if source.is_dir():
            shutil.copytree(source, root / relative)
    if (REPO / 'COORDINATION.md').is_file():
        shutil.copy2(REPO / 'COORDINATION.md', root / 'COORDINATION.md')
    return root


def repo_dirty():
    result = subprocess.run(['git', 'status', '--porcelain'], cwd=str(REPO),
                            capture_output=True, text=True,
                            encoding='utf-8', errors='ignore')
    return sorted(line for line in (result.stdout or '').split('\n')
                  if line.strip())


def main():
    workdir = stage_fake_root()
    before = repo_dirty()
    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(
        [str(workdir / 'ahig'), env.get('PYTHONPATH', '')])
    env['PYTHONIOENCODING'] = 'utf-8'
    env['AHIG_PRIVATE_ROOT'] = str(ROOT)

    rows = []
    for name in CHECKS:
        script = workdir / '.scratch' / name
        if not script.is_file():
            rows.append({'check': name, 'status': '🚨 檔案不在', 'tail': []})
            continue
        try:
            result = subprocess.run(
                [sys.executable, '-X', 'utf8', str(script)],
                cwd=str(workdir), capture_output=True, text=True,
                encoding='utf-8', errors='ignore', env=env, timeout=TIMEOUT)
            code = result.returncode
            tail = [line.strip() for line
                    in (result.stdout or '').strip().split('\n')[-3:]
                    if line.strip()]
            stderr_tail = ((result.stderr or '').strip().split('\n')
                           or [''])[-1]
        except subprocess.TimeoutExpired:
            code, tail, stderr_tail = None, [], 'timeout>%ds' % TIMEOUT
        if code == 0:
            status = '✅ 通過'
        elif code == 1:
            status = '🚨 判定為紅'
        else:
            status = '🚨 跑不起來'
        rows.append({'check': name, 'exitCode': code, 'status': status,
                     'tail': tail,
                     'error': stderr_tail[:120] if status.endswith('跑不起來')
                     else ''})

    after = repo_dirty()
    shutil.rmtree(workdir, ignore_errors=True)

    passed = [r for r in rows if r['status'] == '✅ 通過']
    red = [r for r in rows if r['status'] == '🚨 判定為紅']
    broken = [r for r in rows if r['status'].endswith('跑不起來')
              or r['status'] == '🚨 檔案不在']

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('每一支都真的被執行到（必觸發之正對照）',
          all(r.get('exitCode') is not None or r['status'].endswith('跑不起來')
              for r in rows) and len(rows) == len(CHECKS),
          '🚨 實跑 %d／%d；⚠️ 少一支就代表本支的總表不完整'
          % (len(rows), len(CHECKS)))
    probe('整趟跑完 repo 一個檔都沒被改動（必觸發之反向）',
          after == before,
          '🚨 前後差異：%s；⚠️ 這些檢查裡有會寫檔的，'
          '**第 648 輪的損害正是那樣造成的**'
          % sorted(set(after) ^ set(before)))
    probe('至少有一支給出明確判定（必觸發之正對照）',
          bool(passed or red),
          '🚨 通過 %d／判紅 %d；⚠️ 若全部都跑不起來，本支等於什麼也沒問到'
          % (len(passed), len(red)))
    # 🚨 這兩道是現況。
    probe('沒有檢查今天是紅的',
          not red,
          '🚨 判定為紅的 %d 支：%s'
          % (len(red), [(r['check'], r['tail'][-1] if r['tail'] else '')
                        for r in red]))
    probe('沒有檢查今天跑不起來',
          not broken,
          '🚨 跑不起來的 %d 支：%s'
          % (len(broken), [(r['check'], r.get('error', '')) for r in broken]))

    doc = {
        'schemaVersion': 1,
        'documentType': 'invisible-checks-status',
        'notAGate': '🚫 不入輪次閘門（n+181 三）',
        'why': (
            '⚠️ 第 652 輪查明 124 支憑證只印到標準輸出、不留 JSON，'
            '🚨 其中 19 支看起來是檢查。'
            '**⚠️ 一個沒有人讀的檢查，與一個不存在的檢查，效果完全一樣。**'),
        'excludedGenerators': sorted(GENERATORS),
        'checksRun': len(rows),
        'passed': len(passed),
        'red': len(red),
        'broken': len(broken),
        'rows': rows,
        'selfNote': (
            '✅ 本支自己**留 JSON**——🚨 否則它就是它所稽核的那個毛病的第 20 個案例。'),
        'whatThisCannotSay': (
            '🚫 「今天通過」不等於「它問對了問題」——⚠️ 本支只轉述判定，'
            '🚨 不重新審查每一支檢查的設計。'),
        'privateRoot': PROV,
        'controlProbes': probes,
    }
    doc['auditHash'] = content_hash(doc)
    OUT.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + '\n',
                   encoding='utf-8')

    print('=== n653 看不見的檢查，今天說什麼 ===')
    print('   跑了 %d 支｜✅ 通過 %d｜🚨 判紅 %d｜🚨 跑不起來 %d'
          % (len(rows), len(passed), len(red), len(broken)))
    for row in rows:
        print('   %-34s %s' % (row['check'], row['status']))
        for line in row['tail'][-2:]:
            print('        %s' % line[:150])
        if row.get('error'):
            print('        ⚠️ %s' % row['error'])
    print('   控制探針：')
    for p in probes:
        print('     %s %s' % ('✅' if p['passed'] else '🚨', p['probe']))
        print('        %s' % p['detail'])
    print('   → %s' % OUT.name)
    return 0 if all(p['passed'] for p in probes) else 1


if __name__ == '__main__':
    raise SystemExit(main())
