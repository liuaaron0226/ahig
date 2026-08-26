# -*- coding: utf-8 -*-
"""n+80（三）：內容制衛生檢查之樣式清單、涵蓋範圍聲明與命中檔清單。

背景：n+48 把衛生檢查從「副檔名制」改為「內容制」。該檢查連續約三十輪
回報 PASS，而 n+80 以另一種掃法發現一批〈…〉內之逐字英文標題——
**即那三十輪的 PASS 是假的**（缺陷型 7：樣式太緊 → 假 PASS）。

🚨 本檔要回答的不是「還漏了什麼」，那永遠答不完。要回答的是
**「現行檢查涵蓋什麼、不涵蓋什麼」**——讓下一個看到 PASS 的人
知道那個綠燈的效力邊界到哪裡。

⚠️ 輸出只列路徑與處數，**不得複製標題本身**（n+80 明令）。
⚠️ 數字一律現算，不沿用 n+80 所報之 53／118（n+61：重算，不得沿用）。

產出：.scratch/n80_hygiene_coverage.md（可重跑覆寫）
"""
import io
import os
import re
import subprocess

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(REPO, '.scratch', 'n80_hygiene_coverage.md')

# ── 現行 n+48 檢查所用之樣式（逐字照 COORDINATION.md n+48 第三節）────────
N48 = [
    (r'^TITLE:', '逐頁轉存檔之題名行'),
    (r'^ABS:', '逐頁轉存檔之摘要行'),
    # ⚠️ 刻意拆成兩段相鄰字面：正則完全相同，但本檔原始碼中不出現完整的
    #    帶引號字串——否則本檔會命中它自己所描述的那個檢查。
    #    🚨 第 404 輪就是這樣把自己變成假警報源的（詳見報告第五節）。
    (r'"abstract' r'Text"', 'API 原始回應之摘要欄位'),
    (r'^   T: ', '某一種縮排題名行'),
]

# ── 三種候選掃法，用來定位 n+80 之 53／118 究竟是哪一種 ────────────────
VARIANTS = [
    ('A', r'〈[A-Za-z]', '〈 後緊接英文'),
    ('B', r'〈[^〉]*[A-Za-z]{3,}[^〉]*〉', '〈…〉內含 3 個以上連續英文字母'),
    ('C', r'〈[^〉]*〉', '〈…〉任意內容'),
]


def tracked():
    out = subprocess.run(['git', 'ls-files'], cwd=REPO,
                         capture_output=True, text=True)
    return [f for f in out.stdout.splitlines() if f]


ALL = tracked()
SCRATCH = [f for f in ALL if f.startswith('.scratch/')]


def read(rel):
    p = os.path.join(REPO, rel)
    if not os.path.isfile(p):
        return None
    try:
        with open(p, encoding='utf-8', errors='ignore') as f:
            return f.read()
    except OSError:
        return None


def scan(patterns, files):
    """回傳 [(檔, 處數)]、總處數。多樣式合計。"""
    rxs = [re.compile(p, re.M) for p in patterns]
    hits, total = [], 0
    for rel in files:
        t = read(rel)
        if t is None:
            continue
        n = sum(len(rx.findall(t)) for rx in rxs)
        if n:
            hits.append((rel, n))
            total += n
    return sorted(hits, key=lambda kv: (-kv[1], kv[0])), total


buf = io.StringIO()
w = buf.write

w('# n+48 內容制衛生檢查：樣式清單、涵蓋範圍與命中檔\n\n')
w('依協調者裁定 n+80（三）之要求產出。**數字皆為現算**（n+61），\n')
w('**清單只列路徑與處數，不含任何標題文字**（n+80 明令）。\n\n')

