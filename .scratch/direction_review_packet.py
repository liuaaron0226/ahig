# -*- coding: utf-8 -*-
"""**方向審查資料包**：給外部模型判斷「這個方向對不對」。（第 498 輪）

## 🚨 這支存在的理由

擁有者說：「為什麼我覺得都沒有什麼進展」，並決定請外部模型審查方向。

> **⚠️ 他的感覺是對的，而本檔的第一要務是把那件事講清楚，🚫 不是辯解。**

**🚨 故本檔刻意先列成本、再列產出**，⚠️ 而不是相反——
**因為那個順序才是他實際經歷的順序。**

## 🚫 本檔不做的事

- 🚫 **不粉飾**：⚠️ 若資料包把問題藏起來，那份審查就是廢的。
- 🚫 **不替自己辯護**：✅ 反方論點與正方論點並列，**由審查者判。**
- 🚫 **不放論文內容、不放私有根的東西。**

Run:  python3 .scratch/direction_review_packet.py
"""

import io
import re
import subprocess
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

REPO = Path(__file__).resolve().parents[1]
OUT = REPO / ".scratch" / "direction-review-packet.md"


def _lines(pattern, root):
    total = 0
    for p in (REPO / root).rglob(pattern):
        if "__pycache__" in str(p):
            continue
        try:
            total += len(p.read_text(encoding="utf-8", errors="ignore").splitlines())
        except OSError:
            pass
    return total


def _measured():
    m = {}
    log = subprocess.run(["git", "log", "--format=%cs"], cwd=REPO,
                         capture_output=True, text=True).stdout.split()
    m["commits"], m["start"], m["end"] = len(log), log[-1], log[0]
    from datetime import date
    a = date.fromisoformat(log[-1])
    b = date.fromisoformat(log[0])
    m["days"] = (b - a).days

    m["product"] = _lines("*.py", "ahig/ahig")
    m["tests"] = _lines("*.py", "ahig/tests")
    m["scratch"] = _lines("*.py", ".scratch")
    board = 0
    for name in ("COORDINATION.md", "ahig/COORDINATION.md"):
        p = REPO / name
        if p.exists():
            board += len(p.read_text(encoding="utf-8", errors="ignore"))
    m["board_chars"] = board

    gate = (REPO / ".scratch" / "round_gate.py").read_text(encoding="utf-8")
    m["testcount"] = int(re.search(r"SHACL_BASE_PASSED = (\d+)", gate).group(1))
    m["adrs"] = len(list((REPO / "docs" / "adr").glob("*.md"))) + \
        len(list((REPO / "ahig" / "docs" / "adr").glob("*.md")))
    m["rulings"] = len(set(re.findall(
        r"協調者裁定 n\+(\d+)",
        (REPO / "COORDINATION.md").read_text(encoding="utf-8", errors="ignore")
        + (REPO / "ahig" / "COORDINATION.md").read_text(encoding="utf-8",
                                                        errors="ignore"))))
    return m


