from pathlib import Path

from ahig.scope import matcher as sm
from ahig.stats import adjudication as adj
from ahig.stats import family as sf
from ahig.stats import grade as gd


# ===========================================================================
# ScopeMatcher
# ===========================================================================

def base_contract(**over):
    c = {
        "scopeContractId": "ahig:scope:creatine-strength",
        "version": "1.0.0",
        "status": "frozen",
        "scopeContractHash": "sha256:" + "0" * 64,
        "canonicalCompetency": ["ahig:cc:creatine-supplementation"],
        "derivedFromSearchContract": {"searchContractId": "sc-1", "version": "1.0.0",
                                      "hash": "sha256:" + "1" * 64},
        "researchQuestion": {
            "population": {"label": "resistance-trained adults"},
            "interventionOrExposure": {
                "label": "creatine monohydrate",
                "doseBands": [{"bandId": "maintenance", "min": 3, "max": 5, "unit": "g"},
                              {"bandId": "loading", "min": 20, "max": 25, "unit": "g"}],
            },
            "comparator": {"types": ["placebo"]},
            "questionType": "efficacy",
        },
        "inScopeOutcomes": [
            {"outcomeId": "1rm-squat", "label": "1RM squat", "role": "critical",
             "quantityKind": "ahig:qk:pct-1rm", "comparabilityClass": "relative-load",
             "allowedInstruments": ["barbell-back-squat"]},
            {"outcomeId": "lean-mass", "label": "lean body mass", "role": "important",
             "quantityKind": "ahig:qk:dose-per-body-mass-daily",
             "comparabilityClass": "body-composition", "allowedInstruments": []},
        ],
        "inScopeTimepoints": [
            {"timepointId": "wk4", "label": "4 weeks", "windowStart": 3,
             "windowEnd": 5, "unit": "week"},
            {"timepointId": "wk12", "label": "12 weeks", "windowStart": 10,
             "windowEnd": 14, "unit": "week"},
        ],
        "inScopeAnalysisSets": ["ITT"],
        "inScopeEffectMeasures": ["MD", "SMD"],
        "inScopeStatisticalModels": ["unadjusted", "adjusted-prespecified"],
        "extractionPolicy": {
            "subgroupPolicy": "prespecified-only",
            "sensitivityAnalysisPolicy": "exclude",
            "adjustedModelPolicy": "primary-model-only",
            "onOutOfScope": "record-in-outcome-inventory-only",
            "maxStudyResultsPerStudy": 4,
            "onExceedMax": "escalate",
        },
        "outcomeInventoryPolicy": {"required": True,
                                   "completeness": "all-reported-outcomes"},
        "provenance": {"authoredBy": "x", "createdAt": "2026-08-13T00:00:00Z",
                       "approvedBy": [{"agent": "aaron", "agentClass": "human-self",
                                       "at": "2026-08-13T00:00:00Z"}]},
    }
    c.update(over)
    return c


def reported(**over):
    r = {"localLabel": "1RM back squat", "normalisedOutcomeRef": "1rm-squat",
         "instrument": "barbell-back-squat", "hasNumericResult": True,
         "timepointDays": 28, "analysisSet": "ITT", "effectMeasure": "MD",
         "statisticalModel": "unadjusted", "dose": 5, "doseUnit": "g"}
    r.update(over)
    return r


def test_scope_requires_frozen_contract():
    c = base_contract(status="draft")
    try:
        sm.ScopeMatcher(c)
        raise AssertionError("應拒絕未凍結的契約")
    except ValueError:
        pass


def test_in_scope_basic():
    m = sm.ScopeMatcher(base_contract())
    d = m.decide(reported())
    assert d.in_scope and d.reason_code == "in-scope"
    assert d.matched["timepointId"] == "wk4"
    assert d.matched["doseBandId"] == "maintenance"


def test_timepoint_outside_window_excluded():
    m = sm.ScopeMatcher(base_contract())
    d = m.decide(reported(timepointDays=56))       # 8 週，落在兩個時窗之間
    assert not d.in_scope
    assert d.reason_code == "notExtracted-timepoint-outside-window"


