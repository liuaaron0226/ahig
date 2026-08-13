#!/usr/bin/env python3
"""AHIG v2.1 裁決層修正的行為測試（Task #13 / issue 05）。

本檔對應六項要求：
  1. coverage / gold accuracy / major-error 三者分離；沒有 gold 不得產生 accuracy；
     共同錯誤（NO_CONFLICT）也必須可由 gold 評估。
  2. 數值欄位不得以 anchor 強度單獨裁決；anchor 需 verifiedBinding 才可作非數值定位。
  3. ADJ-004 的 crude 2x2 只適用 unadjusted 且 estimand/analysisSet/model 一致。
  4. null 狀態區分 NOT_REPORTED / CANNOT_LOCATE。
  5. ADJ-001 保留 canonical 值；ADJ-003 回傳一致結構與 registry canonical unit。
  6. 每條 ADJ 規則都有可達 fixture，且數值分歧不得以計票方式處理。
"""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

from ahig.stats import adjudication as adj

MODULE_PATH = Path(__file__).resolve().parents[1] / "ahig" / "stats" / "adjudication.py"


# ===========================================================================
# 共用 fixture 工具
# ===========================================================================

def binding(**over):
    """一個完整合格的 verifiedBinding。"""
    b = {
        "sourceHash": "sha256:" + "a" * 64,
        "field": "populationLabel",
        "outcome": "1rm-squat",
        "timepoint": "wk12",
        "arm": "intervention",
        "analysisSet": "ITT",
    }
    b.update(over)
    return b


def anchored(value, method="exact", unique=True, bind=None, **over):
    payload = {"value": value,
               "anchor": {"anchorMethod": method, "uniqueMatch": unique,
                          "verifiedBinding": bind}}
    payload.update(over)
    return payload


def two_by_two_ctx(**over):
    ctx = {"effectMeasure": "RR",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100},
           "baseStudyResult": {"ciLow": 0.28, "ciHigh": 0.89, "pValue": 0.019}}
    ctx.update(over)
    return ctx


# ===========================================================================
# 要求 1 —— coverage / accuracy / major-error 分離
# ===========================================================================

def test_coverage_is_reported_without_gold():
    fields = {
        "analysisSet": {"A": {"value": "intention-to-treat"}, "B": {"value": "ITT"}},
        "sampleSize": {"A": {"value": 200}, "B": {"value": 198}},
    }
    out = adj.adjudicate_record(fields)
    cov = out["metrics"]["coverage"]
    assert cov["nConflicts"] == 2
    assert cov["nAutoResolved"] == 1
    assert cov["deterministicResolutionCoverage"] == 0.5
    assert "coverage 不是正確率" in cov["note"]


