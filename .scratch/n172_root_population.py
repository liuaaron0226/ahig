# -*- coding: utf-8 -*-
"""同字根之格名：**母體是否相同，須逐組登記**。

## 🚨 這支存在的理由：登記簿有一個它抓不到的洞

n+154 起有一本同值異義簿，抓「兩個不相干的量現算後恰好相等」。
**⚠️ 而 n+169（四）發現它抓不到另一族**：

> `SRC_REPO`（10）與 `LANDING_REPO`（15）**同一節、同一個分類詞「機構典藏庫」，
> 母體完全不重疊**（一個是已到手的 41 份，一個是尚未到手的 33 筆）。
> **🚨 它們只因為值不相等而躲過那本簿。**

**🚫 值相同才會被抓，名字相同不會**——⚠️ 而後者更容易誤導，
因為**名字是給人看的，值不是**：讀者看見兩個 `*_REPO` 會假設它們可比。

## ✅ 故本檔逐「字根」登記，而不是逐格

⚠️ 判準取字根（第一個底線之前），因為**誤讀是沿著名字發生的**：
`ACQ_*` 四格看起來像同一件事的四個切面，**🚨 實際是四個不同母體。**

| 登記 | 意思 | 檢查 |
|---|---|---|
| `SAME` | 該組成員共用同一母體 | 只需登記其母體之敘述 |
| `MIXED` | **成員之母體不同** | 🚨 **每一格之定位欄都須自帶母體或單位標記** |

**🚫 未登記之字根一律失敗**——⚠️ 新增一格而字根未登記時，
**它會逼我判一次「這一組的母體是不是同一個」**，
🚨 而那正是本檔要保護的那個判斷。

## ⚠️ 本檔之涵蓋範圍（🚫 不得讀成更強）

- ✅ 抓得到：同字根而母體不同、卻沒有任何一格標明母體。
- 🚫 抓不到：**標記寫了而寫錯**——⚠️ 「母體＝41」寫成「母體＝33」照樣過。
- 🚫 抓不到：**跨字根之同義誤讀**（`CALIB_VER_PUB` 對 `VER_PUBLISHED`）——
  🚨 那兩組字根不同、母體不同，**而它們是同一種量的兩個切面**，
  ⚠️ 本檔看不到；目前僅靠 `CALIB_NONPUB` 定位欄那句「不得與 41 筆之 10 互換」擋著。

Run:  python3 .scratch/n172_root_population.py
"""

import re
import sys
from collections import defaultdict
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

CHECKLIST = Path("docs/m1-e-delivery-checklist.md")
ROW = re.compile(r"^\| (\S+) \| `([A-Z0-9_]+)` \| (\S+) \| (\S+) \| (.+) \|$", re.M)

# 🚨 母體／單位標記之詞表。⚠️ 這是一份**詞表**，🚫 不是語意判斷——
#    見上方涵蓋範圍：它證明「有人寫了母體」，🚫 不證明寫得對。
MARKERS = ("母體", "單位", "就已量到", "之中", "筆之", "不得與", "互換",
           "配額", "非 33", "非 41", "全池")

