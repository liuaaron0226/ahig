# -*- coding: utf-8 -*-
"""執行室常設檢查之總跑：**一道指令跑完，🚫 不靠記得哪幾支還在。**

## 🚨 為什麼要有這一支

上一輪查明的事，值得推廣：

> **🚨 產得出來 ≠ 交得出去**——值放在沒有人會讀的地方，等於沒產。

**⚠️ 同一個道理套在「檢查」上更嚴重**：
**🚨 一支沒有人會跑的檢查，與一支壞掉的檢查，在輸出上完全一樣——都是沒有輸出。**

本室至今累積了七支常設檢查，散在七個檔名裡。
**⚠️ 交付當日「既有機檢全綠」是盤點第 7 項的判準之一，而本室這一半從來沒有一道指令跑得完。**
**✅ 本檔即那道指令。**

## 🚫 網路預設不跑

`n501` 會對外送請求。**⚠️ 一個每次都打網路的總跑，會把 n+146（三）之節流紀律
變成一件每跑一次就重來的事。**
**✅ 故預設略過，需要時以 `--with-network` 明示開啟**——
**🚨 而略過者一律列名為 `skipped`，🚫 不得從表上消失**（消失會被讀成通過）。

## 🚨 控制探針：一個「總是說通過」的跑法，與真的全過長得一樣

**✅ 故本檔先跑兩個合成命令**：一個必然成功、一個必然失敗（`sys.exit(3)`），
**🚨 兩者之判定都必須如預期，否則拒絕報告任何結果。**

⚠️ 併記：**退出碼是唯一判準**。本檔**不解析各支的輸出**——
🚨 解析輸出就變成「讀別人印的表」，而那是另一種脆弱；
✅ 各支自己以非零碼表達失敗，這是本 run 一貫的約定。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 看得到：每支是否以 0 結束、各花多久。
- 🚨 看不到：**某支「跑完了但驗得不對」**——⚠️ 那要靠各支自己的控制探針，
  **🚫 本檔不替它們驗。**
- ⚠️ **本室漏寫的檢查**：清單是手維護的，🚨 而手維護的清單看不見自己漏了什麼。
  **✅ 故第三節掃出第 490 輪以後之三位數編號腳本，凡未列入清單者一律印出**，
  非檢查者須附排除理由；**🚨 無理由者即以非零碼失敗。**
  **🚫 但掃描只涵蓋該命名範圍**——⚠️ 更早的、或不照此命名者仍看不到，
  **故這是把盲點縮小，不是關掉。**
"""
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

S = '.scratch/'
ROUND = 528

# ⚠️ 清單手維護——🚨 故末行會逼人核對；新增常設檢查時請一併加進來。
CHECKS = [
    ('private_root', '私有根前置檢查之自測（🚨 來源不在即拒絕產出）', False),
    ('n506_failclosed_acceptance',
     '八支產生器在「根不存在」下是否 fail-closed（🚫 不需私有根）', False),
    ('round_gate', '每輪閘門：樣式來源、控制探針、n+48 兩道、n+54 三道、測試基線',
     False),
    ('fetch_guard', '對外抓取閘門之自測（🚫 不發真實請求）', False),
    ('n492_stratum_table', '層別筆數兩母體並列（🚨 兩欄分母不得互換）', False),
    ('n496_corpus_verify', '已取得 41 份之位元組與 manifest 對帳（唯讀）', False),
    ('n498_sections_integrity', '節切偏移是否指到它宣稱的那段文字', False),
    ('n499_calibration_redraw', '校準集之獨立重抽（種子／名單／drawHash）', False),
    ('n500_inaccessible_cells', '不可及 18 格之產出與清單漂移偵測', False),
    ('n507_blocked_cells_review',
     '四格受阻者之複查（🚨 一格已夾出上界）', False),
    ('n512_source_host_provenance',
     '在手 41 份之來源主機分類（🚫 唯讀、不記網址）', False),
    ('n514_hash_lineending_exposure',
     '行尾曝險逐份量測（🚫 唯讀，不改規則）', False),
    ('n515_conversion_drill',
     '行尾轉換演習：誰響誰不響（🚫 只動複本）', False),
    ('n517_temporal_order_check',
     '取得層之時序與「抽樣結果未被改過」（🚫 只讀 git）', False),
    ('n519_manifest_generation_drift',
     'latest manifest 有無沒被記成一代的編輯（🚫 唯讀）', False),
    ('n525_id_key_conventions',
     '識別碼切法清冊（🚫 唯讀、不需私有根）', False),
    ('n528_acquisition_effort_facts',
     '取得階段實測時刻（🚫 唯讀、不對外請求）', False),
    ('n503_executor_handoff', '三項交辦之答覆與 18 格交接檔', False),
    ('n501_retraction_recheck', '撤稿現場重查（🚨 會對外送請求）', True),
]
WITH_NETWORK = '--with-network' in sys.argv