def test_analysis_set_out_of_scope():
    m = sm.ScopeMatcher(base_contract())
    d = m.decide(reported(analysisSet="PP"))
    assert d.reason_code == "notExtracted-analysis-set-not-in-scope"


def test_instrument_allowlist_enforced():
    m = sm.ScopeMatcher(base_contract())
    d = m.decide(reported(instrument="smith-machine-squat"))
    assert d.reason_code == "notExtracted-instrument-not-in-allowlist"


def test_unknown_outcome_excluded():
    m = sm.ScopeMatcher(base_contract())
    d = m.decide(reported(normalisedOutcomeRef="vo2max"))
    assert d.reason_code == "notExtracted-outcome-not-in-scope"


def test_subgroup_policy_prespecified_only():
    m = sm.ScopeMatcher(base_contract())
    assert m.decide(reported(isSubgroup=True, subgroupPrespecified=False)).reason_code \
        == "notExtracted-subgroup-excluded-by-policy"
    assert m.decide(reported(isSubgroup=True, subgroupPrespecified=True)).in_scope


def test_sensitivity_analysis_excluded_by_default():
    m = sm.ScopeMatcher(base_contract())
    assert m.decide(reported(isSensitivityAnalysis=True)).reason_code \
        == "notExtracted-sensitivity-analysis-excluded-by-policy"


def test_dose_outside_bands_excluded():
    m = sm.ScopeMatcher(base_contract())
    assert m.decide(reported(dose=10, doseUnit="g")).reason_code \
        == "notExtracted-dose-outside-bands"


def test_no_numeric_result_excluded():
    m = sm.ScopeMatcher(base_contract())
    assert m.decide(reported(hasNumericResult=False)).reason_code \
        == "notExtracted-no-numeric-result"


def test_multiple_measurements_in_window_escalates_not_guesses():
    m = sm.ScopeMatcher(base_contract())
    d = m.decide(reported(multipleMeasurementsInWindow=True))
    assert not d.in_scope
    assert d.reason_code == "escalated-multiple-matches-in-window"


def test_scope_reduces_studyresult_count_dramatically():
    """核心主張：同一篇論文在無範圍契約下會產生數十個 StudyResult，
    在範圍契約下只產生少數幾個。"""
    m = sm.ScopeMatcher(base_contract())
    outcomes = ["1rm-squat", "lean-mass", "vo2max", "bench-1rm", "body-fat"]
    days = [14, 28, 56, 84, 180]
    sets = ["ITT", "PP"]
    models = ["unadjusted", "adjusted-posthoc"]
    inv = {"inventoryId": "inv-1", "reportedOutcomes": []}
    for o in outcomes:
        for d in days:
            for s in sets:
                for mo in models:
                    inv["reportedOutcomes"].append(reported(
                        normalisedOutcomeRef=o, timepointDays=d,
                        analysisSet=s, statisticalModel=mo,
                        instrument=("barbell-back-squat" if o == "1rm-squat" else None)))
    total = len(inv["reportedOutcomes"])          # 5*5*2*2 = 100
    res = m.decide_inventory(inv)
    assert total == 100
    # 只有 (1rm-squat 或 lean-mass) × (wk4 或 wk12) × ITT × unadjusted = 4
    assert res["candidateCount"] == 4
    assert res["candidateCount"] / total < 0.05


def test_exceeding_max_escalates_rather_than_truncates():
    c = base_contract()
    c["extractionPolicy"]["maxStudyResultsPerStudy"] = 2
    m = sm.ScopeMatcher(c)
    inv = {"inventoryId": "inv-2", "reportedOutcomes": [
        reported(normalisedOutcomeRef=o, timepointDays=d, instrument=(
            "barbell-back-squat" if o == "1rm-squat" else None))
        for o in ("1rm-squat", "lean-mass") for d in (28, 84)]}
    res = m.decide_inventory(inv)
    assert res["escalated"]
    assert res["inScopeCount"] == 0
    assert all(not d["inScope"] for d in res["decisions"])
    assert {d["reasonCode"] for d in res["decisions"]} == {
        "escalated-exceeds-max-studyresults"}


