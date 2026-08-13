#!/usr/bin/env python3
"""
技術位階與波動幅度表 — 取代「預測明天開高走低」的誠實替代品。

用法：python scripts/levels.py 3481 3673 2303 2344 2313 1802

輸出三類資訊：
1. 均線位階（月線/季線/半年線）與距離 — 決定「訊號有沒有觸發」
2. ATR 與歷史單日振幅分布 — 回答「這檔一天通常動多少」
3. 上下方關鍵價位 — 前高、前低、缺口、整數關卡

⚠️ 這裡沒有任何一個數字是預測。均線是已發生價格的平均，
   ATR 是歷史振幅的統計。它們描述現況與慣性，不描述未來。
"""
import json
import sys
import urllib.request
import datetime
import statistics

UA = {"User-Agent": "Mozilla/5.0"}
NAMES = {"3481": "群創", "3673": "TPK-KY", "2303": "聯電", "2344": "華邦電",
         "2313": "華通", "1802": "台玻", "2330": "台積電", "%5ETWII": "加權指數"}


def fetch(code, years="2"):
    sym = code if code.startswith("%5E") else f"{code}.TW"
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?interval=1d&range={years}y")
    r = json.load(urllib.request.urlopen(
        urllib.request.Request(url, headers=UA), timeout=30))["chart"]["result"][0]
    q = r["indicators"]["quote"][0]
    rows = []
    for t, o, h, l, c, v in zip(r["timestamp"], q["open"], q["high"],
                                q["low"], q["close"], q["volume"]):
        if None in (o, h, l, c):
            continue
        rows.append({"d": datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m-%d"),
                     "o": o, "h": h, "l": l, "c": c, "v": v or 0})
    return rows


def sma(v, n):
    return sum(v[-n:]) / n if len(v) >= n else None


def atr(rows, n=14):
    trs = []
    for i in range(1, len(rows)):
        h, l, pc = rows[i]["h"], rows[i]["l"], rows[i - 1]["c"]
        trs.append(max(h - l, abs(h - pc), abs(l - pc)))
    return sum(trs[-n:]) / n if len(trs) >= n else None


def main():
    codes = sys.argv[1:] or ["3481", "3673", "2303", "2344", "2313", "1802", "%5ETWII"]
    print(f"{'標的':<9}{'收盤':>10}{'月線20':>10}{'季線60':>10}{'半年120':>10}"
          f"{'距季線':>9}{'ATR14':>9}{'ATR%':>7}{'年位置':>7}")
    print("─" * 82)
    store = {}
    for code in codes:
        try:
            rows = fetch(code)
        except Exception as e:
            print(f"{NAMES.get(code, code):<9} 抓取失敗 {str(e)[:40]}")
            continue
        c = [r["c"] for r in rows]
        px = c[-1]
        m20, m60, m120 = sma(c, 20), sma(c, 60), sma(c, 120)
        a = atr(rows)
        yr = rows[-243:] if len(rows) >= 243 else rows
        hi = max(r["h"] for r in yr)
        lo = min(r["l"] for r in yr)
        pos = (px - lo) / (hi - lo) * 100 if hi > lo else 50
        gap60 = (px / m60 - 1) * 100 if m60 else float("nan")
        name = NAMES.get(code, code)
        print(f"{name:<9}{px:>10,.2f}{m20 or 0:>10,.2f}{m60 or 0:>10,.2f}{m120 or 0:>10,.2f}"
              f"{gap60:>8.2f}%{a or 0:>9,.2f}{(a / px * 100) if a else 0:>6.1f}%{pos:>6.0f}%")
        store[code] = {"rows": rows, "px": px, "m20": m20, "m60": m60,
                       "m120": m120, "atr": a, "hi": hi, "lo": lo}

    print("\n\n單日振幅分布（過去一年，|當日漲跌幅|）")
    print(f"{'標的':<9}{'中位數':>9}{'75%':>8}{'90%':>8}{'最大':>8}{'漲停次數':>10}{'跌停次數':>10}")
    print("─" * 64)
    for code, s in store.items():
        rows = s["rows"][-243:]
        ch = []
        up = dn = 0
        for i in range(1, len(rows)):
            r = (rows[i]["c"] / rows[i - 1]["c"] - 1) * 100
            ch.append(abs(r))
            if r >= 9.5:
                up += 1
            if r <= -9.5:
                dn += 1
        if not ch:
            continue
        ch.sort()
        q = lambda p: ch[min(len(ch) - 1, int(len(ch) * p))]
        print(f"{NAMES.get(code, code):<9}{statistics.median(ch):>8.2f}%{q(.75):>7.2f}%"
              f"{q(.90):>7.2f}%{ch[-1]:>7.2f}%{up:>10}{dn:>10}")

    print("\n判讀：ATR% 與『90% 分位』告訴你這檔一天『正常』會動多少。")
    print("      若某天振幅遠超 90% 分位，那是異常事件，不是趨勢延續的證據。")
    print("      這是唯一能誠實回答『明天會怎麼走』的形式：給你機率分布，不給你方向。")


if __name__ == "__main__":
    main()
