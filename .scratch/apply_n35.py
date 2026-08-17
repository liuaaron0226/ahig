"""Apply coordinator batch ruling n+35 to the reclassification overlay.

Ruling:
 1. Five-axis-match but outcome not in inScopeOutcomes -> exclude, tag outcome-adjacent.
    (c) If the study ALSO has an in-list outcome, advance on that outcome instead.
 2. Altitude/hypoxia/heat = stratifier, NOT an exclusion axis -> tag [context:*].
 3. Cross-lane duplicate: safety lane (frozen) is authoritative; standard side tagged
    cross-lane-duplicate and not double-counted into advance.

Overlay is append-only in spirit: we add entries, never rewrite judgements.json.
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
    # --- Ruling 1: outcome axis co-equal; all outcomes out of list -> exclude ---
    dict(candidateId="ahig:candidate:publication:2d260d25b4ccdd9a461bf3eb",
         effectiveDecision="exclude", ruling="n+35-1", tag="outcome-adjacent",
         note="20 名菁英越野跑者、山徑馬拉松賽中 120/90/60 g/h 三臂劑量梯度（族群/時序/介入/對照/設計五軸相符，"
              "且跨 high 與 very-high 兩劑量帶）；惟結局僅 EIMD 標記（CK/LDH/GOT/尿素/肌酸酐）與 RPE 推算之"
              "內部運動負荷，經核對摘要無任一契約清單內結局。依 n+35 第 1 條由 advance 改判 exclude 並掛牌。"
              "**本筆為 doseBands 設計之最佳素材，若擴充結局軸應優先回收。**"),
    dict(candidateId="ahig:candidate:publication:0a091d14698bed6bdf91da16",
         effectiveDecision="exclude", ruling="n+35-1", tag="outcome-adjacent",
         context="hypoxia",
         note="12 名受過訓練跑者、1 小時 65% VO2max 跑步中攝取 CHO vs 安慰劑（四軸相符）；結局為中樞/周邊疲勞"
              "（ΔVA、ΔQtw,pot）與 f-TRP/BCAA 比值，無清單內結局。依第 1 條 exclude；低氧情境依第 2 條"
              "改標 [context:hypoxia] 為分層變項，非排除依據。"),
    dict(candidateId="ahig:candidate:publication:2cb50ce567236b90e556ed4a",
         effectiveDecision="exclude", ruling="n+35-1", tag="outcome-adjacent",
         note="16 名經驗馬拉松跑者、3 小時 70% VO2max 跑步中 1 L/h CHO vs 安慰劑、雙盲隨機平衡順序"
              "（五軸相符，該類型中族群與時序最無疑義者）；結局為 F2-異前列腺素、脂質過氧化物、FRAP 與皮質醇，"
              "無清單內結局。依第 1 條 exclude 並掛牌。"),
    # --- Ruling 3: cross-lane duplicate, do not double-count ---
    dict(candidateId="ahig:candidate:publication:283e1f5040cec6ae96a1d3de",
         effectiveDecision="exclude", ruling="n+35-3", tag="cross-lane-duplicate",
         note="與 safety lane pass-2 之 advance a8d22fb413c2014a80482106 為同一試驗之兩個預印本版本"
              "（標題逐字相同、2024 vs 2026、分屬不同 lane）。依第 3 條以較早且已固化之 safety lane 為準，"
              "standard 側不重複計入 advance 總數。**證據本身未被丟棄——safety 側之 advance 仍為權威紀錄。**"),
    # --- Ruling 2: altitude is a stratifier; decision unchanged, tag added ---
    dict(candidateId="ahig:candidate:publication:56aab1fbd07d05ffaff699d4",
         effectiveDecision="unclear", ruling="n+35-2", tag="context-only",
         context="altitude",
         note="標題明載結局為外源性葡萄糖氧化（＝契約 exogenous-cho-oxidation-peak，清單內），故不屬"
              "outcome-adjacent。高海拔情境依第 2 條為分層變項非排除軸，決定維持 unclear（無摘要，"
              "受試者數/年齡/訓練狀態/劑量/對照臂皆未知），加標 [context:altitude]。已列 W4b 首批四強。"),
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
        print(f"[{r['originalOpinion']} -> {r['effectiveDecision']}] {r['tag']:22} {r['candidateId'][-16:]}")
    print(f"\n(dry run) would add {len(added)} entries; overlay 86 -> {86 + len(added)}")
    sys.exit(0)

doc["entries"].extend(added)
doc["ruling"] = (doc["ruling"] + " | coordinator batch ruling, commit 4547b6d (協調者第 n+35 輪)")
doc["producedAtJudgedCount"] = len(judged)
tmp = ovf.with_suffix(".json.tmp")
tmp.write_text(json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
tmp.replace(ovf)
print(f"WROTE overlay: {len(doc['entries'])} entries (+{len(added)})")
