#!/usr/bin/env python3
"""
多假說篩選檢定引擎。

跟原本 screen_test.py 的兩個關鍵差異：

1) 【同期基準】原本拿「全期間所有 (股票,月份) 的平均」當基準。
   但像「距高點>100%」這種條件只會在空頭時觸發，拿它去比一個含多頭的
   平均值，比較的是「時機」不是「選股」。
   這裡改成：每個訊號都跟「同一個月、全市場所有股票」的未來 12 個月報酬比，
   算超額（excess）。這才分得出選股能力。

2) 【月份叢集推論】同一個月的訊號高度相關（大盤一起漲跌），
   把它們當成獨立樣本會嚴重高估顯著性。
   這裡用「以月為單位的 block bootstrap」算信賴區間。

用法：python scripts/hypo_test.py [cache.json]
"""
import json
import sys
import math
import random
import statistics
import collections

import numpy as np

CACHE = sys.argv[1] if len(sys.argv) > 1 else "data/monthly_cache.json"
HORIZON = 12          # 未來報酬觀察期（月）
MIN_HIST = 36         # 篩選需要的最短歷史
random.seed(7)
np.random.seed(7)


# ───────────────────────── 資料載入與特徵計算 ─────────────────────────

def load():
    with open(CACHE, encoding="utf-8") as f:
        raw = json.load(f)
    out = {}
    for code, rows in raw.items():
        rows = [r for r in rows if r["c"] and r["c"] > 0 and r["a"] and r["a"] > 0]
        if len(rows) < MIN_HIST + HORIZON + 1:
            continue
        out[code] = rows
    return out


def build_observations(data, use_adj=True):
    """
    產生所有 (股票, 月份) 觀測點，每點含篩選特徵 + 未來報酬。
    只用「當下已知」資料算特徵，避免前視偏誤。
    """
    obs = []
    for code, rows in data.items():
        n = len(rows)
        px_r = [r["c"] for r in rows]                     # 未還原收盤（篩選用，貼近看盤價）
        px_a = [r["a"] for r in rows]                     # 還原收盤（算報酬用，含息）
        hi = [r["h"] if r["h"] else r["c"] for r in rows]
        lo = [r["l"] if r["l"] else r["c"] for r in rows]
        vol = [r["v"] if r["v"] else 0 for r in rows]
        fwd_src = px_a if use_adj else px_r

        for i in range(MIN_HIST, n - HORIZON):
            p = px_r[i]
            pa = px_a[i]
            if p <= 0 or pa <= 0:
                continue

            w36 = px_r[i - 36:i + 1]
            lo36, hi36 = min(w36), max(w36)
            if lo36 <= 0:
                continue

            w12a = px_a[i - 12:i + 1]
            rets12 = [w12a[k + 1] / w12a[k] - 1 for k in range(len(w12a) - 1)
                      if w12a[k] > 0]
            sd = statistics.pstdev(rets12) if len(rets12) > 3 else None

            h12 = max(hi[i - 12:i + 1])
            l12 = min(lo[i - 12:i + 1])
            v_recent = vol[i]
            v_base = statistics.mean(vol[i - 12:i]) if i >= 12 else 0

            # 至今為止的歷史最高（只看過去，不看未來）
            hi_all = max(px_r[:i + 1])

            f = {
                "code": code,
                "i": i,
                "ym": rows[i]["d"],
                "price": p,
                # 動能
                "r1": px_a[i] / px_a[i - 1] - 1 if px_a[i - 1] > 0 else None,
                "r3": px_a[i] / px_a[i - 3] - 1 if px_a[i - 3] > 0 else None,
                "r6": px_a[i] / px_a[i - 6] - 1 if px_a[i - 6] > 0 else None,
                "r12": px_a[i] / px_a[i - 12] - 1 if px_a[i - 12] > 0 else None,
                "r36": px_a[i] / px_a[i - 36] - 1 if px_a[i - 36] > 0 else None,
                # 動能（跳過最近 1 個月，Jegadeesh-Titman 標準做法，避開短期反轉）
                "r12_1": px_a[i - 1] / px_a[i - 12] - 1 if px_a[i - 12] > 0 else None,
                # 位置
                "off_low36": p / lo36 - 1,
                "to_high36": hi36 / p - 1,
                "dd_all": 1 - p / hi_all if hi_all > 0 else 0,
                "near12h": p / h12 if h12 > 0 else None,
                # 波動
                "sd12": sd,
                "range12": h12 / l12 if l12 > 0 else None,
                # 量能
                "vratio": (v_recent / v_base) if v_base > 0 else None,
                "dollar_vol": v_recent * p,
                # 未來報酬（%）
                "f12": (fwd_src[i + HORIZON] / fwd_src[i] - 1) * 100
                if fwd_src[i] > 0 else None,
                "f6": (fwd_src[i + 6] / fwd_src[i] - 1) * 100
                if fwd_src[i] > 0 else None,
            }
            if f["f12"] is None:
                continue
            obs.append(f)
    return obs


