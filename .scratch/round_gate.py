# -*- coding: utf-8 -*-
"""每輪必做檢查之閘門：n+48 兩道資料衛生 ＋ n+54 三道錨定 ＋ 測試套件——以狀態碼回報，壞掉會大聲。

## 🚨 第 433 輪改名之由來

本檔原名 `n48_hygiene_gate.py`，本輪擴入 n+54 三道錨定後即名實不符。
**⚠️ 本 run 已因「標籤與內容不符」吃過虧**（n49／n68 之雜湊標籤，見 n+111 四），
**🚨 故不留一個以單一裁定編號命名、實際涵蓋三道裁定的檔案。**

## 🚨 本檔為何存在：第 432 輪的一次偽 PASS

本室每輪以**手打的 shell 指令**跑第二道：

```
git ls-files | xargs grep -lP '〈[^〉]{20,}〉' 2>/dev/null | wc -l
```

**⚠️ 這一行在本機的 locale 下根本跑不動**——

```
grep: -P supports only unibyte and UTF-8 locales     ← exit=2
```

**🚨 而 `-l` 無命中時本就不印東西，`2>/dev/null` 又把錯誤訊息吞掉，
於是「工具壞了」與「零命中」在畫面上完全一樣，被讀成 PASS。**

**⚠️ 這是本 run 已列管之「偽 PASS」型的新一例，且前幾例是樣式過窄，
🚨 這一例更糟：檢查根本沒有執行。**

## 🚨 第二個教訓：不要憑記憶重建已公布的樣式

察覺 grep 壞掉後，本室改以 python 重算，得 **64 檔／540 處**（基線 53／118），
**⚠️ 一度以為文獻內容外洩。**

實際是本室重建的樣式錯了兩處：

| | 本室重建 | n+85 第 61372 行公布之權威樣式 |
|---|---|---|
| 範圍 | `git ls-files`（全 repo） | **`git ls-files .scratch/`** |
| 長度 | `{20,}` | `{25,300}` |
| 內含條件 | **無** | **`[A-Za-z]{4,}\\s+[A-Za-z]{4,}`** |

**⚠️ 範圍過寬、又漏掉 INNER，於是把看板裡協調者自己的英文敘述算成了逐字標題。**
**🚨 n+85 公布樣式的用意就是可複查；本室卻沒去取用它，而是憑記憶重建。**
照公布樣式現算即為 **53 檔／118 處，與基線相同**。

## 🚨 第 433 輪：同一型缺陷在 n+54 三道錨定上原封不動地存在

上一輪只修了實例，沒修這一類。**⚠️ 本輪回頭問「還有哪些檢查是壞掉也沉默的」**，
對 n+54 實測：

```
① 正常跑                              → 輸出空，exit=123
② 給一個不存在的旗標（模擬工具失效）  → 輸出空，exit=123
```

**🚨 兩者完全無法分辨，而這道守的是「衝突標記不得寫進看板」。**
本室每輪回報之「三道皆空」，與第二道同樣是不可信的 PASS。

## 🚨 控制探針：怎麼證明「掃描真的跑過」

**⚠️ 期待輸出為空的檢查，天生無法自證**——空可能是乾淨，也可能是沒跑。
**故本檔對每一道期待為空者，另跑一個「必定要有命中」的控制樣式**；
**🚨 控制樣式若零命中，即判定為工具或語料出問題，中止並回非零，🚫 不得回報 PASS。**

（第二道天生自帶控制：基線 53／118 不為零，掃描若沒跑會得 0 而立刻不符。）

## 本檔之涵蓋範圍聲明（n+80 三之紀律）

- ✅ 抓得到：三組已公布樣式所涵蓋者（n+48 兩道、n+54 三道），
  且**工具失效或語料讀不到時會以非零狀態碼中止，而非回報 PASS**。
- ⚠️ 樣式來源比對只涵蓋 `PAT`／`INNER`／第一道四樣式**三者**；
  **🚨 n+54 三式無法比對**——看板第 43069 行只公告了三式中的一式（`^<<<<<<< `），
  另兩式以「等三式」帶過。**⚠️ 故那三式在本檔仍是重打，未經原件驗證。**
- 🚨 抓不到：**不加任何標記、直接寫在中文判讀理由裡的英文題名**
  ——n+80 已載明沒有可靠樣式能把它與本室自己寫的英文說明分開。
  **⚠️ 故本檔通過代表「兩道已知樣式無新增」，不代表「無文獻內容」。**
"""
import io
import re
import subprocess
import sys

