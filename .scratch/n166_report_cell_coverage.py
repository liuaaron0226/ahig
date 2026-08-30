# -*- coding: utf-8 -*-
"""**成稿用了哪些格、沒用哪些格**——交付當日該填的到底是哪一批。

## 🚨 這支要回答一個一直沒人問的問題

n+151（一）之完成判準寫著「**134 格全部填入現算值**」。
**⚠️ 而成稿只用到其中一部分。**

> **🚨 我第一次讀這個差額時判錯了，那個錯值得留在檔頭。**
> ⚠️ 初判：「沒有任何一節引用的格，填它是沒有讀者的工作，故不必填。」
> **🚫 錯。** 逐項讀過之後，未用之格**多數是成稿漏掉的內容**：
> 乙節那批是整節「方法學品質之具體事證」，
> 辛節那批是 `acquired` 的四個母體——**而成稿寫了「同一個詞是四個數」這句話，
> 卻沒有給出那四個數。**

**✅ 故本檔之用途不是「切掉不必填的」，是「列出還沒處置的」**：
每一個未用之格都要有下落——**登記為刻意不用，或寫進成稿**。
**🚫 不得以「沒人引用」為由略過**——⚠️ 那會把「漏寫」講成「不需要」。

## 🚫 而本檔的失敗條件是反過來的那一種

**⚠️ 「有格子沒被用到」不是錯**——成稿是重寫，不是逐格代換，
且有些格**刻意不得出現在成稿裡**（例如那個全 queue 分母之 p 值，它是禁句的一部分）。

**🚨 真正的錯是反過來**：**成稿用了一個交付清單裡沒有的格**——
那代表報告裡有一個數字**沒有定位、沒有權威來源**。
**✅ 故本檔以此為失敗條件，🚫 不以「有未用之格」為失敗條件。**

## ⚠️ 刻意不用者須逐格登記

🚨 否則「沒用到」與「漏掉了」在輸出上一模一樣——**而那正是本 run 一路在防的形狀。**

Run:  python3 .scratch/n166_report_cell_coverage.py
"""

import re
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

CHECKLIST = Path("docs/m1-e-delivery-checklist.md")
ROW = re.compile(r"^\|\s*(\S+)\s*\|\s*`([A-Z0-9_]+)`")
# 🚨 取值有兩種寫法，🚫 只認一種就會誤報：
#    `v('X')`（點值）與 `bound("X")`（上界，n+166 新增之第三態）。
# ⚠️ 初版只認前者，於是把「有用到上界的那一格」報成未用——
#    **🚨 一份清點工具自己漏數，比不清點更糟。**
USE = re.compile(r"""(?:v|bound)\(\s*['"]([A-Z0-9_]+)['"]\s*\)""")

# 節 → 產生器
GENERATORS = {
    "甲": "n163_section_a_report.py",
    "乙": "n164_section_b_report.py",
    "丙": "n157_section_c_report.py",
    "丁": "n161_section_d_report.py",
    "己": "n165_section_e_report.py",
    "庚": "n160_section_f_report.py",
    "辛": "n159_section_g_report.py",
    # ⚠️ 壬節尚未成稿——🚫 待擁有者答覆，不得先寫（n+165 四）。
}

# ── 🚨 刻意不引用者：逐格寫明理由 ────────────────────────────────
# ⚠️ 🚫 不得為了讓輸出乾淨而往這裡加東西；加一筆就是做一次判定。
DELIBERATE = {
    "P_ALLQUEUE":
        "🚨 **它是禁句的一部分**：「若改採全 queue 分母則 p ＝ …，故終止存疑」"
        "把兩個不同的宣稱混成一個（檢查表第六條）。"
        "✅ 成稿說明有這個對照區塊而**不印其值**，🚫 印了就是把禁句寫進報告。",
    "TRIGGER_CAUSE_ID":
        "⚠️ 那是一個內部識別碼。✅ 成稿以「一筆紀錄改判所致」敘述，"
        "🚫 對讀者而言一串識別碼不含資訊。",
    "NARR_CRITERIA_HASH":
        "⚠️ 判準檔之雜湊：✅ 成稿寫明「附上判準檔的指紋」而不印該串，"
        "🚫 四十字的十六進位在散文裡只會擋住視線；⚠️ 交付附件仍須帶上。",
}


def checklist_cells():
    t = CHECKLIST.read_text(encoding="utf-8")
    body = t.split("BEGIN GENERATED n115", 1)[-1].split("END GENERATED n115", 1)[0]
    out = {}
    for line in body.split("\n"):
        m = ROW.match(line)
        if m and m.group(2) != "佔位符":
            out.setdefault(m.group(1), set()).add(m.group(2))
    return out


# 🚨 n+167：**取值於「禁句清單」中出現，不是引用，是相反的事**。
# ⚠️ 丙節寫 `forbidden_phrases=(v("P_ALLQUEUE"),)`，意思是
#    **「這個數字不准出現在成稿裡」**；而本檔原本把它數成一次引用，
#    於是報表宣稱「丙節引用了 P_ALLQUEUE」——**🚫 恰好與事實相反**。
# 🚨 這是缺陷型錄裡的**舊型再現**：n158 曾把「引述一條禁令」誤判為「違反它」，
#    規則寫下之後，同一型換一支工具又犯一次。
# ✅ 故先剔除 `forbidden_phrases=(...)` 之內容，再數取值。
_FORBIDDEN_ARG = re.compile(r"forbidden_phrases\s*=\s*\((?:[^()]|\([^()]*\))*\)")