# ───────────────────────── 統計工具 ─────────────────────────

def pct(xs, p):
    return float(np.percentile(xs, p)) if len(xs) else float("nan")


def summarize(rows):
    f12 = [r["f12"] for r in rows]
    f6 = [r["f6"] for r in rows if r["f6"] is not None]
    return {
        "n": len(f12),
        "med12": statistics.median(f12) if f12 else float("nan"),
        "avg12": statistics.mean(f12) if f12 else float("nan"),
        "med6": statistics.median(f6) if f6 else float("nan"),
        "hit100": sum(1 for x in f12 if x > 100) / len(f12) * 100 if f12 else 0,
        "hit50": sum(1 for x in f12 if x > 50) / len(f12) * 100 if f12 else 0,
        "bad20": sum(1 for x in f12 if x < -20) / len(f12) * 100 if f12 else 0,
        "months": len({r["ym"] for r in rows}),
    }


def month_stats(obs):
    """每個月的全市場（同期基準）統計。"""
    by = collections.defaultdict(list)
    for r in obs:
        by[r["ym"]].append(r["f12"])
    return {m: {"med": statistics.median(v),
                "hit100": sum(1 for x in v if x > 100) / len(v) * 100,
                "bad20": sum(1 for x in v if x < -20) / len(v) * 100,
                "n": len(v)}
            for m, v in by.items()}


def excess_stats(rows, msta):
    """相對同月全市場的超額表現。"""
    d_med, d_hit, d_bad = [], [], []
    by = collections.defaultdict(list)
    for r in rows:
        by[r["ym"]].append(r["f12"])
    for m, v in by.items():
        b = msta.get(m)
        if not b or b["n"] < 30:
            continue
        d_med.append(statistics.median(v) - b["med"])
        d_hit.append(sum(1 for x in v if x > 100) / len(v) * 100 - b["hit100"])
        d_bad.append(sum(1 for x in v if x < -20) / len(v) * 100 - b["bad20"])
    if not d_med:
        return None
    return {
        "months": len(d_med),
        "ex_med": statistics.mean(d_med),
        "ex_med_median": statistics.median(d_med),
        "win_rate": sum(1 for x in d_med if x > 0) / len(d_med) * 100,
        "ex_hit100": statistics.mean(d_hit),
        "ex_bad20": statistics.mean(d_bad),
        "series": d_med,
    }


def block_bootstrap_ci(series, iters=4000):
    """以月為單位重抽，算平均超額的 95% 信賴區間與 p 值（雙尾，H0: 平均=0）。"""
    if len(series) < 5:
        return None
    a = np.array(series, dtype=float)
    n = len(a)
    idx = np.random.randint(0, n, size=(iters, n))
    means = a[idx].mean(axis=1)
    lo, hi = np.percentile(means, [2.5, 97.5])
    p = 2 * min((means <= 0).mean(), (means >= 0).mean())
    return {"lo": float(lo), "hi": float(hi), "p": float(min(1.0, p)),
            "mean": float(a.mean())}


# ───────────────────────── 假說定義 ─────────────────────────

