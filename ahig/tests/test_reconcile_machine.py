"""W9：機器對帳路徑 `reconcile_machine`（ADR-0009 裁定②，B 路線）。

人類路徑 `reconcile`／`_validate_binding` 一行不動，本檔的第一組測試就是
釘住這件事的迴歸網。機器路徑的三條不變量：

1. 兩位 reviewer 皆 `agentClass == "llm"` 且 `modelId` 必須相異；
2. `judgedBy` 依 ADR-0009 原則 2/3 完整（含 rawResponse 對應的判讀理由）；
3. 對立判讀與任一方 unclear 一律進 `ownerAuditQueue`，**不自動裁決**——
   產物不得出現 `resolved`／`decision` 這類自動欄位。
"""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from ahig.contracts.freeze import verify_frozen
from ahig.search import screening, screening_decisions

ROOT = Path(__file__).resolve().parents[1]

MODEL_A = {"id": "claude-opus-5", "version": "2026-05"}
MODEL_B = {"id": "gemini-3-pro", "version": "2026-04"}


def queue_fixture():
    candidates = [
        {
            "candidateId": f"c{i}", "entityKind": "publication",
            "canonicalIdentity": f"doi:10.1000/{i}", "title": f"T{i}",
            "publicationYear": 2020,
            "identifiers": {"doi": [f"10.1000/{i}"], "pmid": [], "pmcid": [],
                            "registryId": []},
        }
        for i in (1, 2, 3, 4)
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


def assignment_fixture(candidate_ids=None):
    manifest, queue = queue_fixture()
    assignment = screening_decisions.make_assignment(
        manifest, queue, candidate_ids=candidate_ids or ["c1", "c2", "c3", "c4"],
        assignment_id="assign-1", created_at="2026-08-14T12:00:00Z")
    return manifest, queue, assignment


def machine_review(assignment: dict, reviewer_id: str, model: dict,
                   judgements: list[dict], review_id: str | None = None,
                   *, agent_class: str = "llm",
                   blinded: bool = True) -> dict:
    """機器審查文件；`judgements` 每筆 {candidateId, opinion, rawResponse}。"""
    return {
        "documentType": "title-abstract-machine-review",
        "schemaVersion": "1.0.0",
        "reviewId": review_id or f"review-{reviewer_id}",
        "assignmentId": assignment["assignmentId"],
        "runId": assignment["runId"],
        "screeningQueueHash": assignment["screeningQueueHash"],
        "candidateSetHash": assignment["candidateSetHash"],
        "reviewer": {
            "reviewerId": reviewer_id,
            "agentClass": agent_class,
            "blindedToOtherReviewer": blinded,
        },
        "judgedBy": {
            "agentClass": "llm",
            "modelId": model["id"],
            "modelVersion": model["version"],
            "adr": "ADR-0009 裁定①",
        },
        "completedAt": "2026-08-14T13:00:00Z",
        "judgements": judgements,
    }


def judgement(candidate_id: str, opinion: str, raw: str | None = None) -> dict:
    return {
        "candidateId": candidate_id,
        "opinion": opinion,
        "rawResponse": raw or f"{opinion}：判讀理由全文（{candidate_id}）",
    }


def human_review(assignment: dict, reviewer_id: str,
                 decisions: list[dict]) -> dict:
    return {
        "documentType": "title-abstract-screening-review",
        "schemaVersion": "1.0.0",
        "reviewId": f"review-{reviewer_id}",
        "assignmentId": assignment["assignmentId"],
        "runId": assignment["runId"],
        "screeningQueueHash": assignment["screeningQueueHash"],
        "candidateSetHash": assignment["candidateSetHash"],
        "reviewer": {
            "reviewerId": reviewer_id,
            "agentClass": "human-self",
            "blindedToOtherReviewer": True,
        },
        "completedAt": "2026-08-14T13:00:00Z",
        "decisions": decisions,
    }


def decision(candidate_id: str, value: str, reason: str) -> dict:
    return {"candidateId": candidate_id, "decision": value,
            "primaryReasonCode": reason}


def assert_rejected(callable_, contains: str = ""):
    try:
        callable_()
    except (RuntimeError, ValueError,
            screening_decisions.ScreeningDecisionError) as exc:
        assert contains.lower() in str(exc).lower(), \
            f"預期訊息含 {contains!r}，實際：{exc}"
        return
    raise AssertionError("預期 fail-closed 拒絕")


def all_agree(opinion: str = "exclude") -> list[dict]:
    return [judgement(f"c{i}", opinion) for i in (1, 2, 3, 4)]


def machine_pair(assignment, primary_ops: list[dict],
                 secondary_ops: list[dict]):
    return (machine_review(assignment, "model-a", MODEL_A, primary_ops),
            machine_review(assignment, "model-b", MODEL_B, secondary_ops))


# ---------------------------------------------------------------------------
# W9 規格第 1 條：人類路徑保持原樣（迴歸網）
# ---------------------------------------------------------------------------

def test_human_reconcile_still_resolves_and_rejects_machine_reviewers():
    """人類路徑行為不變：人審能 resolve，且機器審查者仍被 `_validate_binding` 擋。"""
    manifest, queue, assignment = assignment_fixture(["c1", "c2"])
    decisions = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ]
    result = screening_decisions.reconcile(
        manifest, queue, assignment,
        human_review(assignment, "alice", decisions),
        human_review(assignment, "bob", list(reversed(decisions))))
    assert result["status"] == "resolved"
    assert result["counts"]["advanceCount"] == 1
    assert verify_frozen(result, "reconciliationHash")

    llm_reviewer = human_review(assignment, "carol", decisions)
    llm_reviewer["reviewer"]["agentClass"] = "llm"
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment,
        human_review(assignment, "alice", decisions), llm_reviewer),
        "human")


