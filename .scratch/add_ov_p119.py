"""Page-119 overlay addition: harm-adjacent tag for 886f1576.

886f1576 — five axes match: 14 endurance athletes (VO2peak 67+-6 mL/min/kg,
the most clearly specified training status seen so far), three bouts of 4 h
cycling at 70% of individual anaerobic threshold, 6% or 12% CHO beverages
(a genuine dose gradient) versus placebo. Excluded on the outcome axis:
NT-proBNP, leucocyte subpopulations, CRP, IL-6 and cortisol are cardiac
wall-stress and immune-response outcomes, none of the contract's six.

Critically, this paper is a SECONDARY analysis of stored serum from a parent
study whose design falls entirely inside the contract. The parent study is now
the top entry on the lead-chasing list.
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
    dict(candidateId="ahig:candidate:publication:886f157618735754e117e247",
         effectiveDecision="exclude", ruling="n+35-1", tag="harm-adjacent",
         note="五軸相符：(1) 族群——14 名健康耐力運動員，VO2peak 67±6 mL/min/kg，為迄今訓練程度最明確者之一；"
              "(2) 時序與運動型態——三回合 4 小時自行車（個體無氧閾 70% 固定功率）「期間」給予；"
              "(3) 介入——6% 或 12% 碳水飲料，為真實劑量分級；(4) 對照——安慰劑飲料；"
              "(5) 受試者內多條件比較。結局為 NT-proBNP、白血球亞群、CRP、IL-6 與皮質醇，"
              "屬心臟壁應力標記與運動誘發免疫反應，非契約 inScopeOutcomes 六項，"
              "依 n+35 第 1 條判 exclude 並掛 harm-adjacent 牌。"
              "**⚠️ 最重要：本筆自陳為次級分析（Stored serum samples ... who had been examined previously "
              "for exercise-induced immune reactions and their dependence on carbohydrate supplementation），"
              "其母研究之設計（耐力運動員 × 4 小時自行車期間 × 6%/12% 碳水劑量分級 vs 安慰劑）五軸全數"
              "落入契約範圍。建議列為線索型文獻溯源清單最高優先——母研究若含契約結局，即為直接可納入之證據。**"),
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
        print(f"[{r['originalOpinion']} -> {r['effectiveDecision']}] {r['tag']} "
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
