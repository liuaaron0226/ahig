#!/usr/bin/env bash
# 完整打包 Trading Desk 專案 —— 含 analyst-tracker 的新增部分與 skill
#
# 用法：bash scripts/package.sh [輸出目錄]
#
# 打包原則：
#   1. 絕不打包 .env、金鑰、token —— 改附 .env.example 範本
#   2. 排除可重生的快取（trading-desk/data、__pycache__、.venv、音訊暫存）
#   3. 包含語料庫 tracker.db（13.5MB），那是不可重生的資產
#   4. 附還原說明，讓這包在另一台機器上跑得起來

set -uo pipefail
export PYTHONIOENCODING=utf-8 PYTHONUTF8=1

TD="/c/Users/User/Desktop/claude/trading-desk"
AT="/c/Users/User/Desktop/analyst-tracker"
SK="/c/Users/User/.claude/skills/大璋盤勢"
OUT="${1:-/c/Users/User/Desktop}"
STAMP=$(date +%Y%m%d)
NAME="trading-desk-${STAMP}"
STAGE="${OUT}/${NAME}"

echo "═══ 打包 Trading Desk ${STAMP} ═══"
rm -rf "$STAGE"
mkdir -p "$STAGE"

# ── 1. trading-desk 本體（排除快取）────────────────────────
echo "[1/5] trading-desk 本體"
mkdir -p "$STAGE/trading-desk"
for d in docs briefings reviews scripts; do
  [ -d "$TD/$d" ] && cp -r "$TD/$d" "$STAGE/trading-desk/"
done
cp "$TD"/*.md "$TD"/*.html "$STAGE/trading-desk/" 2>/dev/null
find "$STAGE/trading-desk" -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null
find "$STAGE/trading-desk" -name "*.pyc" -delete 2>/dev/null

# ── 2. analyst-tracker 的新增部分＋語料庫 ──────────────────
echo "[2/5] analyst-tracker 新增部分與語料庫"
mkdir -p "$STAGE/analyst-tracker-additions/scripts" "$STAGE/analyst-tracker-additions/data"
cp "$AT/scripts/captions_only.py" "$STAGE/analyst-tracker-additions/scripts/" 2>/dev/null
cp "$AT/data/tracker.db" "$STAGE/analyst-tracker-additions/data/" 2>/dev/null

# ── 3. skill ────────────────────────────────────────────────
echo "[3/5] 大璋盤勢 skill"
mkdir -p "$STAGE/skills/大璋盤勢"
cp "$SK/SKILL.md" "$STAGE/skills/大璋盤勢/" 2>/dev/null

# ── 4. 金鑰範本（絕不含實際值）──────────────────────────────
echo "[4/5] .env 範本"
cat > "$STAGE/analyst-tracker-additions/.env.example" <<'EOF'
# analyst-tracker 需要的環境變數範本
# 複製成 .env 並填入自己的金鑰。**絕對不要把填好的 .env 加入版控或打包。**

LLM_PROVIDER=gemini          # gemini | anthropic
GEMINI_API_KEY=              # https://aistudio.google.com/apikey
GROQ_API_KEY=                # https://console.groq.com/keys（Whisper 轉錄用）
ANTHROPIC_API_KEY=           # 選用

BACKFILL_DAYS=365
FETCH_DELAY_SEC=2
EOF

# ── 5. 安全稽核 ──────────────────────────────────────────────
echo "[5/5] 安全稽核"
LEAK=$(grep -rIl -E "(AIza[0-9A-Za-z_-]{30,}|gsk_[0-9A-Za-z]{40,}|sk-ant-[0-9A-Za-z_-]{20,})" \
       "$STAGE" 2>/dev/null || true)
if [ -n "$LEAK" ]; then
  echo "  ✗ 偵測到疑似金鑰，中止打包："
  echo "$LEAK"
  exit 1
fi
STRAY=$(find "$STAGE" -name ".env" -not -name ".env.example" 2>/dev/null)
if [ -n "$STRAY" ]; then
  echo "  ✗ 發現 .env 檔，中止："; echo "$STRAY"; exit 1
fi
echo "  ✓ 未偵測到金鑰或 .env"

# ── 統計 ────────────────────────────────────────────────────
echo
echo "═══ 內容 ═══"
du -sh "$STAGE"/* 2>/dev/null
N=$(find "$STAGE" -type f | wc -l)
echo
echo "檔案數：$N"
echo "輸出目錄：$STAGE"
echo
echo "壓縮：cd \"$OUT\" && tar -czf ${NAME}.tar.gz ${NAME}"
