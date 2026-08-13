#!/usr/bin/env python3
"""
進場時機檢定 —— 「反正要長期持有，那該現在買還是等技術訊號？」

這和一般的技術分析回測是**不同的問題**：
  一般回測問：「這個技術規則能不能產生 alpha？」（進出場都靠它）
  本檢定問：  「我已經決定要長抱這檔，等訊號進場能不能比立刻買更好？」

方法論關鍵（多數散戶測試會做錯的地方）：
  **所有策略都從「決策日」開始計算報酬，不是從「進場日」。**
  因為等待有機會成本——如果等的期間股票漲走了，那個損失必須算在等待策略頭上。
  用進場日計算會系統性偏袒等待策略，是常見的作弊。

用法：python scripts/entry_timing.py [持有月數]
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
HOLD = int(sys.argv[1]) if len(sys.argv) > 1 else 24     # 持有月數
WAIT = 6                                                 # 最長等待月數


def universe(n=300):
    lst = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL", headers=UA), timeout=30))
    codes = [r["Code"] for r in lst if r["Code"].isdigit() and len(r["Code"]) == 4]
    random.seed(7)
    return random.sample(codes, n)


def get(code):
    try:
        u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW"
             f"?interval=1mo&range=10y")
        r = json.load(urllib.request.urlopen(
            urllib.request.Request(u, headers=UA), timeout=25))["chart"]["result"][0]
        q = r["indicators"]["quote"][0]
        s = [(datetime.datetime.utcfromtimestamp(t), c)
             for t, c in zip(r["timestamp"], q["close"]) if c]
        return code, s
    except Exception:
        return code, None


def sma(v, i, n):
    if i + 1 < n:
        return None
    return sum(v[i - n + 1:i + 1]) / n


def main():
    codes = universe()
    data = {}
    with ThreadPoolExecutor(max_workers=12) as ex:
        for c, s in ex.map(get, codes):
            if s and len(s) >= 60:
                data[c] = s
    print(f"樣本 {len(data)} 檔台股，月線 10 年")
    print(f"設定：決策後持有 {HOLD} 個月，等待型策略最長等 {WAIT} 個月\n")

    res = collections.defaultdict(list)

    for code, s in data.items():
        px = [c for _, c in s]
        n = len(px)
        for i in range(12, n - HOLD - WAIT):
            p0 = px[i]                       # 決策日價格
            end = px[i + HOLD]               # 決策後 HOLD 個月的價格（所有策略共用終點）

            # 1) 立刻買
            res["立刻買進"].append((end / p0 - 1) * 100)

            # 2) 等回檔到月線(3個月均) 才買，最多等 WAIT 個月
            entry = None
            for k in range(1, WAIT + 1):
                m = sma(px, i + k, 3)
                if m and px[i + k] <= m:
                    entry = px[i + k]
                    break
            if entry is None:
                entry = px[i + WAIT]
            res[f"等回檔(≤{WAIT}月)"].append((end / entry - 1) * 100)

            # 3) 等跌 10% 才買
            entry = None
            for k in range(1, WAIT + 1):
                if px[i + k] <= p0 * 0.90:
                    entry = px[i + k]
                    break
            if entry is None:
                entry = px[i + WAIT]
            res[f"等跌10%(≤{WAIT}月)"].append((end / entry - 1) * 100)

            # 4) 等突破：站上 6 個月均線才買
            entry = None
            for k in range(1, WAIT + 1):
                m = sma(px, i + k, 6)
                if m and px[i + k] > m:
                    entry = px[i + k]
                    break
            if entry is None:
                entry = px[i + WAIT]
            res[f"等突破(≤{WAIT}月)"].append((end / entry - 1) * 100)

            # 5) 分批：決策後 0,2,4 月各買 1/3
            legs = [px[i], px[i + 2], px[i + 4]]
            # 等權金額 → 平均成本用調和平均
            avg = 3 / sum(1 / p for p in legs)
            res["分批3次(0/2/4月)"].append((end / avg - 1) * 100)

            # 6) 分批 6 次（每月一筆）
            legs = [px[i + k] for k in range(6)]
            avg = 6 / sum(1 / p for p in legs)
            res["分批6次(每月)"].append((end / avg - 1) * 100)

    print(f"{'策略':<20}{'樣本':>8}{'中位報酬':>10}{'平均報酬':>10}"
          f"{'勝率':>8}{'>100%':>8}{'<-30%':>8}")
    print("─" * 72)
    base_med = statistics.median(res["立刻買進"])
    order = ["立刻買進", f"等回檔(≤{WAIT}月)", f"等跌10%(≤{WAIT}月)",
             f"等突破(≤{WAIT}月)", "分批3次(0/2/4月)", "分批6次(每月)"]
    for k in order:
        v = res[k]
        if not v:
            continue
        med = statistics.median(v)
        win = sum(1 for x in v if x > 0) / len(v) * 100
        h = sum(1 for x in v if x > 100) / len(v) * 100
        l = sum(1 for x in v if x < -30) / len(v) * 100
        mark = "" if k == "立刻買進" else f"  ({med - base_med:+.1f}pp)"
        print(f"{k:<20}{len(v):>8}{med:>9.1f}%{statistics.mean(v):>9.1f}%"
              f"{win:>7.1f}%{h:>7.1f}%{l:>7.1f}%{mark}")

    print(f"\n所有策略的報酬都從**決策日**起算，終點相同（決策後 {HOLD} 個月）。")
    print("括號內是相對「立刻買進」的中位數差距（百分點）。")
    print("\n若等待型策略沒有明顯正的差距，代表：對長期持有而言，")
    print("進場時機的優化空間遠小於一般人的想像——而等待的機會成本是真實的。")


if __name__ == "__main__":
    main()