def test_human_path_still_requires_reason_codes_and_full_coverage():
    """人類路徑的理由碼與覆蓋檢查未被機器路徑改動。"""
    manifest, queue, assignment = assignment_fixture(["c1", "c2"])
    good = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ]
    bad_reason = [
        decision("c1", "advance", "TA-EXC-ANIMAL-ONLY"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ]
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment,
        human_review(assignment, "alice", bad_reason),
        human_review(assignment, "bob", good)), "primaryReasonCode")
    assert_rejected(lambda: screening_decisions.reconcile(
        manifest, queue, assignment,
        human_review(assignment, "alice", good[:1]),
        human_review(assignment, "bob", good)), "mismatch")


# ---------------------------------------------------------------------------
# W9 規格第 2 條：雙 LLM、modelId 必異、judgedBy 完整
# ---------------------------------------------------------------------------

def test_machine_reconcile_requires_both_reviewers_to_be_llm():
    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(assignment, all_agree(), all_agree())
    human_flavoured = machine_review(
        assignment, "model-b", MODEL_B, all_agree(), agent_class="human-self")
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, human_flavoured), "llm")


def test_machine_reconcile_rejects_identical_model_id():
    """雙模型盲判的執行點：同 modelId 兩位 reviewer 必須被拒。"""
    manifest, queue, assignment = assignment_fixture()
    primary = machine_review(assignment, "model-a", MODEL_A, all_agree())
    same_model = machine_review(assignment, "model-b", MODEL_A, all_agree())
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, same_model), "model")


def test_machine_reconcile_rejects_same_model_id_even_with_different_version():
    """版本不同不算不同模型——盲判要的是獨立模型，不是同模型換版。"""
    manifest, queue, assignment = assignment_fixture()
    primary = machine_review(assignment, "model-a", MODEL_A, all_agree())
    other_version = machine_review(
        assignment, "model-b", {"id": MODEL_A["id"], "version": "2026-08"},
        all_agree())
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, other_version), "model")


def test_machine_reconcile_requires_complete_judged_by():
    """ADR-0009 原則 2：缺 judgedBy 的判讀不得進入任何下游計算。"""
    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(assignment, all_agree(), all_agree())
    for mutate in (
        lambda r: r.pop("judgedBy"),
        lambda r: r["judgedBy"].pop("modelId"),
        lambda r: r["judgedBy"].pop("agentClass"),
        lambda r: r["judgedBy"].update({"agentClass": "human-self"}),
    ):
        broken = json.loads(json.dumps(secondary))
        mutate(broken)
        assert_rejected(lambda: screening_decisions.reconcile_machine(
            manifest, queue, assignment, primary, broken), "judgedby")