# 🚨 手維護清單看不到自己漏了什麼——⚠️ 故把那個盲點做成一份可見清單：
# 掃出第 490 輪以後之三位數編號腳本，凡不在 CHECKS 內者一律列出。
# ⚠️ 其中有些本來就不是常設檢查（一次性的描述型產物），故各附排除理由；
# 🚨 沒有理由可寫的，就是漏了。
RECENT = re.compile(r'^n(49[0-9]|5[0-9][0-9])_.*\.py$')
NOT_A_CHECK = {
    'n495_stratum_purpose': '一次性描述：把七層各自要檢驗什麼列出來，🚫 無成敗可言',
    'n504_executor_suite': '本檔自己',
    'n505_licence_completion': ('一次性補齊作業：🚨 會對外請求且 `--apply` 會寫入'
                                '私有根，🚫 不宜納入每次總跑'),
    'n510_licence_second_source': ('一次性補查：🚨 會對外請求且 `--apply` 會寫入'
                                   '私有根，🚫 不宜納入每次總跑'),
    'n511_datacite_licence': ('一次性補查：🚨 會對外請求且 `--apply` 會寫入私有根，'
                              '🚫 不宜納入每次總跑'),
    'n513_repository_deposit_terms': ('一次性補查：🚨 會對外請求，'
                                      '🚫 不宜納入每次總跑'),
    'n521_owner_briefing_crosscheck': ('跨室對帳：🚨 其非零表示**簡報**有待協調者'
                                       '處置，⚠️ 不是本室之檢查失敗——'
                                       '🚫 不納入總跑，否則本室恆紅'),
    'n522_s3_record_factsheet': ('一次性事實表：🚨 會對外請求（版本查詢），'
                                 '🚫 不宜納入每次總跑'),
    'n523_s56_version_with_backfill': ('一次性量測：🚨 會對外請求（版本查詢），'
                                       '🚫 不宜納入每次總跑'),
    'n524_gi_published_availability': ('一次性補查：🚨 會對外請求，'
                                       '🚫 不宜納入每次總跑'),
    'n526_no_oa_locations_recheck': ('一次性複查：🚨 會對外請求 40 次，'
                                     '🚫 不宜納入每次總跑'),
    'n527_incomplete_record_closeout': ('一次性收尾：🚨 會對外請求，'
                                        '🚫 不宜納入每次總跑'),
    'n508_section_g_crosscheck': ('跨室對帳：🚨 其非零表示**協調者之文件**有待更正，'
                                  '⚠️ 不是本室之檢查失敗——'
                                  '🚫 不納入總跑，否則本室會因他室文件而恆紅，'
                                  '而恆紅等於沒有紅'),
}
# 🚨 n+162（九之一）：協調者不得執行本清單——⚠️ 其中多支是產生器，
# 「跑一下看看」不是唯讀動作。✅ 兩室之總跑清單各自獨立，🚫 不互跑。