def test_backfill_finds_newly_in_scope_without_rereading():
    old = sm.ScopeMatcher(base_contract())
    c2 = base_contract()
    c2["version"] = "1.1.0"
    c2["inScopeAnalysisSets"] = ["ITT", "PP"]
    new = sm.ScopeMatcher(c2)
    inv = {"inventoryId": "inv-3", "reportedOutcomes": [
        reported(analysisSet="ITT"), reported(analysisSet="PP")]}
    cand = sm.backfill_candidates(inv, old, new)
    assert len(cand) == 1
    assert cand[0]["previousReason"] == "notExtracted-analysis-set-not-in-scope"


def test_canonical_hash_is_stable_and_order_independent():
    a = sm.canonical_hash({"x": 1, "y": [1, 2]})
    b = sm.canonical_hash({"y": [1, 2], "x": 1})
    assert a == b and a.startswith("sha256:")


# ===========================================================================
# StudyFamily
# ===========================================================================

def R(wid, **kw):
    return sf.Report(work_id=wid, **kw)


def test_registry_id_normalisation():
    assert sf.normalise_registry_id(" nct01234567 ") == "NCT01234567"
    assert sf.normalise_registry_id("NCT-123") is None
    assert sf.normalise_registry_id(None) is None


def test_author_normalisation():
    assert sf.normalise_author("Smith, John A.") == "smith|J"
    assert sf.normalise_author("John A. Smith") == "smith|J"


def test_tier1_same_registry_auto_merges():
    a = R("w1", registry_id="NCT01234567", authors=["Smith J"])
    b = R("w2", registry_id="NCT01234567", authors=["Jones K"])
    assert sf.classify_pair(a, b)["tier"] == "tier1-deterministic"
    fam = sf.build_families([a, b])
    assert len(fam["families"]) == 1
    members = fam["families"][0]["members"]
    assert sum(m["contributesEvidence"] for m in members) == 1


def test_tier2_not_auto_merged():
    a = R("w1", sample_size=24, recruitment_start="2020-01-01",
          recruitment_end="2020-06-01", country_or_site="Taipei",
          authors=["Smith J", "Lee C"])
    b = R("w2", sample_size=24, recruitment_start="2020-01-01",
          recruitment_end="2020-06-01", country_or_site="Taipei",
          authors=["Lee C", "Smith J"])
    assert sf.classify_pair(a, b)["tier"] == "tier2-strong-heuristic"
    fam = sf.build_families([a, b])
    assert fam["families"] == []
    assert len(fam["suspectedPairs"]) == 1


def test_suspected_deferred_when_not_claim_supporting():
    a = R("w1", sample_size=24, recruitment_start="2020-01-01",
          recruitment_end="2020-06-01", country_or_site="Taipei")
    b = R("w2", sample_size=24, recruitment_start="2020-01-01",
          recruitment_end="2020-06-01", country_or_site="Taipei")
    fam = sf.build_families([a, b], claim_supporting=set())
    assert fam["humanQueueSize"] == 0
    assert fam["deferredCount"] == 1
    assert fam["suspectedPairs"][0]["status"] == "deferred-not-claim-supporting"


def test_suspected_enters_human_queue_when_claim_supporting():
    a = R("w1", sample_size=24, recruitment_start="2020-01-01",
          recruitment_end="2020-06-01", country_or_site="Taipei")
    b = R("w2", sample_size=24, recruitment_start="2020-01-01",
          recruitment_end="2020-06-01", country_or_site="Taipei")
    fam = sf.build_families([a, b], claim_supporting={"w1"})
    assert fam["humanQueueSize"] == 1