def test_machine_reconcile_requires_raw_response_per_judgement():
    """ADR-0009 原則 3：原始回應（判讀理由）必須逐筆落盤。"""
    manifest, queue, assignment = assignment_fixture()
    primary, _ = machine_pair(assignment, all_agree(), all_agree())
    for bad in ("", "   ", None):
        ops = all_agree()
        ops[0]["rawResponse"] = bad
        secondary = machine_review(assignment, "model-b", MODEL_B, ops)
        assert_rejected(lambda: screening_decisions.reconcile_machine(
            manifest, queue, assignment, primary, secondary), "rawresponse")
    ops = all_agree()
    ops[0].pop("rawResponse")
    secondary = machine_review(assignment, "model-b", MODEL_B, ops)
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary), "rawresponse")


def test_machine_reconcile_rejects_human_decision_fields_in_judgements():
    """盲判不變量：機器判讀條目不得攜帶人類決策欄位。"""
    manifest, queue, assignment = assignment_fixture()
    primary, _ = machine_pair(assignment, all_agree(), all_agree())
    ops = all_agree()
    ops[0]["humanDecision"] = "advance"
    secondary = machine_review(assignment, "model-b", MODEL_B, ops)
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary), "盲")


def test_machine_reconcile_reuses_binding_checks():
    """綁定檢查與人類路徑共用：queue hash、候選集、覆蓋範圍都要擋。"""
    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(assignment, all_agree(), all_agree())

    drifted = json.loads(json.dumps(secondary))
    drifted["screeningQueueHash"] = "sha256:" + "0" * 64
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, drifted), "hash")

    partial = machine_review(assignment, "model-b", MODEL_B, all_agree()[:2])
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, partial), "mismatch")

    dupe = machine_review(assignment, "model-b", MODEL_B,
                          all_agree() + [judgement("c1", "exclude")])
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, dupe), "duplicate")


def test_machine_reconcile_rejects_invalid_opinion_and_shared_review_id():
    manifest, queue, assignment = assignment_fixture()
    primary, _ = machine_pair(assignment, all_agree(), all_agree())
    ops = all_agree()
    ops[0]["opinion"] = "maybe"
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary,
        machine_review(assignment, "model-b", MODEL_B, ops)), "opinion")

    same_id = machine_review(assignment, "model-b", MODEL_B, all_agree(),
                             review_id=primary["reviewId"])
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, same_id), "reviewid")


def test_machine_reconcile_requires_blinded_reviewers():
    manifest, queue, assignment = assignment_fixture()
    primary, _ = machine_pair(assignment, all_agree(), all_agree())
    unblinded = machine_review(assignment, "model-b", MODEL_B, all_agree(),
                               blinded=False)
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, unblinded), "blind")


# ---------------------------------------------------------------------------
# W9 規格第 3 條：對立／unclear 進佇列，不自動裁決
# ---------------------------------------------------------------------------

def test_opposed_and_unclear_go_to_owner_audit_queue_without_adjudication():
    """advance vs exclude 是對立；任一方 unclear 也進佇列。兩者都不自動裁決。"""
    manifest, queue, assignment = assignment_fixture()
    primary = machine_review(assignment, "model-a", MODEL_A, [
        judgement("c1", "advance"),
        judgement("c2", "advance"),
        judgement("c3", "unclear"),
        judgement("c4", "exclude"),
    ])
    secondary = machine_review(assignment, "model-b", MODEL_B, [
        judgement("c1", "advance"),
        judgement("c2", "exclude"),
        judgement("c3", "exclude"),
        judgement("c4", "unclear"),
    ])
    result = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        completed_at="2026-08-14T14:00:00Z")

    assert result["opposedCandidateIds"] == ["c2"]
    assert [item["candidateId"] for item in result["ownerAuditQueue"]] == \
        ["c2", "c3", "c4"]
    kinds = {item["candidateId"]: item["disagreementKind"]
             for item in result["ownerAuditQueue"]}
    assert kinds == {"c2": "opposed", "c3": "either-unclear",
                     "c4": "either-unclear"}
    assert result["status"] == "needs-owner-audit"
    assert result["counts"]["concordantCount"] == 1
    assert result["counts"]["ownerAuditCount"] == 3