# ── n+132：本檔**刻意不裝** SIGPIPE guard ──────────────────────────
# ⚠️ n115／n116／n131 三支報表檔已把 SIGPIPE 還原為系統預設，接管線即安靜結束。
# 🚨 本檔不同：**本檔的產物是 exit code**（0=閘門通過）。
# 裝了 guard，接管線後會以 141 結束；不裝，則會噴 BrokenPipeError。
# **兩者都不是 0，也都不是真正的閘門結果**——差別只在哪一種比較吵。
# ⚠️ 故此處不靠寫法補救，直接立為使用限制：
#     🚫 **本檔不得接任何管線**；要看片段請先重導向到檔案再讀。
# ──────────────────────────────────────────────────────────────────

# ⚠️ 樣式在原始碼中一律以片段組合，🚨 否則本檔自己會命中第一道。
CARET = chr(94)
PASS1 = [
    (CARET + 'TITLE:', 'title-line'),
    (CARET + 'ABS:', 'abstract-line'),
    ('"abstract' + 'Text"', 'europepmc-field'),
    (CARET + '   T: ', 'indented-title'),
]
# n+85 第 61372 行公布之樣式，逐字照抄
PAT = re.compile(r"〈([^〉]{25,300})〉")
INNER = re.compile(r"[A-Za-z]{4,}\s+[A-Za-z]{4,}")
BASELINE_FILES, BASELINE_SITES = 53, 118

# n+54 第 43069 行：行首錨定之三式。⚠️ 同樣以片段組合，🚨 否則本檔自我命中。
LT, GT, EQ = chr(60) * 7, chr(62) * 7, chr(61) * 7
CONFLICT = [
    (CARET + LT + ' ', 'merge-begin'),
    (CARET + GT + ' ', 'merge-end'),
    (CARET + EQ + '$', 'merge-sep'),
]

# 🚨 控制探針：期待為空之檢查無法自證，故各配一個「必定命中」之樣式。
#    ⚠️ 控制零命中 → 判為工具／語料出問題，🚫 不得回報 PASS。
# ⚠️ 下限之用途是偵測「完全沒跑」，不是精確計數，故取實際值之半並留餘裕；
# 🚨 第 433 輪初版把下限訂成 100 而實際為 43，被自己的探針擋下——已改為實測後訂定。
# ⚠️ 兩式刻意正交：一個打資料面、一個打程式面，避免同時失效。
CONTROLS = [
    ('.scratch/', 'candidateId', 200, '資料面：.scratch/ 含 candidateId（實測 368）'),
    ('.scratch/', CARET + r'(import|from) ', 150, '程式面：.scratch/ 含 import（實測 277）'),
]
CONTROL_BOARD = (CARET + r'## ', 100, '看板含 ## 標題行（實測 866）')


def tracked(prefix='.scratch/'):
    # ⚠️ 空字串在 git 是無效 pathspec，故無前綴時不傳該參數。
    cmd = ['git', 'ls-files'] + ([prefix] if prefix else [])
    out = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
    if out.returncode != 0:
        sys.exit('🚨 git ls-files 失敗，本檔不得回報 PASS：%s' % out.stderr[:200])
    return [f for f in out.stdout.split('\n') if f.strip()]


def board_provenance():
    """🚨 n+112（四）／n+44：本檔之樣式是**重打**進原始碼的，不是載入原件。

    ⚠️ 協調者抄列管、本室抄樣式，同一條規矩兩個房間各犯一次。
    🚨 重打之副作用不是當下寫錯（當下會比對），是**原件日後修訂而副本不動**，
    且副本仍每輪回報 PASS——即一種會隨時間長出來的偽 PASS。

    故本函式從看板抽出公告之樣式原件，與本檔硬寫者比對；
    🚫 不一致即中止：那時候的 PASS 沒有意義。
    """
    try:
        b = io.open('COORDINATION.md', encoding='utf-8').read()
    except OSError as e:
        sys.exit('🚨 讀不到看板，無從驗證樣式來源：%s' % e)
    out = []
    for name, mine in (('PAT', PAT.pattern), ('INNER', INNER.pattern)):
        got = sorted(set(re.findall(name + r'\s*=\s*re\.compile\(r"([^"]+)"\)', b)))
        if len(got) != 1:
            sys.exit('🚨 看板上 %s 之公告有 %d 種相異寫法，🚫 無從認定原件。' % (name, len(got)))
        out.append((name, got[0] == mine, got[0], mine))
    # 第一道：取看板上含 \| 之完整四樣式字串
    cand = sorted({s for s in re.findall(r"xargs grep -l '([^']+)'", b) if r'\|' in s})
    if len(cand) != 1:
        sys.exit('🚨 看板上第一道之公告有 %d 種相異寫法，🚫 無從認定原件。' % len(cand))
    board_list = cand[0].split(r'\|')
    mine_list = [p for p, _ in PASS1]
    out.append(('PASS1', board_list == mine_list, board_list, mine_list))
    return out


