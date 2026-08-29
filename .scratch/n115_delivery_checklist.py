"""Generate the placeholder table inside docs/m1-e-delivery-checklist.md.

The four M1 section skeletons each carry their own appendix source table.
This script merges all four into one delivery table and adds two columns the
per-section tables do not have:

  來源型態  - can the cited authority actually be opened from this repo?
  定位      - the exact file + JSON path (or the reason there isn't one)

Fails loudly if a skeleton gains a placeholder with no DETAIL entry, so a new
placeholder cannot silently reach delivery without a named locator.

Run:  python3 .scratch/n115_delivery_checklist.py
"""

import re
from pathlib import Path

FILES = {
    "甲": "docs/m1-a-search-coverage-skeleton.md",
    "乙": "docs/m1-b-screening-limits-skeleton.md",
    "丙": "docs/m1-c-termination-skeleton.md",
    "丁": "docs/m1-d-audit-debt-skeleton.md",
    "庚": "docs/m1-f-harms-skeleton.md",
    "辛": "docs/m1-g-acquisition-skeleton.md",
}
TARGET = "docs/m1-e-delivery-checklist.md"
BEGIN = "<!-- BEGIN GENERATED n115 -->"
END = "<!-- END GENERATED n115 -->"

PLACEHOLDER = re.compile(r"\{\{([A-Z0-9_]+)\}\}")
ROW = re.compile(r"^\|\s*(`[^|]+`)\s*\|\s*([^|]+?)\s*\|\s*(.+?)\s*\|\s*$")
CODE = re.compile(r"`([A-Z0-9_*]+)`")

EV = "`.scratch/n78_termination_evidence.json`"
SR = "`ahig/analysis/results/synergy_replay.json`（**受追蹤**）→ `aggregate"

