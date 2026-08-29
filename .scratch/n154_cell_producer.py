# -*- coding: utf-8 -*-
"""交付當日之**佔位符現算器**（協調者可及的那一半）。

## 🚨 這支腳本要解的問題，不是「填格子」

n+115（清冊 48897）明訂：**🚫 不得沿用任何一輪之數字**。
**⚠️ 而「不得沿用」與「每次手查一百多格」之間，只有一條路**——
**✅ 讓值由權威來源現算，人只維護「哪一格取自哪裡」。**

> **🚨 故本檔🚫 不儲存任何值。**每跑一次都重新開檔、重新取。
> **⚠️ 值若變了，輸出就變了；🚫 沒有一個地方可以讓舊值存活。**

## ⚠️ 第二件事，才是本檔真正抓到東西的地方

`docs/m1-e-delivery-checklist.md` 的「定位」欄是**人手寫的**，
**🚨 而其中有數十格順手把值也寫進去了**（`… → counts.consistent＝**41**`）。

**⚠️ 那些值寫下的當輪是對的。🚫 而沒有任何東西在看它們有沒有過期。**

**✅ 故本檔逐格比對：定位欄自報之值 vs 由來源現算之值。**
**🚨 不符即為「狀態變了而描述沒跟著變」（型錄第 12 型），且發生在防它的那份清單上。**

## 涵蓋範圍聲明（n+80 三）

- ✅ 抓得到：定位欄自報值過期、兩格取自同一欄位而未聲明、解析器覆蓋率下降。
- 🚨 抓不到：**定位欄指錯來源**。⚠️ 若某格的權威來源本來就寫錯，
  本檔會忠實地從錯的地方取值，**🚫 且兩邊都「相符」。**
- 🚨 抓不到：**私有根之 18 格**（`來源型態 == 不可及`）——那是執行室 `n500` 的範圍。

**🚫 故本檔之「覆蓋率 N／M」不是進度條**：未解之格**不是通過，是還沒做**。

Run:  python3 .scratch/n154_cell_producer.py
"""

import json
import re
import sys
from pathlib import Path

import signal
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass

CHECKLIST = "docs/m1-e-delivery-checklist.md"
ROW = re.compile(r"^\|\s*(\S+)\s*\|\s*`([A-Z0-9_]+)`\s*\|\s*(\S+)\s*\|\s*(\S+)\s*\|\s*(.*?)\s*\|\s*$")
# 🚨 定位欄自報之值：`＝**41**`／`＝ **0.3652**`／`＝**22,761**`
SELF_VALUE = re.compile(r"＝\s*\*\*([0-9][0-9,]*(?:\.[0-9]+)?)\*\*")

_cache = {}


def J(path):
    if path not in _cache:
        _cache[path] = json.loads(Path(path).read_text(encoding="utf-8"))
    return _cache[path]


F78 = ".scratch/n78_termination_evidence.json"
F68T = ".scratch/n68_tail_result.json"
F78T = ".scratch/n78_tail_result.json"
INV = ".scratch/m1_step3_inventory.json"
STRATA = "ahig/calibration/b11-carbohydrate/strata.json"
N450 = ".scratch/n450_landing_survey.json"
N456 = ".scratch/n456_pdf_textlayer.json"
N477 = ".scratch/n477_alt_oa_locations.json"
N482 = ".scratch/n482_harms_adjacent_roster.json"
N489 = ".scratch/n489_calibration_versions.json"
N492 = ".scratch/n492_stratum_table.json"
N493 = ".scratch/n493_unprobed_available.json"
N494 = ".scratch/n494_alt_oa_round2.json"
N496 = ".scratch/n496_corpus_verify.json"
N498 = ".scratch/n498_sections_integrity.json"
W7 = "ahig/analysis/results/synergy_replay.json"
F68E = ".scratch/n68_termination_evidence.json"
N439 = ".scratch/n439_route_cost.json"
N486 = ".scratch/n486_licence_gap.json"
N487 = ".scratch/n487_version_and_licence.json"
N488 = ".scratch/n488_pmcid_to_doi.json"
BACKFILL = ".scratch/m1_step3_backfill.json"


def _stratum(sid, key="quota"):
    for s in J(STRATA)["strata"]:
        if s["stratumId"] == sid:
            return s[key]
    raise KeyError(sid)


def _pool(pid, key):
    for r in J(N492)["rows"]:
        if r["pool"] == pid:
            return r[key]
    raise KeyError(pid)


def _bf_pool(pid, key):
    for p in J(BACKFILL)["pools"]:
        if p["poolId"] == pid:
            return p[key]
    raise KeyError(pid)


def _landing_words():
    """⚠️ 母體＝已量到之 16 筆（http 200），🚫 非 33 筆。"""
    w = sorted(r["textWords"] for r in J(N450)["records"] if r["http"] == 200)
    return w


