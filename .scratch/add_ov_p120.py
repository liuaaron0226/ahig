"""Page-120 overlay additions.

14027aad — five axes match (28 ultramarathon runners, during-race, placebo arm,
  randomised double-blind). Excluded because the tested intervention is vitamin C
  with CHO supplied identically to both arms, and the outcomes are oxidative
  markers plus salivary IgA. Tagged harm-adjacent: it is the second five-axes
  case whose only failing axis is an immune outcome (cf. 099900f6 on page 116).
  Also records the most precisely quantified real-race intake rate seen so far:
  60 g/h beverage + 50-75 g/h gels = 110-135 g/h.

8bfaddda — no-abstract dissertation whose title names carbohydrate AND fluid
  INGESTION (not rinsing), during exercise, with performance among the outcomes,
  in hot conditions. Judged unclear per the page-114 asymmetry; carries
  [context:heat], taking that group to five.
"""
import json, os, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
P = Path(os.environ["AHIG_PRIVATE_ROOT"]) / "search-runs" / "b11-exogenous-cho-endurance" \
    / "b11-full-run" / "standard-full-screen-pass-1"
ovf = P / "post-ruling-reclassification.json"

doc = json.loads(ovf.read_text(encoding="utf-8"))
judged = {e["candidateId"]: e for e in
          json.loads((P / "judgements.json").read_text(encoding="utf-8"))["entries"]}
existing = {e["candidateId"] for e in doc["entries"]}

NEW = [
    dict(candidateId="ahig:candidate:publication:14027aadda3ad3fd56b628ea",
         effectiveDecision="exclude", ruling="n+35-1", tag="harm-adjacent",
         note="五軸相符：28 名超級馬拉松跑者（平均 69 km／9.8 h／75% HRmax）、賽事「期間」給予、"
              "雙盲安慰劑對照、隨機雙盲設計。介入軸違反——受測介入為維生素 C（1,500 mg/day × 7 日前置"
              "＋賽中 150 mg/L），碳水為兩臂共同之背景補給（「兩臂完全配對之背景成分」型第 3 筆）。"
              "結局為血漿抗壞血酸、脂質過氧化氫、F2-異前列腺素與唾液 IgA，非契約六項，依 n+35 第 1 條"
              "判 exclude 並掛 harm-adjacent 牌。"
              "**⚠️ 兩項高價值註記：(1) 賽中碳水攝取率為 1 L/h × 60 g/L ＝ 60 g/h（飲料）＋每小時 2-3 包 "
              "25 g 膠（50-75 g/h），合計 110-135 g/h，落在契約劑量帶高端（high 至 very-high doseBand），"
              "為迄今最明確量化之真實賽事攝取率；(2) 唾液 IgA 結局與 page 116 `099900f6` 同構念，"
              "該免疫結局群累計 2 筆且皆為五軸相符僅結局出局者，強化 safety lane 結局範圍覆核之必要性。**"),
    dict(candidateId="ahig:candidate:publication:8bfaddda88d20ead5f704d90",
         effectiveDecision="unclear", ruling="n+35-2", tag="context-only",
         context="heat",
         note="決策不變（unclear）。無摘要學位論文，標題〈The influence of carbohydrate and fluid "
              "ingestion on thermoregulation and performance during prolonged, intermittent, "
              "high-intensity exercise in hot environmental conditions〉四項要素皆正面指向入局："
              "介入軸（碳水與液體「攝取」ingestion，非漱口）、時序軸（during ... exercise）、"
              "結局軸部分相符（performance 屬 tt-completion-time／time-to-exhaustion 構念）、"
              "運動型態為長時間間歇高強度（該型態是否屬契約耐力運動仍為既有待裁示項，本筆為該議題之"
              "首見無摘要案例）。族群／對照／設計三軸無資訊，依 page 114 不對稱性判 unclear。"
              "本覆蓋層項目僅為承載 [context:heat] 分層標籤（該群 4→5 筆）。"
              "列為學位論文全文期優先取得之第二順位，僅次於 page 118 之 3aed2932。"),
]

added = []
for rec in NEW:
    cid = rec["candidateId"]
    if cid in existing:
        print(f"SKIP already in overlay: {cid[-16:]}")
        continue
    if cid not in judged:
        print(f"ERROR not judged: {cid[-16:]}")
        sys.exit(1)
    rec["originalOpinion"] = judged[cid]["opinion"]
    added.append(rec)

if "--write" not in sys.argv:
    for r in added:
        ctx = f" [context:{r['context']}]" if r.get("context") else ""
        print(f"[{r['originalOpinion']} -> {r['effectiveDecision']}] {r['tag']}{ctx} "
              f"{r['candidateId'][-16:]}")
    print(f"\n(dry run) would add {len(added)}; overlay {len(doc['entries'])} -> "
          f"{len(doc['entries'])+len(added)}")
    sys.exit(0)

doc["entries"].extend(added)
doc["producedAtJudgedCount"] = len(judged)
tmp = ovf.with_suffix(".json.tmp")
tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
tmp.replace(ovf)
print(f"WROTE overlay: {len(doc['entries'])} entries (+{len(added)})")
