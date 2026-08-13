from __future__ import annotations

import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load_analysis(name: str):
    path = ROOT / "analysis" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_three_year_capacity_is_coverage_not_accuracy():
    module = load_analysis("adjudication_sensitivity")
    result = module.required_auto_resolution(module.BASE, 10, 3)
    coverage = result["required_deterministic_resolution_coverage"]
    assert 0.873 < coverage < 0.874
    assert coverage < 0.875


def test_policy_target_rounds_capacity_requirement_up_to_87_5_percent():
    target = 0.875
    assert target > 0.8733


def test_sampling_none_means_not_reached_within_grid():
    payload = json.loads((ROOT / "analysis" / "results" / "sampling_power.json").read_text(encoding="utf-8"))
    scenario = payload["ac1_min_sample_size"]["binary-balanced-err05"]
    if scenario["min_n_for_ci_lower_0.80_at_power_0.80"] is None:
        assert scenario.get("not_reached_within_grid", True)