print('樣式來源比對（🚨 與看板公告之原件不符即中止）')
prov = board_provenance()
for name, ok, board, mine in prov:
    print('   %-6s %s' % (name, '✅ 與看板一致' if ok else '🚨 不一致'))
    if not ok:
        print('      看板：%r' % (board,))
        print('      本檔：%r' % (mine,))
if not all(ok for _, ok, _, _ in prov):
    sys.exit('🚨 本檔樣式已與看板公告分歧，🚫 拒絕回報 PASS——請先對齊。')
print()

files = tracked()
if not files:
    sys.exit('🚨 受追蹤檔為零——不合理，可能是工作目錄錯誤。🚫 不回報 PASS。')

texts = {}
for f in files:
    try:
        texts[f] = io.open(f, encoding='utf-8', errors='ignore').read()
    except OSError:
        pass

print('=== 每輪閘門｜n+48 範圍 .scratch/（%d 檔）===' % len(files))
print()

# ── 控制探針：先證明「讀得到、比對得動」──────────────────────────
print('控制探針（🚨 零命中即中止，不得回報 PASS）')
for _, pat, floor, why in CONTROLS:
    rx = re.compile(pat, re.M)
    n = sum(1 for t in texts.values() if rx.search(t))
    print('   %-42s %4d 檔（下限 %d） %s' % (why, n, floor, '✅' if n >= floor else '🚨'))
    if n < floor:
        sys.exit('🚨 控制探針未達下限——掃描機制或語料有問題，🚫 本檔拒絕回報 PASS。')

# ── 第一道：四樣式，須為空 ──────────────────────────────────────
print('第一道（四樣式，須為空）')
p1_hits = []
for pat, name in PASS1:
    rx = re.compile(pat, re.M)
    hit = sorted(f for f, t in texts.items() if rx.search(t))
    # 🚨 本檔自身必然含有樣式片段，但組合後不應命中；若命中即為組合方式有誤。
    print('   %-18s %s' % (name, '✅ 空' if not hit else '🚨 %d 檔：%s' % (len(hit), hit[:5])))
    p1_hits += hit
p1_ok = not p1_hits

# ── 第二道：n+85 樣式，須等於基線 ────────────────────────────────
hf, hn = set(), 0
for f, t in texts.items():
    for m in PAT.findall(t):
        if INNER.search(m):
            hf.add(f)
            hn += 1
p2_ok = (len(hf) == BASELINE_FILES and hn == BASELINE_SITES)
print()
print('第二道（n+85 樣式，須等於基線）')
print('   現算 %d 檔／%d 處｜基線 %d 檔／%d 處   %s'
      % (len(hf), hn, BASELINE_FILES, BASELINE_SITES, '✅ 相同' if p2_ok else '🚨 有出入'))
if not p2_ok:
    print('   🚨 出入不等於外洩，也不等於沒事——⚠️ 須逐檔查明是新增、刪除，還是樣式套錯。')

# ── n+54 三道錨定：範圍為全 repo，須為空 ────────────────────────
# ⚠️ 衝突標記可能出現在任何受追蹤檔，尤以看板為然，故不限 .scratch/。
allfiles = tracked('')
alltexts = {}
for f in allfiles:
    try:
        alltexts[f] = io.open(f, encoding='utf-8', errors='ignore').read()
    except OSError:
        pass