ROOTS = {
    # ── 🚨 母體不同者：每一格都須自帶標記 ──────────────────────
    "ACQ": ("MIXED", {
        "ACQ_ALL": "私有根 fulltext 全體（含舊工作線）",
        "ACQ_CALIB": "校準集抽出之 60",
        "ACQ_IN_OBTAINABLE": "45 筆可得",
        "ACQ_SCOPED": "校準 60 ＋ n+103 補集＝84",
    }),
    "LANDING": ("MIXED", {
        "LANDING_ROUTE_N": "45 筆可得中之 available-landing-page",
        "LANDING_REPO": "尚未到手之 33 筆", "LANDING_PUBLISHER": "尚未到手之 33 筆",
        "LANDING_FIGSHARE": "尚未到手之 33 筆", "LANDING_PMC_SCAN": "尚未到手之 33 筆",
        "LANDING_REACHED": "實際抓過之 33 筆中 HTTP 200 者",
        "LANDING_FULLTEXT_MARKER": "已量到之 16 筆",
        "LANDING_WORTH_PARSER": "已量到之 16 筆",
        "LANDING_WORDS_MIN": "已量到之 16 筆",
        "LANDING_WORDS_MED": "已量到之 16 筆",
        "LANDING_WORDS_MAX": "已量到之 16 筆",
    }),
    "PDF": ("MIXED", {
        # 🚨 n+172 由本檔查出：⚠️ `PDF_ROUTE_N` 是**尚未到手者之路徑分類**，
        #    其餘四格是**私有快取中實際在手的檔案**。**🚫 兩者不可相減。**
        "PDF_ROUTE_N": "45 筆可得中之 available-pdf",
        "PDF_IN_HAND": "私有 pdf 快取之檔案",
        "PDF_TEXTLAYER": "私有 pdf 快取之檔案",
        "PDF_UNCERTAIN": "私有 pdf 快取之檔案",
        "PDF_SCANNED": "私有 pdf 快取之檔案",
    }),
    "S3": ("MIXED", {
        "S3_QUOTA": "設計配額（單位＝配額，🚫 非文獻）",
        "S3_ACQ_CALIB": "校準 60 之中該層",
        "S3_ACQ_BACKFILL": "含補抽之 84 之中該層",
    }),
    "HARMS": ("MIXED", {
        "HARMS_S5_QUOTA": "設計配額", "HARMS_S6_QUOTA": "設計配額",
        "HARMS_COMBINED": "設計配額（S5＋S6）",
        "HARMS_COUNTER_LAST": "看板計數器之最終讀數（🚨 讀數，不是名單）",
        "HARMS_ATTRIBUTABLE": "相鄰名冊 included 之相異 id",
        "HARMS_UNATTRIBUTABLE": "讀數 − 可指認者（推導）",
        "HARMS_RESERVE_MENTIONS": "reserve 之長度（⚠️ 單位＝提及）",
        "HARMS_S5_ACTUAL": "全文取得後方存在（尚無值）",
    }),
    "DEBT": ("MIXED", {
        "DEBT_CUMULATIVE": "累計抽查項目", "DEBT_SETTLED": "已清償抽查項目",
        "DEBT_OUTSTANDING": "尚欠抽查項目（總）",
        "DEBT_B4": "尚欠之中的影子歧異那一部分（🚨 子集）",
    }),

    # ── ✅ 共用同一母體者 ───────────────────────────────────────
    "SRC": ("SAME", "已在手之 41 份（NOLIC 兩格為其依類別之子集）"),
    "VER": ("SAME", "已在手之全部 manifest（三批互斥，合計即全體）"),
    "CALIB": ("SAME", "校準集 acquired 之 14 份"),
    "UNPROBED": ("SAME", "從未試過替代位址之 12 筆（ALT／PDF 為其子集）"),
    "SHORTFALL": ("SAME", "校準集之缺口（HARMS／S7 為其依層別之子集）"),
    "ALT": ("SAME", "第一輪替代位址查詢之 11 筆"),
    "OCC1": ("SAME", "第一次終止判定當下之序列"),
    "OCC2": ("SAME", "第二次終止判定當下之序列"),
    "OBLIGATION": ("SAME", "義務清冊之條目（DISTINCT 為條目數減重述數）"),
    "SHADOW": ("SAME", "影子對帳之 300 筆候選"),
    "THRESHOLD3": ("SAME", "門檻 3 之事前值與兩次實測（🚨 兩次檢定母體不同，見定位欄）"),
    "PLANNING": ("SAME", "菁英層級補給規劃率（男／女／整體）"),
    "NARR": ("SAME", "判讀理由文字之敘述式辨識"),
    "RETRACT": ("SAME", "八份工作單之 publicationTypes 聯集（IN_EVIDENCE 為其子集）"),
    "PMC": ("SAME", "Europe PMC 查無全文之 33 筆（依成因二分）"),
    "S56": ("MIXED", {
        # 🚨 n+177：本組原登記為 SAME，⚠️ 而新增 `S56_ACQ_BACKFILL` 之後不再是。
        #    **前兩格之母體是「當初抽出的那一批」，末格是「含已接受補抽的那一批」。**
        "S56_ACQ": "當初抽出之校準 60 中該層",
        "S56_NONPUB": "同上之中的非刊出版者（🚨 為 `S56_ACQ` 之子集）",
        "S56_ACQ_BACKFILL": "含已接受補抽之該層（⚠️ 分母較大）",
    }),
    "W7": ("SAME", "synergy_replay 之六組重放"),
    "TAG": ("SAME", "掛牌名冊"),
    "TITLE": ("SAME", "僅讀標題即判者之名冊"),
    "UNTITLED": ("SAME", "節次完整性檢查之無標題節"),
    "ADVANCE": ("SAME", "advance 側之期望與實測"),
    "OCC": ("SAME", "（保留）"),
}


