"""Page-117 overlay addition: [context:altitude] stratifier for b5163608.

b5163608 — five axes match (CHO supplementation via commercial energy drinks,
placebo arm, RCT, mountaineering time trial at 5192 m completed 17% faster
with 18% lower RPE). Judged unclear because population training status is
unreported and the 3.5 g/kg/day figure is a DAILY total that cannot be
converted to g/h for the 10-150 g/h band; ad libitum whole-expedition intake
also prevents separating in-exercise from out-of-exercise consumption.

Decision UNCHANGED — this overlay entry only carries the [context:altitude]
stratifier, mirroring the 56aab1fb / ab9f58c4 / a289453d context-only precedent.
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
    dict(candidateId="ahig:candidate:publication:b5163608cc6435918a1f0aac",
         effectiveDecision="unclear", ruling="n+35-2", tag="context-only",
         context="altitude",
         note="決策不變（unclear）。五軸相符：市售能量飲料之碳水補充（依從者每日較安慰劑多攝取 "
              "3.5±1.4 g/kg 體重）、雙盲安慰劑對照、標題即載 randomized controlled trial、"
              "**結局為 5,192 m 登山計時賽完成時間（tt-completion-time 構念），碳水組快 17%、"
              "RPE 低 18%**、22 日遠征全程 ad libitum 攝取含運動期間。三項不足："
              "(1) 族群——41 名高海拔遠征隊成員，全無訓練程度描述，遠征隊成員與競技耐力運動員未必等同；"
              "(2) 劑量——3.5 g/kg/day 為每日總量，無法換算為運動期間 g/h 以核對 10-150 g/h 劑量帶；"
              "(3) 時序——ad libitum 全程攝取使運動期間與非運動期間攝取無從分離，摘要自陳為 "
              "chronic carbohydrate supplementation，屬「ad libitum 自由飲用設計」議題第三例。"
              "本覆蓋層項目僅為承載 [context:altitude] 分層標籤供 W4c 分層設計使用。"),
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
