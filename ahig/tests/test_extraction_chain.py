"""萃取鏈的接合處：sections → draft → scoped → 稽核。

不測各段內部（各自已有測試），只測**接起來會不會散**：
每一段交出的形狀，下一段收不收得下。
接上模型之前先證明這件事，接上之後才分得出「是模型的問題」還是「是接線的問題」。
"""
from __future__ import annotations

import pytest

from ahig.extraction import build_reading_request, validate_draft, draft_to_scoped
from ahig.scope import inventory as inv

SHA_A = "sha256:" + "a" * 64
SHA_C = "sha256:" + "c" * 64

CONTRACT = {
    "status": "frozen",
    "scopeContractHash": SHA_C,
    "inScopeOutcomes": [
        {"outcomeId": "ffm-change", "label": "去脂體重變化", "role": "critical",
         "quantityKind": "qk:ffm",
         "comparabilityClass": "body-composition-multi-compartment"}],
    "inScopeTimepoints": [
        {"timepointId": "end", "label": "介入結束", "windowStart": 4,
         "windowEnd": 104, "unit": "week"}],
    "researchQuestion": {
        "questionType": "efficacy",
        "population": {"label": "赤字期成人"},
        "interventionOrExposure": {"label": "較高蛋白質", "doseBands": [
            {"bandId": "high", "min": 1.6, "max": 2.39, "unit": "g/kg/day"}]},
        "comparator": {"types": ["dose-comparison"]}},
    "inScopeAnalysisSets": ["ITT"],
    "inScopeEffectMeasures": ["MD"],
    "extractionPolicy": {
        "subgroupPolicy": "prespecified-only",
        "sensitivityAnalysisPolicy": "exclude",
        "adjustedModelPolicy": "primary-model-only",
        "onOutOfScope": "record-in-outcome-inventory-only",
        "maxStudyResultsPerStudy": 16},
}

SECTIONS_DOC = {
    "documentType": "fulltext-sections",
    "contentSha256": SHA_A,
    "content": "Methods... Results...",
    "sections": [{"title": "Methods", "path": ["Methods"], "text": "m"},
                 {"title": "Results", "path": ["Results"], "text": "r"}],
}


def _stub_draft(req, outcomes):
    """替代讀論文那一端。**只造形狀，不造判定**——判定是下一段的事。"""
    return {
        "inventoryId": "inv:chain",
        "report": req.report,
        "manifestation": req.manifestation,
        "scopeContractHash": req.scope_contract_hash,
        "lifecycle": "draft",
        "reportedOutcomes": outcomes,
        "registryComparison": {"status": "pending"},
        "createdBy": {"agentClass": "model", "modelVersion": "stub"},
        "completenessAttestation": {
            "sectionsScanned": req.section_titles,
            "supplementaryScanned": False,
            "harmsScan": {"performed": True},
            "attestedBy": {"agentClass": "model"}},
    }


def _chain(outcomes):
    req = build_reading_request(SECTIONS_DOC, CONTRACT, report="rep:chain")
    draft = validate_draft(_stub_draft(req, outcomes), req)
    return draft_to_scoped(draft, CONTRACT)


def test_chain_holds_and_every_item_gets_a_named_decision():
    scoped = _chain([
        {"localLabel": "fat-free mass", "normalisedOutcomeRef": "ffm-change",
         "sourceLocation": {"section": "Results"}},
    ])
    assert scoped["lifecycle"] == "scoped"
    assert inv.is_scoped(scoped)
    d = scoped["reportedOutcomes"][0]["scopeDecision"]
    assert d.get("ruleId"), "判定必須具名——沒有規則編號就無法回溯它為什麼這樣判"
    assert d.get("reasonCode"), "判定必須帶理由碼"


def test_missing_timepoint_falls_out_of_scope_rather_than_being_assumed():
    """沒報時間點時，判定為範圍外並具名，🚫 不猜一個時間點讓它落進窗內。"""
    scoped = _chain([
        {"localLabel": "fat-free mass", "normalisedOutcomeRef": "ffm-change",
         "sourceLocation": {"section": "Results"}}])
    d = scoped["reportedOutcomes"][0]["scopeDecision"]
    assert d["inScope"] is False
    assert "timepoint" in d["ruleId"]


def test_out_of_scope_outcome_is_kept_not_dropped():
    """範圍外者留在清冊裡，否則 outcome-switching 偵測與日後 backfill 失去依據。"""
    scoped = _chain([
        {"localLabel": "fat-free mass", "normalisedOutcomeRef": "ffm-change",
         "sourceLocation": {"section": "Results"}},
        {"localLabel": "mood questionnaire", "normalisedOutcomeRef": "mood",
         "sourceLocation": {"section": "Results"}},
    ])
    labels = [o["localLabel"] for o in scoped["reportedOutcomes"]]
    assert "mood questionnaire" in labels, "範圍外者被丟掉了——那等於它從未被報告過"
    assert len(scoped["reportedOutcomes"]) == 2


def test_scoped_output_passes_the_existing_lifecycle_audit():
    """交給既有稽核層，確認形狀是它收得下的。"""
    scoped = _chain([
        {"localLabel": "fat-free mass", "normalisedOutcomeRef": "ffm-change",
         "sourceLocation": {"section": "Results"}}])
    assert inv.lifecycle_of(scoped) == "scoped"
    # 已 scoped 者不得再被當成可 scope 的輸入。
    with pytest.raises(Exception):
        inv.assert_scopable(scoped, SHA_C)


def test_a_stub_that_returns_nothing_breaks_the_chain_loudly():
    """接上模型後若它什麼都沒讀到，鏈必須斷在這裡，🚫 不得產出空的 scoped 清冊。"""
    with pytest.raises(Exception):
        _chain([])
