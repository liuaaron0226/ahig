"""GRADE v2.1：indicators → human judgement → deterministic aggregation

v2 的 grade.py 把 I²、300 events、Egger p 值直接當成 final domain rating，
且 k<10 / Egger 失敗時回落到 not-serious —— 那是 fail-open。

v2.1 的契約：
  1. 三個可計算 domain 只產出 indicators + suggested judgement，不是 final rating。
  2. 統計量不可信時（k<10、Egger 奇異或失敗、資料不足）一律 indeterminate，
     且必須人工確認，絕不回落 not-serious。
  3. final certainty 只接受五個具「生效」humanDomainJudgement 的 domain。
     一般風險可 human-self；safety-critical 必須 human-expert。
  4. 模型 override 只寫 advisory，不動 effective domain 與 effectiveCertainty。
  5. provisional MID 不支援 high；unavailable MID 的 imprecision 不是
     contextualised 評級，必須人工說明 —— 但不發明新 GRADE 級別、不硬鎖 low。
"""

from __future__ import annotations

from contextlib import contextmanager

from ahig.stats import grade as gd


@contextmanager
def assert_raises(exc_type):
    try:
        yield
    except exc_type:
        return
    raise AssertionError(f"預期拋出 {exc_type.__name__}，但沒有")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def judgement(domain, rating=gd.NOT_SERIOUS, agent_class="human-expert",
              rationale="人工檢視後確認", acknowledged=None, indicators=None):
    return gd.HumanDomainJudgement(
        domain=domain, rating=rating, agent_class=agent_class,
        rationale=rationale, acknowledged_flags=list(acknowledged or []),
        indicators=indicators)


def registered_imprecision_indicators():
    return gd.rate_imprecision(0.30, 0.50, total_n=1000, mid=0.10,
                               mid_status="registered", ois=500)


def five_judgements(rating=gd.NOT_SERIOUS, agent_class="human-expert",
                    imprecision_indicators=None):
    ind = (imprecision_indicators if imprecision_indicators is not None
           else registered_imprecision_indicators())
    out = {}
    for d in gd.GRADE_DOMAINS:
        out[d] = judgement(
            d, rating=rating, agent_class=agent_class,
            acknowledged=(list(ind.requires_acknowledgement)
                          if d == "imprecision" else []),
            indicators=(ind if d == "imprecision" else None))
    return out


# ===========================================================================
# 1. 三個 domain 回傳 indicators，不是 final rating
# ===========================================================================

def test_inconsistency_returns_indicators_not_final_rating():
    r = gd.rate_inconsistency([0.20, 0.22, 0.18, 0.21], [0.01] * 4)
    assert isinstance(r, gd.DomainIndicators)
    assert r.domain == "inconsistency"
    assert r.suggested_judgement in gd.SUGGESTABLE
    assert r.human_judgement_required is True
    for key in ("I2", "tau2", "Q", "Q_p", "k"):
        assert key in r.indicators
    # 不得對外宣稱這是 final rating
    assert not hasattr(r, "final_rating")


def test_inconsistency_high_i2_suggests_very_serious_but_still_human_required():
    r = gd.rate_inconsistency([0.10, 0.90, 0.15, 0.85], [0.005] * 4)
    assert r.suggested_judgement == gd.VERY_SERIOUS
    assert r.human_judgement_required is True
    assert r.indicators["I2"] > 75


def test_inconsistency_low_i2_suggests_not_serious():
    r = gd.rate_inconsistency([0.20, 0.22, 0.18, 0.21], [0.01] * 4)
    assert r.suggested_judgement == gd.NOT_SERIOUS
    assert r.indicators["I2"] < 25


def test_imprecision_returns_indicators_not_final_rating():
    r = registered_imprecision_indicators()
    assert isinstance(r, gd.DomainIndicators)
    assert r.domain == "imprecision"
    assert r.human_judgement_required is True
    assert r.indicators["contextualised"] is True


def test_publication_bias_returns_indicators_not_final_rating():
    se = [0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05]
    eff = [0.52, 0.47, 0.50, 0.49, 0.51, 0.48, 0.50, 0.51, 0.49, 0.50]
    r = gd.rate_publication_bias(eff, se)
    assert isinstance(r, gd.DomainIndicators)
    assert r.human_judgement_required is True
    assert "egger" in r.indicators


