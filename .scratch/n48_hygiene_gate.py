# -*- coding: utf-8 -*-
"""n+48 兩道資料衛生檢查之閘門——以狀態碼回報，壞掉會大聲。

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

## 本檔之涵蓋範圍聲明（n+80 三之紀律）

- ✅ 抓得到：兩道已公布樣式所涵蓋者，且**工具失效時會以非零狀態碼中止**。
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


def tracked(prefix='.scratch/'):
    out = subprocess.run(['git', 'ls-files', prefix],
                         capture_output=True, text=True, encoding='utf-8')
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

print('=== n+48 資料衛生閘門｜範圍 git ls-files .scratch/（%d 檔）===' % len(files))
print()

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

print()
print('=' * 62)
ok = p1_ok and p2_ok
print('第一道 %s｜第二道 %s' % ('✅' if p1_ok else '🚨', '✅' if p2_ok else '🚨'))
print('⚠️ 本檔通過只代表兩道已知樣式無新增；🚨 未加標記之英文題名不在涵蓋範圍內。')
sys.exit(0 if ok else 1)