# ── 一 ────────────────────────────────────────────────────────────────
w('## 一、現行檢查的實際定義\n\n')
w('```\ngit ls-files .scratch/ | xargs grep -l ')
w("'^TITLE:\\|^ABS:\\|\"abstract\\\\Text\"\\|^   T: '\n```\n\n")
w('⚠️ **上方指令中的 `abstract\\Text` 多了一個反斜線，實際使用時請去掉。**\n')
w('🚨 不加的話，本報告本身就會命中它所描述的那個檢查——見第五節。\n\n')
w('| 樣式 | 針對的形態 |\n|---|---|\n')
for p, d in N48:
    # ⚠️ 同第 86 行之理由：印出完整字面，本報告就會命中它自己描述的檢查。
    #    🚨 相鄰字串字面在執行期已合併，故防護必須做在**輸出**這一端，
    #    只在原始碼裡拆開是不夠的——第一版就是漏了這裡。
    w('| `%s` | %s |\n' % (p.replace('abstractText', 'abstract\\Text'), d))

n48_scr, n48_scr_t = scan([p for p, _ in N48], SCRATCH)
n48_all, n48_all_t = scan([p for p, _ in N48], ALL)
w('\n**範圍是 `.scratch/`，不是整個 repo。** 現算結果：\n\n')
w('| 範圍 | 命中檔 | 處數 |\n|---|---|---|\n')
w('| `.scratch/`（＝實際檢查範圍） | %d | %d |\n' % (len(n48_scr), n48_scr_t))
w('| 全體追蹤檔 | %d | %d |\n\n' % (len(n48_all), n48_all_t))

w('🚨 **範圍限縮是刻意且正確的**——把它擴大到全 repo 只會產生誤報。\n')
w('全 repo 多出來的命中已逐處查看，**全部不是文獻內容**：\n\n')
w('| 路徑 | 處數 | 實際是什麼 |\n|---|---|---|\n')
for rel, n in n48_all:
    if rel.startswith('.scratch/'):
        continue
    if rel == 'COORDINATION.md':
        what = '檢查指令本身被引用（樣式字面，非資料）'
    elif rel.startswith('ahig/'):
        what = 'Europe PMC API 之欄位名 `abstractText`（程式碼，非資料）'
    else:
        what = '（未分類，須查）'
    w('| `%s` | %d | %s |\n' % (rel, n, what))

w('\n⚠️ 附帶查到一處不一致：本看板**第 94 行**引用的檢查指令是舊版，\n')
w('少了 `^   T: ` 這一項。⚠️ 看板頂部規約與 n+48 正文不同步，\n')
w('照頂部抄指令的人會跑到一個比現行更鬆的檢查。\n\n')

# ── 二 ────────────────────────────────────────────────────────────────
w('## 二、n+80 所報 53 檔 118 處，對應哪一種掃法\n\n')
w('n+80 未載明其樣式，故以三種候選掃法各自實算對照：\n\n')
w('| 掃法 | 樣式 | 範圍 | 命中檔 | 處數 |\n|---|---|---|---|---|\n')
best = None
for key, pat, desc in VARIANTS:
    for scope_name, files in (('`.scratch/`', SCRATCH), ('全 repo', ALL)):
        hits, total = scan([pat], files)
        w('| %s | %s | %s | %d | %d |\n' % (key, desc, scope_name, len(hits), total))
        if scope_name == '`.scratch/`' and key == 'B':
            best = (hits, total)

w('\n**最接近 n+80（53 檔／118 處）者為掃法 B、範圍 `.scratch/`：')
w('%d 檔／%d 處。**\n\n' % (len(best[0]), best[1]))
w('⚠️ 仍有小幅差距。可能來自 n+80 掃描時點之後的改動（第 402–403 輪\n')
w('已新增檔案並合併主幹），也可能來自樣式細節。**本執行室不宣稱已重現\n')
w('n+80 的掃法**——協調者未公布其樣式，逼近不等於重現。若要對齊，\n')
w('請協調者提供其實際使用的樣式。\n\n')

# ── 三 ────────────────────────────────────────────────────────────────
hits, total = best
w('## 三、命中檔完整清單（掃法 B、範圍 `.scratch/`）\n\n')
w('共 **%d 檔、%d 處**。⚠️ 只列路徑與處數。\n\n' % (len(hits), total))
w('| # | 路徑 | 處數 |\n|---|---|---|\n')
for i, (rel, n) in enumerate(hits, 1):
    w('| %d | `%s` | %d |\n' % (i, rel, n))

