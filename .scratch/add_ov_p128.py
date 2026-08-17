"""Page-128 overlay addition: harm-adjacent tag for 4f8472d2.

4f8472d2 — the strongest single case in the immune-outcome group. SIX axes
match: 10 triathletes serving as their own controls, 2.5 h of intense running
and cycling at ~75% VO2max, a 6% carbohydrate beverage given DURING exercise,
a placebo beverage as comparator, a within-subject crossover design, and —
unlike most of the group — carbohydrate itself is the tested variable (the
C-vs-P contrast is primary; exercise mode is secondary).

Excluded on the outcome axis only: lymphocyte proliferation, natural killer
cell cytotoxicity, IL-1beta production and hormonal responses are none of the
contract's six.

Immune-outcome group now 5, of which 3 have carbohydrate as the tested
intervention (099900f6, 196a38b4, this). This one has the closest population
and exercise-mode match of the three.
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
    dict(candidateId="ahig:candidate:publication:4f8472d29e0844e0cafe9ec5",
         effectiveDecision="exclude", ruling="n+35-1", tag="harm-adjacent",
         note="**六軸相符——為免疫結局群中軸線相符度最高者。**(1) 族群軸——10 名鐵人三項選手（自為對照）；"
              "(2) 時序與運動型態軸——2.5 小時約 75% VO2max 之高強度跑步與自行車「期間」攝取；"
              "(3) 介入軸——6% 碳水飲料，為契約 CHO 型態且屬運動期間補給；(4) 對照軸——安慰劑飲料；"
              "(5) 設計軸——受試者內交叉；(6) **且本筆之受測變項即為碳水本身**（C vs P 條件為主要對比，"
              "運動模式為次要對比）。結局為淋巴球增生、自然殺手細胞毒殺活性（NKCA）、IL-1β 生成與"
              "荷爾蒙反應（血糖、皮質醇），皆非契約 inScopeOutcomes 六項，依 n+35 第 1 條判 exclude "
              "並掛 harm-adjacent 牌。"
              "**⚠️ 免疫結局群至此累計 5 筆，其中碳水本身即受測介入者達 3 筆（page 116 099900f6 馬拉松"
              "唾液 IgA 與 URTI、page 125 196a38b4 高海拔唾液 IgA、本筆）。本筆之族群（鐵人三項選手）"
              "與運動型態（2.5 小時 75% VO2max）為三筆中最貼合契約者，且結論明確——碳水攝取顯著影響"
              "血糖、皮質醇、淋巴球計數與 NKCA。此為 safety lane 結局範圍覆核之最強單一證據。**"),
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