def test_no_gold_means_no_accuracy_anywhere_in_the_payload():
    """沒有 gold set 時，輸出中不得出現任何非 None 的 accuracy 數字。"""
    fields = {"analysisSet": {"A": {"value": "intention-to-treat"},
                              "B": {"value": "ITT"}}}
    out = adj.adjudicate_record(fields)
    assert out["metrics"]["goldEvaluation"] is None

    found = []

    def walk(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if "accuracy" in k.lower() and v is not None:
                    found.append((path + "/" + k, v))
                walk(v, path + "/" + k)
        elif isinstance(node, list):
            for i, v in enumerate(node):
                walk(v, f"{path}[{i}]")

    walk(json.loads(json.dumps(out)))
    assert not found, f"沒有 gold 卻產生了 accuracy：{found}"


def test_empty_gold_dict_is_treated_as_no_gold():
    fields = {"analysisSet": {"A": {"value": "ITT"}, "B": {"value": "ITT"}}}
    out = adj.adjudicate_record(fields, gold={})
    assert out["metrics"]["goldEvaluation"] is None


def test_gold_accuracy_is_separate_from_coverage():
    """coverage 高不代表 accuracy 高 —— 兩個數字必須各自獨立呈現。"""
    fields = {
        "analysisSet": {"A": {"value": "intention-to-treat"}, "B": {"value": "ITT"}},
        "effectMeasure": {"A": {"value": "Risk Ratio"}, "B": {"value": "RR"}},
    }
    gold = {"analysisSet": {"value": "ITT"}, "effectMeasure": {"value": "OR"}}
    out = adj.adjudicate_record(fields, gold=gold)
    cov = out["metrics"]["coverage"]
    ge = out["metrics"]["goldEvaluation"]
    assert cov["deterministicResolutionCoverage"] == 1.0
    assert ge["deterministicResolutionAccuracy"] == 0.5
    assert ge["nCorrect"] == 1 and ge["nWrong"] == 1


def test_shared_error_in_no_conflict_is_caught_by_gold():
    """兩位盲審者犯同一個錯 —— agreement 完全看不到，只有 gold 抓得到。"""
    fields = {"pointEstimate": {"A": {"value": 0.80}, "B": {"value": 0.80}}}
    gold = {"pointEstimate": {"value": 0.50}}
    out = adj.adjudicate_record(fields, gold=gold)
    ge = out["metrics"]["goldEvaluation"]
    assert out["adjudications"][0]["outcome"] == adj.NO_CONFLICT
    assert ge["sharedErrorCount"] == 1
    assert ge["majorErrorCount"] == 1
    assert ge["byField"]["pointEstimate"]["agreementClass"] == "both-agreed"
    # NO_CONFLICT 不是「裁決」，不得混進裁決正確率
    assert ge["deterministicResolutionAccuracy"] is None
    assert ge["committedValueAccuracy"] == 0.0


def test_major_error_count_separates_major_from_minor():
    fields = {
        "pointEstimate": {"A": {"value": 0.80}, "B": {"value": 0.80}},
        "settingDescription": {"A": {"value": "University Lab"},
                               "B": {"value": "university  lab"}},
    }
    gold = {"pointEstimate": {"value": 0.50},
            "settingDescription": {"value": "university laboratory"}}
    out = adj.adjudicate_record(fields, gold=gold)
    ge = out["metrics"]["goldEvaluation"]
    assert ge["nWrong"] == 2
    assert ge["majorErrorCount"] == 1
    assert ge["minorErrorCount"] == 1
    assert ge["majorErrors"][0]["field"] == "pointEstimate"


def test_escalation_is_not_counted_as_an_accuracy_error():
    fields = {"sampleSize": {"A": {"value": 42}, "B": {"value": 24}}}
    gold = {"sampleSize": {"value": 42}}
    out = adj.adjudicate_record(fields, gold=gold)
    ge = out["metrics"]["goldEvaluation"]
    assert ge["nEscalated"] == 1
    assert ge["nWrong"] == 0
    assert ge["majorErrorCount"] == 0
    assert ge["committedValueAccuracy"] is None


def test_gold_entry_may_override_severity():
    fields = {"settingDescription": {"A": {"value": "lab"}, "B": {"value": "lab"}}}
    gold = {"settingDescription": {"value": "field", "severity": "major"}}
    ge = adj.adjudicate_record(fields, gold=gold)["metrics"]["goldEvaluation"]
    assert ge["majorErrorCount"] == 1


def test_fields_absent_from_gold_are_not_evaluable():
    fields = {"analysisSet": {"A": {"value": "intention-to-treat"},
                              "B": {"value": "ITT"}},
              "settingDescription": {"A": {"value": "a"}, "B": {"value": "b"}}}
    gold = {"analysisSet": {"value": "ITT"}}
    ge = adj.adjudicate_record(fields, gold=gold)["metrics"]["goldEvaluation"]
    assert ge["nNotEvaluable"] == 1
    assert ge["byField"]["settingDescription"]["status"] == "NOT_EVALUABLE"


# ===========================================================================
# 要求 2 —— anchor 只能定位，不能替數值背書
# ===========================================================================

def test_numeric_field_is_never_decided_by_anchor_strength_alone():
    a = anchored(42, "exact", True, binding(field="sampleSize"))
    b = anchored(24, "fuzzy-accepted", False, binding(field="sampleSize"))
    r = adj.adjudicate_field("sampleSize", a, b, {})
    assert r.outcome == adj.ESCALATE
    assert r.escalate_to == "human-expert"
    assert r.rule_id == "ADJ-999-no-deterministic-basis"


def test_non_numeric_anchor_strength_resolves_when_binding_is_verified():
    a = anchored("resistance-trained men", "exact", True, binding())
    b = anchored("recreational men", "fuzzy-accepted", False, binding())
    r = adj.adjudicate_field("populationLabel", a, b, {})
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.rule_id == "ADJ-005-anchor-strength"
    assert r.winner == "A" and r.value == "resistance-trained men"


def test_anchor_without_verified_binding_cannot_win():
    a = anchored("resistance-trained men", "exact", True, None)
    b = anchored("recreational men", "fuzzy-accepted", False, None)
    r = adj.adjudicate_field("populationLabel", a, b, {})
    assert r.outcome == adj.ESCALATE
    assert r.escalate_to == "third-model"
    assert "verified-binding-absent" in json.dumps(r.to_json())


def test_binding_missing_a_required_key_cannot_win():
    incomplete = binding()
    del incomplete["arm"]
    a = anchored("resistance-trained men", "exact", True, incomplete)
    b = anchored("recreational men", "fuzzy-accepted", False, None)
    r = adj.adjudicate_field("populationLabel", a, b, {})
    assert r.outcome == adj.ESCALATE
    assert "binding-missing-arm" in json.dumps(r.to_json())


def test_binding_bound_to_a_different_arm_cannot_win():
    a = anchored("resistance-trained men", "exact", True,
                 binding(arm="comparator"))
    b = anchored("recreational men", "fuzzy-accepted", False, None)
    ctx = {"arm": "intervention"}
    r = adj.adjudicate_field("populationLabel", a, b, ctx)
    assert r.outcome == adj.ESCALATE
    assert "binding-arm-mismatch" in json.dumps(r.to_json())


def test_binding_with_malformed_source_hash_cannot_win():
    a = anchored("resistance-trained men", "exact", True,
                 binding(sourceHash="notebooklm-doc-42"))
    b = anchored("recreational men", "fuzzy-accepted", False, None)
    r = adj.adjudicate_field("populationLabel", a, b, {})
    assert r.outcome == adj.ESCALATE
    assert "binding-source-hash-malformed" in json.dumps(r.to_json())


def test_numeric_without_recomputation_basis_goes_to_human_expert():
    r = adj.adjudicate_field("pointEstimate", {"value": 0.5}, {"value": 0.7}, {})
    assert r.outcome == adj.ESCALATE and r.escalate_to == "human-expert"


# ===========================================================================
# 要求 3 —— crude 2x2 的適用範圍
# ===========================================================================

def test_crude_2x2_resolves_when_model_is_unadjusted():
    ctx = two_by_two_ctx(statisticalModel="unadjusted")
    r = adj.adjudicate_field("pointEstimate", {"value": 0.50}, {"value": 0.85}, ctx)
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.rule_id == "ADJ-004-numeric-recomputation" and r.winner == "A"


def test_adjusted_estimate_is_not_defeated_by_crude_2x2():
    """crude 2x2 重算出 0.50，但報告的是校正模型 —— 不得判 A 錯。"""
    ctx = {"effectMeasure": "RR",
           "statisticalModel": "adjusted-prespecified",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100},
           "baseStudyResult": {}}
    r = adj.adjudicate_field("pointEstimate", {"value": 0.85}, {"value": 0.50}, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-004c-crude-2x2-inadmissible"
    assert r.escalate_to == "human-expert"
    assert r.winner is None


def test_crude_2x2_with_mismatched_analysis_set_is_inadmissible():
    ctx = {"effectMeasure": "RR", "analysisSet": "PP",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100,
                        "analysisSet": "ITT"},
           "baseStudyResult": {}}
    r = adj.adjudicate_field("pointEstimate", {"value": 0.85}, {"value": 0.50}, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-004c-crude-2x2-inadmissible"
    assert "analysisSet" in r.rationale


def test_crude_2x2_with_mismatched_estimand_is_inadmissible():
    ctx = {"effectMeasure": "RR", "estimand": "per-protocol-principal-stratum",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100,
                        "estimand": "treatment-policy"},
           "baseStudyResult": {}}
    r = adj.adjudicate_field("pointEstimate", {"value": 0.85}, {"value": 0.50}, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-004c-crude-2x2-inadmissible"


def test_inadmissible_2x2_does_not_block_other_recomputation_evidence():
    """2x2 不可用時，CI/p 的內部一致性檢查仍然可以裁決。"""
    ctx = {"effectMeasure": "RR", "statisticalModel": "adjusted-prespecified",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100},
           "baseStudyResult": {"ciLow": 0.28, "ciHigh": 0.89, "pValue": 0.019}}
    r = adj.adjudicate_field("pointEstimate", {"value": 0.50}, {"value": 9.9}, ctx)
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.rule_id == "ADJ-004-numeric-recomputation" and r.winner == "A"