def test_unrelated_reports_produce_no_family():
    a = R("w1", sample_size=20, authors=["Smith J"], publication_year=2015)
    b = R("w2", sample_size=88, authors=["Wu T"], publication_year=2023)
    assert sf.classify_pair(a, b)["tier"] == "none"
    assert sf.build_families([a, b])["families"] == []


def test_claim_duplicate_flag_caps_certainty():
    a = R("w1", registry_id="NCT01234567")
    b = R("w2", registry_id="NCT01234567")
    fam = sf.build_families([a, b])
    flag = sf.claim_duplicate_flag(["w1", "w2", "w3"], fam)
    assert flag["possibleDuplicateEvidence"]
    assert flag["certaintyCeiling"] == "moderate"


def test_claim_without_duplicates_is_clean():
    a = R("w1", registry_id="NCT01234567")
    b = R("w2", registry_id="NCT07654321")
    fam = sf.build_families([a, b])
    flag = sf.claim_duplicate_flag(["w1", "w2"], fam)
    assert not flag["possibleDuplicateEvidence"]


# ===========================================================================
# GRADE
# ===========================================================================

def test_meta_analysis_homogeneous_gives_low_i2():
    eff = [0.20, 0.22, 0.18, 0.21]
    var = [0.01] * 4
    ma = gd.meta_analyse_dl(eff, var)
    assert ma["I2"] < 25
    assert abs(ma["pooled"] - 0.2025) < 0.01


def test_meta_analysis_heterogeneous_gives_high_i2():
    eff = [0.10, 0.90, 0.15, 0.85]
    var = [0.005] * 4
    ma = gd.meta_analyse_dl(eff, var)
    assert ma["I2"] > 75
    assert ma["tau2"] > 0


def test_inconsistency_rating_scales_with_i2():
    low = gd.rate_inconsistency([0.20, 0.22, 0.18, 0.21], [0.01] * 4)
    high = gd.rate_inconsistency([0.10, 0.90, 0.15, 0.85], [0.005] * 4)
    assert low.proposed == gd.NOT_SERIOUS
    assert high.proposed == gd.VERY_SERIOUS


def test_single_study_flagged_not_rated():
    r = gd.rate_inconsistency([0.2], [0.01])
    assert "single-study-evidence" in r.flags
    # v2.1：「無異質性可評」不得被讀成「一致性良好」
    assert r.proposed == gd.INDETERMINATE


def test_k_less_than_3_requires_human_confirmation():
    r = gd.rate_inconsistency([0.20, 0.22], [0.01, 0.01])
    assert r.requires_human_confirmation
    assert "k<3-I2-unstable" in r.flags
    # v2.1：指標不可信時不給方向性建議，且必須經人工明確確認
    assert r.proposed == gd.INDETERMINATE
    assert "k<3-I2-unstable" in r.requires_acknowledgement


def test_imprecision_without_mid_is_flagged_not_silently_defaulted():
    r = gd.rate_imprecision(-0.1, 0.5, total_n=200, mid=None, mid_status="unavailable")
    assert "midUnavailable" in r.flags
    assert r.requires_human_confirmation
    # v2.1：無 MID 就不是 contextualised 評級，且該旗標必須被人工確認
    assert r.computed["contextualised"] is False
    assert "midUnavailable" in r.requires_acknowledgement


def test_imprecision_ci_spanning_both_mids_is_very_serious():
    r = gd.rate_imprecision(-0.6, 0.6, total_n=1000, mid=0.5,
                            mid_status="registered", ois=500)
    assert r.proposed == gd.VERY_SERIOUS


def test_imprecision_precise_estimate_not_serious():
    r = gd.rate_imprecision(0.30, 0.50, total_n=1000, mid=0.10,
                            mid_status="registered", ois=500)
    assert r.proposed == gd.NOT_SERIOUS


def test_imprecision_below_ois_downgrades():
    a = gd.rate_imprecision(0.30, 0.50, total_n=1000, mid=0.10,
                            mid_status="registered", ois=500)
    b = gd.rate_imprecision(0.30, 0.50, total_n=100, mid=0.10,
                            mid_status="registered", ois=500)
    assert gd.DOWNGRADE[b.proposed] > gd.DOWNGRADE[a.proposed]


