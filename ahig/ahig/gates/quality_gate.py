from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from scipy import stats


@dataclass(frozen=True)
class GatePolicy:
    error_rate_ceiling: float = 0.01
    confidence: float = 0.95
    ac1_point_min: float = 0.85
    ac1_lower_min: float = 0.65
    deterministic_coverage_min: float = 0.875
    deterministic_accuracy_min: float = 0.99
    major_error_max: int = 0
    common_wrong_agreement_max: int = 0


def clopper_pearson_upper(errors: int, sample_size: int, confidence: float = 0.95) -> float:
    if sample_size <= 0:
        raise ValueError("sample_size must be positive")
    if errors < 0 or errors > sample_size:
        raise ValueError("errors must be between zero and sample_size")
    if errors == sample_size:
        return 1.0
    alpha = 1.0 - confidence
    return float(stats.beta.ppf(1.0 - alpha, errors + 1, sample_size - errors))


def minimum_sample_size(ceiling: float, observed_errors: int = 0,
                        confidence: float = 0.95, maximum: int = 1_000_000) -> int:
    if not 0 < ceiling < 1:
        raise ValueError("ceiling must be between zero and one")
    lo = max(1, observed_errors + 1)
    hi = lo
    while hi < maximum and clopper_pearson_upper(observed_errors, hi, confidence) > ceiling:
        hi = min(maximum, hi * 2)
    if clopper_pearson_upper(observed_errors, hi, confidence) > ceiling:
        raise ValueError("required sample size exceeds maximum")
    while lo < hi:
        mid = (lo + hi) // 2
        if clopper_pearson_upper(observed_errors, mid, confidence) <= ceiling:
            hi = mid
        else:
            lo = mid + 1
    return lo


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def evaluate_batch_quality(*, sample_size: int, error_count: int,
                           conflict_count: int, auto_resolved_count: int,
                           auto_resolved_correct_count: int | None,
                           major_error_count: int | None,
                           common_wrong_agreement_count: int | None,
                           agreement: dict[str, Any] | None,
                           policy: GatePolicy | None = None) -> dict[str, Any]:
    policy = policy or GatePolicy()
    upper = clopper_pearson_upper(error_count, sample_size, policy.confidence)
    coverage = _ratio(auto_resolved_count, conflict_count)
    accuracy = (_ratio(auto_resolved_correct_count, auto_resolved_count)
                if auto_resolved_correct_count is not None else None)

    result: dict[str, Any] = {
        "sampleSize": sample_size,
        "errorCount": error_count,
        "errorRateUpper95": upper,
        "errorRateMethod": "clopper-pearson-one-sided-95",
        "deterministicResolution": {
            "conflictCount": conflict_count,
            "autoResolvedCount": auto_resolved_count,
            "coverage": coverage,
            "accuracy": accuracy,
            "commonWrongAgreementCount": common_wrong_agreement_count,
        },
        "majorErrorCount": major_error_count,
        "agreement": agreement,
        "policy": {
            "errorRateCeiling": policy.error_rate_ceiling,
            "ac1PointMin": policy.ac1_point_min,
            "ac1LowerMin": policy.ac1_lower_min,
            "coverageMin": policy.deterministic_coverage_min,
            "accuracyMin": policy.deterministic_accuracy_min,
            "majorErrorMax": policy.major_error_max,
        },
    }

    missing_gold = (accuracy is None or major_error_count is None
                    or common_wrong_agreement_count is None)
    missing_agreement_evidence = bool(
        agreement is not None and not agreement.get("modelAssumptions")
    )
    if missing_gold or missing_agreement_evidence:
        result["decision"] = "insufficient-evidence"
        return result

    checks = [
        upper <= policy.error_rate_ceiling,
        coverage is not None and coverage >= policy.deterministic_coverage_min,
        accuracy >= policy.deterministic_accuracy_min,
        major_error_count <= policy.major_error_max,
        common_wrong_agreement_count <= policy.common_wrong_agreement_max,
    ]
    if agreement is not None:
        checks.extend([
            agreement.get("gwetAC1", -1) >= policy.ac1_point_min,
            agreement.get("ciLower95", -1) >= policy.ac1_lower_min,
        ])
    result["decision"] = "pass" if all(checks) else "fail"
    return result
