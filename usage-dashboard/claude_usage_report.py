#!/usr/bin/env python3
"""Claude Code 本地用量儀表板產生器（校準基準：Claude Pro 方案）。

背景限制（請先讀）：
Anthropic 沒有公開 API 讓外部程式查詢 Pro 方案的 5 小時 / 每週用量上限
百分比 —— 那個數字只能透過 Claude Code 互動指令 `/usage` 或 Anthropic
Console 網頁查看。Anthropic Help Center 公開的參考值是「Pro 方案 5 小時
視窗約 45 則提示」，但實際可用則數會隨訊息長度、附加檔案、對話長度、
使用的模型而變動 —— 官方原文即註明這只是估計值。

本工具以這個 ~45 則/5小時 的公開參考值為基準，計算「本地估算剩餘空間」：
  - 掃描本機 ~/.claude/projects/**/*.jsonl，統計過去 5 小時內送出的
    assistant 回覆則數，除以 45 得出估算使用率。
  - 這是「用你自己在這台電腦上的 Claude Code 用量」去對照公開參考值，
    不是官方即時查詢——如果你也用 claude.ai 網頁版或 Cowork，那邊的用量
    不會被算進來（但仍會計入同一個官方額度）。
  - 每週上限沒有可靠的公開則數基準，因此週用量僅顯示本地趨勢，不做%估算；
    要看準確的週用量，仍需手動記錄 `/usage` 顯示的官方數字。

用法：
  python claude_usage_report.py                      重新產生 dashboard.html 並開啟
  python claude_usage_report.py --log 42              記一筆「5小時視窗」官方 42%
  python claude_usage_report.py --log 60 --type week   記一筆「本週」官方 60%
  python claude_usage_report.py --log 42 --note "剛開一個大重構"
"""
import argparse
import json
import os
import webbrowser
from datetime import datetime, timedelta, timezone
from pathlib import Path

CLAUDE_HOME = Path(os.environ.get("USERPROFILE") or os.environ.get("HOME") or "~").expanduser() / ".claude"
PROJECTS_DIR = CLAUDE_HOME / "projects"
MANUAL_LOG_DIR = CLAUDE_HOME / "usage_dashboard"
MANUAL_LOG_FILE = MANUAL_LOG_DIR / "manual_log.jsonl"
OUTPUT_HTML = Path(__file__).parent / "dashboard.html"

# Anthropic Help Center 公開參考值（截至 2026-07）：Pro 方案 5 小時視窗約 45 則提示。
# 官方明講這是估計值，會隨訊息長度/附件/模型變動——這裡拿它當估算分母，不是保證值。
PRO_5H_MESSAGE_REFERENCE = 45


def iter_session_files():
    if not PROJECTS_DIR.exists():
        return
    for jsonl_path in PROJECTS_DIR.rglob("*.jsonl"):
        yield jsonl_path


LOCAL_COMMAND_PREFIXES = (
    "<command-name>", "<local-command-stdout>",
    "<local-command-stderr>", "<local-command-caveat>",
)


def _parse_ts(ts):
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except (ValueError, AttributeError):
        return None


