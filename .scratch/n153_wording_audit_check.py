# -*- coding: utf-8 -*-
"""檢查表逐節套用紀錄之**結構完備性**檢查。

## 🚨 這支只做一件事，而那件事很窄

`docs/m1-wording-audit.md` 是**我的判斷**：九節 × 十二條，每格寫該節之處置。
**⚠️ 本檔🚫 不判那些判斷對不對**——那要人讀。

**✅ 本檔證明的是：我沒有跳格、沒有留白、沒有用打勾充數。**

> **🚨 為什麼這值得一支腳本**：n+151 查出該項是交付盤點七項中
> **唯一連產物都沒有**的一項。而「有產物」與「產物是完整的」是兩件事——
> **⚠️ 一份缺了二十格的矩陣，讀起來和完整的一模一樣。**

## 判準

| 查什麼 | 為何 |
|---|---|
| 九節 × 十二條 ＝ 108 格齊備 | 缺格即等於那一節那一條沒被套過 |
| 無空格 | 空格與「不適用」不同：後者是判斷，前者是漏掉 |
| **無僅打勾者** | 🚨 打勾不含資訊；n+151 明訂「打勾不算」 |
| 條次與檢查表逐字對應 | ⚠️ 檢查表若增為十三條，本矩陣須跟著長，🚫 不得靜默落後 |

## 涵蓋範圍聲明（n+80 三）

- ✅ 抓得到：缺格、空格、打勾、條數與檢查表不符。
- 🚨 抓不到：**格子裡寫的是不是真的**。⚠️ 一格寫「不適用」而其實適用，本檔照樣放行。
  **🚫 故本檔通過只代表「每一格都有人寫了字」，不代表那些字是對的。**

Run:  python3 .scratch/n153_wording_audit_check.py
"""

import re
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

AUDIT = "docs/m1-wording-audit.md"
CHECKLIST = "docs/m1-wording-checklist.md"
SECTIONS = ["甲", "乙", "丙", "丁", "己", "庚", "辛", "壬", "檢"]

ROW = re.compile(r"^\|\s*([一二三四五六七八九十]+)\s+(.+?)\s*\|\s*(.*?)\s*\|\s*$")
# 🚨 「僅打勾」之樣式：只有記號與空白，或短到不可能含判斷。
TICK_ONLY = re.compile(r"^[✅⚠️🚫🚨\s✓×—\-]*$")
MIN_CHARS = 12


def parse(text):
    out, sec = {}, None
    for line in text.split("\n"):
        m = re.match(r"^## (\S+)節\s*$", line)
        if m:
            sec = m.group(1)
            out[sec] = []
            continue
        m = ROW.match(line)
        if m and sec and m.group(1) != "條":
            out[sec].append((m.group(1), m.group(3)))
    return out


def run(text, label):
    problems = []
    got = parse(text)

    n_rules = len(re.findall(r"^## [一二三四五六七八九十]+、",
                             Path(CHECKLIST).read_text(encoding="utf-8"), re.M))
    missing_secs = [s for s in SECTIONS if s not in got]
    if missing_secs:
        problems.append(f"缺節：{missing_secs}")
    for sec in SECTIONS:
        cells = got.get(sec, [])
        if len(cells) != n_rules:
            problems.append(f"{sec}節 {len(cells)} 格，應為 {n_rules} 格")
        for rule, body in cells:
            if not body:
                problems.append(f"{sec}節「{rule}」為空格")
            elif TICK_ONLY.match(body) or len(body) < MIN_CHARS:
                problems.append(f"{sec}節「{rule}」僅打勾或過短：{body!r}")

    total = sum(len(v) for v in got.values())
    print(f"=== {label} ===")
    print(f"  節 {len(got)}／{len(SECTIONS)}｜檢查表 {n_rules} 條｜"
          f"格 {total}／{len(SECTIONS) * n_rules}")
    if problems:
        for p in problems[:12]:
            print(f"  🚨 {p}")
        if len(problems) > 12:
            print(f"  …另 {len(problems) - 12} 項")
    else:
        print("  ✅ 結構完備（🚫 不代表內容正確——見涵蓋範圍聲明）")
    return problems


real = run(Path(AUDIT).read_text(encoding="utf-8"), "實際文件")

# ── 🚨 反向對照：三種注入，各對應一種漏法 ────────────────────────────
# ⚠️ 依 n+131 三：注入物須落在本檢查有能力判定的範圍內。
src = Path(AUDIT).read_text(encoding="utf-8")
first = ROW_LINE = next(l for l in src.split("\n") if ROW.match(l) and "不適用" in l)
inj = src.replace(first, "| " + ROW.match(first).group(1) + " " +
                  ROW.match(first).group(2) + " | ✅ |", 1)          # 僅打勾
inj = inj.replace("## 壬節", "## 壬節-已改名", 1)                     # 缺節
lines = inj.split("\n")
for i, l in enumerate(lines):                                        # 刪一格
    if ROW.match(l) and l is not first and "|---|" not in l:
        del lines[i]
        break
control = run("\n".join(lines), "反向對照（注入：僅打勾／缺節／缺格）")

kinds = {("僅打勾" in p) * 1 or ("缺節" in p) * 2 or ("格，應為" in p) * 3
         for p in control}
ok = {1, 2, 3} <= kinds
print()
print(f"反向對照：抓到 {len(control)} 項，涵蓋三型 → "
      f"{'✅ 本檢查會失敗' if ok else '🚨 本檢查有盲區'}")
sys.exit(1 if real or not ok else 0)
