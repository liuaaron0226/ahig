#!/usr/bin/env python3
"""
AHIG 確定性統計攔截層 —— 參考實作

契約原則：LLM 只負責抽取；可以計算的事全部由程式重算。
本模組的每個檢查回傳一個 Check 物件，帶 ruleId、verdict、觀察值與重算值。

verdict 語意：
  PASS          —— 重算結果與抽取值一致
  FAIL          —— 存在數學矛盾。屬於零容忍項，該 StudyResult 不得晉升。
  INCONCLUSIVE  —— 資料不足以判定（缺欄位）。不是 PASS。
  NOT_APPLICABLE—— 該檢查的數學假設不成立（例如 GRIM 用在連續變項）

重要：INCONCLUSIVE 與 NOT_APPLICABLE 必須嚴格區分。前者是缺資料，
後者是這個檢查根本不該套用。契約原文對 GRIM/GRIMMER 的警告正是後者。
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Optional, Sequence

from scipy import stats

RATIO_MEASURES = {"RR", "OR", "HR", "IRR", "ratio-of-means"}
DIFFERENCE_MEASURES = {"MD", "SMD", "RD", "mean", "proportion"}
NULL_VALUE = {**{m: 1.0 for m in RATIO_MEASURES},
              **{m: 0.0 for m in DIFFERENCE_MEASURES}}

PASS, FAIL, INCONCLUSIVE, NOT_APPLICABLE = "PASS", "FAIL", "INCONCLUSIVE", "NOT_APPLICABLE"


@dataclass
class Check:
    rule_id: str
    verdict: str
    message: str
    observed: dict = field(default_factory=dict)
    recomputed: dict = field(default_factory=dict)

    @property
    def blocking(self) -> bool:
        return self.verdict == FAIL

    def __repr__(self):
        return f"<{self.rule_id} {self.verdict}: {self.message}>"


def _z_crit(ci_level: float = 0.95) -> float:
    return float(stats.norm.ppf(1 - (1 - ci_level) / 2))


def _to_log_space(est, lo, hi, measure):
    if measure in RATIO_MEASURES:
        if min(est, lo, hi) <= 0:
            return None
        return math.log(est), math.log(lo), math.log(hi)
    return est, lo, hi


# ---------------------------------------------------------------------------
# 1–3. 效果量 / CI / SE / p 一致性
# ---------------------------------------------------------------------------

def check_ci_symmetry(estimate: float, ci_low: float, ci_high: float,
                      measure: str, tolerance: float = 0.05) -> Check:
    """CI 在適當尺度上應以點估計為中心。比值型測度須在 log 尺度檢查。"""
    rid = "STAT-001-ci-symmetry"
    if None in (estimate, ci_low, ci_high):
        return Check(rid, INCONCLUSIVE, "缺少 estimate 或 CI")
    if ci_low > ci_high:
        return Check(rid, FAIL, "CI 下界大於上界",
                     {"ci_low": ci_low, "ci_high": ci_high})
    if not (ci_low <= estimate <= ci_high):
        return Check(rid, FAIL, "點估計落在 CI 之外",
                     {"estimate": estimate, "ci": [ci_low, ci_high]})

    tr = _to_log_space(estimate, ci_low, ci_high, measure)
    if tr is None:
        return Check(rid, FAIL, "比值型測度出現非正值",
                     {"estimate": estimate, "ci": [ci_low, ci_high], "measure": measure})
    e, lo, hi = tr
    half_lo, half_hi = e - lo, hi - e
    if half_lo <= 0 or half_hi <= 0:
        return Check(rid, FAIL, "轉換後 CI 半寬非正")
    asym = abs(half_hi - half_lo) / ((half_hi + half_lo) / 2)
    scale = "log" if measure in RATIO_MEASURES else "identity"
    if asym > tolerance:
        return Check(rid, FAIL,
                     f"CI 在 {scale} 尺度不對稱（相對差 {asym:.1%} > {tolerance:.0%}）",
                     {"estimate": estimate, "ci": [ci_low, ci_high], "measure": measure},
                     {"scale": scale, "half_low": half_lo, "half_high": half_hi,
                      "relative_asymmetry": asym})
    return Check(rid, PASS, f"CI 在 {scale} 尺度對稱（相對差 {asym:.2%}）",
                 recomputed={"relative_asymmetry": asym, "scale": scale})


def se_from_ci(ci_low: float, ci_high: float, measure: str,
               ci_level: float = 0.95) -> Optional[float]:
    tr = _to_log_space(1.0, ci_low, ci_high, measure)
    if tr is None:
        return None
    _, lo, hi = tr
    return (hi - lo) / (2 * _z_crit(ci_level))


def p_from_estimate_ci(estimate: float, ci_low: float, ci_high: float,
                       measure: str, ci_level: float = 0.95) -> Optional[float]:
    """Altman & Bland 法：由點估計與 CI 反推 p 值。"""
    se = se_from_ci(ci_low, ci_high, measure, ci_level)
    if se is None or se <= 0:
        return None
    null = NULL_VALUE.get(measure, 0.0)
    if measure in RATIO_MEASURES:
        if estimate <= 0:
            return None
        z = math.log(estimate) / se
    else:
        z = (estimate - null) / se
    return float(2 * (1 - stats.norm.cdf(abs(z))))


def check_p_vs_ci(estimate: float, ci_low: float, ci_high: float, measure: str,
                  reported_p: Optional[float], ci_level: float = 0.95,
                  ratio_tolerance: float = 3.0) -> Check:
    """重算 p 值並與報告值比較。容忍度以倍數表示，因為 p 值本身橫跨數量級。"""
    rid = "STAT-002-p-vs-ci"
    if reported_p is None:
        return Check(rid, INCONCLUSIVE, "未報告 p 值")
    recomputed = p_from_estimate_ci(estimate, ci_low, ci_high, measure, ci_level)
    if recomputed is None:
        return Check(rid, INCONCLUSIVE, "無法由 CI 反推 SE")
    if recomputed < 1e-12 and reported_p < 1e-3:
        return Check(rid, PASS, "兩者皆極小，一致",
                     {"reported_p": reported_p}, {"p": recomputed})
    hi = max(reported_p, recomputed)
    lo = max(min(reported_p, recomputed), 1e-12)
    ratio = hi / lo
    obs = {"reported_p": reported_p}
    rec = {"p_from_ci": round(recomputed, 6), "ratio": round(ratio, 2)}
    if ratio > ratio_tolerance:
        return Check(rid, FAIL,
                     f"報告 p={reported_p:.4g} 與由 CI 反推的 p={recomputed:.4g} "
                     f"相差 {ratio:.1f} 倍", obs, rec)
    return Check(rid, PASS, f"p 值一致（比值 {ratio:.2f}）", obs, rec)


def check_significance_coherence(ci_low: float, ci_high: float, measure: str,
                                 reported_p: Optional[float],
                                 alpha: float = 0.05) -> Check:
    """p < alpha 與 95% CI 是否跨虛無值必須一致。這是最常見的抽取錯誤來源。"""
    rid = "STAT-003-significance-coherence"
    if reported_p is None:
        return Check(rid, INCONCLUSIVE, "未報告 p 值")
    null = NULL_VALUE.get(measure)
    if null is None:
        return Check(rid, NOT_APPLICABLE, f"測度 {measure} 無定義的虛無值")
    crosses = ci_low <= null <= ci_high
    significant = reported_p < alpha
    obs = {"ci": [ci_low, ci_high], "reported_p": reported_p, "null": null}
    if significant and crosses:
        return Check(rid, FAIL,
                     f"p={reported_p:.4g} < {alpha} 但 CI 跨越虛無值 {null}", obs)
    if (not significant) and (not crosses):
        return Check(rid, FAIL,
                     f"p={reported_p:.4g} >= {alpha} 但 CI 未跨越虛無值 {null}", obs)
    return Check(rid, PASS, "顯著性與 CI 一致", obs)


# ---------------------------------------------------------------------------
# 4–6. 人數與事件數對帳，由 2x2 重算效果量
# ---------------------------------------------------------------------------

def check_event_counts(events: Sequence[int], n: Sequence[int]) -> Check:
    rid = "STAT-004-event-le-n"
    if len(events) != len(n):
        return Check(rid, INCONCLUSIVE, "arm 數不一致")
    bad = [(i, e, m) for i, (e, m) in enumerate(zip(events, n))
           if e is None or m is None or e < 0 or m <= 0 or e > m]
    if bad:
        return Check(rid, FAIL, f"事件數超出該 arm 樣本數或為負：{bad}",
                     {"events": list(events), "n": list(n)})
    return Check(rid, PASS, "各 arm 事件數皆不超過樣本數")


def check_arm_accounting(randomised: Optional[int], analysed: Optional[int],
                         lost_to_followup: Optional[int] = None,
                         excluded: Optional[int] = None,
                         analysis_set: str = "ITT") -> Check:
    """randomised = analysed + lost + excluded。ITT 下 analysed 應等於 randomised。"""
    rid = "STAT-005-arm-accounting"
    if randomised is None or analysed is None:
        return Check(rid, INCONCLUSIVE, "缺少 randomised 或 analysed")
    lost = lost_to_followup or 0
    exc = excluded or 0
    if analysed > randomised:
        return Check(rid, FAIL, f"analysed({analysed}) > randomised({randomised})",
                     {"randomised": randomised, "analysed": analysed})
    total = analysed + lost + exc
    obs = {"randomised": randomised, "analysed": analysed,
           "lost": lost, "excluded": exc, "analysis_set": analysis_set}
    if total != randomised:
        return Check(rid, FAIL,
                     f"人數對不上：analysed+lost+excluded={total} != randomised={randomised}",
                     obs, {"unaccounted": randomised - total})
    if analysis_set == "ITT" and analysed != randomised:
        return Check(rid, FAIL,
                     f"宣告 ITT 但 analysed({analysed}) != randomised({randomised})", obs)
    return Check(rid, PASS, "人數對帳一致", obs)


def recompute_from_2x2(a: int, n1: int, c: int, n2: int,
                       ci_level: float = 0.95) -> dict:
    """由 2x2 (介入組事件 a/n1、對照組事件 c/n2) 重算 RR、OR、RD 及其 CI。
    對零格採 Haldane-Anscombe 0.5 校正，並回報是否使用。"""
    b, d = n1 - a, n2 - c
    z = _z_crit(ci_level)
    zero_cell = 0 in (a, b, c, d)
    aa, bb, cc, dd = (a + 0.5, b + 0.5, c + 0.5, d + 0.5) if zero_cell else (a, b, c, d)
    n1c, n2c = aa + bb, cc + dd

    r1, r2 = aa / n1c, cc / n2c
    rr = r1 / r2
    se_log_rr = math.sqrt(1 / aa - 1 / n1c + 1 / cc - 1 / n2c)
    or_ = (aa * dd) / (bb * cc)
    se_log_or = math.sqrt(1 / aa + 1 / bb + 1 / cc + 1 / dd)
    rd = r1 - r2
    se_rd = math.sqrt(r1 * (1 - r1) / n1c + r2 * (1 - r2) / n2c)

    return {
        "haldane_correction_applied": zero_cell,
        "RR": rr,
        "RR_ci": [math.exp(math.log(rr) - z * se_log_rr),
                  math.exp(math.log(rr) + z * se_log_rr)],
        "OR": or_,
        "OR_ci": [math.exp(math.log(or_) - z * se_log_or),
                  math.exp(math.log(or_) + z * se_log_or)],
        "RD": rd,
        "RD_ci": [rd - z * se_rd, rd + z * se_rd],
        "risk_intervention": r1, "risk_comparator": r2,
    }


def check_effect_vs_2x2(measure: str, estimate: float, a: int, n1: int, c: int,
                        n2: int, rel_tolerance: float = 0.05) -> Check:
    rid = "STAT-006-effect-vs-2x2"
    if measure not in {"RR", "OR", "RD"}:
        return Check(rid, NOT_APPLICABLE, f"{measure} 無法由 2x2 直接重算")
    try:
        rec = recompute_from_2x2(a, n1, c, n2)
    except (ZeroDivisionError, ValueError) as exc:
        return Check(rid, INCONCLUSIVE, f"重算失敗：{exc}")
    val = rec[measure]
    denom = abs(val) if abs(val) > 1e-12 else 1.0
    rel = abs(estimate - val) / denom
    obs = {"reported": estimate, "a": a, "n1": n1, "c": c, "n2": n2}
    recd = {measure: round(val, 6), "ci": [round(x, 6) for x in rec[f"{measure}_ci"]],
            "haldane": rec["haldane_correction_applied"], "relative_diff": round(rel, 4)}
    if rel > rel_tolerance:
        return Check(rid, FAIL,
                     f"報告 {measure}={estimate:.4g} 與由事件數重算的 {val:.4g} "
                     f"相對差 {rel:.1%}", obs, recd)
    return Check(rid, PASS, f"{measure} 與 2x2 一致（相對差 {rel:.2%}）", obs, recd)


# ---------------------------------------------------------------------------
# 7. 由檢定統計量與 df 重算 p 值
# ---------------------------------------------------------------------------

def p_from_test_statistic(stat_type: str, value: float, df1: Optional[float] = None,
                          df2: Optional[float] = None, two_sided: bool = True
                          ) -> Optional[float]:
    st = stat_type.lower()
    if st == "z":
        p = 2 * (1 - stats.norm.cdf(abs(value)))
        return float(p if two_sided else p / 2)
    if st == "t":
        if df1 is None:
            return None
        p = 2 * (1 - stats.t.cdf(abs(value), df1))
        return float(p if two_sided else p / 2)
    if st == "chi2":
        if df1 is None:
            return None
        return float(1 - stats.chi2.cdf(value, df1))
    if st == "f":
        if df1 is None or df2 is None:
            return None
        return float(1 - stats.f.cdf(value, df1, df2))
    return None


def check_test_statistic_p(stat_type: str, value: float, reported_p: float,
                           df1=None, df2=None, ratio_tolerance: float = 3.0) -> Check:
    rid = "STAT-007-test-statistic-p"
    rec = p_from_test_statistic(stat_type, value, df1, df2)
    if rec is None:
        return Check(rid, INCONCLUSIVE, "缺少必要的自由度")
    if rec < 1e-12 and reported_p < 1e-3:
        return Check(rid, PASS, "兩者皆極小，一致")
    ratio = max(reported_p, rec) / max(min(reported_p, rec), 1e-12)
    obs = {"stat_type": stat_type, "value": value, "df1": df1, "df2": df2,
           "reported_p": reported_p}
    if ratio > ratio_tolerance:
        return Check(rid, FAIL,
                     f"由 {stat_type}={value} 重算 p={rec:.4g}，報告為 {reported_p:.4g}",
                     obs, {"p": rec, "ratio": ratio})
    return Check(rid, PASS, f"檢定統計量與 p 值一致（比值 {ratio:.2f}）", obs, {"p": rec})


# ---------------------------------------------------------------------------
# 11–13. 效果量重算與設計誤用偵測
# ---------------------------------------------------------------------------

def cohens_d_independent(m1, sd1, n1, m2, sd2, n2) -> dict:
    sp = math.sqrt(((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / (n1 + n2 - 2))
    d = (m1 - m2) / sp
    df = n1 + n2 - 2
    J = 1 - 3 / (4 * df - 1)
    g = J * d
    se_d = math.sqrt((n1 + n2) / (n1 * n2) + d ** 2 / (2 * (n1 + n2)))
    z = _z_crit()
    return {"pooled_sd": sp, "cohens_d": d, "hedges_g": g,
            "correction_J": J, "se_d": se_d,
            "d_ci": [d - z * se_d, d + z * se_d]}


def check_smd(reported_smd: float, m1, sd1, n1, m2, sd2, n2,
              smd_type: str = "hedges_g", rel_tolerance: float = 0.10) -> Check:
    rid = "STAT-011-smd-recompute"
    try:
        rec = cohens_d_independent(m1, sd1, n1, m2, sd2, n2)
    except (ValueError, ZeroDivisionError) as exc:
        return Check(rid, INCONCLUSIVE, f"重算失敗：{exc}")
    val = rec["hedges_g"] if smd_type == "hedges_g" else rec["cohens_d"]
    denom = abs(val) if abs(val) > 1e-9 else 1.0
    rel = abs(reported_smd - val) / denom
    obs = {"reported_smd": reported_smd, "smd_type": smd_type}
    recd = {k: round(v, 5) if isinstance(v, float) else v for k, v in rec.items()
            if k != "d_ci"}
    # 常見錯誤：報告 Cohen's d 卻標為 Hedges' g，或反之
    alt = rec["cohens_d"] if smd_type == "hedges_g" else rec["hedges_g"]
    if rel > rel_tolerance:
        alt_rel = abs(reported_smd - alt) / (abs(alt) if abs(alt) > 1e-9 else 1.0)
        if alt_rel <= rel_tolerance:
            return Check(rid, FAIL,
                         f"報告值與 {smd_type} 不符，但與另一種 SMD 定義相符 "
                         f"（可能標錯類型）", obs, {**recd, "matches_instead": (
                             "cohens_d" if smd_type == "hedges_g" else "hedges_g")})
        return Check(rid, FAIL,
                     f"報告 SMD={reported_smd:.4g}，重算 {smd_type}={val:.4g}"
                     f"（相對差 {rel:.1%}）", obs, recd)
    return Check(rid, PASS, f"SMD 一致（相對差 {rel:.2%}）", obs, recd)


def check_paired_design_formula(design: str, analysis_reported: str,
                                df_reported: Optional[float],
                                n_subjects: Optional[int]) -> Check:
    """crossover / repeated-measures 不得誤用獨立樣本公式。
    以自由度作為確定性訊號：配對 t 檢定 df = n-1；獨立樣本 df = 2n-2。"""
    rid = "STAT-012-paired-vs-independent"
    paired_designs = {"RCT-crossover", "repeated-measures", "within-subject",
                      "matched-pairs"}
    if design not in paired_designs:
        return Check(rid, NOT_APPLICABLE, f"{design} 非配對設計")
    obs = {"design": design, "analysis_reported": analysis_reported,
           "df_reported": df_reported, "n_subjects": n_subjects}
    if "independent" in (analysis_reported or "").lower() or \
       "unpaired" in (analysis_reported or "").lower():
        return Check(rid, FAIL, "配對設計卻宣告使用獨立樣本分析", obs)
    if df_reported is None or n_subjects is None:
        return Check(rid, INCONCLUSIVE, "缺少 df 或受試者數，無法以自由度佐證", obs)
    if abs(df_reported - (n_subjects - 1)) < 0.5:
        return Check(rid, PASS, "自由度與配對分析一致（df = n-1）", obs)
    if abs(df_reported - (2 * n_subjects - 2)) < 0.5:
        return Check(rid, FAIL,
                     f"自由度 {df_reported} 對應獨立樣本公式（2n-2），"
                     f"但設計為 {design}", obs,
                     {"expected_paired_df": n_subjects - 1})
    return Check(rid, INCONCLUSIVE,
                 f"自由度 {df_reported} 既非 n-1 也非 2n-2，可能為混合模型", obs)


def check_sphericity_correction(test: str, df1: float, df2: float,
                                correction: Optional[str],
                                n_levels: Optional[int],
                                n_subjects: Optional[int]) -> Check:
    """Greenhouse–Geisser / Huynh–Feldt 校正後 df 必須小於未校正 df。"""
    rid = "STAT-013-sphericity-df"
    if test.lower() != "rm-anova":
        return Check(rid, NOT_APPLICABLE, "非重複量數 ANOVA")
    if n_levels is None or n_subjects is None:
        return Check(rid, INCONCLUSIVE, "缺少水準數或受試者數")
    uncorrected_df1 = n_levels - 1
    uncorrected_df2 = (n_levels - 1) * (n_subjects - 1)
    obs = {"df1": df1, "df2": df2, "correction": correction,
           "uncorrected_df1": uncorrected_df1, "uncorrected_df2": uncorrected_df2}
    if correction in (None, "none", "sphericity-assumed"):
        if abs(df1 - uncorrected_df1) > 0.01 or abs(df2 - uncorrected_df2) > 0.01:
            return Check(rid, FAIL,
                         "宣告未校正，但 df 與未校正值不符（可能實際有校正卻未標示）", obs)
        return Check(rid, PASS, "未校正 df 與設計一致", obs)
    if df1 > uncorrected_df1 + 0.01 or df2 > uncorrected_df2 + 0.01:
        return Check(rid, FAIL,
                     f"宣告 {correction} 校正，但校正後 df 大於未校正 df", obs)
    epsilon = df1 / uncorrected_df1 if uncorrected_df1 else float("nan")
    lower_bound_eps = 1 / (n_levels - 1)
    if epsilon < lower_bound_eps - 0.01:
        return Check(rid, FAIL,
                     f"隱含 epsilon={epsilon:.3f} 低於理論下界 {lower_bound_eps:.3f}",
                     obs, {"implied_epsilon": epsilon})
    return Check(rid, PASS, f"校正後 df 合理（隱含 epsilon={epsilon:.3f}）", obs,
                 {"implied_epsilon": epsilon})


# ---------------------------------------------------------------------------
# GRIM / GRIMMER —— 嚴格守衛適用範圍
# ---------------------------------------------------------------------------

def _decimals(value_str: str) -> int:
    d = Decimal(str(value_str))
    return max(-d.as_tuple().exponent, 0)


def grim_test(reported_mean: str, n: int, items_per_subject: int = 1,
              is_discrete_integer_scale: bool = True) -> Check:
    """GRIM：n 個整數（或 k 個整數項目之平均）的平均值，其可能取值是離散的。

    契約要求：只在離散整數量表或可由整數項目形成的平均值上使用。
    本函式強制傳入 is_discrete_integer_scale，為 False 時回傳 NOT_APPLICABLE。
    """
    rid = "STAT-014-grim"
    if not is_discrete_integer_scale:
        return Check(rid, NOT_APPLICABLE,
                     "量表非離散整數構成，GRIM 的數學假設不成立")
    if n is None or n <= 0 or n > 10000:
        return Check(rid, INCONCLUSIVE, "n 不適用於 GRIM")
    dec = _decimals(reported_mean)
    if dec == 0:
        return Check(rid, INCONCLUSIVE, "報告平均無小數位，GRIM 無鑑別力")
    mean = float(reported_mean)
    granularity = 1.0 / (n * items_per_subject)
    nearest = round(mean / granularity) * granularity
    tol = 0.5 * 10 ** (-dec) + 1e-9
    obs = {"reported_mean": reported_mean, "n": n,
           "items_per_subject": items_per_subject, "decimals": dec}
    rec = {"granularity": granularity, "nearest_consistent_mean": round(nearest, 10),
           "abs_diff": abs(mean - nearest)}
    if abs(mean - nearest) <= tol:
        return Check(rid, PASS, "GRIM 一致", obs, rec)
    return Check(rid, FAIL,
                 f"GRIM 不一致：平均 {mean} 在 n={n} 下不可能出現", obs, rec)


def grimmer_test(reported_mean: str, reported_sd: str, n: int,
                 items_per_subject: int = 1,
                 is_discrete_integer_scale: bool = True) -> Check:
    """GRIMMER：n 個整數的變異數受平方和為整數的約束。

    實作採區間搜尋：在報告平均與 SD 的捨入區間內，尋找是否存在一組
    (平方和為整數) 的可行解。找不到即為不一致。
    """
    rid = "STAT-015-grimmer"
    if not is_discrete_integer_scale:
        return Check(rid, NOT_APPLICABLE,
                     "量表非離散整數構成，GRIMMER 的數學假設不成立")
    if n is None or n < 2 or n > 5000:
        return Check(rid, INCONCLUSIVE, "n 不適用於 GRIMMER")
    dm, ds = _decimals(reported_mean), _decimals(reported_sd)
    if dm == 0 or ds == 0:
        return Check(rid, INCONCLUSIVE, "平均或 SD 無小數位，GRIMMER 鑑別力不足")

    mean, sd = float(reported_mean), float(reported_sd)
    gran = 1.0 / (n * items_per_subject)
    tol_m = 0.5 * 10 ** (-dm)
    tol_s = 0.5 * 10 ** (-ds)

    # 候選平均：捨入區間內所有 GRIM-一致的值
    lo_k = math.ceil((mean - tol_m) / gran - 1e-9)
    hi_k = math.floor((mean + tol_m) / gran + 1e-9)
    obs = {"mean": reported_mean, "sd": reported_sd, "n": n}
    if hi_k < lo_k:
        return Check(rid, FAIL, "捨入區間內不存在 GRIM-一致的平均值", obs)

    scale = float(items_per_subject)   # 每位受試者的值 = 整數 / scale
    for k in range(lo_k, hi_k + 1):
        cand_mean = k * gran
        # 平方和 SS = (n-1)*sd^2 + n*mean^2；以整數尺度表示需乘 scale^2
        ss_lo = (n - 1) * (max(sd - tol_s, 0.0) ** 2) + n * cand_mean ** 2
        ss_hi = (n - 1) * ((sd + tol_s) ** 2) + n * cand_mean ** 2
        lo_i = math.ceil(ss_lo * scale ** 2 - 1e-9)
        hi_i = math.floor(ss_hi * scale ** 2 + 1e-9)
        if hi_i >= lo_i:
            return Check(rid, PASS, "GRIMMER 一致（存在可行的整數平方和）", obs,
                         {"feasible_mean": round(cand_mean, 10),
                          "integer_ss_range": [lo_i, hi_i]})
    return Check(rid, FAIL,
                 "GRIMMER 不一致：捨入區間內不存在整數平方和的可行解", obs)


# ---------------------------------------------------------------------------
# Magnitude-Based Inference 守衛
# ---------------------------------------------------------------------------

def check_inference_framework(framework: str, has_conventional_statistics: bool,
                              claim_type: str) -> Check:
    """MBI 不得單獨支撐 Approved efficacy Claim。"""
    rid = "STAT-016-inference-framework"
    mbi = {"MBI", "magnitude-based-inference", "magnitude-based-decisions", "MBD"}
    obs = {"framework": framework, "has_conventional_statistics":
           has_conventional_statistics, "claim_type": claim_type}
    if framework not in mbi:
        return Check(rid, PASS, "使用常規推論框架", obs)
    if has_conventional_statistics:
        return Check(rid, PASS,
                     "使用 MBI 但同時提供可核對的常規統計，以常規統計為準", obs)
    if claim_type in {"efficacy", "harm"}:
        return Check(rid, FAIL,
                     "僅有 MBI 且無常規統計可核對，不得支撐 efficacy/harm Claim；"
                     "本研究只能標記為 exploratory", obs,
                     {"forced_label": "exploratory"})
    return Check(rid, PASS, "非 efficacy/harm 主張，MBI 可保留但標記 exploratory", obs,
                 {"forced_label": "exploratory"})


# ---------------------------------------------------------------------------
# 彙總
# ---------------------------------------------------------------------------

def run_all(sr: dict) -> dict:
    """對一個 StudyResult dict 執行所有適用檢查。"""
    checks: list[Check] = []
    m = sr.get("effectMeasure")
    est, lo, hi = sr.get("pointEstimate"), sr.get("ciLow"), sr.get("ciHigh")
    p = sr.get("pValue")

    if None not in (est, lo, hi) and m:
        checks.append(check_ci_symmetry(est, lo, hi, m))
        checks.append(check_p_vs_ci(est, lo, hi, m, p))
        checks.append(check_significance_coherence(lo, hi, m, p))

    if sr.get("events") and sr.get("armN"):
        checks.append(check_event_counts(sr["events"], sr["armN"]))
        if m in {"RR", "OR", "RD"} and len(sr["events"]) == 2 and est is not None:
            checks.append(check_effect_vs_2x2(m, est, sr["events"][0], sr["armN"][0],
                                              sr["events"][1], sr["armN"][1]))

    for arm in sr.get("armAccounting", []):
        checks.append(check_arm_accounting(
            arm.get("randomised"), arm.get("analysed"), arm.get("lostToFollowUp"),
            arm.get("excluded"), sr.get("analysisSet", "ITT")))

    ts = sr.get("testStatistic")
    if ts and p is not None:
        checks.append(check_test_statistic_p(ts["type"], ts["value"], p,
                                             ts.get("df1"), ts.get("df2")))

    ad = sr.get("armDescriptives")
    if ad and m == "SMD" and est is not None:
        checks.append(check_smd(est, ad["m1"], ad["sd1"], ad["n1"],
                                ad["m2"], ad["sd2"], ad["n2"],
                                sr.get("smdType", "hedges_g")))

    checks.append(check_paired_design_formula(
        sr.get("studyDesign", ""), sr.get("analysisReported", ""),
        (ts or {}).get("df1"), sr.get("nSubjects")))

    if sr.get("rmAnova"):
        r = sr["rmAnova"]
        checks.append(check_sphericity_correction(
            "rm-anova", r["df1"], r["df2"], r.get("correction"),
            r.get("nLevels"), r.get("nSubjects")))

    for d in sr.get("descriptives", []):
        checks.append(grim_test(d["mean"], d["n"], d.get("itemsPerSubject", 1),
                                d.get("isDiscreteIntegerScale", False)))
        if d.get("sd") is not None:
            checks.append(grimmer_test(d["mean"], d["sd"], d["n"],
                                       d.get("itemsPerSubject", 1),
                                       d.get("isDiscreteIntegerScale", False)))

    checks.append(check_inference_framework(
        sr.get("inferenceFramework", "frequentist"),
        sr.get("hasConventionalStatistics", True),
        sr.get("claimType", "efficacy")))

    fails = [c for c in checks if c.verdict == FAIL]
    inconclusive = [c for c in checks if c.verdict == INCONCLUSIVE]
    return {
        "checks": checks,
        "n_checks": len(checks),
        "n_fail": len(fails),
        "n_inconclusive": len(inconclusive),
        "blocking": bool(fails),
        "verdict": FAIL if fails else (INCONCLUSIVE if inconclusive else PASS),
        "failed_rules": [c.rule_id for c in fails],
    }
