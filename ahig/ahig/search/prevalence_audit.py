#!/usr/bin/env python3
"""摘要層級劑量可讀性的人工稽核工具（prevalence audit）。

量測「光看 title/abstract 能不能讀出 CHO 攝取速率」與 band 分布，用途是判斷
strata.json 裡 dose-band 配額（S1/S2/S4/S7 共 37 篇）能不能靠 metadata 填滿，
以及現行劑量 regex 的實測漏抓率。附帶一個誤剔抽查：從被關鍵字分流出主池的
四類（動物、綜述／指引、registry、安全分支）隨機抽一小批，估誤剔率上界——
那些分類全靠正則提示訊號，提示訊號需要被稽核。

這不是 screening，也不是校準集抽樣：

- 只讀取 candidate-pool 與 screening-queue，絕不改動它們；
- 抽到的紀錄不因此 include/exclude，``requiresHumanScreening`` 不受影響；
- 產出只是 strata 決策的輸入，決策仍由人做。

抽樣誠實性的三道護欄：

- 抽樣區段以 ``samplingLockHash`` 凍結：estimate 前重算比對，抽到哪些篇、
  其標題摘要、seed 都不可事後更動；只有判讀欄位開放回填。
- ``draws.jsonl`` 是 append-only 抽樣日誌：每次 sample 都留一行，estimate
  回報同一母體被抽過幾次。挑 seed 不被阻止，但一定留痕。
- ``--redo`` 不覆蓋：舊稽核目錄整個搬進 previous-prevalence-audits/。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import shutil
from datetime import datetime, timezone
from pathlib import Path

from scipy import stats

from ahig.bootstrap import private_root
from ahig.contracts.freeze import content_hash
from ahig.search import screening
from ahig.state import atomic_write_json

AUDIT_DIRNAME = "prevalence-audit"
ARCHIVE_DIRNAME = "previous-prevalence-audits"
DRAW_LOG = "draws.jsonl"

# 從主抽樣框扣掉的四類 screening lane（誤剔抽查的母體）。
EXCLUDED_LANES = frozenset({
    "animal-signal-review", "review-source-review",
    "registry-review", "safety-review"})

READABILITY_LEVELS = ("exact-value", "intensity-only", "not-reported")
BANDS = ("low", "moderate", "high", "very-high")
BAND_VALUES = frozenset(BANDS) | {"unclear"}

_IMMUTABLE_RECORD_KEYS = ("candidateId", "title", "abstract",
                          "publicationYear", "identifiers", "outcomeHints",
                          "screeningLane")
_IMMUTABLE_EXCLUSION_KEYS = ("candidateId", "title", "abstract",
                             "screeningLane", "flags")

DEFAULT_STRATA_PATH = (Path(__file__).resolve().parents[2] / "calibration"
                       / "b11-carbohydrate" / "strata.json")


class PrevalenceAuditError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clopper_pearson(successes: int, n: int,
                    alpha: float = 0.05) -> tuple[float, float]:
    """雙側 (1-alpha) Clopper–Pearson 精確區間。n=0 時無資訊，回傳 (0, 1)。"""
    if n <= 0:
        return (0.0, 1.0)
    if not 0 <= successes <= n:
        raise PrevalenceAuditError(f"successes 必須在 [0, n]：{successes}/{n}")
    lower = (0.0 if successes == 0
             else float(stats.beta.ppf(alpha / 2, successes,
                                       n - successes + 1)))
    upper = (1.0 if successes == n
             else float(stats.beta.ppf(1 - alpha / 2, successes + 1,
                                       n - successes)))
    return (lower, upper)


def clopper_pearson_upper(successes: int, n: int,
                          alpha: float = 0.05) -> float:
    """單側 (1-alpha) 上界（rule of three 的一般化）。"""
    if n <= 0:
        return 1.0
    if successes >= n:
        return 1.0
    return float(stats.beta.ppf(1 - alpha, successes + 1, n - successes))


def _require_private(run_root: Path) -> Path:
    root = private_root()
    resolved = Path(run_root).expanduser().resolve()
    if resolved != root and root not in resolved.parents:
        raise PrevalenceAuditError(
            f"prevalence audit 只能在 AHIG_PRIVATE_ROOT 之下執行：{root}")
    return resolved


def _load_run(run_root: Path) -> tuple[dict, list[dict], dict[str, dict]]:
    queue_dir = run_root / "screening-queue"
    manifest = json.loads(
        (queue_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("candidateSourcesComplete") is not True:
        raise PrevalenceAuditError(
            "candidate sources must be complete before prevalence audit")
    queue = json.loads((queue_dir / "queue.json").read_text(encoding="utf-8"))
    candidates = json.loads(
        (run_root / "candidate-pool" / "candidates.json").read_text(
            encoding="utf-8"))
    return manifest, queue, {c["candidateId"]: c for c in candidates}


def _record(entry: dict, candidate: dict) -> dict:
    return {
        "candidateId": entry["candidateId"],
        "title": candidate.get("title"),
        "abstract": candidate.get("abstract"),
        "publicationYear": candidate.get("publicationYear"),
        "identifiers": candidate.get("identifiers", {}),
        "outcomeHints": entry.get("outcomeHints", []),
        "screeningLane": entry.get("screeningLane"),
        # ---- 以下由人工回填 ----
        "doseReadability": None,     # exact-value / intensity-only / not-reported
        "maxDose": {"value": None, "unit": None},
        "doseBands": None,           # 多臂研究填完整清單，如 ["moderate", "high"]
        "notes": None,
    }


def _exclusion_record(entry: dict, candidate: dict) -> dict:
    return {
        "candidateId": entry["candidateId"],
        "title": candidate.get("title"),
        "abstract": candidate.get("abstract"),
        "screeningLane": entry.get("screeningLane"),
        "flags": entry.get("flags", []),
        # ---- 以下由人工回填 ----
        "exclusionJustified": None,  # true = 真的該從主抽樣框剔除
        "notes": None,
    }


def _immutable(record: dict, keys: tuple[str, ...]) -> dict:
    return {key: record[key] for key in keys}


def _sampling_lock(audit: dict) -> str:
    return content_hash({
        "seed": audit["seed"],
        "frameHash": audit["frameHash"],
        "outcomeFilter": audit["outcomeFilter"],
        "records": [_immutable(r, _IMMUTABLE_RECORD_KEYS)
                    for r in audit["records"]],
        "exclusionAudit": [_immutable(r, _IMMUTABLE_EXCLUSION_KEYS)
                           for r in audit["exclusionAudit"]],
    })


def draw_sample(run_root: Path, *, seed: int, n: int = 50,
                excluded_n: int = 12, outcome_filter: list[str] | None = None,
                redo: bool = False) -> dict:
    """抽出主樣本與誤剔抽查樣本，寫出待回填的稽核檔、判讀表與抽樣日誌。"""
    run_root = _require_private(run_root)
    manifest, queue, by_id = _load_run(run_root)

    frame = [e for e in queue if e.get("screeningLane") not in EXCLUDED_LANES]
    if outcome_filter:
        frame = [e for e in frame
                 if set(e.get("outcomeHints", [])) & set(outcome_filter)]
    excluded_pool = [e for e in queue
                     if e.get("screeningLane") in EXCLUDED_LANES]
    if not frame:
        raise PrevalenceAuditError("主抽樣框是空的，無從稽核")

    exclusion_counts: dict[str, int] = {}
    for entry in excluded_pool:
        lane = entry["screeningLane"]
        exclusion_counts[lane] = exclusion_counts.get(lane, 0) + 1

    frame_ids = sorted(e["candidateId"] for e in frame)
    excluded_ids = sorted(e["candidateId"] for e in excluded_pool)
    frame_hash = content_hash({
        "screeningQueueHash": manifest["screeningQueueHash"],
        "frame": frame_ids, "excludedPool": excluded_ids,
        "outcomeFilter": sorted(outcome_filter or [])})

    rng = random.Random(seed)
    sampled_ids = rng.sample(frame_ids, min(n, len(frame_ids)))
    excluded_sample_ids = rng.sample(excluded_ids,
                                     min(excluded_n, len(excluded_ids)))
    queue_by_id = {e["candidateId"]: e for e in queue}

    audit_id = hashlib.sha256(content_hash({
        "frameHash": frame_hash, "seed": seed, "n": n,
        "excludedN": excluded_n}).encode("utf-8")).hexdigest()[:12]
    audit = {
        "documentType": "prevalence-audit",
        "schemaVersion": "1.0.0",
        "auditId": audit_id,
        "purpose": "abstract-dose-readability-prevalence-audit",
        "notAScreeningDecision": True,
        "requiresHumanScreeningUnchanged": True,
        "runId": manifest["runId"],
        "screeningQueueHash": manifest["screeningQueueHash"],
        "candidatePoolHash": manifest["candidatePoolHash"],
        "seed": seed,
        "frameHash": frame_hash,
        "frameSize": len(frame_ids),
        "excludedPoolSize": len(excluded_ids),
        "exclusionCountsByLane": dict(sorted(exclusion_counts.items())),
        "outcomeFilter": sorted(outcome_filter or []),
        "requestedSampleSize": n,
        "sampleSize": len(sampled_ids),
        "requestedExclusionAuditSize": excluded_n,
        "exclusionAuditSize": len(excluded_sample_ids),
        "samplingRule": "random.Random(seed).sample 於 candidateId 升冪清單；"
                        "先抽主樣本、後抽誤剔樣本，共用同一 rng 狀態",
        "drawnAt": _utc_now(),
        "records": [_record(queue_by_id[cid], by_id.get(cid, {}))
                    for cid in sampled_ids],
        "exclusionAudit": [_exclusion_record(queue_by_id[cid],
                                             by_id.get(cid, {}))
                           for cid in excluded_sample_ids],
    }
    audit["samplingLockHash"] = _sampling_lock(audit)

    audit_root = run_root / AUDIT_DIRNAME
    out = audit_root / audit_id
    if out.exists():
        if not redo:
            raise FileExistsError(f"{out} 已存在；重抽請用 --redo")
        archive = run_root / ARCHIVE_DIRNAME
        archive.mkdir(parents=True, exist_ok=True)
        serial = 1
        target = archive / audit_id
        while target.exists():
            serial += 1
            target = archive / f"{audit_id}-{serial}"
        shutil.move(str(out), str(target))
    out.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out / "audit.json", audit)
    (out / "reading-sheet.md").write_text(_reading_sheet(audit),
                                          encoding="utf-8")
    with (audit_root / DRAW_LOG).open("a", encoding="utf-8") as log:
        log.write(json.dumps({
            "drawnAt": audit["drawnAt"], "auditId": audit_id, "seed": seed,
            "requestedSampleSize": n, "requestedExclusionAuditSize": excluded_n,
            "frameHash": frame_hash,
            "outcomeFilter": audit["outcomeFilter"],
        }, ensure_ascii=False) + "\n")
    return audit


def _reading_sheet(audit: dict) -> str:
    lines = [
        f"# 劑量可讀性抽查判讀表（audit {audit['auditId']}）",
        "",
        f"- 主抽樣框 {audit['frameSize']} 篇，抽出 {audit['sampleSize']} 篇；"
        f"誤剔母體 {audit['excludedPoolSize']} 篇，抽出 "
        f"{audit['exclusionAuditSize']} 篇（seed={audit['seed']}）",
        "- 只讀 title/abstract，回填 `audit.json`。第一節每筆四個欄位：",
        "  - `doseReadability`：exact-value（有明確數值）／intensity-only"
        "（只讀得出強度高低）／not-reported（完全沒寫）",
        "  - `maxDose`：exact-value 時必填 {value, unit}（unit 如 g/h、g/min、"
        "%），其餘留 null",
        "  - `doseBands`：涵蓋到的 band 完整清單（多臂研究列全部）："
        "low(<30) / moderate(30–59.9) / high(60–89.9) / very-high(≥90)，"
        "讀得出有劑量但分不出帶用 unclear；not-reported 留 null",
        "  - `notes`：自由文字（可留 null）",
        "- 第二節（誤剔抽查）每筆填 `exclusionJustified`：這篇被分流出主池"
        "（動物／綜述／registry／安全）是否正確（true/false）＋ notes。",
        "- 這是母體量測，不是篩選；不要做 include/exclude 判斷。",
        "- 判讀時請勿參考任何自動劑量偵測結果；regex 對照由 estimate 另行計算。",
        "",
        "## 第一節：劑量可讀性",
        "",
    ]
    for i, record in enumerate(audit["records"], 1):
        lines += [
            f"### 1.{i} {record['candidateId']}",
            "",
            f"**{record.get('title') or '(無標題)'}**"
            + (f"（{record['publicationYear']}）"
               if record.get("publicationYear") else ""),
            "",
            record.get("abstract") or "（無摘要——doseReadability 填 "
            "not-reported，notes 註明 no-abstract）",
            "",
        ]
    lines += ["## 第二節：誤剔抽查", ""]
    for i, record in enumerate(audit["exclusionAudit"], 1):
        lines += [
            f"### 2.{i} {record['candidateId']}（lane: "
            f"{record['screeningLane']}）",
            "",
            f"**{record.get('title') or '(無標題)'}**",
            "",
            record.get("abstract") or "（無摘要）",
            "",
        ]
    return "\n".join(lines)


def _validate_filled(audit: dict) -> None:
    problems = []
    for i, record in enumerate(audit["records"]):
        cid = record["candidateId"]
        level = record.get("doseReadability")
        bands = record.get("doseBands")
        dose = record.get("maxDose") or {}
        value, unit = dose.get("value"), dose.get("unit")
        if level not in READABILITY_LEVELS:
            problems.append(f"records[{i}] {cid}: doseReadability 未回填或"
                            f"不在 {READABILITY_LEVELS}")
            continue
        if level == "not-reported":
            if bands:
                problems.append(f"records[{i}] {cid}: not-reported 卻填了 "
                                "doseBands")
            if value is not None:
                problems.append(f"records[{i}] {cid}: not-reported 卻填了 "
                                "maxDose.value")
            continue
        if (not isinstance(bands, list) or not bands
                or not set(bands) <= BAND_VALUES):
            problems.append(f"records[{i}] {cid}: doseBands 必須是 "
                            f"{sorted(BAND_VALUES)} 的非空清單")
        if level == "exact-value":
            if not isinstance(value, (int, float)):
                problems.append(f"records[{i}] {cid}: exact-value 必須填 "
                                "maxDose.value 數值")
            if not (isinstance(unit, str) and unit.strip()):
                problems.append(f"records[{i}] {cid}: exact-value 必須填 "
                                "maxDose.unit")
        elif value is not None:
            problems.append(f"records[{i}] {cid}: 讀得出數值就該填 "
                            "exact-value，而非 intensity-only")
    for i, record in enumerate(audit["exclusionAudit"]):
        if not isinstance(record.get("exclusionJustified"), bool):
            problems.append(f"exclusionAudit[{i}] {record['candidateId']}: "
                            "exclusionJustified 未回填")
    if problems:
        raise PrevalenceAuditError("稽核表尚未回填完成或有矛盾：\n"
                                   + "\n".join(problems))


def _project(frame_size: int, lo: float, hi: float) -> list[int]:
    """把比率區間乘回母體，下界取 floor、上界取 ceil（保守外推）。"""
    return [math.floor(frame_size * lo), math.ceil(frame_size * hi)]


def _band_estimates(records: list[dict], frame_size: int) -> dict:
    n = len(records)
    out = {}
    for band in BANDS + ("unclear",):
        strict = sum(1 for r in records if r["doseReadability"] == "exact-value"
                     and band in (r.get("doseBands") or []))
        lenient = sum(1 for r in records
                      if r["doseReadability"] in ("exact-value",
                                                  "intensity-only")
                      and band in (r.get("doseBands") or []))
        out[band] = {}
        for label, k in (("strict", strict), ("lenient", lenient)):
            lo, hi = clopper_pearson(k, n)
            out[band][label] = {
                "count": k, "rate": k / n if n else None,
                "cp95": [lo, hi],
                "projectedInFrame": _project(frame_size, lo, hi),
            }
    return out


def _stratum_feasibility(records: list[dict], frame_size: int,
                         strata: list[dict]) -> list[dict]:
    n = len(records)
    results = []
    for stratum in strata:
        outcomes = set(stratum.get("primaryOutcomes", []))
        bands = set(stratum.get("doseBands", []))
        quota = stratum.get("quota")
        rows = {}
        for label, levels in (("strict", ("exact-value",)),
                              ("lenient", ("exact-value", "intensity-only"))):
            k = sum(1 for r in records
                    if set(r.get("outcomeHints", [])) & outcomes
                    and r["doseReadability"] in levels
                    and set(r.get("doseBands") or []) & bands)
            lo, hi = clopper_pearson(k, n)
            projected_lo, projected_hi = _project(frame_size, lo, hi)
            if projected_lo >= quota:
                verdict = "likely-sufficient"
            elif projected_hi < quota:
                verdict = "likely-insufficient"
            else:
                verdict = "not-demonstrated"
            rows[label] = {"count": k, "cp95": [lo, hi],
                           "projectedInFrame": [projected_lo, projected_hi],
                           "verdictAtBound": verdict}
        outcome_group_n = sum(1 for r in records
                              if set(r.get("outcomeHints", [])) & outcomes)
        results.append({
            "stratumId": stratum["stratumId"],
            "quota": quota,
            "outcomeGroupSampleCount": outcome_group_n,
            "insufficientAuditData": outcome_group_n < 5,
            **rows,
        })
    return results


def _regex_audit(records: list[dict]) -> dict:
    missed, false_positive = [], []
    for record in records:
        text = "\n".join(screening.normalise_for_matching(v)
                         for v in (record.get("title"),
                                   record.get("abstract")))
        signals = screening._dose_signals(text)
        human_found = record["doseReadability"] != "not-reported"
        if human_found and not signals:
            missed.append(record["candidateId"])
        if not human_found and signals:
            false_positive.append(record["candidateId"])
    return {
        "missedCandidateIds": sorted(missed),
        "falsePositiveCandidateIds": sorted(false_positive),
        "note": "missed = 人判摘要有劑量、現行 _dose_signals 沒抓到；這是"
                "regex 擴充（選項 D）可回收的實測上限。false positive 逐筆看 "
                "notes。",
    }


def _count_draws(audit_root: Path, frame_hash: str) -> int:
    log = audit_root / DRAW_LOG
    if not log.exists():
        return 0
    count = 0
    for line in log.read_text(encoding="utf-8").splitlines():
        if line.strip() and json.loads(line).get("frameHash") == frame_hash:
            count += 1
    return count


def estimate(audit_dir: Path, *, strata_path: Path | None = None,
             redo: bool = False) -> dict:
    """讀回填完成的 audit.json，驗證抽樣鎖，產出母體推估。"""
    audit_dir = _require_private(audit_dir)
    audit = json.loads((audit_dir / "audit.json").read_text(encoding="utf-8"))
    if _sampling_lock(audit) != audit.get("samplingLockHash"):
        raise PrevalenceAuditError(
            "samplingLockHash 驗證失敗：抽樣區段（seed、抽到哪些篇、其標題"
            "摘要）在回填期間被更動。請回到原始抽樣或以 --redo 重抽。")
    _validate_filled(audit)

    records = audit["records"]
    exclusion_records = audit["exclusionAudit"]
    n = len(records)
    frame_size = audit["frameSize"]

    readability_counts = {
        level: sum(1 for r in records if r["doseReadability"] == level)
        for level in READABILITY_LEVELS}

    strata_file = Path(strata_path) if strata_path else DEFAULT_STRATA_PATH
    strata_doc = json.loads(strata_file.read_text(encoding="utf-8"))

    k_bad = sum(1 for r in exclusion_records
                if r["exclusionJustified"] is False)
    m = len(exclusion_records)
    exclusion_result = {
        "sampleSize": m,
        "unjustifiedCount": k_bad,
        "falseExclusionRateUpper95": clopper_pearson_upper(k_bad, m),
        "projectedLostUpper95": math.ceil(
            audit["excludedPoolSize"] * clopper_pearson_upper(k_bad, m)),
        "note": "上界隨樣本數縮小；預設 12 筆只能證明 <~22%，作煙霧測試用。"
                "要證明 <10% 需約 30 筆（零誤剔時）。",
    }

    result = {
        "documentType": "prevalence-audit-estimate",
        "schemaVersion": "1.0.0",
        "auditId": audit["auditId"],
        "runId": audit["runId"],
        "screeningQueueHash": audit["screeningQueueHash"],
        "samplingLockHash": audit["samplingLockHash"],
        "seed": audit["seed"],
        "sampleSize": n,
        "frameSize": frame_size,
        "drawsForSameFrame": _count_draws(audit_dir.parent,
                                          audit["frameHash"]),
        "strataFile": str(strata_file),
        "strataVersion": strata_doc.get("version"),
        "strataFileSha256": hashlib.sha256(
            strata_file.read_bytes()).hexdigest(),
        "readabilityCounts": readability_counts,
        "bandEstimates": _band_estimates(records, frame_size),
        "stratumFeasibility": _stratum_feasibility(
            records, frame_size, strata_doc.get("strata", [])),
        "exclusionAudit": exclusion_result,
        "regexAudit": _regex_audit(records),
        "interpretation": {
            "quotaRule": "配額判斷取 Clopper–Pearson 下界（保守側）；strict "
                         "只算 exact-value，lenient 含 intensity-only。",
            "frameCaveat": "抽樣框已扣除動物／綜述／registry／安全四類；"
                           "外推只及於主池。誤剔抽查另行估上界。",
            "powerCaveat": "outcomeGroupSampleCount < 5 的層，區間近乎無"
                           "資訊量；用 sample --outcome 對該層補抽，勿逕自"
                           "解讀為不足。",
        },
        "decisionRemainsHuman": True,
        "estimatedAt": _utc_now(),
    }

    out_path = audit_dir / "estimate.json"
    if out_path.exists() and not redo:
        raise FileExistsError(f"{out_path} 已存在；重算請用 --redo")
    atomic_write_json(out_path, result)
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_sample = sub.add_parser("sample", help="抽出待判讀樣本")
    p_sample.add_argument("run_root", type=Path)
    p_sample.add_argument("--seed", type=int, required=True,
                          help="抽樣種子；抽樣當下決定，每次抽樣都寫入 "
                               "draws.jsonl 留痕")
    p_sample.add_argument("--n", type=int, default=50)
    p_sample.add_argument("--excluded-n", type=int, default=12,
                          help="誤剔抽查樣本數")
    p_sample.add_argument("--outcome", action="append", dest="outcomes",
                          help="可重複：把主抽樣框縮到含指定 outcome hint 的"
                               "候選（稀少層補抽用）")
    p_sample.add_argument("--redo", action="store_true")
    p_estimate = sub.add_parser("estimate", help="以回填完成的稽核表推估母體")
    p_estimate.add_argument("audit_dir", type=Path)
    p_estimate.add_argument("--strata", type=Path, default=None)
    p_estimate.add_argument("--redo", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "sample":
        result = draw_sample(args.run_root, seed=args.seed, n=args.n,
                             excluded_n=args.excluded_n,
                             outcome_filter=args.outcomes, redo=args.redo)
        out = {key: result[key] for key in
               ("auditId", "sampleSize", "exclusionAuditSize", "frameSize",
                "excludedPoolSize", "seed")}
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        result = estimate(args.audit_dir, strata_path=args.strata,
                          redo=args.redo)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
