import math

from ahig.stats import deterministic as ds


# --- CI 對稱性 -------------------------------------------------------------

def test_ci_symmetry_ratio_measure_log_scale_pass():
    # RR = 0.80, CI 0.64–1.00 —— log 尺度對稱
    c = ds.check_ci_symmetry(0.80, 0.64, 1.00, "RR")
    assert c.verdict == ds.PASS


def test_ci_symmetry_ratio_measure_naive_arithmetic_would_pass_but_log_fails():
    # 算術上對稱 (1.0 ± 0.4) 但 log 尺度嚴重不對稱 —— 常見的抽取錯誤
    c = ds.check_ci_symmetry(1.00, 0.60, 1.40, "RR")
    assert c.verdict == ds.FAIL
    assert c.recomputed["scale"] == "log"


def test_ci_symmetry_difference_measure():
    assert ds.check_ci_symmetry(2.5, 1.0, 4.0, "MD").verdict == ds.PASS
    assert ds.check_ci_symmetry(2.5, 1.0, 8.0, "MD").verdict == ds.FAIL


def test_estimate_outside_ci_fails():
    assert ds.check_ci_symmetry(5.0, 1.0, 4.0, "MD").verdict == ds.FAIL


def test_ratio_measure_non_positive_fails():
    assert ds.check_ci_symmetry(0.5, -0.1, 1.2, "RR").verdict == ds.FAIL


# --- p 值 -----------------------------------------------------------------

def test_p_from_ci_matches_known_value():
    # MD = 2.0, SE = 1.0 -> CI 0.04–3.96, z = 2.0, p ~ 0.0455
    p = ds.p_from_estimate_ci(2.0, 2.0 - 1.96, 2.0 + 1.96, "MD")
    assert math.isclose(p, 0.0455, abs_tol=5e-4)


def test_p_from_ci_ratio_measure():
    # HR = 0.5, log(0.5) = -0.693; SE = 0.2 -> z = -3.466, p ~ 0.00053
    lo, hi = math.exp(math.log(0.5) - 1.96 * 0.2), math.exp(math.log(0.5) + 1.96 * 0.2)
    p = ds.p_from_estimate_ci(0.5, lo, hi, "HR")
    assert math.isclose(p, 0.000528, rel_tol=0.05)


def test_p_vs_ci_detects_mismatch():
    lo, hi = 2.0 - 1.96, 2.0 + 1.96
    assert ds.check_p_vs_ci(2.0, lo, hi, "MD", 0.045).verdict == ds.PASS
    assert ds.check_p_vs_ci(2.0, lo, hi, "MD", 0.001).verdict == ds.FAIL


def test_significance_coherence_catches_classic_error():
    # p < 0.05 但 CI 跨 1 —— 最常見的抽取矛盾
    assert ds.check_significance_coherence(0.85, 1.20, "RR", 0.02).verdict == ds.FAIL
    # p > 0.05 但 CI 不跨 1
    assert ds.check_significance_coherence(1.10, 1.50, "RR", 0.30).verdict == ds.FAIL
    # 一致
    assert ds.check_significance_coherence(1.10, 1.50, "RR", 0.01).verdict == ds.PASS
    assert ds.check_significance_coherence(0.85, 1.20, "RR", 0.30).verdict == ds.PASS


def test_significance_coherence_inconclusive_without_p():
    assert ds.check_significance_coherence(0.8, 1.2, "RR", None).verdict == ds.INCONCLUSIVE


# --- 人數與事件數 ----------------------------------------------------------

def test_event_counts():
    assert ds.check_event_counts([10, 20], [100, 100]).verdict == ds.PASS
    assert ds.check_event_counts([110, 20], [100, 100]).verdict == ds.FAIL
    assert ds.check_event_counts([-1, 20], [100, 100]).verdict == ds.FAIL


def test_arm_accounting():
    assert ds.check_arm_accounting(100, 100, 0, 0, "ITT").verdict == ds.PASS
    assert ds.check_arm_accounting(100, 90, 10, 0, "PP").verdict == ds.PASS
    # 宣告 ITT 卻只分析 90 人
    assert ds.check_arm_accounting(100, 90, 10, 0, "ITT").verdict == ds.FAIL
    # 加總對不上
    assert ds.check_arm_accounting(100, 90, 5, 0, "PP").verdict == ds.FAIL
    # analysed > randomised
    assert ds.check_arm_accounting(100, 110, 0, 0, "ITT").verdict == ds.FAIL


# --- 2x2 重算 --------------------------------------------------------------

