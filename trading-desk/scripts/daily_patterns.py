#!/usr/bin/env python3
"""
單日型態的條件機率 — 「開高走低或其他可能」的實證版本。

用法：python scripts/daily_patterns.py 3481 2344 2303 3673 2313 1802

四種型態（以當日開盤 vs 前日收盤、當日收盤 vs 當日開盤 定義）：
  開高走高  gap up   + close > open
  開高走低  gap up   + close < open
  開低走高  gap down + close > open
  開低走低  gap down + close < open

輸出：
1. 無條件分布 — 這檔平常四種型態各佔多少
2. 條件分布 — 在「昨天漲停」「昨天大漲」「昨天大跌」之後，隔天的型態分布
3. 跳空統計 — 跳空幅度分布與當日回補率

⚠️ 這不是預測。這是頻率統計。
   「漲停隔天有 X% 開高走低」是歷史頻率，不是明天的機率，
   因為每一天的成因不同，而樣本裡的每次漲停成因也都不同。
   它的用途是校準預期：知道什麼是常見的，什麼是罕見的。
"""
import json
import sys
import urllib.request
import datetime
import statistics

UA = {"User-Agent": "Mozilla/5.0"}
NAMES = {"3481": "群創", "3673": "TPK-KY", "2303": "聯電", "2344": "華邦電",
         "2313": "華通", "1802": "台玻", "2330": "台積電", "%5ETWII": "加權指數"}


def fetch(code, years="5"):
    sym = code if code.startswith("%5E") else f"{code}.TW"
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?interval=1d&range={years}y")
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    rows = []
    for t, o, h, l, c in zip(r["timestamp"], q["open"], q["high"], q["low"], q["close"]):
        if None in (o, h, l, c) or o == 0:
            continue
        rows.append({"d": datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                     "o": o, "h": h, "l": l, "c": c})
    return rows


def classify(prev_c, o, c):
    """回傳 (型態, 跳空%, 盤中%)"""
    gap = (o / prev_c - 1) * 100
    intra = (c / o - 1) * 100
    if gap >= 0 and intra >= 0:
        t = "開高走高"
    elif gap >= 0:
        t = "開高走低"
    elif intra >= 0:
        t = "開低走高"
    else:
        t = "開低走低"
    return t, gap, intra


TYPES = ["開高走高", "開高走低", "開低走高", "開低走低"]


def dist(days):
    n = len(days)
    if n == 0:
        return None
    out = {}
    for t in TYPES:
        k = sum(1 for d in days if d["type"] == t)
        out[t] = (k, k / n * 100)
    rets = [d["ret"] for d in days]
    out["_n"] = n
    out["_mean"] = statistics.mean(rets)
    out["_med"] = statistics.median(rets)
    out["_win"] = sum(1 for r in rets if r > 0) / n * 100
    return out


def show(title, d, indent="  "):
    if not d:
        print(f"{indent}{title}: 無樣本")
        return
    line = f"{indent}{title:<22} n={d['_n']:<5}"
    for t in TYPES:
        k, p = d[t]
        line += f"{t} {p:>5.1f}%  "
    print(line)
    print(f"{indent}{'':<22} 隔日報酬 平均 {d['_mean']:+.2f}%  中位數 {d['_med']:+.2f}%  上漲比率 {d['_win']:.0f}%")


def main():
    codes = sys.argv[1:] or ["3481", "2344", "2303", "3673", "2313", "1802"]
    for code in codes:
        try:
            rows = fetch(code)
        except Exception as e:
            print(f"{NAMES.get(code, code)} 抓取失敗：{str(e)[:50]}")
            continue

        days = []
        for i in range(1, len(rows)):
            prev = rows[i - 1]
            t, gap, intra = classify(prev["c"], rows[i]["o"], rows[i]["c"])
            days.append({
                "d": rows[i]["d"], "type": t, "gap": gap, "intra": intra,
                "ret": (rows[i]["c"] / prev["c"] - 1) * 100,
                "prev_ret": (prev["c"] / rows[i - 2]["c"] - 1) * 100 if i >= 2 else 0.0,
                "o": rows[i]["o"], "c": rows[i]["c"], "l": rows[i]["l"],
                "h": rows[i]["h"], "prev_c": prev["c"],
            })

        name = NAMES.get(code, code)
        print(f"\n\033[1m═══ {name} {code} ═══\033[0m  樣本 {len(days)} 個交易日"
              f"（{days[0]['d']} → {days[-1]['d']}）")

        show("【無條件】平常", dist(days))

        # 條件：前一日漲停 / 大漲 / 大跌
        conds = [
            ("前日漲停(≥9.5%)", lambda x: x["prev_ret"] >= 9.5),
            ("前日大漲(5~9.5%)", lambda x: 5 <= x["prev_ret"] < 9.5),
            ("前日大跌(≤-5%)", lambda x: x["prev_ret"] <= -5),
        ]
        print()
        for label, fn in conds:
            sub = [x for x in days if fn(x)]
            show(f"【條件】{label}", dist(sub))

        # 跳空統計
        gaps = [x["gap"] for x in days]
        up = [x for x in days if x["gap"] > 0.5]
        dn = [x for x in days if x["gap"] < -0.5]
        # 跳空回補 = 開高後當日最低跌回前收 / 開低後當日最高漲回前收
        fill_up = sum(1 for x in up if x["l"] <= x["prev_c"]) / len(up) * 100 if up else 0
        fill_dn = sum(1 for x in dn if x["h"] >= x["prev_c"]) / len(dn) * 100 if dn else 0
        print(f"\n  跳空：向上>0.5% 共 {len(up)} 次，其中 {fill_up:.0f}% 當日回補（最低價跌回前收）")
        print(f"        向下>0.5% 共 {len(dn)} 次，其中 {fill_dn:.0f}% 當日回補（最高價漲回前收）")
        print(f"        跳空幅度中位數 {statistics.median([abs(g) for g in gaps]):.2f}%")


if __name__ == "__main__":
    main()