def test_machine_reconciliation_carries_no_automatic_decision_fields():
    """與 machine_shadow_gate 同一條紀律：產物不含自動裁決欄位。"""
    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(assignment, all_agree("advance"), [
        judgement("c1", "advance"), judgement("c2", "advance"),
        judgement("c3", "unclear"), judgement("c4", "exclude"),
    ])
    result = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary)
    blob = json.dumps(result, ensure_ascii=False)
    for forbidden in ("resolvedDecisions", "\"decision\"", "reconciledDecision",
                      "\"resolved\""):
        assert forbidden not in blob, f"機器產物不得含自動裁決欄位：{forbidden}"
    for item in result["concordant"]:
        assert "decision" not in item
        assert item["opinion"] in {"advance", "exclude", "unclear"}


def test_full_concordance_still_requires_owner_audit_before_release():
    """全數一致也不放行：機器路徑的啟用前提是影子門檻＋協調者放行。"""
    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(assignment, all_agree("exclude"),
                                      all_agree("exclude"))
    result = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary)
    assert result["status"] == "concordant"
    assert result["ownerAuditQueue"] == []
    assert result["eligibleSamplingPoolReady"] is False
    assert result["machineScreeningReleased"] is False
    assert "machine-screening-not-released" in result["blockingReasons"]
    assert "full-text-screening-not-completed" in result["blockingReasons"]
    assert result["evidenceGrade"] == \
        "AI-graded evidence — no human expert review"


def test_unclear_on_both_sides_is_still_owner_audit_not_agreement():
    """兩邊都 unclear 不是共識——它是兩個模型都沒把握，仍要進佇列。"""
    manifest, queue, assignment = assignment_fixture(["c1", "c2"])
    primary, secondary = machine_pair(
        assignment,
        [judgement("c1", "unclear"), judgement("c2", "exclude")],
        [judgement("c1", "unclear"), judgement("c2", "exclude")])
    result = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary)
    assert [i["candidateId"] for i in result["ownerAuditQueue"]] == ["c1"]
    assert result["ownerAuditQueue"][0]["disagreementKind"] == "either-unclear"
    assert result["counts"]["concordantCount"] == 1


def test_owner_audit_items_record_both_model_opinions_for_traceability():
    manifest, queue, assignment = assignment_fixture(["c1", "c2"])
    primary, secondary = machine_pair(
        assignment,
        [judgement("c1", "advance", "主模型：貼題"), judgement("c2", "exclude")],
        [judgement("c1", "exclude", "次模型：時點不符"), judgement("c2", "exclude")])
    result = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary)
    item = result["ownerAuditQueue"][0]
    opinions = {o["modelId"]: o for o in item["modelOpinions"]}
    assert set(opinions) == {MODEL_A["id"], MODEL_B["id"]}
    assert opinions[MODEL_A["id"]]["opinion"] == "advance"
    assert opinions[MODEL_B["id"]]["opinion"] == "exclude"
    assert opinions[MODEL_B["id"]]["rawResponse"] == "次模型：時點不符"


# ---------------------------------------------------------------------------
# 產物結構、確定性、落盤
# ---------------------------------------------------------------------------

def test_machine_reconciliation_is_deterministic_and_frozen():
    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(assignment, all_agree(), all_agree())
    one = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        completed_at="2026-08-14T14:00:00Z")
    two = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        completed_at="2026-08-14T14:00:00Z")
    assert one == two
    assert verify_frozen(one, "reconciliationHash")
    assert one["documentType"] == "title-abstract-machine-reconciliation"
    assert one["adr"] == "ADR-0009"