def test_total_events_below_300_is_indicator_not_final_rating():
    r = gd.rate_imprecision(0.30, 0.50, total_n=1000, mid=0.10,
                            mid_status="registered", ois=500, total_events=120)
    assert r.indicators["total_events"] == 120
    assert "total-events<300" in r.flags
    assert r.human_judgement_required is True


# ===========================================================================
# 2. 資料不足一律 indeterminate，不得 not-serious fail-open
# ===========================================================================

def test_inconsistency_single_study_is_indeterminate_not_not_serious():
    r = gd.rate_inconsistency([0.2], [0.01])
    assert r.suggested_judgement == gd.INDETERMINATE
    assert r.suggested_judgement != gd.NOT_SERIOUS
    assert r.human_judgement_required is True
    assert "single-study-evidence" in r.flags
    assert "single-study-evidence" in r.requires_acknowledgement


def test_inconsistency_k2_is_indeterminate_and_requires_acknowledgement():
    r = gd.rate_inconsistency([0.20, 0.22], [0.01, 0.01])
    assert r.suggested_judgement == gd.INDETERMINATE
    assert r.human_judgement_required is True
    assert "k<3-I2-unstable" in r.flags
    assert "k<3-I2-unstable" in r.requires_acknowledgement


def test_publication_bias_k_below_10_is_indeterminate():
    r = gd.rate_publication_bias([0.1] * 5, [0.1] * 5)
    assert r.suggested_judgement == gd.INDETERMINATE
    assert r.suggested_judgement != gd.NOT_SERIOUS
    assert r.human_judgement_required is True
    assert "k<10-egger-not-applicable" in r.flags
    assert "k<10-egger-not-applicable" in r.requires_acknowledgement
    assert "egger" not in r.indicators


def test_publication_bias_k_below_10_records_unreported_trials_as_indicator():
    r = gd.rate_publication_bias([0.1] * 5, [0.1] * 5,
                                 all_registered_trials_reported=False)
    # 仍是 indeterminate（k<10 一律不可判定），但已知未發表試驗必須留在 indicators
    assert r.suggested_judgement == gd.INDETERMINATE
    assert r.indicators["all_registered_trials_reported"] is False
    assert "known-unreported-registered-trials" in r.flags


def test_publication_bias_singular_egger_is_indeterminate():
    # 所有 SE 相同 -> precision 欄位為常數，與截距共線，迴歸奇異
    r = gd.rate_publication_bias([0.3] * 12, [0.2] * 12)
    assert r.suggested_judgement == gd.INDETERMINATE
    assert r.suggested_judgement != gd.NOT_SERIOUS
    assert r.human_judgement_required is True
    assert any(f.startswith("egger-") for f in r.flags)
    assert any(f.startswith("egger-") for f in r.requires_acknowledgement)


def test_publication_bias_non_positive_se_is_indeterminate():
    se = [0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.0]
    eff = [0.52, 0.47, 0.50, 0.49, 0.51, 0.48, 0.50, 0.51, 0.49, 0.50]
    r = gd.rate_publication_bias(eff, se)
    assert r.suggested_judgement == gd.INDETERMINATE
    assert r.human_judgement_required is True


def test_publication_bias_length_mismatch_raises():
    with assert_raises(ValueError):
        gd.rate_publication_bias([0.1] * 10, [0.1] * 9)


def test_publication_bias_asymmetry_suggests_serious():
    se = [0.5, 0.45, 0.4, 0.35, 0.3, 0.25, 0.2, 0.15, 0.1, 0.05, 0.04, 0.03]
    eff = [1.2, 1.1, 1.0, 0.9, 0.8, 0.7, 0.5, 0.4, 0.25, 0.15, 0.12, 0.1]
    r = gd.rate_publication_bias(eff, se)
    assert r.suggested_judgement in (gd.SERIOUS, gd.VERY_SERIOUS)
    assert r.indicators["egger"]["p"] < 0.10
    assert r.human_judgement_required is True


def test_imprecision_unavailable_mid_without_ois_is_indeterminate():
    r = gd.rate_imprecision(0.30, 0.50, total_n=200, mid=None,
                            mid_status="unavailable", ois=None)
    # 既無 MID 也無 OIS，CI 不跨虛無值 —— 舊版會回 not-serious，那是 fail-open
    assert r.suggested_judgement == gd.INDETERMINATE
    assert r.suggested_judgement != gd.NOT_SERIOUS


# ===========================================================================
# 3. aggregation 只接受五個 effective humanDomainJudgement
# ===========================================================================

