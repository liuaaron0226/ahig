#!/usr/bin/env python3
"""雙盲 title/abstract screening 的不可變指派與確定性對帳。

本模組不判斷文獻資格。它只驗證兩份人工決策是否完整綁定同一批候選，並把
一致決策保留為 resolved、把任何決策分歧或排除理由分歧送往人工 adjudication。

W9（ADR-0009 裁定②）新增機器對帳路徑 :func:`reconcile_machine`：人類路徑
（:func:`reconcile`／:func:`_validate_binding` 的人類閘）一行不動，機器路徑
另開，兩者共用同一份文件綁定檢查（:func:`_validate_envelope`）。機器路徑的
不變量與 :func:`ahig.search.llm_second_review.machine_shadow_gate` 同一條紀律：

- 兩位 reviewer 皆為 LLM 且 modelId 必須相異——這是雙模型盲判的執行點；
- judgedBy 依 ADR-0009 原則 2／3 完整落盤（含 rawResponse 對應的判讀理由）；
- 對立判讀與任一方 unclear 一律進 ownerAuditQueue，**不自動裁決**，產物
  結構上不存在 resolved／decision 這類自動欄位（ADR-0009 原則 5）。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ahig.bootstrap import private_root
from ahig.contracts.freeze import content_hash, freeze_document, verify_frozen
from ahig.search.llm_second_review import (
    _FORBIDDEN_ENTRY_KEYS as _FORBIDDEN_JUDGEMENT_KEYS,
)
from ahig.search.llm_second_review import OPINIONS as MACHINE_OPINIONS
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


def _validate_envelope(manifest: dict, queue: list[dict], assignment: dict,
                       review: dict) -> list[str]:
    """驗證指派與審查文件的交叉綁定；不碰 reviewer 身分與判讀內容。

    人類路徑與機器路徑共用這段——綁定漂移的定義不因判讀者是人是機而不同。
    回傳指派的候選 id（已確認排序、無重複、全在 queue 內）。
    """
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
    return list(assignment_ids)


def _validate_binding(manifest: dict, queue: list[dict], assignment: dict,
                      review: dict) -> dict[str, dict]:
    assignment_ids = _validate_envelope(manifest, queue, assignment, review)
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


def _validate_machine_binding(manifest: dict, queue: list[dict], assignment: dict,
                              review: dict) -> tuple[dict[str, dict], dict]:
    """機器審查文件的綁定＋留痕檢查。回傳 (判讀索引, judgedBy)。

    與人類路徑對稱但閘門不同：這裡要求 reviewer 為 LLM、judgedBy 依
    ADR-0009 原則 2／3 完整、每筆判讀附 rawResponse。任何一項缺漏都
    fail-closed——ADR-0009 原則 2 明定缺 judgedBy 的判讀不得進入任何下游計算。
    """
    assignment_ids = _validate_envelope(manifest, queue, assignment, review)

    reviewer = review.get("reviewer") or {}
    if reviewer.get("agentClass") != "llm":
        raise ScreeningDecisionError(
            "machine screening reviewer must have agentClass == 'llm'："
            f"{reviewer.get('agentClass')!r}")
    if not reviewer.get("reviewerId"):
        raise ScreeningDecisionError("machine reviewer missing reviewerId")
    if reviewer.get("blindedToOtherReviewer") is not True:
        raise ScreeningDecisionError(
            "machine reviewer must be blinded to other reviewer")

    judged_by = review.get("judgedBy")
    if not isinstance(judged_by, dict):
        raise ScreeningDecisionError(
            "機器審查缺 judgedBy——ADR-0009 原則 2 規定缺此欄位的判讀"
            "不得進入任何下游計算")
    if judged_by.get("agentClass") != "llm":
        raise ScreeningDecisionError(
            f"judgedBy.agentClass must be 'llm'：{judged_by.get('agentClass')!r}")
    for field in ("modelId", "modelVersion"):
        if not judged_by.get(field):
            raise ScreeningDecisionError(
                f"judgedBy 缺 {field}——ADR-0009 原則 3 要求模型與版本落盤入雜湊鏈")

    judgements = _index_unique(review.get("judgements") or [], "candidateId",
                               label="machine judgement")
    for candidate_id, item in judgements.items():
        forbidden = sorted(set(item) & _FORBIDDEN_JUDGEMENT_KEYS)
        if forbidden:
            raise ScreeningDecisionError(
                f"機器判讀 {candidate_id} 攜帶人類決策欄位，違反盲判不變量：{forbidden}")
        opinion = item.get("opinion")
        if opinion not in MACHINE_OPINIONS:
            raise ScreeningDecisionError(
                f"invalid machine opinion for {candidate_id}：{opinion!r}")
        raw = item.get("rawResponse")
        if not isinstance(raw, str) or not raw.strip():
            raise ScreeningDecisionError(
                f"機器判讀 {candidate_id} 缺 rawResponse——ADR-0009 原則 3 要求"
                "原始回應（判讀理由）逐筆落盤入雜湊鏈")

    expected, actual = set(assignment_ids), set(judgements)
    if actual != expected:
        raise ScreeningDecisionError(
            f"machine review candidate set mismatch："
            f"missing={sorted(expected - actual)[:3]} "
            f"extra={sorted(actual - expected)[:3]}")
    return judgements, judged_by


def reconcile_machine(manifest: dict, queue: list[dict], assignment: dict,
                      review_a: dict, review_b: dict, *,
                      completed_at: str | None = None) -> dict:
    """對帳兩位 LLM 審查者（ADR-0009 裁定②）；絕不自動裁決。

    沒有金標準——兩批判讀對稱。對立（advance vs exclude）與任一方 unclear
    一律進 ``ownerAuditQueue`` 等擁有者裁決；一致者只記錄 ``opinion``，
    **不轉成 decision**。機器路徑的啟用前提不變：影子門檻通過並經協調者
    放行後才用於正式篩選，故 ``machineScreeningReleased`` 恆為 False，
    由後續放行流程另行處置。
    """
    by_a, judged_a = _validate_machine_binding(manifest, queue, assignment, review_a)
    by_b, judged_b = _validate_machine_binding(manifest, queue, assignment, review_b)

    reviewer_a = review_a["reviewer"]["reviewerId"]
    reviewer_b = review_b["reviewer"]["reviewerId"]
    if reviewer_a == reviewer_b:
        raise ScreeningDecisionError("machine reviewers must be distinct")
    if review_a.get("reviewId") == review_b.get("reviewId"):
        raise ScreeningDecisionError("machine reviewIds must be distinct")
    if judged_a["modelId"] == judged_b["modelId"]:
        raise ScreeningDecisionError(
            "雙模型盲判要求兩位 reviewer 的 judgedBy.modelId 相異："
            f"{judged_a['modelId']!r}——同模型換版不算獨立模型")

    # 主／次順序不影響結果：以 reviewerId 排序取得確定性輸出。
    if reviewer_b < reviewer_a:
        review_a, review_b = review_b, review_a
        by_a, by_b = by_b, by_a
        judged_a, judged_b = judged_b, judged_a
        reviewer_a, reviewer_b = reviewer_b, reviewer_a

    concordant: list[dict[str, Any]] = []
    audit_queue: list[dict[str, Any]] = []
    opposed_ids: list[str] = []
    for candidate_id in assignment["candidateIds"]:
        a, b = by_a[candidate_id], by_b[candidate_id]
        opinions = {a["opinion"], b["opinion"]}
        if opinions == {"advance", "exclude"}:
            kind = "opposed"
            opposed_ids.append(candidate_id)
        elif "unclear" in opinions:
            kind = "either-unclear"
        elif a["opinion"] != b["opinion"]:
            kind = "divergent"
        else:
            kind = None

        if kind:
            audit_queue.append({
                "candidateId": candidate_id,
                "disagreementKind": kind,
                "modelOpinions": [
                    {"reviewerId": reviewer_a, "modelId": judged_a["modelId"],
                     "modelVersion": judged_a["modelVersion"],
                     "opinion": a["opinion"], "rawResponse": a["rawResponse"]},
                    {"reviewerId": reviewer_b, "modelId": judged_b["modelId"],
                     "modelVersion": judged_b["modelVersion"],
                     "opinion": b["opinion"], "rawResponse": b["rawResponse"]},
                ],
            })
            continue
        concordant.append({"candidateId": candidate_id, "opinion": a["opinion"]})

    counts = {
        "candidateCount": len(assignment["candidateIds"]),
        "concordantCount": len(concordant),
        "ownerAuditCount": len(audit_queue),
        "opposedCount": len(opposed_ids),
        "concordantAdvanceCount": sum(c["opinion"] == "advance" for c in concordant),
        "concordantExcludeCount": sum(c["opinion"] == "exclude" for c in concordant),
    }
    status = "needs-owner-audit" if audit_queue else "concordant"
    assignment_covers_queue = set(assignment["candidateIds"]) == {
        item["candidateId"] for item in queue}
    sources_complete = bool(manifest.get("candidateSourcesComplete"))
    screening_complete = (
        status == "concordant" and assignment_covers_queue and sources_complete)

    blockers = []
    if not sources_complete:
        blockers.append("candidate-sources-incomplete")
    if not screening_complete:
        blockers.append("machine-title-abstract-screening-not-completed")
    # 派發第 4 項：影子門檻通過並經協調者放行前，機器路徑不得用於正式篩選。
    blockers.append("machine-screening-not-released")
    blockers.append("full-text-screening-not-completed")

    if not sources_complete:
        next_stage = "candidate-source-search"
    elif audit_queue:
        next_stage = "owner-audit"
    elif not assignment_covers_queue:
        next_stage = "title-abstract-screening"
    else:
        next_stage = "machine-screening-release-review"

    doc = {
        "documentType": "title-abstract-machine-reconciliation",
        "schemaVersion": "1.0.0",
        "adr": "ADR-0009",
        "reconciliationId": f"reconcile-machine:{assignment['assignmentId']}",
        "assignmentId": assignment["assignmentId"],
        "runId": assignment["runId"],
        "screeningQueueHash": assignment["screeningQueueHash"],
        "candidateSetHash": assignment["candidateSetHash"],
        "reviewIds": sorted([review_a["reviewId"], review_b["reviewId"]]),
        "reviewerIds": sorted([reviewer_a, reviewer_b]),
        "modelIds": sorted([judged_a["modelId"], judged_b["modelId"]]),
        "judgedBy": [
            {"reviewerId": reviewer_a, **judged_a},
            {"reviewerId": reviewer_b, **judged_b},
        ],
        "evidenceGrade": "AI-graded evidence — no human expert review",
        "status": status,
        "concordant": concordant,
        "ownerAuditQueue": audit_queue,
        "opposedCandidateIds": opposed_ids,
        "counts": counts,
        "assignmentCoversQueue": assignment_covers_queue,
        "candidateSourcesComplete": sources_complete,
        "machineTitleAbstractScreeningComplete": screening_complete,
        "machineScreeningReleased": False,
        "eligibleSamplingPoolReady": False,
        "blockingReasons": blockers,
        "nextStage": next_stage,
        "completedAt": completed_at or _utc_now(),
        # 預置後由 freeze_document 覆寫為 frozen——凍結狀態在產物裡明示。
        "documentFreezeStatus": "draft",
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
