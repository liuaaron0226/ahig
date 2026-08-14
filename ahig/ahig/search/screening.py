#!/usr/bin/env python3
"""建立 B.11 title/abstract screening 的確定性優先佇列。

輸出只有 priority、lane、concept hints 與 safety/identity flags。每一筆都固定
``requiresHumanScreening=true``、``autoDecision=null``；本模組沒有 include/exclude
詞彙，也不允許把低分候選從 queue 移除。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Any

from ahig.contracts.freeze import content_hash
from ahig.state import atomic_write_json

# 1.4.0：動物訊號詞表補強（W1）。舊詞表只涵蓋哺乳實驗動物，實測漏抓魚類、
#         家禽與乳牛研究。
# 1.5.0：劑量 regex 升級（W3）。新增 g/min、括號負號與 HTML 上標、
#         濃度×體積×頻率換算、共用單位列舉；並排除代謝速率誤收。
# **升版不等於現行 queue 已重建**——重建會改動 screeningQueueHash，使
# audit 22f634d2325d／0030677e77bf 的源頭重放護欄失效。W5 才重建，
# 屆時 1.4.0＋1.5.0 一起生效（見 COORDINATION.md 的協調者裁定）。
RULE_VERSION = "b11-screening/1.5.0"

# 每個 pattern 都只是提示訊號，絕不是資格判定。
CONCEPTS: dict[str, tuple[str, tuple[str, ...]]] = {
    "population": ("SCREEN-001-population", (
        r"\bathlet\w*\b", r"\btrained\b", r"\bwell[- ]trained\b",
        r"\bendurance[- ]trained\b", r"\bcyclist\w*\b", r"\brunner\w*\b",
        r"\btriathl\w*\b", r"\bcompetitive\b", r"\belite\b")),
    "intervention": ("SCREEN-002-carbohydrate", (
        r"\bcarbohydrat\w*\b", r"\bglucose\b", r"\bfructose\b",
        r"\bsucrose\b", r"\bmaltodextrin\b", r"\bcho\b",
        r"\bmultiple transportable\b")),
    "exercise": ("SCREEN-003-exercise", (
        r"\bexercis\w*\b", r"\bendurance\b", r"\bcycling\b",
        r"\bcyclist\w*\b", r"\brunning\b", r"\brunner\w*\b",
        r"\btriathl\w*\b", r"\btime trial\b", r"\btime to exhaustion\b")),
    "timing": ("SCREEN-004-ingestion-timing", (
        r"\bingest\w*\b", r"\bintake\b", r"\bfeeding\b", r"\bfed\b",
        r"\bbeverage\w*\b", r"\bdrink\w*\b", r"\bgels?\b",
        r"\bduring (?:prolonged )?exercis\w*\b", r"\bbefore exercis\w*\b",
        r"\bpre[- ]exercise\b", r"\bintra[- ]exercise\b")),
}

OUTCOMES: dict[str, tuple[str, tuple[str, ...]]] = {
    "tt-completion-time": ("SCREEN-010-time-trial", (
        r"\btime[- ]trial\b", r"\btime trial\b", r"\bcompletion time\b")),
    "time-to-exhaustion": ("SCREEN-011-tte", (
        r"\btime to exhaustion\b", r"\btime-to-exhaustion\b", r"\btte\b")),
    "exogenous-cho-oxidation-peak": ("SCREEN-012-exogenous-oxidation", (
        r"\bexogenous (?:carbohydrate|cho|glucose) oxidation\b",
        r"\b13c\b", r"\btracer\b", r"\boxidation rate\b")),
    "gi-symptom-incidence": ("SCREEN-013-gi-harms", (
        r"\bgastrointestinal\b", r"\bgi symptoms?\b", r"\bgi distress\b",
        r"\bnausea\b", r"\bvomit\w*\b", r"\bdiarrh\w*\b",
        r"\babdominal (?:pain|cramp\w*)\b")),
    "gi-symptom-severity": ("SCREEN-014-gi-severity", (
        r"\bgastrointestinal symptom severity\b", r"\bgi severity\b",
        r"\bgi symptom score\b")),
    "muscle-glycogen-post-exercise": ("SCREEN-015-glycogen", (
        r"\bmuscle glycogen\b", r"\bglycogen concentration\b",
        r"\bglycogen resynthesis\b", r"\bmuscle biopsy\b")),
}

SAFETY: dict[str, tuple[str, tuple[str, ...]]] = {
    "safety-red-s": ("SCREEN-020-safety-red-s", (
        r"\breds\b", r"\bred[- ]s\b", r"\brelative energy deficiency\b")),
    "safety-low-energy-availability": ("SCREEN-021-safety-lea", (
        r"\blow energy availability\b", r"\benergy availability\b")),
    "safety-rapid-weight-loss": ("SCREEN-022-safety-weight-cut", (
        r"\brapid weight loss\b", r"\bweight cutting\b", r"\bmaking weight\b")),
    "safety-clinical-metabolic": ("SCREEN-023-safety-clinical", (
        r"\bdiabet\w*\b", r"\binflammatory bowel\b", r"\bcoeliac\b",
        r"\bceliac\b")),
}

SCORE = {"population": 2, "intervention": 4, "exercise": 3,
         "timing": 2, "outcomes": 3}
LANE_ORDER = {"safety-review": 0, "identity-review": 1,
              "registry-review": 2, "review-source-review": 3,
              "animal-signal-review": 4, "standard-screening": 5}
TIER_ORDER = {"T1-high-signal": 0, "T2-moderate-signal": 1, "T3-partial-signal": 2,
              "T4-broad-signal": 3, "T5-low-signal": 4}


def normalise_for_matching(raw: Any) -> str:
    value = unicodedata.normalize("NFKC", str(raw or "")).lower()
    value = value.replace("–", "-").replace("−", "-")
    return re.sub(r"\s+", " ", value).strip()


def _matches(text: str, patterns: tuple[str, ...]) -> bool:
    return any(re.search(pattern, text, flags=re.I) for pattern in patterns)


DOSE_MIN_G_PER_H = 10.0
DOSE_MAX_G_PER_H = 200.0

# 速率語彙出現在數值前方時代表「身體燒掉多少」而非「嘴巴吃進多少」。
# W2 補抽第 31 筆的實測陷阱：摘要的 169 g.h-1 是總醣氧化速率，
# 誤收會直接把該篇灌進 high band。
#
# 但同一句同時出現氧化與攝取是常態（「oxidation was measured while
# cyclists ingested 60 g/h」），所以攝取動詞優先：只有在數值前方既有
# 代謝語彙、又沒有攝取動詞介入時才判為代謝速率。
_OXIDATION_CONTEXT = re.compile(
    r"(?:oxidation|oxidised|oxidized|turnover|appearance|disappearance|"
    r"clearance|expenditure)"
    r"(?:(?!ingest|consum|drank|drink|fed|feeding|intake|supplement|"
    r"provid|administer)[^.;])*$", flags=re.I)

# 每小時飲液量：600 ml/h、1 l·h-1。
_VOLUME_PER_H = (r"(\d{1,4}(?:\.\d+)?)\s*(ml|millilitres?|milliliters?|l|"
                 r"litres?|liters?)\s*(?:/\s*h|[·. ]?h\s*[-^]?\s*1|"
                 r"per\s+hour|/\s*hour)")
# 定量定頻：200 ml … every 20 min（順序兩種寫法都有）。
# 摘要慣寫 mean ± SD（「227 +/- 3 ml」），此時帶單位的是誤差項而非量值，
# 故允許數值與單位之間夾一段 ± 誤差，並以第一個數字為量值。
_VOLUME_EVERY = (r"(\d{1,4}(?:\.\d+)?)\s*(?:(?:\+/-|±)\s*\d+(?:\.\d+)?\s*)?"
                 r"(ml|millilitres?|milliliters?|l|litres?|liters?)\b")
# 定頻的兩種寫法：every 20 min／at 15-min intervals。
_EVERY_MIN = (r"(?:every\s+(?P<every>\d{1,3})\s*(?:min|minutes?)\b"
              r"|(?P<interval>\d{1,3})\s*-?\s*min(?:ute)?\s+intervals?\b)")
_PERCENT = r"(\d{1,2}(?:\.\d+)?)\s*%"


def _band_for(value: float) -> str:
    if value < 30:
        return "low"
    if value < 60:
        return "moderate"
    if value < 90:
        return "high"
    return "very-high"


def _oxidation_context(text: str, start: int) -> bool:
    """數值是否落在代謝速率語境（而非攝取速率）。

    只看同一子句：從最近的句讀切起，避免跨句誤判。
    """
    head = re.split(r"[.;]", text[:start])[-1]
    return bool(_OXIDATION_CONTEXT.search(head))


def _dose_signals(text: str) -> list[dict]:
    """摘要層劑量速率的 band hint——只作提示，不作 extraction。

    W3 起支援三種在真實文獻裡常見、舊版全數漏抓的樣式（樣式清單來自
    prevalence audit 0030677e77bf 的 regexAudit：13 筆 exact-value 中
    有 11 筆漏抓）：

    1. ``g/min`` 單位——多重可運輸醣類文獻的慣用寫法，乘 60 換算；
    2. ``g·h(-1)`` 括號負號——有兩篇連標題都寫著劑量仍漏抓；
    3. 濃度 × 體積 × 頻率——摘要常只寫「每 20 分鐘喝 200 ml 的 10%」。

    刻意不收的（維持 W2 判讀慣例，寧可漏抓也不污染 band）：每日總量
    （g/day）、體重標準化劑量（g/kg，缺體重無從換算）、單獨出現的濃度
    或體積、以及氧化／週轉速率（是代謝輸出不是攝取輸入）。
    """
    result = []

    def add(value: float, unit: str, surface: str, per_hour: float) -> None:
        if not DOSE_MIN_G_PER_H <= per_hour <= DOSE_MAX_G_PER_H:
            return
        result.append({"value": value, "unit": unit,
                       "bandHint": _band_for(per_hour), "surface": surface})

    # 樣式 1：g/h 直述（含 g·h(-1)、g h-1、g/h、g·h<sup>-1</sup>）。
    # `g` 也接受 gram/grams 全稱（1992 年那篇綜述就寫 gram/min）。
    # (?!\s*kg) 擋掉 g·kg-1·h-1 這種體重標準化速率。
    per_h = re.compile(
        r"(?<![\d.])(\d{1,3}(?:\.\d+)?)\s*g(?:ram)?s?\s*"
        r"(?!\s*(?:/\s*kg|[·.]\s*kg|kg))"
        r"(?:/\s*h|\s*[·.]?\s*h\s*(?:<sup>\s*[-−]\s*1\s*</sup>|"
        r"\(\s*[-−]\s*1\s*\)|[-−^]\s*1)|\s*per\s+hour)(?![a-z])",
        flags=re.I)
    for m in per_h.finditer(text):
        if _oxidation_context(text, m.start()):
            continue
        value = float(m.group(1))
        add(value, "g/h", m.group(0), value)

    # 樣式 2：g/min（乘 60）。
    per_min = re.compile(
        r"(?<![\d.])(\d{1,2}(?:\.\d+)?)\s*g(?:ram)?s?\s*"
        r"(?!\s*(?:/\s*kg|[·.]\s*kg|kg))"
        r"(?:/\s*min|\s*[·.]?\s*min\s*(?:<sup>\s*[-−]\s*1\s*</sup>|"
        r"\(\s*[-−]\s*1\s*\)|[-−^]\s*1)|\s*per\s+min(?:ute)?)(?![a-z])",
        flags=re.I)
    for m in per_min.finditer(text):
        if _oxidation_context(text, m.start()):
            continue
        value = float(m.group(1))
        add(value, "g/min", m.group(0), value * 60.0)

    # 樣式 1b：共用單位的列舉。「39 or 64 g·h(-1)」「20, 39, or 64 g/h」
    # 裡只有最後一個數字帶單位，前面的靠共用——這是真實文獻的常見寫法
    # （W2 有一篇標題就這樣寫）。只回收緊接在命中值之前、以連接詞或逗號
    # 相連的純數字，不跨句也不跨其他詞。
    lead = re.compile(r"((?:\d{1,3}(?:\.\d+)?\s*(?:,|、|or|to|and|-|–)\s*)+)$",
                      flags=re.I)
    for signal in list(result):
        if signal["unit"] != "g/h":
            continue
        idx = text.find(signal["surface"])
        if idx <= 0:
            continue
        prefix = lead.search(text[max(0, idx - 40):idx])
        if not prefix:
            continue
        for number in re.findall(r"\d{1,3}(?:\.\d+)?", prefix.group(1)):
            value = float(number)
            add(value, "g/h", f"{number} (shared unit: {signal['surface']})",
                value)

    # 樣式 3：濃度 × 體積 × 頻率。三個要素常被逗號與插入子句隔開（實測有
    # 「every 15 min, cyclists consumed 143 ml of either (i) water; (ii)
    # …16% w/v」這種寫法），故以「體積為中心、前後 300 字元」的視窗配對，
    # 不用整句切分。同一視窗取最近的濃度，避免跨處方誤連。
    def _ml(number: str, unit: str) -> float:
        return float(number) * (1000.0 if unit.lower().startswith("l") else 1.0)

    def _nearest_pct(centre: int) -> float | None:
        best = None
        for m in re.finditer(_PERCENT, text):
            distance = abs(m.start() - centre)
            if distance > 300:
                continue
            value = float(m.group(1)) / 100.0
            if not 0 < value <= 0.30:  # >30% w/v 不是可飲用的運動飲料
                continue
            if best is None or distance < best[0]:
                best = (distance, value, m.group(0))
        return best

    for m in re.finditer(_VOLUME_PER_H, text, flags=re.I):
        pct = _nearest_pct(m.start())
        if not pct:
            continue
        grams = _ml(m.group(1), m.group(2)) * pct[1]
        add(round(grams, 1), "g/h", f"{m.group(0)} @ {pct[2]}", grams)

    for every in re.finditer(_EVERY_MIN, text, flags=re.I):
        minutes = float(every.group("every") or every.group("interval"))
        if minutes <= 0:
            continue
        window = text[max(0, every.start() - 150):every.end() + 150]
        vol = re.search(_VOLUME_EVERY, window, flags=re.I)
        if not vol:
            continue
        pct = _nearest_pct(every.start())
        if not pct:
            continue
        per_hour = _ml(vol.group(1), vol.group(2)) * pct[1] * (60.0 / minutes)
        add(round(per_hour, 1), "g/h",
            f"{vol.group(0)} @ {pct[2]} {every.group(0)}", per_hour)

    unique = {(s["value"], s["unit"], s["surface"]): s for s in result}
    return [unique[key] for key in sorted(unique)]


def _suggested_strata(outcomes: list[str], dose_signals: list[dict]) -> list[str]:
    strata: set[str] = set()
    bands = {d["bandHint"] for d in dose_signals}
    if "tt-completion-time" in outcomes:
        if bands & {"high", "very-high"}:
            strata.add("S2-tt-high-and-very-high-dose")
        if not bands or bands & {"low", "moderate"}:
            strata.add("S1-tt-moderate-dose")
    if "time-to-exhaustion" in outcomes:
        strata.add("S3-tte")
    if "exogenous-cho-oxidation-peak" in outcomes:
        strata.add("S4-exogenous-oxidation")
    if "gi-symptom-incidence" in outcomes or "gi-symptom-severity" in outcomes:
        strata.update({"S5-gi-harms-primary", "S6-gi-harms-secondary-only"})
    if "muscle-glycogen-post-exercise" in outcomes:
        strata.add("S7-glycogen")
    return sorted(strata)


def _priority(concepts: set[str], outcomes: list[str]) -> str:
    if {"population", "intervention", "exercise", "timing"} <= concepts and outcomes:
        return "T1-high-signal"
    if {"intervention", "exercise"} <= concepts and (
            "timing" in concepts or outcomes or "population" in concepts):
        return "T2-moderate-signal"
    if "intervention" in concepts and ("exercise" in concepts or outcomes):
        return "T3-partial-signal"
    if "exercise" in concepts or outcomes:
        return "T4-broad-signal"
    return "T5-low-signal"


def _entry(candidate: dict, conflict_ids: set[str], ambiguity_ids: set[str]) -> dict:
    title = normalise_for_matching(candidate.get("title"))
    abstract = normalise_for_matching(candidate.get("abstract"))
    text = f"{title}\n{abstract}"
    concepts: set[str] = set()
    outcomes: list[str] = []
    rules: list[str] = []
    breakdown = {key: 0 for key in (*CONCEPTS.keys(), "outcomes")}

    for concept, (rule, patterns) in CONCEPTS.items():
        if _matches(text, patterns):
            concepts.add(concept)
            rules.append(rule)
            breakdown[concept] = SCORE[concept]
    for outcome, (rule, patterns) in OUTCOMES.items():
        if _matches(text, patterns):
            outcomes.append(outcome)
            rules.append(rule)
    if outcomes:
        breakdown["outcomes"] = SCORE["outcomes"]
        concepts.add("outcomes")

    flags: set[str] = set()
    for flag, (rule, patterns) in SAFETY.items():
        if _matches(text, patterns):
            flags.add(flag)
            rules.append(rule)
    if not candidate.get("abstract"):
        flags.add("metadata-missing-abstract")
        rules.append("SCREEN-030-missing-abstract")
    if candidate["candidateId"] in conflict_ids:
        flags.add("identifier-conflict")
        rules.append("SCREEN-031-identifier-conflict")
    if candidate["candidateId"] in ambiguity_ids:
        flags.add("title-ambiguity")
        rules.append("SCREEN-032-title-ambiguity")
    if ("gi-symptom-incidence" in outcomes
            or "gi-symptom-severity" in outcomes):
        flags.add("critical-harms-signal")
        rules.append("SCREEN-033-critical-harms")
    if candidate.get("isPreprint"):
        flags.add("preprint")
        rules.append("SCREEN-034-preprint")

    publication_types = {str(value).strip().lower()
                         for value in candidate.get("publicationTypes") or []}
    review_type = any(
        "review" in value or value in {"guideline", "practice guideline",
                                       "consensus statement", "meta-analysis",
                                       "scoping review"}
        for value in publication_types)
    if review_type:
        flags.add("review-or-guideline")
        rules.append("SCREEN-035-review-or-guideline")

    # 詞表涵蓋哺乳實驗動物、家畜家禽與水產物種。魚類是實測漏抓來源：
    # prevalence audit 22f634d2325d 抽到的草魚轉錄體研究落在 standard-screening。
    # 漏抓的代價與誤剔相反——誤剔是少收該收的，漏抓是主池混入非人體研究並
    # 推高篩選工時，故此處寧可多標（本旗標只改 lane，從不自動排除）。
    # 詞邊界必須嚴格：fish oil／fishermen／catheter／ratio 都不得觸發。
    animal_signal = _matches(text, (
        r"\brats?\b", r"\bmice\b", r"\bmouse\b", r"\bmurine\b",
        r"\bporcine\b", r"\bswine\b", r"\bhorses?\b", r"\bcanine\b",
        r"\bdogs?\b", r"\brabbit\w*\b",
        # 反芻獸與其他家畜。以下詞刻意排除，實測誤標率過高：
        #   calf   → 小腿肌（calf muscle / calf raises），人體運動研究常用
        #   bovine → 胎牛血清、牛初乳補劑，多為人體或體外研究
        #   pig    → guinea pig 已另列；單獨 pig 誤觸 pig small intestinal mucus
        #            等體外材料研究
        r"\bcalves\b", r"\blambs?\b", r"\bgoats?\b", r"\bpiglets?\b",
        r"\bferrets?\b", r"\bmacaques?\b", r"\bhamsters?\b",
        r"\bguinea pigs?\b",
        r"\bovine (?:muscle|models?|study|studies|subjects?)\b",
        # cattle／sheep 需語境：兩者會出現在「反芻獸胃道菌相」等環境微生物
        # 研究的材料描述裡，本身不是介入對象。
        r"\b(?:in|of|from) (?:cattle|sheep)\b", r"\bdairy cows?\b",
        r"\bbos taurus\b",
        # equine 需語境：conjugated equine estrogens 是人用荷爾蒙藥物。
        r"\bequine (?:muscle|model|study|athletes?|somatotropin|exercise)\b",
        r"\bstallions?\b", r"\bmares?\b",
        # 家禽。poultry／turkey／hen 排除：分別是膳食攝取項目、國名、
        # hen egg yolk 試劑語境。裸詞 chicken 亦排除——實測誤觸「chicken
        # noodle soup」與成語「the chicken or the egg」，均為人體研究。
        r"\bbroilers?\b", r"\bchick embryo\w*\b", r"\blaying hens?\b",
        r"\bquail\b",
        # 水產。裸詞 fish/poultry 是膳食問卷選項（「魚、禽、蛋」），誤標率過高，
        # 故只收物種名與明確的養殖／實驗語境。
        r"\bteleost\w*\b", r"\bcarp\b", r"\bgoldfish\b", r"\bzebrafish\b",
        r"\bsalmon\b", r"\btrout\b", r"\btilapia\b", r"\bseabass\b",
        r"\bsea bass\b", r"\bbarramundi\b", r"\bmedaka\b", r"\bkillifish\b",
        r"\bfarmed fish\w*\b", r"\bfish (?:larvae|fingerlings?|juveniles?|"
        r"species|were fed|fed a)\b", r"\bin fish\b", r"\bbroodstock\b",
        # 通用實驗動物語彙。animal model(s)／rodent(s) 排除：人體研究的
        # 討論段落常引用動物文獻（「in animal models…」），屬敘述提及而非
        # 研究對象，誤標會把人體研究踢出主池。
        r"\bin vivo animal\b"))
    if animal_signal:
        flags.add("animal-signal")
        rules.append("SCREEN-036-animal-signal")

    # 「post-exercise」常是 recovery/B.20 而非本契約的 during-exercise 介入。
    # 只標旗，不排除：同一研究可能同時有運動中介入與 post-exercise 測量。
    if (_matches(text, (r"\bpost[- ]exercise\b", r"\brecovery feeding\b"))
            and not _matches(text, (r"\bduring (?:prolonged )?exercis\w*\b",
                                    r"\bintra[- ]exercise\b"))):
        flags.add("post-exercise-only-signal")
        rules.append("SCREEN-037-post-exercise-only")

    safety = any(flag.startswith("safety-") for flag in flags)
    if safety:
        lane = "safety-review"
    elif "identifier-conflict" in flags:
        lane = "identity-review"
    elif candidate["entityKind"] == "registry-record":
        lane = "registry-review"
    elif "review-or-guideline" in flags:
        lane = "review-source-review"
    elif "animal-signal" in flags:
        lane = "animal-signal-review"
    else:
        lane = "standard-screening"

    doses = _dose_signals(text)
    tier = _priority(concepts, outcomes)
    # ADR-0007：第二審由盲化 LLM 擔任；安全分支與 critical harms 維持純人類
    # 雙盲——harms 是 critical outcome，不拿來省時間。
    review_mode = ("dual-blind-title-abstract"
                   if lane == "safety-review"
                   or "critical-harms-signal" in flags
                   else "human-plus-blinded-llm-title-abstract")
    return {
        "candidateId": candidate["candidateId"],
        "entityKind": candidate["entityKind"],
        "canonicalIdentity": candidate["canonicalIdentity"],
        "title": candidate.get("title"),
        "publicationYear": candidate.get("publicationYear"),
        "identifiers": candidate.get("identifiers", {}),
        "screeningLane": lane,
        "priorityTier": tier,
        "priorityScore": sum(breakdown.values()),
        "scoreBreakdown": breakdown,
        "conceptMatches": sorted(concepts),
        "outcomeHints": sorted(outcomes),
        "doseSignals": doses,
        "suggestedStrata": _suggested_strata(outcomes, doses),
        "strataAssignmentFinal": False,
        "flags": sorted(flags),
        "matchedRuleIds": sorted(set(rules)) or ["SCREEN-000-no-signal"],
        "requiresHumanScreening": True,
        "requiredReviewMode": review_mode,
        "autoDecision": None,
    }


def build_queue(candidate_list: list[dict], *, candidate_pool_hash: str,
                search_contract_hash: str, run_id: str,
                identifier_conflicts: list[dict],
                title_ambiguities: list[dict],
                source_coverage: dict[str, str],
                complete_across_contract_sources: bool) -> dict:
    conflict_ids = {item["candidateId"] for item in identifier_conflicts}
    ambiguity_ids = {cid for bucket in title_ambiguities
                     for cid in bucket.get("candidateIds", [])}
    queue = [_entry(candidate, conflict_ids, ambiguity_ids)
             for candidate in candidate_list]
    queue.sort(key=lambda e: (
        LANE_ORDER[e["screeningLane"]], TIER_ORDER[e["priorityTier"]],
        -e["priorityScore"], e["candidateId"]))

    candidate_sources_complete = bool(complete_across_contract_sources)
    blocking_reasons = []
    if not candidate_sources_complete:
        blocking_reasons.append("candidate-sources-incomplete")
    blocking_reasons.append("human-title-abstract-screening-not-completed")

    manifest = {
        "runId": run_id,
        "candidatePoolHash": candidate_pool_hash,
        "searchContractHash": search_contract_hash,
        "screeningRuleVersion": RULE_VERSION,
        "screeningQueueHash": content_hash(queue),
        "sourceCoverage": dict(sorted(source_coverage.items())),
        "candidateSourcesComplete": candidate_sources_complete,
        "humanTitleAbstractScreeningComplete": False,
        "eligibleSamplingPoolReady": False,
        "blockingReasons": blocking_reasons,
        "candidateCount": len(candidate_list),
        "queueCount": len(queue),
        "countByPriorityTier": dict(sorted(Counter(
            e["priorityTier"] for e in queue).items())),
        "countByScreeningLane": dict(sorted(Counter(
            e["screeningLane"] for e in queue).items())),
        "countByOutcomeHint": dict(sorted(Counter(
            outcome for entry in queue for outcome in entry["outcomeHints"]).items())),
        "countBySuggestedStratum": dict(sorted(Counter(
            stratum for entry in queue for stratum in entry["suggestedStrata"]).items())),
        "autoExcludedCount": 0,
        "requiresHumanScreeningCount": len(queue),
        "invariant": "priority-only-never-auto-include-or-exclude",
    }
    return {"manifest": manifest, "queue": queue}


def build_from_run_root(run_root: Path, *, dry_run: bool = False,
                        redo: bool = False) -> dict:
    run_root = Path(run_root).resolve()
    pool = run_root / "candidate-pool"
    pool_manifest_path = pool / "manifest.json"
    candidates_path = pool / "candidates.json"
    if not pool_manifest_path.exists() or not candidates_path.exists():
        raise FileNotFoundError("缺少 candidate-pool 產物")
    pool_manifest = json.loads(pool_manifest_path.read_text(encoding="utf-8"))
    candidate_list = json.loads(candidates_path.read_text(encoding="utf-8"))
    if len(candidate_list) != pool_manifest.get("candidateCount"):
        raise ValueError(
            f"candidate count 漂移：檔案 {len(candidate_list)} vs manifest "
            f"{pool_manifest.get('candidateCount')}")
    conflicts = json.loads((pool / "identifier-conflicts.json").read_text(
        encoding="utf-8"))
    ambiguities = json.loads((pool / "title-ambiguities.json").read_text(
        encoding="utf-8"))
    pool_hash = "sha256:" + hashlib.sha256(candidates_path.read_bytes()).hexdigest()
    built = build_queue(
        candidate_list, candidate_pool_hash=pool_hash,
        search_contract_hash=pool_manifest["searchContractHash"],
        run_id=pool_manifest["runId"], identifier_conflicts=conflicts,
        title_ambiguities=ambiguities,
        source_coverage=pool_manifest.get("sourceCoverage", {}),
        complete_across_contract_sources=bool(
            pool_manifest.get("completeAcrossContractSources")))
    summary = dict(built["manifest"])
    summary["candidateCount"] = len(candidate_list)
    if dry_run:
        return summary

    out = run_root / "screening-queue"
    if out.exists():
        if not redo:
            raise FileExistsError(f"{out} 已存在；重建請用 --redo")
        archive_root = run_root / "previous-screening-queues"
        archive_root.mkdir(parents=True, exist_ok=True)
        suffix = hashlib.sha256((out / "manifest.json").read_bytes()).hexdigest()[:12]
        target = archive_root / suffix
        serial = 1
        while target.exists():
            serial += 1
            target = archive_root / f"{suffix}-{serial}"
        shutil.move(str(out), str(target))
    out.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out / "manifest.json", built["manifest"])
    atomic_write_json(out / "queue.json", built["queue"])
    atomic_write_json(out / "summary.json", summary)
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run_root", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--redo", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    result = build_from_run_root(args.run_root, dry_run=args.dry_run, redo=args.redo)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