def test_reviewer_order_does_not_change_the_outcome():
    """主／次順序不影響對帳結果——對立是對稱認定，沒有金標準。"""
    manifest, queue, assignment = assignment_fixture(["c1", "c2"])
    a_ops = [judgement("c1", "advance"), judgement("c2", "exclude")]
    b_ops = [judgement("c1", "exclude"), judgement("c2", "exclude")]
    primary = machine_review(assignment, "model-a", MODEL_A, a_ops)
    secondary = machine_review(assignment, "model-b", MODEL_B, b_ops)
    forward = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        completed_at="2026-08-14T14:00:00Z")
    backward = screening_decisions.reconcile_machine(
        manifest, queue, assignment, secondary, primary,
        completed_at="2026-08-14T14:00:00Z")
    assert forward == backward


def test_partial_assignment_does_not_complete_machine_screening():
    manifest, queue = queue_fixture()
    assignment = screening_decisions.make_assignment(
        manifest, queue, candidate_ids=["c1"], assignment_id="partial",
        created_at="2026-08-14T12:00:00Z")
    ops = [judgement("c1", "exclude")]
    primary = machine_review(assignment, "model-a", MODEL_A, ops)
    secondary = machine_review(assignment, "model-b", MODEL_B, ops)
    result = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary)
    assert result["assignmentCoversQueue"] is False
    assert result["nextStage"] == "title-abstract-screening"
    assert "machine-title-abstract-screening-not-completed" in \
        result["blockingReasons"]


def schema_doc() -> dict:
    return json.loads(
        (ROOT / "schema" / "title-abstract-screening.schema.json").read_text(
            encoding="utf-8"))


def test_machine_documents_validate_against_schema():
    from jsonschema import Draft202012Validator

    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(assignment, [
        judgement("c1", "advance"), judgement("c2", "advance"),
        judgement("c3", "unclear"), judgement("c4", "exclude"),
    ], [
        judgement("c1", "advance"), judgement("c2", "exclude"),
        judgement("c3", "exclude"), judgement("c4", "exclude"),
    ])
    result = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary)
    validator = Draft202012Validator(schema_doc())
    for doc in (primary, secondary, result):
        errors = list(validator.iter_errors(doc))
        assert not errors, f"{doc['documentType']}：{[e.message for e in errors][:2]}"


def test_schema_still_accepts_human_documents_and_rejects_hybrids():
    """新增分支不得污染人類文件的驗證——oneOf 必須恰好命中一支。"""
    from jsonschema import Draft202012Validator

    manifest, queue, assignment = assignment_fixture(["c1", "c2"])
    decisions = [
        decision("c1", "advance", "TA-ADV-POTENTIALLY-ELIGIBLE"),
        decision("c2", "exclude", "TA-EXC-ANIMAL-ONLY"),
    ]
    validator = Draft202012Validator(schema_doc())
    review_a = human_review(assignment, "alice", decisions)
    human_result = screening_decisions.reconcile(
        manifest, queue, assignment, review_a,
        human_review(assignment, "bob", decisions))
    for doc in (assignment, review_a, human_result):
        assert not list(validator.iter_errors(doc)), doc["documentType"]

    # 機器審查文件掛人類 agentClass 不得通過任一分支。
    hybrid = machine_review(assignment, "model-a", MODEL_A,
                            [judgement("c1", "exclude"), judgement("c2", "exclude")],
                            agent_class="human-self")
    assert list(validator.iter_errors(hybrid))

    # 機器對帳產物被塞入自動裁決欄位也必須被 schema 擋下。
    primary, secondary = machine_pair(
        assignment,
        [judgement("c1", "exclude"), judgement("c2", "exclude")],
        [judgement("c1", "exclude"), judgement("c2", "exclude")])
    tampered = json.loads(json.dumps(screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary)))
    tampered["resolvedDecisions"] = [{"candidateId": "c1", "decision": "exclude"}]
    assert list(validator.iter_errors(tampered))