def parse_usage_events():
    """回傳 (assistant_events, prompt_timestamps)。

    assistant_events：每一則 assistant 回覆的 (dt, model, total_tokens) —— 用來算
    token 用量趨勢，這部分是真的算力消耗，用 assistant 條目算沒有問題。

    prompt_timestamps：你自己「送出」的提示時間點（排除工具結果、本地指令回顯）。
    這才是 Anthropic 公開參考值「~45 則/5小時」對應的單位——一個 Claude Code
    任務背後可能觸發幾十次工具呼叫／assistant 回應，但那些不是「45 則」裡的
    「則」，用 assistant 條目數去對 45 會嚴重高估用量（agentic 工具迴圈越多，
    誤差越大），所以兩者要分開算。
    """
    assistant_events = []
    prompt_timestamps = []
    for path in iter_session_files():
        try:
            with path.open(encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    etype = entry.get("type")
                    ts = entry.get("timestamp")
                    dt = _parse_ts(ts) if ts else None

                    if etype == "assistant" and dt:
                        msg = entry.get("message") or {}
                        usage = msg.get("usage")
                        if not usage:
                            continue
                        total = (
                            (usage.get("input_tokens") or 0)
                            + (usage.get("output_tokens") or 0)
                            + (usage.get("cache_creation_input_tokens") or 0)
                            + (usage.get("cache_read_input_tokens") or 0)
                        )
                        assistant_events.append({
                            "dt": dt,
                            "model": msg.get("model") or "unknown",
                            "total_tokens": total,
                        })
                    elif etype == "user" and dt:
                        content = (entry.get("message") or {}).get("content")
                        if isinstance(content, str) and not content.lstrip().startswith(LOCAL_COMMAND_PREFIXES):
                            prompt_timestamps.append(dt)
        except OSError:
            continue
    assistant_events.sort(key=lambda e: e["dt"])
    prompt_timestamps.sort()
    return assistant_events, prompt_timestamps


def aggregate(assistant_events, prompt_timestamps):
    now = datetime.now().astimezone()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    five_hr_ago = now - timedelta(hours=5)
    week_ago = now - timedelta(days=7)

    # Token 用量（真的算力消耗，assistant 條目算沒問題）
    today_tokens = 0
    rolling5h_tokens = 0
    week_tokens = 0
    per_day_tokens = {}  # date -> tokens
    per_model = {}

    for e in assistant_events:
        dt, tok = e["dt"], e["total_tokens"]
        day_key = dt.strftime("%Y-%m-%d")
        per_day_tokens[day_key] = per_day_tokens.get(day_key, 0) + tok

        if dt >= today_start:
            today_tokens += tok
        if dt >= five_hr_ago:
            rolling5h_tokens += tok
        if dt >= week_ago:
            week_tokens += tok
            m = per_model.setdefault(e["model"], {"tokens": 0, "msgs": 0})
            m["tokens"] += tok
            m["msgs"] += 1

    # 提示（prompt）數——這才是對應 Anthropic「~45 則/5小時」的單位
    today_prompts = rolling5h_prompts = week_prompts = 0
    per_day_prompts = {}
    for dt in prompt_timestamps:
        day_key = dt.strftime("%Y-%m-%d")
        per_day_prompts[day_key] = per_day_prompts.get(day_key, 0) + 1
        if dt >= today_start:
            today_prompts += 1
        if dt >= five_hr_ago:
            rolling5h_prompts += 1
        if dt >= week_ago:
            week_prompts += 1

    last8 = []
    for i in range(7, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        last8.append({
            "date": day,
            "tokens": per_day_tokens.get(day, 0),
            "prompts": per_day_prompts.get(day, 0),
        })

    pro_5h_pct = min(100, round(rolling5h_prompts / PRO_5H_MESSAGE_REFERENCE * 100))
    pro_5h_remaining_pct = max(0, 100 - pro_5h_pct)

    return {
        "generated_at": now.isoformat(),
        "today": {"tokens": today_tokens, "prompts": today_prompts},
        "rolling5h": {"tokens": rolling5h_tokens, "prompts": rolling5h_prompts},
        "week": {"tokens": week_tokens, "prompts": week_prompts},
        "last8_days": last8,
        "per_model_7d": per_model,
        "pro_5h_pct": pro_5h_pct,
        "pro_5h_remaining_pct": pro_5h_remaining_pct,
    }


def load_manual_log():
    if not MANUAL_LOG_FILE.exists():
        return []
    entries = []
    with MANUAL_LOG_FILE.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    entries.sort(key=lambda e: e["timestamp"])
    return entries


def append_manual_log(percent: float, log_type: str, note: str):
    MANUAL_LOG_DIR.mkdir(parents=True, exist_ok=True)
    entry = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "percent": percent,
        "type": log_type,
        "note": note or "",
    }
    with MANUAL_LOG_FILE.open("a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    print(f"已記錄：{entry['timestamp']}｜{log_type}｜{percent}%｜{note or '(無備註)'}")


def render_html(agg, manual_entries):
    session_entries = [e for e in manual_entries if e.get("type") == "session"]
    week_entries = [e for e in manual_entries if e.get("type") == "week"]
    latest_session = session_entries[-1] if session_entries else None
    latest_week = week_entries[-1] if week_entries else None

    max_day_tokens = max((d["tokens"] for d in agg["last8_days"]), default=0) or 1
    bars_html = ""
    for d in agg["last8_days"]:
        pct = round(d["tokens"] / max_day_tokens * 100)
        label = d["date"][5:]  # MM-DD
        bars_html += f"""
        <div class="bar-col">
          <div class="bar-track"><div class="bar-fill" style="height:{pct}%"></div></div>
          <div class="bar-label">{label}</div>
          <div class="bar-value">{d['tokens']:,}</div>
        </div>"""

    def fmt_entry(e):
        if not e:
            return '<span class="muted">尚未記錄</span>'
        dt = datetime.fromisoformat(e["timestamp"])
        return f'{e["percent"]}%　<span class="muted">({dt.strftime("%m-%d %H:%M")}{"　" + e["note"] if e.get("note") else ""})</span>'

    history_rows = ""
    for e in reversed(manual_entries[-20:]):
        dt = datetime.fromisoformat(e["timestamp"])
        type_label = "5小時視窗" if e["type"] == "session" else "本週"
        history_rows += f"""
        <tr><td>{dt.strftime("%Y-%m-%d %H:%M")}</td><td>{type_label}</td><td>{e['percent']}%</td><td>{e.get('note','')}</td></tr>"""

    model_rows = ""
    for model, m in sorted(agg["per_model_7d"].items(), key=lambda kv: -kv[1]["tokens"]):
        model_rows += f"<tr><td>{model}</td><td>{m['tokens']:,}</td><td>{m['msgs']}</td></tr>"

    generated = datetime.fromisoformat(agg["generated_at"]).strftime("%Y-%m-%d %H:%M:%S")
    remaining = agg["pro_5h_remaining_pct"]
    used = agg["pro_5h_pct"]
    ring_color = "var(--ok)" if remaining >= 40 else ("var(--warn2)" if remaining >= 15 else "var(--danger)")
    circumference = 2 * 3.14159265 * 70
    dash = circumference * used / 100

    html = f"""<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta http-equiv="refresh" content="300">
<title>Claude 用量儀表板</title>
<style>
  :root {{
    --bg: #f7f6f3; --card: #ffffff; --text: #1f1f1f; --muted: #767267;
    --accent: #c96a43; --track: #ece8e0; --border: #e5e1d8;
    --ok:#3f8f5f; --warn2:#c98a2c; --danger:#c9483f;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{ --bg:#1c1a17; --card:#26231f; --text:#f1ede4; --muted:#a39c8c; --accent:#e08a5f; --track:#38342c; --border:#3a362e;
             --ok:#6bc78e; --warn2:#e0ac52; --danger:#e07a6f; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ margin:0; background:var(--bg); color:var(--text); font-family:-apple-system,"Segoe UI",system-ui,sans-serif; padding:32px 20px; }}
  .wrap {{ max-width:920px; margin:0 auto; }}
  h1 {{ font-size:1.4rem; margin:0 0 4px; }}
  .sub {{ color:var(--muted); font-size:0.85rem; margin-bottom:28px; }}
  .hero {{ background:var(--card); border:1px solid var(--border); border-radius:18px; padding:28px; margin-bottom:20px;
           display:flex; align-items:center; gap:32px; flex-wrap:wrap; }}
  .ring-label {{ font-size:0.78rem; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; margin-bottom:14px; }}
  .ring-pct {{ font-size:2.6rem; font-weight:800; }}
  .ring-sub {{ font-size:0.8rem; color:var(--muted); margin-top:4px; }}
  .hero-side {{ flex:1; min-width:220px; }}
  .hero-side .row {{ display:flex; justify-content:space-between; padding:6px 0; border-bottom:1px solid var(--border); font-size:0.88rem; }}
  .hero-side .row:last-child {{ border-bottom:none; }}
  .grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:16px; margin-bottom:24px; }}
  .card {{ background:var(--card); border:1px solid var(--border); border-radius:14px; padding:20px; }}
  .card h2 {{ font-size:0.8rem; text-transform:uppercase; letter-spacing:.04em; color:var(--muted); margin:0 0 10px; font-weight:600; }}
  .big {{ font-size:1.9rem; font-weight:700; }}
  .official .big {{ color:var(--accent); }}
  .muted {{ color:var(--muted); font-size:0.82rem; }}
  .bars {{ display:flex; align-items:flex-end; gap:10px; height:160px; padding-top:10px; }}
  .bar-col {{ flex:1; display:flex; flex-direction:column; align-items:center; height:100%; justify-content:flex-end; }}
  .bar-track {{ width:100%; max-width:36px; height:120px; background:var(--track); border-radius:6px; display:flex; align-items:flex-end; overflow:hidden; }}
  .bar-fill {{ width:100%; background:var(--accent); border-radius:6px 6px 0 0; min-height:2px; }}
  .bar-label {{ font-size:0.7rem; color:var(--muted); margin-top:6px; }}
  .bar-value {{ font-size:0.65rem; color:var(--muted); }}
  table {{ width:100%; border-collapse:collapse; font-size:0.85rem; }}
  th,td {{ text-align:left; padding:7px 6px; border-bottom:1px solid var(--border); }}
  th {{ color:var(--muted); font-weight:600; font-size:0.75rem; text-transform:uppercase; }}
  .howto {{ background:var(--card); border:1px dashed var(--border); border-radius:14px; padding:18px 20px; font-size:0.85rem; line-height:1.7; }}
  code {{ background:var(--track); padding:2px 6px; border-radius:5px; font-size:0.85em; }}
  .warn {{ font-size:0.78rem; color:var(--muted); margin-top:6px; }}
  .banner {{ background:var(--card); border:1px solid var(--warn2); border-radius:12px; padding:12px 16px; font-size:0.82rem; margin-bottom:20px; }}
</style>
</head>
<body>
<div class="wrap">
  <h1>Claude 用量儀表板</h1>
  <div class="sub">更新時間 {generated}　·　校準基準：Claude Pro 方案</div>

  <div class="banner">⏰ 提醒：Anthropic 目前的每週用量上限暫時提高 50%，這個加成到 <strong>2026-07-13</strong> 就會結束——屆時週用量會變緊，本工具目前沒有可靠的公開數字能估算週上限，請以手動記錄的 <code>/usage</code> 為準。</div>

  <div class="hero">
    <div>
      <div class="ring-label">5 小時視窗 · 估算剩餘空間</div>
      <svg width="170" height="170" viewBox="0 0 170 170">
        <circle cx="85" cy="85" r="70" fill="none" stroke="var(--track)" stroke-width="16"/>
        <circle cx="85" cy="85" r="70" fill="none" stroke="{ring_color}" stroke-width="16"
                stroke-dasharray="{dash:.1f} {circumference:.1f}" stroke-linecap="round"
                transform="rotate(-90 85 85)"/>
        <text x="85" y="80" text-anchor="middle" font-size="34" font-weight="800" fill="var(--text)">{remaining}%</text>
        <text x="85" y="102" text-anchor="middle" font-size="12" fill="var(--muted)">還剩</text>
      </svg>
    </div>
    <div class="hero-side">
      <div class="row"><span>過去 5 小時已送出提示</span><strong>{agg['rolling5h']['prompts']} 則</strong></div>
      <div class="row"><span>Pro 方案 5 小時參考值</span><strong>約 {PRO_5H_MESSAGE_REFERENCE} 則</strong></div>
      <div class="row"><span>估算已使用</span><strong>{used}%</strong></div>
      <div class="row"><span>官方回報（你手動記的 /usage）</span><strong>{fmt_entry(latest_session)}</strong></div>
      <div class="muted" style="margin-top:10px">估算值只算這台電腦的 Claude Code 用量；若你也用 claude.ai 網頁版或 Cowork，實際剩餘空間會比這裡顯示的更少。訊息長度、附件、模型都會讓實際額度跟 45 則這個參考值有落差。</div>
    </div>
  </div>

  <div class="grid">
    <div class="card official">
      <h2>官方回報｜本週</h2>
      <div class="big">{fmt_entry(latest_week)}</div>
      <div class="warn">週上限沒有公開則數基準，僅能靠手動記錄</div>
    </div>
    <div class="card">
      <h2>本地估算｜今天</h2>
      <div class="big">{agg['today']['prompts']} <span class="muted" style="font-size:1rem">則</span></div>
      <div class="muted">{agg['today']['tokens']:,} tokens（含快取讀寫）</div>
    </div>
    <div class="card">
      <h2>本地估算｜本週累計</h2>
      <div class="big">{agg['week']['prompts']} <span class="muted" style="font-size:1rem">則</span></div>
      <div class="muted">{agg['week']['tokens']:,} tokens</div>
    </div>
  </div>

  <div class="card" style="margin-bottom:24px">
    <h2>本地活躍度趨勢（過去 8 天，訊息數對應的 token 量）</h2>
    <div class="bars">{bars_html}
    </div>
  </div>

  <div class="grid">
    <div class="card">
      <h2>過去 7 天各模型用量（本地估算）</h2>
      <table><tr><th>模型</th><th>Tokens</th><th>訊息數</th></tr>{model_rows or '<tr><td colspan="3" class="muted">近 7 天無紀錄</td></tr>'}</table>
    </div>
    <div class="card">
      <h2>官方數字記錄歷史</h2>
      <table><tr><th>時間</th><th>類型</th><th>%</th><th>備註</th></tr>{history_rows or '<tr><td colspan="4" class="muted">尚未記錄，見下方說明</td></tr>'}</table>
    </div>
  </div>

  <div class="howto">
    <strong>想校準得更準？記錄官方數字：</strong><br>
    1. 在 Claude Code 互動 session 裡輸入 <code>/usage</code>，記下顯示的百分比。<br>
    2. 回到終端機執行：<code>python claude_usage_report.py --log 42</code>（5 小時視窗）或
    <code>python claude_usage_report.py --log 60 --type week</code>（本週）。<br>
    <span class="warn">中央圓環的「估算剩餘空間」是拿 Anthropic 公開的「Pro 方案約 45 則/5小時」參考值換算，不是官方即時查詢——官方原文本身也註明這只是估計值。</span>
  </div>
</div>
</body>
</html>"""
    OUTPUT_HTML.write_text(html, encoding="utf-8")
    print(f"儀表板已產生：{OUTPUT_HTML}")
    webbrowser.open(OUTPUT_HTML.resolve().as_uri())


def main():
    parser = argparse.ArgumentParser(description="Claude Code 本地用量儀表板")
    parser.add_argument("--log", type=float, help="記錄一筆你在 /usage 看到的官方百分比")
    parser.add_argument("--type", choices=["session", "week"], default="session", help="--log 對應的類型（預設 session＝5小時視窗）")
    parser.add_argument("--note", default="", help="這筆記錄的備註")
    args = parser.parse_args()

    if args.log is not None:
        append_manual_log(args.log, args.type, args.note)

    assistant_events, prompt_timestamps = parse_usage_events()
    agg = aggregate(assistant_events, prompt_timestamps)
    manual = load_manual_log()
    render_html(agg, manual)


if __name__ == "__main__":
    main()