TEMPLATE = """\
# AHIG 專案｜方向審查（請你判斷這個方向對不對）

## 0. 先說你看不到什麼，以及請你怎麼回答

你看不到程式碼與論文。下面的數字全部是現算的。

**請你直說。如果你認為這個專案應該大幅縮減、換做法、或乾脆停掉，請直接講。**
**一份不能說「這樣不對」的審查沒有價值。**
看不出來的地方請說「這份資料判斷不了」，不要猜。

## 1. 這個人要什麼

一個非醫學專業、看不懂英文論文的人，想減掉 18.5 公斤脂肪而不掉肌肉。
他請 AI 用系統性文獻回顧的方法，回答他自己的健康問題。

他現在的實際狀況：**體重掉不下去，而且維持不住熱量赤字**。
他先前減下來過一次，那次**肌肉也掉很多**。

## 2. 花了多少（🚨 先看這個）

| | |
|---|---|
| 時間 | **{days} 天**（{start} 至 {end}） |
| git 提交 | **{commits} 次** |
| 產品程式碼 | {product:,} 行 |
| 測試碼 | {tests:,} 行（**{testcount} 條測試全過**） |
| **協調用腳本** | **{scratch:,} 行**（🚨 產品碼的 {ratio:.1f} 倍） |
| 協調看板 | {board_chars:,} 字元 |
| 決策紀錄 | {adrs} 份 ADR、{rulings} 條協調者裁定 |

## 3. 產出了什麼（🚨 對他的健康問題而言）

**一個結論。** 就這一個：

> 針對「情緒性／壓力性進食」的介入，既有的系統性回顧結果多半是零——
> 而且愈新、問得愈精準的回顧，效果愈不顯著。
> 唯一直接測過「某種策略能不能提高熱量赤字維持率」的回顧：**沒有差別。**

**除此之外，他手上沒有任何可以拿來做健康決定的東西。**

主要工作對象是一個叫 B.11 的領域（運動中補碳水對耐力表現），
**而那個領域從一開始就被定義為「校準用」，設計上就不會回答他任何一個問題。**
41 篇論文已全部讀完，但驗收「讀得對不對」的四道門檻只過了一道。

## 4. 這套機器確實抓到了東西（公平起見）

- 一篇論文因為儀器名稱寫法對不上，**整篇被錯誤排除**——它其實完全合格。
- 98 個「符合條件」的項目裡，**4 個宣稱了論文裡根本不存在的數值**。
- 另外 7 個的出處指向「方法」段落，不是它宣稱的那個結果。
- 一整層品質檢查從來沒被執行過（套件沒裝），而沒人發現。

**這些錯誤，{testcount} 條格式測試一個都抓不到。**

## 5. 兩個對立的論點，請你判

**正方**：
直接問 AI「怎麼減脂不掉肌肉」五分鐘就有答案，
**但你無從知道那個答案是不是編的**。這套機器存在的理由就是讓每一句話
都指得回一篇論文的一個位置，而它確實抓到了上面那些錯誤。

**反方**：
**{days} 天、{scratch:,} 行協調腳本，換到一個結論**，
而那個結論的內容是「別人做過，結果多半是零」。
主要投入的領域與他的需求無關。**這個投入報酬率不合理。**

## 6. 請你回答

1. **這個方向對不對？** 如果不對，錯在哪一步——是目標、方法、還是執行順序？
2. **應該砍掉什麼？** 具體到「哪一部分的工作可以停掉而不影響結果」。
3. **如果換你來做**，一個沒有經費、沒有團隊、看不懂英文的人，
   要在合理時間內得到可信的健康建議，你會怎麼做？
4. **「嚴謹」與「有用」在這裡衝突嗎？** 如果衝突，該往哪邊靠？
5. **有沒有一條更短的路**，能保留「每句話都指得回原文」這個性質，
   但不需要造這麼多東西？

## 7. 如果你要看程式碼

告訴我你要看哪一部分，我再貼給你。可看的有：

- 萃取鏈（讀論文 → 清冊 → 範圍判定），約 1,500 行
- 範圍判定的確定性核心
- 每輪跑的檢查閘門
- 契約與 schema 定義

**🚫 不要一次要全部**：加起來 {total:,} 行，貼給你會燒光額度。

## 8. 回答時請注意

- 沒有經費、沒有團隊、沒有領域專家。
- 他**看不懂英文論文**，「自己去讀原文確認」不是可行建議。
- 請用中文回答。
"""


def main():
    m = _measured()
    m["ratio"] = m["scratch"] / m["product"]
    m["total"] = m["product"] + m["tests"] + m["scratch"]
    text = TEMPLATE.format(**m)
    OUT.write_text(text, encoding="utf-8")
    size = len(text)
    print("✅ 已寫出 %s" % OUT)
    print()
    print("   %d 字元 → 約 %.1f–%.1f 千 token" % (size, size / 1500, size / 1000))
    print()
    print("🚨 本檔刻意**先列成本、再列產出**——⚠️ 那是擁有者實際經歷的順序。")
    print("⚠️ 正方與反方並列，**🚫 不替自己辯護**；")
    print("🚨 並明文邀請審查者說「該停掉」——**✅ 不能說停的審查沒有價值。**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
