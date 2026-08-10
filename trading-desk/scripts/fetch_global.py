#!/usr/bin/env python3
"""
全球市場資料 + 台積電 ADR 溢價率
用法：python scripts/fetch_global.py [台積電台股收盤價] [美元兌台幣匯率]

資料源：Yahoo Finance chart API（免費、免金鑰，2026-08-10 實測通過）
只抓數據，不做判讀。
"""
import json
import sys
import urllib.request
import datetime

UA = {"User-Agent": "Mozilla/5.0"}


def quote(sym, label):
    """回傳 (最新收盤, 前一交易日收盤, 日期字串)"""
    url = (f"https://query1.finance.yahoo.com/v8/finance/chart/{sym}"
           f"?interval=1d&range=10d")
    try:
        req = urllib.request.Request(url, headers=UA)
        r = json.load(urllib.request.urlopen(req, timeout=20))["chart"]["result"][0]
        ts = r["timestamp"]
        closes = r["indicators"]["quote"][0]["close"]
        pairs = [(t, c) for t, c in zip(ts, closes) if c is not None]
        if len(pairs) < 2:
            print(f"  {label:<12} 資料不足")
            return None
        (t1, c1), (_, c0) = pairs[-1], pairs[-2]
        d = datetime.datetime.utcfromtimestamp(t1).strftime("%m/%d")
        chg, pct = c1 - c0, (c1 - c0) / c0 * 100
        print(f"  {label:<12} {c1:>11,.2f}  {chg:+9.2f} ({pct:+6.2f}%)  [{d}]")
        return c1
    except Exception as e:
        print(f"  {label:<12} 抓取失敗: {str(e)[:60]}")
        return None


def hr(t):
    print(f"\n\033[1;36m─── {t} ───\033[0m")


hr("亞洲（與台股同時段，可即時對照）")
quote("%5EN225", "日經225")
kospi = quote("%5EKS11", "韓國KOSPI")
quote("%5EHSI", "恆生")

hr("美國（隔夜，決定台股開盤）")
quote("%5EGSPC", "S&P 500")
quote("%5EIXIC", "Nasdaq")
quote("%5EDJI", "道瓊")
sox = quote("%5ESOX", "費半 SOX")

hr("風險與匯率")
quote("%5EVIX", "VIX")
quote("DX-Y.NYB", "美元指數")
quote("%5ETNX", "美債10Y")

hr("台積電 ADR 溢價率")
tsm = quote("TSM", "台積電ADR")

tw_close = float(sys.argv[1]) if len(sys.argv) > 1 else None
fx = float(sys.argv[2]) if len(sys.argv) > 2 else None

if tsm and tw_close and fx:
    adr_twd = tsm * fx / 5          # 1 ADR = 5 股普通股
    prem = adr_twd / tw_close - 1
    print()
    print(f"  ADR 折合台股價  {adr_twd:>10,.1f} 元  ({tsm:.2f} USD × {fx} ÷ 5)")
    print(f"  台積電台股收盤  {tw_close:>10,.1f} 元")
    print(f"  \033[1m溢價率        {prem*100:>+10.2f} %\033[0m")
    print()
    print("  ⚠ 【待驗 B-06】溢價率的「水準」是否有預測力尚未驗證。")
    print("    我的推論是「變化」比「水準」更有訊息量，但這也還沒回測。")
else:
    print()
    print("  → 要算溢價率請帶入參數：python scripts/fetch_global.py <台積電收盤> <匯率>")
    print("    匯率查 https://www.cbc.gov.tw/tw/lp-645-1.html")

hr("交叉檢查提醒")
print("""  韓國 KOSPI 是台股最直接的對照組（同為半導體出口導向）。
  兩者背離時要問為什麼：是產業因素（記憶體 vs 邏輯製程）、
  匯率因素、還是個別市場的資金流？背離本身就是資訊。""")
