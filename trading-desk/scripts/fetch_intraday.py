#!/usr/bin/env python3
"""
台股即時盤中報價（TWSE MIS）
用法：python scripts/fetch_intraday.py [代號 代號 ...]
      不帶參數 = 大盤 + 櫃買 + 主要權值股

為什麼需要這支：MIS 的欄位有幾個坑，直接取 z 會在漲跌停或無成交時拿到空值，
取 b（委買）又會踩到第一個佔位的 0.0000。這裡把解析邏輯集中處理一次。

實測於 2026-08-10。
"""
import json
import sys
import urllib.request

MIS = "https://mis.twse.com.tw/stock/api/getStockInfo.jsp"
HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://mis.twse.com.tw/stock/index.jsp",
}

DEFAULT = ["tse_t00.tw", "otc_o00.tw", "tse_2330.tw", "tse_2317.tw",
           "tse_2454.tw", "tse_2308.tw", "tse_2891.tw"]


def _first_positive(field):
    """MIS 的 b/a 欄位是 '價1_價2_..._'，第一個常是佔位的 0.0000。"""
    if not field or field == "-":
        return None
    for part in str(field).split("_"):
        try:
            v = float(part)
            if v > 0:
                return v
        except ValueError:
            continue
    return None


def resolve_price(m):
    """回傳 (價格, 來源說明)。找不到有效價格回傳 (None, 原因)。"""
    z = m.get("z", "-")
    if z not in ("-", "", None):
        try:
            v = float(z)
            if v > 0:
                return v, "成交"
        except ValueError:
            pass

    # 漲跌停鎖死時無成交價，用委買/委賣最佳價
    for key, label in (("b", "委買"), ("a", "委賣")):
        v = _first_positive(m.get(key))
        if v:
            return v, label

    # 仍取不到 → 若最高價已達漲停價，視為鎖漲停
    try:
        h, u, w = float(m.get("h", 0)), float(m.get("u", 0)), float(m.get("w", 0))
        if h and u and abs(h - u) < 1e-6:
            return h, "鎖漲停"
        lo = float(m.get("l", 0))
        if lo and w and abs(lo - w) < 1e-6:
            return lo, "鎖跌停"
    except (ValueError, TypeError):
        pass

    try:
        o = float(m.get("o", 0))
        if o > 0:
            return o, "開盤價"
    except (ValueError, TypeError):
        pass

    return None, "無有效報價"


def main(codes):
    chans = []
    for c in codes:
        if "_" in c:
            chans.append(c)
        elif c in ("t00", "大盤"):
            chans.append("tse_t00.tw")
        elif c in ("o00", "櫃買"):
            chans.append("otc_o00.tw")
        else:
            chans.append(f"tse_{c}.tw")

    url = f"{MIS}?ex_ch={'|'.join(chans)}&json=1&delay=0"
    req = urllib.request.Request(url, headers=HEADERS)
    data = json.load(urllib.request.urlopen(req, timeout=25))

    arr = data.get("msgArray", [])
    if not arr:
        print("查無資料（非交易時段，或代號有誤）")
        return

    print(f"{'名稱':<12}{'現價':>11}{'漲跌':>10}{'幅度':>9}  {'最高':>11}{'最低':>11}  來源   時間")
    print("─" * 88)
    for m in arr:
        name = m.get("n", "?")
        try:
            y = float(m.get("y", 0) or 0)
        except ValueError:
            y = 0
        px, src = resolve_price(m)
        t = m.get("t", "")
        if px is None or y <= 0:
            print(f"{name:<12}{'—':>10}  {src}  {t}")
            continue
        chg = px - y
        pct = chg / y * 100
        hi, lo = m.get("h", "-"), m.get("l", "-")
        try:
            hi = f"{float(hi):,.2f}"
            lo = f"{float(lo):,.2f}"
        except (ValueError, TypeError):
            pass
        flag = ""
        if src in ("鎖漲停", "鎖跌停"):
            flag = f" ⚠{src}"
        print(f"{name:<12}{px:>11,.2f}{chg:>+10.2f}{pct:>+8.2f}%  "
              f"{hi:>11}{lo:>11}  {src:<6} {t}{flag}")

    print()
    print("提醒：盤中數據不是收盤價。13:30 收盤後請改用 TWSE 正式收盤資料。")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)
