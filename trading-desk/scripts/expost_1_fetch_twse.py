#!/usr/bin/env python3
"""抓取全上市股票月線 + 產業別 + 股本，存成 cache 供事後歸因分析。"""
import json, urllib.request, datetime, os, sys
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0"}
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "expost_cache.json")


def jget(url, timeout=60):
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout))


def meta():
    ind = {}
    for r in jget("https://openapi.twse.com.tw/v1/opendata/t187ap05_L"):
        ind[r["公司代號"]] = {"name": r["公司名稱"], "industry": r["產業別"]}
    for r in jget("https://openapi.twse.com.tw/v1/opendata/t187ap03_L"):
        c = r["公司代號"]
        d = ind.setdefault(c, {"name": r.get("公司簡稱", ""), "industry": "?"})
        try:
            d["shares"] = float(r.get("已發行普通股數或TDR原股發行股數") or 0)
        except Exception:
            d["shares"] = 0.0
        d.setdefault("name", r.get("公司簡稱", ""))
    return ind


def get(code):
    for attempt in range(3):
        try:
            u = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW"
                 f"?interval=1mo&range=10y&events=div")
            r = jget(u, 30)["chart"]["result"][0]
            q = r["indicators"]["quote"][0]
            adj = None
            if "adjclose" in r["indicators"]:
                adj = r["indicators"]["adjclose"][0]["adjclose"]
            out = []
            for k, (t, c) in enumerate(zip(r["timestamp"], q["close"])):
                if c is None:
                    continue
                a = adj[k] if adj and adj[k] is not None else c
                v = q["volume"][k] if q.get("volume") else None
                d = datetime.datetime.utcfromtimestamp(t + 28800)
                out.append([d.strftime("%Y-%m"), c, a, v])
            return code, out
        except Exception as e:
            if attempt == 2:
                return code, None
    return code, None


def main():
    ind = meta()
    codes = sorted(c for c in ind if c.isdigit() and len(c) == 4)
    print(f"上市公司清單 {len(codes)} 檔", flush=True)
    data = {}
    done = 0
    with ThreadPoolExecutor(max_workers=10) as ex:
        for code, s in ex.map(get, codes):
            done += 1
            if s and len(s) >= 24:
                data[code] = s
            if done % 100 == 0:
                print(f"  {done}/{len(codes)}  取得 {len(data)}", flush=True)
    print(f"完成：{len(data)} 檔有月線資料")
    json.dump({"meta": ind, "px": data}, open(OUT, "w", encoding="utf-8"), ensure_ascii=False)
    print("cache ->", OUT)


if __name__ == "__main__":
    main()
