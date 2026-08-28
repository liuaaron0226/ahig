# -*- coding: utf-8 -*-
"""每輪必做檢查之閘門：n+48 兩道資料衛生 ＋ n+54 三道錨定——以狀態碼回報，壞掉會大聲。

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
- 🚨 抓不到：**不加任何標記、直接寫在中文判讀理由裡的英文題名**
  ——n+80 已載明沒有可靠樣式能把它與本室自己寫的英文說明分開。
  **⚠️ 故本檔通過代表「兩道已知樣式無新增」，不代表「無文獻內容」。**
"""
import io
import re
import subprocess
import sys

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

print()
print('=' * 62)
ok = p1_ok and p2_ok and p3_ok
print('n+48 第一道 %s｜第二道 %s｜n+54 三道 %s'
      % ('✅' if p1_ok else '🚨', '✅' if p2_ok else '🚨', '✅' if p3_ok else '🚨'))
print('⚠️ 本檔通過只代表三組已知樣式無新增；🚨 未加標記之英文題名不在涵蓋範圍內。')
sys.exit(0 if ok else 1)