def test_recompute_2x2_known_values():
    r = ds.recompute_from_2x2(a=15, n1=100, c=30, n2=100)
    assert math.isclose(r["RR"], 0.5, rel_tol=1e-9)
    assert math.isclose(r["RD"], -0.15, rel_tol=1e-9)
    # OR = (15*70)/(85*30) = 1050/2550
    assert math.isclose(r["OR"], 1050 / 2550, rel_tol=1e-9)
    assert not r["haldane_correction_applied"]


def test_recompute_2x2_zero_cell_applies_haldane():
    r = ds.recompute_from_2x2(a=0, n1=50, c=10, n2=50)
    assert r["haldane_correction_applied"]
    assert r["RR"] > 0


def test_effect_vs_2x2_detects_transcription_error():
    ok = ds.check_effect_vs_2x2("RR", 0.50, 15, 100, 30, 100)
    assert ok.verdict == ds.PASS
    bad = ds.check_effect_vs_2x2("RR", 0.85, 15, 100, 30, 100)
    assert bad.verdict == ds.FAIL


def test_effect_vs_2x2_not_applicable_for_md():
    assert ds.check_effect_vs_2x2("MD", 1.0, 1, 2, 1, 2).verdict == ds.NOT_APPLICABLE


# --- 檢定統計量 ------------------------------------------------------------

def test_p_from_test_statistic():
    assert math.isclose(ds.p_from_test_statistic("z", 1.96), 0.05, abs_tol=1e-3)
    assert math.isclose(ds.p_from_test_statistic("t", 2.0, df1=30), 0.0546, abs_tol=1e-3)
    assert math.isclose(ds.p_from_test_statistic("chi2", 3.841, df1=1), 0.05, abs_tol=1e-3)
    assert ds.p_from_test_statistic("t", 2.0) is None


def test_check_test_statistic_p():
    assert ds.check_test_statistic_p("t", 2.0, 0.055, df1=30).verdict == ds.PASS
    assert ds.check_test_statistic_p("t", 2.0, 0.001, df1=30).verdict == ds.FAIL


# --- SMD -------------------------------------------------------------------

def test_cohens_d_and_hedges_g():
    r = ds.cohens_d_independent(10, 2, 25, 8, 2, 25)
    assert math.isclose(r["cohens_d"], 1.0, rel_tol=1e-9)
    assert r["hedges_g"] < r["cohens_d"]        # J < 1
    assert math.isclose(r["correction_J"], 1 - 3 / (4 * 48 - 1), rel_tol=1e-12)


def test_check_smd_flags_mislabelled_type():
    # 小樣本時 J 校正夠大，d 與 g 的差異超過容忍度而可被偵測。
    # n=5/組 -> df=8, J=1-3/31=0.903
    r = ds.cohens_d_independent(10, 2, 5, 8, 2, 5)
    c = ds.check_smd(r["cohens_d"], 10, 2, 5, 8, 2, 5, smd_type="hedges_g")
    assert c.verdict == ds.FAIL
    assert c.recomputed.get("matches_instead") == "cohens_d"


def test_check_smd_type_mixup_undetectable_at_large_n_by_design():
    # n=60/組 -> J≈0.994，d 與 g 差 <1%，落在容忍度內。
    # 這是正確行為：大樣本下兩者實質等價，標錯類型不影響證據判讀。
    r = ds.cohens_d_independent(10, 2, 60, 8, 2, 60)
    c = ds.check_smd(r["cohens_d"], 10, 2, 60, 8, 2, 60, smd_type="hedges_g")
    assert c.verdict == ds.PASS


def test_check_smd_pass():
    r = ds.cohens_d_independent(10, 2, 25, 8, 2, 25)
    assert ds.check_smd(r["hedges_g"], 10, 2, 25, 8, 2, 25).verdict == ds.PASS


# --- 設計誤用 --------------------------------------------------------------

def test_paired_design_detects_independent_df():
    c = ds.check_paired_design_formula("RCT-crossover", "paired t-test",
                                       df_reported=38, n_subjects=20)
    assert c.verdict == ds.FAIL      # 2n-2 = 38
    ok = ds.check_paired_design_formula("RCT-crossover", "paired t-test",
                                        df_reported=19, n_subjects=20)
    assert ok.verdict == ds.PASS


def test_paired_design_not_applicable_for_parallel():
    c = ds.check_paired_design_formula("RCT-parallel", "independent t-test", 38, 20)
    assert c.verdict == ds.NOT_APPLICABLE


def test_paired_design_flags_declared_independent():
    c = ds.check_paired_design_formula("RCT-crossover", "independent samples t-test",
                                       None, None)
    assert c.verdict == ds.FAIL


# --- 球形性校正 ------------------------------------------------------------

def test_sphericity_uncorrected_consistent():
    # 3 水準、20 受試者 -> df1=2, df2=38
    c = ds.check_sphericity_correction("rm-anova", 2, 38, "none", 3, 20)
    assert c.verdict == ds.PASS


