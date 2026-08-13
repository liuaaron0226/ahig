#!/usr/bin/env python3
"""
「找下一檔群創」篩選器的歷史檢定。

假說來源：群創 2026 年 4 月在 23 元時的特徵——
  已從多年低點翻倍（11 → 23），但距多年高點仍遠，屬低估值循環股。

用法：python scripts/screen_test.py [樣本檔數]

檢定方式（避免前視偏誤）：
  在每個月底，只用「當時已知」的價格資料篩選，
  然後計算「之後」6 / 12 個月的實際報酬。
  篩選當下不使用任何未來資訊。

⚠️ 本檢定的根本限制：
  - 樣本不含已下市個股（存活者偏誤），所有報酬偏樂觀。
  - 只用價格特徵，未納入基本面（估值、營收）——因為歷史估值資料難取得。
  - 測了多組參數，「最好的那組」很可能是過度配適（Harvey, Liu & Zhu 2016）。
"""
import json
import sys
import urllib.request
import datetime
import statistics
import random
import collections
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


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 300
    codes = universe(n)
    print(f"抽樣 {len(codes)} 檔，抓取月線資料…")
    data = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        for code, s in ex.map(get, codes):
            if s and len(s) >= 60:
                data[code] = s
    print(f"取得 {len(data)} 檔（至少 60 個月）\n")

    # 篩選參數：以「當月收盤」為基準點 i
    #   off_low  = 距 36 個月低點的漲幅
    #   to_high  = 距 36 個月高點還有多少上檔空間
    CONFIGS = [
        ("A 已翻倍+距高點>50%", 1.00, 0.50),
        ("B 已翻倍+距高點>100%", 1.00, 1.00),
        ("C 漲50%+距高點>50%", 0.50, 0.50),
        ("D 漲200%+距高點>50%", 2.00, 0.50),
        ("E 漲30%+距高點>30%", 0.30, 0.30),
    ]
    LOOKBACK = 36

    print(f"{'篩選條件':<22}{'訊號數':>7}{'6M中位':>9}{'12M中位':>9}"
          f"{'12M平均':>9}{'12M>100%':>10}{'12M<-20%':>10}")
    print("─" * 78)

    baseline_12 = []
    for code, s in data.items():
        for i in range(LOOKBACK, len(s) - 12):
            baseline_12.append((s[i + 12][1] / s[i][1] - 1) * 100)

    results = {}
    for label, min_off_low, min_to_high in CONFIGS:
        r6, r12 = [], []
        picks = []
        for code, s in data.items():
            for i in range(LOOKBACK, len(s) - 12):
                win = [c for _, c in s[i - LOOKBACK:i + 1]]
                lo, hi = min(win), max(win)
                px = s[i][1]
                if lo <= 0:
                    continue
                off_low = px / lo - 1
                to_high = hi / px - 1
                if off_low >= min_off_low and to_high >= min_to_high:
                    f6 = (s[i + 6][1] / px - 1) * 100
                    f12 = (s[i + 12][1] / px - 1) * 100
                    r6.append(f6)
                    r12.append(f12)
                    picks.append((code, s[i][0], px, f12))
        if not r12:
            print(f"{label:<22} 無訊號")
            continue
        hit100 = sum(1 for x in r12 if x > 100) / len(r12) * 100
        bad = sum(1 for x in r12 if x < -20) / len(r12) * 100
        results[label] = {"r12": r12, "picks": picks}
        print(f"{label:<22}{len(r12):>7}{statistics.median(r6):>8.1f}%"
              f"{statistics.median(r12):>8.1f}%{statistics.mean(r12):>8.1f}%"
              f"{hit100:>9.1f}%{bad:>9.1f}%")

    b100 = sum(1 for x in baseline_12 if x > 100) / len(baseline_12) * 100
    bbad = sum(1 for x in baseline_12 if x < -20) / len(baseline_12) * 100
    print(f"{'【基準】全樣本隨機':<22}{len(baseline_12):>7}{'—':>9}"
          f"{statistics.median(baseline_12):>8.1f}%{statistics.mean(baseline_12):>8.1f}%"
          f"{b100:>9.1f}%{bbad:>9.1f}%")

    print("\n判讀：只有當篩選後的『12M>100%』明顯高於基準，這個篩選才有價值。")
    print("      同時要看『12M<-20%』——如果它也一起變高，代表只是提高了波動，不是提高了勝算。")

    # 最佳條件的年度穩定性
    best = max(results, key=lambda k: statistics.median(results[k]["r12"])) if results else None
    if best:
        print(f"\n═══ 「{best}」的逐年穩定性（訊號發生年份 → 之後 12 個月報酬）═══")
        byyear = collections.defaultdict(list)
        for code, d, px, f12 in results[best]["picks"]:
            byyear[d.year].append(f12)
        print(f"{'年份':<8}{'訊號數':>7}{'12M中位':>10}{'12M平均':>10}{'>100%比率':>11}")
        print("─" * 48)
        for y in sorted(byyear):
            v = byyear[y]
            print(f"{y:<8}{len(v):>7}{statistics.median(v):>9.1f}%"
                  f"{statistics.mean(v):>9.1f}%"
                  f"{sum(1 for x in v if x > 100) / len(v) * 100:>10.1f}%")
        print("\n若中位數逐年劇烈變動，代表這個篩選對『時機』極度敏感，")
        print("在錯的年份使用會虧損——那就不是一個可靠的選股法則。")


if __name__ == "__main__":
    main()
