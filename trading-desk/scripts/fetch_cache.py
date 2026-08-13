#!/usr/bin/env python3
"""
把台股月線資料抓下來存成本機快取，之後各種假說檢定都讀這份快取，不重抓。

存下 open/high/low/close/volume/adjclose，讓後續可以測波動度、成交量、
以及「用還原股價 vs 未還原股價」的差異。

用法：python scripts/fetch_cache.py [輸出檔] [--otc]
"""
import json
import sys
import os
import urllib.request
import urllib.error
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
OUT = sys.argv[1] if len(sys.argv) > 1 else "data/monthly_cache.json"


def twse_codes():
    """上市（TWSE）全清單。"""
    req = urllib.request.Request(
        "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL", headers=UA)
    lst = json.load(urllib.request.urlopen(req, timeout=40))
    return sorted({r["Code"] for r in lst
                   if r["Code"].isdigit() and len(r["Code"]) == 4})


def tpex_codes():
    """上櫃（TPEx）全清單，抓不到就回空的。"""
    urls = [
        "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_peratio_analysis",
        "https://www.tpex.org.tw/openapi/v1/tpex_esb_latest_statistics",
    ]
    for u in urls:
        try:
            lst = json.load(urllib.request.urlopen(
                urllib.request.Request(u, headers=UA), timeout=40))
            codes = set()
            for r in lst:
                for k in ("SecuritiesCompanyCode", "Code", "CompanyCode", "stock_id"):
                    v = r.get(k)
                    if v and str(v).isdigit() and len(str(v)) == 4:
                        codes.add(str(v))
            if codes:
                return sorted(codes)
        except Exception as e:
            print(f"  TPEx {u} 失敗: {e}", file=sys.stderr)
    return []


def fetch(args):
    code, suffix = args
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}{suffix}"
           f"?interval=1mo&range=20y&events=div%2Csplit")
    for attempt in range(3):
        try:
            r = json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=30))
            res = r["chart"]["result"][0]
            q = res["indicators"]["quote"][0]
            adj = None
            try:
                adj = res["indicators"]["adjclose"][0]["adjclose"]
            except Exception:
                pass
            ts = res["timestamp"]
            rows = []
            for i, t in enumerate(ts):
                c = q["close"][i]
                if c is None or c <= 0:
                    continue
                rows.append({
                    "d": datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m"),
                    "o": q["open"][i], "h": q["high"][i], "l": q["low"][i],
                    "c": c, "v": q["volume"][i],
                    "a": (adj[i] if adj and adj[i] else c),
                })
            return code + suffix, rows
        except urllib.error.HTTPError as e:
            if e.code in (404, 401):
                return code + suffix, None
            time.sleep(1 + attempt)
        except Exception:
            time.sleep(1 + attempt)
    return code + suffix, None


def main():
    want_otc = "--otc" in sys.argv
    targets = [(c, ".TW") for c in twse_codes()]
    print(f"上市 {len(targets)} 檔")
    if want_otc:
        otc = tpex_codes()
        print(f"上櫃 {len(otc)} 檔")
        targets += [(c, ".TWO") for c in otc]

    data = {}
    done = 0
    with ThreadPoolExecutor(max_workers=10) as ex:
        for key, rows in ex.map(fetch, targets):
            done += 1
            if rows and len(rows) >= 48:
                data[key] = rows
            if done % 100 == 0:
                print(f"  {done}/{len(targets)} → 成功 {len(data)}", flush=True)

    os.makedirs(os.path.dirname(OUT) or ".", exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f)
    lens = sorted(len(v) for v in data.values())
    print(f"\n完成：{len(data)} 檔寫入 {OUT}")
    print(f"月數 中位={lens[len(lens)//2]} 最短={lens[0]} 最長={lens[-1]}")
    span = sorted({r['d'] for v in data.values() for r in v})
    print(f"資料涵蓋 {span[0]} ~ {span[-1]}")


if __name__ == "__main__":
    main()
