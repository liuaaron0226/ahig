# -*- coding: utf-8 -*-
"""產生**己節成稿**：`docs/m1-e-delivery-report.md`。

## 🚨 這一節的讀者不是擁有者

其餘七節講「我們做了什麼、發現了什麼」；
**⚠️ 本節講「交付當天要做什麼」——它的讀者是那天執行的人。**

**🚫 若不在節首寫明這件事**，擁有者會以為那是一份交給他的待辦清單。

## ⚠️ 本節最容易被寫成的謊

盤點七項裡只有一項是機器可驗的。
**🚨 而其餘十四道機檢每輪全綠**——那很容易被寫成「都驗過了」。

> **⚠️ 十四道全綠證明的是「該跑的跑了」，
> 🚫 不是「該做的都做了」。**

**✅ 故本節必須把三態並列**：可驗／半可驗／不可驗，
**🚫 且不得因為前者全綠就把後兩者說成就緒。**

Run:  python3 .scratch/n165_section_e_report.py
"""

import datetime as _dt
import importlib.util
import re
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

OUT = Path("docs/m1-e-delivery-report.md")
CHECKLIST = Path("docs/m1-e-delivery-checklist.md")


def _load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(Path(path)))
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


_n154 = _load("n154", ".scratch/n154_cell_producer.py")
_n151 = _load("n151", ".scratch/n151_delivery_readiness.py")
lint = _load("n158", ".scratch/n158_report_lint.py")


def v(name):
    return f"{_n154.value(name)}"


def _inaccessible():
    """權威來源不可及之格數——🚨 自清單現數，🚫 不打字（n+174）。

    ⚠️ 本句原寫死 **18**。那個數字對，**而它會停在對的地方不動**：
    🚨 交接檔補齊或新增不可及格時，成稿仍會說 18。
    """
    n = len(re.findall(r"^\| \S+ \| `[A-Z0-9_]+` \| \S+ \| 不可及 \|",
                       CHECKLIST.read_text(encoding="utf-8"), re.M))
    if n == 0:
        raise ValueError("🚨 清單中數不到「不可及」列——⚠️ 表格格式已變，🚫 不得印 0")
    return n


def _n_gates():
    """每輪機檢之支數——🚨 自 `n151` 之單一清單現數，🚫 不打字（n+174）。

    ⚠️ 本節原寫「十四道」。那句話在寫下的當天是對的，
    🚨 而機檢由十四支長到十九支之後，**它仍然說十四**。
    ✅ `n151` 之 `GATES` 已是單一來源，此處併本檔自身一支。
    """
    return len(_n151.GATES) + 1


def _handoff_split():
    """（交接檔已給幾格, 尚無值幾格）——🚨 現數，🚫 不打字。"""
    import json
    rows = _n154.parse_rows()
    inacc = {r["name"] for r in rows if r["srctype"] == "不可及"}
    got = inacc & set(_n154.RESOLVERS)
    return len(got), len(inacc - got)


def must_do():
    """🚨 交付當日必做清單——**自骨架抽取，🚫 不重打**。

    ⚠️ 只取該節之後第一個連續 `- [ ]` 區塊（n+157 三之教訓：抽過頭會掃到檔尾）。
    """
    t = CHECKLIST.read_text(encoding="utf-8")
    block = t.split("## 七、交付當日必做（逐項打勾，不得憑印象）", 1)[1]
    items, cur = [], None
    for l in block.split("\n"):
        if l.startswith("- [ ] "):
            if cur:
                items.append(cur)
            cur = l
        elif cur is not None and l.startswith("      "):
            cur += " " + l.strip()          # 續行
        elif cur is not None and not l.strip():
            continue
        elif cur is not None:
            break
    if cur:
        items.append(cur)
    if len(items) < 10:
        raise ValueError(f"🚨 必做清單只抽到 {len(items)} 項——⚠️ 骨架已變")
    return items