# ===========================================================================
# 要求 4 —— null 狀態
# ===========================================================================

def test_cannot_locate_loses_to_verified_non_numeric_anchor():
    a = anchored("double-blind", "exact", True, binding(field="blinding"))
    b = {"value": None, "nullState": adj.CANNOT_LOCATE}
    r = adj.adjudicate_field("blinding", a, b, {})
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.rule_id == "ADJ-006-null-vs-anchored" and r.winner == "A"


def test_not_reported_is_a_positive_claim_and_must_escalate():
    a = anchored("double-blind", "exact", True, binding(field="blinding"))
    b = {"value": None, "nullState": adj.NOT_REPORTED}
    r = adj.adjudicate_field("blinding", a, b, {})
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-006c-null-state-contradiction"


def test_undeclared_null_state_does_not_get_the_lenient_path():
    a = anchored("double-blind", "exact", True, binding(field="blinding"))
    b = {"value": None}
    r = adj.adjudicate_field("blinding", a, b, {})
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-006b-null-unanchored"
    assert adj.NULL_STATE_UNDECLARED in r.rationale


def test_two_nulls_with_different_states_are_a_conflict_not_agreement():
    a = {"value": None, "nullState": adj.NOT_REPORTED}
    b = {"value": None, "nullState": adj.CANNOT_LOCATE}
    r = adj.adjudicate_field("pointEstimate", a, b, {})
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-006c-null-state-contradiction"


