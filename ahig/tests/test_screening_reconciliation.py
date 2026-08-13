"""B.11 title/abstract screening 的雙盲人工決策與確定性對帳。"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from jsonschema import Draft202012Validator

from ahig.contracts.freeze import content_hash, freeze_document, verify_frozen
from ahig.search import screening, screening_decisions

ROOT = Path(__file__).resolve().parents[1]


def queue_fixture():
    candidates = [
        {
            "candidateId": "c1", "entityKind": "publication",
            "canonicalIdentity": "doi:10.1000/1", "title": "One",
            "publicationYear": 2020,
            "identifiers": {"doi": ["10.1000/1"], "pmid": [], "pmcid": [],
                            "registryId": []},
        },
        {
            "candidateId": "c2", "entityKind": "publication",
            "canonicalIdentity": "doi:10.1000/2", "title": "Two",
            "publicationYear": 2021,
            "identifiers": {"doi": ["10.1000/2"], "pmid": [], "pmcid": [],
                            "registryId": []},
        },
    ]
    built = screening.build_queue(
        candidates,
        candidate_pool_hash="sha256:" + "a" * 64,
        search_contract_hash="sha256:" + "b" * 64,
        run_id="run-1", identifier_conflicts=[], title_ambiguities=[],
        source_coverage={
            "pubmed": "completed", "europe-pmc": "completed",
            "openalex": "completed", "clinicaltrials-gov": "completed",
        },
        complete_across_contract_sources=True,
    )
    return built["manifest"], built["queue"]


def assignment_fixture():
    manifest, queue = queue_fixture()
    assignment = screening_decisions.make_assignment(
        manifest, queue, candidate_ids=["c1", "c2"], assignment_id="assign-1",
        created_at="2026-08-13T12:00:00Z")
    return manifest, queue, assignment


def review(assignment: dict, reviewer_id: str, decisions: list[dict],
           review_id: str | None = None) -> dict:
    return {
        "documentType": "title-abstract-screening-review",
        "schemaVersion": "1.0.0",
        "reviewId": review_id or f"review-{reviewer_id}",
        "assignmentId": assignment["assignmentId"],
        "runId": assignment["runId"],
        "screeningQueueHash": assignment["screeningQueueHash"],
        "candidateSetHash": assignment["candidateSetHash"],
        "reviewer": {
            "reviewerId": reviewer_id,
            "agentClass": "human-self",
            "blindedToOtherReviewer": True,
        },
        "completedAt": "2026-08-13T13:00:00Z",
        "decisions": decisions,
    }


def decision(candidate_id: str, value: str, reason: str) -> dict:
    return {"candidateId": candidate_id, "decision": value,
            "primaryReasonCode": reason}


def assert_rejected(callable_, contains: str = ""):
    try:
        callable_()
    except (RuntimeError, ValueError, screening_decisions.ScreeningDecisionError) as exc:
        assert contains.lower() in str(exc).lower()
        return
    raise AssertionError("預期 fail-closed 拒絕")


def test_schema_meta_validates_and_distinguishes_three_document_types():
    doc = json.loads((ROOT / "schema" / "title-abstract-screening.schema.json").read_text(
        encoding="utf-8"))
    Draft202012Validator.check_schema(doc)
    validator = Draft202012Validator(doc)
    manifest, queue, assignment = assignment_fixture()
    r = review(assignment, "alice", [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ])
    reconciliation = screening_decisions.reconcile(
        manifest, queue, assignment, r,
        review(assignment, "bob", list(reversed(r["decisions"]))),
        completed_at="2026-08-13T14:00:00Z")
    assert not list(validator.iter_errors(assignment))
    assert not list(validator.iter_errors(r))
    assert not list(validator.iter_errors(reconciliation))


def test_screening_manifest_hash_binds_exact_queue_content():
    manifest, queue = queue_fixture()
    assert manifest["screeningQueueHash"] == content_hash(queue)


def test_assignment_is_deterministic_and_bound_to_queue():
    manifest, queue = queue_fixture()
    one = screening_decisions.make_assignment(
        manifest, queue, candidate_ids=["c2", "c1"], assignment_id="assign-1",
        created_at="2026-08-13T12:00:00Z")
    two = screening_decisions.make_assignment(
        manifest, queue, candidate_ids=["c1", "c2"],
        assignment_id="assign-1", created_at="2026-08-13T12:00:00Z")
    assert one == two
    assert one["candidateIds"] == ["c1", "c2"]
    assert one["candidateSetHash"] == content_hash(["c1", "c2"])


def test_assignment_rejects_incomplete_candidate_sources():
    manifest, queue = queue_fixture()
    manifest["candidateSourcesComplete"] = False
    assert_rejected(lambda: screening_decisions.make_assignment(
        manifest, queue, candidate_ids=["c1"], assignment_id="a",
        created_at="2026-08-13T12:00:00Z"), "sources")


def test_assignment_rejects_queue_hash_drift_and_unknown_candidates():
    manifest, queue = queue_fixture()
    bad = dict(manifest, screeningQueueHash="sha256:" + "0" * 64)
    assert_rejected(lambda: screening_decisions.make_assignment(
        bad, queue, candidate_ids=["c1"], assignment_id="a",
        created_at="2026-08-13T12:00:00Z"), "hash")
    assert_rejected(lambda: screening_decisions.make_assignment(
        manifest, queue, candidate_ids=["missing"], assignment_id="a",
        created_at="2026-08-13T12:00:00Z"), "missing")


def test_review_schema_requires_human_blinded_reviewer_and_reason_by_decision():
    _, _, assignment = assignment_fixture()
    valid = review(assignment, "alice", [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "unclear", "TA-UNCLEAR-MISSING-ABSTRACT"),
    ])
    schema_doc = json.loads((ROOT / "schema" / "title-abstract-screening.schema.json").read_text(
        encoding="utf-8"))
    validator = Draft202012Validator(schema_doc)
    assert not list(validator.iter_errors(valid))
    model = json.loads(json.dumps(valid))
    model["reviewer"]["agentClass"] = "model"
    assert list(validator.iter_errors(model))
    wrong_reason = json.loads(json.dumps(valid))
    wrong_reason["decisions"][0]["primaryReasonCode"] = "TA-EXC-ANIMAL-ONLY"
    assert list(validator.iter_errors(wrong_reason))


def test_identical_human_decisions_resolve_without_programmatic_eligibility():
    manifest, queue, assignment = assignment_fixture()
    decisions = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ]
    result = screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", decisions),
        review(assignment, "bob", list(reversed(decisions))))
    assert result["status"] == "resolved"
    assert result["counts"] == {
        "candidateCount": 2, "agreementCount": 2, "needsAdjudicationCount": 0,
        "advanceCount": 1, "excludeCount": 1, "unclearCount": 0,
    }
    assert result["eligibleSamplingPoolReady"] is False
    assert result["nextStage"] == "full-text-screening"
    assert verify_frozen(result, "reconciliationHash")


def test_partial_assignment_cannot_advance_entire_queue_to_full_text():
    manifest, queue = queue_fixture()
    assignment = screening_decisions.make_assignment(
        manifest, queue, candidate_ids=["c1"], assignment_id="partial",
        created_at="2026-08-13T12:00:00Z")
    decisions = [decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE")]
    result = screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", decisions),
        review(assignment, "bob", decisions))
    assert result["status"] == "resolved"
    assert result["assignmentCoversQueue"] is False
    assert result["humanTitleAbstractScreeningComplete"] is False
    assert result["nextStage"] == "title-abstract-screening"
    assert "human-title-abstract-screening-not-completed" in result["blockingReasons"]


def test_incomplete_sources_prevent_title_abstract_completion():
    manifest, queue, assignment = assignment_fixture()
    manifest["candidateSourcesComplete"] = False
    decisions = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    result = screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", decisions),
        review(assignment, "bob", decisions))
    assert result["humanTitleAbstractScreeningComplete"] is False
    assert result["nextStage"] == "candidate-source-search"
    assert "candidate-sources-incomplete" in result["blockingReasons"]


def test_decision_disagreement_never_auto_resolves():
    manifest, queue, assignment = assignment_fixture()
    a = review(assignment, "alice", [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ])
    b = review(assignment, "bob", [
        decision("c1", "exclude", "TA-EXC-POPULATION-OUT-OF-SCOPE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ])
    result = screening_decisions.reconcile(manifest, queue, assignment, a, b)
    assert result["status"] == "needs-adjudication"
    assert [x["candidateId"] for x in result["needsAdjudication"]] == ["c1"]
    assert result["needsAdjudication"][0]["disagreementKind"] == "decision-mismatch"
    assert result["resolvedDecisions"][0]["candidateId"] == "c2"


def test_exclusion_reason_disagreement_requires_adjudication():
    manifest, queue, assignment = assignment_fixture()
    a = review(assignment, "alice", [
        decision("c1", "exclude", "TA-EXC-ANIMAL-ONLY"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ])
    b = review(assignment, "bob", [
        decision("c1", "exclude", "TA-EXC-POPULATION-OUT-OF-SCOPE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ])
    result = screening_decisions.reconcile(manifest, queue, assignment, a, b)
    assert result["needsAdjudication"][0]["disagreementKind"] == "exclusion-reason-mismatch"
    assert result["counts"]["excludeCount"] == 0


def test_same_unclear_decision_preserves_both_human_reason_codes():
    manifest, queue, assignment = assignment_fixture()
    a = review(assignment, "alice", [
        decision("c1", "unclear", "TA-UNCLEAR-MISSING-ABSTRACT"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ])
    b = review(assignment, "bob", [
        decision("c1", "unclear", "TA-UNCLEAR-POPULATION"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ])
    result = screening_decisions.reconcile(manifest, queue, assignment, a, b)
    c1 = next(x for x in result["resolvedDecisions"] if x["candidateId"] == "c1")
    assert c1["decision"] == "unclear"
    assert c1["primaryReasonCodes"] == [
        "TA-UNCLEAR-MISSING-ABSTRACT", "TA-UNCLEAR-POPULATION"]


def test_hand_authored_assignment_cannot_contain_duplicates_or_unknown_ids():
    manifest, queue, assignment = assignment_fixture()
    decisions = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    duplicate = json.loads(json.dumps(assignment))
    duplicate["candidateIds"] = ["c1", "c1"]
    duplicate["candidateSetHash"] = content_hash(["c1", "c1"])
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, duplicate,
        review(assignment, "alice", decisions),
        review(assignment, "bob", decisions)), "duplicate")
    unknown = json.loads(json.dumps(assignment))
    unknown["candidateIds"] = ["c1", "missing"]
    unknown["candidateSetHash"] = content_hash(["c1", "missing"])
    unknown_review_a = review(unknown, "alice", [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("missing", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ])
    unknown_review_b = review(unknown, "bob", unknown_review_a["decisions"])
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, unknown, unknown_review_a, unknown_review_b), "queue")


def test_reviewer_argument_order_does_not_change_reconciliation_hash():
    manifest, queue, assignment = assignment_fixture()
    alice_decisions = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ]
    bob_decisions = [
        decision("c1", "exclude", "TA-EXC-POPULATION-OUT-OF-SCOPE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ]
    alice = review(assignment, "alice", alice_decisions)
    bob = review(assignment, "bob", bob_decisions)
    one = screening_decisions.reconcile(
        manifest, queue, assignment, alice, bob,
        completed_at="2026-08-13T14:00:00Z")
    two = screening_decisions.reconcile(
        manifest, queue, assignment, bob, alice,
        completed_at="2026-08-13T14:00:00Z")
    assert one == two
    assert one["reconciliationHash"] == two["reconciliationHash"]


def test_same_reviewer_or_incomplete_assignment_is_rejected():
    manifest, queue, assignment = assignment_fixture()
    complete = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", complete, "r1"),
        review(assignment, "alice", complete, "r2")), "distinct")
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", complete),
        review(assignment, "bob", complete[:1])), "candidate")


def test_invalid_decision_value_is_rejected_without_relying_on_schema_call():
    manifest, queue, assignment = assignment_fixture()
    bad = [
        decision("c1", "include", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    good = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", bad),
        review(assignment, "bob", good)), "decision")


def test_decision_reason_mapping_is_rejected_without_relying_on_schema_call():
    manifest, queue, assignment = assignment_fixture()
    bad = [
        decision("c1", "advance", "TA-EXC-ANIMAL-ONLY"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    good = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", bad),
        review(assignment, "bob", good)), "primaryReasonCode")


def test_reason_codes_in_schema_and_runtime_cannot_drift():
    schema_doc = json.loads((ROOT / "schema" / "title-abstract-screening.schema.json").read_text(
        encoding="utf-8"))
    branches = schema_doc["$defs"]["Decision"]["allOf"]
    schema_codes = {}
    for branch in branches:
        value = branch["if"]["properties"]["decision"]["const"]
        reason = branch["then"]["properties"]["primaryReasonCode"]
        schema_codes[value] = {reason["const"]} if "const" in reason else set(reason["enum"])
    assert schema_codes == screening_decisions.REASON_CODES


def test_duplicate_candidate_decision_and_binding_drift_are_rejected():
    manifest, queue, assignment = assignment_fixture()
    duplicate = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c1", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ]
    complete = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", duplicate),
        review(assignment, "bob", complete)), "duplicate")
    drift = review(assignment, "alice", complete)
    drift["candidateSetHash"] = "sha256:" + "0" * 64
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment, drift,
        review(assignment, "bob", complete)), "hash")


def resolved_fixture():
    manifest, queue, assignment = assignment_fixture()
    decisions = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
    ]
    result = screening_decisions.reconcile(
        manifest, queue, assignment,
        review(assignment, "alice", decisions),
        review(assignment, "bob", decisions),
        completed_at="2026-08-13T14:00:00Z")
    return result


def test_reconciliation_write_is_atomic_and_private_root_bounded():
    result = resolved_fixture()
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=False):
            path = Path(tmp) / "screening" / "reconciliation.json"
            screening_decisions.write_reconciliation(path, result)
            assert json.loads(path.read_text(encoding="utf-8")) == result
            assert not list(path.parent.glob("*.tmp"))
            outside = Path(tmp).parent / "outside-reconciliation.json"
            assert_rejected(
                lambda: screening_decisions.write_reconciliation(outside, result),
                "AHIG_PRIVATE_ROOT")


def test_reconciliation_write_requires_private_root():
    result = resolved_fixture()
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {}, clear=True):
            assert_rejected(lambda: screening_decisions.write_reconciliation(
                Path(tmp) / "reconciliation.json", result), "AHIG_PRIVATE_ROOT")


def test_existing_reconciliation_is_immutable_but_idempotent_write_is_allowed():
    result = resolved_fixture()
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=False):
            path = Path(tmp) / "reconciliation.json"
            screening_decisions.write_reconciliation(path, result)
            screening_decisions.write_reconciliation(path, result)
            changed = json.loads(json.dumps(result))
            changed["completedAt"] = "2026-08-13T15:00:00Z"
            changed = freeze_document(
                changed, "reconciliationHash", status_field="documentFreezeStatus")
            assert_rejected(
                lambda: screening_decisions.write_reconciliation(path, changed),
                "immutable")