def test_ois_binary_sanity():
    # 對照組風險 0.20、RRR 0.25 -> 需要相當大的樣本
    n = gd.optimal_information_size_binary(0.20, 0.25)
    assert 1000 < n < 4000


def test_ois_continuous_sanity():
    # MID = 0.5 SD -> 每組約 63，總計約 126
    n = gd.optimal_information_size_continuous(mid=0.5, sd=1.0)
    assert 120 < n < 135


def test_publication_bias_not_applicable_below_k10():
    r = gd.rate_publication_bias([0.1] * 5, [0.1] * 5)
    assert "k<10-egger-not-applicable" in r.flags
    assert r.requires_human_confirmation
    # v2.1：「檢定不出來」不得回落 not-serious
    assert r.proposed == gd.INDETERMINATE
    assert "egger" not in r.computed


def test_publication_bias_detects_asymmetry():
    # 小型研究效果大、大型研究效果小 —— 典型漏斗圖不對稱
    se = [0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.04, 0.03]
    eff = [1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.5, 0.4, 0.25, 0.15, 0.12, 0.1]
    r = gd.rate_publication_bias(eff, se)
    assert r.proposed in (gd.SERIOUS, gd.VERY_SERIOUS)
    assert r.computed["egger"]["p"] < 0.10


def test_publication_bias_symmetric_funnel_passes():
    se = [0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05]
    eff = [0.52, 0.47, 0.50, 0.49, 0.51, 0.48, 0.50, 0.51, 0.49, 0.50]
    r = gd.rate_publication_bias(eff, se)
    assert r.proposed == gd.NOT_SERIOUS


def test_certainty_blocked_when_domain_missing():
    out = gd.propose_certainty("RCT-parallel", {"risk-of-bias": gd.NOT_SERIOUS})
    assert out["blocked"]


# v2.1：階梯算術不變，但裸的等級字串只能得到 advisoryCertainty。
# effectiveCertainty 需要 HumanDomainJudgement —— 見 test_grade_v21.py。

def test_certainty_high_when_all_clean():
    d = {k: gd.NOT_SERIOUS for k in gd.GRADE_DOMAINS}
    out = gd.propose_certainty("RCT-parallel", d)
    assert out["advisoryCertainty"] == "high"
    assert out["effectiveCertainty"] is None


def test_certainty_downgrades_accumulate():
    d = {"risk-of-bias": gd.SERIOUS, "inconsistency": gd.SERIOUS,
         "indirectness": gd.NOT_SERIOUS, "imprecision": gd.NOT_SERIOUS,
         "publication-bias": gd.NOT_SERIOUS}
    out = gd.propose_certainty("RCT-parallel", d)
    assert out["advisoryCertainty"] == "low"
    assert out["effectiveCertainty"] is None


def test_observational_starts_low():
    d = {k: gd.NOT_SERIOUS for k in gd.GRADE_DOMAINS}
    out = gd.propose_certainty("cohort-prospective", d)
    assert out["advisoryCertainty"] == "low"
    assert out["effectiveCertainty"] is None


def _human_judged_proposal(**ratings):
    """五個 domain 都有生效人類判斷的 proposal（一般風險層）。"""
    ind = gd.rate_imprecision(0.30, 0.50, total_n=1000, mid=0.10,
                              mid_status="registered", ois=500)
    j = {d: gd.HumanDomainJudgement(
            domain=d, rating=ratings.get(d, gd.NOT_SERIOUS),
            agent_class="human-expert", rationale="人工檢視後確認",
            acknowledged_flags=(list(ind.requires_acknowledgement)
                                if d == "imprecision" else []),
            indicators=(ind if d == "imprecision" else None))
         for d in gd.GRADE_DOMAINS}
    return gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")


