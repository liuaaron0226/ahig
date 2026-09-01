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
# 第 549 輪：780 → 784。前後對照（n+113 四）：
#   改動前  780 passed／0 failed
#   改動後  784 passed／0 failed
# 新增四條（新檔 test_extraction_route.py），測「工作單＋存放處＋逐頁」
# 三者合起來的那個模式：前幾頁再跑時記成 reused 且 reader 呼叫數 2→4（不是 2→6）、
# 收據只收這一輪讀的錢、每份存下的清冊都指得到且位元組相符、跑完的批次再跑一次
# 一篇都不讀。三個突變（關掉存放處查詢）打紅其中 3 條，第 4 條與重用無關故仍綠。
# 增量恰為 4。
# 第 550 輪：784 → 786。前後對照（n+113 四）：
#   改動前  784 passed／0 failed
#   改動後  786 passed／0 failed
# 新增兩條，測收據新增的 unknownSections（每個數字的出處指不指得到真章節）：
# 指不到者要被數到但**不得**讓那一篇失敗；指得到者為 0（大小寫與空白不計）。
# 增量恰為 2。
# 第 551 輪：786 → 789。前後對照（n+113 四）：
#   改動前  786 passed／0 failed
#   改動後  789 passed／0 failed
# 新增三條，測預設名冊（不給 candidate_ids 那條路，先前無任何測試走過）：
# 預設涵蓋每一筆 acquired、驗不過的那筆仍留在批次裡（🚨 修掉一個真的缺陷：
# 原本被濾掉，收據會顯示「嘗試 N 成功 N」而磁碟上多一筆壞的）、
# manifest 讀不出來的目錄以目錄名列出。增量恰為 3。
# 第 552 輪：789 → 796。前後對照（n+113 四）：
#   改動前  789 passed／0 failed
#   改動後  796 passed／0 failed
# 新增七條，補上 sys.settrace 查出「從未被執行過」的那幾道守衛：
# 桶子不變式真的喊得出來（🚨 含一句先前恆真、執行不到的斷言，已改寫成拿輸入比）、
# 兩份全文不得默默挑第一份、缺 contentSha256 不得組出請求、缺綁定的清冊不得存、
# 同批次 id 不同內容不得覆寫、空工作單要拒、工作單上沒有的那一篇不得收。
# 增量恰為 7。
# 第 485 輪（併入後接續）：796 → 798。前後對照（n+113 四）：
#   改動前  796 passed／0 failed
#   改動後  798 passed／0 failed
# 🚨 本輪協調者先造了第二條讀論文路線（`in_room_reader`，八條測試），
#    ⚠️ 而執行室同時造的 `worksheet` 做的是同一件事且更完整。
#    **🚫 一個接縫兩套機制正是本 run 列管的那一族**（n+116 之 OBLIGATION_RESTATED），
#    故整條連同八條測試一併刪除，🚫 不留「兩條都在、擇一使用」。
# ✅ 併過去的只有一項執行室沒有的守衛：readBy 記為 human-self 或 deterministic
#    時要擋——⚠️ 那兩種來源記載在本專案不可能為真（ADR-0009）。
#    新增兩條（load_drafts 一條含正向對照、append_drafts 一條）。淨增量恰為 2。
# 第 487 輪：798 → 803。前後對照（n+113 四）：
#   改動前  798 passed／0 failed
#   改動後  803 passed／0 failed
# 新增五條，測「多個視窗同時讀」（n+187）：兩頁各自寫互不覆蓋且逐頁記下誰讀的、
# 🚨 寫一頁不得動到任何共用檔（**這一條才是在測並行的那個性質**，前一條循序跑
# 照樣會綠）、同一頁兩種結果不得悄悄覆寫（相同內容則為無害重寫）、寫進別頁要擋、
# 同一篇同時出現在共用檔與逐頁檔要抓到。增量恰為 5。
# 第 488 輪：803 → 806。前後對照（n+113 四）：
#   改動前  803 passed／0 failed
#   改動後  806 passed／0 failed
# 新增三條，測第二位讀者（n+188）：🚨 第二道的東西**永遠不會**進入正式清冊
# （最要緊的一條——⚠️ 否則對照組會變成產量，而半數 A 讀半數 B 讀的清冊
# 看起來和乾淨的一模一樣）、標籤比對要算得出兩邊都有／只有一邊有且說明它
# 不是錯誤數、只比兩邊都讀過的那些（🚫 對方沒讀的不得算成不同意）。增量恰為 3。
# 第 489 輪：806 → 810。前後對照（n+113 四）：
#   改動前  806 passed／0 failed
#   改動後  810 passed／0 failed
# 新增四條，測儀器那道接縫（n+189）：讀的人要看得到判定會逐字比的允許清單、
# 🚨 改寫過的儀器名要當場擋（🚫 不得留到判定那步變成「不在允許清單」，
# ⚠️ 那個理由與「這篇真的用了別的儀器」分不開）、null 收得下（兩個理由因此
# 分得開）、範圍外的那些照樣用論文的用詞。增量恰為 4。
# 第 490 輪：810 → 812。前後對照（n+113 四）：
#   改動前  810 passed／0 failed
#   改動後  812 passed／0 failed
# 新增兩條，測「以契約結局為單位的一致性」（n+190）：🚨 顆粒度不同（一邊拆
# 十筆、一邊記一筆）時標籤零重疊而契約結局完全一致、⚠️ 反向——顆粒度免疫
# 不等於什麼都算一致，真的指向不同就要顯示出來。增量恰為 2。
BASE_PASSED, BASE_FAILED = 814, 0
KNOWN_FAIL = '無（原 test_clopper_pearson_matches_closed_forms 已於第 437 輪依 n+113 四修正）'
# 第 544 輪更正：先前只寫「缺 pyshacl」。⚠️ 操作上沒錯（裝 pyshacl 會帶 rdflib），
# 🚨 但那句話讓人以為只差一個套件，而實測 rdflib 也不在——
# 亦即 gates/shacl.py 與 verify.py 整層在本機都跑不起來，不只是這 26 條測試。
# 🚨 第 490 輪：擁有者核准安裝 rdflib 與 pyshacl（n+8 就此兩者解除）。
# ⚠️ 協調者環境裝完後，那 26 條**第一次真的跑過，全數通過**——
#    **✅ 那一層不是壞的，是從來沒被執行過。**
# 🚨 但兩室環境不同步：執行室裝好之前，那邊仍收集不到。
#    **⚠️ 故基線改為「由實測決定」**，🚫 不寫死一個數字：
#    裝了就跑全部（838），沒裝就照舊排除（812），**兩者各自標明**。
#    🚨 若改成單一基線，其中一室會恆紅或恆綠，而恆紅的閘門等於沒有閘門。
# 第 491 輪：812 → 814（不含 SHACL）／838 → 840（含）。前後對照（n+113 四）：
#   改動前  812／838 passed，0 failed
#   改動後  814／840 passed，0 failed
# 新增兩條，測不一致之裁決（n+192，外部審視第三題）：🚨 每一處不一致都要有
# 成因，沒判完不算裁決過（⚠️ 那份分類比任何一致性分數有價值）；
# ⚠️ 自創的成因要擋，判了不存在的不一致也要擋。增量恰為 2。
SHACL_BASE_PASSED = 840          # 有 rdflib+pyshacl：814 + 26
UNCOLLECTABLE_NOTE = ('%s（🚨 rdflib 或 pyshacl **匯入不了**，pyproject 第 15 行已宣告；'
                      '⚠️ 故本機 gates/shacl.py 與 verify.py 整層跑不起來。'
                      '🚨 匯入不了 ≠ 沒裝——見下一行的實際失敗）'
                      % PYTEST_IGNORE)
