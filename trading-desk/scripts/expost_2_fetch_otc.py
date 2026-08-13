#!/usr/bin/env python3
"""補抓上櫃(TPEx)股票，擴大樣本到全台股。"""
import json, urllib.request, datetime, os
from concurrent.futures import ThreadPoolExecutor
UA = {"User-Agent": "Mozilla/5.0"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "otc_cache.json")


def get(code):
    for _ in range(3):
        try:
            u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TWO"
                 f"?interval=1mo&range=6y")
            r = json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA),
                                                 timeout=30))["chart"]["result"][0]
            q = r["indicators"]["quote"][0]
            adj = r["indicators"].get("adjclose", [{}])[0].get("adjclose")
            out = []
            for k, (t, c) in enumerate(zip(r["timestamp"], q["close"])):
                if c is None:
                    continue
                a = adj[k] if adj and adj[k] is not None else c
                out.append([datetime.datetime.utcfromtimestamp(t + 28800).strftime("%Y-%m"),
                            c, a, q["volume"][k] if q.get("volume") else None])
            return code, out
        except Exception:
            pass
    return code, None


meta = {}
for r in json.load(urllib.request.urlopen(urllib.request.Request(
        "https://www.tpex.org.tw/openapi/v1/mopsfin_t187ap05_O", headers=UA), timeout=60)):
    meta[r["公司代號"]] = {"name": r["公司名稱"], "industry": r["產業別"], "shares": 0}
codes = sorted(c for c in meta if c.isdigit() and len(c) == 4)
print("上櫃", len(codes))
data, done = {}, 0
with ThreadPoolExecutor(max_workers=10) as ex:
    for c, s in ex.map(get, codes):
        done += 1
        if s and len(s) >= 24:
            data[c] = s
        if done % 200 == 0:
            print(f"  {done}/{len(codes)} 取得 {len(data)}", flush=True)
print("完成", len(data))
json.dump({"meta": meta, "px": data}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