def test_sphericity_correction_cannot_increase_df():
    c = ds.check_sphericity_correction("rm-anova", 2.5, 38, "greenhouse-geisser", 3, 20)
    assert c.verdict == ds.FAIL


def test_sphericity_epsilon_below_lower_bound_fails():
    # 3 水準 -> epsilon 下界 = 0.5 -> df1 下界 = 1.0
    c = ds.check_sphericity_correction("rm-anova", 0.6, 11, "greenhouse-geisser", 3, 20)
    assert c.verdict == ds.FAIL


def test_sphericity_valid_correction_passes():
    c = ds.check_sphericity_correction("rm-anova", 1.6, 30.4, "greenhouse-geisser", 3, 20)
    assert c.verdict == ds.PASS
    assert 0.5 <= c.recomputed["implied_epsilon"] <= 1.0


# --- GRIM / GRIMMER --------------------------------------------------------

def test_grim_not_applicable_for_continuous():
    c = ds.grim_test("3.14", 20, is_discrete_integer_scale=False)
    assert c.verdict == ds.NOT_APPLICABLE


def test_grim_detects_impossible_mean():
    # n=20 -> 平均的可能值間隔 0.05；3.14 不可能
    assert ds.grim_test("3.14", 20).verdict == ds.FAIL
    assert ds.grim_test("3.15", 20).verdict == ds.PASS


def test_grim_with_multi_item_scale():
    # 每人 5 個整數項目的平均 -> 間隔 1/(20*5) = 0.01
    assert ds.grim_test("3.14", 20, items_per_subject=5).verdict == ds.PASS


def test_grim_inconclusive_without_decimals():
    assert ds.grim_test("3", 20).verdict == ds.INCONCLUSIVE


def test_grimmer_not_applicable_for_continuous():
    assert ds.grimmer_test("3.15", "1.23", 20,
                           is_discrete_integer_scale=False).verdict == ds.NOT_APPLICABLE


def test_grimmer_accepts_consistent_integer_data():
    # 真實整數資料：n=8, 值 = 1..8 -> mean 4.5, sd = 2.449
    assert ds.grimmer_test("4.50", "2.45", 8).verdict in (ds.PASS, ds.INCONCLUSIVE)


def test_grimmer_rejects_when_mean_not_grim_consistent():
    # mean 4.44 在 n=8 下不是 GRIM-一致的（間隔 0.125）
    assert ds.grimmer_test("4.44", "2.45", 8).verdict == ds.FAIL


# --- 推論框架 --------------------------------------------------------------

def test_mbi_alone_cannot_support_efficacy():
    c = ds.check_inference_framework("MBI", False, "efficacy")
    assert c.verdict == ds.FAIL
    assert c.recomputed["forced_label"] == "exploratory"


def test_mbi_with_conventional_stats_passes():
    assert ds.check_inference_framework("MBI", True, "efficacy").verdict == ds.PASS


def test_frequentist_passes():
    assert ds.check_inference_framework("frequentist", True, "efficacy").verdict == ds.PASS


# --- 彙總 ------------------------------------------------------------------

def test_run_all_clean_record():
    sr = {
        "effectMeasure": "RR", "pointEstimate": 0.50,
        "ciLow": 0.28, "ciHigh": 0.89, "pValue": 0.019,
        "events": [15, 30], "armN": [100, 100],
        "armAccounting": [{"randomised": 100, "analysed": 100}],
        "analysisSet": "ITT", "studyDesign": "RCT-parallel",
        "inferenceFramework": "frequentist", "hasConventionalStatistics": True,
    }
    r = ds.run_all(sr)
    assert r["n_fail"] == 0, r["failed_rules"]
    assert r["verdict"] in (ds.PASS, ds.INCONCLUSIVE)


def test_run_all_catches_planted_contradiction():
    sr = {
        "effectMeasure": "RR", "pointEstimate": 0.50,
        "ciLow": 0.28, "ciHigh": 0.89,
        "pValue": 0.40,                      # 與 CI 不跨 1 矛盾
        "events": [15, 100], "armN": [100, 100],
        "analysisSet": "ITT", "studyDesign": "RCT-parallel",
    }
    r = ds.run_all(sr)
    assert r["blocking"]
    assert "STAT-003-significance-coherence" in r["failed_rules"]


def test_run_all_catches_event_exceeding_n():
    sr = {"effectMeasure": "RR", "events": [150, 30], "armN": [100, 100],
          "studyDesign": "RCT-parallel"}
    r = ds.run_all(sr)
    assert "STAT-004-event-le-n" in r["failed_rules"]


if __name__ == "__main__":
    from run_tests import main
    raise SystemExit(main([__file__]))