UNCOLLECTABLE = UNCOLLECTABLE_NOTE   # run_tests() 依實測改寫


def _has_shacl(exe):
    """這台機器跑不跑得動那一層。🚨 由實際 import 決定，🚫 不憑記載。

    回傳 (可用, 說不出所以然時的原因)。
    🚨 第 579 輪：本室照 n+191 四裝完之後，這一格仍說「不在」——
    ⚠️ 而實情是**兩個套件都在**，只是 rdflib 7.6 需要 pyparsing>=3.1
    （`DelimitedList`），而環境裡是 3.0.9，於是 import 當場拋 AttributeError。
    🚨 「沒裝」與「裝了但匯入壞掉」要做的事完全不同（去裝 vs 去修相依），
    **⚠️ 而這一格原本把兩者說成同一句話**，照著做只會再 pip install 一次。
    ✅ 故失敗時把真正的最後一行錯誤帶出來。
    """
    done = subprocess.run([exe, '-c', 'import rdflib, pyshacl'],
                          capture_output=True, text=True,
                          encoding='utf-8', errors='ignore')
    if done.returncode == 0:
        return True, None
    lines = [ln.strip() for ln in (done.stderr or '').splitlines() if ln.strip()]
    return False, (lines[-1] if lines else '（無錯誤輸出）')


