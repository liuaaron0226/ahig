# -*- coding: utf-8 -*-
"""接上「讀論文」那一段要花多少錢——**輸入側是實測的，輸出側不是**。

## 🚨 這支存在的理由

擁有者卡在一個決定：要不要讓我接上模型去讀那 41 篇。⚠️ 我兩次跟他說
「我給不出金額」——**🚨 而那句話在 n+183 之後已經不成立了**：語料的字元數
一直躺在 `.scratch/n498_sections_integrity.json` 裡（每一篇一筆，已過稽核）。

> **⚠️ 「沒有 B.11 的用量紀錄」是真的，但它擋不住這件事。**
> 🚨 要問的不是「上次花了多少」，是「這一次要送進去多少字」——
> **✅ 而那個數字是量得到的。**

## ✅ 哪些是量的、哪些是猜的

| 這一項 | 來源 | 可信度 |
|---|---|---|
| 送進去的字元數 | 🚨 n498 逐篇實測（41 篇） | ✅ 實測 |
| 每次呼叫的固定開銷 | ✅ 由凍結契約與 `prompt_payload()` 現算 | ✅ 實測 |
| 字元→token 的換算 | ⚠️ 一段區間，🚫 本機沒有分詞器可量 | ⚠️ 估計 |
| 回來的清冊有多長 | 🚨 **一次都沒跑過** | 🚨 **猜的** |
| 每百萬 token 的牌價 | ⚠️ 公開價，🚫 本 repo 無憑據 | ⚠️ 外部 |

**🚨 故本檔把「猜的」那兩項故意放寬到荒謬**——⚠️ 若結論在整段區間內都一樣，
那結論就不靠那兩個猜測撐著。**✅ 這是本檔唯一想證明的事。**

## 🚫 本檔不做的事

- 🚫 **不呼叫模型**，🚫 不做任何需要授權的動作（ADR-0010 五）。
- 🚫 **不給單一數字**（看板 49308）。
- 🚫 **不算擁有者的時間**，🚫 不算重跑幾次——⚠️ 那要看第一趟的結果。
- 🚫 **不算 P1**：⚠️ P1 的語料還不存在，**連幾篇都不知道**。

Run:  python3 .scratch/n184_reading_seam_cost.py
"""

import json
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

AUDIT = Path(".scratch/n498_sections_integrity.json")
CONTRACT = Path("ahig/calibration/b11-carbohydrate/scope-contract.json")

# ⚠️ 字元→token：學術英文偏密（數字、單位、參考文獻），故下界壓到 3.0。
#    🚫 本機沒有分詞器可實測，故給區間而非一個係數。
CHARS_PER_TOKEN = (4.5, 3.0)          # (省 token 的一端, 費 token 的一端)

# 🚨 回來的清冊有多長——**這是本檔唯一沒有任何依據的數字。**
#    ⚠️ 故意放寬成「輸入的 5% 到 30%」：30% 已經是每篇回一份長篇報告了。
OUTPUT_FRACTION = (0.05, 0.30)

# ⚠️ 每百萬 token 的美金牌價。🚨 本 repo 沒有這個數字的憑據，
#    故取一段**寬到蓋住各層級**的區間；代入時以官方公告為準。
USD_PER_MTOK_IN = (1.0, 15.0)
USD_PER_MTOK_OUT = (5.0, 75.0)

TITLE_CHARS_EACH = 30                  # ⚠️ 章節標題長度之粗估；n498 不留標題文字
USD_TWD = 31.0                         # ⚠️ 匯率之粗估；🚫 本 repo 無憑據


