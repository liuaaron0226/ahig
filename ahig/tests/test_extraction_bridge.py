"""萃取橋接：sections → draft → scoped。

每一條測的是一種**會安靜過去**的壞法，不是一般路徑。
"""
from __future__ import annotations

import json
import pytest

from ahig.extraction import (
    DraftRequest,
    ReadingSeamNotImplemented,
    build_reading_request,
    validate_draft,
    draft_to_scoped,
)
from ahig.extraction.inventory_draft import DraftRejected, read_sections

SHA_A = "sha256:" + "a" * 64
SHA_C = "sha256:" + "c" * 64


def _sections_doc(**over):
    doc = {
        "documentType": "fulltext-sections",
        "contentSha256": SHA_A,
        "content": "Methods ... Results ...",
        "sections": [{"title": "Methods", "path": ["Methods"], "text": "m"},
                     {"title": "Results", "path": ["Results"], "text": "r"}],
    }
    doc.update(over)
    return doc


def _contract(**over):
    c = {
        "status": "frozen",
        "scopeContractHash": SHA_C,
        "inScopeOutcomes": [
            {"outcomeId": "ffm-change", "label": "去脂體重變化",
             "role": "critical", "quantityKind": "qk:ffm",
             "comparabilityClass": "body-composition-multi-compartment"},
        ],
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
    c.update(over)
    return c


def _draft(req, **over):
    d = {
        "inventoryId": "inv:1",
        "report": req.report,
        "manifestation": req.manifestation,
        "scopeContractHash": req.scope_contract_hash,
        "lifecycle": "draft",
        "reportedOutcomes": [
            {"localLabel": "fat-free mass", "sourceLocation": {"section": "Results"}},
        ],
        "registryComparison": {"status": "pending"},
        "createdBy": {"agentClass": "model"},
        "completenessAttestation": {
            "sectionsScanned": ["Methods", "Results"],
            "supplementaryScanned": False,
            "harmsScan": {"performed": True},
            "attestedBy": {"agentClass": "model"}},
    }
    d.update(over)
    return d


def _req():
    return build_reading_request(_sections_doc(), _contract(), report="rep:1")


# ── 請求的建立 ────────────────────────────────────────────────────
def test_request_binds_the_document_actually_read():
    r = _req()
    assert r.manifestation == SHA_A
    assert r.section_titles == ["Methods", "Results"]


def test_missing_content_hash_is_refused_not_recomputed():
    """重算會得到「現在這份」的雜湊，而清冊要綁的是產生它的那一份。"""
    doc = _sections_doc()
    del doc["contentSha256"]
    with pytest.raises(ValueError, match="contentSha256"):
        build_reading_request(doc, _contract(), report="rep:1")


def test_unfrozen_contract_refused_before_the_paper_is_read():
    """對著還會變的契約讀論文，讀完也不能用——故擋在讀之前，不是判定時。"""
    with pytest.raises(ValueError, match="非 frozen"):
        build_reading_request(_sections_doc(), _contract(status="draft"),
                              report="rep:1")


def test_frozen_but_unhashed_contract_refused():
    c = _contract()
    del c["scopeContractHash"]
    with pytest.raises(ValueError, match="綁定不完整"):
        build_reading_request(_sections_doc(), c, report="rep:1")


def test_empty_sections_refused():
    with pytest.raises(ValueError, match="sections"):
        build_reading_request(_sections_doc(sections=[]), _contract(), report="rep:1")


def test_hints_do_not_become_an_allowlist():
    """契約結局只是對照；清冊須含範圍外者，否則 backfill 失去依據。"""
    p = _req().prompt_payload()
    assert p["mustIncludeOutOfScope"] is True
    assert "scopeDecision" in p["mustNotReturn"]


# ── draft 的驗收 ──────────────────────────────────────────────────
def test_good_draft_accepted():
    r = _req()
    assert validate_draft(_draft(r), r)["lifecycle"] == "draft"


def test_draft_carrying_scope_decision_rejected():
    """模型自填範圍判定＝繞過範圍契約。"""
    r = _req()
    d = _draft(r)
    d["reportedOutcomes"][0]["scopeDecision"] = {"inScope": True}
    with pytest.raises(DraftRejected, match="範圍判定"):
        validate_draft(d, r)


def test_draft_claiming_scoped_lifecycle_rejected():
    r = _req()
    with pytest.raises(DraftRejected, match="lifecycle"):
        validate_draft(_draft(r, lifecycle="scoped"), r)


def test_empty_outcomes_rejected():
    """空清冊會被讀成「這篇沒報告任何結局」——那是關於論文的宣稱。"""
    r = _req()
    with pytest.raises(DraftRejected, match="空清冊"):
        validate_draft(_draft(r, reportedOutcomes=[]), r)


def test_draft_bound_to_another_document_rejected():
    r = _req()
    with pytest.raises(DraftRejected, match="manifestation"):
        validate_draft(_draft(r, manifestation="sha256:" + "b" * 64), r)


def test_draft_bound_to_another_contract_rejected():
    r = _req()
    with pytest.raises(DraftRejected, match="scopeContractHash"):
        validate_draft(_draft(r, scopeContractHash="sha256:" + "d" * 64), r)


def test_attesting_sections_the_document_lacks_is_rejected():
    """聲稱掃描過不存在的章節，該聲明整份不可信。"""
    r = _req()
    d = _draft(r)
    d["completenessAttestation"]["sectionsScanned"] = ["Methods", "Appendix Z"]
    with pytest.raises(DraftRejected, match="Appendix Z"):
        validate_draft(d, r)


# ── 接縫 ──────────────────────────────────────────────────────────
def test_reading_seam_raises_rather_than_returning_empty():
    with pytest.raises(ReadingSeamNotImplemented):
        read_sections(_req())


# ── 交回既有確定性層 ──────────────────────────────────────────────
def test_scoping_is_delegated_and_produces_scoped_lifecycle():
    r = _req()
    scoped = draft_to_scoped(validate_draft(_draft(r), r), _contract())
    assert scoped["lifecycle"] == "scoped"
    assert all("scopeDecision" in o for o in scoped["reportedOutcomes"])


# ── 儀器：讀的人必須看得到判定會逐字比對的那份清單（第 488 輪） ──────
INSTRUMENTS = ["dxa", "four-compartment-model"]


def _req_with_instruments():
    return build_reading_request(
        _sections_doc(),
        _contract(inScopeOutcomes=[
            {"outcomeId": "ffm-change", "label": "去脂體重變化",
             "role": "critical", "quantityKind": "qk:ffm",
             "comparabilityClass": "body-composition-multi-compartment",
             "allowedInstruments": list(INSTRUMENTS)}]),
        report="rep:1")


def test_the_reader_is_told_which_instruments_will_be_accepted():
    """判定拿 instrument 逐字比 allowedInstruments，而讀的人先前看不到那份清單。

    第二位讀者第一次比對就撞到：六項全部以「儀器不在允許清單」被排除，
    而那篇論文用的就是允許的儀器，只是名字被改寫過。
    """
    payload = _req_with_instruments().prompt_payload()
    hint = payload["contractOutcomesForReference"][0]
    assert hint["allowedInstruments"] == INSTRUMENTS
    # 清單會讓人想去湊一個，故規則要同時說「或留 null」。
    assert "null" in payload["instrumentRule"]
    assert "nearest" in payload["instrumentRule"]


def test_an_invented_instrument_is_refused_at_the_door():
    """擋的是**沉默的排除**：改寫過的名字下游會變成「儀器不在允許清單」，
    而那個理由與「這篇真的用了別的儀器」長得一模一樣。"""
    r = _req_with_instruments()
    d = _draft(r)
    d["reportedOutcomes"][0].update(
        {"normalisedOutcomeRef": "ffm-change",
         "instrument": "dual-energy-x-ray-absorptiometry-whole-body"})
    with pytest.raises(DraftRejected, match="不在允許清單"):
        validate_draft(d, r)


def test_null_instrument_is_accepted_so_the_two_reasons_stay_apart():
    """null 一樣落在範圍外，但它說的是「這篇的儀器不在清單裡」。"""
    r = _req_with_instruments()
    d = _draft(r)
    d["reportedOutcomes"][0].update({"normalisedOutcomeRef": "ffm-change",
                                     "instrument": None})
    assert validate_draft(d, r) is not None
    d["reportedOutcomes"][0]["instrument"] = "dxa"
    assert validate_draft(d, r) is not None


def test_an_out_of_scope_outcome_may_use_the_papers_own_wording():
    """清冊登錄的是論文報告了什麼——範圍外的那些不必落在任何允許清單裡。"""
    r = _req_with_instruments()
    d = _draft(r)
    d["reportedOutcomes"][0].update({"normalisedOutcomeRef": None,
                                     "instrument": "bioimpedance, 8-electrode"})
    assert validate_draft(d, r) is not None
