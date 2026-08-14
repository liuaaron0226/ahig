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

抽樣誠實性的護欄：

- estimate 對源頭重放驗證：重新載入 queue/pool、以同 seed 重放抽樣、逐欄
  比對抽樣區段。audit.json 裡的抽樣內容不是信任來源，只是工作副本——改了
  它（含自行重算 samplingLockHash）也過不了源頭重放。
- ``samplingLockHash`` 作為第一線的意外改動偵測；真正的保證來自上一條。
- ``draws.jsonl`` 是 append-only 抽樣日誌：每次 sample 都留一行，estimate
  回報同一母體被抽過幾次並在多次抽樣時明示警告。挑 seed 不被阻止，但一定
  留痕。
- ``--redo`` 不覆蓋：舊稽核目錄搬進 previous-prevalence-audits/，舊
  estimate.json 改名保留。
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
from ahig.state import atomic_write_bytes, atomic_write_json

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
DEFAULT_EXCLUSION_AUDIT_N = 12

_IMMUTABLE_RECORD_KEYS = ("candidateId", "title", "abstract",
                          "publicationYear", "identifiers", "outcomeHints",
                          "screeningLane")
_IMMUTABLE_EXCLUSION_KEYS = ("candidateId", "title", "abstract",
                             "screeningLane", "flags")

DEFAULT_STRATA_PATH = (Path(__file__).resolve().parents[2] / "calibration"
                       / "b11-carbohydrate" / "strata.json")
# 抽樣證據錨定檔：放在 repo（公開契約側），只含雜湊與識別碼、不含文獻內容。
# 抽樣後 commit+push，竄改抽樣就必須改寫已推送的 git 歷史。
DEFAULT_ANCHOR_PATH = (Path(__file__).resolve().parents[2] / "calibration"
                       / "b11-carbohydrate" / "prevalence-audit-anchors.jsonl")


class PrevalenceAuditError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def clopper_pearson(successes: int, n: int,
                    alpha: float = 0.05) -> tuple[float, float]:
    """雙側 (1-alpha) Clopper–Pearson 精確區間。n=0 時無資訊，回傳 (0, 1)。

    區間本身按二項假設計算；無放回抽樣下偏保守。母體外推的收緊
    （普查塌縮、觀察值夾定）在 :func:`_project` 做。
    """
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


def _project(frame_size: int, lo: float, hi: float, *,
             successes: int, n: int) -> list[int]:
    """比率區間乘回母體，並以有限母體事實夾定。

    - 樣本即母體（普查）時，母體計數已知，區間塌縮為 [k, k]。
    - 下界不得低於樣本中已觀察到的 k（樣本 ⊆ 母體）。
    - 上界不得高於 frame_size - (n - k)（樣本中確定不合格的也在母體裡）。
    """
    if n >= frame_size:
        return [successes, successes]
    lower = max(math.floor(frame_size * lo), successes)
    upper = min(math.ceil(frame_size * hi), frame_size - (n - successes))
    return [lower, upper]


def _require_private(path: Path) -> Path:
    root = private_root()
    resolved = Path(path).expanduser().resolve()
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


def _build_frames(manifest: dict, queue: list[dict],
                  outcome_filter: list[str]) -> tuple[list[str], list[str],
                                                      dict[str, int], str]:
    frame = [e for e in queue if e.get("screeningLane") not in EXCLUDED_LANES]
    if outcome_filter:
        frame = [e for e in frame
                 if set(e.get("outcomeHints", [])) & set(outcome_filter)]
    excluded_pool = [e for e in queue
                     if e.get("screeningLane") in EXCLUDED_LANES]
    exclusion_counts: dict[str, int] = {}
    for entry in excluded_pool:
        lane = entry["screeningLane"]
        exclusion_counts[lane] = exclusion_counts.get(lane, 0) + 1
    frame_ids = sorted(e["candidateId"] for e in frame)
    excluded_ids = sorted(e["candidateId"] for e in excluded_pool)
    frame_hash = content_hash({
        "screeningQueueHash": manifest["screeningQueueHash"],
        "frame": frame_ids, "excludedPool": excluded_ids,
        "outcomeFilter": outcome_filter})
    return frame_ids, excluded_ids, exclusion_counts, frame_hash


def _replay_draw(frame_ids: list[str], excluded_ids: list[str], *,
                 seed: int, n: int, excluded_n: int) -> tuple[list[str],
                                                              list[str]]:
    rng = random.Random(seed)
    sampled = rng.sample(frame_ids, min(n, len(frame_ids)))
    excluded_sample = rng.sample(excluded_ids,
                                 min(excluded_n, len(excluded_ids)))
    return sampled, excluded_sample


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
        "outcomeConfirmed": None,    # 必填：outcomeHints 判讀正確填 true，錯填 false
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
        "frameSize": audit["frameSize"],
        "excludedPoolSize": audit["excludedPoolSize"],
        "outcomeFilter": audit["outcomeFilter"],
        "provenance": [audit["runId"], audit["screeningQueueHash"],
                       audit["candidatePoolHash"]],
        "records": [_immutable(r, _IMMUTABLE_RECORD_KEYS)
                    for r in audit["records"]],
        "exclusionAudit": [_immutable(r, _IMMUTABLE_EXCLUSION_KEYS)
                           for r in audit["exclusionAudit"]],
    })