def report():
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    full, half, unver = _n151.counts()
    items = must_do()
    L = []
    A = L.append

    A("# 己：交付當天要做的事")
    A("")
    A(f"**產生時刻：{now}**　"
      "（⚠️ 本節數字於產生當下由權威來源現算，🚫 未沿用任何一輪之值）")
    A("")
    A("> **🚨 這一節和其他七節不一樣：它的讀者是交付當天動手的人。**")
    A("> ⚠️ 其他七節講「我們做了什麼、發現了什麼」；"
      "**這一節講「交出去之前還要做什麼」。**")
    A("> **🚫 它不是一份交給擁有者的事項清單。**")
    A("")
    A("---")
    A("")

    # ── 一 ────────────────────────────────────────────────────
    A("## 一、先講一件最容易被寫成謊的事")
    A("")
    A(f"**一句話**：我們有 **{_n_gates()}** 道自動檢查，每一輪都全部通過。"
      "**🚨 而那證明的是「該跑的跑了」，🚫 不是「該做的都做了」。**")
    A("")
    A(f"交付前還要做的事一共 **{full + half + unver}** 項，"
      "而它們分成三種，**🚫 不可以混為一談**：")
    A("")
    A("| 種類 | 幾項 | 意思 |")
    A("|---|---|---|")
    A(f"| **機器驗得了** | **{full}** | 跑一次就知道過沒過 |")
    A(f"| **機器只驗得了一半** | **{half}** | ⚠️ 有一支會通過的程式，"
      "**而它只證明了這一項的一部分** |")
    A(f"| **機器完全驗不了** | **{unver}** | 🚨 只能靠人做、靠人記錄 |")
    A("")
    A("> **⚠️ 中間那一類最危險。**"
      "它有一支跑得過的程式，**而那正是最容易被讀成「已驗證」的形狀。**")
    A("")
    A("**舉例**：措辭檢查表的逐節套用有一支程式，"
      "它能證明每一格都寫了字——**🚫 但它證明不了那些字是對的。**"
      "一格寫「本節不適用」而其實適用，**那支程式照樣放行。**")
    A("")

    # ── 二 ────────────────────────────────────────────────────
    A("## 二、每一個數字都要附三件事")
    A("")
    A("**一句話**：光是數字對，不夠。"
      "**⚠️ 這份工作已經出過五次「數字都對，但量的不是同一件事」。**")
    A("")
    A("| 要附什麼 | 不附會怎樣（真實案例） |")
    A("|---|---|")
    A("| **母體**（這個數是從哪一批算出來的） | 「可得 45」與「在手 12」並列，"
      "讀者以為在講同一批 |")
    A("| **計數單位**（篇？項？次？） | 抽查帳的「項」與抽查了幾「篇」並列，"
      "看起來互相矛盾 |")
    A("| **判準**（怎麼算才算） | 「只憑標題可判」是資料形態，"
      "「無從判定方向」是判讀結果——**兩者都不是「沒有」** |")
    A("")
    A("> **🚨 缺任何一項，一個完全正確的數字都可能被讀成別的意思。**")
    A("")

    # ── 三 ────────────────────────────────────────────────────
    A("## 三、交付當天逐項打勾（🚫 不得憑印象）")
    A("")
    A(f"共 **{len(items)}** 項。**⚠️ 每一項都對應一次真的犯過的錯**——"
      "🚫 這不是一份想像出來的清單。")
    A("")
    for it in items:
        A(it)
    A("")
    A("**⚠️ 其中兩項刻意不寫出數字**（抽查債三欄、義務清冊條數）："
      "**🚨 一份禁止沿用舊值的清單，自己不該內建一組舊值。**")
    A("")

    # ── 四 ────────────────────────────────────────────────────
    A("## 四、有一批數字，我這邊核不到")
    A("")
    A(f"報告用到的數字裡，有 **{_inaccessible()}** 個的權威來源在另一台機器上"
      "（存放原始文獻的那台），**我這邊看不到**。")
    A("")
    A(f"**✅ 目前 {_handoff_split()[0]} 個已由那台機器交過來**，"
      "而交過來的檔案自己標明了「**這是某一刻的快照**」並附上時間。")
    A("")
    A("> **🚨 交付當天仍然要重跑一次。**"
      "⚠️ 那個時間戳越舊，這句話就越該被當成警告，"
      "**🚫 而不是「已經有值了」。**")
    A("")
    A(f"**⚠️ 另外 {_handoff_split()[1]} 個目前還沒有值**，而它們各自的理由不同——"
      "有的要等全文讀完才會存在，有的是算法需要重建。"
      "**🚨 三種「沒有值」用三種不同的標記，🚫 不共用一個。**")
    A("")

    # ── 五 ────────────────────────────────────────────────────
    A("## 五、有一條算式可以直接引用（現算通過）")
    A("")
    A(f"標準線的池子是閉合的：已篩 **{v('SEQ_LEN')}** ＋ 亂序 "
      f"**{v('OUT_OF_SEQ')}** ＋ 未篩 **{v('NOT_SCREENED_STD')}** "
      f"＝ **{v('N_TOTAL_STD')}**，分毫不差。")
    A("")
    A("**⚠️ 這條算式是「為什麼分母是這一批」的依據**，"
      "**🚨 而它一直到最近才真的被程式跑過**——在那之前它只是文件裡的一句話。")
    A("")

    # ── 六 ────────────────────────────────────────────────────
    A("## 六、這一節的限制")
    A("")
    A("1. **這份清單只保證「不漏」，🚫 不保證「已辦」。** "
      "打勾的人要真的做過，而**沒有任何程式在看這件事**。")
    A(f"2. **{_n_gates()} 道自動檢查全綠，🚫 不代表全部都好了**——"
      f"⚠️ 那些事裡有 **{half + unver}** 項它們碰不到。")
    A("3. **快照不是現算。** 另一台機器交過來的值帶著時戳，"
      "**🚨 交付當天不重跑就是沿用舊值。**")
    A("")
    return "\n".join(L)


text = report()
_prev = OUT.read_text(encoding="utf-8") if OUT.exists() else None
_strip = lambda s: "\n".join(l for l in s.split("\n")
                             if not l.startswith("**產生時刻："))
changed = _prev is not None and _strip(_prev) != _strip(text)
OUT.write_text(text, encoding="utf-8")
print(f"{'🆕 首次產生' if _prev is None else ('⚠️ 內容有變（值漂移或被手改）' if changed else '✅ 內容未變')}"
      f" {OUT}（{len(text.splitlines())} 行）")

problems, controls = lint.run(
    text, _n154.COINCIDENCE, _n154.value,
    forbidden_phrases=("整體就緒", "全部驗證完畢"),
    # 🚨 本節之讀者是交付當天動手的人，🚫 不是擁有者。
    # ⚠️ 「佔位符」對他是日常用語，且必做清單係**逐字抽取**，🚫 不得改寫。
    # 🚫 而「待辦」等其餘骨架用語仍擋——⚠️ 覆寫是縮小，不是關掉。
    skeleton_words=[w for w in lint.SKELETON_WORDS if w != "佔位符"])
sys.exit(1 if lint.report(problems, controls, "己節成稿自檢") else 0)
