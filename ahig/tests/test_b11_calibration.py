"""B.11 碳水化合物策略與肝醣管理：凍結校準契約。

本檔驗證的是**契約本身**，不是文獻。分四個層次：

1. **量綱註冊表**：B.11 專屬量綱通過 schema，且所有註冊表可合併成單一命名空間
   （ID 不得碰撞）——裁決層只有一個查表入口。
2. **危險的相等**：肝醣乾重與濕重的 UCUM code 完全相同（``mmol/kg``）卻相差
   四倍餘。契約必須讓自動換算在此止步，而不是靠抽取者記得。
3. **範圍契約**：凍結雜湊自我驗證、時窗與劑量帶無重疊、GI harms 是
   in-scope critical outcome 而非只在廉價 inventory 裡、REDs/LEA/快速減重
   在排除條件內。
4. **抽樣框**：分層配額加總等於總篇數，且每層的閘門宣稱與 Clopper–Pearson
   實算一致——不接受「60 篇可證明 1% 錯誤率」這類數字。
"""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from ahig.contracts import freeze
from ahig.gates.quality_gate import clopper_pearson_upper
from ahig.scope import matcher as sm
from ahig.stats import adjudication as adj

ROOT = Path(__file__).resolve().parents[1]
CAL = ROOT / "calibration" / "b11-carbohydrate"
CONTRACT_PATH = CAL / "scope-contract.json"
STRATA_PATH = CAL / "strata.json"
QK_PATH = ROOT / "registry" / "quantity-kinds.b11-carbohydrate.json"

SCOPE_SCHEMA = json.loads(
    (ROOT / "schema" / "extraction-scope-contract.schema.json").read_text(
        encoding="utf-8"))
QK_SCHEMA = json.loads(
    (ROOT / "schema" / "quantity-kind-registry.schema.json").read_text(
        encoding="utf-8"))


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


# ===========================================================================
# 1. 量綱註冊表
# ===========================================================================

def test_b11_quantity_kinds_validate():
    v = Draft202012Validator(QK_SCHEMA)
    for entry in load(QK_PATH)["entries"]:
        errs = sorted(v.iter_errors(entry), key=lambda e: list(e.path))
        assert not errs, (f"{entry['quantityKindId']}: "
                          f"{list(errs[0].path)} — {errs[0].message}")


def test_quantity_kind_ids_do_not_collide_across_registries():
    """裁決層只有一個查表入口；ID 碰撞會讓後載入者靜默覆蓋前者。"""
    ids: list[str] = []
    for path in sorted((ROOT / "registry").glob("quantity-kinds.*.json")):
        ids += [e["quantityKindId"] for e in load(path)["entries"]]
    assert len(ids) == len(set(ids)), \
        f"重複的 quantityKindId：{sorted({i for i in ids if ids.count(i) > 1})}"


def test_adjudication_layer_can_see_b11_quantity_kinds():
    """契約寫了量綱但裁決層看不到，等於沒有 blockingConditions。"""
    for qk in ("ahig:qk:muscle-glycogen-dry-weight",
               "ahig:qk:exogenous-cho-oxidation-rate",
               "ahig:qk:gi-symptom-incidence"):
        assert adj.quantity_kind_entry(qk) is not None, f"{qk} 未被裁決層載入"


def test_adjudication_layer_still_sees_the_base_registry():
    """新增領域註冊表不得讓既有的量綱消失。"""
    assert adj.quantity_kind_entry("ahig:qk:vo2max-relative") is not None


def test_colliding_registries_raise_instead_of_silently_overwriting():
    """靜默覆蓋會讓 blockingConditions 取決於檔名排序——最難察覺的閘門失效。"""
    import tempfile

    original_dir, original_cache = adj._REGISTRY_DIR, adj._REGISTRY_CACHE
    try:
        with tempfile.TemporaryDirectory() as tmp:
            entry = {"quantityKindId": "ahig:qk:duplicated", "label": "x",
                     "representation": {"kind": "ucum", "ucumCode": "g"},
                     "comparabilityClass": "c",
                     "crossStudyComparability": {"level": "directly-comparable"}}
            for name in ("quantity-kinds.a.json", "quantity-kinds.b.json"):
                (Path(tmp) / name).write_text(
                    json.dumps({"entries": [entry]}), encoding="utf-8")
            adj._REGISTRY_DIR, adj._REGISTRY_CACHE = Path(tmp), None
            try:
                adj.quantity_kind_entry("ahig:qk:duplicated")
            except adj.QuantityKindCollision:
                return
            raise AssertionError("重複的 quantityKindId 必須拋出，不得靜默覆蓋")
    finally:
        adj._REGISTRY_DIR, adj._REGISTRY_CACHE = original_dir, original_cache


# ===========================================================================
# 2. 危險的相等：乾重 vs 濕重
# ===========================================================================

