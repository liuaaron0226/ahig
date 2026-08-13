#!/usr/bin/env python3
"""
自我檢查：
1. 我的「超額中位」指標會不會高估小樣本組？（用 pooled 差值對照）
2. 擇時 vs 選股：哪個解釋力大？（變異數分解）
"""
import sys
import statistics
import collections

import numpy as np

sys.path.insert(0, "scripts")
from hypo_test import (load, build_observations, month_stats, excess_stats,
                       block_bootstrap_ci, deciles)

np.random.seed(53)


def sec(t):
    print("\n" + "═" * 100)
    print(t)
    print("═" * 100)


def main():
    data = load()
    obs = build_observations(data, use_adj=True)
    msta = month_stats(obs)
    mkt_med = statistics.median([r["f12"] for r in obs])
    mkt_hit = sum(1 for r in obs if r["f12"] > 100) / len(obs) * 100

    # ── 1. 指標偏誤檢查 ─────────────────────────────────────
    sec("1. 我的『超額中位』會不會高估小樣本組？三種算法對照")
    groups = {
        "低價<10元": [r for r in obs if r["price"] < 10],
        "低價<15元": [r for r in obs if r["price"] < 15],
        "貼近12M高點>95%": [r for r in obs if r["near12h"] and r["near12h"] > 0.95],
        "創36M新高": [r for r in obs if r["to_high36"] <= 0.0001],
        "低價<15 且 貼近12M高點": [r for r in obs if r["price"] < 15
                             and r["near12h"] and r["near12h"] > 0.95],
        "原始假說B": [r for r in obs if r["off_low36"] >= 1.0 and r["to_high36"] >= 1.0],
        "距高點>100%": [r for r in obs if r["to_high36"] >= 1.0],
    }
    print(f"{'組別':<26}{'N':>8}{'每月檔數':>9}{'A:月中位平均':>14}"
          f"{'B:合併中位差':>14}{'C:月中位差中位':>15}")
    print("─" * 88)
    for lab, sel in groups.items():
        ex = excess_stats(sel, msta)
        pooled = statistics.median([r["f12"] for r in sel]) - mkt_med
        per_month = len(sel) / len({r["ym"] for r in sel})
        print(f"{lab:<26}{len(sel):>8,}{per_month:>9.0f}{ex['ex_med']:>13.1f}%"
              f"{pooled:>13.1f}%{ex['ex_med_median']:>14.1f}%")
    print("\nA = 每月(組中位−市場中位)再平均 ← 我前面用的")
    print("B = 全期合併中位 − 全市場合併中位 ← 最保守，但混入擇時")
    print("C = 每月差值取中位 ← 對離群月份穩健")
    print("若 A 遠大於 B 和 C，代表 A 被少數極端月份（如 2020）拉高。")

    # 用 mean-based 的月度差再算一次（避免小樣本中位數偏誤）
    print("\n改用『每月平均報酬差』（不受中位數小樣本偏誤影響）：")
    print(f"{'組別':<26}{'月平均差(平均)':>16}{'月平均差(中位)':>16}{'月勝率':>9}{'p':>9}")
    print("─" * 78)
    for lab, sel in groups.items():
        bym = collections.defaultdict(list)
        for r in sel:
            bym[r["ym"]].append(r["f12"])
        allm = collections.defaultdict(list)
        for r in obs:
            allm[r["ym"]].append(r["f12"])
        d = [statistics.mean(bym[m]) - statistics.mean(allm[m])
             for m in bym if len(allm[m]) >= 30]
        ci = block_bootstrap_ci(d)
        print(f"{lab:<26}{statistics.mean(d):>15.1f}%{statistics.median(d):>15.1f}%"
              f"{sum(1 for x in d if x>0)/len(d)*100:>8.0f}%{ci['p']:>9.4f}")

    # ── 2. 擇時 vs 選股 ─────────────────────────────────────
    sec("2. 擇時 vs 選股：哪個決定你能不能抓到翻倍股？")
    bym = collections.defaultdict(list)
    for r in obs:
        bym[r["ym"]].append(r)
    months = [m for m in bym if len(bym[m]) >= 30]
    hit_by_month = [sum(1 for r in bym[m] if r["f12"] > 100) / len(bym[m]) * 100
                    for m in months]
    print(f"全市場翻倍率：平均 {statistics.mean(hit_by_month):.2f}%，"
          f"標準差 {statistics.pstdev(hit_by_month):.2f}%")
    print(f"  最低月 {min(hit_by_month):.2f}%   最高月 {max(hit_by_month):.2f}%")
    print(f"  月間全距 = {max(hit_by_month)-min(hit_by_month):.1f} 個百分點")

    screens = {
        "低價<10": [r for r in obs if r["price"] < 10],
        "低價<5": [r for r in obs if r["price"] < 5],
        "貼近12M高": [r for r in obs if r["near12h"] and r["near12h"] > 0.95],
        "創36M新高": [r for r in obs if r["to_high36"] <= 0.0001],
        "距高點>100%": [r for r in obs if r["to_high36"] >= 1.0],
        "高波動前10%": deciles(obs, "sd12", reverse=True),
        "低波動後10%": deciles(obs, "sd12", reverse=False),
        "動能12M前10%": deciles(obs, "r12", reverse=True),
    }
    srates = {k: sum(1 for r in v if r["f12"] > 100) / len(v) * 100
              for k, v in screens.items()}
    srates["【全市場】"] = mkt_hit
    print(f"\n各篩選的翻倍率：標準差 "
          f"{statistics.pstdev(list(srates.values())):.2f}%，"
          f"全距 {max(srates.values())-min(srates.values()):.1f} 個百分點")
    for k, v in sorted(srates.items(), key=lambda x: -x[1]):
        print(f"   {k:<16}{v:>6.2f}%")

    print(f"\n對照：")
    print(f"  換『月份』造成的翻倍率差異 = {max(hit_by_month)-min(hit_by_month):.1f} 個百分點")
    print(f"  換『篩選』造成的翻倍率差異 = "
          f"{max(srates.values())-min(srates.values()):.1f} 個百分點")

    # 在最好與最差的月份，篩選還有用嗎
    print("\n把月份按全市場翻倍率分三段，看篩選在各段的加值：")
    order = sorted(months, key=lambda m: sum(1 for r in bym[m] if r["f12"] > 100) / len(bym[m]))
    t = len(order) // 3
    tiers = {"冷（翻倍率最低1/3）": set(order[:t]),
             "中": set(order[t:2 * t]),
             "熱（翻倍率最高1/3）": set(order[2 * t:])}
    print(f"{'月份分段':<22}{'全市場翻倍率':>14}{'低價<10':>11}{'創36M新高':>11}"
          f"{'距高點>100%':>13}")
    print("─" * 72)
    for tn, ms in tiers.items():
        base = [r for r in obs if r["ym"] in ms]
        b = sum(1 for r in base if r["f12"] > 100) / len(base) * 100
        row = f"{tn:<22}{b:>13.2f}%"
        for sk in ["低價<10", "創36M新高", "距高點>100%"]:
            g = [r for r in screens[sk] if r["ym"] in ms]
            row += f"{sum(1 for r in g if r['f12']>100)/len(g)*100:>10.2f}%" if g else f"{'—':>11}"
        print(row)


if __name__ == "__main__":
    main()
