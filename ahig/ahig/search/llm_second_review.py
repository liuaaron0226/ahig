#!/usr/bin/env python3
"""ADR-0007：盲化 LLM 第二審的產物管理。

本模組不呼叫任何 LLM——它管理證據：把 LLM 的第二意見固化成可稽核批次
（prompt、模型版本、原始回應全部落盤、雜湊入鏈）、執行影子模式門檻、
產出「哪些紀錄需要第二位人類裁決」的計畫。

不變量（與 ADR-0007 一致）：

- 人仍篩完每一篇；LLM 意見永遠只是意見，每個 include/exclude 由人類簽名。
- LLM 必須盲於人類判定：意見批次結構性禁止攜帶人類決策欄位。
- 影子門檻：LLM 對任一人類 include 的漏報必須為 0，否則不得切換模式。
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

from ahig.contracts.freeze import content_hash

OPINIONS = ("advance", "exclude", "unclear")
# 影子批次的歧異率上限。預設值為佔位參數，正式值由影子批次校準後凍結。
DEFAULT_MAX_DISAGREEMENT_RATE = 0.25
# 盲化結構檢查：意見條目不得攜帶任何人類決策欄位。
_FORBIDDEN_ENTRY_KEYS = frozenset({
    "humanDecision", "decision", "reviewerDecision", "reconciledDecision"})


class LlmReviewError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_opinion_batch(queue_manifest: dict, queue: list[dict],
                        opinions: list[dict], *, model_id: str,
                        model_version: str, prompt_template: str) -> dict:
    """把一批 LLM 第二意見固化成可稽核文件。

    ``opinions`` 每筆：{candidateId, opinion, rawResponse}。批次綁定
    screeningQueueHash 與 prompt 範本雜湊；prompt 修改視同換版，必須重跑
    影子批次（ADR-0007）。
    """
    queue_ids = {e["candidateId"] for e in queue}
    problems = []
    seen: set[str] = set()
    entries = []
    for i, raw in enumerate(opinions):
        forbidden = _FORBIDDEN_ENTRY_KEYS & set(raw)
        if forbidden:
            problems.append(f"opinions[{i}] 帶有人類決策欄位 {sorted(forbidden)}"
                            "——LLM 必須盲於人類判定")
            continue
        cid = raw.get("candidateId")
        if cid not in queue_ids:
            problems.append(f"opinions[{i}] 的 candidateId 不在 queue：{cid}")
            continue
        if cid in seen:
            problems.append(f"opinions[{i}] 重複 candidateId：{cid}")
            continue
        seen.add(cid)
        opinion = raw.get("opinion")
        if opinion not in OPINIONS:
            problems.append(f"opinions[{i}] {cid}: opinion 必須是 {OPINIONS}")
            continue
        response = raw.get("rawResponse")
        if not (isinstance(response, str) and response.strip()):
            problems.append(f"opinions[{i}] {cid}: 必須保留原始回應全文")
            continue
        entries.append({
            "candidateId": cid,
            "opinion": opinion,
            "rawResponse": response,
            "respondedAt": raw.get("respondedAt") or _utc_now(),
        })
    if problems:
        raise LlmReviewError("LLM 意見批次無效：\n" + "\n".join(problems))
    if not entries:
        raise LlmReviewError("LLM 意見批次是空的")
    batch = {
        "documentType": "llm-second-review-batch",
        "schemaVersion": "1.0.0",
        "adr": "ADR-0007",
        "screeningQueueHash": queue_manifest["screeningQueueHash"],
        "runId": queue_manifest["runId"],
        "model": {"id": model_id, "version": model_version},
        "promptTemplate": prompt_template,
        "promptTemplateSha256": hashlib.sha256(
            prompt_template.encode("utf-8")).hexdigest(),
        "blindedToHumanDecisions": True,
        "opinionCount": len(entries),
        "entries": sorted(entries, key=lambda e: e["candidateId"]),
        "createdAt": _utc_now(),
    }
    batch["llmReviewHash"] = content_hash(
        {key: batch[key] for key in
         ("screeningQueueHash", "model", "promptTemplateSha256", "entries")})
    return batch


def _opinion_map(batch: dict) -> dict[str, str]:
    return {e["candidateId"]: e["opinion"] for e in batch["entries"]}


def shadow_gate(human_decisions: dict[str, str], batch: dict, *,
                max_disagreement_rate: float = DEFAULT_MAX_DISAGREEMENT_RATE
                ) -> dict:
    """影子模式門檻（ADR-0007 條件 4）。

    ``human_decisions``：影子批次中「雙人裁決後」的人類決定
    {candidateId: advance/exclude/unclear}。門檻：

    - LLM 對任一人類 advance 的漏報（LLM 判 exclude）必須為 0；
    - 歧異率不得超過上限（unclear 一律算歧異——它們都要進人工裁決）。

    不通過 → 不得切換為「單人＋LLM」，退回純人類雙盲。
    """
    opinions = _opinion_map(batch)
    missing = sorted(set(human_decisions) - set(opinions))
    if missing:
        raise LlmReviewError(
            f"影子批次要求 LLM 覆蓋全部紀錄，缺 {missing[:3]}")
    missed_includes = sorted(
        cid for cid, decision in human_decisions.items()
        if decision == "advance" and opinions[cid] == "exclude")
    disagreements = sorted(
        cid for cid, decision in human_decisions.items()
        if opinions[cid] != decision or opinions[cid] == "unclear"
        or decision == "unclear")
    rate = len(disagreements) / len(human_decisions) if human_decisions else 1.0
    passed = not missed_includes and rate <= max_disagreement_rate
    return {
        "documentType": "llm-shadow-gate-report",
        "adr": "ADR-0007",
        "llmReviewHash": batch["llmReviewHash"],
        "shadowSampleSize": len(human_decisions),
        "missedIncludeCandidateIds": missed_includes,
        "disagreementCandidateIds": disagreements,
        "disagreementRate": rate,
        "maxDisagreementRate": max_disagreement_rate,
        "verdict": "pass" if passed else "fail",
        "consequence": ("允許後續批次切換為「單人＋盲化 LLM」"
                        if passed else
                        "不得切換：維持純人類雙盲（ADR-0007 自動失效條款）"),
        "evaluatedAt": _utc_now(),
    }


def adjudication_plan(single_human_decisions: dict[str, str],
                      batch: dict) -> dict:
    """人＋LLM 模式的裁決計畫：歧異或任一方 unclear → 第二位人類。

    輸出只指出「誰需要第二位人類」；不含任何自動決定。
    """
    opinions = _opinion_map(batch)
    missing = sorted(set(single_human_decisions) - set(opinions))
    if missing:
        raise LlmReviewError(
            f"有人類已篩、LLM 未出意見的紀錄：{missing[:3]}——第二審必須"
            "覆蓋每一篇")
    needs_second_human = []
    agreed = []
    for cid, decision in sorted(single_human_decisions.items()):
        opinion = opinions[cid]
        if decision == opinion and decision != "unclear":
            agreed.append({"candidateId": cid, "decision": decision,
                           "llmOpinion": opinion})
        else:
            needs_second_human.append({
                "candidateId": cid, "humanDecision": decision,
                "llmOpinion": opinion,
                "reason": ("either-unclear"
                           if "unclear" in (decision, opinion)
                           else "disagreement")})
    return {
        "documentType": "llm-adjudication-plan",
        "adr": "ADR-0007",
        "llmReviewHash": batch["llmReviewHash"],
        "agreedCount": len(agreed),
        "needsSecondHumanCount": len(needs_second_human),
        "needsSecondHuman": needs_second_human,
        "agreed": agreed,
        "note": "agreed 也仍是人類簽名的決定；LLM 意見從不自動生效。",
        "createdAt": _utc_now(),
    }
