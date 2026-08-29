# -*- coding: utf-8 -*-
"""骨架散文中之**字面數字**清查。

## 🚨 為什麼要有這支

本 run 之規則是「**漂移值一律用佔位符、凍結值原樣引用且須標明**」。
⚠️ 而近數輪光靠手查就抓到四處寫死並已過期：

  - 交付清單寫「42 條義務清冊」——實際已達八十餘條
  - 交付清單寫死抽查債三欄 22／6／16
  - 丁節把 55／38／17 寫進散文，一次重跑即變 66／49／17
  - 庚節附表有兩列掉到表格結束之後，markdown 因此斷開

🚨 四處都不是算錯，是**把一個會動的數字寫成了不會動的樣子**。
⚠️ 手查抓得到，但手查不會每輪都做——故本檔把它機械化。

## 本檔怎麼判

散文中的字面數字分三類，**只有第三類是問題**：

| 類 | 例 | 處置 |
|---|---|---|
| **結構性數字** | 「第 12 型」「第 28 行」「看板 47908」 | ✅ 指涉位置與編號，不隨資料變動 |
| **凍結值** | `0.05`、`2270`、門檻 `1.5` | ✅ 可原樣引用，**但須在 ALLOW 中逐一登記其來源** |
| **🚨 漂移值寫成字面** | 「義務 42 條」「在手 27 篇」 | 🚫 應為佔位符 |

⚠️ 判別不能靠數字本身（55 可能是型錄編號也可能是條數），
🚨 故本檔**不猜**：凡不在 ALLOW 內者一律列出，由人逐項判定並登記。
**⚠️ ALLOW 是判定紀錄，不是白名單**——每一筆都要寫清楚它為什麼可以是字面。

## 涵蓋範圍聲明（n+80 三）

- ✅ 抓得到：散文（含表格儲存格）中之整數與小數。
- 🚫 抓不到：**中文數字**（「三分之二」「兩批」），以及寫成文字的量。
- 🚫 **不看表格儲存格**：實際發生過的四次寫死全在散文；表格由 n115 之
  佔位符機制管。⚠️ 故本檔通過**不代表表格裡沒有寫死的量**。
  🚨 兩項合起來：本檔通過只代表「散文裡沒有未登記的阿拉伯數字」。
- ⚠️ 行內程式碼、佔位符、表格分隔線、URL 與雜湊值一律先剔除，
  🚨 否則雜訊會淹掉真正的命中，而「輸出太長沒人看」與「沒在看」等價。

Run:  python3 .scratch/n141_literal_numbers.py
"""

import re
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

DOCS = {
    "甲": "docs/m1-a-search-coverage-skeleton.md",
    "乙": "docs/m1-b-screening-limits-skeleton.md",
    "丙": "docs/m1-c-termination-skeleton.md",
    "丁": "docs/m1-d-audit-debt-skeleton.md",
    "己": "docs/m1-e-delivery-checklist.md",
    "庚": "docs/m1-f-harms-skeleton.md",
    "辛": "docs/m1-g-acquisition-skeleton.md",
    "壬": "docs/m1-h-owner-decisions-skeleton.md",
    "檢": "docs/m1-wording-checklist.md",
}

# 本輪清查範圍。⚠️ 🚫 不得因「其餘尚未清」而宣稱已清查完畢。
SCOPE = ["甲", "丙", "庚", "壬"]

# ── 先剔除的東西（🚨 剔除規則本身就是判準，故逐條寫明理由）──────────
STRIP = [
    (re.compile(r"\{\{[A-Z0-9_]+\}\}"), "佔位符——本來就該是它"),
    (re.compile(r"`[^`\n]*`"), "行內程式碼與檔名"),
    # 🚨 整列表格一律剔除，而這是一個**縮小涵蓋範圍**的決定，須說明：
    # ⚠️ 實際發生過的四次寫死，**全部在散文裡**，沒有一次在表格儲存格。
    # ✅ 且表格若該放漂移值，n115 之佔位符機制已在管（附表逐格比對）。
    # 🚫 故本檔只管散文——**不得因此宣稱「表格裡沒有寫死的量」**。
    (re.compile(r"^\s*\|.*$", re.M), "表格整列（改由 n115 佔位符機制管）"),
    (re.compile(r"https?://\S+"), "URL"),
    (re.compile(r"\bsha256:[0-9a-f]+"), "雜湊值"),
    # 🚨 初版整行剔除標題，**而那是錯的**：標題也會寫進量。
    # ⚠️ 實例：庚節小標「那個『10 筆』不是一份名單」——10 是漂移值之字面，
    #    而它就因為在標題裡而躲過本檢查。**🚫 改為只剔除 `#` 記號本身。**
    (re.compile(r"^#{1,6}\s", re.M), "標題之 # 記號（🚫 標題內文仍須掃）"),
]