print()
print('=== n+54 三道錨定｜範圍 git ls-files 全 repo（%d 檔）===' % len(allfiles))
rx = re.compile(CONTROL_BOARD[0], re.M)
board_hits = len(rx.findall(alltexts.get('COORDINATION.md', '')))
print('   控制探針：%-32s %4d（下限 %d） %s'
      % (CONTROL_BOARD[2], board_hits, CONTROL_BOARD[1],
         '✅' if board_hits >= CONTROL_BOARD[1] else '🚨'))
if board_hits < CONTROL_BOARD[1]:
    sys.exit('🚨 控制探針未達下限——看板讀不到或比對失效，🚫 拒絕回報 PASS。')
p3_hits = []
for pat, name in CONFLICT:
    rxc = re.compile(pat, re.M)
    hit = sorted(f for f, t in alltexts.items() if rxc.search(t))
    print('   %-18s %s' % (name, '✅ 空' if not hit else '🚨 %d 檔：%s' % (len(hit), hit[:5])))
    p3_hits += hit
p3_ok = not p3_hits

# ── 附加（本室自訂，🚨 非 n+48 公布樣式）：路徑內嵌逐字標題之網址 ──
# ⚠️ 第 452 輪發現：figshare 等站之 landing URL 把逐字英文標題放進路徑。
# 🚨 n+48 五道樣式對這一型完全抓不到（已以合成樣本實測，五道皆未命中），
#    ⚠️ 而剛解鎖之取得層工作處理的正是這種網址——
#    任一腳本若把 availableUrl 落盤到 .scratch/，逐字標題就無聲進入版控。
# ⚠️ 本段為預警不是 n+48：基線取「現況」而非「零」，
#    🚨 現有命中全部位於 trading-desk/ 與 docs/research/，與 AHIG 文獻無關。
URLTITLE = re.compile(
    r'https?://[^\s"\'<>)]*/(?:[A-Za-z]{3,}[_-]){3,}[A-Za-z]{3,}[^\s"\'<>)]*')
URLTITLE_BASE_FILES, URLTITLE_BASE_SITES = 5, 32

uf, un = set(), 0
for _f, _t in alltexts.items():
    _m = URLTITLE.findall(_t)
    if _m:
        uf.add(_f)
        un += len(_m)
u_ok = (len(uf) == URLTITLE_BASE_FILES and un == URLTITLE_BASE_SITES)
print()
print('=== 附加預警：路徑內嵌標題之網址（🚨 本室自訂，非 n+48）===')
print('   現算 %d 檔／%d 處｜基線 %d／%d   %s'
      % (len(uf), un, URLTITLE_BASE_FILES, URLTITLE_BASE_SITES,
         '✅ 與基線相同' if u_ok else '🚨 有出入'))
if not u_ok:
    print('   命中檔：%s' % sorted(uf)[:8])
print('   ⚠️ 不影響 exit code（非公布樣式）；🚨 AHIG 之 .scratch/ 出現此型即為外洩。')

