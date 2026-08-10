#!/usr/bin/env bash
# 每日市場資料抓取 — 一次拉完所有硬數據
# 用法：bash scripts/fetch_daily.sh [YYYYMMDD]   （不帶參數 = 最近交易日）
#
# 所有端點於 2026-08-10 實測通過。
# 原則：只抓數據、不做判讀。判讀是人的工作。

set -uo pipefail

# Windows/Git-Bash 下 Python 預設用 cp950 輸出，中文會變亂碼。強制 UTF-8。
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1

DATE="${1:-}"
UA="Mozilla/5.0"
OUT="${OUT_DIR:-./data/$(date +%Y%m%d)}"
if ! mkdir -p "$OUT" 2>/dev/null; then
  OUT="./data/$(date +%Y%m%d)"
  mkdir -p "$OUT" || { echo "無法建立輸出目錄，改用 /dev/null"; OUT="/dev/null"; }
fi

PY=$(command -v python3 || command -v python) || { echo "找不到 python"; exit 1; }

hr() { printf '\n\033[1;36m─── %s ───\033[0m\n' "$1"; }
warn() { printf '\033[1;33m! %s\033[0m\n' "$1"; }

# ── 台股：指數與成交 ────────────────────────────────────────
hr "台股大盤（近 5 日）"
curl -s --max-time 30 "https://openapi.twse.com.tw/v1/exchangeReport/FMTQIK" \
  | tee "$OUT/taiex_5d.json" \
  | "$PY" -c "
import json,sys
try:
    for r in json.load(sys.stdin):
        d=r['Date']; v=int(r['TradeValue'])/1e8; c=float(r['Change'])
        print(f\"{d}  TAIEX {r['TAIEX']:>10}  {c:+9.2f}  成交 {v:,.0f} 億\")
except Exception as e: print('parse failed:', e)
" 2>/dev/null || warn "TAIEX 解析失敗，原始檔在 $OUT/taiex_5d.json"

hr "各指數（含中型100 — 看市場廣度）"
curl -s --max-time 30 "https://openapi.twse.com.tw/v1/exchangeReport/MI_INDEX" \
  | tee "$OUT/indices.json" \
  | "$PY" -c "
import json,sys
want=['發行量加權股價指數','臺灣中型100指數','臺灣50指數','臺灣資訊科技指數','寶島股價指數']
try:
    for r in json.load(sys.stdin):
        if r['指數'] in want:
            sign='-' if r['漲跌']=='-' else '+'
            pct=r['漲跌百分比'].lstrip('+-')
            print(f\"{r['指數']:<18} {r['收盤指數']:>11}  {sign}{r['漲跌點數']:>9}  {sign}{pct:>5}%\")
except Exception as e: print('parse failed:', e)
" 2>/dev/null || warn "指數解析失敗"

# ── 台股：籌碼 ──────────────────────────────────────────────
if [ -n "$DATE" ]; then
  hr "三大法人買賣金額（$DATE）"
  curl -s --max-time 30 -H "User-Agent: $UA" \
    "https://www.twse.com.tw/rwd/zh/fund/BFI82U?dayDate=${DATE}&type=day&response=json" \
    | tee "$OUT/institutional.json" \
    | "$PY" -c "
import json,sys
try:
    j=json.load(sys.stdin)
    if j.get('stat')!='OK': print('查無資料（非交易日？）'); sys.exit()
    print(j['title'])
    for row in j['data']:
        net=int(row[3].replace(',',''))/1e8
        print(f\"  {row[0]:<28} {net:+10.2f} 億\")
except Exception as e: print('parse failed:', e)
" 2>/dev/null || warn "法人資料解析失敗"

  hr "外資台指期未平倉（$DATE）— 注意：空單≠看空，見 daily-dashboard.md §4.2"
  D="${DATE:0:4}%2F${DATE:4:2}%2F${DATE:6:2}"
  curl -s --max-time 30 -H "User-Agent: $UA" -X POST \
    "https://www.taifex.com.tw/cht/3/futContractsDateDown" \
    -d "down_type=1&queryStartDate=${D}&queryEndDate=${D}&commodity_id=TXF" \
    | iconv -f BIG5 -t UTF-8 2>/dev/null \
    | tee "$OUT/futures.csv" \
    | awk -F, 'NR>1 && $2=="臺股期貨" {printf "  %-12s 淨未平倉 %+10s 口\n", $3, $14}'
else
  warn "未指定日期，跳過籌碼資料。用法：bash $0 20260807"
fi

# ── 美國：利率與波動 ────────────────────────────────────────
hr "美債殖利率與期限利差"
for s in DGS10:10年期 DGS2:2年期 T10Y2Y:10Y-2Y利差 BAMLH0A0HYM2:高收債利差 VIXCLS:VIX; do
  id="${s%%:*}"; name="${s##*:}"
  val=$(curl -s --max-time 20 "https://fred.stlouisfed.org/graph/fredgraph.csv?id=${id}" \
        | grep -v '^\s*$' | tail -1)
  printf "  %-14s %s\n" "$name" "$val"
done

hr "新台幣匯率"
echo "  → https://www.cbc.gov.tw/tw/lp-645-1.html （央行銀行間收盤匯率，每日 16:00-17:00 更新）"

# ── 全球市場 + ADR 溢價率 ───────────────────────────────────
# 帶入台積電收盤價與匯率即可自動算 ADR 溢價率
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -f "$SCRIPT_DIR/fetch_global.py" ]; then
  "$PY" "$SCRIPT_DIR/fetch_global.py" ${TSMC_CLOSE:-} ${TWD_RATE:-}
else
  warn "找不到 fetch_global.py，跳過全球市場"
fi

# ── 待辦提醒 ────────────────────────────────────────────────
hr "手動確認項目（無穩定 API）"
cat <<'EOF'
  □ 公開資訊觀測站重訊 https://mops.twse.com.tw/
  □ 月營收（每月 1–10 日密集公布期，10 日為截止日）
  □ 本週美國經濟數據行事曆 https://www.bls.gov/schedule/news_release/
  □ CME FedWatch 升降息機率
  □ 融資融券 / 借券賣出餘額
  □ 台指期夜盤走勢（15:00–次日 05:00）
EOF

printf '\n\033[1;32m✓ 原始資料已存至 %s\033[0m\n' "$OUT"