# 來源型態:
#   產物   一個可從本 repo 開啟的檔案（可重現、部分帶雜湊）
#   原始碼 版控之常數，git 可回溯
#   推導   由兩個其他值相減／相加而得，本身無來源
#   看板   只有看板留痕，無產物、無雜湊
#   不可及 權威來源在私有根或未入版控，協調者無法自行核對
DETAIL = {
    "ALPHA":            ("原始碼", "`statistical_termination.py` `DEFAULT_ALPHA` = 0.05"),
    "TARGET_RECALL":    ("原始碼", "同檔 `DEFAULT_TARGET_RECALL` = 0.95"),
    "SPOT_N":           ("原始碼", "同檔 `DEFAULT_TAIL_SPOT_CHECK_N` = 200"),
    "W7_WALKS":         ("產物", SR + '[*].walks`＝2270（六組皆同）'),
    "W7_RANDOM":        ("產物", SR + "['random@look100'].violationRate`＝0.0115"),
    "W7_ADVERSARIAL":   ("產物", SR + "['adversarial@look100'].violationRate`＝0.3652"),
    "W7_TRIPWIRE_CATCH": ("產物", SR + "['adversarial@look100'].meanTailCatchOnViolation`＝0.8893"),
    "N_TOTAL_STD":      ("產物", EV + " → `standardLaneSequence.nTotal`"),
    "SEQ_LEN":          ("產物", EV + " → `standardLaneSequence.screenedCount`"),
    "OUT_OF_SEQ":       ("產物", EV + " → `standardLaneSequence.outOfSequenceCount`"),
    "NOT_SCREENED_STD": ("產物", EV + " → `tailSpotCheckPopulation.count`（**閉合式之第三項**）"),
    "OCC1_PAGE":        ("產物", EV + " → `previousOccurrence.atPage`"),
    "OCC1_P":           ("產物", EV + " → `previousOccurrence.pScore`"),
    "OCC1_W":           ("產物", EV + " → `previousOccurrence.windowSize`"),
    "OCC1_POP":         ("產物", "`.scratch/n68_termination_evidence.json` 之尾端抽驗母體"),
    "OCC1_HITS":        ("產物", "`.scratch/n68_tail_result.json`（⚠️ 命中 2 筆，即絆網攔下者）"),
    "OCC2_P":           ("產物", EV + " → `standardLaneSequence.pScore`"),
    "OCC2_W":           ("產物", EV + " → `standardLaneSequence.windowSize`"),
    "OCC2_POP":         ("產物", EV + " → `tailSpotCheckPopulation.count`"),
    "OCC2_HITS":        ("產物", "`.scratch/n78_tail_result.json` → `result.relevantOrUnclearFound` **之長度**（非欄位值）"),
    "TRIGGER_CAUSE_ID": ("產物", EV + " → `triggerCause.candidateId`"),
    "P_ALLQUEUE":       ("產物", EV + " → `evaluateTerminationStandardBasis.pScore`（⚠️ 僅用於呈示禁句）"),
    "PAGES_BETWEEN":    ("推導", "**已定案＝20**（299 − 279）；依據見第四節（四）"),
    "ORPHAN_N":         ("看板", "看板 23514–23515；⚠️ 私有根之 `critical-harms-sweep-orphans` 工作單協調者不可及"),
    "COLLISION_N":      ("產物", "`docs/w4b-design-inputs.md`（**受追蹤**）之 `C-*` 相異編號＝**40**（⚠️ 檔內排列非遞增，🚫 不得以「順序遞增」查完備）"),
    "TITLE_ONLY_N":     ("不可及", "私有根 `title-only-judged-roster.json` → `entryCount`＝**175**（執行室量測）；🚨 不得以判讀理由文字代算"),
    "TITLE_ONLY_EXPECTED_GAP": ("不可及", "🚨 **須重算**：底數 77→133→175 而衍生數一直寫「約 10」；舊率 14.7% 取自特定段落，不得直接套用（n+121）"),
    "UNTRACEABLE_N":    ("看板", "看板 61541／61653：33 段設計輸入無 `candidateId` 可對應"),
    # 🚫 `SEX_REPRESENTATION` 作廢（n+120）：該名稱把行為差異標成樣本組成。
    "PLANNING_RATE_OVERALL": ("看板", "看板 49702：菁英層級補給規劃率（⚠️ **規劃率，非佔比**）"),
    "PLANNING_RATE_M":  ("看板", "同上，男性 91–93%"),
    "PLANNING_RATE_F":  ("看板", "同上，女性 67–72%"),
    "SEX_SAMPLE_COMPOSITION": ("不可及", "證據體之性別組成，私有根名冊；🚨 與規劃率是兩個量"),
    "THRESHOLD3_STRATA": ("看板", "看板 47448–47460：三分層之門檻 3 實測 **1.52**"),
    "THRESHOLD3_SUBGROUP": ("看板", "同上：「補得到」子群體之門檻 3 實測 **1.76**（🚨 與 1.52 是兩個檢定）"),
    "THRESHOLD3_VALUE": ("看板", "同上：事前門檻 1.5"),
    "THRESHOLD3_GAP":  ("看板", "同上：差 0.02 倍而未放寬"),
    "FISHER_P":        ("看板", "同上：Fisher p=0.0011"),
    "ADVANCE_EXPECTED": ("看板", "同上：advance 側兩段合計期望 16.9 筆"),
    "ADVANCE_OBSERVED": ("看板", "同上：實測 1 筆"),
    "SIGNAL_DENSITY_RATIO": ("看板", "同上：標題碳水訊號密度相差 26.57 倍"),
    "SHADOW_CONCORDANT": ("不可及", "私有根 `machine-reconciliation.json` → `counts.concordantCount`＝**288**（執行室量測）"),
    "SHADOW_QUEUED":    ("不可及", "同上 → `counts.ownerAuditCount`＝**12**（執行室量測）"),
    "DEBT_B4":          ("看板", "影子歧異之尚欠項 11（未解決者，n+106 裁定；單位＝抽查項目）"),
    "DEBT_CUMULATIVE":  ("看板", "n+108：**22**（相加 23、重疊 1，已去重）"),
    "DEBT_SETTLED":     ("看板", "n+108：**6**"),
    "DEBT_OUTSTANDING": ("看板", "n+108：**16**（W2 之 5 ∪ 影子 11）——⚠️ 單位＝**抽查項目**，非文獻"),
    # ── n+118：庚節（harms）與辛節（取得可行性），n+117 三查出這兩節從未起草 ──
    "HARMS_S5_QUOTA":   ("不可及", "私有根 `strata.json` 之 S5 配額（執行室量測）"),
    "HARMS_S6_QUOTA":   ("不可及", "同上 S6 配額"),
    "HARMS_COMBINED":   ("不可及", "同上，S5＋S6 合併抽樣單位（n+98 裁示）"),
    "HARMS_S5_ACTUAL":  ("不可及", "🚨 **全文取得後才存在**；不得為填滿配額而放寬判準"),
    "HARMS_ADJACENT_N": ("不可及", "harms 相鄰素材名單（私有根）；⚠️ 本 run 內曾 4→5→6"),
    "CALIBRATION_TARGET": ("看板", "ADR-0010 與 `strata.json` 之 `totalSampleSize`"),
    "S7_POOL_N":        ("看板", "看板 63655 一帶之清點（S7 全池）"),
    "PMC_MISS_NO_ID":   ("產物", "`.scratch/n439_route_cost.json` → `europePmcMissCauses`（無 PMCID）"),
    "PMC_MISS_404":     ("產物", "同上（已知 PMCID 但 `fullTextXML` 404）"),
    "OBTAINABLE_N":     ("產物", "`.scratch/m1_step3_inventory.json`＋`m1_step3_backfill.json`；⚠️ **上界非保證**"),
    "SHORTFALL_N":      ("看板", "校準集設計數 − 可得數，交付時現算"),
    "SHORTFALL_S7":     ("看板", "看板 63655 三之缺口分布"),
    "SHORTFALL_HARMS":  ("看板", "同上（S5+S6）"),
    "ACQUIRED_N":       ("產物", "`.scratch/m1_step3_inventory.json` 之 `acquired`"),
    "PDF_ROUTE_N":      ("產物", "同上 `available-pdf`"),
    "LANDING_ROUTE_N":  ("產物", "同上 `available-landing-page`"),
    "LANDING_REPO":     ("產物", "`.scratch/n439_route_cost.json` → `landingKindsAggregate`（機構典藏庫）"),
    "LANDING_PUBLISHER": ("產物", "同上（出版社；⚠️ 經 doi.org 轉址解出後由 9 增為 13）"),
    "LANDING_FIGSHARE": ("產物", "同上（figshare，有 API）"),
    "LANDING_PMC_SCAN": ("產物", "同上（PMC 掃描件）"),
}