def run_tests():
    """回傳 (passed, failed, 直譯器, 原始摘要行)；找不到可用直譯器則回 None。"""
    global BASE_PASSED, UNCOLLECTABLE
    for exe in ('python3', 'python'):
        probe = subprocess.run([exe, '-c', 'import pytest'], capture_output=True)
        if probe.returncode != 0:
            continue
        shacl, why = _has_shacl(exe)
        BASE_PASSED = SHACL_BASE_PASSED if shacl else BASE_PASSED
        UNCOLLECTABLE = ('✅ 無——rdflib 與 pyshacl 皆在，那 26 條**有跑**'
                         if shacl else UNCOLLECTABLE_NOTE + '\n      🚨 實際失敗：'
                         + why)
        args = [] if shacl else ['--ignore=' + PYTEST_IGNORE]
        # 🚨 第 655 輪：⚠️ 測試那格第四次紅，而直接重跑又是 840 passed——
        # **即它是間歇性的**。第 627 輪的修正給了本室數字，🚫 卻沒有給測試名，
        # 而那正是分辨「哪一條在飄」所缺的東西。
        # ✅ 加 `-rf`：偏離基線時把 `FAILED …` 那一行一起留下來。
        r = subprocess.run([exe, '-X', 'utf8', '-m', 'pytest', '-q', '-rf']
                           + args,
                           cwd=PYTEST_DIR, capture_output=True, text=True,
                           encoding='utf-8', errors='ignore')
        txt = re.sub(r'\x1b\[[0-9;]*m', '', r.stdout or '')
        tail = [l for l in txt.strip().split('\n') if 'passed' in l or 'failed' in l]
        line = tail[-1] if tail else ''
        # 🚨 這一行第一次是用 shell heredoc 寫進來的，而 '\n' 被 shell 吃掉、
        # 斷成了真正的換行——⚠️ **本室自己立的規矩就是「含反斜線的文字不經 shell」**，
        # 這已是第三次違反。✅ 改用檔案編輯工具寫。
        failed_names = [l.strip() for l in txt.splitlines()
                        if l.strip().startswith('FAILED')]
        gp = re.search(r'(\d+) passed', line)
        gf = re.search(r'(\d+) failed', line)
        # 🚨 第 623 輪：⚠️ 原本讀不到摘要行時回 (0, 0, exe, '')——
        # 於是 0 != 基線，測試那格變紅，而印出來的那一行是**空的**。
        # **🚨 「測試失敗」與「讀不到 pytest 的輸出」長得一樣**，
        # 而第 622 輪那次一次性的紅，正是這個樣子。
        # ✅ 故兩者分開：讀不到就說讀不到，並把實際輸出留下來。
        if gp is None and gf is None:
            evidence = (txt.strip().split('\n')[-6:]
                        or ['（pytest 沒有輸出）'])
            stderr = (r.stderr or '').strip().split('\n')[-4:]
            return (None, None, exe,
                    '🚨 讀不到 pytest 的摘要行（returncode=%s）——'
                    '⚠️ 這不是「測試失敗」，是本閘門沒看到結果。'
                    '\n      stdout 末幾行：%s\n      stderr 末幾行：%s'
                    % (r.returncode, evidence, [s for s in stderr if s]),
                    failed_names, [])
        # 🚨 第 655 輪：⚠️ 失敗的測試名必須**回傳出去**——
        # 本室第一版把它留在函式裡，而使用它的地方在模組層，
        # **於是新分支根本執行不到（NameError）**；
        # ✅ 而那是「拿假基線實證它會亮」當場抓到的。
        #
        # 🚨 第 658 輪再加一項：⚠️ 有名字仍不夠——**沒有 traceback 就查不出成因**。
        # ✅ 而閘門每輪本來就跑一次套件，故不必額外重跑：
        # 偏離基線時把輸出末段一併帶出去（🚫 平時不帶，免得每輪洗版）。
        if (gp and int(gp.group(1)) != BASE_PASSED) or (gf and int(gf.group(1))):
            # 🚨 第一版取「末 30 行」——⚠️ 而那多半只有進度點與 warnings：
            # **pytest 的 traceback 印在更前面**，於是節錄對查成因沒用。
            # ✅ 改成優先從 FAILURES 那一段起算。
            lines = txt.splitlines()
            start = next((i for i, l in enumerate(lines)
                          if 'FAILURES' in l and l.strip().startswith('=')),
                         None)
            chosen = (lines[start:start + 40] if start is not None
                      else lines[-30:])
            excerpt = [l.rstrip() for l in chosen if l.strip()]
        else:
            excerpt = []
        return (int(gp.group(1)) if gp else 0,
                int(gf.group(1)) if gf else 0, exe, line.strip(),
                failed_names, excerpt)
    return None


