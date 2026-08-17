"""Page-125 overlay addition: harm-adjacent + [context:hypoxia] for 196a38b4.

196a38b4 — the strongest case yet for auditing the safety lane's outcome scope.
Five axes match: 8% maltodextrin at 200 mL/20 min (a contract CHO form on a
timed in-exercise schedule), during exercise at 70% VO2peak to exhaustion,
placebo arm, randomised and double-blind. Excluded only on the outcome axis:
salivary IgA, salivary flow rate and SaO2 are none of the contract's six.

This is the FOURTH member of the immune-outcome group (099900f6, 14027aad,
fcfe3a96) and the only one where carbohydrate itself is the tested
intervention — in the other three CHO was background or a diet composition.
Environment is simulated 4500 m hypoxia, so it also carries [context:hypoxia],
taking that group from 1 to 2.
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
    dict(candidateId="ahig:candidate:publication:196a38b4d4b8991f3d8745c9",
         effectiveDecision="exclude", ruling="n+35-1", tag="harm-adjacent",
         context="hypoxia",
         note="五軸近乎相符：(1) 介入軸——8% 麥芽糊精 200 mL/20 min，為契約 CHO 型態且屬定時補給；"
              "(2) 時序軸——運動「期間」給予；(3) 運動型態軸——70% VO2peak 至力竭；"
              "(4) 對照軸——安慰劑臂；(5) 設計軸——隨機雙盲。結局為唾液免疫（IgA、唾液流速）"
              "與血氧飽和度，皆非契約 inScopeOutcomes 六項，依 n+35 第 1 條判 exclude 並掛 "
              "harm-adjacent 牌。族群軸資訊不足（15 名志願者無訓練程度描述）。"
              "**⚠️ 本筆為免疫結局群第 4 筆（另三筆為 099900f6 唾液 IgA 與賽後 URTI、"
              "14027aad 唾液 IgA、fcfe3a96 NK 細胞活性），且為四筆中唯一以碳水本身為受測介入者"
              "——前三筆之碳水或為兩臂共同背景、或為飲食組成。此使 safety lane 結局範圍覆核之"
              "必要性達到最高：一項以契約介入為受測變項、於契約時序給予、有安慰劑對照之隨機雙盲"
              "試驗，其結局完全落在兩 lane 之外。** 另標 [context:hypoxia]（模擬海拔 4,500 m，"
              "該群 1→2 筆）。"),
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
