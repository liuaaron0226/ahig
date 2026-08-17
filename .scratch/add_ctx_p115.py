"""Add page-115 [context:heat] stratifier tag per the n+35 ruling.

ab9f58c4: judged unclear (four axes match — CHO-electrolyte beverage ingested
during 3 h of cycling at 60% VO2max, distilled-water comparator, within-subject
crossover; population training status and in-list outcomes not reported).
The decision is UNCHANGED — this overlay entry exists only to carry the
[context:heat] stratifier (Tdb 31.5 degC, 22.3% RH) for W4c stratified design,
mirroring the 56aab1fb context-only precedent.
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
    dict(candidateId="ahig:candidate:publication:ab9f58c4dbb696bc50d5a830",
         effectiveDecision="unclear", ruling="n+35-2", tag="context-only",
         context="heat",
         note="決策不變（unclear）。本筆四軸相符：碳水-電解質飲料（4.85% polycose ＋2.65% 果糖）於 3 小時 "
              "60% VO2max 自行車運動「期間」自由飲用、對照為蒸餾水（water-only，allowlist 第二項）、"
              "受試者內兩次試驗（交叉型態）。族群（7 名男性無訓練程度描述）與結局（已載者皆為體溫調節與"
              "體液指標，非契約 6 項）兩軸資訊不足，依 fail-closed 判 unclear。本覆蓋層項目僅為承載 "
              "[context:heat] 分層標籤（Tdb 31.5°C、RH 22.3%）供 W4c 分層設計使用，比照 56aab1fb "
              "之 context-only 前例。另註：ad libitum 自由飲用設計使攝取量無法於摘要換算為 g/h，"
              "「自由飲用設計是否符合契約劑量帶界定」已提請協調者裁示。"),
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
              f"[context:{r['context']}] {r['candidateId'][-16:]}")
    print(f"\n(dry run) would add {len(added)}; overlay {len(doc['entries'])} -> "
          f"{len(doc['entries'])+len(added)}")
    sys.exit(0)

doc["entries"].extend(added)
doc["producedAtJudgedCount"] = len(judged)
tmp = ovf.with_suffix(".json.tmp")
tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
tmp.replace(ovf)
print(f"WROTE overlay: {len(doc['entries'])} entries (+{len(added)})")
