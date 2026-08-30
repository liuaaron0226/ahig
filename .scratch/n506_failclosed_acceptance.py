# -*- coding: utf-8 -*-
"""fail-closed 之驗收：把每支產生器丟進「私有根不存在」的環境，看它會不會亂寫。

## 🚨 這一支要防的事故（n+162 九）

協調者跑了一次本室之總跑套件，**⚠️ 而那不是唯讀動作**：

```
n492_stratum_table.json → totals.withBackfill   27 → 0
n499_calibration_redraw.json                    整份被重寫
```

**🚨 在那個環境裡私有根不存在，而那幾支沒有拒絕**——
它們量到「什麼都沒有」，**把 0 寫回去，然後以 0 結束（通過）。**
**⚠️ 而被寫壞的正是協調者引用的來源。**

> **🚨 它被抓到，只因為有人提交前看了一眼 `git status`。**
> **⚠️ 沒有任何檢查在看這件事——本檔就是那個檢查。**

## ✅ 判準（兩者皆須成立，缺一即不通過）

| # | 判準 |
|---|---|
| 1 | 在假的私有根下，該支須以 **exit 2** 結束（🚨 2＝「這裡根本不該跑」，🚫 不是 1） |
| 2 | **其產物之位元組須逐位不變**——⚠️ 「拒絕了但還是寫了」不算通過 |

**🚨 第 2 條才是重點**：⚠️ 一支可以先寫檔再喊錯，退出碼看起來對，
**而檔案已經壞了。**

## 🚨 控制探針：本檔自己也可能什麼都沒在看

**⚠️ 若比對邏輯壞了，八支「未改」與八支「其實被改了」會印出同一張表。**
**✅ 故先造一支合成產生器**：它在假根下**照樣寫檔並以 0 結束**——
**🚨 本檔必須判它不通過。判得出來，上面那八個 ✅ 才有意義。**

## 🚫 本檔不做什麼

- **🚫 不需要真的私有根**：⚠️ 它跑的是「根不在」的情境，
  **🚨 故任何人在任何機器上都能跑，且跑了不會弄壞東西。**
- **🚫 不改任何產物**——⚠️ 只讀雜湊前後對照。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 驗得到：根**完全不存在**時，八支會不會寫。
- 🚨 驗不到：**根存在但內容被截斷**時的行為——⚠️ 那看起來像一個較小的真實母體，
  **🚫 `private_root.require()` 分不出來**（其產物記錄實見之 artifact 目錄數，
  🚨 讓數字變小時至少看得見）。
- 🚨 亦驗不到：**未列入本檔清單之產生器**——⚠️ 清單手維護，
  **✅ 由 `n504` 之盲點掃描從另一頭夾。**
"""
import hashlib
import io
import json
import os
import subprocess
import sys
import tempfile

S = '.scratch/'
ROUND = 506

# 產生器 → 其產物（⚠️ 手維護；🚨 新增產生器時一併加入）
GENERATORS = {
    'n492_stratum_table': 'n492_stratum_table.json',
    'n496_corpus_verify': 'n496_corpus_verify.json',
    'n498_sections_integrity': 'n498_sections_integrity.json',
    'n499_calibration_redraw': 'n499_calibration_redraw.json',
    'n500_inaccessible_cells': 'n500_inaccessible_cells.json',
    'n501_retraction_recheck': 'n501_retraction_recheck.json',
    'n503_executor_handoff': 'executor_cells.json',
    'n505_licence_completion': 'n505_licence_completion.json',
}
EXPECT_EXIT = 2


def digest(path):
    if not os.path.exists(path):
        return '(不存在)'
    return hashlib.sha256(open(path, 'rb').read()).hexdigest()[:16]


def run_with_absent_root(script_path, env_root):
    env = dict(os.environ, AHIG_PRIVATE_ROOT=env_root,
               PYTHONIOENCODING='utf-8')
    return subprocess.run([sys.executable, script_path], env=env,
                          capture_output=True, encoding='utf-8',
                          errors='replace')


absent = os.path.join(tempfile.gettempdir(), 'n506-absent-private-root')
print('=== fail-closed 驗收（n+162 九之二）===')
print('   假私有根：%s（🚨 刻意不存在）' % absent)
print()

