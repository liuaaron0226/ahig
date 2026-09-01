# -*- coding: utf-8 -*-
"""**這 75 支憑證，今天還跑得出同一份結論嗎。**（第 648 輪）

## 🚨 本 run 一直在引用自己的憑證，而沒有人問過它們還活著沒有

⚠️ 協調者手上的每一個數字都指向某一支憑證。
🚨 但那些憑證是**過去某一輪跑出來的**，而資料一路在變（清冊、名冊、契約）。

> **⚠️ 一支跑不起來的憑證，看起來跟一支還好好的一模一樣**——
> **🚨 因為看的是它留下的 JSON，不是它現在還算不算得出那個 JSON。**

## 🚨 本支的前兩版都錯了，而第二版造成了實際損害——先記在這裡

| 版本 | 作法 | 後果 |
|---|---|---|
| 第一版 | `cwd` ＝ `.scratch` 副本 | 🚨 用 `.scratch/xxx.json` 相對路徑**讀**的憑證全部找不到檔，**87 支被誤判成「跑不起來」** |
| 第二版 | `cwd` ＝ repo 根 | **🚨 用相對路徑寫的憑證寫進了真正的 repo**：26 份憑證 JSON、**產品程式 `statistical_termination.py`、10 份 docs 全被改動**，測試從 840 掉到 839＋1 失敗 |

> **🚨 而本室當時在憑證裡寫著「repo 裡的憑證一個字都沒動」——那句話是假的。**
> ✅ 損害已用 `git checkout` 全部還原，測試回到 **840 passed**。

## ✅ 第三版：搭一個**假的 repo 根**，讓寫入無處可去

暫存目錄裡放 `.scratch/`、`ahig/`、`docs/` 的副本，`cwd` 指向那個假根。
⚠️ 於是**讀**得到（相對路徑解析得到副本），**🚨 而寫也只寫得進副本**。

比對三件事：**跑不跑得起來｜`auditHash` 還一不一樣｜哪些欄位變了**。

## ⚠️ 「雜湊不同」不等於「壞掉」

🚨 有些憑證本來就會隨資料變（例如對帳表）；
⚠️ 有些帶著時間戳或隨機成分。**✅ 故本支只分類，🚫 不判對錯。**

## 🚫 本支不改任何憑證、不送外部請求、不改任何產品程式
"""
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
OUT = S / 'n648_artefact_reproducibility.json'

# ⚠️ 本支自己不重跑自己（會遞迴），🚫 也不跑閘門與非憑證工具。
SKIP = {'n648_artefact_reproducibility.py', 'round_gate.py',
        'private_root.py', 'n629_probe_mutation_test.py',
        'n631_probe_shape_scanner.py'}

TIMEOUT = 240

# 🚨 「跑不起來」又把兩種不同的東西混成一種——⚠️ 本 run 反覆抓到的同一族。
# ✅ 憑證**按設計拒跑**（缺信箱不送請求、外部服務沒開、無待查者）
#    與**真的壞了**必須分開；🚫 前者是紀律生效，不是缺陷。
BY_DESIGN = (
    'AHIG_CONTACT_EMAIL 未設定',
    'GROBID 未在',
    '無待查者',
    '本輪無事可做',
)


def stage_fake_root():
    """搭一個假的 repo 根：🚨 讓任何寫入都只落在副本裡。"""
    root = Path(tempfile.mkdtemp(prefix='ahig-repro-'))
    shutil.copytree(S, root / '.scratch')
    for relative in ('ahig/ahig', 'ahig/calibration', 'ahig/schema', 'docs'):
        source = REPO / relative
        if source.is_dir():
            shutil.copytree(source, root / relative)
    if (REPO / 'COORDINATION.md').is_file():
        shutil.copy2(REPO / 'COORDINATION.md', root / 'COORDINATION.md')
    return root


OUT_LINE = re.compile(
    r"OUT\s*=\s*Path\(__file__\)\.resolve\(\)\.parent\s*/\s*'([^']+)'")