# ══════════════════════════════════════════════════════════════════
# 🚨 第二道（n+173）：**跨字根之同義切面**
#
# ⚠️ 第一道按字根分組，故看不見「兩個字根量的是同一種東西」。
# 🚨 n+172（三）把這一半明寫為「仍靠人」——本輪回頭補上其中可判的部分。
#
# ✅ 判準：兩格**字根不同**而**描述詞相同或互為前綴（≥3 字元）**。
#    ⚠️ 前綴比對是必要的：`CALIB_VER_PUB` 與 `VER_PUBLISHED`
#    **完全比對抓不到**（PUB ≠ PUBLISHED），🚨 而那正是當初舉的例子。
#
# ⚠️ **前綴比對的代價要寫明**：它把 `PUB`（published）與 `PUBLISHER` 也配成對。
#    🚨 **那不是誤報，那是一個真的陷阱**——「刊出版」與「出版社」在中文與英文
#    縮寫下都長得像，⚠️ 而它們毫不相干。故此類登記為「無關」並記其理由。
#
# 🚫 未登記之配對一律失敗。⚠️ 登記為「同義切面」者，**兩格之定位欄須互相指名**——
#    🚨 只有一邊寫，讀者若剛好讀另一邊就看不到。
# ══════════════════════════════════════════════════════════════════
GENERIC = {"N", "P", "W", "ALL", "LAST", "MIN", "MAX", "MED", "HITS", "POP",
           "VALUE", "COUNT", "TOTAL", "ROWS", "GAP", "OK", "ID", "HASH",
           "B4", "F", "M", "IN", "ONLY", "OF", "SEQ"}
MIN_PREFIX = 3

FACET = "同義切面"
UNRELATED = "無關"