# ⚠️ 須吃得下千分位逗號：初版把「9,091」拆成 9 與 091，
# 🚨 那不只是雜訊，是**把一個數字讀成兩個**——正是本檔要防的那種事。
NUM = re.compile(
    r"(?<![0-9A-Za-z_.\-/])(\d{1,3}(?:,\d{3})+|\d+(?:\.\d+)?)(?![0-9A-Za-z_.\-/])")

# 🚨 結構性語境：數字前後之字樣顯示它指涉位置或編號，不是量。
# ⚠️ 初版漏了兩型，都是實跑才看見的：
#   ① 行號區間之尾數（「看板 2087–2091」的 2091）——前綴是破折號不是「看板」
#   ② 裁定編號（「裁定 64」「裁定 62」）
# 🚨 兩者都不是量，卻被報成可疑；**放著不修，下一輪讀的人會學會忽略輸出**。
STRUCTURAL = re.compile(
    r"(第\s*$|看板\s*$|行\s*$|條\s*$|型\s*$|節\s*$|頁\s*$|ADR-$|n\+$|N\s*$"
    r"|裁定\s*$|[0-9][–—-]$)")
STRUCTURAL_AFTER = re.compile(r"^\s*(型|行|節|頁|輪|條(?!\s*義務))")

# ── ALLOW：**判定紀錄**。⚠️ 每一筆須寫明它為何可以是字面 ────────────
# 🚫 不得為了讓輸出變乾淨而往這裡加東西；加一筆就是做一次判定。
ALLOW = {
    # ── 原始碼常數 ──
    "0.05": "顯著水準 α（`DEFAULT_ALPHA`），凍結於原始碼",
    "0.95": "目標召回率（`DEFAULT_TARGET_RECALL`），凍結於原始碼",
    "200":  "尾端抽驗 N（`DEFAULT_TAIL_SPOT_CHECK_N`），凍結於原始碼",
    # ── 抽樣設計（`strata.json`，已凍結）──
    "60": "校準集設計總數 `totalSampleSize`",
    "45": "擁有者裁示之縮減後設計數（n+123 甲案）",
    "15": "S5＋S6 合併配額（8＋7）",
    "8":  "S5 配額／S3 配額（⚠️ 同值兩處，須看上下文）",
    "7":  "S6 配額",
    # ── 🚨 標準線母體：**必須寫成字面** ──
    # ⚠️ 它出現在 n+80（二）之拘束措辭裡，而該措辭要求「一字不改」。
    # 🚨 改成佔位符會使兩節之措辭在交付前不相同，反而破壞那條規則。
    # ✅ 且篩選已終止（第 404 輪擁有者確認），該數不再變動。
    "9,091": "標準線已篩母體；拘束措辭之一部分，n+80（二）要求逐字相同",
    "6,975": "第一次觸發之閉合式項（丙節），凍結",
    "7,431": "第二次觸發之閉合式項（丙節），凍結",
    "2,116": "第一次觸發之未篩數，凍結",
    "1,460": "第二次觸發之未篩數，凍結",
    "115":  "第一次觸發之 windowSize，凍結",
    "201":  "第二次觸發合併後之 windowSize，凍結",
    # ── 第 425 輪影子全量比對：一次性量測，已凍結 ──
    "300": "影子對帳之樣本數（第 425 輪全量比對之母體）",
    "169": "同上：n+86 已解釋之影子樣本",
    "79":  "同上：確定性路由四道、依設計不建工作單者",
    "247": "同上：落在正式層之外者",
    "242": "同上：其中不帶旗標者",
    "52":  "同上：四分類表之一格",
    "47":  "同上",
    "19":  "同上",
    "0":   "同上；亦用於「未解釋漏口為 0」「命中數為 0」等已量測之零",
    "5":   "orphan 工作單交集之量測（第 425 輪），凍結",
    "1":   "同上之分格；亦為「一筆」之計數詞",
    "2":   "「兩者」「兩批」之計數詞，或已凍結之分格",
    "3":   "同上",
    "4":   "同上",
    # ── 證據鏈雜湊之一次性清點（n+115）──
    "10": "自證雜湊 10 個（n+115 之定位結果），凍結",
    "16": "引用雜湊 16 處（同上），凍結",
    "11": "第一次觸發之原像欄位數，凍結",
    "12": "第二次觸發之原像欄位數，凍結（⚠️ 與 11 併記才有意義）",
    # ── 看板行號（非量）──
    "16903": "看板行號（四類不良事件並列之出處）",
    "22769": "看板行號（影子工作單漏口之提請）",
    "47915": "看板行號區間之尾（n+60 之 M1 大綱）",
    # ── 🚨 歷史引述：引的是「當時回報過什麼」，不是現值 ──
    # ⚠️ 壬節「連續數十輪回報 55／55」講的是過去的事實，改成現值反而失真。
    "55": "歷史引述：義務勾稽當時回報之條目數（🚫 不是現值，現值見丁節佔位符）",
}