def test_aggregate_blocked_when_domain_missing():
    j = five_judgements()
    del j["publication-bias"]
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is True
    assert out["effectiveCertainty"] is None
    assert any("publication-bias" in r for r in out["blockReasons"])


def test_aggregate_blocked_when_judgement_is_bare_level_string():
    j = {d: gd.NOT_SERIOUS for d in gd.GRADE_DOMAINS}
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is True
    assert out["effectiveCertainty"] is None


def test_aggregate_blocked_when_judgement_agent_is_model():
    j = five_judgements(agent_class="model")
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is True
    assert out["effectiveCertainty"] is None


def test_aggregate_blocked_when_rating_is_indeterminate():
    j = five_judgements()
    j["inconsistency"] = judgement("inconsistency", rating=gd.INDETERMINATE)
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is True
    assert out["effectiveCertainty"] is None


def test_aggregate_blocked_when_rationale_is_empty():
    j = five_judgements()
    j["indirectness"] = judgement("indirectness", rationale="   ")
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is True


def test_aggregate_blocked_when_domain_key_mismatches_judgement():
    j = five_judgements()
    j["indirectness"] = judgement("imprecision")
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is True


def test_general_tier_accepts_human_self():
    j = five_judgements(agent_class="human-self")
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is False
    assert out["effectiveCertainty"] == "high"


def test_safety_critical_rejects_human_self():
    j = five_judgements(agent_class="human-self")
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="safety-critical")
    assert out["blocked"] is True
    assert out["effectiveCertainty"] is None
    assert any("human-expert" in r for r in out["blockReasons"])


def test_safety_critical_accepts_human_expert():
    j = five_judgements(agent_class="human-expert")
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="safety-critical")
    assert out["blocked"] is False
    assert out["effectiveCertainty"] == "high"


def test_unknown_risk_tier_raises():
    with assert_raises(ValueError):
        gd.aggregate_certainty("RCT-parallel", five_judgements(),
                               risk_tier="whatever")


def test_aggregate_high_when_all_clean():
    out = gd.aggregate_certainty("RCT-parallel", five_judgements(),
                                 risk_tier="general-clinical")
    assert out["effectiveCertainty"] == "high"
    assert out["certaintyDerivation"] == "deterministic-rule"
    assert out["startingLevel"] == "high"


def test_aggregate_downgrades_accumulate():
    j = five_judgements()
    j["risk-of-bias"] = judgement("risk-of-bias", rating=gd.SERIOUS)
    j["inconsistency"] = judgement("inconsistency", rating=gd.SERIOUS)
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["totalDowngrade"] == 2
    assert out["effectiveCertainty"] == "low"


def test_observational_starts_low():
    out = gd.aggregate_certainty("cohort-prospective", five_judgements(),
                                 risk_tier="general-clinical")
    assert out["startingLevel"] == "low"
    assert out["effectiveCertainty"] == "low"


def test_observational_upgrades_apply():
    out = gd.aggregate_certainty("cohort-prospective", five_judgements(),
                                 risk_tier="general-clinical",
                                 upgrades={"large-effect": True,
                                           "dose-response": True})
    assert out["totalUpgrade"] == 2
    assert out["effectiveCertainty"] == "high"


def test_upgrades_do_not_apply_to_rct_start():
    out = gd.aggregate_certainty("RCT-parallel", five_judgements(),
                                 risk_tier="general-clinical",
                                 upgrades={"large-effect": True})
    assert out["totalUpgrade"] == 0


# ===========================================================================
# 4. model override 只寫 advisory
# ===========================================================================

def _serious_proposal():
    """兩個 domain serious 的基準（RCT 起始 high → low）。

    刻意不用「五個全 serious」：那會撞到階梯底部 very-low，
    移掉一個降級也不會改變等級，override 的生效與否就測不出來。
    """
    j = five_judgements()
    j["inconsistency"] = judgement("inconsistency", rating=gd.SERIOUS)
    j["imprecision"] = judgement("imprecision", rating=gd.SERIOUS,
                                 indicators=registered_imprecision_indicators())
    return gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")


def test_serious_proposal_baseline():
    p = _serious_proposal()
    assert p["blocked"] is False
    assert p["totalDowngrade"] == 2
    assert p["effectiveCertainty"] == "low"


