#!/usr/bin/env python3
"""
進出場規則回測 — 勝率 vs 期望值的實證對照。

用法：python scripts/backtest.py 3481 2303 2344 2313 1802 3673

設計原則（避免回測最常見的三種作弊）：
1. 無前視偏誤：訊號用第 t 日收盤資料計算，第 t+1 日「開盤」成交。
   （用當日收盤價成交是回測最常見的作弊，會系統性高估績效）
2. 計入交易成本：台股賣出證交稅 0.3% + 手續費 0.1425% 雙邊（可設折讓）。
3. 同一組資料同時報告勝率與期望值，不挑對自己有利的指標。

⚠️ 回測的根本限制（無法用更好的程式解決）：
- 這是「在已知的歷史上」找最佳規則，必然過度配適（overfitting）。
- 測越多組規則，最好的那組越可能只是運氣。這正是 Harvey, Liu & Zhu (2016)
  「因子動物園」批評的核心：多重檢定會製造出大量假陽性。
- 樣本期涵蓋特定產業循環，換一個循環未必成立。
"""
import json
import sys
import urllib.request
import datetime
import statistics

UA = {"User-Agent": "Mozilla/5.0"}
NAMES = {"3481": "群創", "3673": "TPK-KY", "2303": "聯電", "2344": "華邦電",
         "2313": "華通", "1802": "台玻", "2330": "台積電", "%5ETWII": "加權指數"}

# 台股成本：賣出證交稅 0.3%，手續費 0.1425% 雙邊（假設 4 折折讓 → 0.057%）
TAX = 0.003
FEE = 0.001425 * 0.4