def strip_noise(text):
    for rx, _why in STRIP:
        text = rx.sub(" ", text)
    return text


def scan(sec):
    raw = Path(DOCS[sec]).read_text(encoding="utf-8")
    text = strip_noise(raw)
    out = []
    for m in NUM.finditer(text):
        val = m.group(1)
        before = text[max(0, m.start() - 8):m.start()]
        after = text[m.end():m.end() + 4]
        if STRUCTURAL.search(before) or STRUCTURAL_AFTER.match(after):
            continue                      # ✅ 結構性數字
        line = text[:m.start()].count("\n") + 1
        ctx = text[max(0, m.start() - 34):m.end() + 26].replace("\n", " ")
        out.append((val, line, ctx.strip()))
    return out


def run(label, sections, docs_override=None):
    print(f"=== {label} ===")
    flagged = []
    for sec in sections:
        if docs_override and sec in docs_override:
            saved = Path(DOCS[sec]).read_text(encoding="utf-8")
            Path(DOCS[sec]).write_text(docs_override[sec], encoding="utf-8")
            try:
                hits = scan(sec)
            finally:
                Path(DOCS[sec]).write_text(saved, encoding="utf-8")
        else:
            hits = scan(sec)
        unknown = [h for h in hits if h[0] not in ALLOW]
        print(f"  {sec}：字面數字 {len(hits)}｜**未登記 {len(unknown)}**")
        for val, line, ctx in unknown:
            print(f"     🚨 {val}  第 {line} 行  …{ctx}…")
        flagged += [(sec,) + h for h in unknown]
    return flagged


real = run("實際文件（本輪範圍：" + "／".join(SCOPE) + "）", SCOPE)

# ── 🚨 反向對照：注入一個「漂移值寫成字面」之句子 ──────────────────
# ⚠️ 依 n+131 三：注入物須落在本檢查有能力判定的範圍內——
# 🚨 故注入到**散文**裡（不是表格分隔線、不是行內程式碼、不是標題），
#    且用一個不在 ALLOW 中的值。
inj_sec = "壬"
inj_text = Path(DOCS[inj_sec]).read_text(encoding="utf-8").replace(
    "## 附：佔位符來源表",
    "本節目前共有 9987 項待決事項。\n\n## 附：佔位符來源表", 1)
control = run("反向對照（已注入一個寫死的漂移值）", [inj_sec],
              {inj_sec: inj_text})

caught = any(v == "9987" for _s, v, _l, _c in control)
print()
print(f"反向對照：{'✅ 抓到注入之 9987' if caught else '🚨 沒抓到——本檢查有盲區'}")
print(f"本輪範圍：{'／'.join(SCOPE)}；"
      f"**🚫 乙／丁／己／檢 尚未清查，不得宣稱已清查完畢。**")
sys.exit(0 if caught else 1)