print()
print('=== 測試（🚨 數字須來自實跑）===')
# 🚨 第 627 輪：⚠️ 測試那格第二次一次性地紅，而本室**又**用 tail 截斷了輸出，
# 診斷行**又**被切掉——第 622 輪記下的教訓（不要截斷）本室隔幾輪自己違反。
# **✅ 故改形狀而不是改習慣：截斷保留的是尾巴，就把診斷印在尾巴。**
# ⚠️ 底下這個 list 收集所有紅燈細節，於分隔線**之後**再印一次。
verdict_detail = []
tr = run_tests()
if tr is None:
    print('   🚨 找不到裝有 pytest 的直譯器，🚫 本輪不得回報任何測試數字。')
    verdict_detail.append('🚨 找不到裝有 pytest 的直譯器。')
    t_ok = False
else:
    passed, failed, exe, line, failed_names, excerpt = tr
    # 🚨 passed 為 None ＝ 讀不到摘要行。⚠️ 那不是「測試失敗」，
    # 🚫 而本閘門先前把兩者印成同一種樣子（一個空行加一個紅字）。
    unreadable = passed is None
    t_ok = (not unreadable and passed == BASE_PASSED and failed == BASE_FAILED)
    print('   直譯器 %s｜%s' % (exe, line))
    if unreadable:
        print('   🚨 本輪**沒有測試數字**——⚠️ 不得把它讀成「測試通過」，'
              '🚫 也不得讀成「某條測試壞了」。')
        verdict_detail.append(
            '🚨 讀不到 pytest 摘要行（不是測試失敗）：%s' % line)
    else:
        print('   基線 %d passed／%d failed  %s'
              % (BASE_PASSED, BASE_FAILED, '✅ 相同' if t_ok else '🚨 偏離'))
        if not t_ok:
            verdict_detail.append(
                '🚨 測試數字偏離基線：實得「%s」，基線 %d passed／%d failed。'
                % (line, BASE_PASSED, BASE_FAILED))
            # 🚨 第 655 輪加：⚠️ 沒有測試名就分辨不出「哪一條在飄」。
            verdict_detail.append(
                '🚨 失敗的測試：%s' % (failed_names or ['（pytest 未列出）']))
            # 🚨 第 658 輪：⚠️ 有名字仍不夠，沒有 traceback 就查不出成因。
            for excerpt_line in excerpt:
                verdict_detail.append('   │ %s' % excerpt_line)
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
# 🚨 診斷印在最後：⚠️ 截斷保留尾巴，故這幾行連 tail -3 都躲不掉。
for detail in verdict_detail:
    print('🚨 紅燈細節｜%s' % detail)
sys.exit(0 if ok else 1)
