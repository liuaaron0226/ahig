#!/usr/bin/env python3
"""
低價效應的破壞性檢驗——這是目前唯一同時贏中位數與破百率的假說，
所以要用力打它。

1. 單調性：股價分組是不是越低越好？
2. 是不是只是「小型股／冷門股」的代理？→ 股價 × 成交金額 雙重排序
3. 有效樣本數：15,219 個觀測點其實只有幾檔股票？→ 以股票為單位叢集重抽
4. 通膨中性版本：改用「當月橫斷面股價最低 10%」
5. 實際組合模擬：每月等權買進，持有 12 個月，扣成本，扣下市假設
"""
import json
import sys
import statistics
import collections

import numpy as np

sys.path.insert(0, "scripts")
from hypo_test import (load, build_observations, month_stats, excess_stats,
                       block_bootstrap_ci, deciles)

np.random.seed(23)


def sec(t):
    print("\n" + "═" * 100)
    print(t)
    print("═" * 100)


def grp(rows, msta, label):
    if len(rows) < 30:
        return None
    f = [r["f12"] for r in rows]
    ex = excess_stats(rows, msta)
    return {
        "label": label, "n": len(f),
        "stocks": len({r["code"] for r in rows}),
        "med": statistics.median(f),
        "hit": sum(1 for x in f if x > 100) / len(f) * 100,
        "bad": sum(1 for x in f if x < -20) / len(f) * 100,
        "ex_med": ex["ex_med"] if ex else float("nan"),
        "ex_hit": ex["ex_hit100"] if ex else float("nan"),
        "win": ex["win_rate"] if ex else float("nan"),
    }


