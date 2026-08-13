#!/usr/bin/env python3
"""
抽取範圍契約的確定性比對 (Gap A 的執行層)

核心：決定一個「論文報告的 outcome × timepoint × analysis set × ...」組合
是否應產生 StudyResult。此判定必須是確定性的、可重現的、可回溯到具名規則的。

模型不參與此判定。模型的職責是把論文內容登錄成 OutcomeInventory；
是否抽取由本模組依凍結的 ExtractionScopeContract 決定。
"""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Optional

from ahig.scope import inventory as inv

UNIT_TO_DAYS = {"hour": 1 / 24, "day": 1.0, "week": 7.0,
                "month": 30.4375, "year": 365.25}

EXCEEDS_MAX_REASON = ("in-scope 組合數超過上限，代表範圍契約定義過寬，"
                      "須人工複審而非自動擴張")


def canonical_hash(obj: Any) -> str:
    """JCS 風格的正規化序列化後取 SHA-256。契約凍結用。"""
    payload = json.dumps(obj, sort_keys=True, separators=(",", ":"),
                         ensure_ascii=False).encode("utf-8")
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def to_days(value: float, unit: str) -> Optional[float]:
    if unit == "session":
        return None          # session 無法換算為時間，須以 session 為單位比對
    f = UNIT_TO_DAYS.get(unit)
    return None if f is None else value * f


@dataclass
class ScopeDecision:
    in_scope: bool
    reason_code: str
    matched: dict
    rule_id: str

    def to_json(self) -> dict:
        """schema 要求五個軸一律顯性寫出，且判定者必須是確定性層。"""
        matched = {k: self.matched.get(k) for k in
                   ("outcomeId", "timepointId", "analysisSet",
                    "effectMeasure", "doseBandId")}
        return {"inScope": self.in_scope, "reasonCode": self.reason_code,
                "ruleId": self.rule_id, "matchedScopeElements": matched,
                "decidedBy": inv.decided_by()}


