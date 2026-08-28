# -*- coding: utf-8 -*-
"""本室每輪回報之宣稱 ↔ 產生指令對照，並補上「M1 四步」之產生指令。

## 🚨 為何要做這件事

第 435 輪自曝：本室每輪寫「測試 743/743」，**那個數字沒有跑過**。
**⚠️ 閘門接不住它，因為它不是來自任何檢查，是來自散文。**

**🚨 於是問題一般化為：本室回報中的數字，有多少有對應的產生指令？**
本檔逐條列出，**有指令者當場跑並印出當前值；沒有指令者標紅**。

## ⚠️ 宣稱清單之來源

**不憑記憶列**（n+44：重打而不載入原件）——
以 `COORDINATION.md` 中本室最近 8 段回報實際出現過的句子為準。

## 🚨 本檔之涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：**每條宣稱是否有可執行的產生指令**，以及該指令當前之輸出。
- 🚨 查不到：**宣稱的措辭是否忠實反映該輸出**——⚠️ 那需要人讀。
  例：指令回「716 passed／1 failed」而報告寫成「測試通過」，本檔不會判紅。
"""
import io
import json
import subprocess
import sys

S = '.scratch/'


def load(n):
    return json.load(io.open(S + n, encoding='utf-8'))


# ── 一、M1 四步之產生指令（本輪新建）──────────────────────────────
def m1_steps():
    """🚨 每一步都寫明判準，⚠️ 否則「✅」只是一個沒有定義的勾。"""
    rows = []

    pop = load('n85_tail_population.json')
    rows.append((
        '① 篩選完成＋終止證據',
        '母體已凍結且筆數為 1,460（`n85_tail_population.json`）',
        pop['count'] == 1460,
        '母體 %d 筆；⚠️ 「擁有者宣告終止」本身是看板上的裁定行為，'
        '🚨 非機器可驗，本檔不宣稱驗過它。' % pop['count']))

    cal = load('m1_step2_calibration_set.json')
    quota = sum(v['quota'] for v in cal['draws'].values())
    ids = [x for v in cal['draws'].values() for x in v['candidateIds']]
    rows.append((
        '② 60 筆校準集（依層抽出）',
        'totalSampleSize＝60、六池配額合計＝60、抽出之 id 互斥不重複',
        cal['totalSampleSize'] == 60 and quota == 60 and len(set(ids)) == len(ids) == 60,
        '契約 %d／配額合計 %d／抽出 %d 筆（相異 %d）'
        % (cal['totalSampleSize'], quota, len(ids), len(set(ids)))))

    inv = load('m1_step3_inventory.json')
    bf = load('m1_step3_backfill.json')
    t = bf['totals']
    st = inv['counts']['byStatus']
    rows.append((
        '③ OA 全文取得',
        '60 筆**每筆皆已判定狀態**（狀態合計＝60）且遞補帳平（可得＋缺口＝配額）',
        sum(st.values()) == inv['counts']['total'] == 60
        and t['obtainable'] + t['shortfall'] == t['quota'] == 60,
        '狀態合計 %d／%d；可得 %d ＋ 缺口 %d ＝ 配額 %d'
        % (sum(st.values()), inv['counts']['total'],
           t['obtainable'], t['shortfall'], t['quota'])))

    rows.append((
        '④ 首輪萃取＋品質報告',
        '⏸ 依 n+105 未啟動——待擁有者就交付形狀裁示',
        None,
        '🚫 未開始，故無「完成」可驗；⚠️ 報告不得寫成 ✅ 或 🚨。'))
    return rows


print('=== 一、M1 四步之產生指令（本輪新建）===')
print('🚨 本輪之前，「M1 四步 ①✅②✅③✅」在本室回報中沒有任何產生指令。')
print()
m1_ok = True
for name, crit, ok, detail in m1_steps():
    mark = '⏸' if ok is None else ('✅' if ok else '🚨')
    print('%s %s' % (mark, name))
    print('     判準：%s' % crit)
    print('     實測：%s' % detail)
    if ok is False:
        m1_ok = False

