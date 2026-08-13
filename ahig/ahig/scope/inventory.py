#!/usr/bin/env python3
"""
OutcomeInventory 的 lifecycle 與完整性稽核

兩個 lifecycle 狀態：

- ``draft``：模型或人工完整登錄論文報告了什麼。**不含任何範圍判定。**
- ``scoped``：由確定性 ScopeMatcher 逐項加上具名規則的 scopeDecision。

分界的理由：範圍判定若能由模型填寫，範圍契約就形同虛設 —— 模型可以宣稱任何東西
out-of-scope 而無人可查。因此 draft 帶著 scopeDecision 一律視為污染，不得升級。

本模組只負責 lifecycle 常數、升級前的前置檢查與 harms 掃描對帳；
實際的軸比對邏輯在 ``ahig.scope.matcher``。
"""

from __future__ import annotations

from typing import Any

DRAFT = "draft"
SCOPED = "scoped"
LIFECYCLES = (DRAFT, SCOPED)

#: 寫入每一筆 scopeDecision.decidedBy。規則語意變更時必須同步升版，
#: 否則已 scoped 的清單無法分辨自己是由哪一版規則判定的。
MATCHER_VERSION = "scope-matcher/2.0.0"

DETERMINISTIC = "deterministic"

#: draft 專屬（升級後由 scoped 補上）的頂層欄位。
SCOPED_ONLY_FIELDS = ("scopedAt", "scopeDecisionSummary")


class InventoryLifecycleError(ValueError):
    """draft → scoped 升級的前置條件不成立。"""


def lifecycle_of(inventory: dict) -> str:
    lc = inventory.get("lifecycle")
    if lc not in LIFECYCLES:
        raise InventoryLifecycleError(
            f"lifecycle 必須是 {LIFECYCLES} 之一，實得 {lc!r}")
    return lc


def is_draft(inventory: dict) -> bool:
    return inventory.get("lifecycle") == DRAFT


def is_scoped(inventory: dict) -> bool:
    return inventory.get("lifecycle") == SCOPED


def decided_by() -> dict[str, str]:
    """每一筆 scopeDecision 的判定者。範圍判定只能由確定性層做出。"""
    return {"agentClass": DETERMINISTIC, "matcherVersion": MATCHER_VERSION}


def assert_scopable(inventory: dict, contract_hash: str | None = None) -> None:
    """升級為 scoped 之前的守門。任一條不成立即拒絕，不做靜默修補。

    contract_hash 有值時，必須與 draft 記錄的 scopeContractHash 相符 ——
    以 A 契約登錄、用 B 契約判定，會讓 notExtracted 標記失去意義。
    """
    lc = lifecycle_of(inventory)
    if lc != DRAFT:
        raise InventoryLifecycleError(
            f"只能升級 lifecycle={DRAFT} 的清單，實得 {lc!r}；"
            "已 scoped 的清單要重判必須回到 draft 或建立新版本")

    outcomes = inventory.get("reportedOutcomes")
    if not isinstance(outcomes, list) or not outcomes:
        raise InventoryLifecycleError(
            "reportedOutcomes 不得為空；空清單無法支撐任何 notExtracted 標記")

    for field in SCOPED_ONLY_FIELDS:
        if field in inventory:
            raise InventoryLifecycleError(
                f"draft 不得攜帶 {field}；該欄位由確定性層產生")

    polluted = [i for i, o in enumerate(outcomes) if "scopeDecision" in o]
    if polluted:
        raise InventoryLifecycleError(
            f"draft 的第 {polluted} 項已帶 scopeDecision；"
            "範圍判定不得由登錄端填寫，否則範圍契約形同虛設")

    if contract_hash is not None:
        got = inventory.get("scopeContractHash")
        if got != contract_hash:
            raise InventoryLifecycleError(
                f"契約 hash 不符：清單為 {got!r}，比對器為 {contract_hash!r}")


def audit_harms_scan(inventory: dict) -> list[dict[str, Any]]:
    """harms / safety 掃描的可稽核性對帳。

    schema 擋得住「宣稱找到 harm 卻沒有任何 safety 條目」，但擋不住數量不符 ——
    JSON Schema 無法把 contains 的命中數與另一個欄位的整數相比。此處補上。

    回傳具名發現清單；空清單代表一致。
    """
    findings: list[dict[str, Any]] = []
    att = inventory.get("completenessAttestation") or {}
    scan = att.get("harmsScan")
    if not scan:
        findings.append({
            "code": "harms-scan-missing",
            "message": "缺少 harmsScan；無法主張 safety outcome 未被遺漏",
        })
        return findings

    outcomes = inventory.get("reportedOutcomes") or []
    actual = sum(1 for o in outcomes if o.get("outcomeRoleAsStated") == "safety")
    declared = scan.get("harmOutcomesFound")

    if declared != actual:
        findings.append({
            "code": "harms-count-mismatch",
            "message": (f"harmsScan 宣告 {declared} 項 harm，"
                        f"但清單中 outcomeRoleAsStated=safety 者有 {actual} 項"),
            "declared": declared,
            "actual": actual,
        })

    statement = scan.get("harmsReportingStatement")
    if statement == "harms-reported" and actual == 0:
        findings.append({
            "code": "harms-statement-unsupported",
            "message": "宣稱論文報告了 harm，但清單中沒有任何 safety 條目",
        })
    if statement in ("explicit-none-reported", "not-mentioned") and actual > 0:
        findings.append({
            "code": "harms-statement-contradicted",
            "message": (f"宣稱論文未報告 harm（{statement}），"
                        f"但清單中有 {actual} 項 safety 條目"),
        })

    scanned = scan.get("sectionsScanned") or []
    if not scanned:
        findings.append({
            "code": "harms-scan-sections-empty",
            "message": "未記錄掃描了哪些章節；harms 掃描不可稽核",
        })

    return findings


def audit_registry_comparison(inventory: dict) -> list[dict[str, Any]]:
    """registry 比對與雙審條件的對帳。與 schema 條件同義，供程式流程早期攔截。"""
    findings: list[dict[str, Any]] = []
    rc = inventory.get("registryComparison") or {}
    status = rc.get("status")

    if status == "compared":
        for field in ("registryId", "registryRetrievedAt",
                      "registryPrimaryOutcomes", "outcomeSwitchingFlags"):
            if rc.get(field) in (None, ...) or field not in rc:
                findings.append({
                    "code": "registry-comparison-incomplete",
                    "message": f"status=compared 但缺少 {field}",
                    "field": field,
                })

    if rc.get("outcomeSwitchingFlags"):
        if (inventory.get("createdBy") or {}).get("dualExtracted") is not True:
            findings.append({
                "code": "switching-flag-requires-dual-extraction",
                "message": ("偵測到 outcome switching flag，"
                            "本清單必須雙重抽取（dualExtracted=true）"),
                "flags": list(rc["outcomeSwitchingFlags"]),
            })
    return findings


def audit(inventory: dict) -> list[dict[str, Any]]:
    """全部可稽核性檢查。回傳具名發現清單，不拋例外。"""
    return audit_harms_scan(inventory) + audit_registry_comparison(inventory)
