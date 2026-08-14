#!/usr/bin/env python3
"""W8：AI 主篩選的批次驅動器（ADR-0009 信任模型）。

從 screening queue 依優先序取批、交給**可注入的判讀器**判
advance/exclude/unclear、把結果固化成可稽核批次。

**本模組不呼叫任何 LLM，也不碰網路**——沿用 ``llm_second_review`` 的架構
分離：判讀器是一個 ``(list[dict]) -> list[dict]`` 的 callable，由呼叫端提供。
測試用假判讀器，正式用真模型呼叫層。這樣證據管理的正確性可以完全離線
驗證，不受 API 可用性與費用影響。

不變量：

- **驅動器不做資格判定**。它只負責「取哪一批、把回應固化成什麼形狀」；
  advance/exclude 由判讀器產生，且每筆都必須帶 ``judgedBy``（ADR-0009
  原則 2：缺此欄位的判讀不得進入任何下游計算）。
- **不改 queue**。取批只讀不寫，``screeningQueueHash`` 不受影響。
- **批次可重放**。同一組 candidateId ＋ 同一判讀器 → 同樣的批次內容雜湊；
  取批本身是確定性的（依既定順序，不用隨機）。
- **留痕齊全**。prompt 範本、模型 id/版本、原始回應全文、時間戳一律落盤，
  由 ``llm_second_review.build_opinion_batch`` 統一固化並入雜湊鏈。
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any

from ahig.contracts.freeze import content_hash
from ahig.search.llm_second_review import OPINIONS, build_opinion_batch
from ahig.state import atomic_write_json

# 協調者建議 100 筆/輪（W8 派發）。
DEFAULT_BATCH_SIZE = 100

# ADR-0008：正式篩選前先以隨機前置樣本估盛行率，池子的 1–2%。
PILOT_FRACTION_MIN = 0.01
PILOT_FRACTION_MAX = 0.02

JudgeFn = Callable[[list[dict]], list[dict]]


class ScreeningDriverError(ValueError):
    """驅動器輸入缺漏、判讀器回應違規，或違反取批不變量。"""


def _entry_payload(entry: dict, abstracts: dict[str, str] | None) -> dict:
    """交給判讀器的資料。刻意只給題摘層資訊。

    不給 ``priorityTier``／``matchedRuleIds``／``suggestedStrata`` 等 regex
    推論結果——那些是我們自己的先驗，餵給模型會讓它跟著 regex 的偏誤走，
    影子批次也就測不出模型的獨立判斷力。
    """
    return {
        "candidateId": entry["candidateId"],
        "title": entry.get("title"),
        "abstract": (abstracts or {}).get(entry["candidateId"]),
        "publicationYear": entry.get("publicationYear"),
    }


def take_batch(queue: Sequence[dict], *, already_judged: set[str] | None = None,
               batch_size: int = DEFAULT_BATCH_SIZE,
               ranked_order: Sequence[str] | None = None) -> list[dict]:
    """依優先序取下一批未判讀的候選。

    ``ranked_order``：W6 AL 重排後的 candidateId 順序（``al-rank/``）。
    給了就照它取，否則照 queue 既有順序。兩者都是確定性的。
    """
    if batch_size <= 0:
        raise ScreeningDriverError("batch_size 必須為正整數")
    judged = already_judged or set()
    by_id = {e["candidateId"]: e for e in queue}
    if ranked_order is not None:
        unknown = [cid for cid in ranked_order if cid not in by_id]
        if unknown:
            raise ScreeningDriverError(
                f"ranked_order 含不在 queue 的 candidateId：{unknown[:3]}")
        if len(ranked_order) != len(by_id):
            raise ScreeningDriverError(
                f"ranked_order 未覆蓋整個 queue："
                f"{len(ranked_order)} vs {len(by_id)}")
        ordered = [by_id[cid] for cid in ranked_order]
    else:
        ordered = list(queue)
    return [e for e in ordered if e["candidateId"] not in judged][:batch_size]


def _validate_judgements(batch: list[dict], raw: Any) -> list[dict]:
    """判讀器回應的結構檢查。壞掉要當場炸，不要靜默略過。"""
    if not isinstance(raw, list):
        raise ScreeningDriverError(
            f"判讀器必須回傳 list，得到 {type(raw).__name__}")
    expected = {e["candidateId"] for e in batch}
    seen: set[str] = set()
    out = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise ScreeningDriverError(f"判讀[{i}] 必須是 dict")
        cid = item.get("candidateId")
        if cid not in expected:
            raise ScreeningDriverError(f"判讀[{i}] 的 candidateId 不在批次內：{cid}")
        if cid in seen:
            raise ScreeningDriverError(f"判讀[{i}] 重複 candidateId：{cid}")
        seen.add(cid)
        opinion = item.get("opinion")
        if opinion not in OPINIONS:
            raise ScreeningDriverError(
                f"判讀[{i}] {cid}: opinion 必須是 {OPINIONS}，得到 {opinion!r}")
        response = item.get("rawResponse")
        if not (isinstance(response, str) and response.strip()):
            raise ScreeningDriverError(
                f"判讀[{i}] {cid}: 必須保留原始回應全文（ADR-0009 原則 3）")
        judged_by = item.get("judgedBy")
        if not isinstance(judged_by, dict) or not judged_by.get("agentClass"):
            raise ScreeningDriverError(
                f"判讀[{i}] {cid}: 缺 judgedBy——ADR-0009 原則 2 規定"
                "缺此欄位的判讀不得進入任何下游計算")
        out.append(item)
    missing = sorted(expected - seen)
    if missing:
        raise ScreeningDriverError(
            f"判讀器未覆蓋整批，缺 {missing[:3]}（共 {len(missing)} 筆）")
    return out


def run_batch(queue_manifest: dict, queue: Sequence[dict], batch: list[dict],
              judge: JudgeFn, *, model_id: str, model_version: str,
              prompt_template: str,
              abstracts: dict[str, str] | None = None) -> dict:
    """對一批候選跑判讀，回傳固化後的可稽核批次。"""
    if not batch:
        raise ScreeningDriverError("批次是空的")
    payload = [_entry_payload(e, abstracts) for e in batch]
    judgements = _validate_judgements(batch, judge(payload))
    opinions = [{"candidateId": j["candidateId"], "opinion": j["opinion"],
                 "rawResponse": j["rawResponse"]} for j in judgements]
    fixed = build_opinion_batch(
        queue_manifest, list(queue), opinions, model_id=model_id,
        model_version=model_version, prompt_template=prompt_template)
    fixed["judgedBy"] = {
        "agentClass": "llm",
        "modelId": model_id,
        "modelVersion": model_version,
    }
    fixed["evidenceGrade"] = "AI-graded evidence — no human expert review"
    fixed["batchCandidateSetHash"] = content_hash(
        sorted(e["candidateId"] for e in batch))
    return fixed


def pilot_sample(queue: Sequence[dict], *, fraction: float = PILOT_FRACTION_MIN,
                 seed: str) -> dict:
    """ADR-0008 的隨機前置樣本：估盛行率、餵養排序模型。

    抽樣必須**確定性**且可重放——用 seed ＋ candidateId 的雜湊排序，不用
    ``random``。這樣同一個 seed 永遠得到同一組樣本，稽核時能重算。
    """
    if not PILOT_FRACTION_MIN <= fraction <= PILOT_FRACTION_MAX:
        raise ScreeningDriverError(
            f"前置樣本比例須介於 {PILOT_FRACTION_MIN}–{PILOT_FRACTION_MAX}"
            f"（ADR-0008），得到 {fraction}")
    if not seed:
        raise ScreeningDriverError("必須提供 seed 才能重放抽樣")
    ids = sorted(e["candidateId"] for e in queue)
    if not ids:
        raise ScreeningDriverError("queue 是空的")
    size = max(1, round(len(ids) * fraction))
    keyed = sorted(
        ids, key=lambda cid: hashlib.sha256(
            f"{seed}:{cid}".encode("utf-8")).hexdigest())
    sample = sorted(keyed[:size])
    return {
        "documentType": "screening-pilot-sample",
        "adr": "ADR-0008",
        "seed": seed,
        "fraction": fraction,
        "poolSize": len(ids),
        "sampleSize": len(sample),
        "candidateIds": sample,
        "sampleHash": content_hash(sample),
        "method": "deterministic-sha256-keyed-sort",
        "note": "確定性抽樣：同 seed 可完整重放，稽核時能重算。",
    }


def estimate_prevalence(sample: dict, judgements: dict[str, str]) -> dict:
    """由前置樣本的判讀結果估盛行率（advance 比例）。

    ``unclear`` 不當 advance 也不當 exclude，另計——把猶豫硬歸一邊會讓
    盛行率失真。回傳同時給「保守下界」與「上界」，供排序模型與工時估算
    使用；不做信賴區間，那是 ADR-0008 統計終止那條線的事。
    """
    expected = set(sample["candidateIds"])
    missing = sorted(expected - set(judgements))
    if missing:
        raise ScreeningDriverError(
            f"前置樣本未判讀完整，缺 {missing[:3]}（共 {len(missing)} 筆）")
    values = [judgements[cid] for cid in sorted(expected)]
    bad = sorted({v for v in values if v not in OPINIONS})
    if bad:
        raise ScreeningDriverError(f"判讀值非法：{bad}")
    n = len(values)
    advance = sum(v == "advance" for v in values)
    unclear = sum(v == "unclear" for v in values)
    return {
        "documentType": "screening-prevalence-estimate",
        "adr": "ADR-0008",
        "sampleHash": sample["sampleHash"],
        "sampleSize": n,
        "advanceCount": advance,
        "excludeCount": sum(v == "exclude" for v in values),
        "unclearCount": unclear,
        "prevalenceLowerBound": advance / n,
        "prevalenceUpperBound": (advance + unclear) / n,
        "poolSize": sample["poolSize"],
        "projectedAdvanceLow": round(sample["poolSize"] * advance / n),
        "projectedAdvanceHigh": round(
            sample["poolSize"] * (advance + unclear) / n),
        "note": ("unclear 另計，不併入任一端；下界視 unclear 全為 exclude、"
                 "上界視 unclear 全為 advance。"),
    }


def load_run_root(run_root: Path) -> dict:
    """讀 run root 的 queue、manifest、abstract 與 AL 排序（若有）。"""
    run_root = Path(run_root).resolve()
    qdir = run_root / "screening-queue"
    queue = json.loads((qdir / "queue.json").read_text(encoding="utf-8"))
    manifest = json.loads((qdir / "manifest.json").read_text(encoding="utf-8"))
    abstracts = None
    candidates = run_root / "candidate-pool" / "candidates.json"
    if candidates.exists():
        abstracts = {c["candidateId"]: c.get("abstract") or ""
                     for c in json.loads(candidates.read_text(encoding="utf-8"))}
    ranked = None
    ranked_path = run_root / "al-rank" / "ranked-order.json"
    if ranked_path.exists():
        ranked = json.loads(ranked_path.read_text(encoding="utf-8"))
    return {"queue": queue, "manifest": manifest, "abstracts": abstracts,
            "rankedOrder": ranked, "runRoot": run_root}


def write_pilot_sample(run_root: Path, *, fraction: float = PILOT_FRACTION_MIN,
                       seed: str) -> dict:
    """產生並落盤 ADR-0008 前置樣本（只寫樣本清單，不含判讀）。"""
    loaded = load_run_root(run_root)
    sample = pilot_sample(loaded["queue"], fraction=fraction, seed=seed)
    sample["runId"] = loaded["manifest"].get("runId")
    sample["screeningQueueHash"] = loaded["manifest"].get("screeningQueueHash")
    out = loaded["runRoot"] / "screening-pilot"
    out.mkdir(parents=True, exist_ok=True)
    atomic_write_json(out / "sample.json", sample)
    return sample


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    pilot = sub.add_parser("pilot", help="產生 ADR-0008 隨機前置樣本")
    pilot.add_argument("run_root", type=Path)
    pilot.add_argument("--seed", required=True)
    pilot.add_argument("--fraction", type=float, default=PILOT_FRACTION_MIN)
    peek = sub.add_parser("next-batch", help="列出下一批要判讀的候選")
    peek.add_argument("run_root", type=Path)
    peek.add_argument("--batch-size", type=int, default=DEFAULT_BATCH_SIZE)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "pilot":
        result = write_pilot_sample(args.run_root, fraction=args.fraction,
                                    seed=args.seed)
    else:
        loaded = load_run_root(args.run_root)
        batch = take_batch(loaded["queue"], batch_size=args.batch_size,
                           ranked_order=loaded["rankedOrder"])
        result = {"batchSize": len(batch),
                  "candidateIds": [e["candidateId"] for e in batch]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