def output_name(script):
    """該憑證實際寫到哪個檔名。

    🚨 本支第一版假設「JSON 與 .py 同名」——⚠️ 而有 4 支寫的是別的名字
    （例如 n611_tables_missing_from_payload.py → n611_tables_missing.json），
    **於是它們被判成「沒有 JSON」而遭略過**，第 650 輪的 126／128 因此是錯的。
    ✅ 改成從原始碼讀 `OUT =` 那一行，🚫 不猜。
    """
    try:
        match = OUT_LINE.search(script.read_text(encoding='utf-8'))
    except (UnicodeDecodeError, OSError):
        match = None
    return match.group(1) if match else script.stem + '.json'


def repo_dirty():
    """repo 目前有哪些被改動的檔案——🚨 用來證明本支沒有動到它們。"""
    result = subprocess.run(['git', 'status', '--porcelain'], cwd=str(REPO),
                            capture_output=True, text=True,
                            encoding='utf-8', errors='ignore')
    return sorted(line for line in (result.stdout or '').split('\n')
                  if line.strip())


def main():
    workdir = stage_fake_root()
    stage = workdir / '.scratch'
    before_dirty = repo_dirty()

    env = dict(os.environ)
    env['PYTHONPATH'] = os.pathsep.join(
        [str(workdir / 'ahig'), env.get('PYTHONPATH', '')])
    env['PYTHONIOENCODING'] = 'utf-8'
    env['AHIG_PRIVATE_ROOT'] = str(ROOT)

    # 🚨 Canary：⚠️ 先單獨跑**一支已知會寫進 repo 的憑證**（重產 docs 的那種），
    # 然後檢查 repo 有沒有被動。**🚫 不通過就不准跑其餘**——
    # ✅ 因為第 648 輪那次損害，正是「以為擋得住」造成的。
    CANARY = 'n155_owner_briefing.py'
    canary_ran = canary_safe = None
    if (stage / CANARY).is_file():
        subprocess.run([sys.executable, '-X', 'utf8', str(stage / CANARY)],
                       cwd=str(workdir), capture_output=True, text=True,
                       encoding='utf-8', errors='ignore', env=env,
                       timeout=TIMEOUT)
        canary_ran = True
        canary_safe = repo_dirty() == before_dirty
        if not canary_safe:
            shutil.rmtree(workdir, ignore_errors=True)
            raise SystemExit(
                '🚨 Canary 失敗：跑一支會寫檔的憑證之後 repo 被改動了——'
                '🚫 本支中止，不跑其餘。差異：%s'
                % sorted(set(repo_dirty()) - set(before_dirty)))

    # ⚠️ 沒有已回報 JSON 的憑證**無從比較**——🚫 跑它們不會產生任何結論，
    # 只會拉長時間。✅ 故本支只跑「有 JSON 可對」的那些，
    # 並把略過的數目照實記下來（🚨 不是假裝它們不存在）。
    all_scripts = [p for p in sorted(S.glob('n*.py')) if p.name not in SKIP]
    out_names = {p.name: output_name(p) for p in all_scripts}
    scripts = [p for p in all_scripts if (S / out_names[p.name]).is_file()]
    skipped_no_json = [p.name for p in all_scripts if p not in scripts]
    rows = []
    for script in scripts:
        recorded_path = S / out_names[script.name]
        recorded = None
        if recorded_path.is_file():
            try:
                recorded = json.loads(
                    recorded_path.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                recorded = None
        target = stage / script.name
        fresh_path = stage / out_names[script.name]
        if fresh_path.exists():
            fresh_path.unlink()
        try:
            result = subprocess.run(
                # 🚨 第一版 cwd 在副本裡 ⇒ 相對路徑**讀**不到，87 支誤判；
                # 🚨 第二版 cwd 在 repo 根 ⇒ 相對路徑**寫**進了真正的 repo，
                #    改動了產品程式與 10 份 docs（已還原）。
                # ✅ 第三版：cwd 指向**假的 repo 根**——讀得到、而寫也只寫得進副本。
                [sys.executable, '-X', 'utf8', str(target)],
                cwd=str(workdir),
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

        refused = any(marker in (error or '') for marker in BY_DESIGN)
        if recorded is None:
            verdict = '（沒有已回報的 JSON）'
        elif refused and fresh is None:
            verdict = '✅ 按設計拒跑（前置條件不在）'
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

    after_dirty = repo_dirty()
    shutil.rmtree(workdir, ignore_errors=True)

    same = [r for r in rows if r['verdict'] == '✅ 一模一樣']
    drifted = [r for r in rows if r['verdict'] == '⚠️ 跑得起來但結果變了']
    broken = [r for r in rows if r['verdict'] == '🚨 跑不起來']
    refused_rows = [r for r in rows
                    if r['verdict'].startswith('✅ 按設計拒跑')]
    no_json = [r for r in rows if r['verdict'].startswith('（')]

    probes = []

    def probe(name, ok, detail):
        probes.append({'probe': name, 'passed': bool(ok), 'detail': detail})

    probe('真的跑了夠多支（必觸發之正對照）',
          len(rows) >= 50,
          '🚨 實跑 %d 支；⚠️ 太少的話「全部還活著」沒有份量' % len(rows))
    probe('🚨 Canary：跑一支會寫檔的憑證後 repo 仍未被動（必觸發之反向）',
          canary_safe is True,
          '🚨 canary=%s、safe=%s；⚠️ **第 648 輪的損害正是「以為擋得住」造成的**，'
          '故本支先跑一支會重產 docs 的憑證再檢查 git status'
          % (CANARY, canary_safe))
    probe('整趟跑完 repo 一個檔都沒被改動（必觸發之反向）',
          after_dirty == before_dirty,
          '🚨 前後差異：%s；⚠️ 若有差異，本支的「安全」就是假的'
          % sorted(set(after_dirty) ^ set(before_dirty)))
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
        'method': (
            '✅ 在暫存目錄搭一個**假的 repo 根**'
            '（`.scratch`／`ahig`／`docs` 副本），cwd 指向那裡：'
            '⚠️ 相對路徑讀得到，**🚨 而寫也只寫得進副本**。'),
        'twoBrokenVersionsBefore': (
            '🚨 第一版 cwd 在 .scratch 副本裡 ⇒ 相對路徑讀不到，'
            '**87 支被誤判成「跑不起來」**。'
            '**🚨 第二版 cwd 在 repo 根 ⇒ 相對路徑的寫入落進了真正的 repo**：'
            '26 份憑證 JSON、產品程式 `statistical_termination.py`、'
            '10 份 docs 全被改動，測試從 840 掉到 839＋1 失敗。'
            '⚠️ 而本室當時在憑證裡寫著「repo 裡的憑證一個字都沒動」——**那是假的**。'
            '✅ 已用 `git checkout` 全部還原，測試回到 840 passed。'),
        'canary': {'artefact': CANARY, 'ran': canary_ran,
                   'repoUntouched': canary_safe},
        'repoUntouchedAfterSweep': after_dirty == before_dirty,
        'scanned': len(rows),
        'identical': len(same),
        'drifted': len(drifted),
        'broken': len(broken),
        'skippedBecauseNoRecordedJson': len(skipped_no_json),
        'scopeNote': (
            '⚠️ 只跑「有已回報 JSON 可對」的憑證（%d 支）；'
            '🚫 另 %d 支沒有 JSON，無從比較故未執行——'
            '✅ 照實記下，🚫 不假裝它們不存在。'
            % (len(scripts), len(skipped_no_json))),
        'refusedByDesign': len(refused_rows),
        'refusedDetail': [(r['artefact'], r['error']) for r in refused_rows],
        'whyRefusedIsNotBroken': (
            '✅ 憑證因為「缺聯絡信箱不送請求」「外部服務沒開」「無待查者」而停下，'
            '**是紀律生效，🚫 不是缺陷**。'
            '🚨 本支第一版把它們和真的壞掉混成同一個「跑不起來」——'
            '⚠️ 又是本 run 反覆抓到的那一族：**一種失敗長得像另一種**。'),
        'withoutRecordedJson': len(skipped_no_json),
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
    print('   掃過 %d 支｜✅ 一模一樣 %d｜⚠️ 結果變了 %d｜🚨 真的跑不起來 %d｜'
          '✅ 按設計拒跑 %d｜（無已回報 JSON）%d'
          % (len(rows), len(same), len(drifted), len(broken),
             len(refused_rows), len(no_json)))
    for row in refused_rows:
        print('      ✅ 拒跑 %-38s %s' % (row['artefact'], row['error']))
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
