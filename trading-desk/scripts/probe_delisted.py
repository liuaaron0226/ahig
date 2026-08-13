#!/usr/bin/env python3
"""
測「存活者偏誤」到底有多大。

做法：Yahoo 上掃描「不在今日上市清單裡」的四位數代號。
如果某代號有歷史資料、但資料在 2025 年之前就停了，
代表它曾經上市、後來下市（或被併購）——這些正是我的樣本裡缺的股票。

先用已知下市個股驗證 Yahoo 到底留不留下市資料。
"""
import json
import sys
import urllib.request
import urllib.error
import datetime
import time
from concurrent.futures import ThreadPoolExecutor

UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
MODE = sys.argv[1] if len(sys.argv) > 1 else "known"

KNOWN_DELISTED = {
    "3662": "樂陞科技（2017 假收購案下市）",
    "2384": "勝華科技（2016 觸控面板破產下市）",
    "5387": "茂德科技（2013 DRAM 下市）",
    "3452": "益通光能（太陽能，下市）",
    "6702": "興航／復興航空（2016 解散）",
    "2311": "日月光（2018 換股為 3711）",
    "2328": "廣宇（併入鴻海集團）",
    "1439": "中和紡織",
    "2506": "太設",
    "9945": "潤泰新（對照組：仍上市）",
}


def probe(code):
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{code}.TW"
           f"?interval=1mo&range=20y")
    for attempt in range(2):
        try:
            r = json.load(urllib.request.urlopen(
                urllib.request.Request(url, headers=UA), timeout=25))
            res = r["chart"]["result"][0]
            ts = res["timestamp"]
            q = res["indicators"]["quote"][0]
            good = [(t, c) for t, c in zip(ts, q["close"]) if c]
            if not good:
                return code, None
            first = datetime.datetime.utcfromtimestamp(good[0][0])
            last = datetime.datetime.utcfromtimestamp(good[-1][0])
            return code, {"first": first.strftime("%Y-%m"),
                          "last": last.strftime("%Y-%m"),
                          "n": len(good),
                          "last_px": good[-1][1]}
        except urllib.error.HTTPError as e:
            if e.code in (404, 401):
                return code, None
            time.sleep(0.5)
        except Exception:
            time.sleep(0.5)
    return code, None


def main():
    if MODE == "known":
        print("── 已知下市個股在 Yahoo 上還查得到嗎？ ──\n")
        for code, name in KNOWN_DELISTED.items():
            _, r = probe(code)
            if r:
                print(f"{code} {name:<28} 資料 {r['first']} ~ {r['last']}"
                      f"（{r['n']} 個月，末價 {r['last_px']:.2f}）")
            else:
                print(f"{code} {name:<28} ✗ Yahoo 查無資料")
        return

    # 全面掃描：不在今日清單裡的代號
    lst = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL",
        headers=UA), timeout=40))
    live = {r["Code"] for r in lst if r["Code"].isdigit() and len(r["Code"]) == 4}
    candidates = [str(c) for c in range(1101, 9999) if str(c) not in live]
    print(f"掃描 {len(candidates)} 個非現存代號…")

    found = {}
    done = 0
    with ThreadPoolExecutor(max_workers=12) as ex:
        for code, r in ex.map(probe, candidates):
            done += 1
            if r and r["n"] >= 12:
                found[code] = r
            if done % 500 == 0:
                print(f"  {done}/{len(candidates)} → 找到 {len(found)}", flush=True)

    dead = {c: r for c, r in found.items() if r["last"] < "2025-01"}
    print(f"\n有資料的非現存代號：{len(found)}")
    print(f"其中資料停在 2025 年以前（＝已下市）：{len(dead)}")
    with open("data/delisted_probe.json", "w", encoding="utf-8") as f:
        json.dump(dead, f, ensure_ascii=False, indent=1)

    byyear = {}
    for c, r in dead.items():
        y = r["last"][:4]
        byyear[y] = byyear.get(y, 0) + 1
    print("\n下市年份分布：")
    for y in sorted(byyear):
        print(f"  {y}: {byyear[y]}")
    print("\n寫入 data/delisted_probe.json")


if __name__ == "__main__":
    main()
