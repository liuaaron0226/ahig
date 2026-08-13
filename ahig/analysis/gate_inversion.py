#!/usr/bin/env python3
"""
把「AC1 的 95% CI 下限 >= 0.80」這道閘門反解成可解釋的要求。

閘門其實同時施加兩個獨立限制：
  (1) 真值限制：true AC1 必須 > 0.80，這對應到一個隱含的「每位評分者最大誤差率」
  (2) 精度限制：CI 要夠窄，這對應到一個最小樣本數

契約作者通常只想要 (1)，但寫法上把 (2) 綁進去，導致「證據不足」被誤判成「品質不足」。
本腳本量化 (1)，讓契約可以把兩者拆開分別設定。
"""

from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np
from scipy.optimize import brentq
from ahig.bootstrap import configure_stdio

configure_stdio()
OUT = Path(__file__).resolve().parent / "results"
OUT.mkdir(parents=True, exist_ok=True)


def asymptotic_ac1(prev: np.ndarray, e: float, model: str = "uniform") -> float:
    """在誤差率 e 下，兩位獨立評分者的 AC1 漸近值（n -> 無限大）。"""
    K = len(prev)
    # 評分者的類別產出分布
    if model == "uniform":
        # P(rater=j) = prev[j]*(1-e) + sum_{t!=j} prev[t]*e/(K-1)
        marg = prev * (1 - e) + (e / (K - 1)) * (1 - prev)
        # 兩位評分者一致機率
        Pa = 0.0
        for t in range(K):
            # 給定真值 t，某位評分者的條件分布
            cond = np.full(K, e / (K - 1))
            cond[t] = 1 - e
            Pa += prev[t] * float((cond ** 2).sum())
    elif model == "modal":
        modal = int(np.argmax(prev))
        second = int(np.argsort(prev)[-2])
        Pa = 0.0
        marg = np.zeros(K)
        for t in range(K):
            cond = np.zeros(K)
            cond[t] = 1 - e
            tgt = second if t == modal else modal
            cond[tgt] += e
            Pa += prev[t] * float((cond ** 2).sum())
            marg += prev[t] * cond
    else:
        raise ValueError(model)

    Pe = float((marg * (1 - marg)).sum() / (K - 1))
    return (Pa - Pe) / (1 - Pe)


def max_error_rate_for_target(prev, target: float, model="uniform") -> float | None:
    prev = np.array(prev, dtype=float)
    f = lambda e: asymptotic_ac1(prev, e, model) - target
    if f(1e-9) < 0:
        return None            # 即使零誤差也達不到（Pe 太高）
    lo, hi = 1e-9, 0.9
    if f(hi) > 0:
        return hi
    return float(brentq(f, lo, hi, xtol=1e-6))


def main():
    field_shapes = [
        ("二分類，平衡 (0.50/0.50)", (0.50, 0.50), "uniform"),
        ("二分類，中度偏斜 (0.75/0.25)", (0.75, 0.25), "uniform"),
        ("二分類，高度偏斜 (0.90/0.10)", (0.90, 0.10), "uniform"),
        ("三分類，平衡", (1/3, 1/3, 1/3), "uniform"),
        ("四分類，RoB2 típ (0.25/0.35/0.25/0.15)", (0.25, 0.35, 0.25, 0.15), "uniform"),
        ("四分類，unclear 主導 (0.08/0.80/0.07/0.05)", (0.08, 0.80, 0.07, 0.05), "modal"),
        ("六分類，effect measure 類型", tuple([1/6]*6), "uniform"),
    ]
    rows = []
    for label, prev, model in field_shapes:
        row = {"field_shape": label, "error_model": model,
               "ac1_at_zero_error": round(asymptotic_ac1(np.array(prev), 1e-9, model), 4)}
        for tgt in (0.80, 0.85, 0.90):
            e = max_error_rate_for_target(prev, tgt, model)
            row[f"max_per_rater_error_for_AC1_{tgt}"] = (
                None if e is None else round(e, 4))
        rows.append(row)
        print(f"{label:44s} "
              f"AC1>=0.80 需誤差率 <= {row['max_per_rater_error_for_AC1_0.8']}"
              if False else "")

    for r in rows:
        print(f"{r['field_shape']:42s} | AC1>=0.80 需 e<= "
              f"{r['max_per_rater_error_for_AC1_0.8']} | AC1>=0.85 需 e<= "
              f"{r['max_per_rater_error_for_AC1_0.85']} | AC1>=0.90 需 e<= "
              f"{r['max_per_rater_error_for_AC1_0.9']}")

    payload = {
        "note": "e = 每位評分者的獨立誤分類率。這是把 AC1 門檻反解成可解釋的抽取品質要求。",
        "rows": rows,
    }
    (OUT / "gate_inversion.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"\n寫出 {OUT / 'gate_inversion.json'}")


if __name__ == "__main__":
    main()
