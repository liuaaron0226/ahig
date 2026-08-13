"""B.11 SearchContract：PRISMA-S 稽核軌、查詢 artifact 與契約鏈。

本檔不測任何搜尋結果；它測的是在送出第一個 API request 之前，方法是否已經
被凍結到足以重現與稽核。搜尋之後才補查詢式，等於用結果反過來畫靶。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator

from ahig.contracts import freeze

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "calibration" / "b11-carbohydrate"
SCHEMA_PATH = ROOT / "schema" / "search-contract-version.schema.json"
CONTRACT_PATH = CAL / "search-contract.json"
SCOPE_PATH = CAL / "scope-contract.json"
STRATA_PATH = CAL / "strata.json"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def contract() -> dict:
    return load(CONTRACT_PATH)


def source(source_id: str) -> dict:
    return next(s for s in contract()["sources"] if s["sourceId"] == source_id)


# ---------------------------------------------------------------------------
# schema、lifecycle 與 hash
# ---------------------------------------------------------------------------

def test_search_contract_validates_against_schema():
    errors = sorted(Draft202012Validator(load(SCHEMA_PATH)).iter_errors(contract()),
                    key=lambda e: list(e.path))
    assert not errors, f"{list(errors[0].path)} — {errors[0].message}"


def test_search_contract_is_frozen_and_hash_self_verifies():
    c = contract()
    assert c["status"] == "frozen" and c.get("frozenAt")
    assert freeze.verify_frozen(c, "contractHash")


def test_first_version_is_explicitly_initial_not_falsely_editorial():
    """第一版沒有前版可比較；標 editorial 或 recall-neutral 都是假證據。"""
    c = contract()
    assert c["changeClass"] == "initial"
    assert c["supersedes"] is None
    assert c["backfillObligation"] == {
        "required": False,
        "scope": "none",
        "deadlinePolicy": "before-any-approved-claim-in-domain",
        "blocksNewBatches": False,
    }


def test_initial_contract_does_not_claim_unmeasured_recall():
    r = contract()["recallEvaluation"]
    assert r["status"] == "pending-calibration"
    assert r["knownItemSeedSet"] == []
    assert r["seedRecallCurrent"] is None
    assert r["minAcceptableSeedRecall"] == 0.95


# ---------------------------------------------------------------------------
# query artifacts
# ---------------------------------------------------------------------------

def test_every_candidate_source_has_a_hashed_query_artifact():
    candidates = [s for s in contract()["sources"] if s["generatesCandidateRecords"]]
    assert candidates
    for s in candidates:
        assert s["queryArtifacts"], s["sourceId"]
        for artifact in s["queryArtifacts"]:
            path = ROOT / artifact["path"]
            assert path.is_file(), f"缺少 query artifact：{path}"
            actual = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
            assert artifact["sha256"] == actual, \
                f"{artifact['strategyId']} hash 過期：{artifact['sha256']} vs {actual}"


def test_pubmed_query_is_self_contained_not_history_dependent():
    text = (ROOT / source("pubmed")["queryArtifacts"][0]["path"]).read_text(
        encoding="utf-8")
    assert "#1" not in text and "#2" not in text, \
        "PubMed History 編號只在 cookie/session 內有效，不可作正式檢索式"
    assert "[tiab]" in text and "[Mesh]" in text
    assert "carbohydrat" in text.lower() and "exercis" in text.lower()


def test_no_candidate_query_uses_relative_date_language():
    """`last 5 years` 每天意思都不同；正式契約只允許絕對日期或不設日期限制。"""
    forbidden = ("last 30 days", "last 1 year", "last 5 years", "last 10 years")
    for s in contract()["sources"]:
        for artifact in s.get("queryArtifacts", []):
            text = (ROOT / artifact["path"]).read_text(encoding="utf-8").lower()
            assert not any(token in text for token in forbidden), artifact["strategyId"]


def test_query_artifacts_are_utf8_lf_text_or_json():
    for s in contract()["sources"]:
        for artifact in s.get("queryArtifacts", []):
            raw = (ROOT / artifact["path"]).read_bytes()
            raw.decode("utf-8")
            assert b"\r\n" not in raw, f"{artifact['path']} 不是 LF"
            assert artifact["encoding"] == "utf-8"


# ---------------------------------------------------------------------------
# PRISMA-S 與來源覆蓋
# ---------------------------------------------------------------------------

def test_prisma_s_attestation_covers_all_sixteen_items_exactly_once():
    items = contract()["prismaSAttestation"]
    ids = [item["item"] for item in items]
    assert sorted(ids) == list(range(1, 17))
    assert len(ids) == len(set(ids)) == 16
    assert all(item["status"] in {"implemented", "not-applicable"} for item in items)


def test_database_and_platform_are_both_named():
    for s in contract()["sources"]:
        assert s["databaseName"].strip(), s["sourceId"]
        assert s["platform"].strip(), s["sourceId"]


def test_required_candidate_source_classes_are_present():
    classes = {s["sourceClass"] for s in contract()["sources"]
               if s["generatesCandidateRecords"]}
    assert {"bibliographic-database", "discovery-index", "study-registry"} <= classes


def test_required_free_sources_are_present():
    ids = {s["sourceId"] for s in contract()["sources"]}
    assert {"pubmed", "europe-pmc", "openalex", "clinicaltrials-gov"} <= ids


def test_every_candidate_source_has_deterministic_pagination():
    for s in contract()["sources"]:
        if not s["generatesCandidateRecords"]:
            continue
        p = s["pagination"]
        assert p["mode"] in {"eutils-history", "cursor", "page-token", "offset"}
        assert p["pageSize"] > 0
        assert p["terminationCondition"].strip()


def test_limits_are_explicit_and_not_hidden_in_database_filters():
    limits = contract()["searchLimits"]
    assert limits["languages"] == "none"
    assert limits["publicationDateLower"] is None
    assert limits["studyDesignFilter"] == "none-screen-downstream"
    assert limits["publicationStatus"] == "all-including-preprints"
    assert limits["justification"].strip()


def test_press_review_gap_blocks_approved_claims():
    c = contract()
    assert c["pressReview"]["status"] == "notPRESSReviewed"
    assert c["governance"]["blocksApprovedClaims"] is True
    assert "press-review" in c["governance"]["unblockConditions"]


# ---------------------------------------------------------------------------
# execution、deduplication 與合法取得
# ---------------------------------------------------------------------------

def test_raw_requests_and_responses_are_retained():
    e = contract()["executionProtocol"]
    assert e["requestManifestRequired"] is True
    assert e["rawResponseRetention"] == "required"
    assert e["recordCountPerSourceRequired"] is True
    assert e["requestTimestampRequired"] is True


def test_deduplication_never_auto_merges_on_title_only():
    d = contract()["deduplication"]
    assert d["titleOnlyAutoMerge"] is False
    assert d["ambiguousMatchAction"] == "human-review"
    assert d["identifierPrecedence"][:4] == ["doi", "pmid", "pmcid", "registry-id"]


def test_access_policy_is_legal_only_and_forbids_bypass():
    a = contract()["accessPolicy"]
    assert a["legalAccessOnly"] is True
    assert a["bypassAccessControls"] is False
    assert a["onNoLegalFullText"] == "record-unavailable-and-continue-metadata-only"


def test_access_resolver_order_uses_open_routes_before_manual_review():
    order = contract()["accessPolicy"]["resolverOrder"]
    assert order[:3] == ["pmc-open-access", "europe-pmc", "unpaywall"]
    assert order[-1] == "manual-author-or-library-request"


def test_access_provenance_records_license_version_and_location():
    required = set(contract()["accessPolicy"]["requiredProvenanceFields"])
    assert {"resolvedUrl", "hostType", "versionType", "license",
            "checkedAt", "resolver", "fullTextChecksum"} <= required


# ---------------------------------------------------------------------------
# 契約鏈
# ---------------------------------------------------------------------------

def test_scope_contract_references_the_real_search_contract_hash():
    search = contract()
    derived = load(SCOPE_PATH)["derivedFromSearchContract"]
    assert derived == {
        "searchContractId": search["searchContractId"],
        "version": search["version"],
        "hash": search["contractHash"],
    }
    assert set(derived["hash"]) != {"0", ":", "s", "h", "a", "2", "5", "6"}


def test_scope_and_strata_contract_chain_remains_consistent():
    scope = load(SCOPE_PATH)
    strata = load(STRATA_PATH)
    assert freeze.verify_frozen(scope, "scopeContractHash")
    assert strata["scopeContractHash"] == scope["scopeContractHash"]


def test_scope_draft_is_already_bound_to_the_frozen_search_contract():
    """避免有人單跑 freeze_contract.py，把下游又凍結回舊 placeholder hash。"""
    search = contract()
    draft = load(CAL / "scope-contract.draft.json")
    assert draft["derivedFromSearchContract"] == {
        "searchContractId": search["searchContractId"],
        "version": search["version"],
        "hash": search["contractHash"],
    }


def test_update_policy_is_executable_not_just_narrative():
    u = contract()["updatePolicy"]
    assert u["rerunMode"] == "full-query-rerun-plus-date-delta-audit"
    assert u["beforeApprovedClaim"] is True
    assert u["recordNewAndRemovedCandidates"] is True


def test_method_references_include_prisma_s_and_api_docs():
    urls = {r["url"] for r in contract()["methodReferences"]}
    assert any("PMC8270366" in u for u in urls)
    assert any("NBK25499" in u for u in urls)
    assert any("clinicaltrials.gov" in u for u in urls)
    assert any("unpaywall.org" in u for u in urls)
