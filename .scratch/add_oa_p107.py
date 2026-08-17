"""Add page-107 outcome-adjacent tag to the overlay per n+35 ruling step (b).

30b13e9b was judged exclude at page 107 with reason citing the outcome axis.
Ruling n+35-1 requires: (a) exclude, (b) tag [outcome-adjacent] and record it in
the tagged list with a one-line outcome note, (c) advance only if some other
outcome IS in the list — verified not the case here (all outcomes out of list).

Note: effectiveDecision equals the original opinion (exclude); this entry exists
to carry the tag, matching the 'context-only' precedent added under n+35-2.
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
    dict(candidateId="ahig:candidate:publication:30b13e9bd973181dfd417811",
         effectiveDecision="exclude", ruling="n+35-1", tag="outcome-adjacent",
         note="19 名健康男性 60-65% 最大有氧能力騎乘至力竭，運動中攝取葡萄糖 40 或 80 g/h（兩劑量皆落在契約 "
              "10-150 g/h，分屬 moderate 與 high band），對照為未攝取（no-intervention，allowlist 內）——"
              "介入/時序/對照三軸相符且劑量精確。結局為低血糖發生率與血漿腎上腺素反應；力竭時間雖有報告但為"
              "附帶陰性結果（摘要明載低血糖組與正常血糖組無顯著差異、預防低血糖亦未持續延後力竭），非受控主結局。"
              "經核對摘要，無任一契約清單內結局。族群另未載訓練狀態客觀指標。**若擴充結局軸或納入低血糖為 harm "
              "結局，本筆之 40/80 g/h 劑量對比應優先回收。**"),
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
