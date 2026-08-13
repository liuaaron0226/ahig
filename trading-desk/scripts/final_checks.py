#!/usr/bin/env python3
"""
最後一輪檢驗：
1. 128 檔下市股裡，有多少是「被併購／改組」（會拿到溢價）vs「真的倒了」
2. 低價效應是不是在衰退？（近年 vs 早年）
3. 剔除最可疑的 <5 元組之後還在嗎？
4. 容量：低價組的低流動性層到底多不能買
5. 「貼近12M高點」「突破36M新高」的同樣檢驗
"""
import json
import sys
import statistics
import collections
import urllib.request

import numpy as np

sys.path.insert(0, "scripts")
from hypo_test import (load, build_observations, month_stats, excess_stats,
                       block_bootstrap_ci, deciles)

np.random.seed(31)
UA = {"User-Agent": "Mozilla/5.0"}


def sec(t):
    print("\n" + "═" * 100)
    print(t)
    print("═" * 100)


def main():
    # ── 1. 下市原因拆解 ─────────────────────────────────────
    sec("1. 128 檔下市股：併購改組（有溢價）vs 疑似失敗（歸零）")
    dl = json.load(open("data/twse_delistings.json", encoding="utf-8"))
    win = [r for r in dl
           if 2009 <= int(r["DelistingDate"].split("/")[0]) + 1911 <= 2026]
    try:
        live = json.load(urllib.request.urlopen(urllib.request.Request(
            "https://openapi.twse.com.tw/v1/opendata/t187ap03_L",
            headers=UA), timeout=60))
        livenames = {r.get("公司簡稱", ""): r.get("公司代號", "") for r in live}
    except Exception as e:
        print("取得現存公司名稱失敗:", e)
        livenames = {}
    print(f"目前上市公司名稱樣本數：{len(livenames)}")

    merged, unclear = [], []
    for r in win:
        nm = r["Company"]
        hit = None
        for ln in livenames:
            if not ln:
                continue
            # 名稱高度重疊 → 極可能是改組／控股公司化／同集團存續
            core = nm.replace("股份有限公司", "").replace("公司", "")
            if len(core) >= 2 and (core in ln or ln[:2] == core[:2] and len(ln) >= 2):
                hit = ln
                break
        (merged if hit else unclear).append((r["DelistingDate"], nm, r["Code"], hit))
    print(f"名稱可對到仍存續公司（極可能併購／控股化，非歸零）：{len(merged)}")
    print(f"對不到（可能真失敗，也可能純換名）：{len(unclear)}")
    print("\n可對到的範例（下市名 → 現存名）：")
    for d, nm, c, h in merged[:15]:
        print(f"  {d} {c} {nm} → {h}")
    print("\n對不到的範例：")
    for d, nm, c, h in unclear[:20]:
        print(f"  {d} {c} {nm}")
    print("\n注意：這只是名稱啟發式，不是權威分類。真正的下市原因要查個案公告。")

    # ── 資料 ────────────────────────────────────────────────
    data = load()
    obs = build_observations(data, use_adj=True)
    msta = month_stats(obs)

    def stat(rows, tag):
        if len(rows) < 30:
            return f"{tag:<30}樣本不足({len(rows)})"
        f = [r["f12"] for r in rows]
        ex = excess_stats(rows, msta)
        ci = block_bootstrap_ci(ex["series"]) if ex else None
        return (f"{tag:<30}{len(rows):>7,}{statistics.median(f):>9.1f}%"
                f"{sum(1 for x in f if x>100)/len(f)*100:>8.2f}%"
                f"{sum(1 for x in f if x<-20)/len(f)*100:>8.1f}%"
                f"{ex['ex_med']:>10.1f}%{ex['ex_hit100']:>9.2f}%"
                f"{ex['win_rate']:>7.0f}%{(ci['p'] if ci else 9):>8.4f}")

    hdr = (f"{'組別':<30}{'N':>7}{'中位':>9}{'破百率':>8}{'<-20%':>8}"
           f"{'超額中位':>10}{'超額破百':>9}{'月勝率':>7}{'p':>8}")

    # ── 2. 衰退檢定 ─────────────────────────────────────────
    sec("2. 低價效應在衰退嗎？（橫斷面最低價 10%，切前後期）")
    cheap = deciles(obs, "price", reverse=False)
    print(hdr)
    print("─" * 96)
    print(stat(cheap, "全期 2009-2025"))
    print(stat([r for r in cheap if r["ym"] < "2014"], "2009-2013"))
    print(stat([r for r in cheap if "2014" <= r["ym"] < "2018"], "2014-2017"))
    print(stat([r for r in cheap if "2018" <= r["ym"] < "2022"], "2018-2021"))
    print(stat([r for r in cheap if r["ym"] >= "2022"], "2022-2025"))
    print()
    # 用月度超額序列做趨勢檢定
    ex = excess_stats(cheap, msta)
    bym = collections.defaultdict(list)
    for r in cheap:
        bym[r["ym"]].append(r["f12"])
    ms = sorted(m for m in bym if m in msta and msta[m]["n"] >= 30)
    series = [statistics.median(bym[m]) - msta[m]["med"] for m in ms]
    x = np.arange(len(series), dtype=float)
    y = np.array(series)
    slope, icpt = np.polyfit(x, y, 1)
    print(f"月度超額中位序列的線性趨勢：每月 {slope:+.4f}% "
          f"（{len(series)} 個月，總計 {slope*len(series):+.1f}%）")
    half = len(series) // 2
    print(f"前半平均超額 = {np.mean(y[:half]):+.1f}%   "
          f"後半平均超額 = {np.mean(y[half:]):+.1f}%")
    # 後半是否仍顯著
    ci2 = block_bootstrap_ci(list(y[half:]))
    print(f"後半段 95%CI [{ci2['lo']:+.1f}%, {ci2['hi']:+.1f}%]  p={ci2['p']:.4f}")

    # ── 3. 剔除 <5 元 ───────────────────────────────────────
    sec("3. 剔除最可疑的 <5 元組（下市前多半在這區間）之後還在嗎？")
    print(hdr)
    print("─" * 96)
    print(stat([r for r in obs if r["price"] < 5], "股價<5元（最可疑）"))
    print(stat([r for r in obs if 5 <= r["price"] < 10], "股價5–10元"))
    print(stat([r for r in obs if 5 <= r["price"] < 15], "股價5–15元"))
    print(stat([r for r in obs if 5 <= r["price"] < 20], "股價5–20元"))
    print(stat([r for r in obs if r["price"] < 10], "股價<10元（含<5，原結果）"))
    print("\n<5 元組的 <-20% 比率若遠低於全市場(16.2%)，幾乎確定是存活者偏誤：")
    print("  真實世界裡從 4 元跌到 1 元、或直接下市的股票，Yahoo 上根本不存在。")

    # ── 4. 容量 ─────────────────────────────────────────────
    sec("4. 容量：低價股裡真正有超額的那一塊，到底能買多少？")
    bym2 = collections.defaultdict(list)
    for r in obs:
        if r["dollar_vol"]:
            bym2[r["ym"]].append(r)
    cells = collections.defaultdict(list)
    for m, rows in bym2.items():
        if len(rows) < 60:
            continue
        rows = sorted(rows, key=lambda r: r["dollar_vol"])
        n = len(rows)
        for li, chunk in enumerate([rows[:n//3], rows[n//3:2*n//3], rows[2*n//3:]]):
            chunk = sorted(chunk, key=lambda r: r["price"])
            k = len(chunk)
            for pi, sub in enumerate([chunk[:k//3], chunk[k//3:2*k//3], chunk[2*k//3:]]):
                cells[(li, pi)].extend(sub)
    print(hdr)
    print("─" * 96)
    for li, ln in enumerate(["成交金額低", "成交金額中", "成交金額高"]):
        print(stat(cells[(li, 0)], f"{ln} × 股價低"))
    print()
    lowcell = cells[(0, 0)]
    dv = sorted(r["dollar_vol"] for r in lowcell if r["dollar_vol"])
    print(f"『成交金額低×股價低』這格的月成交金額分布（新台幣）：")
    for p in (10, 25, 50, 75, 90):
        print(f"   {p:>2} 分位 = {np.percentile(dv, p):>15,.0f}")
    print(f"\n若單月只吃該股月成交金額的 1%（避免衝擊成本），中位個股可投入 "
          f"{np.percentile(dv,50)*0.01:,.0f} 元")
    print(f"該格每月平均檔數 = {len(lowcell)/len({r['ym'] for r in lowcell}):.0f}")

    # ── 5. 另兩個候選 ───────────────────────────────────────
    sec("5. 另兩個通過檢定的假說，做同樣的衰退檢驗")
    for name, sel in [("貼近12M高點>95%",
                       [r for r in obs if r["near12h"] and r["near12h"] > 0.95]),
                      ("突破36M新高",
                       [r for r in obs if r["to_high36"] <= 0.0001]),
                      ("低波動後10%",
                       deciles(obs, "sd12", reverse=False))]:
        print(f"\n── {name} ──")
        print(hdr)
        print("─" * 96)
        print(stat(sel, "全期"))
        print(stat([r for r in sel if r["ym"] < "2014"], "2009-2013"))
        print(stat([r for r in sel if "2014" <= r["ym"] < "2018"], "2014-2017"))
        print(stat([r for r in sel if "2018" <= r["ym"] < "2022"], "2018-2021"))
        print(stat([r for r in sel if r["ym"] >= "2022"], "2022-2025"))


if __name__ == "__main__":
    main()