def test_two_nulls_with_the_same_state_agree():
    a = {"value": None, "nullState": adj.NOT_REPORTED}
    b = {"value": None, "nullState": adj.NOT_REPORTED}
    r = adj.adjudicate_field("pointEstimate", a, b, {})
    assert r.outcome == adj.NO_CONFLICT
    assert r.rule_id == "ADJ-000-identical"


def test_numeric_null_needs_recomputation_not_anchor():
    a = anchored(0.50, "exact", True, binding(field="pointEstimate"))
    b = {"value": None, "nullState": adj.CANNOT_LOCATE}
    assert adj.adjudicate_field("pointEstimate", a, b, {}).outcome == adj.ESCALATE
    r = adj.adjudicate_field("pointEstimate", a, b,
                             two_by_two_ctx(statisticalModel="unadjusted"))
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.rule_id == "ADJ-006-null-vs-anchored" and r.winner == "A"


# ===========================================================================
# 要求 5 —— ADJ-001 canonical 值、ADJ-003 結構與註冊表
# ===========================================================================

def test_text_normalisation_keeps_canonical_casing():
    r = adj.adjudicate_field("populationLabel", {"value": "Trained  Males"},
                             {"value": "trained males"}, {})
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.value == "Trained Males"


def test_text_normalisation_is_order_independent():
    ab = adj.adjudicate_field("populationLabel", {"value": "Trained  Males"},
                              {"value": "trained males"}, {})
    ba = adj.adjudicate_field("populationLabel", {"value": "trained males"},
                              {"value": "Trained  Males"}, {})
    assert ab.value == ba.value


