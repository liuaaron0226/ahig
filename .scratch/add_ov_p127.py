"""Page-127 overlay addition: harm-adjacent tag for dad77a5b.

dad77a5b — five axes match: 8 male distance runners at a training camp, a
25 km run with the drink given five times DURING the run, a 4% carbohydrate
solution as the base of both arms, an iso-caloric placebo comparator, and a
double-blind crossover design. Excluded on the outcome axis: blood lactate
dehydrogenase (a tissue-damage marker) and blood BCAA concentration are none
of the contract's six.

The tested intervention is BCAA, with carbohydrate matched across both arms —
so this is not evidence about carbohydrate itself. It carries harm-adjacent
because the outcome is a tissue-damage marker measured in a setting that
otherwise sits entirely inside the contract.
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
    dict(candidateId="ahig:candidate:publication:dad77a5b72659e91c787eff9",
         effectiveDecision="exclude", ruling="n+35-1", tag="harm-adjacent",
         note="五軸相符：(1) 族群軸——8 名男性長跑選手（訓練營期間）；(2) 時序與運動型態軸——25 公里"
              "跑步「期間」分 5 次給予；(3) 介入軸——飲料為 4% 碳水溶液（BCAA 臂另含 0.4% BCAA），"
              "碳水於兩臂皆為基底；(4) 對照軸——等熱量安慰劑飲料；(5) 設計軸——雙盲交叉。"
              "結局為血液乳酸脫氫酶（LDH，組織損傷指標）與血中 BCAA 濃度，皆非契約 inScopeOutcomes "
              "六項，依 n+35 第 1 條判 exclude 並掛 harm-adjacent 牌。"
              "**⚠️ 本筆之受測介入實為 BCAA，碳水為兩臂配對之基底（「兩臂完全配對之背景成分」型第 7 筆），"
              "故非碳水本身之效應證據；掛牌係因其結局為組織損傷標記且五軸情境完全落在契約範圍內。"
              "另註：飲料攝取量有記錄（BCAA 臂 591±188 mL、安慰劑臂 516±169 mL），以 4% 碳水濃度換算"
              "25 公里跑步期間約攝取 21-24 g 碳水——若以 2 小時計約 10-12 g/h，落在契約劑量帶下界附近。**"),
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
