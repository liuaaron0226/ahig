#!/usr/bin/env python3
"""
對前一輪「贏過基準」的假說做破壞性檢驗：

1. 存活者偏誤上界：128 檔下市股全部當成歸零，低價效應還在嗎？
2. 「破百率」是不是只是波動度的代理變數？
3. 子期間穩定性（切三段）
4. 流動性：低價股買得到嗎？
5. 還原股價 vs 未還原股價
6. 多重檢定校正
"""
import json
import sys
import math
import statistics
import collections

import numpy as np

sys.path.insert(0, "scripts")
from hypo_test import (load, build_observations, summarize, month_stats,
                       excess_stats, block_bootstrap_ci, deciles)

np.random.seed(11)


def sec(t):
    print("\n" + "═" * 100)
    print(t)
    print("═" * 100)


def main():
    data = load()
    obs = build_observations(data, use_adj=True)
    msta = month_stats(obs)
    print(f"樣本：{len(data)} 檔 / {len(obs):,} 觀測點")

    low10 = [r for r in obs if r["price"] < 10]
    low20 = [r for r in obs if r["price"] < 20]

    # ── 1. 存活者偏誤上界 ───────────────────────────────────
    sec("1. 存活者偏誤上界檢定：把 128 檔下市股當成「全部歸零」灌進低價組")
    dl = json.load(open("data/twse_delistings.json", encoding="utf-8"))
    n_del = sum(1 for r in dl if 2009 <= int(r["DelistingDate"].split("/")[0]) + 1911 <= 2026)
    print(f"2009-2026 實際下市家數：{n_del}（我的樣本含 0 檔）")
    print(f"低價組(<10元)現有觀測點：{len(low10):,}")
    print()
    print("假設每檔下市股在歸零前，於低價組留下 K 個月觀測，報酬 R：")
    print(f"{'K(月)':>6}{'注入筆數':>10}{'占比':>8}{'新中位':>10}{'新破百率':>10}"
          f"{'新超額中位':>12}{'原超額中位':>12}")
    print("─" * 70)
    f12_low = sorted(r["f12"] for r in low10)
    base_med = statistics.median(f12_low)
    base_hit = sum(1 for x in f12_low if x > 100) / len(f12_low) * 100
    ex0 = excess_stats(low10, msta)
    for K in (6, 12, 24, 36, 60):
        for R in (-100.0,):
            inj = [R] * (n_del * K)
            merged = sorted(f12_low + inj)
            nm = statistics.median(merged)
            nh = sum(1 for x in merged if x > 100) / len(merged) * 100
            share = len(inj) / len(merged) * 100
            # 超額：粗略把中位差平移
            print(f"{K:>6}{len(inj):>10,}{share:>7.1f}%{nm:>9.1f}%{nh:>9.2f}%"
                  f"{nm - statistics.median([r['f12'] for r in obs]):>11.1f}%"
                  f"{ex0['ex_med']:>11.1f}%")
    print()
    print(f"（對照）全市場中位 = {statistics.median([r['f12'] for r in obs]):+.1f}%，"
          f"破百率 = {sum(1 for r in obs if r['f12'] > 100) / len(obs) * 100:.2f}%")
    print("判讀：K 要大到什麼程度，低價組的中位才會掉到全市場之下？")

    # ── 2. 破百率 = 波動度代理？ ─────────────────────────────
    sec("2. 「破百率」是不是只是波動度的代理變數？")
    # 按波動度分十組，看每組的破百率與中位報酬
    withsd = [r for r in obs if r["sd12"] is not None]
    withsd.sort(key=lambda r: r["sd12"])
    k = len(withsd) // 10
    print(f"{'波動十分位':<12}{'月報酬SD':>10}{'12M中位':>10}{'12M平均':>10}"
          f"{'>100%':>9}{'<-20%':>9}")
    print("─" * 62)
    for d in range(10):
        g = withsd[d * k:(d + 1) * k] if d < 9 else withsd[9 * k:]
        f = [r["f12"] for r in g]
        print(f"D{d + 1:<11}{statistics.mean([r['sd12'] for r in g]):>9.3f}"
              f"{statistics.median(f):>9.1f}%{statistics.mean(f):>9.1f}%"
              f"{sum(1 for x in f if x > 100) / len(f) * 100:>8.2f}%"
              f"{sum(1 for x in f if x < -20) / len(f) * 100:>8.1f}%")

    # 各假說的平均波動度 vs 其超額破百率
    sec("2b. 各假說：選中股票的平均波動度 vs 超額破百率（若高度相關＝破百率只是波動度）")
    from hypo_test import build_hypotheses
    H = build_hypotheses(obs)
    pts = []
    print(f"{'假說':<26}{'平均月SD':>10}{'超額破百率':>12}{'超額中位':>11}")
    print("─" * 60)
    for name, desc, sel in H:
        if len(sel) < 50:
            continue
        sds = [r["sd12"] for r in sel if r["sd12"] is not None]
        if not sds:
            continue
        ex = excess_stats(sel, msta)
        if not ex:
            continue
        msd = statistics.mean(sds)
        pts.append((msd, ex["ex_hit100"], ex["ex_med"], name))
        print(f"{name:<26}{msd:>9.3f}{ex['ex_hit100']:>11.2f}%{ex['ex_med']:>10.1f}%")
    if len(pts) > 3:
        x = np.array([p[0] for p in pts])
        yh = np.array([p[1] for p in pts])
        ym = np.array([p[2] for p in pts])
        print(f"\n相關係數  波動度 vs 超額破百率 = {np.corrcoef(x, yh)[0,1]:+.3f}")
        print(f"相關係數  波動度 vs 超額中位報酬 = {np.corrcoef(x, ym)[0,1]:+.3f}")
        print("若第一個接近 +1：提高破百率＝單純買波動，不是選股能力。")

    # ── 3. 子期間穩定性 ─────────────────────────────────────
    sec("3. 子期間穩定性（訊號年份切段）")
    tests = {
        "低價<10元": low10,
        "低價<20元": low20,
        "貼近12M高點": [r for r in obs if r["near12h"] and r["near12h"] > 0.95],
        "突破36M新高": [r for r in obs if r["to_high36"] <= 0.0001],
        "成交金額最低10%": deciles(obs, "dollar_vol", reverse=False),
        "低價<20+動能6M>50%": [r for r in obs if r["price"] < 20 and r["r6"] and r["r6"] > 0.5],
        "原始假說B": [r for r in obs if r["off_low36"] >= 1.0 and r["to_high36"] >= 1.0],
    }
    periods = [("2009-2013", "2009", "2013"), ("2014-2019", "2014", "2019"),
               ("2020-2025", "2020", "2025")]
    print(f"{'假說':<22}" + "".join(f"{p[0]:>28}" for p in periods))
    print(f"{'':<22}" + "".join(f"{'超額中位/超額破百/N':>28}" for p in periods))
    print("─" * 106)
    for label, sel in tests.items():
        line = f"{label:<22}"
        for pname, y0, y1 in periods:
            sub = [r for r in sel if y0 <= r["ym"][:4] <= y1]
            if len(sub) < 30:
                line += f"{'樣本不足':>28}"
                continue
            ex = excess_stats(sub, msta)
            if not ex:
                line += f"{'—':>28}"
                continue
            line += f"{ex['ex_med']:>+11.1f}%{ex['ex_hit100']:>+9.2f}%{len(sub):>7}"
        print(line)

    # ── 4. 流動性 ───────────────────────────────────────────
    sec("4. 流動性：低價股 / 冷門股實際上買得到嗎？（月成交金額，新台幣）")
    groups = {
        "全市場": obs,
        "股價<10元": low10,
        "股價<20元": low20,
        "成交金額最低10%": deciles(obs, "dollar_vol", reverse=False),
        "低價<20+動能6M>50%": [r for r in obs if r["price"] < 20 and r["r6"] and r["r6"] > 0.5],
    }
    print(f"{'組別':<22}{'月成交金額中位':>18}{'25分位':>16}{'<1000萬比率':>14}")
    print("─" * 72)
    for g, rows in groups.items():
        dv = [r["dollar_vol"] for r in rows if r["dollar_vol"]]
        if not dv:
            continue
        med = np.percentile(dv, 50)
        q25 = np.percentile(dv, 25)
        thin = sum(1 for x in dv if x < 1e7) / len(dv) * 100
        print(f"{g:<22}{med:>17,.0f}{q25:>15,.0f}{thin:>13.1f}%")

    # ── 5. 還原 vs 未還原 ───────────────────────────────────
    sec("5. 含息（還原）vs 不含息（未還原）：原始回測用未還原收盤，差多少？")
    obs_raw = build_observations(data, use_adj=False)
    msta_raw = month_stats(obs_raw)
    print(f"{'組別':<24}{'含息中位':>11}{'不含息中位':>12}{'差異':>9}"
          f"{'含息破百':>10}{'不含息破百':>11}")
    print("─" * 78)
    pairs = {
        "全市場": (obs, obs_raw),
        "股價<10元": ([r for r in obs if r["price"] < 10],
                    [r for r in obs_raw if r["price"] < 10]),
        "原始假說B": ([r for r in obs if r["off_low36"] >= 1.0 and r["to_high36"] >= 1.0],
                   [r for r in obs_raw if r["off_low36"] >= 1.0 and r["to_high36"] >= 1.0]),
    }
    for g, (a, b) in pairs.items():
        ma, mb = statistics.median([r["f12"] for r in a]), statistics.median([r["f12"] for r in b])
        ha = sum(1 for r in a if r["f12"] > 100) / len(a) * 100
        hb = sum(1 for r in b if r["f12"] > 100) / len(b) * 100
        print(f"{g:<24}{ma:>10.1f}%{mb:>11.1f}%{ma - mb:>+8.1f}%{ha:>9.2f}%{hb:>10.2f}%")

    # ── 6. 多重檢定 ─────────────────────────────────────────
    sec("6. 多重檢定校正（測了 28 個假說）")
    res = json.load(open("data/hypo_results.json", encoding="utf-8"))
    ps = sorted([(r["ci"]["p"], r["name"], r["excess"]["ex_med"]) for r in res if r["ci"]])
    m = len(ps)
    print(f"檢定數 m={m}；Bonferroni 門檻 = {0.05/m:.5f}")
    print(f"{'假說':<26}{'p值':>9}{'超額中位':>11}{'Bonferroni':>12}{'BH-FDR':>10}")
    print("─" * 70)
    for rank, (p, name, exm) in enumerate(ps, 1):
        bh = 0.05 * rank / m
        print(f"{name:<26}{p:>9.4f}{exm:>10.1f}%"
              f"{'通過' if p < 0.05/m else '不通過':>12}"
              f"{'通過' if p <= bh else '不通過':>10}")


if __name__ == "__main__":
    main()