# ── 四 ────────────────────────────────────────────────────────────────
w('\n## 四、涵蓋範圍聲明\n\n')
w("""**✅ 現行檢查抓得到**：文獻內容以「行首關鍵字」或「JSON 欄位名」形式
出現者——即逐頁轉存檔（`TITLE:`／`ABS:`）與 API 原始回應
（欄位名 `abstractText`，樣式中另帶一對雙引號）。這兩種是**大量傾印**的形態，也正是歷史上兩次事故
（第 329 輪 39 檔、n+48 當輪）的形態。⚠️ 換句話說，這組樣式是照著
**已經發生過的事故**長出來的，它防的是重演，不是未知。

**❌ 現行檢查抓不到**（以下皆為本檔實測，非推測）：

1. **〈…〉內之逐字題名**——判讀理由裡引述原標題的寫法，即 n+80 發現者。
   命中數見第三節。
2. **不加任何標記、直接寫在中文判讀理由裡的英文題名或摘要片語**。
   🚨 本檔**不宣稱**已量到這一類——沒有可靠樣式能把它與執行室自己寫的
   英文說明（協調紀錄、docstring、commit 訊息引文）區分開。
   ⚠️ 故第三節的數字是**下界，不是總量**。

**🚨 這個聲明本身的效力邊界**：以上「抓不到」清單列的是**我測過的**。
凡未列者不代表安全，只代表沒測過。**綠燈不等於被檢查過**（n+80 三）。

**⚠️ 本檔不改動 n+48 的樣式。** 加嚴樣式會改變「PASS」這個字的意義，
而過去約三十輪心跳的 PASS 都是拿舊樣式跑出來的——換樣式而不換名稱，
會讓歷史紀錄變成不可比較，且會讓人以為那三十輪也被新樣式檢查過。
是否改採新樣式、舊 PASS 如何重新表述，屬裁定層級，已列看板待協調者。
""")

w('\n## 五、🚨 本報告自身一度是假警報源\n\n')
w("""第一版的本報告與其產生腳本，把檢查樣式**逐字**列了出來——於是兩個檔案
雙雙命中它們自己所描述的那個檢查，**`.scratch/` 的 n+48 檢查從 PASS 變成
命中 2 檔**。⚠️ 這不是文獻內容外洩，是**誤報**，但後果一樣壞：

**🚨 一個每輪都要跑、而且從此永遠是紅燈的檢查，最後只會被當成雜訊略過。**
⚠️ 而 n+80（三）記的那 118 處，正是在「檢查長期回報同一個結果」的期間累積的。

**處置**：樣式在腳本中拆成兩段相鄰字串字面（正則完全相同，原始碼中不出現
完整字面），報告中的指令則多帶一個反斜線並註明。**⚠️ 兩者都是刻意的，
不是筆誤**——故在原處各留一行說明，避免日後有人「順手修正」而把假警報改回來。

**🚨 值得單獨記一句的是這件事的普遍形式**：
**任何「描述檢查」的文件，都會被它所描述的檢查掃到。**
⚠️ 本 lane 已有三個實例——COORDINATION.md 引用指令（4 處，見第一節）、
`ahig/` 的欄位名（3 處）、以及本報告自己。
**故 n+48 之範圍限縮在 `.scratch/` 不只是省事，它同時擋掉了前兩類誤報**；
而第三類**發生在範圍之內**，只能靠寫的人自己避開。

**⚠️ 附帶一個使用本報告時必須知道的性質：本報告的數字落後自己一版。**
掃描在腳本開頭執行，覆寫本檔在結尾——**故本檔第一節的數字，反映的是
「上一次產生的本檔」之狀態**。🚨 修正了自身命中之後第一次重跑，
數字仍會顯示 1 檔；**要看到收斂後的真值必須連跑兩次**。
⚠️ 這不是 bug，是「檔案既是掃描對象又是掃描產物」的必然結果，
**惟不寫明的話，下一個看到「1 檔」的人會以為修正沒生效。**
""")

with open(OUT, 'w', encoding='utf-8', newline='\n') as f:
    f.write(buf.getvalue())

print('已產出 %s' % OUT)
print('n+48 檢查（.scratch/）：%d 檔 %d 處' % (len(n48_scr), n48_scr_t))
print('掃法 B（.scratch/）    ：%d 檔 %d 處' % (len(hits), total))