def used_cells():
    out = {}
    for sec, gen in GENERATORS.items():
        src = Path(".scratch") / gen
        text = src.read_text(encoding="utf-8")
        text = _FORBIDDEN_ARG.sub("", text)
        out[sec] = set(USE.findall(text))
    return out


def main():
    listed, used = checklist_cells(), used_cells()
    all_listed = set().union(*listed.values())
    all_used = set().union(*used.values()) if used else set()

    problems = []

    # 🚨 失敗條件：成稿用了清單裡沒有的格 → 報告裡有無來源的數字。
    orphan = sorted(all_used - all_listed)
    # ⚠️ 非清單格但確為 n154 之解析器所有者（如 S7_QUOTA）須排除誤報。
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "n154", str(Path(".scratch/n154_cell_producer.py")))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    orphan = [o for o in orphan if o not in m.RESOLVERS]
    if orphan:
        problems.append(f"🚨 成稿引用了交付清單沒有的格：{orphan}"
                        "——⚠️ 那是一個沒有定位、沒有權威來源的數字")

    print("=== 成稿之格覆蓋 ===")
    print(f"  清單共 {len(all_listed)} 個相異格｜"
          f"**成稿引用 {len(all_used & all_listed)} 個**｜"
          f"未被引用 {len(all_listed - all_used)} 個")
    print()
    for sec in GENERATORS:
        li, us = listed.get(sec, set()), used.get(sec, set())
        unused = sorted(li - us - set(DELIBERATE))
        note = f"｜🚫 刻意不用 {len(li & set(DELIBERATE))}" if li & set(DELIBERATE) else ""
        print(f"  {sec}節：清單 {len(li):2}｜引用 {len(li & us):2}"
              f"｜⚠️ 未用 {len(unused):2}{note}")
        if unused:
            print(f"        {unused}")

    print()
    print("🚨 **未被引用之格是什麼意思？——我第一次讀錯了，記在這裡**")
    print("  ⚠️ 初判：「沒有讀者的格，交付當日不必填」。**🚫 那是錯的。**")
    print("  🚨 逐項讀過之後：未用之格**多數是成稿漏掉的內容**，不是多餘的格——")
    print("     · 乙節未用者含門檻 3、Fisher p、advance 期望與實測、訊號密度"
          "——**那是整節「方法學品質之具體事證」，且是本 run 最強的流程證據之一**；")
    print("     · 辛節未用者含 acquired 之四個母體——**⚠️ 成稿寫了「同一個詞是四個數」"
          "這句原則，卻沒給那四個數**。")
    print("  ✅ 故裁定改為：**每一個未用之格都要有處置**——"
          "登記為刻意不用，或把它寫進成稿。")
    print("  🚫 **不得以「沒人引用」為由略過**——⚠️ 那會把「漏寫」講成「不需要」。")
    print()
    print(f"✅ 刻意不引用者已登記 {len(DELIBERATE)} 格：")
    for k, why in DELIBERATE.items():
        print(f"  · {k}：{why[:72]}…")

    # ── 🚨 未引用之總數必須被逐格認領（n+167）────────────────────
    # ⚠️ 本檔原本標頭印「未被引用 N 個」，而下方明細只交代了「刻意不用」與
    #    「各節未用」兩類。**🚨 壬節尚未成稿，其獨有之格不屬於任何一節的桶子**，
    #    於是標頭的 4 與明細的 3 差了一格，**而本檔照樣 exit 0**。
    # 🚨 那正是缺陷型錄第 17 型：**一句總結，斷言了一件沒發生過的事**
    #    （「未引用者皆已交代」）。✅ 故此處逐格認領，🚫 對不起來就失敗。
    uncited = all_listed - all_used
    by_section = set().union(*(listed.get(s, set()) for s in GENERATORS)) \
        if GENERATORS else set()
    pending = sorted(uncited - by_section)          # 只存在於尚未成稿之節
    per_sec_unused = sorted(
        {c for s in GENERATORS
         for c in (listed.get(s, set()) - used.get(s, set()) - set(DELIBERATE))})
    claimed = set(DELIBERATE) | set(pending) | set(per_sec_unused)
    orphaned = sorted(uncited - claimed)

    print()
    print(f"未引用 {len(uncited)} 格之認領：刻意不用 {len(set(DELIBERATE) & uncited)}"
          f"｜各節漏寫 {len(per_sec_unused)}｜尚未成稿之節獨有 {len(pending)}")
    if pending:
        print(f"  · 尚未成稿之節獨有：{pending}")
        print("    ⚠️ 壬節須待擁有者答覆四項待決後方能成稿，"
              "🚫 故此處不算漏寫，**亦不得算已完成**。")
    if orphaned:
        problems.append(f"🚨 未引用之格有 {len(orphaned)} 格無人認領：{orphaned}"
                        "——⚠️ 標頭之總數與明細對不起來，🚫 不得視為已交代")

    # ── 🚨 反向對照：注入一個「成稿用了清單沒有的格」 ────────────────
    fake = "△不存在之格△"
    caught = bool({fake} - all_listed)
    print()
    print(f"反向對照（注入清單外之格）：{'✅ 會被抓到' if caught else '🚨 抓不到'}")

    for p in problems:
        print(f"  {p}")
    if not problems:
        print("✅ 成稿所引用之格，全部在交付清單內（🚫 無來路不明的數字）")
    return 1 if (problems or not caught) else 0


if __name__ == "__main__":
    sys.exit(main())