def deciles(obs, key, reverse=False):
    """每個月份內做橫斷面排名，回傳 top decile 的門檻判斷函式所需資料。"""
    by = collections.defaultdict(list)
    for r in obs:
        if r.get(key) is not None:
            by[r["ym"]].append(r)
    picked = []
    for m, rows in by.items():
        if len(rows) < 30:
            continue
        rows.sort(key=lambda r: r[key], reverse=reverse)
        k = max(1, len(rows) // 10)
        picked.extend(rows[:k])
    return picked


def build_hypotheses(obs):
    """回傳 [(名稱, 說明, 選中的觀測點 list)]"""
    H = []

    def add(name, desc, sel):
        H.append((name, desc, sel))

    # ── 對照組：重現原始假說（驗證引擎一致性）
    add("REF-B 原始假說B",
        "距36M低點已翻倍 且 距36M高點還有>100%空間",
        [r for r in obs if r["off_low36"] >= 1.0 and r["to_high36"] >= 1.0])

    # ── H1 純動能（Jegadeesh-Titman）
    add("H1a 動能12M前10%",
        "月內橫斷面：過去12個月報酬前10%",
        deciles(obs, "r12", reverse=True))
    add("H1b 動能12-1前10%",
        "月內橫斷面：過去12個月(跳過最近1月)報酬前10%",
        deciles(obs, "r12_1", reverse=True))
    add("H1c 動能6M前10%",
        "月內橫斷面：過去6個月報酬前10%",
        deciles(obs, "r6", reverse=True))
    add("H1d 反動能12M後10%",
        "月內橫斷面：過去12個月報酬最後10%（輸家）",
        deciles(obs, "r12", reverse=False))

    # ── H2 低價股效應
    add("H2a 股價<20元",
        "絕對股價低於20元",
        [r for r in obs if r["price"] < 20])
    add("H2b 股價<15元",
        "絕對股價低於15元",
        [r for r in obs if r["price"] < 15])
    add("H2c 股價<10元",
        "絕對股價低於10元（雞蛋水餃股）",
        [r for r in obs if r["price"] < 10])
    add("H2d 股價>200元",
        "絕對股價高於200元（高價股，對照）",
        [r for r in obs if r["price"] > 200])

    # ── H3 波動度
    add("H3a 波動前10%",
        "月內橫斷面：過去12個月月報酬標準差前10%",
        deciles(obs, "sd12", reverse=True))
    add("H3b 振幅前10%",
        "月內橫斷面：過去12個月 最高/最低 比值前10%",
        deciles(obs, "range12", reverse=True))
    add("H3c 波動後10%",
        "月內橫斷面：波動最低10%（低波動異象，對照）",
        deciles(obs, "sd12", reverse=False))

    # ── H4 成交量激增
    add("H4a 量增>3倍",
        "當月成交量 > 過去12個月均量的3倍",
        [r for r in obs if r["vratio"] and r["vratio"] > 3])
    add("H4b 量增>5倍",
        "當月成交量 > 過去12個月均量的5倍",
        [r for r in obs if r["vratio"] and r["vratio"] > 5])
    add("H4c 量縮<0.5倍",
        "當月成交量 < 過去12個月均量的0.5倍（量縮，對照）",
        [r for r in obs if r["vratio"] and r["vratio"] < 0.5])

    # ── H5 深度回撤後復甦
    add("H5a 距歷史高點>70%",
        "距上市以來最高價跌超過70%",
        [r for r in obs if r["dd_all"] > 0.70])
    add("H5b 距歷史高點>85%",
        "距上市以來最高價跌超過85%",
        [r for r in obs if r["dd_all"] > 0.85])
    add("H5c 深跌>70%+已從低點反彈>30%",
        "深跌但已開始回升（落難股翻身）",
        [r for r in obs if r["dd_all"] > 0.70 and r["off_low36"] > 0.30])

    # ── H6 創新高（George & Hwang 52週高點）
    add("H6a 貼近12M高點(>95%)",
        "股價在過去12個月高點的95%以上",
        [r for r in obs if r["near12h"] and r["near12h"] > 0.95])
    add("H6b 突破36M新高",
        "當月收盤即為過去36個月最高",
        [r for r in obs if r["to_high36"] <= 0.0001])

    # ── H7 組合：低價 × 動能
    add("H7a 低價<20 且 動能6M>50%",
        "便宜又已經在動",
        [r for r in obs if r["price"] < 20 and r["r6"] and r["r6"] > 0.5])
    add("H7b 低價<20 且 量增>3倍",
        "便宜 + 爆量",
        [r for r in obs if r["price"] < 20 and r["vratio"] and r["vratio"] > 3])
    add("H7c 低價<20 且 波動高 且 量增>2倍",
        "便宜 + 高波動 + 放量",
        [r for r in obs if r["price"] < 20 and r["vratio"] and r["vratio"] > 2
         and r["sd12"] and r["sd12"] > 0.12])

    # ── H8 群創原型：深跌 + 低價 + 剛翻倍
    add("H8a 群創原型",
        "股價<30 且 距歷史高點>70% 且 距36M低點已漲>50%",
        [r for r in obs if r["price"] < 30 and r["dd_all"] > 0.70
         and r["off_low36"] > 0.50])

    # ── H9 成交金額（流動性）
    add("H9a 成交金額最低10%",
        "月內橫斷面：成交金額最低10%（冷門股）",
        deciles(obs, "dollar_vol", reverse=False))
    add("H9b 成交金額最高10%",
        "月內橫斷面：成交金額最高10%（熱門股）",
        deciles(obs, "dollar_vol", reverse=True))

    # ── H10 長期反轉（DeBondt-Thaler）
    add("H10a 3年輸家",
        "月內橫斷面：過去36個月報酬最後10%",
        deciles(obs, "r36", reverse=False))
    add("H10b 3年贏家",
        "月內橫斷面：過去36個月報酬前10%",
        deciles(obs, "r36", reverse=True))

    return H


# ───────────────────────── 主流程 ─────────────────────────

def main():
    data = load()
    print(f"載入 {len(data)} 檔，月線資料")
    obs = build_observations(data, use_adj=True)
    print(f"觀測點（股票×月份）：{len(obs):,}")
    ym = sorted({r['ym'] for r in obs})
    print(f"訊號月份範圍：{ym[0]} ~ {ym[-1]}（{len(ym)} 個月）\n")

    msta = month_stats(obs)
    base = summarize(obs)

    print("═" * 108)
    print("【基準】全樣本（所有股票所有月份）")
    print(f"  N={base['n']:,}  12M中位={base['med12']:+.1f}%  "
          f"12M平均={base['avg12']:+.1f}%  >100%={base['hit100']:.2f}%  "
          f"<-20%={base['bad20']:.1f}%")
    print("═" * 108)

    H = build_hypotheses(obs)
    results = []

    hdr = (f"{'假說':<26}{'訊號數':>7}{'月數':>5}{'12M中位':>9}{'12M平均':>9}"
           f"{'>100%':>8}{'<-20%':>8}{'超額中位':>10}{'超額>100%':>10}"
           f"{'月勝率':>8}{'p值':>8}")
    print("\n" + hdr)
    print("─" * 108)

    for name, desc, sel in H:
        if len(sel) < 50:
            print(f"{name:<26}{len(sel):>7}  訊號太少，略過")
            continue
        s = summarize(sel)
        ex = excess_stats(sel, msta)
        ci = block_bootstrap_ci(ex["series"]) if ex else None
        results.append((name, desc, s, ex, ci))
        pv = f"{ci['p']:.3f}" if ci else "—"
        star = ""
        if ci and ci["p"] < 0.05:
            star = "*" if ex["ex_med"] > 0 else "!"
        print(f"{name:<26}{s['n']:>7}{s['months']:>5}{s['med12']:>8.1f}%"
              f"{s['avg12']:>8.1f}%{s['hit100']:>7.2f}%{s['bad20']:>7.1f}%"
              f"{ex['ex_med']:>9.1f}%{ex['ex_hit100']:>9.2f}%"
              f"{ex['win_rate']:>7.0f}%{pv:>8}{star}")

    print("─" * 108)
    print("超額中位 = 訊號股當月中位報酬 − 同月全市場中位報酬（平均over月份）")
    print("超額>100% = 訊號股破百率 − 同月全市場破百率")
    print("月勝率 = 有多少比例的月份，訊號組打敗同月全市場")
    print("p值 = 以『月』為單位 block bootstrap，H0：平均超額=0。* 顯著為正，! 顯著為負")

    # 排序輸出：誰真的贏
    print("\n" + "═" * 108)
    print("【按 超額破百率 排序】——找『下一檔群創』最該看這欄")
    print("═" * 108)
    ranked = sorted(results, key=lambda x: -x[3]["ex_hit100"])
    print(f"{'假說':<26}{'超額破百率':>12}{'絕對破百率':>12}{'基準破百率':>12}{'p值':>9}")
    print("─" * 75)
    for name, desc, s, ex, ci in ranked:
        pv = f"{ci['p']:.3f}" if ci else "—"
        print(f"{name:<26}{ex['ex_hit100']:>11.2f}%{s['hit100']:>11.2f}%"
              f"{s['hit100'] - ex['ex_hit100']:>11.2f}%{pv:>9}")

    print("\n" + "═" * 108)
    print("【按 超額中位報酬 排序】")
    print("═" * 108)
    ranked2 = sorted(results, key=lambda x: -x[3]["ex_med"])
    print(f"{'假說':<26}{'超額中位':>11}{'95%信賴區間':>24}{'p值':>9}{'月勝率':>8}")
    print("─" * 80)
    for name, desc, s, ex, ci in ranked2:
        cis = f"[{ci['lo']:+.1f}%, {ci['hi']:+.1f}%]" if ci else "—"
        pv = f"{ci['p']:.3f}" if ci else "—"
        print(f"{name:<26}{ex['ex_med']:>10.1f}%{cis:>24}{pv:>9}"
              f"{ex['win_rate']:>7.0f}%")

    with open("data/hypo_results.json", "w", encoding="utf-8") as f:
        json.dump([{"name": n, "desc": d, "summary": s,
                    "excess": {k: v for k, v in e.items() if k != "series"},
                    "ci": c}
                   for n, d, s, e, c in results], f, ensure_ascii=False, indent=1)
    print("\n結果寫入 data/hypo_results.json")


if __name__ == "__main__":
    main()
