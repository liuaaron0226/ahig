# -*- coding: utf-8 -*-
"""P1 要花多久——**以 B.11 的實測時間為基準，🚫 不憑印象**。

## 🚨 這支存在的理由

ADR-0011 說「工時模型改以 P1–P4 重估」。**⚠️ 那件事從未做過**
（看板行 838／1102 兩度記為「後續巡檢輪消化」，而後續巡檢輪都在磨 M1）。
🚨 擁有者第 479 輪直接問了，故本檔補上。

## ✅ 方法：不估，先量

⚠️ 唯一可信的基準是 **B.11 自己走過一遍的實測時間**，而那可由 git 現算：
各階段之關鍵產物**第一次出現**的時刻。

> **🚨 而「總共 15 天」不能直接套到 P1**——⚠️ 其中有一段是**在造機器**，
> **✅ 而 P1 用的是同一台機器，不必再造一次。**
> 故本檔把兩者分開：**造機器的時間（一次性）vs 跑一遍的時間（每個領域都要）**。

## 🚫 本檔不做的事

- 🚫 **不給單一數字**（看板 49308：敘述式估計不得以單一數字呈現）——⚠️ 一律給區間。
- 🚫 **不估萃取階段**：🚨 **它一次都沒跑過**，⚠️ 沒有任何實測可以外推。
  **✅ 「不知道」就寫不知道**，🚫 不以「應該和取得差不多」帶過。
- 🚫 **不估 P1 的候選池大小**：⚠️ 那要等搜尋跑過才知道。
  🚨 而篩選成本幾乎全由池子大小決定——**故最大的未知數在這裡**。

Run:  python3 .scratch/n180_p1_effort_estimate.py
"""

import subprocess
import sys
from datetime import datetime

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

# 階段 → (辨識用檔名片段, 這一格代表什麼)
STAGES = [
    ("search-contract.json", "契約凍結（起點）"),
    (None, "篩選機器最後一次改動（造機器結束）"),      # 🚨 見 BUILD_MODULES
    ("n78_termination_evidence.json", "篩選跑完並留下終止證據"),
    ("m1_step2_calibration_set.json", "校準集抽出"),
    ("m1_step3_backfill.json", "全文取得（含補抽）完成"),
]

# 🚨 造機器何時結束＝**這些模組最後一次被改動**的時刻。
# ⚠️ 本檔第一版寫的是 `statistical_termination.py` 之**首次出現**，
#    而標籤寫的是「最後一次改動」——**🚫 標籤與取法不一致**，
#    於是造機器只算了 0.4 天，區間塌成 15–15，看起來像個答案而其實沒有內容。
# 🚨 那正是本 run 一路在抓的那一族（取的東西不是那句話依賴的東西），
#    **⚠️ 而這次是在「量自己要花多久」的腳本裡。**
BUILD_MODULES = ["screening.py", "screening_driver.py", "llm_second_review.py",
                 "active_learning.py", "candidates.py", "runner.py",
                 "statistical_termination.py"]


def _path(frag):
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True).stdout
    hits = [l for l in out.split("\n") if l.endswith("/" + frag) or l == frag]
    return hits[0] if hits else None


def _first_seen(path):
    """該檔第一次進入版控之時刻。🚨 用 --diff-filter=A 取新增那一筆。"""
    out = subprocess.run(
        ["git", "log", "--format=%cI", "--diff-filter=A", "--", path],
        capture_output=True, text=True).stdout.strip().split("\n")
    return datetime.fromisoformat(out[-1]) if out and out[-1] else None


def _build_end():
    """篩選機器最後一次改動之時刻——🚨 取各模組**最後一筆**提交之最大值。"""
    times = []
    for frag in BUILD_MODULES:
        p = _path(frag)
        if not p:
            continue
        out = subprocess.run(["git", "log", "--format=%cI", "-1", "--", p],
                             capture_output=True, text=True).stdout.strip()
        if out:
            times.append(datetime.fromisoformat(out))
    return max(times) if times else None