def main():
    data = load()
    obs = build_observations(data, use_adj=True)
    msta = month_stats(obs)
    print(f"樣本 {len(data)} 檔 / {len(obs):,} 觀測點")

    # ── 1. 單調性 ───────────────────────────────────────────
    sec("1. 股價分組單調性：越便宜真的越好嗎？")
    bands = [(0, 5), (5, 10), (10, 15), (15, 20), (20, 30), (30, 50),
             (50, 100), (100, 200), (200, 1e9)]
    print(f"{'股價區間':<16}{'N':>8}{'檔數':>6}{'12M中位':>10}{'>100%':>9}"
          f"{'<-20%':>9}{'超額中位':>11}{'超額破百':>10}{'月勝率':>8}")
    print("─" * 87)
    for lo, hi in bands:
        rows = [r for r in obs if lo <= r["price"] < hi]
        g = grp(rows, msta, "")
        if not g:
            continue
        name = f"{lo}–{hi if hi < 1e8 else '∞'}元"
        print(f"{name:<16}{g['n']:>8,}{g['stocks']:>6}{g['med']:>9.1f}%"
              f"{g['hit']:>8.2f}%{g['bad']:>8.1f}%{g['ex_med']:>10.1f}%"
              f"{g['ex_hit']:>9.2f}%{g['win']:>7.0f}%")

    # ── 2. 雙重排序：股價 × 成交金額 ────────────────────────
    sec("2. 雙重排序：低價效應是不是只是『小型股／冷門股』的代理？")
    # 每月內先按成交金額分三組，再在各組內按股價分三組
    bym = collections.defaultdict(list)
    for r in obs:
        if r["dollar_vol"]:
            bym[r["ym"]].append(r)
    cells = collections.defaultdict(list)
    for m, rows in bym.items():
        if len(rows) < 60:
            continue
        rows.sort(key=lambda r: r["dollar_vol"])
        n = len(rows)
        for li, chunk in enumerate([rows[:n // 3], rows[n // 3:2 * n // 3],
                                    rows[2 * n // 3:]]):
            chunk = sorted(chunk, key=lambda r: r["price"])
            k = len(chunk)
            for pi, sub in enumerate([chunk[:k // 3], chunk[k // 3:2 * k // 3],
                                      chunk[2 * k // 3:]]):
                cells[(li, pi)].extend(sub)
    lnames = ["成交金額低", "成交金額中", "成交金額高"]
    pnames = ["股價低", "股價中", "股價高"]
    print("每格顯示：超額中位報酬 ／ 超額破百率\n")
    print(f"{'':<14}" + "".join(f"{p:>22}" for p in pnames))
    print("─" * 80)
    for li in range(3):
        line = f"{lnames[li]:<14}"
        for pi in range(3):
            g = grp(cells[(li, pi)], msta, "")
            line += f"{g['ex_med']:>+11.1f}% /{g['ex_hit']:>+7.2f}%" if g else f"{'—':>22}"
        print(line)
    print("\n若『股價低』那一欄在三個流動性層都是正的 → 低價效應獨立於流動性。")

    print("\n各格絕對數字：")
    print(f"{'格':<24}{'N':>8}{'檔數':>6}{'中位':>9}{'破百率':>9}{'平均月SD':>10}")
    print("─" * 66)
    for li in range(3):
        for pi in range(3):
            rows = cells[(li, pi)]
            g = grp(rows, msta, "")
            if not g:
                continue
            sd = statistics.mean([r["sd12"] for r in rows if r["sd12"]])
            print(f"{lnames[li] + '×' + pnames[pi]:<24}{g['n']:>8,}{g['stocks']:>6}"
                  f"{g['med']:>8.1f}%{g['hit']:>8.2f}%{sd:>10.3f}")

    # ── 3. 有效樣本數 / 以股票叢集 ──────────────────────────
    sec("3. 有效樣本數：低價組其實只有幾檔股票？以『股票』為單位重抽")
    low10 = [r for r in obs if r["price"] < 10]
    codes = collections.Counter(r["code"] for r in low10)
    print(f"低價(<10)觀測點 {len(low10):,}，來自 {len(codes)} 檔股票")
    top = codes.most_common(10)
    print(f"出現最多次的 10 檔佔 {sum(c for _, c in top) / len(low10) * 100:.1f}%：")
    print("  " + ", ".join(f"{c}({n})" for c, n in top))

    # 以股票為單位 bootstrap：每次重抽股票，算該組中位減同月市場中位
    bycode = collections.defaultdict(list)
    for r in low10:
        bycode[r["code"]].append(r)
    clist = list(bycode)
    per_stock_ex = []
    for c in clist:
        ds = [r["f12"] - msta[r["ym"]]["med"] for r in bycode[c] if r["ym"] in msta]
        if ds:
            per_stock_ex.append(statistics.median(ds))
    arr = np.array(per_stock_ex)
    idx = np.random.randint(0, len(arr), size=(4000, len(arr)))
    means = arr[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    p = 2 * min((means <= 0).mean(), (means >= 0).mean())
    print(f"\n以股票叢集：每檔股票在低價期間的中位超額，平均 = {arr.mean():+.1f}%")
    print(f"  95% 信賴區間 [{lo:+.1f}%, {hi:+.1f}%]   p = {min(1.0, p):.4f}")
    print(f"  有 {(arr > 0).mean() * 100:.0f}% 的股票在低價期間跑贏同月市場中位")

    # ── 4. 通膨中性：橫斷面股價最低 10% ────────────────────
    sec("4. 通膨中性版本：改用『當月橫斷面股價最低 10%』（不用固定 10 元門檻）")
    cheap_rank = deciles(obs, "price", reverse=False)
    g = grp(cheap_rank, msta, "")
    print(f"N={g['n']:,}（{g['stocks']} 檔）  12M中位={g['med']:+.1f}%  "
          f"破百率={g['hit']:.2f}%  <-20%={g['bad']:.1f}%")
    print(f"超額中位={g['ex_med']:+.1f}%  超額破百={g['ex_hit']:+.2f}%  月勝率={g['win']:.0f}%")
    ex = excess_stats(cheap_rank, msta)
    ci = block_bootstrap_ci(ex["series"])
    print(f"月叢集 bootstrap：95%CI [{ci['lo']:+.1f}%, {ci['hi']:+.1f}%]  p={ci['p']:.4f}")
    print("\n逐年：")
    byy = collections.defaultdict(list)
    for r in cheap_rank:
        byy[r["ym"][:4]].append(r)
    print(f"{'年':<8}{'N':>7}{'中位':>9}{'超額中位':>11}{'破百率':>9}{'超額破百':>10}")
    print("─" * 55)
    for y in sorted(byy):
        sub = byy[y]
        gg = grp(sub, msta, "")
        if gg:
            print(f"{y:<8}{gg['n']:>7}{gg['med']:>8.1f}%{gg['ex_med']:>10.1f}%"
                  f"{gg['hit']:>8.2f}%{gg['ex_hit']:>9.2f}%")

    # ── 5. 組合模擬 ─────────────────────────────────────────
    sec("5. 實際組合模擬：每月等權買進 <10 元的股票，持有 12 個月")
    # 疊加式：每月開一個等權籃子，12 個月後結算，看年化
    baskets = collections.defaultdict(list)
    for r in obs:
        if r["price"] < 10:
            baskets[r["ym"]].append(r["f12"])
    mkt = collections.defaultdict(list)
    for r in obs:
        mkt[r["ym"]].append(r["f12"])

    months = sorted(baskets)
    strat = [statistics.mean(baskets[m]) for m in months if len(baskets[m]) >= 5]
    bench = [statistics.mean(mkt[m]) for m in months if len(baskets[m]) >= 5]
    print(f"可建倉月份 {len(strat)} 個（每月至少 5 檔）")
    print(f"每月籃子平均檔數 = {statistics.mean([len(baskets[m]) for m in months if len(baskets[m])>=5]):.0f}")
    print(f"\n{'情境':<40}{'策略平均12M':>14}{'市場等權12M':>14}{'差':>9}")
    print("─" * 78)
    print(f"{'原始（無成本、無下市）':<40}{statistics.mean(strat):>13.1f}%"
          f"{statistics.mean(bench):>13.1f}%{statistics.mean(strat)-statistics.mean(bench):>+8.1f}%")

    # 加成本：低價股買賣價差大，假設來回 2%
    for cost in (1.0, 2.0, 4.0):
        s = [x - cost for x in strat]
        print(f"{'扣交易成本 ' + str(cost) + '%（來回）':<40}{statistics.mean(s):>13.1f}%"
              f"{statistics.mean(bench):>13.1f}%{statistics.mean(s)-statistics.mean(bench):>+8.1f}%")

    # 加下市：每年 x% 的低價股歸零
    for drate in (1.0, 3.0, 5.0, 10.0):
        s = [x * (1 - drate / 100) + (-100.0) * (drate / 100) - 2.0 for x in strat]
        print(f"{'扣成本2% + 每年' + str(drate) + '%的持股歸零':<40}"
              f"{statistics.mean(s):>13.1f}%{statistics.mean(bench):>13.1f}%"
              f"{statistics.mean(s)-statistics.mean(bench):>+8.1f}%")

    print(f"\n實際下市率參考：128 檔 / 約 1130 檔 / 17 年 ≈ 每年 {128/1130/17*100:.2f}% 全市場，")
    print("低價股的下市率會高於全市場平均，但要到每年 10% 才會吃掉全部超額。")

    # 最差年份
    print(f"\n{'建倉年':<10}{'策略平均':>11}{'市場平均':>11}{'差':>9}")
    print("─" * 41)
    byy2 = collections.defaultdict(lambda: ([], []))
    for m in months:
        if len(baskets[m]) >= 5:
            byy2[m[:4]][0].append(statistics.mean(baskets[m]))
            byy2[m[:4]][1].append(statistics.mean(mkt[m]))
    for y in sorted(byy2):
        a, b = byy2[y]
        print(f"{y:<10}{statistics.mean(a):>10.1f}%{statistics.mean(b):>10.1f}%"
              f"{statistics.mean(a)-statistics.mean(b):>+8.1f}%")


if __name__ == "__main__":
    main()