# ── 測試：🚨 數字必須來自實跑，不得沿用上一輪 ────────────────────
# ⚠️ 第 435 輪之由來：本室每輪回報「測試 743/743」，實為抄寫。
# 🚨 本機 `python` 根本沒有 pytest（只有 `python3` 有），即使有也收集不全
#    （缺已宣告依賴 pyshacl>=0.30，pyproject 第 15 行），故該數字不可能是本室跑出來的。
# ⚠️ 基線之用途與 53/118 相同：**已知且已載明者為綠，偏離者為紅**；
#    🚨 若把已知失敗一律判紅，閘門會恆紅而被忽略，那等於沒有閘門。
PYTEST_DIR = 'ahig'
PYTEST_IGNORE = 'tests/test_shacl_gates.py'
# ✅ 第 437 輪依 n+113（四）修好該筆後，基線由 716+1 改為 717+0。
# ⚠️ 基線是「已知且已載明之狀態」，🚨 修好了就得跟著改，否則閘門會把正確狀態判紅。
# ⚠️ 第 475 輪新增 1 筆測試（_artifact_files 之來源型別），基線隨之由 717 改為 718。
# 第 516 輪：720 → 722。改動基線之前後對照（n+113 四）：
#   改動前  720 passed／0 failed
#   改動後  722 passed／0 failed
# 新增的兩條測的是同一件事在兩條路徑上的樣子——產線驗證器現在也對
# sections 檔自記的來源指紋（n+171 交辦一）。**沒有既有測試由通過變成失敗**，
# 增量恰為 2，故基線只是往上加，不是把紅的調成綠的。
# 第 529 輪：722 → 726。前後對照（n+113 四）：
#   改動前  722 passed／0 failed
#   改動後  726 passed／0 failed
# 新增四條，測的是萃取讀取層（M1 第四步之第一塊，n+181 三之 2）。
# 沒有既有測試由通過變成失敗，增量恰為 4。
# 第 481–482 輪：726 → 741 → 746。改動基線之前後對照（n+113 四）：
#   改動前  726 passed／0 failed
#   改動後  741 passed／0 failed（+15 橋接）
#   再改後  746 passed／0 failed（+5 鏈接合處；第 482 輪）
# 增量 15 條全部來自萃取橋接（`test_extraction_bridge.py`，協調者），
# 測的是 draft 清冊會安靜出錯的幾種方式：綁錯文件、綁錯契約、自稱 scoped、
# 挾帶範圍判定、聲稱掃描過不存在的章節。
# **沒有既有測試由通過變成失敗**，故基線只是往上加。
#
# 🚨 併記一次數字對不上：我先以 `pytest -q` 得 767，而本閘門得 741。
# ⚠️ 差的 26 條是 `tests/test_shacl_gates.py`——**本閘門 `--ignore` 掉它**。
# 🚫 兩個數都對，而它們數的不是同一個集合；**若當時逕自把基線寫成 767，
#    此後每一輪都會偏離**。故基線一律以**本閘門自己的跑法**為準。
# 第 530 輪：746 → 749。前後對照（n+113 四）：
#   改動前  746 passed／0 failed
#   改動後  749 passed／0 failed
# 新增三條，測讀取層與橋之接合：manifestation 綁 sections 自記之
# contentSha256、驗證發生在組請求之前、契約未凍結即拒絕。
# 無既有測試由通過變成失敗，增量恰為 3。
# 第 531 輪：749 → 753。前後對照（n+113 四）：
#   改動前  749 passed／0 failed
#   改動後  753 passed／0 failed
# 新增四條，測整批跑：不給 reader 要大聲失敗、reader 出錯的那篇仍列出、
# 空清冊算失敗、每一篇恰好落在一個桶子裡。增量恰為 4。
# 第 533 輪：753 → 756。前後對照（n+113 四）：
#   改動前  753 passed／0 failed
#   改動後  756 passed／0 failed
# 新增三條，測清冊存放處：存過就重用且記成 reused 而非「這次讀到的」、
# 換了契約不算做過、同鍵不同內容拒絕覆寫。增量恰為 3。
# 同一輪另修兩處測試自身之缺陷（不改變條數）：本檔的樁契約殘缺，
# ScopeMatcher 收不下，於是「混合結果」那條其實兩筆都失敗仍照樣通過。
# 第 534 輪：756 → 760。前後對照（n+113 四）：
#   改動前  756 passed／0 failed
#   改動後  760 passed／0 failed
# 新增四條，測跑完留下的收據：桶子數不得改用嘗試數、記下的字元數須等於
# 真的送出去的那串、每一列指得到磁碟上的檔且位元組相符、重用那趟送出 0 字元。
# 三個必觸發控制（把對應的錯誤各種進去一次）皆打中該紅的那一條。增量恰為 4。
# 第 535 輪：760 → 763。前後對照（n+113 四）：
#   改動前  760 passed／0 failed
#   改動後  763 passed／0 failed
# 新增三條，測「契約先驗再花錢」：造不出 ScopeMatcher 的契約整批拒跑且
# 一篇都不讀（正向對照：能用的契約照樣過關）、真的那份凍結契約過得了前驗。
# 增量恰為 3。
# 第 536 輪：763 → 773。前後對照（n+113 四）：
#   改動前  763 passed／0 failed
#   改動後  773 passed／0 failed
# 新增十條，測萃取工作單（ADR-0009 裁定①那條路的萃取版）：按字元編頁、
# 超預算單篇自成一頁不切開、索引不帶全文而逐頁帶、工作單不得離開私有根、
# 綁到別份文件的清冊收回時被拒（正向對照：綁對的照樣收）、沒讀完不算讀完、
# 沒有 readBy 不收、文件在寫清冊之後變過則拒用、找不到清冊要丟不要回空的。
# 增量恰為 10。
# 第 539 輪：773 → 775。前後對照（n+113 四）：
#   改動前  773 passed／0 failed
#   改動後  775 passed／0 failed
# 新增兩條，測「下游 schema 也要驗」：validate_draft 收得下而 schema 收不下的
# draft 要記成 validate-draft 失敗（正向對照：合規的一份 schema 無話可說，
# 而多一個未宣告欄位就該有話）。增量恰為 2。
# ⚠️ 同一輪修了三處 fixture 自身之不合規（本檔與 worksheet 檔的 _draft_for、
# n537 之替身）——那三處先前都不合下游 schema，是新檢查抓出來的，不改變條數。
# 第 546 輪：775 → 780。前後對照（n+113 四）：
#   改動前  775 passed／0 failed
#   改動後  780 passed／0 failed
# 新增五條，測工作單的「一頁一頁併回去」：併入一頁、同一篇不得併兩次、
# 併入失敗時檔案要維持原樣（半套寫入會讓前面幾頁也卡住）、沒有 readBy 不併、
# 單獨取一頁（含取不存在的頁要丟）。增量恰為 5。
BASE_PASSED, BASE_FAILED = 780, 0
KNOWN_FAIL = '無（原 test_clopper_pearson_matches_closed_forms 已於第 437 輪依 n+113 四修正）'
# 第 544 輪更正：先前只寫「缺 pyshacl」。⚠️ 操作上沒錯（裝 pyshacl 會帶 rdflib），
# 🚨 但那句話讓人以為只差一個套件，而實測 rdflib 也不在——
# 亦即 gates/shacl.py 與 verify.py 整層在本機都跑不起來，不只是這 26 條測試。
UNCOLLECTABLE = ('%s（🚨 rdflib 與 pyshacl 皆不在，pyproject 第 15 行已宣告；'
                 '⚠️ 故本機 gates/shacl.py 與 verify.py 整層跑不起來）'
                 % PYTEST_IGNORE)