def main():
    print("=== P1 工時估算｜🚨 基準＝B.11 實測，🚫 非印象 ===")
    print()
    marks = []
    for frag, label in STAGES:
        if frag is None:
            t = _build_end()
            if t is None:
                print("  🚨 找不到篩選模組——⚠️ 基準不完整，🚫 不得續算")
                return 1
        else:
            p = _path(frag)
            if not p:
                print(f"  🚨 找不到 {frag}——⚠️ 基準不完整，🚫 不得續算")
                return 1
            t = _first_seen(p)
        marks.append((t, label))

    # 🚨 時間軸必須遞增。⚠️ 若造機器結束晚於篩選跑完，
    #    表示機器在跑的期間仍在改——**那時「造」與「跑」分不開，🚫 不得硬分。**
    for a, b in zip(marks, marks[1:]):
        if b[0] < a[0]:
            print(f"  🚨 時間軸不遞增：「{a[1]}」晚於「{b[1]}」")
            print("  ⚠️ 表示造機器與跑篩選**在時間上重疊**，"
                  "**🚫 故本檔的「造 vs 跑」拆法在此不成立**，不得給區間。")
            return 1

    t0 = marks[0][0]
    print("**B.11 實測時間軸**（自契約凍結起算）：")
    print()
    for t, label in marks:
        d = (t - t0).total_seconds() / 86400
        print(f"  第 {d:5.1f} 天  {label}")
    print()

    build = (marks[1][0] - marks[0][0]).total_seconds() / 86400
    screen = (marks[2][0] - marks[1][0]).total_seconds() / 86400
    draw = (marks[3][0] - marks[2][0]).total_seconds() / 86400
    acq = (marks[4][0] - marks[3][0]).total_seconds() / 86400
    total = (marks[4][0] - marks[0][0]).total_seconds() / 86400

    print("**拆成「造機器」與「跑一遍」**：")
    print()
    print("| 這一段 | B.11 花了 | P1 要不要再花一次 |")
    print("|---|---|---|")
    print(f"| 造篩選機器 | {build:.1f} 天 | ✅ **不用**——同一台機器 |")
    print(f"| 跑篩選 | {screen:.1f} 天 | 🚨 **要**，且幾乎全看池子多大 |")
    print(f"| 抽校準集 | {draw:.1f} 天 | ⚠️ 要，**而這段多半是我在覆核，不是機器在跑** |")
    print(f"| 取全文 | {acq:.1f} 天 | ✅ 要，但很快（實測不到兩小時） |")
    print(f"| **合計** | **{total:.1f} 天** | |")
    print()

    lo = screen + draw + acq
    hi = total
    print(f"**✅ 故 P1 之對應區間：約 {lo:.0f}–{hi:.0f} 天**")
    print(f"  · 下界 {lo:.0f} 天＝**完全不用造機器、且一切照 B.11 一樣順**")
    print(f"  · 上界 {hi:.0f} 天＝**等於重走 B.11 全程**（含造機器那一段）")
    print()
    print("🚨 **而我已經知道下界不會成立**：")
    print("  ⚠️ P1 開工第一個小時就撞到「契約 schema 容不下三項判準」"
          "（`scope-extensions-required.md`）——")
    print("  **🚨 換一個題目就會冒出 B.11 沒遇過的事，而那正是 B.11 存在的理由。**")
    print()
    print("🚫 **這個區間不含兩件事，且兩件都不小**：")
    print("  1. **萃取階段（M1 第四步）**——🚨 **一次都沒跑過**，"
          "⚠️ 沒有實測可外推，**✅ 我不知道，就寫不知道**。")
    print("  2. **擁有者核准契約所需的時間**——⚠️ 那不在我這邊。")
    print()
    print("⚠️ **最大的未知數是池子大小**：篩選成本幾乎全由它決定，"
          f"而 B.11 那 {screen:.0f} 天對應的是約九千筆。")
    print("  **✅ 而池子大小是可以便宜量出來的**——"
          "🚨 **先只跑搜尋、不跑篩選**，就能知道 P1 有多少筆，"
          "⚠️ 那一步的成本以小時計，**卻能把最大的未知數變成一個實測值**。")
    print()
    print("🚫 **本檔未量之成本：模型呼叫的費用。**"
          "⚠️ 本 repo 沒有留下 B.11 的用量紀錄，🚨 故我給不出金額——"
          "**✅ 而那正是需要擁有者決定的那一項**（ADR-0010 五）。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
