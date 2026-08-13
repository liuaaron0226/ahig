#!/usr/bin/env python3
"""雙盲 title/abstract screening 的不可變指派與確定性對帳。

本模組不判斷文獻資格。它只驗證兩份人工決策是否完整綁定同一批候選，並把
一致決策保留為 resolved、把任何決策分歧或排除理由分歧送往人工 adjudication。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ahig.bootstrap import private_root
from ahig.contracts.freeze import content_hash, freeze_document, verify_frozen
from ahig.state import atomic_write_json


class ScreeningDecisionError(ValueError):
    """screening 決策文件缺漏、漂移或違反雙盲不變量。"""


REASON_CODES = {
    "advance": {"TA-ADV-POTENTIALLY-ELIGIBLE"},
    "exclude": {
        "TA-EXC-ANIMAL-ONLY",
        "TA-EXC-POPULATION-OUT-OF-SCOPE",
        "TA-EXC-INTERVENTION-OUT-OF-SCOPE",
        "TA-EXC-COMPARATOR-OUT-OF-SCOPE",
        "TA-EXC-STUDY-DESIGN-OUT-OF-SCOPE",
        "TA-EXC-SAFETY-BRANCH-OUT-OF-SCOPE",
        "TA-EXC-NOT-PRIMARY-RESEARCH",
        "TA-EXC-NO-ENDURANCE-EXERCISE",
    },
    "unclear": {
        "TA-UNCLEAR-MISSING-ABSTRACT",
        "TA-UNCLEAR-POPULATION",
        "TA-UNCLEAR-INTERVENTION-TIMING",
        "TA-UNCLEAR-STUDY-DESIGN",
        "TA-UNCLEAR-OTHER",
    },
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _queue_hash(manifest: dict, queue: list[dict]) -> str:
    actual = content_hash(queue)
    recorded = manifest.get("screeningQueueHash")
    if recorded != actual:
        raise ScreeningDecisionError(
            f"screening queue hash mismatch：manifest={recorded!r} actual={actual}")
    return actual


def _index_unique(items: list[dict], key: str, *, label: str) -> dict[str, dict]:
    out: dict[str, dict] = {}
    for item in items:
        value = item.get(key)
        if not value:
            raise ScreeningDecisionError(f"{label} missing {key}")
        if value in out:
            raise ScreeningDecisionError(f"duplicate {label} {key}={value}")
        out[value] = item
    return out


def make_assignment(manifest: dict, queue: list[dict], *, candidate_ids: list[str],
                    assignment_id: str, created_at: str | None = None) -> dict:
    """建立綁定 queue 內容的候選批次；候選順序採 candidateId 確定性排序。"""
    queue_hash = _queue_hash(manifest, queue)
    if manifest.get("candidateSourcesComplete") is not True:
        raise ScreeningDecisionError(
            "candidate sources must be complete before screening assignment")
    queue_by_id = _index_unique(queue, "candidateId", label="queue candidate")
    ordered = sorted(candidate_ids)
    if not ordered:
        raise ScreeningDecisionError("assignment candidateIds cannot be empty")
    if len(ordered) != len(set(ordered)):
        raise ScreeningDecisionError("duplicate assignment candidateId")
    missing = sorted(set(ordered) - set(queue_by_id))
    if missing:
        raise ScreeningDecisionError(f"missing candidateIds from queue：{missing[:3]}")
    return {
        "documentType": "title-abstract-screening-assignment",
        "schemaVersion": "1.0.0",
        "assignmentId": assignment_id,
        "runId": manifest["runId"],
        "screeningQueueHash": queue_hash,
        "candidateSetHash": content_hash(ordered),
        "candidateIds": ordered,
        "screeningMode": "dual-blind-title-abstract",
        "requiredReviewerCount": 2,
        "createdAt": created_at or _utc_now(),
    }


def _validate_binding(manifest: dict, queue: list[dict], assignment: dict,
                      review: dict) -> dict[str, dict]:
    queue_hash = _queue_hash(manifest, queue)
    queue_by_id = _index_unique(queue, "candidateId", label="queue candidate")
    assignment_ids = assignment.get("candidateIds") or []
    if not assignment_ids:
        raise ScreeningDecisionError("assignment candidateIds cannot be empty")
    if len(assignment_ids) != len(set(assignment_ids)):
        raise ScreeningDecisionError("duplicate assignment candidateId")
    if assignment_ids != sorted(assignment_ids):
        raise ScreeningDecisionError("assignment candidateIds must be sorted")
    missing_from_queue = sorted(set(assignment_ids) - set(queue_by_id))
    if missing_from_queue:
        raise ScreeningDecisionError(
            f"assignment candidateIds missing from queue：{missing_from_queue[:3]}")
    if assignment.get("screeningQueueHash") != queue_hash:
        raise ScreeningDecisionError("assignment screeningQueueHash mismatch")
    if assignment.get("candidateSetHash") != content_hash(sorted(assignment_ids)):
        raise ScreeningDecisionError("assignment candidateSetHash mismatch")
    if review.get("assignmentId") != assignment.get("assignmentId"):
        raise ScreeningDecisionError("review assignmentId mismatch")
    if review.get("runId") != assignment.get("runId"):
        raise ScreeningDecisionError("review runId mismatch")
    if review.get("screeningQueueHash") != queue_hash:
        raise ScreeningDecisionError("review screeningQueueHash mismatch")
    if review.get("candidateSetHash") != assignment.get("candidateSetHash"):
        raise ScreeningDecisionError("review candidateSetHash mismatch")
    reviewer = review.get("reviewer") or {}
    if reviewer.get("agentClass") not in {"human-self", "human-expert"}:
        raise ScreeningDecisionError("screening reviewer must be human")
    if reviewer.get("blindedToOtherReviewer") is not True:
        raise ScreeningDecisionError("reviewer must be blinded to other reviewer")
    decisions = _index_unique(review.get("decisions") or [], "candidateId",
                              label="review decision")
    for candidate_id, decision in decisions.items():
        value = decision.get("decision")
        if value not in REASON_CODES:
            raise ScreeningDecisionError(
                f"invalid decision for {candidate_id}：{value!r}")
        reason = decision.get("primaryReasonCode")
        if reason not in REASON_CODES[value]:
            raise ScreeningDecisionError(
                f"invalid primaryReasonCode for {candidate_id} decision={value!r}："
                f"{reason!r}")
    expected, actual = set(assignment_ids), set(decisions)
    if actual != expected:
        raise ScreeningDecisionError(
            f"review candidate set mismatch：missing={sorted(expected - actual)[:3]} "
            f"extra={sorted(actual - expected)[:3]}")
    return decisions


def reconcile(manifest: dict, queue: list[dict], assignment: dict,
              review_a: dict, review_b: dict, *,
              completed_at: str | None = None) -> dict:
    """對帳兩位人工審查者；絕不自行裁決資格或排除理由。"""
    by_a = _validate_binding(manifest, queue, assignment, review_a)
    by_b = _validate_binding(manifest, queue, assignment, review_b)
    reviewer_a = review_a["reviewer"]["reviewerId"]
    reviewer_b = review_b["reviewer"]["reviewerId"]
    if reviewer_a == reviewer_b:
        raise ScreeningDecisionError("reviewers must be distinct")
    if review_a.get("reviewId") == review_b.get("reviewId"):
        raise ScreeningDecisionError("reviewIds must be distinct")
    if reviewer_b < reviewer_a:
        review_a, review_b = review_b, review_a
        by_a, by_b = by_b, by_a
        reviewer_a, reviewer_b = reviewer_b, reviewer_a

    resolved: list[dict[str, Any]] = []
    needs: list[dict[str, Any]] = []
    for candidate_id in assignment["candidateIds"]:
        a, b = by_a[candidate_id], by_b[candidate_id]
        if a["decision"] != b["decision"]:
            disagreement = "decision-mismatch"
        elif (a["decision"] == "exclude"
              and a["primaryReasonCode"] != b["primaryReasonCode"]):
            disagreement = "exclusion-reason-mismatch"
        else:
            disagreement = None

        if disagreement:
            needs.append({
                "candidateId": candidate_id,
                "disagreementKind": disagreement,
                "reviewerDecisions": [
                    {"reviewerId": reviewer_a, "decision": a["decision"],
                     "primaryReasonCode": a["primaryReasonCode"]},
                    {"reviewerId": reviewer_b, "decision": b["decision"],
                     "primaryReasonCode": b["primaryReasonCode"]},
                ],
            })
            continue
        resolved.append({
            "candidateId": candidate_id,
            "decision": a["decision"],
            "primaryReasonCodes": sorted({a["primaryReasonCode"],
                                           b["primaryReasonCode"]}),
        })

    counts = {
        "candidateCount": len(assignment["candidateIds"]),
        "agreementCount": len(resolved),
        "needsAdjudicationCount": len(needs),
        "advanceCount": sum(d["decision"] == "advance" for d in resolved),
        "excludeCount": sum(d["decision"] == "exclude" for d in resolved),
        "unclearCount": sum(d["decision"] == "unclear" for d in resolved),
    }
    status = "needs-adjudication" if needs else "resolved"
    assignment_covers_queue = set(assignment["candidateIds"]) == {
        item["candidateId"] for item in queue}
    sources_complete = bool(manifest.get("candidateSourcesComplete"))
    screening_complete = (
        status == "resolved" and assignment_covers_queue and sources_complete)
    blockers = []
    if not sources_complete:
        blockers.append("candidate-sources-incomplete")
    if not screening_complete:
        blockers.append("human-title-abstract-screening-not-completed")
    blockers.append("full-text-screening-not-completed")

    if not sources_complete:
        next_stage = "candidate-source-search"
    elif needs:
        next_stage = "screening-adjudication"
    elif not assignment_covers_queue:
        next_stage = "title-abstract-screening"
    else:
        next_stage = "full-text-screening"

    doc = {
        "documentType": "title-abstract-screening-reconciliation",
        "schemaVersion": "1.0.0",
        "reconciliationId": f"reconcile:{assignment['assignmentId']}",
        "assignmentId": assignment["assignmentId"],
        "runId": assignment["runId"],
        "screeningQueueHash": assignment["screeningQueueHash"],
        "candidateSetHash": assignment["candidateSetHash"],
        "reviewIds": sorted([review_a["reviewId"], review_b["reviewId"]]),
        "reviewerIds": sorted([reviewer_a, reviewer_b]),
        "status": status,
        "resolvedDecisions": resolved,
        "needsAdjudication": needs,
        "counts": counts,
        "assignmentCoversQueue": assignment_covers_queue,
        "candidateSourcesComplete": sources_complete,
        "humanTitleAbstractScreeningComplete": screening_complete,
        "eligibleSamplingPoolReady": False,
        "blockingReasons": blockers,
        "nextStage": next_stage,
        "completedAt": completed_at or _utc_now(),
    }
    return freeze_document(doc, "reconciliationHash",
                           status_field="documentFreezeStatus")


def write_reconciliation(path: Path, reconciliation: dict) -> None:
    root = private_root()
    target = Path(path).expanduser().resolve()
    if target != root and root not in target.parents:
        raise ScreeningDecisionError(
            f"reconciliation output must stay under AHIG_PRIVATE_ROOT：{root}")
    if not verify_frozen(reconciliation, "reconciliationHash"):
        raise ScreeningDecisionError("reconciliation hash is invalid")
    if target.exists():
        existing = json.loads(target.read_text(encoding="utf-8"))
        if existing == reconciliation:
            return
        raise ScreeningDecisionError("reconciliation is immutable once written")
    atomic_write_json(target, reconciliation)