def test_unit_conversion_returns_a_consistent_structure():
    r = adj.adjudicate_field("dose", {"value": 5, "unit": "g"},
                             {"value": 5000, "unit": "mg"}, {})
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.rule_id == "ADJ-003-unit-conversion"
    assert r.value == {"value": 5.0, "unit": "g"}


def test_unit_conversion_is_order_independent():
    ab = adj.adjudicate_field("dose", {"value": 5, "unit": "g"},
                              {"value": 5000, "unit": "mg"}, {})
    ba = adj.adjudicate_field("dose", {"value": 5000, "unit": "mg"},
                              {"value": 5, "unit": "g"}, {})
    assert ab.value == ba.value == {"value": 5.0, "unit": "g"}


def test_unit_conversion_uses_the_registry_canonical_unit():
    ctx = {"quantityKinds": {"jumpHeight": "ahig:qk:countermovement-jump-height"}}
    r = adj.adjudicate_field("jumpHeight", {"value": 450, "unit": "mm"},
                             {"value": 45, "unit": "cm"}, ctx)
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.value == {"value": 45.0, "unit": "cm"}   # 註冊表的 ucumCode
    assert r.evidence["quantityKindId"] == "ahig:qk:countermovement-jump-height"


def test_registry_seed_supplies_a_canonical_unit_for_absolute_dose():
    entry = adj.quantity_kind_entry("ahig:qk:supplement-dose-absolute")
    assert entry is not None, "註冊表需要一個可作為絕對劑量 canonical unit 的項目"
    assert entry["representation"]["ucumCode"] == "g"
    ctx = {"quantityKinds": {"dose": "ahig:qk:supplement-dose-absolute"}}
    r = adj.adjudicate_field("dose", {"value": 5000, "unit": "mg"},
                             {"value": 5, "unit": "g"}, ctx)
    assert r.value == {"value": 5.0, "unit": "g"}