def test_model_override_is_advisory_only():
    p = _serious_proposal()
    before_certainty = p["effectiveCertainty"]
    before_domain = p["perDomain"]["imprecision"]
    r = gd.apply_override(p, "imprecision", gd.NOT_SERIOUS, "model", "看起來夠精確")
    assert r["advisoryOverrides"][0]["effectiveForApprovedClaim"] is False
    assert r["effectiveCertainty"] == before_certainty
    assert r["perDomain"]["imprecision"] == before_domain
    assert r["certaintyDerivation"] == "deterministic-rule"
    assert r["advisoryOverrides"][0]["advisoryCertainty"] is not None


def test_model_override_does_not_mutate_original_proposal():
    p = _serious_proposal()
    snapshot = dict(p["perDomain"])
    r = gd.apply_override(p, "imprecision", gd.NOT_SERIOUS, "model", "x")
    assert p["advisoryOverrides"] == []
    assert p["perDomain"] == snapshot
    assert r is not p


def test_repeated_overrides_do_not_pollute_history():
    p = _serious_proposal()
    r1 = gd.apply_override(p, "imprecision", gd.NOT_SERIOUS, "model", "一")
    r2 = gd.apply_override(r1, "inconsistency", gd.NOT_SERIOUS, "model", "二")
    assert len(p["advisoryOverrides"]) == 0
    assert len(r1["advisoryOverrides"]) == 1
    assert len(r2["advisoryOverrides"]) == 2
    assert r1["advisoryOverrides"] is not r2["advisoryOverrides"]


def test_human_expert_override_updates_effective_certainty():
    p = _serious_proposal()
    r = gd.apply_override(p, "imprecision", gd.NOT_SERIOUS, "human-expert",
                          "OIS 已達，CI 未跨雙向 MID")
    assert r["overrides"][0]["effectiveForApprovedClaim"] is True
    assert r["perDomain"]["imprecision"] == gd.NOT_SERIOUS
    assert r["totalDowngrade"] == 1
    assert r["certaintyDerivation"] == "deterministic-rule-with-logged-override"
    assert p["effectiveCertainty"] == "low"
    assert r["effectiveCertainty"] == "moderate"


def test_human_self_override_on_safety_critical_is_advisory_only():
    j = five_judgements(agent_class="human-expert")
    j["imprecision"] = judgement("imprecision", rating=gd.SERIOUS,
                                 indicators=registered_imprecision_indicators())
    p = gd.aggregate_certainty("RCT-parallel", j, risk_tier="safety-critical")
    r = gd.apply_override(p, "imprecision", gd.NOT_SERIOUS, "human-self",
                          "我覺得夠精確")
    assert r["advisoryOverrides"][0]["effectiveForApprovedClaim"] is False
    assert r["perDomain"]["imprecision"] == gd.SERIOUS
    assert r["effectiveCertainty"] == p["effectiveCertainty"]


def test_override_on_blocked_proposal_is_safe():
    j = five_judgements()
    del j["imprecision"]
    blocked = gd.aggregate_certainty("RCT-parallel", j,
                                     risk_tier="general-clinical")
    r = gd.apply_override(blocked, "imprecision", gd.NOT_SERIOUS,
                          "human-expert", "補上")
    assert r["blocked"] is True
    assert r["effectiveCertainty"] is None
    assert r["advisoryOverrides"][0]["effectiveForApprovedClaim"] is False
    assert blocked["advisoryOverrides"] == []


def test_override_with_unknown_agent_class_raises():
    with assert_raises(ValueError):
        gd.apply_override(_serious_proposal(), "imprecision", gd.NOT_SERIOUS,
                          "aliens", "?")


def test_override_with_indeterminate_level_raises():
    with assert_raises(ValueError):
        gd.apply_override(_serious_proposal(), "imprecision", gd.INDETERMINATE,
                          "human-expert", "說不準")


def test_override_with_empty_rationale_raises():
    with assert_raises(ValueError):
        gd.apply_override(_serious_proposal(), "imprecision", gd.NOT_SERIOUS,
                          "human-expert", "  ")


# ===========================================================================
# 5. MID 狀態的處置
# ===========================================================================

def test_unavailable_mid_is_not_contextualised_and_requires_human_explanation():
    r = gd.rate_imprecision(-0.1, 0.5, total_n=200, mid=None,
                            mid_status="unavailable", ois=500)
    assert r.indicators["contextualised"] is False
    assert "midUnavailable" in r.flags
    assert "midUnavailable" in r.requires_acknowledgement
    assert r.human_judgement_required is True


