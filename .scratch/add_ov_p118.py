"""Page-118 overlay additions: two [context:*] stratifiers.

0b13175a — no-abstract dissertation whose TITLE points to inclusion
  ("The effect of carbohydrate feeding on exercise performance and capacity in
  thermo neutral and hot"). Judged unclear per the page-114 asymmetry.
  Carries [context:heat]; it is the only heat-context case where the
  environment is the study's own contrast axis, so its W4c value is highest.

5eec2720 — 214 km winter ultraendurance case study at -13 to -1 degC.
  Excluded on design (n=1) and intervention (self-selected intake) axes.
  Carries [context:cold], the FIRST cold entry in the [context:*] family.

Both entries leave the decision unchanged; they exist only to carry the
stratifier, mirroring the 56aab1fb / ab9f58c4 / a289453d / b5163608 precedent.
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
    dict(candidateId="ahig:candidate:publication:0b13175a886219c4d7e9ee4e",
         effectiveDecision="unclear", ruling="n+35-2", tag="context-only",
         context="heat",
         note="決策不變（unclear）。無摘要學位論文，標題〈The effect of carbohydrate feeding on exercise "
              "performance and capacity in thermo neutral and hot〉正面載明介入軸（碳水餵食）與結局軸"
              "（exercise performance and capacity，涵蓋 tt-completion-time 與 time-to-exhaustion 兩構念）"
              "相符，族群／對照／設計三軸無資訊，依 page 114 所立無摘要不對稱性（標題載入局證據不得反推）"
              "判 unclear。本覆蓋層項目僅為承載 [context:heat] 分層標籤——**本筆為 heat 群中唯一以環境"
              "（thermo neutral vs hot）為受測對比軸者，對 W4c 分層設計價值最高。**"),
    dict(candidateId="ahig:candidate:publication:5eec272094d35398fff3645b",
         effectiveDecision="exclude", ruling="n+35-2", tag="context-only",
         context="cold",
         note="決策不變（exclude）。2025 年 Arrowhead Ultra 冠軍自行車選手個案研究（214 公里雪地賽道、"
              "17.9 小時、-13 至 -1°C）。依設計軸（n=1 case study）與介入軸（無受控碳水介入，攝取為自選記錄）"
              "排除。本覆蓋層項目僅為承載 [context:cold] 分層標籤——**cold 為 [context:*] 族之首例**，"
              "與既有 heat／altitude／hypoxia 並列為第四類環境情境。另建議納入「菁英耐力賽事實際攝取量分佈」"
              "校準素材：雙標水法量測總能量消耗 63.9 MJ（15,273 kcal，達基礎代謝率 9.6 倍）而攝取僅 "
              "33.2 MJ（7,941 kcal，達消耗之 52%），為該素材之極端赤字端點。"),
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
