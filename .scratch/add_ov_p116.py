"""Page-116 overlay additions.

099900f6 — five axes match (6% CHO beverage at 1 L/h = 60 g/h, mid-band;
  competitive marathon, during-race; placebo arm; RCT). Excluded on the
  outcome axis: salivary IgA and post-race URTI incidence are immune-function
  and infectious-adverse-event outcomes, not the contract's six. Tagged
  harm-adjacent per n+35 step (b).

ab9f58c4 was tagged [context:heat] last round; a289453d is this round's
  heat-context counterpart (32 degC / 65% RH), judged unclear, decision
  unchanged — the overlay entry only carries the stratifier.
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
    dict(candidateId="ahig:candidate:publication:099900f62658e9f7fd6148b7",
         effectiveDecision="exclude", ruling="n+35-1", tag="harm-adjacent",
         note="五軸相符：6% 碳水飲料 1 L/h（換算 60 g/h，落在契約 10-150 g/h 劑量帶正中）、競技馬拉松"
              "「期間」給予、馬拉松為契約核心耐力項目、對照為安慰劑臂（C 組 n=48 vs P 組 n=50）、"
              "型別明列 Randomized Controlled Trial。結局為唾液 IgA（濃度、IgA:蛋白比、分泌速率）與"
              "賽後 15 日內上呼吸道感染發生率（16/93，17%），屬免疫功能與感染性不良事件結局，"
              "非契約 inScopeOutcomes 六項，依 n+35 第 1 條判 exclude 並掛 harm-adjacent 牌。"
              "**提請協調者注意跨 lane 覆蓋問題：URTI 為不良事件結局而 safety lane 已完成對帳；"
              "若 safety lane 納入範圍未涵蓋「賽後上呼吸道感染」，此類證據將同時落在兩 lane 之外。"
              "建議一併確認 safety lane 結局範圍是否需回溯補充。**"),
    dict(candidateId="ahig:candidate:publication:a289453d5057b8fbc6e17bfc",
         effectiveDecision="unclear", ruling="n+35-2", tag="context-only",
         context="heat",
         note="決策不變（unclear）。四軸相符：葡萄糖-電解質溶液、32°C／65% RH 環境下 50% VO2max "
              "持續 2 小時運動「期間」給予、對照為水補充（water-only，allowlist 第二項）另設無補液臂、"
              "隔日交替之受試者內三條件比較。族群（8 名健康年輕男性無訓練程度描述）、運動模式（未載）、"
              "結局（標題明載 and performance 惟摘要無表現結局數值）、劑量（溶液濃度與給予量未載，"
              "無法核對 10-150 g/h 劑量帶）四項不足，依 fail-closed 判 unclear。本覆蓋層項目僅為承載 "
              "[context:heat] 分層標籤供 W4c 分層設計使用，比照 56aab1fb／ab9f58c4 之 context-only 前例。"),
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
