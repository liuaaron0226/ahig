# -*- coding: utf-8 -*-
"""成稿產生器裡**用打的數字**，逐個登記。

## 🚨 這支存在的理由：我給成稿開的例外，比我以為的大

本 run 的核心紀律是「**每一個數字都經過 `n154.value()`，沒有一個是打字打上去的**」，
而 `n141`（字面數字掃描）**放過所有 `docs/m1-*-report.md`**——
✅ 理由是它們由產生器產生，而產生器會宣告檔案有沒有被手改。

**⚠️ 那個理由假設了一件沒有人查過的事：產生器本身只印現算值。**

🚨 第 473 輪實查：**四支產生器裡有 10 處粗體數字是直接打上去的**，
其中三處**本來就有對應的格**（`ORPHAN_N`＝5、`UNPROBED_PDF`＝0、不可及格數＝18），
⚠️ 另有一處寫「十四道自動檢查」而當時實跑十九道。

> **🚨 例外不是錯的，錯的是「例外從沒被量過範圍」。**
> ⚠️ 一道說「這一區我不看」的檢查，必須有另一道說「這一區裡有什麼」。

## ✅ 判準

掃描各節產生器中**會被寫進成稿的字串**，找 `**數字**`（粗體數字）：

  - ✅ 該行含 `v(...)`／`bound(...)`／`_`開頭之現算函式 → 視為現算，放行
  - 🚨 否則須列於 `ALLOWED`，並附**它為何不能是現算值**的理由

⚠️ **登記理由只有兩種是可接受的**：
  1. **歷史值**——那是某一輪當時的量測，現在已經不同（🚨 現算會抹掉它要講的事）
  2. **非量測**——它是一個推理、一個門檻、一個舉例，本來就沒有來源

🚫 「懶得接線」不是理由。⚠️ 三處本輪即因此被改成現算，而不是登記。

## ⚠️ 本檔抓不到什麼（🚫 不得讀成更強）

- 🚫 **不抓非粗體數字**：⚠️ 甲節四分類表裡的 `169`／`52`／`79` 未加粗，本檔看不見。
  🚨 它們已登記於 `FROZEN_TABLE`，**而那是靠人記得，不是靠這道檢查**。
- 🚫 **不抓文字寫的數**（「十四道」「四篇」）——⚠️ 本輪那一處是用讀的發現的。
- 🚫 **不驗登記的理由對不對**：⚠️ 一個標成「歷史值」而其實可現算的，照樣過。

Run:  python3 .scratch/n174_generator_literals.py
"""

import re
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

GENS = sorted(Path(".scratch").glob("n1[5-7]*_section_*_report.py"))
BOLD = re.compile(r"\*\*([0-9][0-9,]*(?:\.[0-9]+)?)\*\*")
LIVE = re.compile(r"\b(?:v|bound)\(|_[a-z_]+\(\)")

HISTORY = "歷史值"
NOTMEASURE = "非量測"

# 鍵：(產生器檔名, 數字字串)
ALLOWED = {
    ("n159_section_g_report.py", "26"): (
        HISTORY, "補查之前之「版本不明」筆數。🚨 現值為 1（`VER_UNKNOWN`），"
                 "⚠️ 而本句要講的正是「它曾經是 26，而那個 26 誤導過判斷」——"
                 "**🚫 現算會把這句話的主詞抹掉。**"),
    ("n161_section_d_report.py", "4"): (
        NOTMEASURE, "🚨 這是一個**沒有被採納的預測**（照 4／11 外推之估計）。"
                    "⚠️ 它從來不是量測，故無來源可接；"
                    "**✅ 而它必須寫出來，因為本段講的正是「我們拒絕這樣推」。**"),

    # ── 🚨 甲節四分類表：第 425 輪影子批之當時量測 ─────────────────
    # ⚠️ 該次比對讀的是**私有根之各線工作單**，協調者不可及，
    #    **🚫 故無法現算**；其合計 300 已改為現算並設閉合式（見 `_batch()`）。
    # 🚨 登記為歷史值，**而歷史值有一個代價要寫明**：
    #    ⚠️ 若日後工作單改變，這四個數不會跟著動，而合計那道閉合式**也不會叫**
    #    ——因為它比的是 300 對 300，🚫 不是逐格。
    ("n163_section_a_report.py", "169"): (
        HISTORY, "第 425 輪影子批四分類之「已有解釋」數（主線）。"
                 "⚠️ 來源為私有根工作單，🚫 協調者不可及故無法現算。"),
    ("n163_section_a_report.py", "52"): (
        HISTORY, "同上：安全線之「在單內」數。"),
    ("n163_section_a_report.py", "0"): (
        HISTORY, "同上：四分類表中之零格（**沒有解釋的漏口**）。"
                 "🚨 這幾個 0 是本節最強的證據，⚠️ 而它們同樣是那一輪的量測，"
                 "**🚫 不是現在重跑出來的**——交付當日須由執行室重驗。"),
}

