"""Page-133 overlay addition: harm-adjacent tag for b59d8173.

b59d8173 — sixth member of the immune-outcome group and the fourth in which
carbohydrate itself is the tested intervention. Six axes match: 30 experienced
marathon runners, 2.5 h of high-intensity running, 6% carbohydrate ingested
DURING exercise, placebo comparator, randomised double-blind design, and the
C-vs-P contrast is the study's primary question.

Excluded on the outcome axis only: lymphocyte proliferative response, T-cell
counts, glucose and cortisol are none of the contract's six.

Same team and same 2.5 h / 6% CHO design as page 128's 4f8472d2 (triathletes,
running and cycling) — dedup type four, variant "split by population and
exercise mode". The two findings agree: CHO raises glucose, lowers cortisol,
and blunts the post-exercise T-cell fall.
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
    dict(candidateId="ahig:candidate:publication:b59d8173d82feec5a6ae355c",
         effectiveDecision="exclude", ruling="n+35-1", tag="harm-adjacent",
         note="**六軸相符**：(1) 族群軸——30 名有經驗馬拉松跑者；(2) 時序與運動型態軸——2.5 小時"
              "高強度跑步「期間」攝取；(3) 介入軸——6% 碳水，為契約 CHO 型態且為受測變項；"
              "(4) 對照軸——安慰劑；(5) 設計軸——隨機雙盲安慰劑對照；(6) 受測變項即為碳水本身。"
              "結局為淋巴球增生反應（Con A／PHA／PWM 誘發）、T 細胞計數、血糖與皮質醇，"
              "皆非契約 inScopeOutcomes 六項，依 n+35 第 1 條判 exclude 並掛 harm-adjacent 牌。"
              "**⚠️ 免疫結局群至此累計 6 筆，其中碳水本身即受測介入者達 4 筆（099900f6、196a38b4、"
              "4f8472d2、本筆）。本筆與 page 128 4f8472d2 為同一團隊、同 2.5 小時高強度運動、"
              "同 6% 碳水設計之系列研究（前者為鐵人三項選手之跑步與自行車、本筆為馬拉松跑者之跑步）"
              "——去重第四型第 14 例，變體為分族群與運動模式。其結論明確：碳水攝取使血糖較高、"
              "皮質醇較低，並減輕運動後 T 細胞下降，與 4f8472d2 之 NKCA 發現一致，兩筆互為佐證。"
              "safety lane 結局範圍覆核之證據再強化。**"),
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
