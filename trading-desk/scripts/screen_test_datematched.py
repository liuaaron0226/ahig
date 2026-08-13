#!/usr/bin/env python3
"""
對 screen_test.py 的方法學複驗：日期配對基準（date-matched baseline）。

原始 screen_test.py 的基準是「全樣本所有月份的 forward 12M 報酬」，
但篩選訊號在時間上是高度叢聚的（空頭年份訊號特別多）。
拿叢聚在特定月份的訊號去比「全期間平均」，等於把
「選股效果」和「進場時機（市場 beta）」混在一起。

學術文獻（Bali/Cakici/Whitelaw 2011 的月度橫斷面排序、
Fama-MacBeth）都是逐月做橫斷面比較，正是為了消掉這個。

本腳本對每一個訊號 (股票 c, 月份 t)，用「同一個月份 t 全體樣本股的
forward 12M 報酬」當對照，計算超額報酬，再彙總。
"""
import json
import sys
import urllib.request
import datetime
import statistics
import random
import collections
import math
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0"}


def universe(n):
    lst = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL", headers=UA), timeout=30))
    codes = [r["Code"] for r in lst if r["Code"].isdigit() and len(r["Code"]) == 4]
    random.seed(42)
    return random.sample(codes, min(n, len(codes)))


def get(code):
    try:
        u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW"
             f"?interval=1mo&range=10y")
        r = json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers=UA), timeout=25))["chart"]["result"][0]
        q = r["indicators"]["quote"][0]
        s = []
        for t, c in zip(r["timestamp"], q["close"]):
            if c is None:
                continue
            s.append((datetime.datetime.utcfromtimestamp(t), c))
        return code, s
    except Exception:
        return code, None


def ym(d):
    return (d.year, d.month)


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    codes = universe(n)
    print(f"抽樣 {len(codes)} 檔，抓取月線資料…", flush=True)
    data = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        for code, s in ex.map(get, codes):
            if s and len(s) >= 60:
                data[code] = s
    print(f"取得 {len(data)} 檔（至少 60 個月）\n", flush=True)

    CONFIGS = [
        ("A 已翻倍+距高點>50%", 1.00, 0.50),
        ("B 已翻倍+距高點>100%", 1.00, 1.00),
        ("C 漲50%+距高點>50%", 0.50, 0.50),
        ("D 漲200%+距高點>50%", 2.00, 0.50),
        ("E 漲30%+距高點>30%", 0.30, 0.30),
    ]
    LOOKBACK = 36

    # 每個月份的全樣本 forward 12M 報酬池（date-matched baseline）
    pool = collections.defaultdict(list)
    for code, s in data.items():
        for i in range(LOOKBACK, len(s) - 12):
            pool[ym(s[i][0])].append((s[i + 12][1] / s[i][1] - 1) * 100)

    print("每月樣本股數中位數：", statistics.median(len(v) for v in pool.values()))
    print("涵蓋月份數：", len(pool), "\n")

    print(f"{'篩選條件':<22}{'訊號':>6}{'12M中位':>9}{'同月基準':>9}{'中位差':>8}"
          f"{'>100%':>8}{'同月>100%':>10}{'p(月叢集)':>11}")
    print("-" * 86)

    for label, min_off_low, min_to_high in CONFIGS:
        sig = []          # (month, ret)
        for code, s in data.items():
            for i in range(LOOKBACK, len(s) - 12):
                win = [c for _, c in s[i - LOOKBACK:i + 1]]
                lo, hi = min(win), max(win)
                px = s[i][1]
                if lo <= 0:
                    continue
                if px / lo - 1 >= min_off_low and hi / px - 1 >= min_to_high:
                    sig.append((ym(s[i][0]), (s[i + 12][1] / px - 1) * 100))
        if not sig:
            print(f"{label:<22} 無訊號")
            continue

        rets = [r for _, r in sig]
        months = [m for m, _ in sig]
        # 同月基準：把每個訊號對應月份的全樣本池，依訊號月份分布加權組合
        matched = []
        cnt = collections.Counter(months)
        for m, k in cnt.items():
            matched.extend(pool[m] * 1)  # 每個出現的月份取其整池一次
        # 依訊號數加權的同月基準（更精確：逐訊號抽同月全池）
        matched_w = []
        for m, k in cnt.items():
            matched_w.extend(pool[m])

        med_s = statistics.median(rets)
        med_b = statistics.median(matched_w)
        h_s = sum(1 for x in rets if x > 100) / len(rets) * 100
        h_b = sum(1 for x in matched_w if x > 100) / len(matched_w) * 100

        # 月份叢集 bootstrap：以「月份」為抽樣單位（訊號在同月高度相關）
        by_month = collections.defaultdict(list)
        for m, r in sig:
            by_month[m].append(r)
        keys = list(by_month)
        rng = random.Random(7)
        diffs = []
        for _ in range(2000):
            samp = []
            base = []
            for _ in range(len(keys)):
                m = keys[rng.randrange(len(keys))]
                samp.extend(by_month[m])
                base.extend(pool[m])
            if samp and base:
                diffs.append(statistics.median(samp) - statistics.median(base))
        # 雙尾 p：差異分布跨過 0 的比例
        if diffs:
            neg = sum(1 for d in diffs if d <= 0) / len(diffs)
            p = 2 * min(neg, 1 - neg)
        else:
            p = float("nan")

        print(f"{label:<22}{len(rets):>6}{med_s:>8.1f}%{med_b:>8.1f}%"
              f"{med_s - med_b:>7.1f}%{h_s:>7.1f}%{h_b:>9.1f}%{p:>11.3f}")

    # 訊號的時間分布：證明叢聚
    print("\n═══ 條件 B 的訊號年份分布（證明訊號在時間上叢聚）═══")
    sigB = []
    for code, s in data.items():
        for i in range(LOOKBACK, len(s) - 12):
            win = [c for _, c in s[i - LOOKBACK:i + 1]]
            lo, hi = min(win), max(win)
            px = s[i][1]
            if lo <= 0:
                continue
            if px / lo - 1 >= 1.00 and hi / px - 1 >= 1.00:
                sigB.append(s[i][0].year)
    allyears = []
    for code, s in data.items():
        for i in range(LOOKBACK, len(s) - 12):
            allyears.append(s[i][0].year)
    cb, ca = collections.Counter(sigB), collections.Counter(allyears)
    print(f"{'年份':<8}{'B訊號數':>9}{'佔B比重':>9}{'全樣本比重':>11}")
    for y in sorted(ca):
        pb = cb.get(y, 0) / len(sigB) * 100 if sigB else 0
        pa = ca[y] / len(allyears) * 100
        print(f"{y:<8}{cb.get(y,0):>9}{pb:>8.1f}%{pa:>10.1f}%")


if __name__ == "__main__":
    main()