def test_model_override_not_effective_for_approved_claim():
    p = _human_judged_proposal(imprecision=gd.SERIOUS, inconsistency=gd.SERIOUS)
    assert p["effectiveCertainty"] == "low"

    r = gd.apply_override(p, "imprecision", gd.NOT_SERIOUS, "model", "看起來夠精確")
    # v2.1：模型 override 只寫 advisory，且不得改動 effective 結果
    assert r["overrides"] == []
    assert r["advisoryOverrides"][0]["effectiveForApprovedClaim"] is False
    assert r["effectiveCertainty"] == p["effectiveCertainty"]
    assert r["perDomain"]["imprecision"] == gd.SERIOUS

    r2 = gd.apply_override(p, "imprecision", gd.NOT_SERIOUS, "human-expert",
                           "OIS 已達")
    assert r2["overrides"][0]["effectiveForApprovedClaim"] is True
    assert r2["effectiveCertainty"] == "moderate"


# ===========================================================================
# Adjudication
# ===========================================================================

def test_no_conflict():
    r = adj.adjudicate_field("x", {"value": 1}, {"value": 1}, {})
    assert r.outcome == adj.NO_CONFLICT


def test_text_normalisation_resolves():
    r = adj.adjudicate_field("populationLabel", {"value": "Trained  Males"},
                             {"value": "trained males"}, {})
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.rule_id == "ADJ-001-text-normalisation"


def test_enum_synonym_resolves():
    r = adj.adjudicate_field("analysisSet", {"value": "intention-to-treat"},
                             {"value": "ITT"}, {})
    assert r.outcome == adj.AUTO_RESOLVED and r.value == "ITT"


def test_effect_measure_synonym_resolves():
    r = adj.adjudicate_field("effectMeasure", {"value": "Risk Ratio"},
                             {"value": "RR"}, {})
    assert r.outcome == adj.AUTO_RESOLVED and r.value == "RR"


def test_unit_conversion_resolves():
    r = adj.adjudicate_field("dose", {"value": 5, "unit": "g"},
                             {"value": 5000, "unit": "mg"}, {})
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.rule_id == "ADJ-003-unit-conversion"


def test_undeclared_unit_pair_does_not_auto_resolve():
    r = adj.adjudicate_field("load", {"value": 5, "unit": "AU"},
                             {"value": 5000, "unit": "TRIMP"}, {})
    assert r.outcome == adj.ESCALATE


def test_numeric_recomputation_picks_the_self_consistent_side():
    ctx = {"effectMeasure": "RR",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100},
           "baseStudyResult": {"ciLow": 0.28, "ciHigh": 0.89, "pValue": 0.019}}
    r = adj.adjudicate_field("pointEstimate", {"value": 0.50}, {"value": 0.85}, ctx)
    assert r.outcome == adj.AUTO_RESOLVED
    assert r.winner == "A" and r.value == 0.50


def test_both_sides_failing_escalates_to_human_expert():
    ctx = {"effectMeasure": "RR",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100},
           "baseStudyResult": {"ciLow": 0.28, "ciHigh": 0.89, "pValue": 0.019}}
    r = adj.adjudicate_field("pointEstimate", {"value": 0.85}, {"value": 0.95}, ctx)
    assert r.outcome == adj.ESCALATE
    assert r.escalate_to == "human-expert"


def test_anchor_strength_resolves():
    """v2.1：anchor 只能定位非數值欄位，且必須有 verifiedBinding。
    數值欄位改由 test_numeric_field_is_never_decided_by_anchor_strength_alone
    （tests/test_adjudication_v21.py）涵蓋。"""
    bind = {"sourceHash": "sha256:" + "a" * 64, "field": "populationLabel",
            "outcome": "1rm-squat", "timepoint": "wk12", "arm": "intervention",
            "analysisSet": "ITT"}
    a = {"value": "resistance-trained men",
         "anchor": {"anchorMethod": "exact", "uniqueMatch": True,
                    "verifiedBinding": bind}}
    b = {"value": "recreational men",
         "anchor": {"anchorMethod": "fuzzy-accepted", "uniqueMatch": False,
                    "verifiedBinding": bind}}
    r = adj.adjudicate_field("populationLabel", a, b, {})
    assert r.outcome == adj.AUTO_RESOLVED and r.winner == "A"


