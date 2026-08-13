#!/usr/bin/env python3
"""
大錢往哪裡跑 —— 法人資金流的產業別彙總。

用法：
  python scripts/money_flow.py                    # 近 5 個交易日
  python scripts/money_flow.py 20260807 20260806  # 指定日期

做什麼：
  抓 TWSE 逐檔三大法人買賣超（T86），join 官方產業別（t187ap05_L），
  彙總出「哪個族群在被買、哪個在被賣」，以及每個族群裡誰是主力標的。

為什麼看這個：
  台股籌碼透明度全球少見——每天收盤後可以知道每一檔被誰買了多少。
  個股層級的雜訊很大，但**彙總到產業層級**後，資金輪動的方向會清楚得多。

⚠️ 重要限制：
  1. 官方「產業別」是粗分類（光電業、半導體業…），
     抓不到「玻璃基板」「功率元件」「光通訊」這類**跨產業別的次主題**。
     次主題要另外定義成分股清單，見 themes.json。
  2. 自營商買賣超含避險部位（權證對沖），**不是方向性看法**，本工具分開列示。
  3. 單日資料雜訊極大，務必看 5 日以上的累計。
  4. TWSE 的 RWD 端點會限流，本工具已加入延遲與重試。
"""
import json
import os
import sys
import time
import urllib.request
import datetime
import collections

UA = {"User-Agent": "Mozilla/5.0", "Referer": "https://www.twse.com.tw/"}
CACHE = os.path.join(os.path.dirname(__file__), "..", "data", "flow_cache")


def fetch_json(url, tries=4, delay=8):
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers=UA)
            raw = urllib.request.urlopen(req, timeout=40).read()
            return json.loads(raw.decode("utf-8"))
        except Exception as e:
            if k == tries - 1:
                raise
            time.sleep(delay)
    return None