SYNONYMS = {
    # ── 🚨 同義切面：同一種量的不同切面，兩邊定位欄須互相指名 ─────
    ("CALIB_VER_PUB", "VER_PUBLISHED"): (FACET, "刊出版之份數：校準 14 vs 在手 41"),
    ("CALIB_VER_ACC", "VER_ACCEPTED"): (FACET, "作者接受版：校準 14 vs 在手 41"),
    ("CALIB_VER_SUB", "VER_SUBMITTED"): (FACET, "投稿版：校準 14 vs 在手 41"),
    ("SRC_UNKNOWN", "VER_UNKNOWN"): (
        FACET, "🚨 **同母體（41）、同一個「不明」字、而不明的是不同東西**："
               "前者來源不明，後者版本不明。⚠️ 本簿最危險的一對。"),
    ("LANDING_REPO", "SRC_REPO"): (FACET, "機構典藏庫：尚未到手 33 vs 在手 41"),
    ("LANDING_REPO", "SRC_NOLIC_REPO"): (FACET, "同上，後者為在手中未記載授權者"),
    ("LANDING_PUBLISHER", "SRC_PUBLISHER"): (FACET, "出版社：尚未到手 33 vs 在手 41"),
    ("LANDING_PUBLISHER", "SRC_NOLIC_PUB"): (FACET, "同上，後者為在手中未記載授權者"),
    ("LANDING_PMC_SCAN", "SRC_PMC"): (
        FACET, "🚨 同一個 PMC，兩種相反處境：前者是**掃描件、不在可取全文子集**，"
               "後者是**已成功取回全文者**。⚠️ 併排會讀成同一批。"),
    ("LANDING_ROUTE_N", "PDF_ROUTE_N"): (
        FACET, "同為 45 筆可得之路徑分類，⚠️ 與 `ACQ_IN_OBTAINABLE` 三者相加＝45"),
    ("ACQ_CALIB", "S3_ACQ_CALIB"): (FACET, "校準 60 之 acquired：全體 vs S3 該層"),
    ("S3_ACQ_CALIB", "S56_ACQ"): (FACET, "各層之 acquired，🚫 層別不同"),
    ("S3_ACQ_BACKFILL", "S56_ACQ"): (
        FACET, "⚠️ 層別不同**且分母不同**（後者為當初抽出者，前者含補抽）"),
    ("S3_ACQ_BACKFILL", "S56_ACQ_BACKFILL"): (
        FACET, "✅ **同一種量、同一種分母，只差層別**（含補抽之該層取得數）——"
               "🚨 故這一對是本簿裡最乾淨的一種同義切面，⚠️ 而正因為乾淨，"
               "**兩數相鄰書寫時最容易被當成同一層**。"),
    ("S3_ACQ_CALIB", "S56_ACQ_BACKFILL"): (
        UNRELATED, "🚨 **層別不同，分母也不同**：前者為當初抽出之 S3，"
                   "後者為含補抽之 S5+S6。⚠️ 兩者僅因同含 `ACQ` 而被本簿配對，"
                   "**🚫 並無切面關係**——它們既不同層也不同母體。"),
    ("CALIB_NONPUB", "S56_NONPUB"): (FACET, "非刊出版之份數：校準 14 vs S5+S6"),
    ("HARMS_S5_QUOTA", "S3_QUOTA"): (FACET, "設計配額，層別不同"),
    ("HARMS_S6_QUOTA", "S3_QUOTA"): (FACET, "設計配額，層別不同"),
    ("ALT_PDF", "UNPROBED_PDF"): (FACET, "替代位址可取 PDF：第一輪 11 筆 vs 第二輪 12 筆"),
    ("NOT_SCREENED_STD", "N_TOTAL_STD"): (
        FACET, "同為標準線之計數，⚠️ 與 `SEQ_LEN`／`OUT_OF_SEQ` 同屬 n+80 之閉合式"),

    # ── ✅ 無關：字形碰巧相近，🚫 不得因此互相指名（那會製造假關聯）──
    ("CALIB_VER_PUB", "LANDING_PUBLISHER"): (
        UNRELATED, "🚨 `PUB`＝**刊出版**（published），`PUBLISHER`＝**出版社**。"
                   "⚠️ 前綴相同而意思無關——**本簿之前綴比對必然配出此對，"
                   "而它正好也是人最容易混的一種。**"),
    ("CALIB_VER_PUB", "SRC_PUBLISHER"): (UNRELATED, "同上：刊出版 vs 出版社"),
    ("CALIB_VER_PUB", "SRC_NOLIC_PUB"): (UNRELATED, "同上：刊出版 vs 出版社"),
    ("SRC_NOLIC_PUB", "VER_PUBLISHED"): (UNRELATED, "同上：出版社 vs 刊出版"),
    ("NARR_COMPARATOR_ADV", "W7_ADVERSARIAL"): (
        UNRELATED, "`ADV`＝advance（判讀為推進）vs adversarial（對抗式重放）"),
    ("ADVANCE_EXPECTED", "TITLE_ONLY_EXPECTED_GAP"): (
        UNRELATED, "一為統計期望值，一為「預期缺口」之估計，🚫 兩者無關"),
    ("CALIB_VER_SUB", "THRESHOLD3_SUBGROUP"): (
        UNRELATED, "`SUB`＝submitted（投稿版）vs subgroup（子群體）"),
    ("LANDING_PMC_SCAN", "PDF_SCANNED"): (
        UNRELATED, "⚠️ 一為**著陸頁之主機分類**，一為**在手檔案之性質**"
                   "（無文字層）；🚨 同一個「掃描」字描述的是兩種不同的東西"),
    ("NARR_RETRACT_TEXT_N", "PDF_TEXTLAYER"): (
        UNRELATED, "一為判讀理由之文字，一為 PDF 之文字層"),
}