def derive_seed(queue_hash: str, outcome_filter: list[str]) -> int:
    """從公開狀態確定性導出 seed，拆掉 seed-shopping 的攻擊面。"""
    payload = "\n".join(["prevalence-audit-seed", queue_hash,
                         json.dumps(outcome_filter)])
    return int.from_bytes(
        hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")


def draw_sample(run_root: Path, *, seed: int | None = None, n: int = 50,
                excluded_n: int | None = None,
                outcome_filter: list[str] | None = None,
                anchor_path: Path | None = None,
                redo: bool = False) -> dict:
    """抽出主樣本與誤剔抽查樣本，寫出待回填的稽核檔、判讀表與抽樣日誌。

    ``seed`` 未指定時（預設）從 screeningQueueHash 確定性導出——沒有可挑的
    自由度就沒有 seed-shopping；手動指定會在輸出標記 ``manual``。
    ``excluded_n`` 未指定時預設 12；但 outcome 過濾的補抽（--outcome）預設
    0——補抽的目的只是縮小主樣本框，不該每次都多背 12 筆誤剔判讀。
    """
    run_root = _require_private(run_root)
    manifest, queue, by_id = _load_run(run_root)
    outcome_filter = sorted(outcome_filter or [])
    seed_derivation = "manual" if seed is not None else "derived-from-queue-hash"
    if seed is None:
        seed = derive_seed(manifest["screeningQueueHash"], outcome_filter)
    if excluded_n is None:
        excluded_n = 0 if outcome_filter else DEFAULT_EXCLUSION_AUDIT_N

    frame_ids, excluded_ids, exclusion_counts, frame_hash = _build_frames(
        manifest, queue, outcome_filter)
    if not frame_ids:
        raise PrevalenceAuditError("主抽樣框是空的，無從稽核")
    missing = [cid for cid in frame_ids + excluded_ids if cid not in by_id]
    if missing:
        raise PrevalenceAuditError(
            f"queue 與 candidate pool 不一致，缺 candidate：{missing[:3]}")

    sampled_ids, excluded_sample_ids = _replay_draw(
        frame_ids, excluded_ids, seed=seed, n=n, excluded_n=excluded_n)
    queue_by_id = {e["candidateId"]: e for e in queue}

    audit_id = hashlib.sha256(content_hash({
        "frameHash": frame_hash, "seed": seed, "n": n,
        "excludedN": excluded_n}).encode("utf-8")).hexdigest()[:12]
    audit = {
        "documentType": "prevalence-audit",
        "schemaVersion": "1.2.0",
        "auditId": audit_id,
        "seedDerivation": seed_derivation,
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
        "outcomeFilter": outcome_filter,
        "requestedSampleSize": n,
        "sampleSize": len(sampled_ids),
        "requestedExclusionAuditSize": excluded_n,
        "exclusionAuditSize": len(excluded_sample_ids),
        "samplingRule": "random.Random(seed).sample 於 candidateId 升冪清單；"
                        "先抽主樣本、後抽誤剔樣本，共用同一 rng 狀態",
        "drawnAt": _utc_now(),
        # ADR-0009：回填者必須宣告身分（human，或 llm＋模型資訊）。
        "judgedBy": None,
        "records": [_record(queue_by_id[cid], by_id[cid])
                    for cid in sampled_ids],
        "exclusionAudit": [_exclusion_record(queue_by_id[cid], by_id[cid])
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
    atomic_write_bytes(out / "reading-sheet.md",
                       _reading_sheet(audit).encode("utf-8"))
    with (audit_root / DRAW_LOG).open("a", encoding="utf-8") as log:
        log.write(json.dumps({
            "drawnAt": audit["drawnAt"], "auditId": audit_id, "seed": seed,
            "seedDerivation": seed_derivation,
            "requestedSampleSize": n, "requestedExclusionAuditSize": excluded_n,
            "frameHash": frame_hash,
            "outcomeFilter": outcome_filter,
        }, ensure_ascii=False) + "\n")
    anchor = Path(anchor_path) if anchor_path else DEFAULT_ANCHOR_PATH
    anchor.parent.mkdir(parents=True, exist_ok=True)
    with anchor.open("a", encoding="utf-8") as log:
        log.write(json.dumps({
            "anchoredAt": audit["drawnAt"], "auditId": audit_id,
            "runId": audit["runId"],
            "screeningQueueHash": audit["screeningQueueHash"],
            "frameHash": frame_hash,
            "samplingLockHash": audit["samplingLockHash"],
            "seed": seed, "seedDerivation": seed_derivation,
            "requestedSampleSize": n,
            "requestedExclusionAuditSize": excluded_n,
            "outcomeFilter": outcome_filter,
        }, ensure_ascii=False) + "\n")
    return audit


def _reading_sheet(audit: dict) -> str:
    lines = [
        f"# 劑量可讀性抽查判讀表（audit {audit['auditId']}）",
        "",
        f"- 主抽樣框 {audit['frameSize']} 篇，抽出 {audit['sampleSize']} 篇；"
        f"誤剔母體 {audit['excludedPoolSize']} 篇，抽出 "
        f"{audit['exclusionAuditSize']} 篇（seed={audit['seed']}）",
    ]
    if audit["outcomeFilter"]:
        lines.append(f"- ⚠️ 本次是 outcome 過濾補抽（{audit['outcomeFilter']}）："
                     "主抽樣框已縮小，估計只適用於該子母體。")
    lines += [
        "- 只讀 title/abstract，回填 `audit.json`。第一節每筆欄位：",
        "  - `doseReadability`：exact-value（有明確數值）／intensity-only"
        "（只讀得出強度高低）／not-reported（完全沒寫）",
        "  - `maxDose`：exact-value 時必填 {value, unit}（unit 如 g/h、g/min、"
        "%），其餘兩級 value 與 unit 都留 null",
        "  - `doseBands`：涵蓋到的 band 完整清單（多臂研究列全部）："
        "low(<30) / moderate(30–59.9) / high(60–89.9) / very-high(≥90)。"
        "清單元素 unclear 表示「該篇有讀得出劑量、但無法分帶的臂」，可與"
        "具體 band 並列；not-reported 留 null",
        "  - `outcomeConfirmed`（必填）：這篇的 outcomeHints 是否正確"
        "（true/false）。層級配額計數只採計 true 的紀錄——regex 提示只是"
        "預填，人工判定才是計數依據",
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
    if not audit["exclusionAudit"]:
        lines += ["（本次抽樣不含誤剔抽查。）", ""]
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


def _verify_against_source(run_root: Path, audit: dict) -> None:
    """對源頭重放驗證：audit.json 的抽樣區段必須能從 queue/pool 重新導出。

    這使 samplingLockHash 從「可自行重算的 checksum」升級為「錨定源頭的
    證據」：改 audit.json 的抽樣內容（即使同時重算 lock）也無法通過。
    """
    manifest, queue, by_id = _load_run(run_root)
    for key, manifest_key in (("runId", "runId"),
                              ("screeningQueueHash", "screeningQueueHash"),
                              ("candidatePoolHash", "candidatePoolHash")):
        if audit.get(key) != manifest.get(manifest_key):
            raise PrevalenceAuditError(
                f"audit 的 {key} 與現行 screening-queue manifest 不符；"
                "queue 可能已重建，本稽核不再對應現行母體")
    frame_ids, excluded_ids, _, frame_hash = _build_frames(
        manifest, queue, audit.get("outcomeFilter", []))
    if frame_hash != audit.get("frameHash"):
        raise PrevalenceAuditError("frameHash 與源頭重算不符")
    if (len(frame_ids) != audit.get("frameSize")
            or len(excluded_ids) != audit.get("excludedPoolSize")):
        raise PrevalenceAuditError("frameSize/excludedPoolSize 與源頭不符")
    sampled_ids, excluded_sample_ids = _replay_draw(
        frame_ids, excluded_ids, seed=audit["seed"],
        n=audit["requestedSampleSize"],
        excluded_n=audit["requestedExclusionAuditSize"])
    if sampled_ids != [r["candidateId"] for r in audit["records"]]:
        raise PrevalenceAuditError("重放抽樣與 audit.json 的主樣本不符")
    if excluded_sample_ids != [r["candidateId"]
                               for r in audit["exclusionAudit"]]:
        raise PrevalenceAuditError("重放抽樣與 audit.json 的誤剔樣本不符")
    queue_by_id = {e["candidateId"]: e for e in queue}
    for record in audit["records"]:
        source = _record(queue_by_id[record["candidateId"]],
                         by_id[record["candidateId"]])
        if (_immutable(record, _IMMUTABLE_RECORD_KEYS)
                != _immutable(source, _IMMUTABLE_RECORD_KEYS)):
            raise PrevalenceAuditError(
                f"抽樣內容與源頭不符：{record['candidateId']}")
    for record in audit["exclusionAudit"]:
        source = _exclusion_record(queue_by_id[record["candidateId"]],
                                   by_id[record["candidateId"]])
        if (_immutable(record, _IMMUTABLE_EXCLUSION_KEYS)
                != _immutable(source, _IMMUTABLE_EXCLUSION_KEYS)):
            raise PrevalenceAuditError(
                f"誤剔樣本內容與源頭不符：{record['candidateId']}")


def _validate_filled(audit: dict) -> None:
    problems = []
    judged_by = audit.get("judgedBy")
    if not isinstance(judged_by, dict) or judged_by.get("type") not in (
            "human", "llm"):
        problems.append('judgedBy 必填：{"type": "human"} 或 '
                        '{"type": "llm", "model": {"id":…, "version":…}}'
                        '（ADR-0009）')
    elif judged_by["type"] == "llm":
        model = judged_by.get("model")
        if not (isinstance(model, dict)
                and isinstance(model.get("id"), str) and model["id"].strip()
                and isinstance(model.get("version"), str)
                and model["version"].strip()):
            problems.append("judgedBy.type=llm 必須附 model.id 與 "
                            "model.version（ADR-0009 留痕要求）")
    for i, record in enumerate(audit["records"]):
        cid = record["candidateId"]
        level = record.get("doseReadability")
        bands = record.get("doseBands")
        dose = record.get("maxDose") or {}
        value, unit = dose.get("value"), dose.get("unit")
        confirmed = record.get("outcomeConfirmed")
        if not isinstance(confirmed, bool):
            problems.append(f"records[{i}] {cid}: outcomeConfirmed 必填 "
                            "true/false")
        notes = record.get("notes")
        if notes is not None and not isinstance(notes, str):
            problems.append(f"records[{i}] {cid}: notes 只能是字串或 null")
        if level not in READABILITY_LEVELS:
            problems.append(f"records[{i}] {cid}: doseReadability 未回填或"
                            f"不在 {READABILITY_LEVELS}")
            continue
        if level == "not-reported":
            if bands:
                problems.append(f"records[{i}] {cid}: not-reported 卻填了 "
                                "doseBands")
            if value is not None or unit is not None:
                problems.append(f"records[{i}] {cid}: not-reported 卻填了 "
                                "maxDose")
            continue
        if (not isinstance(bands, list) or not bands
                or not set(bands) <= BAND_VALUES):
            problems.append(f"records[{i}] {cid}: doseBands 必須是 "
                            f"{sorted(BAND_VALUES)} 的非空清單")
        if level == "exact-value":
            if not isinstance(value, (int, float)) or isinstance(value, bool):
                problems.append(f"records[{i}] {cid}: exact-value 必須填 "
                                "maxDose.value 數值")
            if not (isinstance(unit, str) and unit.strip()):
                problems.append(f"records[{i}] {cid}: exact-value 必須填 "
                                "maxDose.unit")
        else:
            if value is not None:
                problems.append(f"records[{i}] {cid}: 讀得出數值就該填 "
                                "exact-value，而非 intensity-only")
            if unit is not None:
                problems.append(f"records[{i}] {cid}: intensity-only 不該"
                                "殘留 maxDose.unit")
    for i, record in enumerate(audit["exclusionAudit"]):
        if not isinstance(record.get("exclusionJustified"), bool):
            problems.append(f"exclusionAudit[{i}] {record['candidateId']}: "
                            "exclusionJustified 未回填")
        notes = record.get("notes")
        if notes is not None and not isinstance(notes, str):
            problems.append(f"exclusionAudit[{i}] {record['candidateId']}: "
                            "notes 只能是字串或 null")
    if problems:
        raise PrevalenceAuditError("稽核表尚未回填完成或有矛盾：\n"
                                   + "\n".join(problems))


def _band_estimates(records: list[dict], frame_size: int,
                    alpha: float) -> dict:
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
            lo, hi = clopper_pearson(k, n, alpha)
            out[band][label] = {
                "count": k, "rate": k / n if n else None,
                "cpInterval": [lo, hi],
                "projectedInFrame": _project(frame_size, lo, hi,
                                             successes=k, n=n),
            }
    return out


def _joint_allocation(records: list[dict], strata: list[dict],
                      levels: tuple[str, ...],
                      outcome_filter: list[str]) -> dict[str, int]:
    """二部圖匹配：一篇只能填一層時，各層最多能同時填到多少（樣本層級）。

    邊際計數會把同一篇算給多層，但配額不得跨層挪用；這裡用 Kuhn 匹配算
    聯合最優分配，補齊邊際讀數的樂觀偏差。只採計 outcomeConfirmed=true。
    """
    slots: list[str] = []
    spec_by_id: dict[str, dict] = {}
    for stratum in strata:
        outcomes = set(stratum.get("primaryOutcomes", []))
        if outcome_filter and not outcomes & set(outcome_filter):
            continue
        sid = stratum["stratumId"]
        spec_by_id[sid] = {"outcomes": outcomes,
                           "bands": set(stratum.get("doseBands", []))}
        slots.extend([sid] * stratum["quota"])
    eligible: list[list[int]] = []
    for record in records:
        if record.get("outcomeConfirmed") is not True:
            continue
        if record["doseReadability"] not in levels:
            continue
        bands = set(record.get("doseBands") or [])
        hints = set(record.get("outcomeHints", []))
        options = [i for i, sid in enumerate(slots)
                   if hints & spec_by_id[sid]["outcomes"]
                   and bands & spec_by_id[sid]["bands"]]
        if options:
            eligible.append(options)

    slot_owner: dict[int, int] = {}

    def try_assign(rec_idx: int, seen: set[int]) -> bool:
        for slot in eligible[rec_idx]:
            if slot in seen:
                continue
            seen.add(slot)
            if slot not in slot_owner or try_assign(slot_owner[slot], seen):
                slot_owner[slot] = rec_idx
                return True
        return False

    for rec_idx in range(len(eligible)):
        try_assign(rec_idx, set())
    allocation: dict[str, int] = {}
    for slot in slot_owner:
        allocation[slots[slot]] = allocation.get(slots[slot], 0) + 1
    return allocation


def _stratum_feasibility(records: list[dict], frame_size: int,
                         strata: list[dict], outcome_filter: list[str],
                         alpha: float) -> list[dict]:
    n = len(records)
    outcome_sets = {s["stratumId"]: set(s.get("primaryOutcomes", []))
                    for s in strata}
    results = []
    for stratum in strata:
        sid = stratum["stratumId"]
        outcomes = outcome_sets[sid]
        if outcome_filter and not outcomes & set(outcome_filter):
            results.append({"stratumId": sid,
                            "skippedReason": "outcome-filtered-draw",
                            "note": "本次抽樣框已按 outcome 過濾，與此層無交集，"
                                    "不產生判定"})
            continue
        bands = set(stratum.get("doseBands", []))
        quota = stratum.get("quota")
        if not isinstance(quota, int) or isinstance(quota, bool) or quota <= 0:
            raise PrevalenceAuditError(
                f"strata 檔的 {sid} quota 必須是正整數：{quota!r}")
        rows = {}
        for label, levels in (("strict", ("exact-value",)),
                              ("lenient", ("exact-value", "intensity-only"))):
            # 只採計人工確認過 outcome 的紀錄：regex 提示誤報不得抬高下界。
            k = sum(1 for r in records
                    if r.get("outcomeConfirmed") is True
                    and set(r.get("outcomeHints", [])) & outcomes
                    and r["doseReadability"] in levels
                    and set(r.get("doseBands") or []) & bands)
            lo, hi = clopper_pearson(k, n, alpha)
            projected = _project(frame_size, lo, hi, successes=k, n=n)
            if projected[0] >= quota:
                verdict = "likely-sufficient"
            elif projected[1] < quota:
                verdict = "likely-insufficient"
            else:
                verdict = "not-demonstrated"
            rows[label] = {"count": k, "cpInterval": [lo, hi],
                           "projectedInFrame": projected,
                           "verdictAtBound": verdict}
        outcome_group_n = sum(1 for r in records
                              if r.get("outcomeConfirmed") is True
                              and set(r.get("outcomeHints", [])) & outcomes)
        overlapping = sorted(other for other, other_set in outcome_sets.items()
                             if other != sid and other_set & outcomes)
        results.append({
            "stratumId": sid,
            "quota": quota,
            "outcomeGroupSampleCount": outcome_group_n,
            "insufficientAuditData": outcome_group_n < 5,
            "overlappingStrata": overlapping,
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


def _verify_anchor(anchor_path: Path | None, audit: dict) -> str:
    """抽樣證據必須已錨定：anchor 檔要有與本稽核一致的一行。"""
    path = Path(anchor_path) if anchor_path else DEFAULT_ANCHOR_PATH
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            entry = json.loads(line)
            if (entry.get("auditId") == audit["auditId"]
                    and entry.get("samplingLockHash")
                    == audit["samplingLockHash"]
                    and entry.get("frameHash") == audit["frameHash"]):
                return str(path)
    raise PrevalenceAuditError(
        f"抽樣證據未錨定或與稽核不符：{path} 裡沒有對應 "
        f"auditId={audit['auditId']} 的錨定紀錄。抽樣與錨定必須出自同一次 "
        "sample；錨定檔應 commit 進 git 並推送。")


def _count_draws(audit_root: Path, frame_hash: str) -> int:
    log = audit_root / DRAW_LOG
    if not log.exists():
        return 0
    count = 0
    for line in log.read_text(encoding="utf-8").splitlines():
        if line.strip() and json.loads(line).get("frameHash") == frame_hash:
            count += 1
    return count


def _load_strata(strata_path: Path | None) -> tuple[dict, dict]:
    path = Path(strata_path) if strata_path else DEFAULT_STRATA_PATH
    raw = path.read_bytes()  # 只讀一次：parse 與 sha256 用同一份 bytes
    doc = json.loads(raw.decode("utf-8"))
    if doc.get("status") != "frozen":
        raise PrevalenceAuditError(
            f"strata 檔必須 status=frozen：{path}")
    meta = {
        "strataFile": str(path),
        "strataVersion": doc.get("version"),
        "strataFileSha256": hashlib.sha256(raw).hexdigest(),
        "strataOverride": strata_path is not None,
    }
    return doc, meta


def estimate(audit_dir: Path, *, strata_path: Path | None = None,
             anchor_path: Path | None = None, redo: bool = False) -> dict:
    """讀回填完成的 audit.json，對源頭重放與錨定驗證後產出母體推估。"""
    audit_dir = _require_private(audit_dir)
    run_root = audit_dir.parents[1]
    audit = json.loads((audit_dir / "audit.json").read_text(encoding="utf-8"))
    if _sampling_lock(audit) != audit.get("samplingLockHash"):
        raise PrevalenceAuditError(
            "samplingLockHash 驗證失敗：抽樣區段在回填期間被更動。")
    _verify_against_source(run_root, audit)
    anchor_file = _verify_anchor(anchor_path, audit)
    _validate_filled(audit)

    records = audit["records"]
    exclusion_records = audit["exclusionAudit"]
    n = len(records)
    frame_size = audit["frameSize"]
    outcome_filter = audit.get("outcomeFilter", [])

    readability_counts = {
        level: sum(1 for r in records if r["doseReadability"] == level)
        for level in READABILITY_LEVELS}
    hint_rejected = sum(1 for r in records
                        if r["outcomeConfirmed"] is False)

    strata_doc, strata_meta = _load_strata(strata_path)

    # 同一母體抽樣多次時做 Bonferroni 收緊，讓區間涵蓋率的宣稱仍成立。
    draws = _count_draws(audit_dir.parent, audit["frameHash"])
    alpha = 0.05 / max(draws, 1)

    m = len(exclusion_records)
    k_bad = sum(1 for r in exclusion_records
                if r["exclusionJustified"] is False)
    exclusion_result = {
        "sampleSize": m,
        "unjustifiedCount": k_bad,
        "falseExclusionRateUpperBound": clopper_pearson_upper(k_bad, m, alpha),
        "projectedLostUpperBound": math.ceil(
            audit["excludedPoolSize"]
            * clopper_pearson_upper(k_bad, m, alpha)),
        "note": ("本次抽樣不含誤剔抽查，上界無資訊量（=1）。" if m == 0 else
                 "上界隨樣本數縮小；預設 12 筆只能證明 <~22%，作煙霧測試用。"
                 "要證明 <10% 需約 30 筆（零誤剔時）。"),
    }

    interpretation = {
        "quotaRule": "配額判斷取 Clopper–Pearson 下界（保守側）並以有限母體"
                     "夾定（普查塌縮為精確計數）；strict 只算 exact-value，"
                     "lenient 含 intensity-only。",
        "frameCaveat": "抽樣框已扣除動物／綜述／registry／安全四類；外推只及"
                       "於主池。誤剔抽查另行估上界。",
        "marginalCountingCaveat": "各層計數是邊際的：同一篇可同時支撐多層"
                                  "（見各層 overlappingStrata），但配額不得跨層"
                                  "挪用，故逐層 likely-sufficient 不蘊涵聯合"
                                  "可行；jointSampleAllocation 給出樣本層級的"
                                  "聯合最優分配。S5/S6 在摘要層無法分辨 "
                                  "primary 與 secondary，兩層讀數必然相同。",
        "outcomeHintCaveat": "層級計數只採計 outcomeConfirmed=true 的紀錄；"
                             "regex 提示只是預填，誤報（outcomeHintRejected"
                             "Count）不會進入計數。",
        "powerCaveat": "outcomeGroupSampleCount < 5 的層，區間近乎無資訊量；"
                       "用 sample --outcome 對該層補抽，勿逕自解讀為不足。",
    }
    if outcome_filter:
        interpretation["outcomeFilterCaveat"] = (
            f"本稽核來自 outcome 過濾補抽（{outcome_filter}）：frameSize 是"
            "過濾後子母體，所有外推只適用於該子母體，與主池估計不可直接相加。")
    multiplicity_warning = None
    if draws > 1:
        multiplicity_warning = (
            f"同一母體已被抽樣 {draws} 次（見 draws.jsonl）。所有區間已以 "
            f"Bonferroni 收緊至 α={alpha:.4f}；請在決策文件中列出全部抽樣"
            "與棄用理由。")

    strata_list = strata_doc.get("strata", [])
    result = {
        "documentType": "prevalence-audit-estimate",
        "schemaVersion": "1.2.0",
        "auditId": audit["auditId"],
        "runId": audit["runId"],
        "screeningQueueHash": audit["screeningQueueHash"],
        "candidatePoolHash": audit["candidatePoolHash"],
        "samplingLockHash": audit["samplingLockHash"],
        "judgedBy": audit.get("judgedBy"),
        "groundTruthLabel": (
            "AI-graded evidence — no human expert review (ADR-0009)"
            if (audit.get("judgedBy") or {}).get("type") == "llm"
            else "human-judged"),
        "sourceReplayVerified": True,
        "anchorFile": anchor_file,
        "seed": audit["seed"],
        "seedDerivation": audit.get("seedDerivation"),
        "sampleSize": n,
        "frameSize": frame_size,
        "frameHash": audit["frameHash"],
        "outcomeFilter": outcome_filter,
        "isCensus": n >= frame_size,
        "drawsForSameFrame": draws,
        "alpha": alpha,
        "multiplicityWarning": multiplicity_warning,
        **strata_meta,
        "readabilityCounts": readability_counts,
        "outcomeHintRejectedCount": hint_rejected,
        "bandEstimates": _band_estimates(records, frame_size, alpha),
        "stratumFeasibility": _stratum_feasibility(
            records, frame_size, strata_list, outcome_filter, alpha),
        "jointSampleAllocation": {
            "strict": _joint_allocation(records, strata_list,
                                        ("exact-value",), outcome_filter),
            "lenient": _joint_allocation(
                records, strata_list,
                ("exact-value", "intensity-only"), outcome_filter),
            "note": "樣本層級的聯合最優分配（一篇只能填一層）；逐層邊際讀數"
                    "的樂觀偏差以此校正。",
        },
        "exclusionAudit": exclusion_result,
        "regexAudit": _regex_audit(records),
        "interpretation": interpretation,
        "decisionRemainsHuman": True,
        "estimatedAt": _utc_now(),
    }

    out_path = audit_dir / "estimate.json"
    if out_path.exists():
        if not redo:
            raise FileExistsError(f"{out_path} 已存在；重算請用 --redo")
        serial = 1
        superseded = audit_dir / "estimate-superseded-1.json"
        while superseded.exists():
            serial += 1
            superseded = audit_dir / f"estimate-superseded-{serial}.json"
        shutil.move(str(out_path), str(superseded))
    atomic_write_json(out_path, result)
    return result


_BAND_ALIASES = {"l": "low", "m": "moderate", "h": "high", "v": "very-high",
                 "u": "unclear", "low": "low", "moderate": "moderate",
                 "high": "high", "very-high": "very-high",
                 "unclear": "unclear"}


def _parse_bands(raw: str) -> list[str] | None:
    tokens = [t for t in raw.replace(",", " ").split() if t]
    if not tokens:
        return None
    bands = []
    for token in tokens:
        band = _BAND_ALIASES.get(token.lower())
        if band is None:
            return None
        if band not in bands:
            bands.append(band)
    return bands


def fill_interactive(audit_dir: Path, *, input_fn=input,
                     print_fn=print) -> dict:
    """逐篇互動回填 audit.json——判斷仍是人做的，工具只免去手改 JSON。

    每答完一筆立即存檔；隨時 q 中斷，重跑會從第一筆未回填的接著問。
    """
    audit_dir = _require_private(audit_dir)
    path = audit_dir / "audit.json"
    audit = json.loads(path.read_text(encoding="utf-8"))

    audit["judgedBy"] = {"type": "human"}

    def save() -> None:
        atomic_write_json(path, audit)

    def ask(prompt: str, *, allow_empty: bool = False) -> str:
        while True:
            value = input_fn(prompt).strip()
            if value or allow_empty:
                return value

    filled_records = filled_exclusions = 0
    records = audit["records"]
    for i, record in enumerate(records, 1):
        if (record.get("doseReadability") in READABILITY_LEVELS
                and isinstance(record.get("outcomeConfirmed"), bool)):
            continue
        print_fn(f"\n── 第一節 {i}/{len(records)} ─ {record['candidateId']}")
        print_fn(f"標題：{record.get('title') or '(無標題)'}")
        print_fn(f"摘要：{record.get('abstract') or '(無摘要 → 選 n)'}")
        print_fn(f"outcomeHints（regex 預判）：{record.get('outcomeHints')}")
        while True:
            level = ask("劑量可讀性 [e]xact / [i]ntensity / [n]ot-reported "
                        "/ [q]uit：").lower()
            if level in ("e", "i", "n", "q"):
                break
        if level == "q":
            save()
            break
        if level == "n":
            record.update(doseReadability="not-reported", doseBands=None,
                          maxDose={"value": None, "unit": None})
        else:
            while True:
                bands = _parse_bands(ask(
                    "band 清單（l=low m=moderate h=high v=very-high "
                    "u=unclear，逗號或空白分隔）："))
                if bands:
                    break
            if level == "e":
                while True:
                    try:
                        value = float(ask("最高劑量數值："))
                        break
                    except ValueError:
                        continue
                unit = ask("單位（如 g/h）：")
                record.update(doseReadability="exact-value", doseBands=bands,
                              maxDose={"value": value, "unit": unit})
            else:
                record.update(doseReadability="intensity-only",
                              doseBands=bands,
                              maxDose={"value": None, "unit": None})
        while True:
            confirmed = ask("outcomeHints 正確嗎？[y/n]：").lower()
            if confirmed in ("y", "n"):
                break
        record["outcomeConfirmed"] = confirmed == "y"
        notes = ask("備註（Enter 跳過）：", allow_empty=True)
        record["notes"] = notes or None
        filled_records += 1
        save()
    else:
        for i, record in enumerate(audit["exclusionAudit"], 1):
            if isinstance(record.get("exclusionJustified"), bool):
                continue
            print_fn(f"\n── 第二節 {i}/{len(audit['exclusionAudit'])} ─ "
                     f"{record['candidateId']}（lane: "
                     f"{record['screeningLane']}）")
            print_fn(f"標題：{record.get('title') or '(無標題)'}")
            print_fn(f"摘要：{record.get('abstract') or '(無摘要)'}")
            while True:
                justified = ask("被分流出主池是否正確？[y/n]（q 中斷）：").lower()
                if justified in ("y", "n", "q"):
                    break
            if justified == "q":
                save()
                break
            record["exclusionJustified"] = justified == "y"
            notes = ask("備註（Enter 跳過）：", allow_empty=True)
            record["notes"] = notes or None
            filled_exclusions += 1
            save()

    remaining = sum(
        1 for r in audit["records"]
        if r.get("doseReadability") not in READABILITY_LEVELS
        or not isinstance(r.get("outcomeConfirmed"), bool)) + sum(
        1 for r in audit["exclusionAudit"]
        if not isinstance(r.get("exclusionJustified"), bool))
    summary = {"filledRecords": filled_records,
               "filledExclusions": filled_exclusions,
               "remainingUnfilled": remaining}
    print_fn(f"\n本次回填 {filled_records}＋{filled_exclusions} 筆，"
             f"還剩 {remaining} 筆未完成。"
             + ("可以跑 estimate 了。" if remaining == 0
                else "重跑 fill 可接著填。"))
    return summary


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p_sample = sub.add_parser("sample", help="抽出待判讀樣本")
    p_sample.add_argument("run_root", type=Path)
    p_sample.add_argument("--seed", type=int, default=None,
                          help="手動抽樣種子（輸出會標記 manual）；預設從 "
                               "screeningQueueHash 確定性導出，無從挑選")
    p_sample.add_argument("--n", type=int, default=50)
    p_sample.add_argument("--excluded-n", type=int, default=None,
                          help="誤剔抽查樣本數（預設 12；--outcome 補抽時"
                               "預設 0）")
    p_sample.add_argument("--outcome", action="append", dest="outcomes",
                          help="可重複：把主抽樣框縮到含指定 outcome hint 的"
                               "候選（稀少層補抽用）")
    p_sample.add_argument("--anchor", type=Path, default=None,
                          help="抽樣證據錨定檔（預設 repo 內 "
                               "prevalence-audit-anchors.jsonl；記得 "
                               "commit+push）")
    p_sample.add_argument("--redo", action="store_true")
    p_fill = sub.add_parser("fill", help="逐篇互動回填判讀（可中斷續填）")
    p_fill.add_argument("audit_dir", type=Path)
    p_estimate = sub.add_parser("estimate", help="以回填完成的稽核表推估母體")
    p_estimate.add_argument("audit_dir", type=Path)
    p_estimate.add_argument("--strata", type=Path, default=None,
                            help="覆蓋預設 strata 檔（會在輸出標記 "
                                 "strataOverride）")
    p_estimate.add_argument("--anchor", type=Path, default=None,
                            help="錨定檔位置（預設同 sample）")
    p_estimate.add_argument("--redo", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "sample":
        result = draw_sample(args.run_root, seed=args.seed, n=args.n,
                             excluded_n=args.excluded_n,
                             outcome_filter=args.outcomes,
                             anchor_path=args.anchor, redo=args.redo)
        out = {key: result[key] for key in
               ("auditId", "sampleSize", "exclusionAuditSize", "frameSize",
                "excludedPoolSize", "seed", "seedDerivation")}
        print(json.dumps(out, ensure_ascii=False, indent=2))
        print("提醒：錨定檔已更新，記得 commit + push。")
    elif args.command == "fill":
        fill_interactive(args.audit_dir)
    else:
        result = estimate(args.audit_dir, strata_path=args.strata,
                          anchor_path=args.anchor, redo=args.redo)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
