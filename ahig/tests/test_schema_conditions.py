from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


def schema(name: str) -> Draft202012Validator:
    doc = json.loads((ROOT / "schema" / name).read_text(encoding="utf-8"))
    Draft202012Validator.check_schema(doc)
    return Draft202012Validator(doc)


def errors(name: str, value: dict) -> list:
    return list(schema(name).iter_errors(value))


def monitoring_policy() -> dict:
    return {
        "policyId": "policy-1", "version": "1.0.0", "riskTier": "general-clinical",
        "sourceStatusSLA": {"maxAgeHours": 240, "graceHours": 12},
        "evidenceRevalidationInterval": {"months": 12},
        "onSLABreach": {"autoTransitionTo": "flagged", "blocksHealthReasoning": False},
    }


def monitoring_run() -> dict:
    return {
        "runId": "run-1", "startedAt": "2026-08-13T00:00:00Z",
        "finishedAt": "2026-08-13T00:01:00Z",
        "feed": {"feedType": "crossref-updates-filter", "strategy": "change-feed-diff",
                 "snapshotHash": "sha256:" + "a" * 64, "snapshotRecordCount": 2},
        "outcome": "success", "coveredSourceCount": 10,
    }


def search_contract() -> dict:
    return {
        "searchContractId": "search-1", "version": "1.1.0",
        "contractHash": "sha256:" + "a" * 64,
        "changeClass": "recall-expanding", "appliesTo": ["cc-1"],
        "backfillObligation": {
            "required": True, "scope": "all-domains-at-lower-version",
            "deadlinePolicy": "before-any-approved-claim-in-domain", "blocksNewBatches": True,
        },
        "recallEvaluation": {
            "knownItemSeedSet": ["10.1000/example"], "seedRecallPrevious": 0.9,
            "seedRecallCurrent": 1.0, "minAcceptableSeedRecall": 0.95,
        },
        "provenance": {
            "authoredBy": "researcher", "approvedBy": [
                {"agent": "owner", "agentClass": "human-self", "at": "2026-08-13T00:00:00Z"}
            ],
            "createdAt": "2026-08-13T00:00:00Z", "llmDrafted": True,
            "modelVersion": "claude-opus-5", "promptHash": "sha256:" + "b" * 64,
        },
    }


def test_monitoring_schema_has_usable_root():
    assert not errors("monitoring.schema.json", monitoring_policy())
    assert not errors("monitoring.schema.json", monitoring_run())
    assert errors("monitoring.schema.json", {"anything": "passes"})


def test_per_item_poll_requires_justification():
    value = monitoring_run()
    value["feed"] = {"feedType": "per-doi-poll", "strategy": "per-item-poll"}
    assert errors("monitoring.schema.json", value)
    value["feed"]["perItemPollJustification"] = "No change feed exists"
    assert not errors("monitoring.schema.json", value)


def test_successful_change_feed_requires_snapshot():
    value = monitoring_run()
    del value["feed"]["snapshotHash"]
    assert errors("monitoring.schema.json", value)


def test_safety_critical_policy_blocks_reasoning():
    value = monitoring_policy()
    value["riskTier"] = "safety-critical"
    assert errors("monitoring.schema.json", value)
    value["onSLABreach"]["blocksHealthReasoning"] = True
    value["onSLABreach"]["autoTransitionTo"] = "stale-monitoring"
    assert not errors("monitoring.schema.json", value)


def test_recall_expanding_requires_full_backfill():
    value = search_contract()
    assert not errors("search-contract-version.schema.json", value)
    value["backfillObligation"]["required"] = False
    value["backfillObligation"]["scope"] = "none"
    assert errors("search-contract-version.schema.json", value)


def test_recall_neutral_requires_seed_evidence():
    value = search_contract()
    value["changeClass"] = "recall-neutral"
    del value["recallEvaluation"]
    value["backfillObligation"] = {
        "required": False, "scope": "none", "deadlinePolicy": "before-next-batch",
        "blocksNewBatches": False,
    }
    assert errors("search-contract-version.schema.json", value)


def test_frozen_scope_requires_timestamp_hash_and_human_approval():
    from tests.test_scope_and_family import base_contract
    value = base_contract()
    value.pop("frozenAt", None)
    value.pop("scopeContractHash", None)
    assert errors("extraction-scope-contract.schema.json", value)


def test_ucum_quantity_requires_code():
    value = {
        "quantityKindId": "ahig:qk:test", "label": "Test",
        "representation": {"kind": "ucum", "isDiscreteIntegerScale": False},
        "comparabilityClass": "test",
        "crossStudyComparability": {"level": "directly-comparable", "blockingConditions": []},
    }
    assert errors("quantity-kind-registry.schema.json", value)


def test_mid_unavailable_requires_no_fabricated_value():
    value = {
        "midId": "ahig:mid:test-unavailable", "version": "1.0.0", "status": "unavailable",
        "outcomeRef": "outcome-1", "quantityKind": "ahig:qk:test",
        "population": {"label": "trained adults"},
        "unavailableReason": "No defensible MID found after documented search",
        "provenance": {
            "sourceType": "project-internal", "approvedBy": [
                {"agent": "owner", "agentClass": "human-self", "at": "2026-08-13T00:00:00Z"}
            ], "createdAt": "2026-08-13T00:00:00Z"
        },
    }
    assert not errors("mid-registry.schema.json", value)
    value["value"] = {"scale": "absolute", "magnitude": 1, "unit": "x"}
    assert errors("mid-registry.schema.json", value)


def test_new_quality_time_and_scope_metric_schemas_meta_validate():
    for name in ("batch-quality-gate.schema.json", "time-log.schema.json", "gold-scope-metrics.schema.json"):
        schema(name)