def _toks(name):
    return [p for p in name.split("_")[1:] if p not in GENERIC and len(p) > 1]


def _shared(a, b):
    out = set()
    for x in _toks(a):
        for y in _toks(b):
            short = min(x, y, key=len)
            if x == y or (len(short) >= MIN_PREFIX
                          and (x.startswith(y) or y.startswith(x))):
                out.add(short)
    return out


def run_synonyms(by, label):
    problems = []
    locator = {n: w for members in by.values() for n, w in members.items()}
    names = sorted(locator)
    seen = set()
    for i, a in enumerate(names):
        for b in names[i + 1:]:
            if a.split("_")[0] == b.split("_")[0]:
                continue                   # 同字根由第一道管
            if not _shared(a, b):
                continue
            key = (a, b)
            seen.add(key)
            if key not in SYNONYMS:
                problems.append(
                    f"🚨 `{a}` 與 `{b}` 跨字根共用描述詞而**未登記**"
                    "——⚠️ 須判定它們是同一種量的兩個切面，抑或字形碰巧相近")
                continue
            kind, _why = SYNONYMS[key]
            if kind == FACET:
                if b not in locator[a]:
                    problems.append(f"🚨 `{a}` 之定位欄未指名 `{b}`"
                                    "——⚠️ 只有一邊寫，讀另一邊的人就看不到")
                if a not in locator[b]:
                    problems.append(f"🚨 `{b}` 之定位欄未指名 `{a}`"
                                    "——⚠️ 只有一邊寫，讀另一邊的人就看不到")

    stale = sorted(k for k in SYNONYMS if k not in seen)
    if stale:
        problems.append(f"⚠️ 已登記而不再配對之項：{stale}"
                        "——🚫 應移除，否則本簿之涵蓋率被高估")

    print(f"=== {label} ===")
    if problems:
        for p in problems:
            print(f"  {p}")
    else:
        nf = sum(1 for k, _ in SYNONYMS.values() if k == FACET)
        print(f"  ✅ 跨字根配對 {len(seen)} 對全部登記"
              f"（同義切面 {nf}｜字形碰巧相近 {len(SYNONYMS) - nf}），"
              "且同義切面者兩邊定位欄互相指名")
    return problems


def groups(text=None):
    t = text if text is not None else CHECKLIST.read_text(encoding="utf-8")
    by = defaultdict(dict)
    for _sec, name, _k, _s, where in ROW.findall(t):
        by[name.split("_")[0]][name] = where
    return by


def run(by, label):
    problems = []

    for root, members in sorted(by.items()):
        if len(members) < 2:
            continue                       # ⚠️ 單格字根無「同名不同母體」之風險
        if root not in ROOTS:
            problems.append(
                f"🚨 字根 `{root}_*` 有 {len(members)} 格而**未登記**："
                f"{sorted(members)}——⚠️ 須先判定其母體是否相同")
            continue
        kind, spec = ROOTS[root]
        if kind != "MIXED":
            continue
        for name, where in sorted(members.items()):
            if name not in spec:
                problems.append(
                    f"🚨 `{name}` 屬 MIXED 字根 `{root}` 而未登記其母體"
                    "——⚠️ 新增一格即須指明它數的是哪一批")
            elif not any(m in where for m in MARKERS):
                problems.append(
                    f"🚨 `{name}` 之定位欄未標母體／單位，而同字根者母體不同"
                    f"（本格應為「{spec[name]}」）"
                    "——⚠️ 讀者會沿著名字假設它們可比")

    # 🚨 登記而已不存在者：⚠️ 留著會使本簿看起來比實際涵蓋得多。
    live = {r for r, m in by.items() if len(m) >= 2}
    stale = sorted(r for r in ROOTS if r not in live and ROOTS[r][1] != "（保留）")
    if stale:
        problems.append(f"⚠️ 已登記而清單中不再成組之字根：{stale}"
                        "——🚫 應移除，否則本簿之涵蓋率被高估")

    print(f"=== {label} ===")
    if problems:
        for p in problems:
            print(f"  {p}")
    else:
        mixed = sum(1 for k, _ in ROOTS.values() if k == "MIXED")
        print(f"  ✅ {len(live)} 個成組字根全部登記；其中母體不同者 {mixed} 組，"
              "各格皆已標母體或單位")
    return problems


