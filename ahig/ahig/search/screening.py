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

RULE_VERSION = "b11-screening/1.3.0"

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


def _dose_signals(text: str) -> list[dict]:
    # 支援 90 g/h、90 g h-1、90 g·h−1；只作 band hint，不作 extraction。
    pattern = re.compile(
        r"(?<!\d)(\d{1,3}(?:\.\d+)?)\s*g\s*(?:/\s*h|[·. ]?h\s*[-^]?\s*1)\b",
        flags=re.I)
    result = []
    for match in pattern.finditer(text):
        value = float(match.group(1))
        if value < 10 or value > 200:
            continue
        if value < 30:
            band = "low"
        elif value < 60:
            band = "moderate"
        elif value < 90:
            band = "high"
        else:
            band = "very-high"
        result.append({"value": value, "unit": "g/h", "bandHint": band,
                       "surface": match.group(0)})
    unique = {(s["value"], s["surface"]): s for s in result}
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

    animal_signal = _matches(text, (
        r"\brats?\b", r"\bmice\b", r"\bmouse\b", r"\bmurine\b",
        r"\bporcine\b", r"\bswine\b", r"\bhorses?\b", r"\bcanine\b",
        r"\bdogs?\b", r"\brabbit\w*\b"))
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
