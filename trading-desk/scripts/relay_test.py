#!/usr/bin/env python3
"""
測試「A 站上季線之後，B 才會發動」這類接力說法。

用法：python scripts/relay_test.py 3481 3673 [年數]
      python scripts/relay_test.py 3481 3673 5

為什麼需要這支：
市場上這類「A 帶動 B」的說法極多，聽起來都很合理，但幾乎沒有人回測過。
本腳本把它變成可證偽的檢定：找出歷史上所有「A 站上季線」的事件，
看 B 在事件後的報酬分布，並與 B 的無條件報酬比較。

⚠️ 已知限制（必讀）：
1. 這類事件樣本數通常只有個位數到十幾次，統計上非常弱，不足以下強結論。
2. 沒有控制大盤與產業共同因子——A 與 B 同屬面板/觸控供應鏈，
   兩者一起漲很可能只是同產業 beta，不是「A 帶動 B」。
3. 未扣交易成本。台股散戶的證交稅與手續費會吃掉大部分短線價差。
"""
import json
import sys
import urllib.request
import datetime
import statistics

UA = {"User-Agent": "Mozilla/5.0"}


def fetch(code, years):
    sym = code if code.startswith("%5E") else f"{code}.TW"
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?interval=1d&range={years}y")
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    rows = []
    for t, o, h, l, c in zip(r["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if None in (o, h, l, c):
            continue
        rows.append({
            "d": datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
            "o": o, "h": h, "l": l, "c": c,
        })
    return rows


def sma(vals, n):
    out = [None] * len(vals)
    s = 0.0
    for i, v in enumerate(vals):
        s += v
        if i >= n:
            s -= vals[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def analyse(rows, label):
    c = [r["c"] for r in rows]
    ma20, ma60, ma120 = sma(c, 20), sma(c, 60), sma(c, 120)
    last = len(c) - 1
    px = c[last]
    print(f"\n\033[1m{label}\033[0m  最新收盤 {px:,.2f}（{rows[last]['d']}）")
    for name, ma in (("月線 20MA", ma20), ("季線 60MA", ma60), ("半年線 120MA", ma120)):
        v = ma[last]
        if v is None:
            print(f"  {name:<12} 資料不足")
            continue
        gap = (px / v - 1) * 100
        state = "站上" if px > v else "跌破"
        print(f"  {name:<12} {v:>10,.2f}   {state}，偏離 {gap:+6.2f}%")
    hi = max(r["h"] for r in rows)
    lo = min(r["l"] for r in rows)
    print(f"  區間高低      {lo:,.2f} – {hi:,.2f}   目前位置 "
          f"{(px - lo) / (hi - lo) * 100:.0f}%")
    return {"c": c, "ma20": ma20, "ma60": ma60, "ma120": ma120, "rows": rows}


def cross_events(a):
    """找出『收盤由季線下方轉為站上』的事件索引。"""
    ev = []
    c, ma = a["c"], a["ma60"]
    for i in range(1, len(c)):
        if ma[i] is None or ma[i - 1] is None:
            continue
        if c[i - 1] <= ma[i - 1] and c[i] > ma[i]:
            ev.append(i)
    return ev


def fwd_ret(c, i, n):
    j = i + n
    return (c[j] / c[i] - 1) * 100 if j < len(c) else None


def main():
    ca, cb = sys.argv[1], sys.argv[2]
    years = sys.argv[3] if len(sys.argv) > 3 else "5"

    ra, rb = fetch(ca, years), fetch(cb, years)
    # 以日期對齊
    da = {r["d"]: r for r in ra}
    db = {r["d"]: r for r in rb}
    common = sorted(set(da) & set(db))
    ra = [da[d] for d in common]
    rb = [db[d] for d in common]
    print(f"共同交易日 {len(common)} 天：{common[0]} → {common[-1]}")

    A = analyse(ra, f"{ca}（觸發標的）")
    B = analyse(rb, f"{cb}（被帶動標的）")

    ev = cross_events(A)
    print(f"\n\033[1m═══ 檢定：「{ca} 站上季線」之後 {cb} 的表現 ═══\033[0m")
    print(f"歷史上 {ca} 收盤站上季線的事件：{len(ev)} 次")
    if len(ev) < 5:
        print("⚠️ 事件數 < 5，統計上無意義，以下數字只能當描述，不能當結論。")

    horizons = [5, 10, 20, 60]
    cbv = B["c"]
    cav = A["c"]
    print(f"\n{'期間':<8}{'B 事件後平均':>14}{'B 中位數':>12}{'B 勝率':>10}"
          f"{'B 無條件平均':>14}{'A 事件後平均':>14}")
    print("─" * 74)
    for n in horizons:
        er = [fwd_ret(cbv, i, n) for i in ev]
        er = [x for x in er if x is not None]
        ar = [fwd_ret(cav, i, n) for i in ev]
        ar = [x for x in ar if x is not None]
        base = [fwd_ret(cbv, i, n) for i in range(len(cbv) - n)]
        base = [x for x in base if x is not None]
        if not er:
            continue
        win = sum(1 for x in er if x > 0) / len(er) * 100
        print(f"{n:>3} 日  {statistics.mean(er):>13.2f}%{statistics.median(er):>11.2f}%"
              f"{win:>9.0f}%{statistics.mean(base):>13.2f}%"
              f"{statistics.mean(ar) if ar else float('nan'):>13.2f}%")

    print(f"\n判讀：只有當「B 事件後平均」明顯高於「B 無條件平均」時，"
          f"\n      這個接力說法才有初步證據。若兩者接近，代表 B 只是跟著漲，"
          f"\n      沒有『等 A 發動完才輪到 B』的關係。")

    # 領先落後相關（日報酬）
    print(f"\n\033[1m═══ 領先落後檢定（日報酬相關係數）═══\033[0m")
    reta = [(cav[i] / cav[i - 1] - 1) for i in range(1, len(cav))]
    retb = [(cbv[i] / cbv[i - 1] - 1) for i in range(1, len(cbv))]
    print(f"{'A 領先天數':<12}{'相關係數':>10}")
    print("─" * 24)
    for lag in range(0, 6):
        x = reta[:len(reta) - lag] if lag else reta
        y = retb[lag:]
        m = min(len(x), len(y))
        x, y = x[:m], y[:m]
        try:
            r = statistics.correlation(x, y)
        except Exception:
            r = float("nan")
        mark = "  ← 同步" if lag == 0 else ""
        print(f"lag {lag:<8}{r:>10.3f}{mark}")
    print("\n判讀：若 lag 0 最高、之後遞減，代表兩檔是同步共動（同產業 beta），")
    print("      沒有領先落後關係。若某個 lag>0 明顯高於 lag 0，才支持『A 領先 B』。")


if __name__ == "__main__":
    main()