def test_machine_reconciliation_write_is_immutable_and_private_root_bound():
    manifest, queue, assignment = assignment_fixture(["c1", "c2"])
    primary, secondary = machine_pair(
        assignment,
        [judgement("c1", "exclude"), judgement("c2", "exclude")],
        [judgement("c1", "exclude"), judgement("c2", "exclude")])
    result = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        completed_at="2026-08-14T14:00:00Z")
    with tempfile.TemporaryDirectory() as tmp:
        with patch.dict(os.environ, {"AHIG_PRIVATE_ROOT": tmp}, clear=False):
            path = Path(tmp) / "machine-reconciliation.json"
            screening_decisions.write_reconciliation(path, result)
            screening_decisions.write_reconciliation(path, result)
            assert json.loads(path.read_text(encoding="utf-8")) == result
            outside = Path(tmp).parent / "outside-machine-reconciliation.json"
            assert_rejected(
                lambda: screening_decisions.write_reconciliation(outside, result),
                "AHIG_PRIVATE_ROOT")


# ---------------------------------------------------------------------------
# W10 追加：reconcile_machine 的擁有者裁決紀錄（第 n+16 輪，步驟 1）
# ---------------------------------------------------------------------------

def owner_record(decision="advance"):
    return {"decidedBy": "owner", "decision": decision,
            "decidedAt": "2026-08-15", "reasonShort": "recall 優先，全文再核"}


def test_reconcile_owner_decision_resolves_opposed_and_flips_status():
    manifest, queue, assignment = assignment_fixture()
    primary = machine_review(assignment, "model-a", MODEL_A, [
        judgement("c1", "advance"), judgement("c2", "exclude"),
        judgement("c3", "exclude"), judgement("c4", "exclude"),
    ])
    secondary = machine_review(assignment, "model-b", MODEL_B, [
        judgement("c1", "exclude"), judgement("c2", "exclude"),
        judgement("c3", "exclude"), judgement("c4", "exclude"),
    ])
    without = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary)
    assert without["status"] == "needs-owner-audit"
    assert without["unresolvedOpposedCandidateIds"] == ["c1"]
    assert without["unresolvedOwnerAuditCandidateIds"] == ["c1"]

    with_decision = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        owner_decisions={"c1": owner_record()})
    assert with_decision["opposedCandidateIds"] == ["c1"]
    assert with_decision["unresolvedOpposedCandidateIds"] == []
    assert with_decision["unresolvedOwnerAuditCandidateIds"] == []
    assert with_decision["ownerDecisions"] == {"c1": owner_record()}
    assert with_decision["status"] == "concordant"
    # 裁決不改變佇列本身——只多記一份已發生的裁決事實。
    assert with_decision["ownerAuditQueue"] == without["ownerAuditQueue"]


def test_reconcile_owner_decision_rejects_candidate_outside_audit_queue():
    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(assignment, all_agree("exclude"),
                                      all_agree("exclude"))
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        owner_decisions={"c1": owner_record()}), "c1")


def test_reconcile_owner_decision_rejects_non_owner_decider():
    manifest, queue, assignment = assignment_fixture()
    primary = machine_review(assignment, "model-a", MODEL_A, [
        judgement("c1", "advance"), judgement("c2", "exclude"),
        judgement("c3", "exclude"), judgement("c4", "exclude"),
    ])
    secondary = machine_review(assignment, "model-b", MODEL_B, [
        judgement("c1", "exclude"), judgement("c2", "exclude"),
        judgement("c3", "exclude"), judgement("c4", "exclude"),
    ])
    bad = {**owner_record(), "decidedBy": "executor-session"}
    assert_rejected(lambda: screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        owner_decisions={"c1": bad}), "owner")


def test_reconcile_owner_decisions_default_empty_preserves_prior_behaviour():
    manifest, queue, assignment = assignment_fixture()
    primary, secondary = machine_pair(
        assignment,
        [judgement("c1", "advance"), judgement("c2", "advance"),
         judgement("c3", "unclear"), judgement("c4", "exclude")],
        [judgement("c1", "advance"), judgement("c2", "exclude"),
         judgement("c3", "exclude"), judgement("c4", "unclear")])
    no_arg = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        completed_at="2026-08-14T14:00:00Z")
    empty_arg = screening_decisions.reconcile_machine(
        manifest, queue, assignment, primary, secondary,
        completed_at="2026-08-14T14:00:00Z", owner_decisions={})
    assert no_arg == empty_arg
    assert no_arg["ownerDecisions"] == {}
    assert no_arg["unresolvedOpposedCandidateIds"] == no_arg["opposedCandidateIds"]