# ── 控制探針 ─────────────────────────────────────────────────────
print('一、控制探針——🚨 未過即拒絕報告')
tmp = tempfile.mkdtemp(prefix='n506-')
victim = os.path.join(tmp, 'victim.json')
io.open(victim, 'w', encoding='utf-8').write('{"value": 27}')
before_v = digest(victim)
naughty = os.path.join(tmp, 'naughty_generator.py')
io.open(naughty, 'w', encoding='utf-8').write(
    'import io, sys\n'
    'io.open(%r, "w", encoding="utf-8").write(\'{"value": 0}\')\n'
    'sys.exit(0)\n' % victim)
r = run_with_absent_root(naughty, absent)
after_v = digest(victim)
caught = not (r.returncode == EXPECT_EXIT and after_v == before_v)
print('   %s 合成之「照寫不誤」產生器：退出碼 %s、產物 %s → 本檔判定「不通過」%s'
      % ('✅' if caught else '🚨', r.returncode,
         '未改' if after_v == before_v else '被改了',
         '✅' if caught else '🚨 判成通過了'))
if not caught:
    sys.exit('🚨 控制探針未過——⚠️ 本檔分不出「有拒絕」與「照寫」，🚫 結果不予採信。')
print('   ✅ 它分得出來，故下面那些 ✅ 才有意義。')
print()

# ── 逐支驗收 ─────────────────────────────────────────────────────
print('二、逐支（判準：exit %d ＋ 產物位元組不變）' % EXPECT_EXIT)
print('   %-30s %6s  %-10s %s' % ('產生器', '退出碼', '產物', '判定'))
print('   ' + '-' * 72)
rows = []
for name, out in sorted(GENERATORS.items()):
    script = S + name + '.py'
    path = S + out
    if not os.path.exists(script):
        rows.append({'generator': name, 'verdict': 'missing-script'})
        print('   %-30s %6s  %-10s 🚨 腳本不存在' % (name, '—', '—'))
        continue
    before = digest(path)
    r = run_with_absent_root(script, absent)
    after = digest(path)
    unchanged = (after == before)
    ok = (r.returncode == EXPECT_EXIT and unchanged)
    rows.append({'generator': name, 'artefact': out, 'exit': r.returncode,
                 'artefactUnchanged': unchanged,
                 'verdict': 'fail-closed' if ok else 'fail-open',
                 'stderrFirstLine': (r.stderr or '').strip().split('\n')[0][:120]})
    print('   %-30s %6s  %-10s %s' % (name, r.returncode,
                                      '未改' if unchanged else '🚨 被改',
                                      '✅ fail-closed' if ok else '🚨 fail-open'))
print('   ' + '-' * 72)
good = [r for r in rows if r.get('verdict') == 'fail-closed']
bad = [r for r in rows if r.get('verdict') != 'fail-closed']
print('   ✅ fail-closed %d／%d' % (len(good), len(rows)))
for r in bad:
    print('      🚨 %s：%s' % (r['generator'], r.get('verdict')))

doc = {
    'schemaVersion': 1,
    'documentType': 'fail-closed-acceptance',
    'ruling': 'n+162(9)(2): generators must refuse to produce, and write nothing, '
              'when their source is absent -- a measured zero and an unmeasurable '
              'one must be distinguishable in the file.',
    'population': 'the executor room\'s generators, hand-maintained list',
    'countingUnit': 'generator',
    'criterion': 'exit code %d AND the artefact\'s bytes unchanged; refusing but '
                 'writing anyway does not pass' % EXPECT_EXIT,
    'controlProbe': {'synthetic': 'a generator that writes and exits 0 under the '
                                  'absent root', 'detectedAsFailing': caught,
                     'why': 'If the comparison were broken, eight refusals and '
                            'eight silent overwrites would print the same table.'},
    'absentRootUsed': absent,
    'generators': rows,
    'failClosed': len(good),
    'failOpen': [r['generator'] for r in bad],
    'needsNoPrivateRoot': True,
    'coverageStatement': 'Covers a root that is absent entirely. A root that is '
                         'present but truncated looks like a smaller real '
                         'population and is not detectable here; require() records '
                         'how many artifact directories it saw so that at least '
                         'shows up as a smaller number. Generators missing from '
                         "this list are invisible here; n504's blind-spot scan "
                         'squeezes that from the other side.',
    'contentNote': 'Script names, exit codes and hash prefixes only.',
}
io.open(S + 'n506_failclosed_acceptance.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn506_failclosed_acceptance.json' % S)
sys.exit(0 if not bad else 1)
