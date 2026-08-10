#!/usr/bin/env bash
# 個股硬數據抓取 — 供 docs/analysis-framework.md 三層分析使用
# 用法：bash scripts/fetch_stock.sh 2330 [YYYYMMDD]
#
# 端點於 2026-08-10 實測通過。只抓數據，判讀由人負責。

set -uo pipefail
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1

STOCK="${1:?用法: bash scripts/fetch_stock.sh <股票代號> [YYYYMMDD]}"
DATE="${2:-$(date +%Y%m%d)}"
UA="Mozilla/5.0"
PY=$(command -v python3 || command -v python) || { echo "找不到 python"; exit 1; }

hr() { printf '\n\033[1;36m─── %s ───\033[0m\n' "$1"; }

# ── 估值 ────────────────────────────────────────────────────
hr "估值（本益比 / 殖利率 / 淨值比）"
curl -s --max-time 30 "https://openapi.twse.com.tw/v1/exchangeReport/BWIBBU_ALL" \
  | "$PY" -c "
import json,sys
s='$STOCK'
for r in json.load(sys.stdin):
    if r.get('Code')==s:
        print(f\"  {r['Name']} ({s})  資料日 {r['Date']}\")
        print(f\"  本益比 P/E   {r['PEratio']:>8}\")
        print(f\"  股價淨值比    {r['PBratio']:>8}\")
        print(f\"  現金殖利率    {r['DividendYield']:>8} %\")
        print()
        print('  ⚠ 循環股(記憶體/鋼鐵/航運)獲利高峰時 P/E 最低，該指標會誤導。見 analysis-framework.md §3.1')
        break
else: print(f'  查無 {s} 的估值資料（可能是上櫃股或 ETF）')
" 2>/dev/null || echo "  估值查詢失敗"

# ── 月營收 ★ 台股中期分析核心 ─────────────────────────────
hr "月營收（中期動能核心指標）"
curl -s --max-time 30 "https://openapi.twse.com.tw/v1/opendata/t187ap05_L" \
  | "$PY" -c "
import json,sys
s='$STOCK'
for r in json.load(sys.stdin):
    if r.get('公司代號')==s:
        cur=int(r['營業收入-當月營收'])/1e5      # 千元 -> 億元
        prev=int(r['營業收入-上月營收'])/1e5
        lastyr=int(r['營業收入-去年當月營收'])/1e5
        yoy=float(r['營業收入-去年同月增減(%)'])
        mom=float(r['營業收入-上月比較增減(%)'])
        cum=float(r['累計營業收入-前期比較增減(%)'])
        print(f\"  {r['公司名稱']} ({s})  {r['產業別']}\")
        print(f\"  資料年月 {r['資料年月']}   出表 {r['出表日期']}\")
        print()
        print(f\"  當月營收    {cur:>10,.1f} 億\")
        print(f\"  上月營收    {prev:>10,.1f} 億\")
        print(f\"  去年同月    {lastyr:>10,.1f} 億\")
        print(f\"  年增率 YoY  {yoy:>+10.2f} %   <- 最重要\")
        print(f\"  月增率 MoM  {mom:>+10.2f} %   (受季節性干擾)\")
        print(f\"  累計年增    {cum:>+10.2f} %\")
        if r.get('備註','').strip(): print(f\"  公司說明：{r['備註']}\")
        print()
        print('  ★ 關鍵：股價反映的常是 YoY 的「二階變化」(加速/減速)，不是 YoY 的水準。')
        print('    要判斷這點，需比對前幾個月的 YoY —— 本腳本只給單月，請到 MOPS 查歷史序列。')
        break
else: print(f'  查無 {s} 的月營收（上櫃股請改查 TPEx，ETF/金融股格式不同）')
" 2>/dev/null || echo "  月營收查詢失敗"

# ── 近期股價 ────────────────────────────────────────────────
hr "近月日線（量價結構）"
curl -s --max-time 30 -H "User-Agent: $UA" \
  "https://www.twse.com.tw/rwd/zh/afterTrading/STOCK_DAY?date=${DATE}&stockNo=${STOCK}&response=json" \
  | "$PY" -c "
import json,sys
try:
    j=json.load(sys.stdin)
    if j.get('stat')!='OK': print('  查無資料:',j.get('stat')); sys.exit()
    rows=j['data'][-12:]
    print(f\"  {'日期':<12}{'收盤':>10}{'漲跌':>9}{'成交股數':>14}{'成交筆數':>10}\")
    for r in rows:
        vol=int(r[1].replace(',',''))/1000
        print(f\"  {r[0]:<12}{r[6]:>10}{r[7]:>9}{vol:>13,.0f}張{r[8]:>10}\")
except Exception as e: print('  解析失敗:',e)
" 2>/dev/null || echo "  股價查詢失敗"

# ── 個股籌碼 ────────────────────────────────────────────────
hr "三大法人買賣超（$DATE）"
curl -s --max-time 30 -H "User-Agent: $UA" \
  "https://www.twse.com.tw/rwd/zh/fund/T86?date=${DATE}&selectType=ALLBUT0999&response=json" \
  | "$PY" -c "
import json,sys
s='$STOCK'
try:
    j=json.load(sys.stdin)
    if j.get('stat')!='OK': print('  查無資料（非交易日？）'); sys.exit()
    for row in j['data']:
        if row[0].strip()==s:
            f=int(row[4].replace(',',''))/1000
            it=int(row[10].replace(',',''))/1000
            dl=int(row[11].replace(',',''))/1000
            tot=int(row[18].replace(',',''))/1000
            print(f\"  {row[1].strip()}\")
            print(f\"  外資      {f:>+12,.0f} 張\")
            print(f\"  投信      {it:>+12,.0f} 張\")
            print(f\"  自營商    {dl:>+12,.0f} 張   <- 含避險部位，非方向性看法\")
            print(f\"  三大法人  {tot:>+12,.0f} 張\")
            print()
            print('  ★ 看連續性，不看單日。單日金額幾乎沒有預測力。')
            break
    else: print(f'  {s} 當日無法人買賣超紀錄')
except Exception as e: print('  解析失敗:',e)
" 2>/dev/null || echo "  籌碼查詢失敗"

hr "需手動補的項目"
cat <<EOF
  □ 月營收 YoY 歷史序列（判斷加速/減速）→ https://mops.twse.com.tw/
  □ 毛利率/營益率趨勢、現金流 → MOPS 財報
  □ 法說會展望、重大訊息 → MOPS
  □ 融資融券、借券賣出餘額
  □ 所屬類股指數的相對強弱
  □ 若為 ADR 標的，查 ADR 溢價率
EOF
printf '\n\033[1;33m提醒：本腳本只產出數據。分析請照 docs/analysis-framework.md 三層架構，\n並依 CONTEXT.md 標註證據等級。不給目標價、不給買賣建議。\033[0m\n'