def test_glycogen_bases_share_a_ucum_code_but_not_a_comparability_class():
    entries = {e["quantityKindId"]: e for e in load(QK_PATH)["entries"]}
    dry = entries["ahig:qk:muscle-glycogen-dry-weight"]
    wet = entries["ahig:qk:muscle-glycogen-wet-weight"]
    assert (dry["representation"]["ucumCode"]
            == wet["representation"]["ucumCode"] == "mmol/kg")
    assert dry["comparabilityClass"] != wet["comparabilityClass"]


def test_wet_basis_glycogen_blocks_automatic_conversion():
    """單位字串相同時，naive 比對會直接判定兩值不一致並選一個勝出。
    這裡要求它升級人工而不是自作主張。"""
    ctx = {"quantityKinds": {"glycogen": "ahig:qk:muscle-glycogen-wet-weight"}}
    r = adj.adjudicate_field("glycogen", {"value": 400, "unit": "mmol/kg"},
                             {"value": 90, "unit": "mmol/kg"}, ctx)
    assert r.outcome == adj.ESCALATE


def test_both_glycogen_kinds_declare_the_basis_blocking_condition():
    for entry in load(QK_PATH)["entries"]:
        if "glycogen" not in entry["quantityKindId"]:
            continue
        blocking = entry["crossStudyComparability"].get("blockingConditions") or []
        assert "basis-differs-dry-vs-wet" in blocking, entry["quantityKindId"]


def test_tt_and_tte_are_separate_comparability_classes():
    """兩者都是「秒」，但測的是不同構念，不得併入同一效果量。"""
    entries = {e["quantityKindId"]: e for e in load(QK_PATH)["entries"]}
    tt = entries["ahig:qk:time-trial-completion-time"]
    tte = entries["ahig:qk:time-to-exhaustion"]
    assert tt["representation"]["ucumCode"] == tte["representation"]["ucumCode"] == "s"
    assert tt["comparabilityClass"] != tte["comparabilityClass"]


def test_absolute_and_per_mass_intake_rates_are_separate_classes():
    entries = {e["quantityKindId"]: e for e in load(QK_PATH)["entries"]}
    assert (entries["ahig:qk:cho-intake-rate-absolute"]["comparabilityClass"]
            != entries["ahig:qk:cho-intake-rate-per-mass"]["comparabilityClass"])


def test_gi_incidence_is_recorded_as_counts_not_percentages():
    """ADJ-004 的 crude 2×2 重算需要事件數；只有百分比就無法重算裁決。"""
    entry = {e["quantityKindId"]: e for e in load(QK_PATH)["entries"]}[
        "ahig:qk:gi-symptom-incidence"]
    assert entry["representation"]["kind"] == "dimensionless-count"
    assert "denominator-not-reported" in (
        entry["crossStudyComparability"]["blockingConditions"])


# ===========================================================================
# 3. 範圍契約
# ===========================================================================

def test_contract_validates_against_schema():
    errs = sorted(Draft202012Validator(SCOPE_SCHEMA).iter_errors(load(CONTRACT_PATH)),
                  key=lambda e: list(e.path))
    assert not errs, f"{list(errs[0].path)} — {errs[0].message}"


def test_contract_is_frozen_and_hash_self_verifies():
    c = load(CONTRACT_PATH)
    assert c["status"] == "frozen" and c.get("frozenAt")
    assert freeze.verify_frozen(c, "scopeContractHash"), \
        "已凍結契約的雜湊必須能自我驗證，否則凍結沒有效力"


def test_contract_passes_freeze_preflight():
    """SCOPE-002b 必須在凍結前為 0：契約層的時窗重疊不是資料品質問題。"""
    assert freeze.freeze_preflight(load(CONTRACT_PATH)) == []


def test_contract_is_accepted_by_the_matcher():
    sm.ScopeMatcher(load(CONTRACT_PATH))            # 不得拋出


def test_gi_harms_is_an_in_scope_critical_outcome():
    """GI harms 若只留在廉價 inventory，就不會進 SoF 表也不會被 GRADE 評級。"""
    outcomes = {o["outcomeId"]: o for o in load(CONTRACT_PATH)["inScopeOutcomes"]}
    gi = [o for oid, o in outcomes.items() if "gi-" in oid]
    assert gi, "契約必須把 GI harms 列為 in-scope outcome"
    assert any(o["role"] == "critical" for o in gi), \
        "GI harms 必須至少有一項是 critical"


def test_every_in_scope_outcome_points_at_a_registered_quantity_kind():
    for o in load(CONTRACT_PATH)["inScopeOutcomes"]:
        assert adj.quantity_kind_entry(o["quantityKind"]) is not None, \
            f"{o['outcomeId']} 指向未註冊的量綱 {o['quantityKind']}"