# ── 二、宣稱 ↔ 產生指令對照 ──────────────────────────────────────
# (宣稱, 產生指令 or None, 判定方式)
CLAIMS = [
    ('n+48 第一道／第二道 53 檔／118 處',
     'python .scratch/round_gate.py', 'exit'),
    ('n+54 三道錨定皆空',
     'python .scratch/round_gate.py', 'exit'),
    ('測試（原「743/743」係抄寫；現 717 passed／0 failed 對基線）',
     'python .scratch/round_gate.py', 'exit'),
    ('產物鏈結 11／6／6',
     'python .scratch/m1_artefact_chain_check.py', 'exit'),
    ('數字附註 12／12',
     'python .scratch/m1_number_annotation_audit.py', 'exit'),
    ('W4b 615 筆／全項通過',
     'python .scratch/n77_w4b_verify.py', 'exit'),
    ('M1 四步 ①✅②✅③✅④⏸',
     'python .scratch/n436_claim_provenance.py', 'self'),
    ('列管：空',
     None, None),
    # 🚨 n+113（五）：`ahig/` 自第 437 輪起有一次正當改動，
    #    ⚠️ 「零改動」不再適用，🚫 不得因習慣續寫——改為列出改動檔案。
    ('`ahig/` 本輪改動清單（🚫 不再寫「零改動」）',
     'git diff --name-only origin/feature/istudy-private-backup-workflow -- ahig/',
     'list'),
]

print()
print('=== 二、宣稱 ↔ 產生指令對照 ===')
print('%-40s %-52s %s' % ('宣稱', '產生指令', '本輪實跑'))
print('-' * 108)
missing = []
cache = {}   # ⚠️ 同一指令支撐多條宣稱（round_gate 三條），跑一次即可。
for claim, cmd, how in CLAIMS:
    if cmd in cache:
        print('%-40s %-52s %s' % (claim, cmd, cache[cmd] + '（同上一次執行）'))
        continue
    if cmd is None:
        print('%-40s %-52s %s' % (claim, '🚨 無產生指令', '—'))
        missing.append(claim)
        continue
    if how == 'self':
        res = '✅' if m1_ok else '🚨'
    elif how == 'list':
        out = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        fs = [x for x in out.stdout.strip().split('\n') if x.strip()]
        res = ('（本輪無改動）' if not fs
               else '⚠️ %d 檔：%s' % (len(fs), '、'.join(fs)))
    else:
        exe = 'python3' if 'round_gate' in cmd else 'python'
        out = subprocess.run([exe, '-X', 'utf8'] + cmd.split()[1:],
                             capture_output=True, text=True, encoding='utf-8',
                             errors='ignore')
        res = '✅ exit=0' if out.returncode == 0 else '🚨 exit=%d' % out.returncode
    cache[cmd] = res
    print('%-40s %-52s %s' % (claim, cmd, res))

print('-' * 108)
print()
if missing:
    print('🚨 仍無產生指令者 %d 條：' % len(missing))
    for m in missing:
        print('   • %s' % m)
    print('⚠️ 這類宣稱在本室回報中與有指令者外觀相同（都是一句斷言），')
    print('   🚨 讀者無從分辨哪一句背後有指令——即第 435 輪那個洞的一般形。')
else:
    print('✅ 每一條經常性宣稱皆有產生指令。')

# ── 三、「列管」之現查輔助 ──────────────────────────────────────
# 🚨 「是否結清」需要判讀，機器判不了；⚠️ 但「抄自己上一輪的話」是可以擋掉的。
#    n+111（乙）要求逐項現查、不得沿用上一輪文字——本段即為此而生：
#    把協調者最近提到列管之處**逐字**印出來，強制載入原件（n+44）。
# ⚠️ 本段初版誤縮排落入上面的 else: 分支，而 missing 非空故從未執行——
#    🚨 畫面上與「本來就沒有第三段」一模一樣，又是一次沉默失效。
print()
print('=== 三、「列管」現查輔助（🚨 只載入原件，不代為判斷結清）===')
board = io.open('COORDINATION.md', encoding='utf-8').read().split('\n')
hits = [(i + 1, l.strip()) for i, l in enumerate(board)
        if '列管' in l and l.strip()]
print('   全看板提及「列管」之行：%d 行；以下為最後 8 行（逐字）' % len(hits))
for ln, txt in hits[-8:]:
    print('   第 %5d 行 | %s' % (ln, txt[:104]))
print('   ⚠️ 本段不判定任何一項是否結清——🚨 判定需人讀，且須附各該項之查核輸出。')
print('   ⚠️ 提請協調者：若開列管時標一個穩定記號（例如 `【列管:xxx】`／`【結清:xxx】`），')
print('      🚨 這一條就能有真正的產生指令；⚠️ 現況下任何自動判定都是猜。')

print()
print('⚠️ 涵蓋範圍：本檔只查「有無產生指令」與「該指令當前之輸出」；')
print('   🚨 不查「報告措辭是否忠於該輸出」——那需要人讀。')
sys.exit(0 if m1_ok else 1)