def run_tests():
    """回傳 (passed, failed, 直譯器, 原始摘要行)；找不到可用直譯器則回 None。"""
    for exe in ('python3', 'python'):
        probe = subprocess.run([exe, '-c', 'import pytest'], capture_output=True)
        if probe.returncode != 0:
            continue
        r = subprocess.run([exe, '-X', 'utf8', '-m', 'pytest', '-q',
                            '--ignore=' + PYTEST_IGNORE],
                           cwd=PYTEST_DIR, capture_output=True, text=True,
                           encoding='utf-8', errors='ignore')
        txt = re.sub(r'\x1b\[[0-9;]*m', '', r.stdout or '')
        tail = [l for l in txt.strip().split('\n') if 'passed' in l or 'failed' in l]
        line = tail[-1] if tail else ''
        gp = re.search(r'(\d+) passed', line)
        gf = re.search(r'(\d+) failed', line)
        return (int(gp.group(1)) if gp else 0,
                int(gf.group(1)) if gf else 0, exe, line.strip())
    return None


print()
print('=== 測試（🚨 數字須來自實跑）===')
tr = run_tests()
if tr is None:
    print('   🚨 找不到裝有 pytest 的直譯器，🚫 本輪不得回報任何測試數字。')
    t_ok = False
else:
    passed, failed, exe, line = tr
    t_ok = (passed == BASE_PASSED and failed == BASE_FAILED)
    print('   直譯器 %s｜%s' % (exe, line))
    print('   基線 %d passed／%d failed  %s' % (BASE_PASSED, BASE_FAILED,
                                             '✅ 相同' if t_ok else '🚨 偏離'))
    print('   已知失敗：%s' % KNOWN_FAIL)
    print('   ⚠️ 未收集：%s' % UNCOLLECTABLE)
    print('   🚨 故本閘門不得聲稱「743/743」——⚠️ 743 是協調者環境之數，非此處實測。')

print()
print('=' * 62)
ok = p1_ok and p2_ok and p3_ok and t_ok
print('n+48 第一道 %s｜第二道 %s｜n+54 三道 %s｜測試 %s'
      % ('✅' if p1_ok else '🚨', '✅' if p2_ok else '🚨',
         '✅' if p3_ok else '🚨', '✅' if t_ok else '🚨'))
print('⚠️ 本檔通過只代表三組已知樣式無新增；🚨 未加標記之英文題名不在涵蓋範圍內。')
sys.exit(0 if ok else 1)