def test_safety_critical_branches_are_excluded_by_the_research_question():
    """REDs／LEA／快速減重屬 safety-critical 分支，需各自的範圍契約與人工裁決
    資格，不得混進本校準集。"""
    exclusions = (load(CONTRACT_PATH)["researchQuestion"]["population"]
                  .get("exclusionCriteria") or [])
    joined = " ".join(exclusions).lower()
    for token in ("red-s", "low energy availability", "rapid weight"):
        assert token in joined, f"排除條件缺少 {token}（現有：{joined}）"


def test_mid_unavailable_outcomes_are_declared_as_null_not_invented():
    """沒有共識 MID 的 outcome 必須顯性寫 null，讓 GRADE 走 midUnavailable
    路徑；捏造一個門檻會讓 imprecision 評級看起來 contextualised。"""
    outcomes = load(CONTRACT_PATH)["inScopeOutcomes"]
    assert any(o.get("midRef") is None for o in outcomes), \
        "至少要有一個 outcome 顯性宣告 midRef=null"


def test_out_of_scope_results_are_recorded_never_discarded():
    policy = load(CONTRACT_PATH)["extractionPolicy"]
    assert policy["onOutOfScope"] == "record-in-outcome-inventory-only"
    assert policy["onExceedMax"] == "escalate"


def test_contract_declares_a_direction_of_benefit_for_every_outcome():
    """方向缺失會讓 TT（越短越好）與 TTE（越長越好）在合成時同號相加。"""
    for o in load(CONTRACT_PATH)["inScopeOutcomes"]:
        assert o.get("directionOfBenefit"), f"{o['outcomeId']} 未宣告方向性"


# ===========================================================================
# 4. 抽樣框
# ===========================================================================

def test_strata_quotas_sum_to_the_declared_total():
    s = load(STRATA_PATH)
    assert sum(x["quota"] for x in s["strata"]) == s["totalSampleSize"]


def test_strata_pin_the_current_contract_hash():
    """契約改版而抽樣框沒跟上時，兩份檔案各自都合法——只有交叉比對抓得到。"""
    assert (load(STRATA_PATH)["scopeContractHash"]
            == load(CONTRACT_PATH)["scopeContractHash"]), \
        "抽樣框釘住的雜湊已過期；改契約後須同步更新 strata.json"


def test_strata_reference_only_contract_declared_axes():
    """抽樣框若引用契約沒有的 outcome，配額就無法被實際抽取滿足。"""
    declared = {o["outcomeId"] for o in load(CONTRACT_PATH)["inScopeOutcomes"]}
    for stratum in load(STRATA_PATH)["strata"]:
        unknown = set(stratum.get("primaryOutcomes") or []) - declared
        assert not unknown, f"{stratum['stratumId']} 引用未宣告的 outcome：{unknown}"


def test_scope_gold_targets_are_declared():
    g = load(STRATA_PATH)["scopeGoldTargets"]
    assert g["scopeRecallMin"] >= 0.95
    assert g["falseExclusionRateMax"] <= 0.05
    assert g["criticalHarmsFalseExclusionMax"] == 0


def test_multiple_measurements_within_window_is_measured_not_pre_passed():
    """SCOPE-002c 是資料端現象，凍結前無從得知比率；只能量測不能先設門檻。"""
    g = load(STRATA_PATH)["scopeGoldTargets"]
    assert g["multipleMeasurementsWithinWindow"]["mode"] == "measure-only"
    assert "threshold" not in g["multipleMeasurementsWithinWindow"]


def test_declared_error_ceiling_matches_clopper_pearson_at_this_sample_size():
    """60 篇能證明什麼，由精確上界決定，不由期望決定。"""
    s = load(STRATA_PATH)
    n = s["totalSampleSize"]
    claimed = s["scopeGoldTargets"]["provableErrorRateUpperBoundAtZeroErrors"]
    actual = clopper_pearson_upper(0, n, confidence=s["scopeGoldTargets"]["confidence"])
    assert abs(claimed - actual) < 5e-5, f"宣稱 {claimed} vs 實算 {actual}"


def test_calibration_does_not_claim_the_one_percent_ceiling():
    """1% 錯誤率上界需要 n=299；60 篇宣稱達標即是誤導。"""
    s = load(STRATA_PATH)
    assert s["scopeGoldTargets"]["provableErrorRateUpperBoundAtZeroErrors"] > 0.01
    assert s["scopeGoldTargets"]["sufficientForOnePercentCeiling"] is False


def test_strata_cover_both_performance_and_harms():
    kinds = {s["stratumKind"] for s in load(STRATA_PATH)["strata"]}
    assert {"performance", "harms"} <= kinds


def test_no_literature_was_acquired():
    """本票只凍結契約與抽樣框。出現具體 DOI/PMID 代表已經越界去取文獻。"""
    text = STRATA_PATH.read_text(encoding="utf-8")
    for token in ("doi.org", "10.1101/", "10.64898/", "pubmed", "PMID", "PMC"):
        assert token not in text, f"抽樣框不應包含具體文獻識別碼：{token}"