def split_appendix(text):
    i = text.find("## 附：佔位符來源表")
    return (text, "") if i < 0 else (text[:i], text[i:])


def expand(name, used):
    if not name.endswith("*"):
        return [name]
    return sorted(u for u in used if u.startswith(name[:-1]))


rows = []
for sec, rel in FILES.items():
    text = Path(rel).read_text(encoding="utf-8")
    body, appendix = split_appendix(text)
    used = sorted(set(PLACEHOLDER.findall(body)))
    listed = {}
    for line in appendix.split("\n"):
        m = ROW.match(line)
        if not m:
            continue
        cell, klass, source = m.groups()
        if "佔位符" in cell:
            continue
        for raw in CODE.findall(cell):
            for name in expand(raw, used):
                listed[name] = klass.strip()
    for name in used:
        klass = listed.get(name, "")
        assert klass, f"{sec} {name}: 該檔附表未列來源"
        assert name in DETAIL, f"{name}: DETAIL 未收——新佔位符不得無定位即交付"
        tag = "凍結" if "凍結" in klass else ("漂移" if "漂移" in klass else "❓")
        kind, where = DETAIL[name]
        rows.append((sec, name, tag, kind, where))

extra = sorted(set(DETAIL) - {r[1] for r in rows})
assert not extra, f"DETAIL 有已不存在之佔位符：{extra}"

lines = [BEGIN,
         "",
         f"共 **{len(rows)}** 個佔位符。"
         f"凍結 **{sum(1 for r in rows if r[2] == '凍結')}**、"
         f"漂移 **{sum(1 for r in rows if r[2] == '漂移')}**；"
         f"其中 **{sum(1 for r in rows if r[3] == '不可及')}** 個之權威來源"
         f"**協調者無法自行核對**（見下文第二節）。",
         "",
         "| 節 | 佔位符 | 類別 | 來源型態 | 定位 |",
         "|---|---|---|---|---|"]
for sec, name, tag, kind, where in rows:
    lines.append(f"| {sec} | `{name}` | {tag} | {kind} | {where} |")
lines += ["", END]

doc = Path(TARGET).read_text(encoding="utf-8")
i, j = doc.index(BEGIN), doc.index(END) + len(END)
Path(TARGET).write_text(doc[:i] + "\n".join(lines) + doc[j:],
                        encoding="utf-8", newline="\n")
print(f"wrote {len(rows)} rows into {TARGET}")
for kind in ("產物", "原始碼", "推導", "看板", "不可及"):
    print(f"  {kind}: {sum(1 for r in rows if r[3] == kind)}")
