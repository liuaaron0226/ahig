"""Add page-113 outcome-adjacent tag per n+35 ruling step (b).

618aa9b9: five axes match (endurance-trained, during-exercise ingestion at 90 min
of a 2 h 60% VO2max run, CHO intervention, water-only + protein comparators,
randomised crossover). Excluded on the outcome axis: plasma lactulose/rhamnose
ratio measures small-intestine PERMEABILITY — a mechanistic biomarker — whereas
the contract lists gi-symptom-incidence and gi-symptom-severity (symptom
outcomes). Verified against the abstract: no in-list outcome present, so (c)
does not apply.

This is the closest case yet to the contract's critical GI outcome; flagged for
priority recovery if permeability is later folded into the GI construct.
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
    dict(candidateId="ahig:candidate:publication:618aa9b9fd540c0213182615",
         effectiveDecision="exclude", ruling="n+35-1", tag="outcome-adjacent",
         context="heat",
         note="耐力訓練受試者、2 小時 60% VO2max 跑步「期間」攝取（雙糖溶液於運動 90 分鐘給予）、對照含 "
              "water-only 與蛋白臂、隨機交叉——族群/時序/介入/對照/設計五軸相符。結局為血漿乳果糖/鼠李糖比值"
              "（HPAEC-PAD）量測之小腸通透性，屬 GI 屏障功能之機轉生物標記；契約 inScopeOutcomes 明列者為 "
              "gi-symptom-incidence（症狀發生率，critical）與 gi-symptom-severity（0-10 自陳嚴重度），"
              "通透性非症狀結局。經核對摘要無任一清單內結局，故不適用 (c)。研究主體另為雙糖試驗量測方法之改良"
              "（血漿 vs 尿液，[methodological]）。**本筆為 outcome-adjacent 名單中與契約 GI critical 結局"
              "最接近者——若協調者決定將腸道通透性納入 GI 結局構念，應優先回收。**"),
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
        print(f"[{r['originalOpinion']} -> {r['effectiveDecision']}] {r['tag']} {r['candidateId'][-16:]}")
    print(f"\n(dry run) would add {len(added)}; overlay {len(doc['entries'])} -> {len(doc['entries'])+len(added)}")
    sys.exit(0)

doc["entries"].extend(added)
doc["producedAtJudgedCount"] = len(judged)
tmp = ovf.with_suffix(".json.tmp")
tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
tmp.replace(ovf)
print(f"WROTE overlay: {len(doc['entries'])} entries (+{len(added)})")