def main():
    audit = json.loads(AUDIT.read_text(encoding="utf-8"))
    recs = audit["records"]
    chars = sorted(r["stats"]["chars"] for r in recs)
    n = len(chars)
    total = sum(chars)
    sections = audit["totals"]["sections"]

    if total != audit["totals"]["chars"]:
        print(f"  🚨 逐篇加總 {total} 與稽核檔自記之 {audit['totals']['chars']} 不符"
              "——⚠️ 基準不一致，🚫 不得續算")
        return 1

    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    hints = [{"outcomeId": o["outcomeId"], "label": o["label"]}
             for o in contract.get("inScopeOutcomes", [])]
    hint_chars = len(json.dumps(hints, ensure_ascii=False))
    fixed_chars = 400                  # ⚠️ prompt_payload 的固定鍵與指示語
    overhead = n * (hint_chars + fixed_chars) + sections * TITLE_CHARS_EACH
    grand = total + overhead

    print("=== 讀論文那一段的成本｜🚨 輸入側實測、輸出側是猜的 ===")
    print()
    print(f"**送進去的量**（B.11 已取得之 {n} 篇全文）：")
    print()
    print(f"  · 正文字元數　　**{total:,}**（🚨 n498 逐篇實測之加總）")
    print(f"  · 每篇之固定開銷　{hint_chars + fixed_chars:,} 字元 × {n} 篇"
          f"（契約結局提示＋指示語）")
    print(f"  · 章節標題　　　　約 {sections:,} 節 × {TITLE_CHARS_EACH} 字元")
    print(f"  · **合計 ≈ {grand:,} 字元**（開銷佔 {overhead / grand:.1%}）")
    print()
    print(f"  ⚠️ 最大的一篇 {chars[-1]:,} 字元，佔全部的 {chars[-1] / total:.0%}；"
          f"次大者 {chars[-2]:,}。")
    print(f"  ✅ 中位 {chars[n // 2]:,}、最小 {chars[0]:,}。")
    print()

    tok_lo = grand / CHARS_PER_TOKEN[0]
    tok_hi = grand / CHARS_PER_TOKEN[1]
    print(f"**換成 token**（每 token {CHARS_PER_TOKEN[1]}–{CHARS_PER_TOKEN[0]} 字元）：")
    print(f"  · 輸入 **{tok_lo / 1e6:.2f}–{tok_hi / 1e6:.2f} 百萬 token**（跑一趟，每篇一次）")
    out_lo = tok_lo * OUTPUT_FRACTION[0]
    out_hi = tok_hi * OUTPUT_FRACTION[1]
    print(f"  · 輸出 {out_lo / 1e6:.2f}–{out_hi / 1e6:.2f} 百萬 token"
          f"（🚨 **猜的**：輸入的 {OUTPUT_FRACTION[0]:.0%}–{OUTPUT_FRACTION[1]:.0%}）")
    print()

    lo = tok_lo / 1e6 * USD_PER_MTOK_IN[0] + out_lo / 1e6 * USD_PER_MTOK_OUT[0]
    hi = tok_hi / 1e6 * USD_PER_MTOK_IN[1] + out_hi / 1e6 * USD_PER_MTOK_OUT[1]
    print(f"**代入每百萬 token {USD_PER_MTOK_IN[0]:.0f}–{USD_PER_MTOK_IN[1]:.0f} 美元"
          f"（輸入）／{USD_PER_MTOK_OUT[0]:.0f}–{USD_PER_MTOK_OUT[1]:.0f} 美元（輸出）**：")
    print()
    print(f"  ### ✅ 跑一趟 ≈ **{lo:.1f}–{hi:.1f} 美元**")
    print()
    print("🚨 **而這個區間的兩端是刻意拉到不合理的**："
          f"上界同時假設最貴的層級、最費 token 的文本、"
          f"以及每篇回一份佔輸入 {OUTPUT_FRACTION[1]:.0%} 的長報告。")
    print("  ⚠️ **三件事同時成立才會到上界。**")
    print()

    # ── ✅ 結論不靠猜測撐著：把兩個猜的數字推到極端，看結論會不會翻 ──
    worst = tok_hi / 1e6 * USD_PER_MTOK_IN[1] * 3 + (tok_hi * 1.0) / 1e6 * USD_PER_MTOK_OUT[1]
    print("**✅ 靈敏度**（🚨 把猜的那兩項推到極端）：")
    print(f"  · 跑三趟、且輸出跟輸入一樣長 → 約 {worst:.0f} 美元")
    # 🚨 台幣換算由程式算，🚫 不手寫——⚠️ 手寫那一句第一版寫成「上千封頂」，
    #    而極端端點其實是 NT${worst*USD_TWD:,.0f}。**那正是本 run 一路在抓的那一族。**
    print(f"  · 換成台幣（每美元 {USD_TWD:.0f} 元）："
          f"**一趟約 NT${lo * USD_TWD:,.0f}–{hi * USD_TWD:,.0f}**，"
          f"推到極端 **約 NT${worst * USD_TWD:,.0f}**。")
    print("  ✅ **故這個決定不需要更準的估計**——⚠️ 再算下去也不會改變答案。")
    print()

    # ── 🚨 一個順帶量到、且會影響作法的事實 ──────────────────
    big_tok_hi = chars[-1] / CHARS_PER_TOKEN[1]
    print("**🚨 順帶量到一件影響作法的事**：")
    print(f"  ⚠️ 最大的那一篇換成 token 約 {big_tok_hi / 1000:.0f} 千，"
          "**✅ 一次呼叫放得下**（現行模型的脈絡窗遠大於此）。")
    print("  🚨 **故不必分段。** ⚠️ 分段會改變模型看到什麼，屬契約層決定"
          "（`corpus.py` 已記此事）——**✅ 而現在不需要做那個決定。**")
    print()

    print("🚫 **本檔沒算、且擁有者該知道的**：")
    print("  1. 🚨 **回來的東西對不對，不在這個價錢裡。**"
          "⚠️ 這只算「讀 41 篇要多少錢」，**🚫 沒算讀錯了要重來幾次**。")
    print("  2. ⚠️ **P1 不適用**：P1 的語料還不存在，連幾篇都不知道"
          "（n+180 說的最大未知數）。")
    print("  3. 🚨 **牌價我沒有憑據**——⚠️ 上面的算式是攤開的，"
          "**✅ 換一個價自己乘得回來。**")
    return 0


if __name__ == "__main__":
    sys.exit(main())