def _median(xs):
    n = len(xs)
    return xs[n // 2] if n % 2 else (xs[n // 2 - 1] + xs[n // 2]) / 2


# ── 解析表 ────────────────────────────────────────────────────────
# 🚨 每一格逐一手寫。**🚫 不得以樣式從定位欄自動猜路徑**——
# ⚠️ 定位欄是散文，猜錯了會安靜地取到別的欄位，而輸出照樣像對的。
RESOLVERS = {
    # 丙：終止統計
    "N_TOTAL_STD":   lambda: J(F78)["standardLaneSequence"]["nTotal"],
    "SEQ_LEN":       lambda: J(F78)["standardLaneSequence"]["screenedCount"],
    "OUT_OF_SEQ":    lambda: J(F78)["standardLaneSequence"]["outOfSequenceCount"],
    "OCC2_P":        lambda: J(F78)["standardLaneSequence"]["pScore"],
    "OCC2_W":        lambda: J(F78)["standardLaneSequence"]["windowSize"],
    "OCC2_POP":      lambda: J(F78)["tailSpotCheckPopulation"]["count"],
    "NOT_SCREENED_STD": lambda: J(F78)["tailSpotCheckPopulation"]["count"],
    "OCC1_P":        lambda: J(F78)["previousOccurrence"]["pScore"],
    "OCC1_PAGE":     lambda: J(F78)["previousOccurrence"]["atPage"],
    "OCC1_W":        lambda: J(F78)["previousOccurrence"]["windowSize"],
    "OCC1_HITS":     lambda: len(J(F68T)["result"]["relevantOrUnclearFound"]),
    "OCC2_HITS":     lambda: len(J(F78T)["result"]["relevantOrUnclearFound"]),
    "P_ALLQUEUE":    lambda: J(F78)["evaluateTerminationStandardBasis"]["pScore"],
    "TRIGGER_CAUSE_ID": lambda: J(F78)["triggerCause"]["candidateId"],

    # 庚：分層與 harms
    "HARMS_S5_QUOTA": lambda: _stratum("S5-gi-harms-primary"),
    "HARMS_S6_QUOTA": lambda: _stratum("S6-gi-harms-secondary-only"),
    "HARMS_COMBINED": lambda: (_stratum("S5-gi-harms-primary")
                               + _stratum("S6-gi-harms-secondary-only")),
    "HARMS_ATTRIBUTABLE": lambda: len({r["idPrefix"] for r in J(N482)["included"]}),
    "HARMS_RESERVE_MENTIONS": lambda: len(J(N482)["reserve"]),
    "S3_QUOTA":        lambda: _stratum("S3-tte"),
    "CALIBRATION_TARGET": lambda: J(STRATA)["totalSampleSize"],
    "S56_ACQ":         lambda: _pool("S5+S6-gi-merged", "acquiredCalibration60"),
    "S3_ACQ_CALIB":    lambda: _pool("S3-tte", "acquiredCalibration60"),
    "S3_ACQ_BACKFILL": lambda: _pool("S3-tte", "acquiredWithBackfill"),

    # 辛：取得
    "ACQ_CALIB":     lambda: J(INV)["counts"]["acquired"],
    "CALIB_VER_PUB": lambda: J(N489)["distribution"]["publishedVersion"],
    "CALIB_VER_ACC": lambda: J(N489)["distribution"]["acceptedVersion"],
    "CALIB_VER_SUB": lambda: J(N489)["distribution"]["submittedVersion"],
    "ALT_HAS":       lambda: sum(1 for r in J(N477)["records"] if r["otherLocations"]),
    "ALT_NONE":      lambda: sum(1 for r in J(N477)["records"] if not r["otherLocations"]),
    "ALT_REACHABLE": lambda: J(N477)["anyAlternativeReachable"],
    "ALT_PDF":       lambda: J(N477)["pdfObtainable"],
    "ALT_LANDING_ONLY": lambda: (J(N477)["anyAlternativeReachable"]
                                 - J(N477)["pdfObtainable"]),
    "LANDING_REACHED": lambda: sum(1 for r in J(N450)["records"] if r["http"] == 200),
    "BLOCKED_N":     lambda: J(N450)["counts"]["blocked-or-error"],
    "LANDING_FULLTEXT_MARKER": lambda: sum(1 for r in J(N450)["records"]
                                           if r["fulltextMarker"]),
    "LANDING_WORDS_MIN": lambda: _landing_words()[0],
    "LANDING_WORDS_MAX": lambda: _landing_words()[-1],
    "LANDING_WORDS_MED": lambda: _median(_landing_words()),
    "PDF_IN_HAND":   lambda: len(J(N456)["files"]),
    "PDF_TEXTLAYER": lambda: J(N456)["counts"]["text-layer"],
    "PDF_UNCERTAIN": lambda: J(N456)["counts"]["uncertain"],
    "PDF_SCANNED":   lambda: (len(J(N456)["files"]) - J(N456)["counts"]["text-layer"]
                              - J(N456)["counts"]["uncertain"]),
    "LEGACY_DIRS":   lambda: len(J(N496)["legacySchemeDirectories"]),
    "SECTIONS_OK":   lambda: J(N498)["counts"]["consistent"],
    "UNTITLED_SECTIONS": lambda: J(N498)["totals"]["untitledSections"],
    "UNTITLED_LEADING": lambda: J(N498)["totals"]["filesWhoseLeadingSectionIsUntitled"],
    "UNPROBED_N":    lambda: J(N493)["count"],
    "UNPROBED_PDF":  lambda: J(N494)["obtainable"],
    "UNPROBED_ALT":  lambda: J(N494)["distribution"]["有位址無 PDF"],

    # 己：W7 重放
    "W7_ADVERSARIAL": lambda: J(W7)["aggregate"]["adversarial@look100"]["violationRate"],
    "W7_RANDOM":      lambda: J(W7)["aggregate"]["random@look100"]["violationRate"],
    "W7_TRIPWIRE_CATCH": lambda: (J(W7)["aggregate"]["adversarial@look100"]
                                  ["meanTailCatchOnViolation"]),
    "W7_WALKS":       lambda: J(W7)["aggregate"]["adversarial@look100"]["walks"],

    # 甲
    "COLLISION_N": lambda: len(set(re.findall(
        r"\bC-\d+\b", Path("docs/w4b-design-inputs.md").read_text(encoding="utf-8")))),

    # 丙：原始碼常數
    "ALPHA":         lambda: _const("DEFAULT_ALPHA"),
    "TARGET_RECALL": lambda: _const("DEFAULT_TARGET_RECALL"),
    "SPOT_N":        lambda: _const("DEFAULT_TAIL_SPOT_CHECK_N"),
    "OCC1_POP":      lambda: J(F68E)["counts"]["notScreenedCount"],
    "PAGES_BETWEEN": lambda: (J(F78)["standardLaneSequence"]["contiguousPagesJudged"]
                              - J(F78)["previousOccurrence"]["atPage"]),

    # 丁：義務勾稽
    "OBLIGATION_ROWS":     lambda: _anchors()[0],
    "OBLIGATION_RESTATED": lambda: _anchors()[1],
    "OBLIGATION_DISTINCT": lambda: _anchors()[0] - _anchors()[1],

    # 辛：取得路徑分類
    "LANDING_REPO":      lambda: J(N439)["landingKindsAggregate"]["機構典藏庫"],
    "LANDING_FIGSHARE":  lambda: J(N439)["landingKindsAggregate"]["資料典藏（有 API）"],
    "LANDING_PMC_SCAN":  lambda: (J(N439)["landingKindsAggregate"]
                                  ["NCBI PMC（掃描件，不在 OA 全文子集）"]),
    # ⚠️ 出版社須含 doi.org 轉址解出者，🚨 否則會停在改正前的 9。
    "LANDING_PUBLISHER": lambda: sum(v for k, v in J(N439)["landingKindsAggregate"].items()
                                     if k.startswith("出版社")),
    "LANDING_ROUTE_N":   lambda: sum(v for k, v in J(N439)["landingKinds"].items()
                                     if k.startswith("available-landing-page|")),
    "PDF_ROUTE_N":       lambda: sum(v for k, v in J(N439)["landingKinds"].items()
                                     if k.startswith("available-pdf|")),
    "PMC_MISS_NO_ID":    lambda: J(N439)["europePmcMissCauses"]["甲：查不到 PMCID（走 search 端點）"],
    "PMC_MISS_404":      lambda: (J(N439)["europePmcMissCauses"]
                                  ["乙：已知 PMCID，fullTextXML 回 404"]),

    # 辛：版本分布（🚨 三批母體互斥，且第三批是對第二批 26 筆未知之補查）
    "VER_PUBLISHED": lambda: _ver("publishedVersion") + J(N488)["distribution"]["publishedVersion"],
    "VER_ACCEPTED":  lambda: _ver("acceptedVersion"),
    "VER_SUBMITTED": lambda: _ver("submittedVersion"),
    "VER_UNKNOWN":   lambda: J(N488)["stillUnknown"],

    # 庚／辛：由已解之格推導
    "HARMS_UNATTRIBUTABLE": lambda: (J(N482)["lastRunningTotal"]["value"]
                                     - len({r["idPrefix"] for r in J(N482)["included"]})),
    "S56_NONPUB":  lambda: J(N489)["byPoolNonPublished"]["S5+S6-gi-merged"],
    "CALIB_NONPUB": lambda: J(N489)["nonPublished"],

    # 乙：判準檔雜湊（n+44 版控；⚠️ CRLF→LF 正規化後取 SHA-256）
    "NARR_CRITERIA_HASH": lambda: _text_sha256(".scratch/n60_tags.py"),

    # 庚：計數器最終讀數。⚠️ 看板型，而該值另有落盤產物可據——取產物。
    "HARMS_COUNTER_LAST": lambda: J(N482)["lastRunningTotal"]["value"],

    # 辛：n+155 更正之四格
    "OBTAINABLE_N":      lambda: J(BACKFILL)["totals"]["obtainable"],
    # ⚠️ 45 筆可得之中 JATS 已在手者。🚨 兩個項皆取自產物，🚫 不是手算的差。
    "ACQ_IN_OBTAINABLE": lambda: (J(BACKFILL)["totals"]["obtainable"]
                                  - len(J(N450)["records"])),
    "EXTRACTABLE_N":     lambda: J(N492)["totals"]["withBackfill"],
    # 🚨 n+156：以下三格原分類為「看板」，⚠️ 而其值就在受追蹤的產物裡。
    # **🚫 分類錯了會讓它們永遠靠引用，而不是靠來源。**
    "SHORTFALL_N":       lambda: J(BACKFILL)["totals"]["shortfall"],
    "SHORTFALL_HARMS":   lambda: _bf_pool("S5+S6-gi-merged", "shortfall"),
    "SHORTFALL_S7":      lambda: _bf_pool("S7-glycogen", "shortfall"),

    # 🚨 看板凍結值：逐格綁一段看板原文，見下方 BOARD_CITED。
    # ⚠️ 其解析器於該表定義後以迴圈掛入，🚫 不在此逐行手寫——手寫會與該表漂開。
}

# ── 🚨 看板凍結值：**驗證引用，🚫 不重算** ──────────────────────
# ⚠️ 這幾格的權威來源是一則裁定，而裁定是凍結的——**重算會毀掉稽核鏈**。
# 🚨 但「凍結」不等於「不必查」：⚠️ 值可能被抄錯，或該段可能已被改寫。
# ✅ 故各自綁一段**看板原文**：原文還在，引用即成立；原文不在，本檔當場失敗。
#
# ⚠️ 錨定的是**一整句帶脈絡的原文**，🚫 不是那個裸數字——
# 🚨 「累計 22 筆」在看板另有數處，皆與抽查債無關（動物雜訊、McArdle 系列、預印本）。
# **⚠️ 若以裸數字錨定，改到別段也會「通過」。**
BOARD_CITED = {
    "DEBT_CUMULATIVE":  (22, "**22**（相加為 23，重疊 1）"),
    "DEBT_SETTLED":     (6,  "| 已清償 | （未曾正確報過） | **6** |"),
    "DEBT_OUTSTANDING": (16, "**16**（w2 5 ∪ 影子尚欠 11）"),
    "DEBT_B4": (11, "| **影子歧異筆** | 11 | **✅ 已定位** | "
                    "私有根 `screening-shadow-gate/gate-report.json` |"),

    # 乙：n+55／n+59 之三分層與子群體檢定（🚨 兩個門檻 3 是**兩個檢定**）
    "THRESHOLD3_STRATA": (1.52,
        "| 三分層（n 由 261 增至 615） | 門檻 1 **通過**（事件數 19）；"
        "門檻 2 **仍重疊**；門檻 3 **1.52 倍，仍未過** |"),
    "THRESHOLD3_SUBGROUP": (1.76,
        "| 「補得到」子群體主檢定 | 門檻 1、2 **通過**（Fisher p=0.0011，"
        "區間不重疊）；**門檻 3（1.76 倍）未過** |"),
    "FISHER_P": (0.0011,
        "| 「補得到」子群體主檢定 | 門檻 1、2 **通過**（Fisher p=0.0011，"
        "區間不重疊）；**門檻 3（1.76 倍）未過** |"),
    "ADVANCE_EXPECTED": (16.9, "| advance 側 | 兩段合計期望 **16.9 筆、實測 1 筆** |"),
    "ADVANCE_OBSERVED": (1,    "| advance 側 | 兩段合計期望 **16.9 筆、實測 1 筆** |"),
    # ⚠️ 門檻值與差距同出一句——🚨 那一句正是「照原判準判」之事證，🚫 不得拆散引用。
    "THRESHOLD3_VALUE": (1.5,  "**⚠️ 門檻 3 差 0.02 倍（1.52 vs 1.5）而執行室未放寬**——"),
    "THRESHOLD3_GAP":   (0.02, "**⚠️ 門檻 3 差 0.02 倍（1.52 vs 1.5）而執行室未放寬**——"),
    "SIGNAL_DENSITY_RATIO": (26.57,
        "**而標題碳水訊號密度相差 26.57 倍**——該變異幾乎完全由主題組成解釋。"),

    # 乙：補給規劃率（⚠️ **規劃率，非佔比**；🚨 男女兩值為區間）
    "PLANNING_RATE_OVERALL": ("81%",
        "- **🚨 菁英層級之補給規劃率 81%，且男女差異顯著（91–93% vs"),
    "PLANNING_RATE_M": ("91–93%",
        "- **🚨 菁英層級之補給規劃率 81%，且男女差異顯著（91–93% vs"),
    "PLANNING_RATE_F": ("67–72%",
        "  67–72%）**——**M1（丙）性別代表性應併記行為差異，"),

    # 甲／乙／辛：三個凍結計數
    "ORPHAN_N": (5, "**6. 五筆孤兒紀錄之成因已可精確描述（供 M1 第 3 項記錄）**"),
    "UNTRACEABLE_N": (33,
        "**語意比對需要判準，而該判準不存在**；為了補 33 段而現造判準，是本末倒置。"),
    "S7_POOL_N": (6,
        "- **S7 全池僅 6 筆**，即該範圍內肌肝醣文獻總數；**最終僅 2 篇可得。**"),
}


# ✅ 逐格掛入解析器：鍵取自 BOARD_CITED 本身，🚫 不另抄一份名單。
RESOLVERS.update({k: (lambda n=k: _board_cited(n)) for k in BOARD_CITED})


def _board_cited(name):
    value, anchor = BOARD_CITED[name]
    board = Path("COORDINATION.md").read_text(encoding="utf-8")
    if anchor not in board:
        raise ValueError(f"{name}：看板已無該段原文——🚨 引用失效，🚫 不得續用該值")
    return value

# ── 🚨 定位欄**不足以決定值**之格 ────────────────────────────────
# ⚠️ 這一組不是「還沒寫解析器」，是**寫不出來**：
# 🚨 定位欄或未指明母體、或未指名產物、或其判準未落盤。
# **⚠️ 而它們在交付當日仍然要被填**——🚫 由人手填，等於由人手猜。
# ✅ 故逐格記其缺什麼，並列為待裁事項。🚫 未登記之未解格視為漏掉。
UNRESOLVABLE = {
    # 🚨 n+155：本簿原有四格，三格已解，⚠️ 第四格是**我把規則套錯了**。
    "WORDING_SPLIT_GROUPS":
        "🚨 **敘述式辨識，且自承非窮舉**。看板 7692（臨界功率兩篇）與 7983"
        "（三篇同試驗）是**讀出來的**，🚫 不是掛牌統計；"
        "⚠️ 故既無來源可重算，亦不宜綁一句原文假裝它是凍結值——"
        "**🚨 綁了就等於宣稱「只有這兩組」，而那正是它自己禁止的寫法。**"
        "✅ 引用時須寫成「至少兩組」並附兩處出處。",
    "LANDING_WORTH_PARSER":
        "🚨 **n+155 更正：本格不是缺陷。**⚠️ 它是**凍結值**，"
        "而凍結值本來就該照引，🚫 重算才會毀掉稽核鏈——"
        "**我上一輪拿漂移值的規則去套它。**"
        "⚠️ 真正仍待補的是**判準**：`n450` 自載「門檻只用來排序，不用來決定」"
        "且未存門檻值，**故引用該 0 時必須同時寫出這句**，🚫 不得只寫一個 0。",
}


def _text_sha256(path):
    import hashlib
    raw = Path(path).read_bytes().replace(b"\r\n", b"\n")
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _const(name):
    src = Path("ahig/ahig/search/statistical_termination.py").read_text(encoding="utf-8")
    m = re.search(rf"^{name}\s*=\s*([0-9.]+)\s*$", src, re.M)
    if not m:
        raise KeyError(name)
    return float(m.group(1)) if "." in m.group(1) else int(m.group(1))


def _anchors():
    """⚠️ 由 n116 之 ANCHORS 現數，🚫 不手抄——n+116 之條目會增。"""
    src = Path(".scratch/n116_obligation_crosscheck.py").read_text(encoding="utf-8")
    ns = {}
    exec("ANCHORS = {" + src.split("ANCHORS = {", 1)[1].split("\n}\n", 1)[0] + "\n}", ns)
    a = ns["ANCHORS"]
    restated = sum(1 for v in a.values()
                   if any("重述" in str(x) or "同上" in str(x) for x in v))
    return len(a), restated


def _ver(key):
    """n486（8 筆）＋ n487（33 筆）之版本分布合計。⚠️ 兩批互斥，合為 41 筆。"""
    from collections import Counter
    c = Counter(r["version"] for r in J(N486)["records"])
    return c.get(key, 0) + J(N487)["versionDistribution"].get(key, 0)

# 🚨 兩格取自同一來源欄位，且**這是刻意的**——須逐對寫明，🚫 不得默默重合。
SAME_SOURCE_OK = {
    ("NOT_SCREENED_STD", "OCC2_POP"):
        "⚠️ 同一欄位（尾端抽驗母體），兩個名字分別用於閉合式與第二次抽驗；"
        "🚫 報告不得寫成兩次獨立量測。",
}

# ── 🚨 同值異義之登記簿 ──────────────────────────────────────────
# ⚠️ 兩個不相干的量現算後恰好相等。**🚫 那不是缺陷**——
# 🚨 但它是本 run 反覆出現的一族（兩個 33、兩個 10、兩個 3），
# **⚠️ 危險只在報告把它們寫在相鄰處時才發生**，而那時已經來不及查。
# ✅ 故逐對登記，並寫明「它們各自是什麼」。🚫 未登記者視為未查。
#
# ⚠️ **本簿設有下限，而那是一個判斷，須寫明**：只登記 `值 ≥ 10` 之重合。
# 🚨 初版沒有下限，於是 78 格小整數在 0–8 上互撞十餘次，**逐對要求登記**。
# **⚠️ 那不是嚴謹，是把我訓練成蓋章的人**——🚫 一份人人都得簽的清單，簽名就不再有意義。
# ✅ 且實際發生過的每一例（兩個 33、兩個 10、兩個 15、兩個 16）**都在下限之上**。
# 🚫 故本檔明白放棄小數值之重合：**抓不到「兩個 3 被寫在一起」**。
MIN_COINCIDENCE = 10

COINCIDENCE = {
    # 🚨 鍵為**該值上的整組名稱**（排序後），🚫 不是任意兩格——
    # ⚠️ 多一格加入同一個值時，這一筆就不再匹配，會逼我重新判一次。
    ("BLOCKED_N", "DEBT_B4", "PDF_IN_HAND"):
        "11＝本環境遭擋之筆數（403 十筆＋逾時一筆）；11＝影子歧異之尚欠抽查項目；"
        "11＝私有 pdf 快取之檔數。🚫 三者互不相干，"
        "⚠️ 且**單位各異**（文獻／抽查項目／檔案）。",
    ("HARMS_COUNTER_LAST", "OBLIGATION_RESTATED"):
        "10＝harms 相鄰計數器之最終讀數（🚨 讀數，不是名單）；"
        "10＝義務清冊中標為「重述／同上」之條數。"
        "⚠️ 本 run 早期即出現過的一對，🚫 兩者毫無關係。",
    ("HARMS_COMBINED", "LANDING_REPO", "SHORTFALL_N"):
        "15＝S5＋S6 合併配額（8＋7）；15＝著陸頁落在機構典藏庫者；"
        "15＝校準集之總缺口（60−45）。"
        "🚨 前兩者與第三者都出現在辛節，⚠️ 而「配額 15」與「缺口 15」相鄰書寫"
        "會讀成「這一層剛好全缺」——**🚫 實際 S5＋S6 之缺口是 6，不是 15。**",
    ("DEBT_OUTSTANDING", "LANDING_REACHED", "LANDING_ROUTE_N"):
        "🚨 **本簿最危險的一組，且其中兩格同節、同一批 33 筆記錄**："
        "16＝`status == available-landing-page`（**路徑分類**）；"
        "16＝`http == 200`（**當時抓得到**）。"
        "**⚠️ 實測交集僅 6 筆**——各有 10 筆只落在其中一邊。"
        "🚫 故報告不得寫「16 筆走著陸頁路徑，其中 16 筆可達」，"
        "**🚨 那會讀成「全部可達」，而實情是 16 筆裡只有 6 筆可達。**"
        "⚠️ 第三個 16 是尚欠之抽查項目，**單位是抽查項目而非文獻**，🚫 與前兩者無關。",
    ("OUT_OF_SEQ", "SPOT_N"):
        "200＝標準線序列之亂序筆數；200＝尾端抽驗之樣本數常數。"
        "⚠️ 兩者同在丙節且皆與篩選序列有關，🚨 相鄰書寫極易被讀成同一個 200。",
    ("ACQ_IN_OBTAINABLE", "UNPROBED_N"):
        "⚠️ **兩者都在講取得，故須特別分清**："
        "12＝45 筆可得之中 JATS 已在手者；"
        "12＝從未被試過替代位址者（校準 60＋補集中 status 為 available-* 者）。"
        "🚨 前者是**已經有了**，後者是**還沒試過**——🚫 相鄰書寫會讀成同一批 12 筆。",
    ("PAGES_BETWEEN", "UNTITLED_SECTIONS"):
        "20＝兩次終止之間的頁數（299−279）；20＝無標題章節數。🚫 毫無關係。",
}

# 🚨 跨產物之閉合式：版本四桶須合為 n496 之 acquired。
# ⚠️ 這一條是本檔唯一「不靠任何自報值」的檢查——🚫 它只靠兩份產物彼此對得上。
def closure_checks(resolved):
    out = []
    need = {"VER_PUBLISHED", "VER_ACCEPTED", "VER_SUBMITTED", "VER_UNKNOWN"}
    if need <= set(resolved):
        total = sum(resolved[k] for k in need)
        acquired = J(N496)["acquired"]
        if total != acquired:
            out.append(f"🚨 版本四桶合計 {total} ≠ `n496` 之 acquired {acquired}"
                       "——⚠️ 兩份產物對不上，其一已過期")

    # 🚨 n+155：辛節第 442 行寫著「三格相加須等於 45」。
    # ⚠️ 而一條寫在文件裡的規則不會自己執行（n+132）——故在此執行它。
    # 🚨 辛節寫著「四個不足之池皆標 exhausted: true」（n+100 二）。
    # ⚠️ 那是一句宣稱，🚫 不是一項檢查——故在此執行它。
    pools = J(BACKFILL)["pools"]
    short = {p["poolId"] for p in pools if p["shortfall"] > 0}
    exh = {p["poolId"] for p in pools if p["exhausted"]}
    if short != exh:
        out.append(f"🚨 有缺口之池 {sorted(short)} ≠ 標 exhausted 之池 {sorted(exh)}"
                   "——⚠️ 「填不滿者皆已窮盡」這句話不再成立")
    if sum(p["shortfall"] for p in pools) != J(BACKFILL)["totals"]["shortfall"]:
        out.append("🚨 逐池缺口合計 ≠ `totals.shortfall`")

    # 🚨 丙節第二節寫著「池子閉合 SEQ_LEN ＋ OUT_OF_SEQ ＋ NOT_SCREENED_STD ＝ N_TOTAL_STD」，
    # ⚠️ 而 n+80 之分母裁定就是靠這條閉合式成立的——**🚫 它從未被執行過。**
    pool = {"SEQ_LEN", "OUT_OF_SEQ", "NOT_SCREENED_STD", "N_TOTAL_STD"}
    if pool <= set(resolved):
        lhs = (resolved["SEQ_LEN"] + resolved["OUT_OF_SEQ"]
               + resolved["NOT_SCREENED_STD"])
        if lhs != resolved["N_TOTAL_STD"]:
            out.append(f"🚨 標準線池子閉合式不成立：{lhs} ≠ {resolved['N_TOTAL_STD']}"
                       "——⚠️ n+80 之分母裁定即建立在這條閉合式上")

    route = {"ACQ_IN_OBTAINABLE", "PDF_ROUTE_N", "LANDING_ROUTE_N"}
    if route <= set(resolved) and "OBTAINABLE_N" in resolved:
        s, ob = sum(resolved[k] for k in route), resolved["OBTAINABLE_N"]
        if s != ob:
            out.append(f"🚨 三條取文路徑合計 {s} ≠ 可得 {ob}"
                       "——⚠️ 三格並非同一母體，或其一已過期")
    return out


def parse_rows():
    text = Path(CHECKLIST).read_text(encoding="utf-8")
    body = text.split("BEGIN GENERATED n115", 1)[-1].split("END GENERATED n115", 1)[0]
    rows = []
    for line in body.split("\n"):
        m = ROW.match(line)
        if m and m.group(2) != "佔位符":
            rows.append(dict(sec=m.group(1), name=m.group(2), kind=m.group(3),
                             srctype=m.group(4), locator=m.group(5)))
    return rows


def run(rows, label):
    problems, resolved = [], {}
    reachable = [r for r in rows if r["srctype"] in ("產物", "原始碼", "推導")]
    for r in reachable:
        fn = RESOLVERS.get(r["name"])
        if fn is None:
            if r["name"] not in UNRESOLVABLE:
                problems.append(
                    f"🚨 {r['name']}：既無解析器亦未登記為「定位欄不足以決定值」"
                    "——⚠️ 那等於這一格沒有人在管")
            continue
        try:
            val = fn()
        except Exception as exc:                       # noqa: BLE001
            problems.append(f"{r['name']}：解析器丟出 {type(exc).__name__}：{exc}")
            continue
        resolved[r["name"]] = val
        m = SELF_VALUE.search(r["locator"])
        if m and not same_value(m.group(1), val):
            problems.append(
                f"🚨 {r['name']}：定位欄自報 **{m.group(1)}**，現算得 **{val}**")

    # 🚨 同來源重合之偵測
    by_val = {}
    for name, val in resolved.items():
        by_val.setdefault(f"{val}", []).append(name)
    # 🚨 同值異義之掃描已移至 main() 之全域一遍（含看板型）。
    # ⚠️ 原本這裡還有一遍只掃「可及列」的——🚫 兩遍共用一份登記簿，
    # 而同一組數在兩遍裡一個是「兩格」一個是「三格」，**登記簿對不上任何一邊。**
    problems += closure_checks(resolved)

    # 🚨 n+155 修正本檔自己的計數單位錯：原印
    #     「可及格 88｜已解 82｜未解 6」
    # ⚠️ 而 88 是**列數**（同一佔位符可出現在數節），82 是**相異名稱數**——
    # 🚨 兩個單位相減，得到一個不指任何東西的 6。
    # **⚠️ 這正是本檔在替別人抓的那一族，發生在本檔身上。**
    unres = [r["name"] for r in reachable if r["name"] not in RESOLVERS]
    print(f"=== {label} ===")
    print(f"  可及**列** {len(reachable)}｜其中有解析器 {len(reachable) - len(unres)}"
          f"｜無解析器 {len(unres)}")
    print(f"  （相異**佔位符** {len({r['name'] for r in reachable})} 個，"
          f"**已解 {len(resolved)}** 個｜未解 {len(set(unres))} 個）")
    for p in problems:
        print(f"  {p}")
    if not problems:
        print("  ✅ 已解之格全部與定位欄自報值相符，且版本閉合式對得上")
    return problems, resolved, reachable


def _numeric(x):
    try:
        float(x)
        return True
    except (TypeError, ValueError):
        return False


def same_value(claimed, got):
    """定位欄自報值 vs 現算值。

    ⚠️ 自報值帶千分位（`22,761`），且**精度往往被截短**（`0.3652` vs 0.36519…）。
    🚨 故數值比對以「自報值之小數位數」為準四捨五入後比——
    🚫 而這是一個放寬，須寫明：**本檔抓得到「值變了」，抓不到「值只在末位變了」。**
    """
    claimed = claimed.replace(",", "")
    if f"{got}" == claimed:
        return True
    try:
        c, g = float(claimed), float(got)
    except (TypeError, ValueError):
        return False
    dp = len(claimed.split(".")[1]) if "." in claimed else 0
    return round(g, dp) == round(c, dp)


def value(name):
    """給別的產生器用：取單一格之現算值。

    🚨 **🚫 找不到解析器時丟例外，不回 None**——
    ⚠️ 回 None 會讓呼叫端把「沒量到」印成一個空格，而空格看起來像零。
    """
    if name not in RESOLVERS:
        raise KeyError(f"{name}：無解析器"
                       f"{'（已登記為定位欄不足以決定值）' if name in UNRESOLVABLE else ''}")
    return RESOLVERS[name]()


def main():
    rows = parse_rows()
    real, resolved, reachable = run(rows, "實際文件")

    # ── 🚨 反向對照：把一格的自報值改掉，本檔須抓到 ──────────────────
    # ⚠️ 依 n+131 三：注入物落在本檢查有能力判定的範圍內（有解析器、有自報值）。
    victim = next(r for r in rows
                  if r["name"] in RESOLVERS and SELF_VALUE.search(r["locator"]))
    bad = dict(victim)
    bad["locator"] = SELF_VALUE.sub("＝**99999**", victim["locator"], count=1)
    ctrl, _, _ = run([bad], "反向對照（注入：定位欄自報值改為 99999）")
    caught = any("99999" in p for p in ctrl)

    # ── 🚨 第二道反向對照：看板原文不見了，引用須當場失效 ────────────
    # ⚠️ 這是本輪新機制，🚫 未經測試的護欄不算護欄（n+134）。
    # ✅ 不改檔案，改讀到的內容——把錨句從記憶中的看板文字裡拿掉。
    _real_read = Path.read_text
    victim2 = sorted(BOARD_CITED)[0]
    _anchor = BOARD_CITED[victim2][1]

    def _tampered(self, *a, **k):
        t = _real_read(self, *a, **k)
        return t.replace(_anchor, "〔本段已被移除〕") if self.name == "COORDINATION.md" else t

    Path.read_text = _tampered
    try:
        _board_cited(victim2)
        caught2 = False
    except ValueError:
        caught2 = True
    finally:
        Path.read_text = _real_read
    print(f"反向對照二（抽掉 {victim2} 之看板原文）："
          f"{'✅ 引用當場失效' if caught2 else '🚨 原文不見了卻照樣回值'}")

    # ── 🚨 同值異義之第二遍：涵蓋**全部**可解之格，含看板型 ──────────
    # ⚠️ 第一遍只掃「可及列」，而看板型不在其中——
    # 🚨 本 run 最早的同值異義例（兩個 33）正是看板型 `UNTRACEABLE_N`，
    # **⚠️ 亦即那個偵測器原本掃不到它自己的第一個案例。**
    allv = {}
    for name in RESOLVERS:
        try:
            allv.setdefault(f"{RESOLVERS[name]()}", []).append(name)
        except Exception:                              # noqa: BLE001
            pass
    extra, noted = [], []
    for val, names in sorted(allv.items()):
        if len(names) < 2 or not _numeric(val) or abs(float(val)) < MIN_COINCIDENCE:
            continue
        key = tuple(sorted(names))
        if key in SAME_SOURCE_OK:
            continue
        if key in COINCIDENCE:
            noted.append(f"⚠️ 已登記 {'＝'.join(key)}＝{val}：{COINCIDENCE[key]}")
            continue
        extra.append(f"🚨 {'、'.join(key)} 皆為 {val}，**未登記**")
    print()
    print("=== 全域同值掃描（含看板型，值 ≥ "
          f"{MIN_COINCIDENCE}）===")
    for n in noted:
        print(f"  {n}")
    for e in extra:
        print(f"  {e}")
    if not extra:
        print("  ✅ ≥10 之重合皆已登記")
    real += extra

    print()
    print(f"反向對照：{'✅ 抓到過期的自報值' if caught else '🚨 沒抓到——本檢查有盲區'}")
    inacc = sum(1 for r in rows if r["srctype"] == "不可及")
    print(f"⚠️ 另有 {inacc} 格為「不可及」，屬執行室 `n500` 之範圍，🚫 本檔不碰。")

    # 🚨 看板型之格**不在 reachable 之內**，⚠️ 而它們一樣要被填。
    # 🚫 不得因為它們不在覆蓋率的分母裡，就當成不存在。
    board = {r["name"] for r in rows if r["srctype"] == "看板"}
    board_done = sorted(board & set(RESOLVERS))
    board_open = sorted(board - set(RESOLVERS) - set(UNRESOLVABLE))
    print(f"⚠️ 另有看板型 {len(board)} 格**不在上列分母內**："
          f"已綁原文查核 {len(board_done)} 格｜"
          f"已登記為不可綁 {len(board & set(UNRESOLVABLE))} 格｜"
          f"🚨 **未處理 {len(board_open)} 格**{('：' + '、'.join(board_open)) if board_open else ''}")
    if board_open:
        problems.append(f"🚨 看板型尚有 {len(board_open)} 格既未綁原文亦未登記"
                        "——⚠️ 它們一樣要被填，🚫 不得因不在分母裡就當成不存在")

    print()
    print("🚨 **定位欄不足以決定值之格**（⚠️ 交付當日只能由人手填，而那正是猜）：")
    for name, why in UNRESOLVABLE.items():
        print(f"  · {name}：{why}")
    print(f"🚫 **上列 {len(UNRESOLVABLE)} 格不是通過，是待裁。**")
    return 1 if (real or not caught or not caught2) else 0


if __name__ == "__main__":
    sys.exit(main())
