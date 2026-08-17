"""Page-126 overlay addition: outcome-adjacent tag for f33ad3f3.

f33ad3f3 — five axes match: 9 male runners, 2 h treadmill run at 65% VO2max
with the drink consumed DURING the run, a carbohydrate arm alongside a placebo
arm (three-condition within-subject design). Excluded on the outcome axis:
insulin, glucagon, catecholamines, growth hormone, testosterone, cortisol and
plasma substrates are none of the contract's six.

Notable within the outcome-adjacent list: this is one of the few entries whose
CHO arm and placebo arm coexist with a fully matching timing axis, so it is a
priority recall if the outcome construct is ever widened to substrate/hormone
responses.
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
    dict(candidateId="ahig:candidate:publication:f33ad3f3bad838123da6fcfb",
         effectiveDecision="exclude", ruling="n+35-1", tag="outcome-adjacent",
         note="五軸相符：(1) 族群軸——9 名男性跑者；(2) 時序與運動型態軸——2 小時 65% VO2max 跑步機"
              "跑步「期間」攝取；(3) 介入軸——碳水飲料（CHO 臂）為三臂之一；(4) 對照軸——安慰劑（PLA）臂；"
              "(5) 設計軸——三條件受試者內比較。結局為胰島素、升糖素、腎上腺素、正腎上腺素、生長激素、"
              "睪固酮、皮質醇及血漿葡萄糖／乳酸／游離脂肪酸／胺基酸，皆非契約 inScopeOutcomes 六項"
              "——屬受質與荷爾蒙反應，無表現、GI 症狀或外源碳水氧化結局。依 n+35 第 1 條判 exclude "
              "並掛 outcome-adjacent 牌。"
              "**⚠️ 本筆為 outcome-adjacent 名單中少數「碳水臂與安慰劑臂並存且時序完全相符」者"
              "——若協調者日後擴充結局構念至受質代謝，本筆應優先回收。另註：MILK 臂為非脂乳品，"
              "構成蛋白-碳水複方對比。**"),
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