live_problems = run(groups(), "同字根之母體登記")
print()
live_syn = run_synonyms(groups(), "跨字根之同義切面登記")

# ── 🚨 反向對照：兩種注入，兩種都必須被抓到 ────────────────────────
raw = CHECKLIST.read_text(encoding="utf-8")

# (a) 一個未登記之新字根（兩格）
inj_a = raw + ("\n| 辛 | `ZZTEST_ONE` | 漂移 | 產物 | 甲 |"
               "\n| 辛 | `ZZTEST_TWO` | 漂移 | 產物 | 乙 |\n")
ctl_a = run(groups(inj_a), "反向對照（注入未登記字根）")

# (b) MIXED 字根中一格之定位欄被抽掉母體標記
#     ⚠️ 取 `PDF_ROUTE_N`——🚨 它正是本檔本輪查出的那一格。
inj_b = re.sub(r"^(\| 辛 \| `PDF_ROUTE_N` \| \S+ \| \S+ \| ).+( \|)$",
               r"\1同上\2", raw, count=1, flags=re.M)
ctl_b = run(groups(inj_b), "反向對照（抽掉 PDF_ROUTE_N 之母體標記）")

# (c) 一對**未登記之跨字根同描述詞**。
#     ⚠️ 兩者字根各只一格，故第一道會略過——🚨 專門打第二道。
inj_c = raw + ("\n| 辛 | `ZZALPHA_WIDGET` | 漂移 | 產物 | 甲 |"
               "\n| 辛 | `ZZBETA_WIDGET` | 漂移 | 產物 | 乙 |\n")
ctl_c = run_synonyms(groups(inj_c), "反向對照（注入未登記之跨字根配對）")

# (d) 已登記為同義切面者，抽掉其中一邊之互相指名。
#     ⚠️ 取 `VER_UNKNOWN`——🚨 它與 `SRC_UNKNOWN` 同母體、同一個「不明」字，
#     **本簿最危險的一對**，故拿它當對照最有意義。
# 🚨 以「整行」為單位注入，🚫 不數管線欄位——⚠️ 上一版用 `(?:[^|]*\|){3}`
#    少數了一欄，於是**注入根本沒發生，而對照卻報「本項無盲區」**。
#    ✅ 故此處改為行內字串替換，並**斷言注入確實改到了東西**。
_dlines = raw.split("\n")
_dhit = 0
for _i, _l in enumerate(_dlines):
    if "`VER_UNKNOWN`" in _l and "同義切面 `SRC_UNKNOWN`" in _l:
        _dlines[_i] = _l.replace("同義切面 `SRC_UNKNOWN`", "（已抽掉）")
        _dhit += 1
assert _dhit == 1, f"🚨 反向對照(d) 之注入未命中（{_dhit} 次）——🚫 對照無效，不得視為通過"
inj_d = "\n".join(_dlines)
ctl_d = run_synonyms(groups(inj_d), "反向對照（抽掉 VER_UNKNOWN 之互相指名）")

print()
ok_a = any("未登記" in p and "ZZTEST" in p for p in ctl_a)
ok_b = any("PDF_ROUTE_N" in p and "未標母體" in p for p in ctl_b)
ok_c = any("未登記" in p and "ZZALPHA_WIDGET" in p for p in ctl_c)
ok_d = any("VER_UNKNOWN" in p and "未指名" in p for p in ctl_d)
print(f"反向對照：未登記字根 {'✅' if ok_a else '🚨'}｜"
      f"缺母體標記 {'✅' if ok_b else '🚨'}｜"
      f"未登記跨字根配對 {'✅' if ok_c else '🚨'}｜"
      f"缺互相指名 {'✅' if ok_d else '🚨'}")
allok = ok_a and ok_b and ok_c and ok_d
if not allok:
    print("🚨 **本檢查有盲區**——⚠️ 全綠時無法分辨「真的都標了」與「根本沒在看」")

sys.exit(1 if live_problems or live_syn or not allok else 0)
