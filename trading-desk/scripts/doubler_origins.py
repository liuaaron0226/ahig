#!/usr/bin/env python3
"""
反向問法：實際上翻倍的股票，當初長什麼樣？
（前面都是「符合條件的股票後來如何」，這裡問「後來翻倍的股票當初如何」）

外加：直接對決「距高點遠」vs「貼近高點」——使用者的核心假設。
"""
import sys
import statistics
import collections

import numpy as np

sys.path.insert(0, "scripts")
from hypo_test import (load, build_observations, month_stats, excess_stats,
                       block_bootstrap_ci)

np.random.seed(41)


def sec(t):
    print("\n" + "═" * 100)
    print(t)
    print("═" * 100)


def main():
    data = load()
    obs = build_observations(data, use_adj=True)
    msta = month_stats(obs)
    doublers = [r for r in obs if r["f12"] > 100]
    print(f"觀測點 {len(obs):,}，其中 12 個月內翻倍 {len(doublers):,} "
          f"（{len(doublers)/len(obs)*100:.2f}%）")

    # ── 1. 翻倍股的「出發點」長相 ──────────────────────────
    sec("1. 後來翻倍的股票，訊號當下長什麼樣？（條件機率反過來看）")

    def dist(key, bins, labels, fmt="{:.2f}"):
        print(f"\n── {key} ──")
        print(f"{'區間':<20}{'全樣本占比':>12}{'翻倍股占比':>12}{'倍率':>8}"
              f"{'該區間翻倍率':>14}")
        print("─" * 68)
        for (lo, hi), lab in zip(bins, labels):
            a = [r for r in obs if r[key] is not None and lo <= r[key] < hi]
            d = [r for r in doublers if r[key] is not None and lo <= r[key] < hi]
            if not a:
                continue
            pa = len(a) / len(obs) * 100
            pd = len(d) / len(doublers) * 100
            print(f"{lab:<20}{pa:>11.1f}%{pd:>11.1f}%{pd/pa if pa else 0:>8.2f}"
                  f"{len(d)/len(a)*100:>13.2f}%")

    dist("price", [(0, 5), (5, 10), (10, 20), (20, 50), (50, 100), (100, 1e9)],
         ["<5元", "5–10元", "10–20元", "20–50元", "50–100元", ">100元"])
    dist("to_high36", [(-1, 0.0001), (0.0001, 0.3), (0.3, 0.5), (0.5, 1.0), (1.0, 1e9)],
         ["創36M新高", "距高點<30%", "距高點30–50%", "距高點50–100%", "距高點>100%"])
    dist("dd_all", [(-1, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 1.1)],
         ["距歷史高<30%", "30–50%", "50–70%", "70–85%", ">85%"])
    dist("sd12", [(0, 0.05), (0.05, 0.08), (0.08, 0.12), (0.12, 0.20), (0.20, 9)],
         ["月SD<5%", "5–8%", "8–12%", "12–20%", ">20%"])
    dist("r12", [(-1, -0.3), (-0.3, 0), (0, 0.3), (0.3, 1.0), (1.0, 99)],
         ["過去1年<-30%", "-30~0%", "0~30%", "30~100%", ">100%"])

    # ── 2. 頭對頭：距高點遠 vs 貼近高點 ────────────────────
    sec("2. 頭對頭：使用者的核心假設（距高點遠）vs 反面（貼近高點）")
    pairs = {
        "距36M高點還有>100%空間": [r for r in obs if r["to_high36"] >= 1.0],
        "距36M高點還有50–100%": [r for r in obs if 0.5 <= r["to_high36"] < 1.0],
        "距36M高點還有30–50%": [r for r in obs if 0.3 <= r["to_high36"] < 0.5],
        "距36M高點<30%（貼近）": [r for r in obs if 0 < r["to_high36"] < 0.3],
        "創36M新高": [r for r in obs if r["to_high36"] <= 0.0001],
    }
    print(f"{'組別':<28}{'N':>8}{'中位':>9}{'平均':>9}{'破百率':>9}{'<-20%':>9}"
          f"{'超額中位':>10}{'超額破百':>10}{'月勝率':>8}{'p':>8}")
    print("─" * 108)
    for lab, sel in pairs.items():
        f = [r["f12"] for r in sel]
        ex = excess_stats(sel, msta)
        ci = block_bootstrap_ci(ex["series"])
        print(f"{lab:<28}{len(sel):>8,}{statistics.median(f):>8.1f}%"
              f"{statistics.mean(f):>8.1f}%"
              f"{sum(1 for x in f if x>100)/len(f)*100:>8.2f}%"
              f"{sum(1 for x in f if x<-20)/len(f)*100:>8.1f}%"
              f"{ex['ex_med']:>9.1f}%{ex['ex_hit100']:>9.2f}%"
              f"{ex['win_rate']:>7.0f}%{ci['p']:>8.4f}")

    # ── 3. 最佳組合：低價 + 貼近高點 ───────────────────────
    sec("3. 把兩個有效訊號疊起來：低價 × 貼近12M高點")
    combos = {
        "全市場": obs,
        "只有低價(<15元)": [r for r in obs if r["price"] < 15],
        "只有貼近12M高點(>95%)": [r for r in obs if r["near12h"] and r["near12h"] > 0.95],
        "低價<15 且 貼近12M高點": [r for r in obs if r["price"] < 15
                             and r["near12h"] and r["near12h"] > 0.95],
        "低價<15 且 貼近高點 且 2022後": [r for r in obs if r["price"] < 15
                                 and r["near12h"] and r["near12h"] > 0.95
                                 and r["ym"] >= "2022"],
    }
    print(f"{'組別':<30}{'N':>8}{'中位':>9}{'破百率':>9}{'<-20%':>9}"
          f"{'超額中位':>10}{'超額破百':>10}{'月勝率':>8}{'p':>8}")
    print("─" * 105)
    for lab, sel in combos.items():
        if len(sel) < 30:
            print(f"{lab:<30}{len(sel):>8} 樣本不足")
            continue
        f = [r["f12"] for r in sel]
        ex = excess_stats(sel, msta)
        ci = block_bootstrap_ci(ex["series"]) if ex else None
        print(f"{lab:<30}{len(sel):>8,}{statistics.median(f):>8.1f}%"
              f"{sum(1 for x in f if x>100)/len(f)*100:>8.2f}%"
              f"{sum(1 for x in f if x<-20)/len(f)*100:>8.1f}%"
              f"{ex['ex_med']:>9.1f}%{ex['ex_hit100']:>9.2f}%"
              f"{ex['win_rate']:>7.0f}%{(ci['p'] if ci else 9):>8.4f}")

    # ── 4. 集中度：翻倍是不是集中在少數幾個月 ──────────────
    sec("4. 翻倍事件的時間集中度（＝這根本是擇時問題，不是選股問題？）")
    bym = collections.Counter(r["ym"] for r in doublers)
    tot = collections.Counter(r["ym"] for r in obs)
    rates = sorted(((bym[m] / tot[m] * 100, m, bym[m], tot[m])
                    for m in tot if tot[m] >= 30), reverse=True)
    print("翻倍率最高的 12 個建倉月份：")
    print(f"{'月份':<10}{'翻倍率':>9}{'翻倍檔數':>10}{'樣本數':>9}")
    print("─" * 40)
    for rt, m, d, t in rates[:12]:
        print(f"{m:<10}{rt:>8.1f}%{d:>10}{t:>9}")
    top12 = {m for _, m, _, _ in rates[:12]}
    share = sum(1 for r in doublers if r["ym"] in top12) / len(doublers) * 100
    mshare = len(top12) / len(tot) * 100
    print(f"\n最高的 12 個月（占全部月份 {mshare:.1f}%）貢獻了 {share:.1f}% 的翻倍事件")
    zero = sorted((bym[m] / tot[m] * 100, m) for m in tot if tot[m] >= 30)[:8]
    print("\n翻倍率最低的月份：")
    for rt, m in zero:
        print(f"  {m}  {rt:.2f}%")


if __name__ == "__main__":
    main()