# 🚨 非粗體而仍屬打字之數：本檔看不見，故在此列名並記其來源。
# ⚠️ 這是一份**人維護的清單**，🚫 沒有機器在證明它完整。
FROZEN_TABLE = {
    "n163_section_a_report.py":
        "四分類表之 169／52／47／19／10／3／79（未加粗，本檔掃不到）——"
        "🚨 第 425 輪影子批四分類之當時量測，看板行 1098 起；"
        "⚠️ 其合計 300 已改為由 `SHADOW_CONCORDANT ＋ SHADOW_QUEUED` 現算並設閉合式，"
        "**🚫 而逐格的四個分類數仍是打上去的**。",
}


def scan(text_by_file):
    problems, allowed_hits = [], 0
    for fname, text in text_by_file.items():
        for i, line in enumerate(text.split("\n"), 1):
            s = line.strip()
            if not (s.startswith("A(") or s.startswith('"') or s.startswith('f"')):
                continue
            if LIVE.search(line):
                continue
            for m in BOLD.finditer(line):
                num = m.group(1)
                key = (fname, num)
                if key in ALLOWED:
                    allowed_hits += 1
                    continue
                problems.append(
                    f"🚨 `{fname}` L{i} 有打字的粗體數字 **{num}**，且該行無現算呼叫"
                    "——⚠️ 須改為現算，或登記它為何不能是現算值")
    return problems, allowed_hits


live = {g.name: g.read_text(encoding="utf-8") for g in GENS}
problems, hits = scan(live)

print("=== 產生器中之打字數字 ===")
if problems:
    for p in problems:
        print(f"  {p}")
else:
    print(f"  ✅ {len(GENS)} 支產生器：粗體數字全部由現算產生，"
          f"或已登記為不可現算（{len(ALLOWED)} 筆登記，命中 {hits} 處）")
print()
print("⚠️ **本檔看不見的**（🚫 靠人維護，不靠這道檢查）：")
for f, why in FROZEN_TABLE.items():
    print(f"  · {f}：{why}")

# 🚨 登記而不再出現者須移除，否則涵蓋率被高估。
stale = []
for (fname, num), _ in ALLOWED.items():
    text = live.get(fname, "")
    if f"**{num}**" not in text:
        stale.append((fname, num))
if stale:
    problems.append(f"⚠️ 已登記而不再出現之打字數字：{stale}——🚫 應移除")
    print(f"  🚨 已登記而不再出現：{stale}")

# ── 🚨 反向對照：注入一個未登記之打字粗體數字 ────────────────────────
target = "n163_section_a_report.py"
inj = dict(live)
_before = inj[target]
inj[target] = _before + '\n    A("測試 **987654** 筆")\n'
assert inj[target] != _before, "🚨 注入未生效——🚫 對照無效（n+173 三之教訓）"
ctl, _ = scan(inj)
ok = any("987654" in p for p in ctl)
print()
print(f"反向對照（注入未登記之打字數字）：{'✅ 會被抓到' if ok else '🚨 抓不到'}")
if not ok:
    print("🚨 **本檢查有盲區**——⚠️ 全綠時無法分辨「真的都接線了」與「根本沒在看」")

sys.exit(1 if problems or not ok else 0)