def industries():
    """代號 → (名稱, 產業別)"""
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, "industry.json")
    if os.path.exists(p) and time.time() - os.path.getmtime(p) < 86400:
        return json.load(open(p, encoding="utf-8"))
    d = fetch_json("https://openapi.twse.com.tw/v1/opendata/t187ap05_L")
    m = {r["公司代號"]: [r["公司名稱"], r["產業別"]] for r in d}
    json.dump(m, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    return m


def t86(date):
    os.makedirs(CACHE, exist_ok=True)
    p = os.path.join(CACHE, f"t86_{date}.json")
    if os.path.exists(p):
        return json.load(open(p, encoding="utf-8"))
    j = fetch_json(f"https://www.twse.com.tw/rwd/zh/fund/T86"
                   f"?date={date}&selectType=ALLBUT0999&response=json")
    if j.get("stat") != "OK":
        return None
    json.dump(j, open(p, "w", encoding="utf-8"), ensure_ascii=False)
    time.sleep(3)                      # 尊重限流
    return j


def recent_dates(n=5):
    """往回找 n 個有資料的交易日"""
    out = []
    d = datetime.date.today()
    for _ in range(20):
        if len(out) >= n:
            break
        if d.weekday() < 5:
            out.append(d.strftime("%Y%m%d"))
        d -= datetime.timedelta(days=1)
    return out


def main():
    dates = sys.argv[1:] or recent_dates(5)
    ind = industries()

    # 累計：產業 → [外資, 投信, 自營]
    agg = collections.defaultdict(lambda: [0.0, 0.0, 0.0])
    stock = collections.defaultdict(lambda: [0.0, 0.0])   # 代號 → [外資, 投信]
    used = []

    for dt in dates:
        try:
            j = t86(dt)
        except Exception as e:
            print(f"  {dt} 抓取失敗：{str(e)[:50]}")
            continue
        if not j:
            continue
        used.append(dt)
        for row in j["data"]:
            code = row[0].strip()
            if code not in ind:
                continue
            name, industry = ind[code]
            try:
                f = int(row[4].replace(",", ""))      # 外資買賣超股數
                it = int(row[10].replace(",", ""))    # 投信
                dl = int(row[11].replace(",", ""))    # 自營商合計
            except (ValueError, IndexError):
                continue
            agg[industry][0] += f
            agg[industry][1] += it
            agg[industry][2] += dl
            stock[code][0] += f
            stock[code][1] += it

    if not used:
        print("查無資料（非交易日或端點限流）")
        return

    print(f"\n\033[1m═══ 法人資金流 · 產業別彙總 ═══\033[0m")
    print(f"涵蓋 {len(used)} 個交易日：{', '.join(sorted(used))}")
    print(f"\n單位：張（千股）。外資與投信為方向性指標；"
          f"自營商含避險部位，僅供參考。\n")

    rows = [(k, v[0] / 1000, v[1] / 1000, v[2] / 1000) for k, v in agg.items()]
    rows.sort(key=lambda r: -(r[1] + r[2]))       # 依外資＋投信排序

    print(f"{'產業別':<16}{'外資':>12}{'投信':>10}{'外資+投信':>12}{'自營(含避險)':>13}")
    print("─" * 65)
    for k, f, it, dl in rows[:12]:
        print(f"{k:<16}{f:>+12,.0f}{it:>+10,.0f}{f + it:>+12,.0f}{dl:>+13,.0f}")
    if len(rows) > 20:
        print(f"{'…':<16}")
        for k, f, it, dl in rows[-6:]:
            print(f"{k:<16}{f:>+12,.0f}{it:>+10,.0f}{f + it:>+12,.0f}{dl:>+13,.0f}")

    # 每個熱門產業的主力標的
    print(f"\n\033[1m═══ 買超前 3 大產業的主力標的 ═══\033[0m")
    for k, f, it, dl in rows[:3]:
        members = [(c, stock[c][0] / 1000, stock[c][1] / 1000)
                   for c in stock if ind[c][1] == k]
        members.sort(key=lambda x: -(x[1] + x[2]))
        print(f"\n  【{k}】 外資 {f:+,.0f} 張　投信 {it:+,.0f} 張")
        for c, cf, ci in members[:5]:
            print(f"    {c} {ind[c][0]:<10} 外資 {cf:>+9,.0f}　投信 {ci:>+8,.0f}")

    print(f"\n\033[1m═══ 賣超前 2 大產業 ═══\033[0m")
    for k, f, it, dl in rows[-2:]:
        members = [(c, stock[c][0] / 1000, stock[c][1] / 1000)
                   for c in stock if ind[c][1] == k]
        members.sort(key=lambda x: (x[1] + x[2]))
        print(f"\n  【{k}】 外資 {f:+,.0f} 張　投信 {it:+,.0f} 張")
        for c, cf, ci in members[:4]:
            print(f"    {c} {ind[c][0]:<10} 外資 {cf:>+9,.0f}　投信 {ci:>+8,.0f}")

    theme_flows(stock, ind)

    print(f"\n⚠️ 【待驗】法人買超與後續報酬的關係尚未回測，見 reviews/backlog.md B-02。")
    print("   本工具描述『錢流去哪』，不代表『跟著買會賺』。")


# ── 次主題資金流（成分股來自 docs/themes/theme_baskets.json）─────
def theme_flows(stock, ind):
    """官方產業別抓不到的跨類別次主題，成分股由技術語料萎取。"""
    tp = os.path.join(os.path.dirname(__file__), "..", "docs", "themes", "theme_baskets.json")
    if not os.path.exists(tp):
        return
    baskets = json.load(open(tp, encoding="utf-8"))
    rows = []
    for b in baskets:
        ts = [t for t in b.get("tickers", []) if t in stock]
        if not ts:
            continue
        f = sum(stock[t][0] for t in ts) / 1000
        it = sum(stock[t][1] for t in ts) / 1000
        rows.append((f + it, b["theme"], b["confidence"], ts, f, it))
    if not rows:
        return
    rows.sort(reverse=True)
    print("\n\033[1m═══ 次主題資金流（跨產業別，來自技術語料）═══\033[0m")
    print(f"{'主題':<30}{'外資':>11}{'投信':>10}{'合計':>11}  信心")
    print("─" * 74)
    for tot, theme, conf, ts, f, it in rows:
        print(f"{theme[:28]:<30}{f:>+11,.0f}{it:>+10,.0f}{tot:>+11,.0f}  {conf}")
    print("\n成分股明細：")
    for tot, theme, conf, ts, f, it in rows:
        det = "、".join(f"{t}{ind[t][0]}({stock[t][0]/1000:+,.0f})" for t in ts if t in ind)
        print(f"    {theme[:22]}：{det}")
    print("\n⚠ 成分股由《曲博科技教室》技術語料萎取，非官方分類。")
    print("    講者明確聲明不推薦個股——「他說某公司做某技術」≠「該股會漲」。")


if __name__ == "__main__":
    main()