class ScopeMatcher:
    def __init__(self, contract: dict):
        if contract.get("status") != "frozen":
            raise ValueError("只能以 status=frozen 的範圍契約進行比對")
        self.c = contract
        self.outcomes = {o["outcomeId"]: o for o in contract["inScopeOutcomes"]}
        self.timepoints = contract["inScopeTimepoints"]
        self.analysis_sets = set(contract["inScopeAnalysisSets"])
        self.effect_measures = set(contract["inScopeEffectMeasures"])
        self.models = set(contract.get("inScopeStatisticalModels",
                                       ["unadjusted", "adjusted-prespecified"]))
        self.policy = contract["extractionPolicy"]
        self.dose_bands = (contract["researchQuestion"]["interventionOrExposure"]
                           .get("doseBands") or [])

    # -- 個別維度 ---------------------------------------------------------

    def _match_outcome(self, reported: dict) -> Optional[dict]:
        ref = reported.get("normalisedOutcomeRef")
        if ref and ref in self.outcomes:
            o = self.outcomes[ref]
            allowed = o.get("allowedInstruments") or []
            if allowed and reported.get("instrument") not in allowed:
                return None
            return o
        return None

    def _match_timepoint(self, reported_days: Optional[float],
                         reported_sessions: Optional[float]) -> list[dict]:
        hits = []
        for tp in self.timepoints:
            if tp["unit"] == "session":
                if reported_sessions is None:
                    continue
                if tp["windowStart"] <= reported_sessions <= tp["windowEnd"]:
                    hits.append(tp)
                continue
            if reported_days is None:
                continue
            lo = to_days(tp["windowStart"], tp["unit"])
            hi = to_days(tp["windowEnd"], tp["unit"])
            if lo is not None and hi is not None and lo <= reported_days <= hi:
                hits.append(tp)
        return hits

    def _match_dose(self, dose: Optional[float], unit: Optional[str]) -> Optional[str]:
        if not self.dose_bands:
            return "__no-band-constraint__"
        if dose is None:
            return None
        for b in self.dose_bands:
            if b["unit"] == unit and b["min"] <= dose <= b["max"]:
                return b["bandId"]
        return None

    # -- 主判定 -----------------------------------------------------------

    def decide(self, reported: dict) -> ScopeDecision:
        """reported 為 OutcomeInventory.reportedOutcomes 的一項，
        外加候選 StudyResult 的軸值。"""
        m: dict = {"outcomeId": None, "timepointId": None, "analysisSet": None,
                   "effectMeasure": None, "doseBandId": None}

        if not reported.get("hasNumericResult", True):
            return ScopeDecision(False, "notExtracted-no-numeric-result", m,
                                 "SCOPE-000-no-numeric-result")

        o = self._match_outcome(reported)
        if o is None:
            ref = reported.get("normalisedOutcomeRef")
            if ref in self.outcomes:
                return ScopeDecision(False, "notExtracted-instrument-not-in-allowlist",
                                     m, "SCOPE-001b-instrument")
            return ScopeDecision(False, "notExtracted-outcome-not-in-scope", m,
                                 "SCOPE-001-outcome")
        m["outcomeId"] = o["outcomeId"]

        tps = self._match_timepoint(reported.get("timepointDays"),
                                    reported.get("timepointSessions"))
        if not tps:
            return ScopeDecision(False, "notExtracted-timepoint-outside-window", m,
                                 "SCOPE-002-timepoint")
        if len(tps) > 1:
            return ScopeDecision(False, "escalated-multiple-matches-in-window", m,
                                 "SCOPE-002b-multiple-timepoint-match")
        tp = tps[0]
        # 同一時窗內若該研究有多個測量點，依契約規則處理，預設 escalate
        if reported.get("multipleMeasurementsInWindow"):
            rule = tp.get("onMultipleMatchesWithinWindow", "escalate")
            if rule == "escalate":
                return ScopeDecision(False, "escalated-multiple-matches-in-window", m,
                                     "SCOPE-002c-multiple-measurements")
        m["timepointId"] = tp["timepointId"]

        aset = reported.get("analysisSet")
        if aset not in self.analysis_sets:
            return ScopeDecision(False, "notExtracted-analysis-set-not-in-scope", m,
                                 "SCOPE-003-analysis-set")
        m["analysisSet"] = aset

        em = reported.get("effectMeasure")
        if em not in self.effect_measures:
            return ScopeDecision(False, "notExtracted-effect-measure-not-in-scope", m,
                                 "SCOPE-004-effect-measure")
        m["effectMeasure"] = em

        model = reported.get("statisticalModel", "unadjusted")
        if "any" not in self.models and model not in self.models:
            return ScopeDecision(False, "notExtracted-model-not-in-scope", m,
                                 "SCOPE-005-model")

        if reported.get("isSubgroup"):
            pol = self.policy.get("subgroupPolicy", "prespecified-only")
            listed = set(self.policy.get("listedSubgroups") or [])
            sg = reported.get("subgroupId")
            ok = (pol == "all"
                  or (pol == "prespecified-only" and reported.get("subgroupPrespecified"))
                  or (pol == "listed-only" and sg in listed))
            if not ok:
                return ScopeDecision(False, "notExtracted-subgroup-excluded-by-policy",
                                     m, "SCOPE-006-subgroup")

        if reported.get("isSensitivityAnalysis"):
            pol = self.policy.get("sensitivityAnalysisPolicy", "exclude")
            if pol == "exclude":
                return ScopeDecision(
                    False, "notExtracted-sensitivity-analysis-excluded-by-policy",
                    m, "SCOPE-007-sensitivity")
            if pol == "extract-if-primary-fails-rob" and not reported.get(
                    "primaryAnalysisFailedRoB"):
                return ScopeDecision(
                    False, "notExtracted-sensitivity-analysis-excluded-by-policy",
                    m, "SCOPE-007b-sensitivity-conditional")

        band = self._match_dose(reported.get("dose"), reported.get("doseUnit"))
        if band is None:
            return ScopeDecision(False, "notExtracted-dose-outside-bands", m,
                                 "SCOPE-008-dose")
        m["doseBandId"] = None if band == "__no-band-constraint__" else band

        return ScopeDecision(True, "in-scope", m, "SCOPE-999-in-scope")

    # -- 批次 -------------------------------------------------------------

    def decide_inventory(self, inventory: dict) -> dict:
        """對整份 OutcomeInventory 判定，並強制 maxStudyResultsPerStudy 上限。"""
        results, in_scope = [], 0
        for r in inventory["reportedOutcomes"]:
            d = self.decide(r)
            results.append({"localLabel": r.get("localLabel"), **d.to_json()})
            if d.in_scope:
                in_scope += 1

        cap = self.policy.get("maxStudyResultsPerStudy", 12)
        exceeded = in_scope > cap
        if exceeded and self.policy.get("onExceedMax", "escalate") == "escalate":
            for r in results:
                if r["inScope"]:
                    r["inScope"] = False
                    r["reasonCode"] = "escalated-exceeds-max-studyresults"
                    r["ruleId"] = "SCOPE-100-exceeds-max"

        return {
            "inventoryId": inventory.get("inventoryId"),
            "scopeContractHash": self.c.get("scopeContractHash"),
            "decisions": results,
            "inScopeCount": 0 if exceeded else in_scope,
            "candidateCount": in_scope,
            "maxStudyResultsPerStudy": cap,
            "escalated": exceeded,
            "escalationReason": (EXCEEDS_MAX_REASON if exceeded else None),
        }

    # -- lifecycle：draft -> scoped ---------------------------------------

    def scope_inventory(self, draft: dict, *, now: Optional[str] = None) -> dict:
        """把 lifecycle=draft 的 OutcomeInventory 升級為 lifecycle=scoped。

        回傳新文件，**不就地修改 draft** —— draft 必須保持可複驗，
        才能在範圍契約升版後重跑判定並比對差異。

        輸出直接符合 outcome-inventory schema 的 scoped 分支：
        每一項都帶具名 ruleId、五個顯性軸與 deterministic 判定者，
        再加上頂層的 scopeDecisionSummary 與 scopedAt。
        """
        inv.assert_scopable(draft, self.c.get("scopeContractHash"))

        scoped = copy.deepcopy(draft)
        scoped["lifecycle"] = inv.SCOPED

        decisions = [self.decide(r) for r in draft["reportedOutcomes"]]
        in_scope = sum(1 for d in decisions if d.in_scope)

        cap = self.policy.get("maxStudyResultsPerStudy", 12)
        exceeded = (in_scope > cap
                    and self.policy.get("onExceedMax", "escalate") == "escalate")

        for item, d in zip(scoped["reportedOutcomes"], decisions):
            payload = d.to_json()
            if exceeded:
                # 超過上限一律 escalate：不截斷、不自動擴張，
                # 且不得留下任何 inScope=true 讓下游誤以為可以抽取。
                payload["inScope"] = False
                payload["reasonCode"] = "escalated-exceeds-max-studyresults"
                payload["ruleId"] = "SCOPE-100-exceeds-max"
            item["scopeDecision"] = payload

        scoped["scopeDecisionSummary"] = {
            "candidateCount": in_scope,
            "inScopeCount": 0 if exceeded else in_scope,
            "maxStudyResultsPerStudy": cap,
            "escalated": exceeded,
            "escalationReason": (EXCEEDS_MAX_REASON if exceeded else None),
        }
        scoped["scopedAt"] = now or datetime.now(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        return scoped


def backfill_candidates(inventory: dict, old: "ScopeMatcher",
                        new: "ScopeMatcher") -> list[dict]:
    """範圍契約版本升級後，從既有 OutcomeInventory 找出新進範圍的組合。
    這是不重讀論文即可補抽的關鍵 —— OutcomeInventory 的存在理由之一。"""
    out = []
    for r in inventory["reportedOutcomes"]:
        was, now = old.decide(r), new.decide(r)
        if now.in_scope and not was.in_scope:
            out.append({"localLabel": r.get("localLabel"),
                        "previousReason": was.reason_code,
                        "nowMatched": now.matched})
    return out
