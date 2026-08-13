from __future__ import annotations

import math

from ahig.gates.quality_gate import (
    GatePolicy,
    clopper_pearson_upper,
    evaluate_batch_quality,
    minimum_sample_size,
)


def test_clopper_pearson_exact_boundaries():
    assert math.isclose(clopper_pearson_upper(0, 30), 0.095034, rel_tol=1e-5)
    assert clopper_pearson_upper(0, 299) <= 0.01
    assert clopper_pearson_upper(0, 298) > 0.01


def test_minimum_sample_size_matches_exact_result():
    assert minimum_sample_size(0.01, observed_errors=0) == 299
    assert minimum_sample_size(0.05, observed_errors=0) == 59


def test_coverage_accuracy_and_major_errors_are_independent():
    policy = GatePolicy()
    result = evaluate_batch_quality(
        sample_size=299,
        error_count=0,
        conflict_count=100,
        auto_resolved_count=90,
        auto_resolved_correct_count=89,
        major_error_count=0,
        common_wrong_agreement_count=0,
        agreement={
            "gwetAC1": 0.90,
            "ciLower95": 0.70,
            "ciUpper95": 0.96,
            "modelAssumptions": ["independent-items", "declared-prevalence-model"],
        },
        policy=policy,
    )
    assert result["deterministicResolution"]["coverage"] == 0.9
    assert result["deterministicResolution"]["accuracy"] == 89 / 90
    assert result["decision"] == "fail"  # accuracy < 0.99 even though coverage passes


def test_three_year_capacity_policy_requires_87_5_percent_coverage():
    result = evaluate_batch_quality(
        sample_size=299,
        error_count=0,
        conflict_count=100,
        auto_resolved_count=87,
        auto_resolved_correct_count=87,
        major_error_count=0,
        common_wrong_agreement_count=0,
        agreement={
            "gwetAC1": 0.90,
            "ciLower95": 0.70,
            "ciUpper95": 0.96,
            "modelAssumptions": ["independent-items"],
        },
    )
    assert result["deterministicResolution"]["coverage"] == 0.87
    assert result["decision"] == "fail"


def test_missing_gold_cannot_claim_accuracy():
    result = evaluate_batch_quality(
        sample_size=60,
        error_count=0,
        conflict_count=20,
        auto_resolved_count=18,
        auto_resolved_correct_count=None,
        major_error_count=None,
        common_wrong_agreement_count=None,
        agreement=None,
    )
    assert result["deterministicResolution"]["accuracy"] is None
    assert result["decision"] == "insufficient-evidence"


def test_ac1_without_assumptions_is_insufficient_evidence():
    result = evaluate_batch_quality(
        sample_size=299,
        error_count=0,
        conflict_count=100,
        auto_resolved_count=90,
        auto_resolved_correct_count=90,
        major_error_count=0,
        common_wrong_agreement_count=0,
        agreement={"gwetAC1": 0.90, "ciLower95": 0.70, "ciUpper95": 0.96, "modelAssumptions": []},
    )
    assert result["decision"] == "insufficient-evidence"