def test_unacknowledged_mid_unavailable_blocks_aggregation():
    ind = gd.rate_imprecision(-0.1, 0.5, total_n=200, mid=None,
                              mid_status="unavailable", ois=500)
    j = five_judgements(imprecision_indicators=ind)
    j["imprecision"] = judgement("imprecision", acknowledged=[], indicators=ind)
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is True
    assert any("midUnavailable" in r for r in out["blockReasons"])


def test_unavailable_mid_not_contextualised_but_not_locked_to_low():
    ind = gd.rate_imprecision(-0.1, 0.5, total_n=200, mid=None,
                              mid_status="unavailable", ois=500)
    out = gd.aggregate_certainty("RCT-parallel",
                                 five_judgements(imprecision_indicators=ind),
                                 risk_tier="general-clinical")
    assert out["blocked"] is False
    assert out["contextualisedImprecision"] is False
    assert out["effectiveCertainty"] != "high"
    # 不得硬鎖 low —— 降級只能來自實際的 domain judgement
    assert out["effectiveCertainty"] == "moderate"


def test_provisional_mid_cannot_support_high():
    ind = gd.rate_imprecision(0.30, 0.50, total_n=1000, mid=0.10,
                              mid_status="provisional", ois=500)
    assert "midProvisional" in ind.flags
    out = gd.aggregate_certainty("RCT-parallel",
                                 five_judgements(imprecision_indicators=ind),
                                 risk_tier="general-clinical")
    assert out["blocked"] is False
    assert out["effectiveCertainty"] == "moderate"
    assert any("provisional" in c.lower() for c in out["capReasons"])


def test_registered_mid_supports_high():
    out = gd.aggregate_certainty("RCT-parallel", five_judgements(),
                                 risk_tier="general-clinical")
    assert out["effectiveCertainty"] == "high"
    assert out["contextualisedImprecision"] is True
    assert out["capReasons"] == []


def test_missing_imprecision_indicators_cannot_claim_high():
    j = five_judgements()
    j["imprecision"] = judgement("imprecision", indicators=None)
    out = gd.aggregate_certainty("RCT-parallel", j, risk_tier="general-clinical")
    assert out["blocked"] is False
    assert out["effectiveCertainty"] == "moderate"
    assert out["contextualisedImprecision"] is None


def test_tau2_zero_prediction_interval_is_not_double_counted():
    # 三個幾乎相同的研究 -> tau2 = 0，預測區間因小 k 的 t 乘數而寬
    r = gd.rate_inconsistency([0.20, 0.201, 0.199], [0.01] * 3)
    assert r.indicators["tau2"] == 0.0
    assert "prediction-interval-not-used-tau2-zero" in r.flags
    assert "prediction-interval-crosses-null" not in r.flags
    assert r.suggested_judgement == gd.NOT_SERIOUS


def test_tau2_positive_prediction_interval_still_counts():
    r = gd.rate_inconsistency([0.10, 0.90, 0.15, 0.85], [0.005] * 4)
    assert r.indicators["tau2"] > 0
    assert "prediction-interval-crosses-null" in r.flags


def test_no_new_grade_levels_invented():
    assert gd.CERTAINTY_LADDER == ["very-low", "low", "moderate", "high"]
    assert set(gd.DOWNGRADE) == {gd.NOT_SERIOUS, gd.SERIOUS, gd.VERY_SERIOUS}
    assert gd.INDETERMINATE not in gd.DOWNGRADE
    assert gd.INDETERMINATE not in gd.CERTAINTY_LADDER


# ===========================================================================
# 6. backward-compatible wrapper（只在安全時）
# ===========================================================================

def test_domain_rating_alias_still_readable():
    r = gd.rate_inconsistency([0.20, 0.22, 0.18, 0.21], [0.01] * 4)
    assert isinstance(r, gd.DomainRating)
    assert r.proposed == r.suggested_judgement
    assert r.computed == r.indicators
    assert r.requires_human_confirmation == r.human_judgement_required


def test_propose_certainty_wrapper_never_produces_effective_certainty():
    d = {k: gd.NOT_SERIOUS for k in gd.GRADE_DOMAINS}
    out = gd.propose_certainty("RCT-parallel", d)
    assert out["blocked"] is True
    assert out["effectiveCertainty"] is None
    assert out["advisoryCertainty"] == "high"


def test_propose_certainty_wrapper_still_blocks_missing_domain():
    out = gd.propose_certainty("RCT-parallel", {"risk-of-bias": gd.NOT_SERIOUS})
    assert out["blocked"] is True
    assert out["effectiveCertainty"] is None
    assert out["advisoryCertainty"] is None
