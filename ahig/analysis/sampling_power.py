#!/usr/bin/env python3
"""
AHIG 品質閘門抽樣統計實算 (P1-5 / Gap C)

目的：解決契約中三個互相矛盾的數字
  (1) non-critical 抽樣「至少 10%，且不少於 30 筆」
  (2) non-critical error rate <= 1%
  (3) Gwet's AC1 的 95% CI 下限 >= 0.80

本腳本計算：
  A. 以 rule of three / Clopper-Pearson 精確法，驗證 error rate <= 1% 所需的最小樣本數
  B. 以蒙地卡羅模擬，求 P(AC1 之 95% CI 下限 >= 0.80) >= 0.80 所需的最小樣本數
     涵蓋不同類別數、不同 prevalence 偏斜度、不同真實一致率、兩種誤分類模型
  C. 與 Cohen's kappa 對照，量化 prevalence paradox，佐證以 AC1 為主指標的決定

所有輸出為「在明列假設下的模型結果」，非外部經驗常數。
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, asdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from scipy import stats
from ahig.bootstrap import configure_stdio

configure_stdio()
RNG_SEED = 20260813
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# A. error-rate 可驗證性
# ---------------------------------------------------------------------------

def clopper_pearson_upper(k: int, n: int, alpha: float = 0.05) -> float:
    """單側 (1-alpha) Clopper-Pearson 上界。k = 觀察到的錯誤數。"""
    if k >= n:
        return 1.0
    return float(stats.beta.ppf(1 - alpha, k + 1, n - k))


def min_n_for_error_ceiling(ceiling: float, observed_errors: int = 0,
                            alpha: float = 0.05, n_max: int = 200_000) -> int:
    """在觀察到 observed_errors 個錯誤的前提下，要讓 95% 單側上界 <= ceiling
    所需的最小 n。"""
    lo, hi = observed_errors + 1, n_max
    while lo < hi:
        mid = (lo + hi) // 2
        if clopper_pearson_upper(observed_errors, mid, alpha) <= ceiling:
            hi = mid
        else:
            lo = mid + 1
    return lo


def error_rate_table() -> dict:
    rows = []
    for ceiling in (0.05, 0.02, 0.01, 0.005):
        for errs in (0, 1, 2, 3):
            rows.append({
                "ceiling": ceiling,
                "observed_errors": errs,
                "min_n": min_n_for_error_ceiling(ceiling, errs),
            })
    # 反向：現行 n=30 / n=100 / n=300 各能證明到什麼上界
    achievable = [{
        "n": n,
        "observed_errors": 0,
        "upper_95": round(clopper_pearson_upper(0, n), 4),
    } for n in (30, 50, 100, 200, 300, 500, 1000)]
    return {"min_n_required": rows, "achievable_ceiling_at_n": achievable}


# ---------------------------------------------------------------------------
# B. Gwet's AC1 —— 點估計與線性化變異數 (Gwet 2008)
# ---------------------------------------------------------------------------

def ac1_with_var(r1: np.ndarray, r2: np.ndarray, categories: list[int]):
    """兩位評分者、K 個類別的 Gwet AC1 與其線性化變異數。

    回傳 (ac1, var, se)。
    """
    n = len(r1)
    K = len(categories)
    if K < 2:
        raise ValueError("需要至少兩個類別")

    # 每個項目、每個類別，兩位評分者中指派到該類別的比例
    pi_i = np.zeros((n, K))
    for j, c in enumerate(categories):
        pi_i[:, j] = ((r1 == c).astype(float) + (r2 == c).astype(float)) / 2.0

    pi_hat = pi_i.mean(axis=0)                       # 邊際類別比例
    pa_i = (r1 == r2).astype(float)                  # 每項目的一致指標
    Pa = pa_i.mean()

    Pe = float((pi_hat * (1.0 - pi_hat)).sum() / (K - 1))
    if math.isclose(Pe, 1.0):
        return float("nan"), float("nan"), float("nan")

    ac1 = (Pa - Pe) / (1.0 - Pe)

    # 每項目的 chance-agreement 貢獻
    Pe_i = (pi_i * (1.0 - pi_hat)).sum(axis=1) / (K - 1)

    gamma_i = (pa_i - Pe) / (1.0 - Pe)
    gamma_star = gamma_i - 2.0 * (1.0 - ac1) * (Pe_i - Pe) / (1.0 - Pe)
    var = float(((gamma_star - ac1) ** 2).sum() / (n * (n - 1)))
    return float(ac1), var, math.sqrt(max(var, 0.0))


def cohen_kappa(r1: np.ndarray, r2: np.ndarray, categories: list[int]) -> float:
    n = len(r1)
    Po = float((r1 == r2).mean())
    Pe = 0.0
    for c in categories:
        Pe += ((r1 == c).sum() / n) * ((r2 == c).sum() / n)
    if math.isclose(Pe, 1.0):
        return float("nan")
    return (Po - Pe) / (1.0 - Pe)


# ---------------------------------------------------------------------------
# 資料生成模型
# ---------------------------------------------------------------------------

def simulate_ratings(rng, n: int, prevalence: np.ndarray, error_rate: float,
                     error_model: str):
    """生成兩位獨立評分者的評分。

    error_model:
      'uniform' —— 誤分類均勻散佈到其他類別
      'modal'   —— 誤分類全部倒向最大宗類別（模擬 'unclear' 預設值行為）
    """
    K = len(prevalence)
    truth = rng.choice(K, size=n, p=prevalence)
    modal = int(np.argmax(prevalence))

    def rate(t):
        err = rng.random(n) < error_rate
        out = t.copy()
        if err.any():
            if error_model == "uniform":
                # 從其他 K-1 類均勻抽
                shift = rng.integers(1, K, size=err.sum())
                out[err] = (t[err] + shift) % K
            elif error_model == "modal":
                cand = np.full(err.sum(), modal)
                # 本來就是 modal 的，倒向次大類別，避免「錯了但仍相同」
                second = int(np.argsort(prevalence)[-2])
                cand[t[err] == modal] = second
                out[err] = cand
            else:
                raise ValueError(error_model)
        return out

    return rate(truth), rate(truth)


@dataclass
class Scenario:
    label: str
    prevalence: tuple
    error_rate: float
    error_model: str


def power_for_n(rng, sc: Scenario, n: int, threshold: float, n_sims: int):
    """回傳 (P(CI 下限 >= threshold), 平均 AC1, 平均 CI 下限, 平均 kappa)"""
    K = len(sc.prevalence)
    cats = list(range(K))
    prev = np.array(sc.prevalence, dtype=float)
    z = stats.norm.ppf(0.975)

    hits = 0
    ac1s, lowers, kappas = [], [], []
    for _ in range(n_sims):
        r1, r2 = simulate_ratings(rng, n, prev, sc.error_rate, sc.error_model)
        ac1, var, se = ac1_with_var(r1, r2, cats)
        if math.isnan(ac1):
            continue
        # 用 t 分布（df = n-1），對小樣本較保守，與 Gwet 建議一致
        tcrit = stats.t.ppf(0.975, n - 1)
        lower = ac1 - tcrit * se
        ac1s.append(ac1)
        lowers.append(lower)
        kappas.append(cohen_kappa(r1, r2, cats))
        if lower >= threshold:
            hits += 1
    m = len(ac1s)
    return (hits / m if m else float("nan"),
            float(np.mean(ac1s)) if m else float("nan"),
            float(np.mean(lowers)) if m else float("nan"),
            float(np.nanmean(kappas)) if m else float("nan"))


def min_n_for_gate(rng, sc: Scenario, threshold: float = 0.80,
                   target_power: float = 0.80, n_sims: int = 1500,
                   grid=None):
    grid = grid or [20, 30, 40, 50, 60, 75, 100, 125, 150, 200, 250,
                    300, 400, 500, 750, 1000, 1500, 2000]
    detail = []
    answer = None
    for n in grid:
        power, ac1, lower, kap = power_for_n(rng, sc, n, threshold, n_sims)
        detail.append({"n": n, "power": round(power, 3),
                       "mean_ac1": round(ac1, 4),
                       "mean_ci_lower": round(lower, 4),
                       "mean_kappa": round(kap, 4)})
        if answer is None and power >= target_power:
            answer = n
    return answer, detail


def ac1_study() -> dict:
    rng = np.random.default_rng(RNG_SEED)
    scenarios = [
        # 二分類，平衡
        Scenario("binary-balanced-err02", (0.50, 0.50), 0.02, "uniform"),
        Scenario("binary-balanced-err05", (0.50, 0.50), 0.05, "uniform"),
        Scenario("binary-balanced-err10", (0.50, 0.50), 0.10, "uniform"),
        # 二分類，偏斜 —— 對應 prespecification status 之類的欄位
        Scenario("binary-skew90-err05", (0.90, 0.10), 0.05, "uniform"),
        Scenario("binary-skew90-err05-modal", (0.90, 0.10), 0.05, "modal"),
        Scenario("binary-skew95-err05-modal", (0.95, 0.05), 0.05, "modal"),
        # 四分類 —— 對應 RoB 2 domain judgement
        Scenario("rob2-4cat-err05", (0.25, 0.35, 0.25, 0.15), 0.05, "uniform"),
        Scenario("rob2-4cat-err10", (0.25, 0.35, 0.25, 0.15), 0.10, "uniform"),
        Scenario("rob2-4cat-skew-err10-modal", (0.15, 0.60, 0.15, 0.10), 0.10, "modal"),
        # 高偏斜四分類，誤差倒向 modal（最惡劣但很常見）
        Scenario("skew-unclear-dominant-err08-modal", (0.08, 0.80, 0.07, 0.05), 0.08, "modal"),
    ]
    results = {}
    for sc in scenarios:
        n_req, detail = min_n_for_gate(rng, sc)
        results[sc.label] = {
            "scenario": asdict(sc),
            "min_n_for_ci_lower_0.80_at_power_0.80": n_req,
            "search_grid_max": max(row["n"] for row in detail),
            "not_reached_within_grid": n_req is None,
            "grid": detail,
        }
        print(f"  {sc.label:38s} -> min n = {n_req}")
    return results


# ---------------------------------------------------------------------------
# C. n=30 到底能證明什麼
# ---------------------------------------------------------------------------

def n30_reality_check() -> dict:
    rng = np.random.default_rng(RNG_SEED + 1)
    out = []
    for sc in [
        Scenario("binary-balanced-err02", (0.50, 0.50), 0.02, "uniform"),
        Scenario("binary-balanced-err05", (0.50, 0.50), 0.05, "uniform"),
        Scenario("rob2-4cat-err05", (0.25, 0.35, 0.25, 0.15), 0.05, "uniform"),
        Scenario("skew-unclear-dominant-err08-modal", (0.08, 0.80, 0.07, 0.05), 0.08, "modal"),
    ]:
        for n in (30, 50, 100):
            p, ac1, lower, kap = power_for_n(rng, sc, n, 0.80, 3000)
            out.append({"scenario": sc.label, "n": n,
                        "P(ci_lower>=0.80)": round(p, 3),
                        "mean_ac1": round(ac1, 4),
                        "mean_ci_lower": round(lower, 4),
                        "mean_kappa": round(kap, 4),
                        "ac1_minus_kappa": round(ac1 - kap, 4)})
    return {"rows": out}


# ---------------------------------------------------------------------------
# 交叉驗證：bootstrap 對照線性化變異數
# ---------------------------------------------------------------------------

def bootstrap_cross_check(n_boot: int = 4000) -> dict:
    rng = np.random.default_rng(RNG_SEED + 2)
    checks = []
    for sc, n in [
        (Scenario("binary-balanced-err05", (0.5, 0.5), 0.05, "uniform"), 100),
        (Scenario("rob2-4cat-err10", (0.25, 0.35, 0.25, 0.15), 0.10, "uniform"), 150),
        (Scenario("skew-unclear-dominant-err08-modal", (0.08, 0.80, 0.07, 0.05), 0.08, "modal"), 200),
    ]:
        cats = list(range(len(sc.prevalence)))
        r1, r2 = simulate_ratings(rng, n, np.array(sc.prevalence), sc.error_rate, sc.error_model)
        ac1, var, se = ac1_with_var(r1, r2, cats)
        tcrit = stats.t.ppf(0.975, n - 1)
        analytic_lower = ac1 - tcrit * se

        boots = []
        idx_all = np.arange(n)
        for _ in range(n_boot):
            idx = rng.choice(idx_all, size=n, replace=True)
            a, _, _ = ac1_with_var(r1[idx], r2[idx], cats)
            if not math.isnan(a):
                boots.append(a)
        boot_lower = float(np.percentile(boots, 2.5))
        checks.append({
            "scenario": sc.label, "n": n,
            "ac1": round(ac1, 4),
            "analytic_se": round(se, 4),
            "bootstrap_se": round(float(np.std(boots, ddof=1)), 4),
            "analytic_ci_lower": round(analytic_lower, 4),
            "bootstrap_ci_lower": round(boot_lower, 4),
            "abs_diff_lower": round(abs(analytic_lower - boot_lower), 4),
        })
        print(f"  cross-check {sc.label:38s} analytic={analytic_lower:.4f} "
              f"bootstrap={boot_lower:.4f}")
    return {"checks": checks}


def main():
    print("== A. error-rate 可驗證性 ==")
    err = error_rate_table()
    for r in err["achievable_ceiling_at_n"]:
        print(f"  n={r['n']:5d}, 0 errors -> 95% 上界 = {r['upper_95']:.2%}")
    n1 = min_n_for_error_ceiling(0.01, 0)
    print(f"  要證明 error rate <= 1%（0 錯誤）需要 n >= {n1}")

    print("\n== B. AC1 CI 下限 >= 0.80 所需最小 n ==")
    ac1 = ac1_study()

    print("\n== C. n=30 現實檢查 ==")
    n30 = n30_reality_check()

    print("\n== D. bootstrap 交叉驗證 ==")
    xcheck = bootstrap_cross_check()

    payload = {
        "meta": {
            "seed": RNG_SEED,
            "note": "模型輸出，非外部經驗常數。假設：兩位獨立評分者、"
                    "誤分類率固定、項目間獨立。",
            "ac1_variance_estimator": "Gwet (2008) linearization, t(df=n-1) critical value",
        },
        "error_rate_verifiability": err,
        "ac1_min_sample_size": ac1,
        "n30_reality_check": n30,
        "bootstrap_cross_check": xcheck,
        "derived_min_n_for_1pct_error_ceiling": n1,
    }
    p = OUT / "sampling_power.json"
    p.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"\n寫出 {p}")


if __name__ == "__main__":
    main()