def test_not_comparable_quantity_kind_blocks_unit_conversion():
    ctx = {"quantityKinds": {"load": "ahig:qk:trimp"}}
    r = adj.adjudicate_field("load", {"value": 5, "unit": "min"},
                             {"value": 300, "unit": "s"}, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-003b-comparability-blocked"
    assert "not-comparable" in r.rationale


def test_blocking_condition_present_blocks_unit_conversion():
    ctx = {"quantityKinds": {"jumpHeight": "ahig:qk:countermovement-jump-height"},
           "declaredConditions": ["flight-time-vs-impulse-momentum"]}
    r = adj.adjudicate_field("jumpHeight", {"value": 450, "unit": "mm"},
                             {"value": 45, "unit": "cm"}, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-003b-comparability-blocked"


def test_instrument_mismatch_blocks_unit_conversion():
    ctx = {"quantityKinds": {"jumpHeight": "ahig:qk:countermovement-jump-height"}}
    a = {"value": 450, "unit": "mm", "instrument": "force-plate"}
    b = {"value": 45, "unit": "cm", "instrument": "contact-mat"}
    r = adj.adjudicate_field("jumpHeight", a, b, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-003b-comparability-blocked"
    assert "instrument" in r.rationale


def test_method_mismatch_blocks_unit_conversion():
    ctx = {"quantityKinds": {"jumpHeight": "ahig:qk:countermovement-jump-height"}}
    a = {"value": 450, "unit": "mm", "method": "impulse-momentum"}
    b = {"value": 45, "unit": "cm", "method": "flight-time"}
    r = adj.adjudicate_field("jumpHeight", a, b, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-003b-comparability-blocked"


def test_undeclared_composite_conversion_is_never_guessed():
    r = adj.adjudicate_field("dose", {"value": 5, "unit": "mg/(kg.d)"},
                             {"value": 0.005, "unit": "g/(kg.d)"}, {})
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-003c-undeclared-composite-conversion"
    assert r.escalate_to == "human-expert"


def test_undeclared_simple_unit_pair_still_escalates():
    r = adj.adjudicate_field("load", {"value": 5, "unit": "AU"},
                             {"value": 5000, "unit": "TRIMP"}, {})
    assert r.outcome == adj.ESCALATE
    assert r.rule_id == "ADJ-999-no-deterministic-basis"


def test_registry_entries_still_validate_against_the_schema():
    root = Path(__file__).resolve().parents[1]
    schema = json.loads((root / "schema" / "quantity-kind-registry.schema.json")
                        .read_text(encoding="utf-8"))
    reg = json.loads((root / "registry" / "quantity-kinds.sport-science.json")
                     .read_text(encoding="utf-8"))
    from jsonschema import Draft202012Validator
    v = Draft202012Validator(schema)
    for e in reg["entries"]:
        errs = list(v.iter_errors(e))
        assert not errs, f"{e['quantityKindId']}: {errs[0].message}"


# ===========================================================================
# 要求 6 —— 規則可達性與「數值不得以計票裁決」
# ===========================================================================

def _rule_fixtures():
    """每條規則至少一個可達 fixture：(ruleId, 呼叫參數)。"""
    bind_pe = binding(field="pointEstimate")
    return [
        ("ADJ-000-identical",
         ("sampleSize", {"value": 42}, {"value": 42}, {})),
        ("ADJ-001-text-normalisation",
         ("populationLabel", {"value": "Trained  Males"},
          {"value": "trained males"}, {})),
        ("ADJ-002-enum-synonym",
         ("analysisSet", {"value": "intention-to-treat"}, {"value": "ITT"}, {})),
        ("ADJ-003-unit-conversion",
         ("dose", {"value": 5, "unit": "g"}, {"value": 5000, "unit": "mg"}, {})),
        ("ADJ-003b-comparability-blocked",
         ("load", {"value": 5, "unit": "min"}, {"value": 300, "unit": "s"},
          {"quantityKinds": {"load": "ahig:qk:trimp"}})),
        ("ADJ-003c-undeclared-composite-conversion",
         ("dose", {"value": 5, "unit": "mg/(kg.d)"},
          {"value": 0.005, "unit": "g/(kg.d)"}, {})),
        ("ADJ-004-numeric-recomputation",
         ("pointEstimate", {"value": 0.50}, {"value": 0.85},
          two_by_two_ctx(statisticalModel="unadjusted"))),
        ("ADJ-004b-both-fail-recomputation",
         ("pointEstimate", {"value": 0.85}, {"value": 0.95},
          two_by_two_ctx(statisticalModel="unadjusted"))),
        ("ADJ-004c-crude-2x2-inadmissible",
         ("pointEstimate", {"value": 0.85}, {"value": 0.50},
          {"effectMeasure": "RR", "statisticalModel": "adjusted-prespecified",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100},
           "baseStudyResult": {}})),
        ("ADJ-005-anchor-strength",
         ("populationLabel", anchored("resistance-trained men", "exact", True,
                                      binding()),
          anchored("recreational men", "fuzzy-accepted", False, binding()), {})),
        ("ADJ-006-null-vs-anchored",
         ("blinding", anchored("double-blind", "exact", True,
                               binding(field="blinding")),
          {"value": None, "nullState": adj.CANNOT_LOCATE}, {})),
        ("ADJ-006b-null-unanchored",
         ("blinding", {"value": "double-blind"}, {"value": None}, {})),
        ("ADJ-006c-null-state-contradiction",
         ("pointEstimate", {"value": None, "nullState": adj.NOT_REPORTED},
          {"value": None, "nullState": adj.CANNOT_LOCATE}, {})),
        ("ADJ-007-schema-violation",
         ("analysisSet", anchored("ITT", "exact", True, bind_pe),
          {"value": "whatever"}, {"allowedValues": {"analysisSet": ["ITT", "PP"]}})),
        ("ADJ-999-no-deterministic-basis",
         ("sampleSize", {"value": 42}, {"value": 24}, {})),
    ]


def test_every_fixture_reaches_its_declared_rule():
    for rule_id, args in _rule_fixtures():
        r = adj.adjudicate_field(*args)
        assert r.rule_id == rule_id, f"期待 {rule_id}，實得 {r.rule_id}（{r.rationale}）"


def test_every_rule_id_in_the_module_has_a_reachable_fixture():
    """模組原始碼中宣告的每一個 ADJ 規則都必須被 fixture 觸達，
    否則就是被前面的規則遮蔽（ADJ-005/006 曾經如此）。"""
    src = MODULE_PATH.read_text(encoding="utf-8")
    declared = set(re.findall(r'"(ADJ-[0-9a-z-]+)"', src))
    covered = {rid for rid, _ in _rule_fixtures()}
    assert declared, "沒有掃到任何規則 id"
    assert declared <= covered, f"以下規則沒有可達 fixture：{sorted(declared - covered)}"


def test_anchor_rule_no_longer_shadows_the_null_rule():
    """舊實作中 ADJ-005 先跑，使 ADJ-006 永遠不可達。"""
    a = anchored("double-blind", "exact", True, binding(field="blinding"))
    b = {"value": None, "nullState": adj.CANNOT_LOCATE}
    assert adj.adjudicate_field("blinding", a, b, {}).rule_id == "ADJ-006-null-vs-anchored"


def test_anchor_rule_no_longer_shadows_the_schema_rule():
    ctx = {"allowedValues": {"analysisSet": ["ITT", "PP"]}}
    a = anchored("ITT", "exact", True, binding(field="analysisSet"))
    b = anchored("whatever", "fuzzy-accepted", False, None)
    r = adj.adjudicate_field("analysisSet", a, b, ctx)
    assert r.rule_id == "ADJ-007-schema-violation"


def test_numeric_conflict_is_not_settled_by_counting_agreeing_raters():
    """行為層面驗證：即使 context 明示第三方與 B 一致、且宣告 2:1，
    數值分歧仍必須升級，不得產生 winner。"""
    ctx = {"thirdModelValue": 24, "agreeingRaterCount": {"A": 1, "B": 2},
           "priorConsensus": 24}
    r = adj.adjudicate_field("sampleSize", {"value": 42}, {"value": 24}, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.winner is None and r.value is None
    assert r.escalate_to == "human-expert"


def test_numeric_record_with_consensus_hints_still_escalates():
    fields = {"pointEstimate": {"A": {"value": 0.50}, "B": {"value": 0.85}},
              "ciLow": {"A": {"value": 0.28}, "B": {"value": 0.30}}}
    ctx = {"thirdModelValues": {"pointEstimate": 0.85, "ciLow": 0.30},
           "agreeingRaterCount": {"B": 2}}
    out = adj.adjudicate_record(fields, ctx)
    assert out["nAutoResolved"] == 0
    assert all(o["winner"] is None for o in out["adjudications"])
    assert len(out["escalatedToHuman"]) == 2


def test_module_source_contains_no_counting_logic():
    src = MODULE_PATH.read_text(encoding="utf-8")
    for banned in ("majority", "vote(", "most_common", "Counter("):
        assert banned not in src, f"發現疑似計票邏輯：{banned}"


# ===========================================================================
# 回歸：既有契約行為不得退化
# ===========================================================================

def test_both_sides_failing_still_escalates_to_human_expert():
    r = adj.adjudicate_field("pointEstimate", {"value": 0.85}, {"value": 0.95},
                             two_by_two_ctx(statisticalModel="unadjusted"))
    assert r.outcome == adj.ESCALATE and r.escalate_to == "human-expert"


def test_non_numeric_disagreement_still_goes_to_third_model():
    r = adj.adjudicate_field("settingDescription", {"value": "university lab"},
                             {"value": "sports institute"}, {})
    assert r.escalate_to == "third-model"


def test_same_after_conversion_still_honours_the_declared_table():
    assert adj.same_after_conversion(5, "g", 5000, "mg")
    assert not adj.same_after_conversion(5, "AU", 5000, "TRIMP")
    assert math.isclose(adj.DECLARED_CONVERSIONS[("g", "mg")], 1000.0)


if __name__ == "__main__":
    from run_tests import main
    raise SystemExit(main([__file__]))
