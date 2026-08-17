#!/usr/bin/env python3
"""ADR-0008：篩選的統計終止（statistical termination ≠ 排除）。

以精確超幾何檢定（BUSCAR 式，Callaghan & Müller-Hansen 2020）檢定
H0：recall < 目標。p < α 才允許終止；證據不足時的預設是繼續篩。

視窗選擇採保守變體：只檢定「自最後一篇 include 之後的連續非相關尾段」。
這是單一視窗、無多重比較問題，且嚴格保守（多視窗取 min 只會更快停）。

不變量（與 ADR-0008 一致）：

- 機器不對任何單篇做決定；終止是對「整批剩餘」的涵蓋宣稱，附統計證據。
- 終止前置：safety-review lane 與 critical-harms-signal 紀錄全數人工篩畢。
- 尾端標記 not-screened（不是 excluded），永久可抽查；抽驗出現任何
  include 即恢復篩選。
- unclear 一律當作相關計算——把不確定往「更難停」的方向算。
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timezone
from fractions import Fraction

from scipy import stats

from ahig.contracts.freeze import content_hash

DEFAULT_ALPHA = 0.05
DEFAULT_TARGET_RECALL = 0.95
DEFAULT_TAIL_SPOT_CHECK_N = 200
# advance 與 unclear 都算相關：unclear 尚未排除，保守側處理。
_RELEVANT_DECISIONS = frozenset({"advance", "unclear"})
_DECISIONS = frozenset({"advance", "exclude", "unclear"})


class TerminationError(ValueError):
    pass


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def p_score(labels_in_order: list[int], n_total: int, *,
            target_recall: float = DEFAULT_TARGET_RECALL) -> dict:
    """檢定 H0：recall < target_recall 的 p 值（保守單視窗變體）。

    ``labels_in_order``：依實際篩選順序的 0/1 標籤（1=相關）。
    ``n_total``：整個候選池大小（含未篩）。

    H0 成立所需的最小總相關數 k_target = floor(rho / target) + 1；
    檢定視窗為最後一篇相關之後的連續 0 尾段（rho=0 時為全部已篩）。
    在 H0 下，視窗起點時剩餘池至少還有 k_target - rho 篇相關；
    p = P(視窗抽 n_z 篇全為不相關 | 超幾何)。
    """
    if not 0 < target_recall < 1:
        raise TerminationError(f"target_recall 必須在 (0,1)：{target_recall}")
    n_seen = len(labels_in_order)
    if n_seen == 0:
        return {"pScore": 1.0, "relevantFound": 0, "screenedCount": 0,
                "windowSize": 0, "note": "尚未篩選，無證據"}
    if n_seen > n_total:
        raise TerminationError("已篩數量超過池子大小")
    if any(label not in (0, 1) for label in labels_in_order):
        raise TerminationError("labels 只能是 0/1")
    rho = sum(labels_in_order)
    # H0 成立所需的最小總相關數：最小整數 K 使 rho/K < target。
    # 用精確十進位分數運算——浮點除法在 rho/target 恰為整數的邊界會反保守
    # （Fraction(str(x)) 取的是使用者寫的十進位意圖，非二進位近似）。
    tau = Fraction(str(target_recall))
    k_target = (rho * tau.denominator) // tau.numerator + 1
    if rho:
        last_relevant = max(i for i, v in enumerate(labels_in_order) if v)
        window = n_seen - last_relevant - 1
    else:
        window = n_seen
    k_remaining_min = k_target - rho  # H0 下視窗起點剩餘池的最少相關數
    n_start = n_total - (n_seen - window)
    if window == 0:
        p = 1.0  # 最後一篇就是相關：對「尾段乾了」毫無證據
    elif k_remaining_min > n_start:
        p = 0.0  # H0 需要的相關數比剩餘池還多：H0 不可能
    else:
        p = float(stats.hypergeom.cdf(0, n_start, k_remaining_min, window))
    return {"pScore": p, "relevantFound": rho, "screenedCount": n_seen,
            "poolSize": n_total, "targetRecall": target_recall,
            "h0MinTotalRelevant": k_target, "windowSize": window}


def evaluate_termination(queue: list[dict],
                         decisions_in_order: list[tuple[str, str]], *,
                         alpha: float = DEFAULT_ALPHA,
                         target_recall: float = DEFAULT_TARGET_RECALL,
                         p_score_excluded: set[str] | None = None) -> dict:
    """依 ADR-0008 評估是否允許統計終止，輸出可凍結的證據產物。

    ``decisions_in_order``：[(candidateId, decision)]，依實際篩選順序；
    decision ∈ advance/exclude/unclear。

    ``p_score_excluded``：**顯式** candidateId 集合，這些紀錄已人工篩畢
    （計入前置條件、不算 not-screened），但**暫不進入 p 值 labels 序列**。
    用於協調者第 n+40 輪裁定之選項（丙）：為解除前置條件而跳頁補判的紀錄，
    若直接接進序列，會把相距上百頁的紀錄接在一起而破壞 ``windowSize``
    （尾端連續無命中長度）的語意。ADR-0008 的兩個條件本就獨立——
    ``preconditions_met`` 立即推進，``pScore`` 序列零擾動。

    這是**暫時**狀態：逐頁推進到該紀錄所在頁時，呼叫端把它移出集合，
    它便依原本的工作單順序進入序列（見 ``.scratch/term.py``）。
    集合為顯式 id 而非規則推導，落盤留痕，M1 稽核可逐筆覆核。
    """
    queue_by_id = {e["candidateId"]: e for e in queue}
    excluded = set(p_score_excluded or ())
    unknown = sorted(excluded - set(queue_by_id))
    if unknown:
        raise TerminationError(f"p 值排除清單的 candidateId 不在 queue：{unknown[:3]}")
    seen: set[str] = set()
    labels = []
    excluded_seen: set[str] = set()
    for cid, decision in decisions_in_order:
        if cid not in queue_by_id:
            raise TerminationError(f"決策的 candidateId 不在 queue：{cid}")
        if cid in seen:
            raise TerminationError(f"重複的篩選決策：{cid}")
        if decision not in _DECISIONS:
            raise TerminationError(f"{cid}: decision 必須是 "
                                   f"{sorted(_DECISIONS)}")
        seen.add(cid)
        if cid in excluded:
            # 已篩畢（計入前置條件、非 not-screened），但不進 labels 序列。
            excluded_seen.add(cid)
            continue
        labels.append(1 if decision in _RELEVANT_DECISIONS else 0)

    never_screened = sorted(excluded - excluded_seen)
    if never_screened:
        raise TerminationError(
            f"p 值排除清單含未篩畢紀錄（排除只適用已判讀者）：{never_screened[:3]}")

    # 前置條件：safety 與 critical harms 全數人工篩畢（ADR-0008 條件 2）。
    mandatory_unscreened = sorted(
        e["candidateId"] for e in queue
        if e["candidateId"] not in seen
        and (e.get("screeningLane") == "safety-review"
             or "critical-harms-signal" in (e.get("flags") or [])))

    not_screened = sorted(cid for cid in queue_by_id if cid not in seen)
    score = p_score(labels, len(queue), target_recall=target_recall)
    preconditions_met = not mandatory_unscreened
    # 排除清單非空時不得終止：p 值序列尚未涵蓋全部已篩紀錄，
    # 此時的統計證據是「部分序列」的，不足以支撐涵蓋宣稱。
    pending_reintegration = sorted(excluded_seen)
    allowed = (preconditions_met and not pending_reintegration
               and score["pScore"] < alpha)
    result = {
        "documentType": "statistical-termination-evaluation",
        "schemaVersion": "1.1.0",
        "adr": "ADR-0008",
        "alpha": alpha,
        **score,
        "notScreenedCount": len(not_screened),
        "notScreenedStatus": "not-screened",
        "notScreenedIsNotExcluded": True,
        "mandatoryLanesFullyScreened": preconditions_met,
        "mandatoryUnscreenedCandidateIds": mandatory_unscreened[:10],
        "pScoreExcludedCount": len(pending_reintegration),
        "pScoreExcludedCandidateIds": pending_reintegration,
        "pScoreExcludedIsScreened": True,
        "allowedToStop": allowed,
        "reason": (
            "p < α 且安全/critical-harms 全數人工篩畢；允許終止，"
            "剩餘標記 not-screened，須完成尾端抽驗（ADR-0008 條件 4）"
            if allowed else
            f"safety/critical-harms 尚有 {len(mandatory_unscreened)} 篇"
            "未人工篩畢；不得終止" if not preconditions_met else
            f"尚有 {len(pending_reintegration)} 篇跳頁補判紀錄未納回 p 值序列"
            "（第 n+40 輪選項丙）；不得終止" if pending_reintegration else
            "統計證據不足（p ≥ α）；預設繼續篩選"),
        "evaluatedAt": _utc_now(),
    }
    result["terminationEvidenceHash"] = content_hash(
        {key: result[key] for key in
         ("alpha", "pScore", "relevantFound", "screenedCount", "poolSize",
          "targetRecall", "windowSize", "notScreenedCount",
          "mandatoryLanesFullyScreened", "pScoreExcludedCount",
          "allowedToStop")})
    return result


def draw_tail_spot_check(not_screened_ids: list[str], *,
                         queue_hash: str,
                         n: int = DEFAULT_TAIL_SPOT_CHECK_N) -> dict:
    """從 not-screened 尾端確定性抽出人工抽驗樣本（ADR-0008 條件 4）。

    seed 從 queue hash 導出（同 ADR 系列的種子導出制），無從挑選。
    """
    if not not_screened_ids:
        raise TerminationError("沒有 not-screened 紀錄，無需抽驗")
    seed = int.from_bytes(hashlib.sha256(
        f"tail-spot-check\n{queue_hash}".encode("utf-8")).digest()[:8], "big")
    ordered = sorted(not_screened_ids)
    sampled = random.Random(seed).sample(ordered, min(n, len(ordered)))
    return {
        "documentType": "tail-spot-check-sample",
        "adr": "ADR-0008",
        "screeningQueueHash": queue_hash,
        "seed": seed,
        "seedDerivation": "derived-from-queue-hash",
        "notScreenedCount": len(ordered),
        "sampleSize": len(sampled),
        "candidateIds": sampled,
        # 由人工回填：{candidateId: advance/exclude/unclear}
        "decisions": None,
        "drawnAt": _utc_now(),
    }


def evaluate_tail_spot_check(sample: dict,
                             decisions: dict[str, str]) -> dict:
    """抽驗判定：出現任何 include（advance）→ 恢復篩選。unclear 同樣恢復
    ——不確定不能當作乾淨。"""
    missing = sorted(set(sample["candidateIds"]) - set(decisions))
    if missing:
        raise TerminationError(f"抽驗未完成，缺 {missing[:3]}")
    bad = sorted(cid for cid in sample["candidateIds"]
                 if decisions[cid] not in _DECISIONS)
    if bad:
        raise TerminationError(f"抽驗決策詞彙不合法：{bad[:3]}")
    hits = sorted(cid for cid in sample["candidateIds"]
                  if decisions[cid] in _RELEVANT_DECISIONS)
    return {
        "documentType": "tail-spot-check-result",
        "adr": "ADR-0008",
        "screeningQueueHash": sample["screeningQueueHash"],
        "sampleSize": sample["sampleSize"],
        "relevantOrUnclearFound": hits,
        "resumeScreening": bool(hits),
        "verdict": ("尾端抽驗發現相關或 unclear 紀錄：終止失效，恢復篩選"
                    if hits else
                    "尾端抽驗通過：終止維持，not-screened 保留可抽查"),
        "evaluatedAt": _utc_now(),
    }