def run(path, timeout=900):
    """跑一支，回傳 (exit code, 秒數)。🚨 以 utf-8 解碼——⚠️ 本機 locale 為 cp950，
    以預設解碼會讓 reader thread 死在中文輸出上（第 500 輪已回報該型）。"""
    t0 = time.time()
    try:
        r = subprocess.run([sys.executable, path], capture_output=True,
                           encoding='utf-8', errors='replace', timeout=timeout,
                           env=dict(os.environ, PYTHONIOENCODING='utf-8'))
        return r.returncode, round(time.time() - t0, 1)
    except subprocess.TimeoutExpired:
        return 'TIMEOUT', round(time.time() - t0, 1)


print('=== 執行室常設檢查總跑（第 %d 輪）===' % ROUND)
print('   網路類：%s' % ('✅ 開啟（--with-network）' if WITH_NETWORK
                         else '🚫 預設略過，⚠️ 但仍列名'))
print()

# ── 控制探針 ─────────────────────────────────────────────────────
print('一、控制探針——🚨 未如預期即拒絕報告')
# 🚨 n+162（九）：初版把探針檔寫進 `./tmp`（`CLAUDE_JOB_DIR` 未設時），
# ⚠️ 於是協調者跑過一次之後，樹裡多出一個 `tmp/` 要清。
# 🚫 檢查工具不該在被檢查的樹裡留東西——✅ 改用系統暫存並自清。
probe_dir = tempfile.mkdtemp(prefix='n504-')
ok_path = os.path.join(probe_dir, '_suite_ok.py')
bad_path = os.path.join(probe_dir, '_suite_bad.py')
io.open(ok_path, 'w', encoding='utf-8').write('import sys\nsys.exit(0)\n')
io.open(bad_path, 'w', encoding='utf-8').write('import sys\nsys.exit(3)\n')
rc_ok, _ = run(ok_path, timeout=60)
rc_bad, _ = run(bad_path, timeout=60)
shutil.rmtree(probe_dir, ignore_errors=True)
ctl = [{'probe': '必然成功之命令', 'expect': 0, 'got': rc_ok, 'ok': rc_ok == 0},
       {'probe': '必然失敗之命令', 'expect': 3, 'got': rc_bad, 'ok': rc_bad == 3}]
for c in ctl:
    print('   %s %-18s 期待 %s／實得 %s'
          % ('✅' if c['ok'] else '🚨', c['probe'], c['expect'], c['got']))
if not all(c['ok'] for c in ctl):
    sys.exit('🚨 控制探針未如預期——🚫 一個分不出成敗的跑法，其「全過」沒有意義，中止。')
print('   ✅ 兩道皆如預期：這個跑法分得出成功與失敗。')
print()

# ── 總跑 ─────────────────────────────────────────────────────────
print('二、逐支')
print('   %-28s %6s %8s  %s' % ('檢查', '退出碼', '秒', '驗什麼'))
print('   ' + '-' * 96)
rows = []
for name, what, needs_net in CHECKS:
    path = S + name + '.py'
    if not os.path.exists(path):
        rows.append({'check': name, 'status': 'missing', 'exit': None,
                     'seconds': 0, 'asserts': what})
        print('   %-28s %6s %8s  🚨 檔案不存在' % (name, '—', '—'))
        continue
    if needs_net and not WITH_NETWORK:
        rows.append({'check': name, 'status': 'skipped', 'exit': None,
                     'seconds': 0, 'asserts': what,
                     'why': '需要對外請求；🚫 預設不跑（--with-network 可開）'})
        print('   %-28s %6s %8s  ⏸ 略過（需網路）' % (name, '—', '—'))
        continue
    rc, secs = run(path)
    rows.append({'check': name, 'status': 'pass' if rc == 0 else 'fail',
                 'exit': rc, 'seconds': secs, 'asserts': what})
    print('   %-28s %6s %8s  %s %s'
          % (name, rc, secs, '✅' if rc == 0 else '🚨', what[:52]))