def fetch(code, years="5"):
    sym = code if code.startswith("%5E") else f"{code}.TW"
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?interval=1d&range={years}y")
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    rows = []
    for t, o, h, l, c in zip(r["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if None in (o, h, l, c) or o <= 0:
            continue
        rows.append({"d": datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                     "o": o, "h": h, "l": l, "c": c})
    return rows


def sma_series(v, n):
    out = [None] * len(v)
    s = 0.0
    for i, x in enumerate(v):
        s += x
        if i >= n:
            s -= v[i - n]
        if i >= n - 1:
            out[i] = s / n
    return out


def rsi_series(v, n=14):
    out = [None] * len(v)
    gains, losses = [], []
    for i in range(1, len(v)):
        ch = v[i] - v[i - 1]
        gains.append(max(ch, 0.0))
        losses.append(max(-ch, 0.0))
        if len(gains) >= n:
            ag = sum(gains[-n:]) / n
            al = sum(losses[-n:]) / n
            out[i] = 100.0 if al == 0 else 100 - 100 / (1 + ag / al)
    return out


def run(rows, entry, exit_, tp=None, sl=None):
    """
    entry/exit_: 函式 (i, ctx) -> bool，用第 i 日收盤資料判斷，第 i+1 日開盤成交。
    tp/sl: 停利/停損百分比（以進場價為基準，用當日最高/最低價觸發，同日以停損優先）。
    回傳每筆交易的淨報酬率（%）清單。
    """
    c = [r["c"] for r in rows]
    ctx = {
        "c": c, "rows": rows,
        "ma5": sma_series(c, 5), "ma20": sma_series(c, 20),
        "ma60": sma_series(c, 60), "ma120": sma_series(c, 120),
        "rsi": rsi_series(c),
    }
    trades = []
    pos = None
    for i in range(len(rows) - 1):
        nxt = rows[i + 1]
        if pos is None:
            if entry(i, ctx):
                pos = {"px": nxt["o"], "i": i + 1}
        else:
            ep = pos["px"]
            # 停損優先（保守假設：同日同時觸及時假定先觸發停損）
            if sl is not None and nxt["l"] <= ep * (1 - sl):
                trades.append(net(ep, ep * (1 - sl)))
                pos = None
                continue
            if tp is not None and nxt["h"] >= ep * (1 + tp):
                trades.append(net(ep, ep * (1 + tp)))
                pos = None
                continue
            if exit_(i, ctx):
                trades.append(net(ep, nxt["o"]))
                pos = None
    if pos is not None:                      # 期末仍持有 → 以最後收盤平倉
        trades.append(net(pos["px"], rows[-1]["c"]))
    return trades


def net(buy, sell):
    """扣除成本後的淨報酬率（%）"""
    cost_buy = buy * FEE
    cost_sell = sell * (FEE + TAX)
    return ((sell - cost_sell) - (buy + cost_buy)) / (buy + cost_buy) * 100


def stats(trades):
    if not trades:
        return None
    wins = [t for t in trades if t > 0]
    losses = [t for t in trades if t <= 0]
    wr = len(wins) / len(trades) * 100
    aw = statistics.mean(wins) if wins else 0.0
    al = statistics.mean(losses) if losses else 0.0
    exp = statistics.mean(trades)
    # 複利總報酬
    eq = 1.0
    peak = 1.0
    mdd = 0.0
    for t in trades:
        eq *= (1 + t / 100)
        peak = max(peak, eq)
        mdd = min(mdd, eq / peak - 1)
    return {"n": len(trades), "wr": wr, "aw": aw, "al": al, "exp": exp,
            "pf": (sum(wins) / abs(sum(losses))) if losses and sum(losses) != 0 else float("inf"),
            "total": (eq - 1) * 100, "mdd": mdd * 100}


# ── 策略定義 ────────────────────────────────────────────────
def strategies():
    S = {}
    S["買進持有"] = (lambda i, x: i == 0, lambda i, x: False, None, None)
    S["站上季線買/跌破賣"] = (
        lambda i, x: x["ma60"][i] and x["c"][i] > x["ma60"][i],
        lambda i, x: x["ma60"][i] and x["c"][i] < x["ma60"][i], None, None)
    S["站上月線買/跌破賣"] = (
        lambda i, x: x["ma20"][i] and x["c"][i] > x["ma20"][i],
        lambda i, x: x["ma20"][i] and x["c"][i] < x["ma20"][i], None, None)
    S["黃金交叉20/60"] = (
        lambda i, x: x["ma20"][i] and x["ma60"][i] and x["ma20"][i] > x["ma60"][i],
        lambda i, x: x["ma20"][i] and x["ma60"][i] and x["ma20"][i] < x["ma60"][i], None, None)
    S["突破20日高"] = (
        lambda i, x: i >= 20 and x["c"][i] >= max(x["c"][i - 20:i]),
        lambda i, x: i >= 20 and x["c"][i] <= min(x["c"][i - 20:i]), None, None)
    S["RSI<30買/>70賣"] = (
        lambda i, x: x["rsi"][i] is not None and x["rsi"][i] < 30,
        lambda i, x: x["rsi"][i] is not None and x["rsi"][i] > 70, None, None)
    # 停利停損組合：同一個進場訊號，只改出場
    base_in = lambda i, x: x["ma20"][i] and x["c"][i] > x["ma20"][i]
    never = lambda i, x: False
    S["月線進+停利3%/停損20%"] = (base_in, never, 0.03, 0.20)
    S["月線進+停利10%/停損10%"] = (base_in, never, 0.10, 0.10)
    S["月線進+停利30%/停損8%"] = (base_in, never, 0.30, 0.08)
    return S


def main():
    codes = sys.argv[1:] or ["3481", "2303", "2344", "2313", "1802", "3673"]
    S = strategies()
    agg = {k: [] for k in S}

    for code in codes:
        try:
            rows = fetch(code)
        except Exception as e:
            print(f"{NAMES.get(code, code)} 抓取失敗：{str(e)[:50]}")
            continue
        print(f"\n\033[1m═══ {NAMES.get(code, code)} {code} ═══\033[0m  "
              f"{rows[0]['d']} → {rows[-1]['d']}（{len(rows)} 日）")
        print(f"{'策略':<22}{'交易數':>6}{'勝率':>8}{'平均賺':>8}{'平均賠':>8}"
              f"{'賺賠比':>7}{'期望值':>8}{'總報酬':>10}{'最大回撤':>9}")
        print("─" * 88)
        for name, (en, ex, tp, sl) in S.items():
            st = stats(run(rows, en, ex, tp, sl))
            if not st:
                print(f"{name:<22} 無交易")
                continue
            agg[name].append(st)
            pf = "∞" if st["pf"] == float("inf") else f"{st['pf']:.2f}"
            print(f"{name:<22}{st['n']:>6}{st['wr']:>7.1f}%{st['aw']:>7.2f}%"
                  f"{st['al']:>7.2f}%{pf:>7}{st['exp']:>7.2f}%"
                  f"{st['total']:>9.1f}%{st['mdd']:>8.1f}%")

    print(f"\n\n\033[1m═══ 六檔平均（跨標的彙總）═══\033[0m")
    print(f"{'策略':<22}{'平均勝率':>9}{'平均期望值':>11}{'平均總報酬':>11}"
          f"{'平均最大回撤':>12}{'勝率排名':>9}{'期望值排名':>11}")
    print("─" * 86)
    rows_out = []
    for name, lst in agg.items():
        if not lst:
            continue
        rows_out.append({
            "name": name,
            "wr": statistics.mean(s["wr"] for s in lst),
            "exp": statistics.mean(s["exp"] for s in lst),
            "total": statistics.mean(s["total"] for s in lst),
            "mdd": statistics.mean(s["mdd"] for s in lst),
        })
    by_wr = sorted(rows_out, key=lambda r: -r["wr"])
    by_exp = sorted(rows_out, key=lambda r: -r["exp"])
    rank_wr = {r["name"]: i + 1 for i, r in enumerate(by_wr)}
    rank_exp = {r["name"]: i + 1 for i, r in enumerate(by_exp)}
    for r in by_wr:
        print(f"{r['name']:<22}{r['wr']:>8.1f}%{r['exp']:>10.2f}%{r['total']:>10.1f}%"
              f"{r['mdd']:>11.1f}%{rank_wr[r['name']]:>9}{rank_exp[r['name']]:>11}")

    print("\n★ 看『勝率排名』與『期望值排名』的落差 —— 那就是「追求勝率」的代價。")


if __name__ == "__main__":
    main()