def test_no_anchor_numeric_disagreement_escalates_to_human():
    r = adj.adjudicate_field("sampleSize", {"value": 42}, {"value": 24}, {})
    assert r.outcome == adj.ESCALATE
    assert r.escalate_to == "human-expert"
    assert r.rule_id == "ADJ-999-no-deterministic-basis"


def test_non_numeric_disagreement_escalates_to_third_model():
    r = adj.adjudicate_field("settingDescription", {"value": "university lab"},
                             {"value": "sports institute"}, {})
    assert r.escalate_to == "third-model"


def test_schema_violation_resolves():
    ctx = {"allowedValues": {"analysisSet": ["ITT", "PP"]}}
    r = adj.adjudicate_field("analysisSet", {"value": "ITT"},
                             {"value": "whatever"}, ctx)
    assert r.outcome == adj.AUTO_RESOLVED and r.winner == "A"


def test_null_vs_anchored_resolves():
    """v2.1：缺值方必須宣告 CANNOT_LOCATE（NOT_REPORTED 是實質主張，須升級），
    且有值方是非數值欄位時才可由已驗證 binding 的 anchor 勝出。"""
    bind = {"sourceHash": "sha256:" + "a" * 64, "field": "blinding",
            "outcome": "1rm-squat", "timepoint": "wk12", "arm": "intervention",
            "analysisSet": "ITT"}
    a = {"value": "double-blind",
         "anchor": {"anchorMethod": "exact", "uniqueMatch": True,
                    "verifiedBinding": bind}}
    b = {"value": None, "nullState": adj.CANNOT_LOCATE}
    r = adj.adjudicate_field("blinding", a, b, {})
    assert r.outcome == adj.AUTO_RESOLVED and r.winner == "A"


def test_null_vs_unanchored_escalates_to_human():
    r = adj.adjudicate_field("pointEstimate", {"value": 3.2}, {"value": None}, {})
    assert r.outcome == adj.ESCALATE and r.escalate_to == "human-self"


def test_adjudicate_record_reports_auto_resolution_rate():
    ctx = {"effectMeasure": "RR",
           "twoByTwo": {"a": 15, "n1": 100, "c": 30, "n2": 100},
           "baseStudyResult": {"ciLow": 0.28, "ciHigh": 0.89, "pValue": 0.019},
           "allowedValues": {"analysisSet": ["ITT", "PP"]}}
    fields = {
        "analysisSet": {"A": {"value": "intention-to-treat"}, "B": {"value": "ITT"}},
        "effectMeasure": {"A": {"value": "Risk Ratio"}, "B": {"value": "RR"}},
        "dose": {"A": {"value": 5, "unit": "g"}, "B": {"value": 5000, "unit": "mg"}},
        "pointEstimate": {"A": {"value": 0.50}, "B": {"value": 0.85}},
        "sampleSize": {"A": {"value": 200}, "B": {"value": 198}},
    }
    out = adj.adjudicate_record(fields, ctx)
    assert out["nConflicts"] == 5
    assert out["nAutoResolved"] == 4
    assert out["autoResolutionRate"] == 0.8
    assert len(out["escalatedToHuman"]) == 1


def test_majority_vote_never_used_for_numeric():
    """契約明確禁止以 2:1 多數決處理數值矛盾。
    本模組不含任何投票邏輯 —— 以介面層面驗證。"""
    src = (Path(__file__).resolve().parents[1] / "ahig" / "stats" / "adjudication.py").read_text(encoding="utf-8")
    for banned in ("majority", "vote(", "most_common", "Counter("):
        assert banned not in src, f"發現疑似投票邏輯：{banned}"


if __name__ == "__main__":
    from run_tests import main
    raise SystemExit(main([__file__]))
