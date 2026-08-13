#!/usr/bin/env python3
"""
欄位裁決是人工工時的主導項（基準情境下佔 82%）。
本腳本反解：確定性層必須涵蓋多少比例的模型分歧，專案才能在給定期程內完成。
這是 coverage 期程指標，不是裁決 accuracy；accuracy 必須另由 gold set 驗證。

這把「確定性統計攔截層」從一個定性要求，變成一個有數字的設計目標。
"""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ahig.bootstrap import configure_stdio
from analysis.human_throughput import BASE, LOW, HIGH, corpus_hours, Params

configure_stdio()
OUT = Path(__file__).resolve().parent / "results"


def required_auto_resolution(p: Params, weekly_h: float, target_years: float,
                             working_weeks: int = 46) -> dict:
    h = corpus_hours(p, scoped=True)
    budget_h = weekly_h * working_weeks * target_years
    fixed_h = h["screening_h"] + h["manual_anchor_h"] + h["highrisk_claim_h"]
    adjud_budget = budget_h - fixed_h
    if adjud_budget <= 0:
        return {"feasible": False, "reason": "固定人工項已超出總預算",
                "budget_h": round(budget_h), "fixed_h": fixed_h,
                "adjudication_h_needed": h["field_adjudication_h"]}
    needed = h["field_adjudication_h"]
    auto_rate = 1.0 - adjud_budget / needed
    return {
        "feasible": auto_rate < 1.0,
        "budget_h": round(budget_h),
        "fixed_human_h": fixed_h,
        "adjudication_h_if_no_automation": needed,
        "adjudication_h_budget": round(adjud_budget),
        "required_deterministic_resolution_coverage": round(max(auto_rate, 0.0), 4),
    }


def main():
    rows = []
    print("必要的確定性自動消解率（讓專案在目標期程內收斂）")
    print("=" * 82)
    print(f"{'情境':<6}{'週產能':>8}{'目標期程':>10}{'裁決預算h':>12}{'需自動消解率':>14}{'可行':>8}")
    for p in (LOW, BASE, HIGH):
        for weekly in (10, 20):
            for years in (2, 3, 5):
                r = required_auto_resolution(p, weekly, years)
                rows.append({"scenario": p.label, "weekly_h": weekly,
                             "target_years": years, **r})
                rate = r.get("required_deterministic_resolution_coverage")
                print(f"{p.label:<6}{weekly:>6}h/週{years:>8}年"
                      f"{r.get('adjudication_h_budget', 0):>12}"
                      f"{(f'{rate:.1%}' if rate is not None else 'n/a'):>14}"
                      f"{('是' if r['feasible'] else '否'):>8}")

    print()
    print("解讀：coverage = 確定性層在無人介入下處理的分歧比例；不代表處理正確率。")
    print("可行的來源包括：數值矛盾時採用通過算術檢查的一方、單位換算後實為同值、")
    print("引用 anchor 唯一命中而另一方無 anchor、schema 列舉值正規化後同義。")
    print()

    # 反向：若確定性層只能達到 60% / 70% / 80%，需要多少週產能
    print("若確定性自動消解率固定，基準情境下 3 年完成所需的週產能")
    print("=" * 60)
    h = corpus_hours(BASE, scoped=True)
    fixed = h["screening_h"] + h["manual_anchor_h"] + h["highrisk_claim_h"]
    cap_rows = []
    for auto in (0.0, 0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95):
        total = fixed + h["field_adjudication_h"] * (1 - auto)
        weekly = total / (46 * 3)
        cap_rows.append({"auto_rate": auto, "total_human_h": round(total),
                         "weekly_h_for_3y": round(weekly, 1)})
        print(f"  自動消解 {auto:>5.0%} -> 總人工 {total:>7,.0f}h -> "
              f"需 {weekly:>5.1f} h/週")

    (OUT / "adjudication_sensitivity.json").write_text(json.dumps(
        {"metric": "deterministic-resolution-coverage",
         "quality_metrics_not_implied": ["accuracy", "major-error-rate"],
         "policy_target_3y_10h_week": 0.875,
         "required_coverage": rows,
         "weekly_capacity_by_coverage_base_3y": cap_rows},
        ensure_ascii=False, indent=2), encoding="utf-8", newline="\n")
    print(f"\n寫出 {OUT / 'adjudication_sensitivity.json'}")


if __name__ == "__main__":
    main()