print('   ' + '-' * 96)

passed = sum(1 for r in rows if r['status'] == 'pass')
failed = [r for r in rows if r['status'] == 'fail']
skipped = [r for r in rows if r['status'] in ('skipped', 'missing')]
total_s = round(sum(r['seconds'] for r in rows), 1)
print('   ✅ 通過 %d｜🚨 失敗 %d｜⏸ 未跑 %d｜合計 %.1f 秒'
      % (passed, len(failed), len(skipped), total_s))
for r in failed:
    print('      🚨 %s 以 %s 結束' % (r['check'], r['exit']))
for r in skipped:
    print('      ⏸ %s：%s' % (r['check'], r.get('why', '檔案不存在')))
print()
print('三、🚨 清單之盲點檢查（⚠️ 手維護清單看不見自己漏了什麼）')
listed = {c[0] for c in CHECKS}
found = sorted(f[:-3] for f in os.listdir(S) if RECENT.match(f))
unlisted = [n for n in found if n not in listed]
missing_reason = [n for n in unlisted if n not in NOT_A_CHECK]
for n in unlisted:
    why = NOT_A_CHECK.get(n)
    print('   %s %-28s %s' % ('⚠️' if why else '🚨', n,
                              why or '🚨 未列入清單且無排除理由——⚠️ 可能是漏了'))
if not unlisted:
    print('   ✅ 第 490 輪後之腳本全數已列入清單。')
print('   🚨 清單為手維護：目前 %d 支，最後更新於第 %d 輪；'
      '掃到 %d 支、未列 %d 支、其中無理由者 %d 支。'
      % (len(CHECKS), ROUND, len(found), len(unlisted), len(missing_reason)))
print('   ⚠️ 掃描只涵蓋第 490 輪之後之三位數編號——'
      '🚫 更早的、或不照此命名的檢查，本掃描看不到。')

doc = {
    'schemaVersion': 1,
    'documentType': 'executor-standing-check-suite',
    'ruling': 'self-initiated, generalising round 503: a value nobody reads is '
              'not produced, and a check nobody runs is indistinguishable from a '
              'broken one -- both produce no output.',
    'population': 'the executor room\'s standing checks, hand-maintained list',
    'countingUnit': 'check',
    'criterion': 'exit code only; the suite deliberately does not parse any '
                 "check's printed output",
    'listedChecks': len(CHECKS),
    'listLastUpdatedRound': ROUND,
    'withNetwork': WITH_NETWORK,
    'controlProbes': ctl,
    'controlNote': 'A runner that always reports success looks exactly like one '
                   'where everything passes, so a certainly-failing command must '
                   'be seen to fail before any result is reported.',
    'checks': rows,
    'listBlindSpotScan': {
        'pattern': 'n490-n599 three-digit scripts in .scratch',
        'found': found,
        'unlisted': unlisted,
        'unlistedWithoutReason': missing_reason,
        'excludedWithReason': {n: NOT_A_CHECK[n] for n in unlisted
                               if n in NOT_A_CHECK},
        'note': 'The scan only covers scripts numbered from round 490 onward and '
                'named that way. An older or differently-named standing check is '
                'invisible to it, so this narrows the blind spot rather than '
                'closing it.',
    },
    'passed': passed,
    'failed': [r['check'] for r in failed],
    'skipped': [r['check'] for r in skipped],
    'totalSeconds': total_s,
    'coverageStatement': 'Sees whether each check exits zero, not whether it '
                         'checks the right thing -- that is each check\'s own '
                         'control probes. And the list is hand-maintained, so a '
                         'check this room forgot to add is invisible here; the '
                         'list length and its last-updated round are printed to '
                         'force that comparison.',
    'contentNote': 'Check names, exit codes and durations only.',
}
io.open(S + 'n504_executor_suite.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn504_executor_suite.json' % S)
sys.exit(1 if (failed or missing_reason) else 0)
