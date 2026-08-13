#!/usr/bin/env python3
"""
產業／技術主題抽取 —— 給「解釋型」財經頻道用，不是給「報明牌」頻道用。

用法：
  python scripts/theme_extract.py --channel 5 --limit 5
  python scripts/theme_extract.py --channel 5 --dry-run    # 只看要處理哪些，不呼叫 LLM

## 為什麼需要另一支

analyst-tracker 現有的抽取器（app/llm/prompt.py）開宗明義寫著：
「抽出**可以事後用股價驗證的預測性主張**」，並明確排除「教學性質的舉例」。

那是為《股票大璋》這類報明牌頻道設計的。但《曲博科技教室》講的是
CoWoS、矽光子、HBM、二維材料電晶體——**技術原理與產業結構，不是股價方向**。
把解釋型內容餵進預測型抽取器，只會得到一堆空陣列，白燒 API 額度。

## 這支抽什麼

不抽「會漲會跌」，抽**產業鏈結構**：
  - 技術主題（先進封裝、矽光子、功率元件、玻璃基板…）
  - 產業鏈位置（上游材料／設備／製造／封測／模組）
  - 被點名的公司與其角色（不是推薦，是「他說誰在做這個」）
  - 技術轉折的時間點與門檻
  - 明確的不確定性（他說「還沒量產」「良率未知」的地方）

輸出可以直接餵給 money_flow.py 當次主題成分股清單——
補上官方「產業別」抓不到的跨類別主題。

⚠️ 這是**內容結構化**，不是投資建議。
   「他說某公司在做某技術」不等於「該公司股價會漲」。
"""
import argparse
import json
import os
import re
import sqlite3
import sys
import urllib.request

DB = r"C:\Users\User\Desktop\analyst-tracker\data\tracker.db"
ENV = r"C:\Users\User\Desktop\analyst-tracker\.env"

SCHEMA_HINT = """{
  "themes": [
    {
      "name": "先進封裝",
      "aka": ["CoWoS", "CoPoS", "InFO"],
      "what": "一句話說明這個技術在解決什麼問題",
      "chain_position": "封測",
      "maturity": "量產中 | 試產 | 研發 | 概念",
      "companies": [
        {"name": "台積電", "ticker": "2330", "role": "主導者，CoWoS 產能擁有者"}
      ],
      "timeline": "他提到的時間點，例如「2027 年量產」；沒提就 null",
      "bottleneck": "他指出的瓶頸或門檻",
      "uncertainty": "他明確說不確定的地方",
      "quote": "逐字稿原句，不可改寫"
    }
  ],
  "supply_chain_links": [
    {"from": "上游環節", "to": "下游環節", "relation": "他描述的依賴關係", "quote": "原句"}
  ],
  "notes": "這支影片的主軸與可信度備註"
}"""

INSTRUCTIONS = f"""你是產業研究助理。以下是一支**技術解說型**財經影片的逐字稿。

## 抽什麼

抽出**產業鏈與技術結構**，不要抽股價預測（這位講者通常不報明牌）。

1. **themes**：影片講到的技術／產業主題。每個主題要標出它在產業鏈的位置、成熟度、
   被點名的公司與角色、時間點、瓶頸、以及講者明說的不確定性。
2. **supply_chain_links**：他描述的上下游依賴關係。
3. **notes**：影片主軸，以及你對內容可信度的備註。

## 硬規則

- `quote` 必須是逐字稿裡**真實出現的原句**，不可改寫或潤飾。這是查證依據。
- 公司名稱若逐字稿有誤植（語音辨識），請依上下文還原並補上台股代號（格式：代號分開放在 ticker 欄）。
  已知常見誤植：「立基店」→力積電、「偽創」→緯創、「太子協業」→台積電。
  外國公司或未上市公司，ticker 填 null。
- **不要推論股價方向**。role 欄寫「他說這家公司在做什麼」，不要寫「所以會漲」。
- 講者沒說的不要補。timeline / bottleneck / uncertainty 查無就填 null。
- 若這支影片沒有實質產業內容（例如純訪談寒暄、生技與半導體無關），
  themes 回空陣列，並在 notes 說明。**不要為了湊數而編造。**

## 輸出

只輸出 JSON，不要其他文字：

{SCHEMA_HINT}
"""


def load_key():
    if not os.path.exists(ENV):
        return None
    for line in open(ENV, encoding="utf-8"):
        if line.startswith("GEMINI_API_KEY="):
            return line.split("=", 1)[1].strip()
    return None


def call_gemini(key, text, title, date_):
    prompt = f"{INSTRUCTIONS}\n\n影片標題：{title}\n發布日期：{date_}\n\n逐字稿：\n{text[:120000]}"
    url = ("https://generativelanguage.googleapis.com/v1beta/models/"
           f"gemini-2.0-flash:generateContent?key={key}")
    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "responseMimeType": "application/json"},
    }).encode()
    req = urllib.request.Request(url, data=body,
                                 headers={"Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=180))
    raw = r["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(re.sub(r"^```json|```$", "", raw.strip(), flags=re.M))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--channel", type=int, default=5)
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--out", default="data/themes.json")
    a = ap.parse_args()

    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    rows = con.execute(
        """SELECT id,title,published_at,transcript_text FROM videos
           WHERE channel_id=? AND transcript_text IS NOT NULL AND LENGTH(transcript_text)>1500
           ORDER BY published_at DESC LIMIT ?""", (a.channel, a.limit)).fetchall()
    con.close()

    if not rows:
        print("查無已轉錄的影片。請先跑 analyst-tracker 的 process 產生逐字稿。")
        return

    print(f"找到 {len(rows)} 支已轉錄影片：")
    for r in rows:
        print(f"  {r['published_at'][:10]}  {len(r['transcript_text']):>6,} 字  {r['title'][:50]}")
    if a.dry_run:
        return

    key = load_key()
    if not key:
        print("\n找不到 GEMINI_API_KEY")
        sys.exit(1)

    out = []
    for r in rows:
        print(f"\n處理：{r['title'][:50]}")
        try:
            res = call_gemini(key, r["transcript_text"], r["title"], r["published_at"][:10])
            res["video_id"] = r["id"]
            res["title"] = r["title"]
            res["published_at"] = r["published_at"][:10]
            out.append(res)
            th = res.get("themes", [])
            print(f"  ✓ {len(th)} 個主題")
            for t in th:
                cos = "、".join(c.get("name", "") for c in (t.get("companies") or [])[:5])
                print(f"    · {t.get('name')} [{t.get('chain_position')}/{t.get('maturity')}] {cos}")
        except Exception as e:
            print(f"  ✗ 失敗：{str(e)[:90]}")

    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    json.dump(out, open(a.out, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"\n✓ 已寫入 {a.out}（{len(out)} 支）")

    # 彙整：主題 → 公司清單，可直接餵給 money_flow.py
    agg = {}
    for v in out:
        for t in v.get("themes", []):
            k = t.get("name")
            if not k:
                continue
            agg.setdefault(k, {"aka": set(), "companies": {}})
            agg[k]["aka"].update(t.get("aka") or [])
            for c in t.get("companies") or []:
                if c.get("ticker"):
                    agg[k]["companies"][c["ticker"]] = c.get("name")
    if agg:
        print("\n═══ 主題 → 台股成分（可餵給 money_flow.py）═══")
        for k, v in agg.items():
            cs = "、".join(f"{t} {n}" for t, n in v["companies"].items())
            aka = f"（{'/'.join(sorted(v['aka']))}）" if v["aka"] else ""
            print(f"  {k}{aka}：{cs or '（未點名台股）'}")


if __name__ == "__main__":
    main()
