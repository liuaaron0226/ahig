"""Pre-flight: does my pass-2 output satisfy every _validate_machine_binding
requirement of reconcile_machine? Checks ONLY my own artefacts — no pass-1 read."""
import json, os, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = Path(os.environ["AHIG_PRIVATE_ROOT"]) / "search-runs/b11-exogenous-cho-endurance/b11-full-run/safety-full-screen-pass-2"

sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
doc = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))

print("files in out dir:", sorted(p.name for p in OUT.iterdir()))
print("\njudgements.json top-level keys:", sorted(doc))
print("worksheet.json top-level keys :", sorted(sheet))

FORBIDDEN = {"decision", "decidedBy", "decidedAt", "reasonShort"}
MACHINE_OPINIONS = {"advance", "exclude", "unclear"}

entries = doc["entries"]
print(f"\n--- entry-level checks over {len(entries)} entries ---")
bad_op = [e for e in entries if e.get("opinion") not in MACHINE_OPINIONS]
print(f"invalid opinion            : {len(bad_op)}")
forb = [e for e in entries if set(e) & FORBIDDEN]
print(f"carrying human-decision key: {len(forb)}")
# rawResponse: the append tool may store the reason under 'reason'
keys = sorted({k for e in entries for k in e})
print(f"entry keys present         : {keys}")
for cand_key in ("rawResponse", "reason"):
    n = sum(1 for e in entries if isinstance(e.get(cand_key), str) and e[cand_key].strip())
    print(f"  non-empty '{cand_key}'      : {n}/{len(entries)}")

print("\n--- reviewer / judgedBy envelope ---")
print("judgedBy :", json.dumps(doc.get("judgedBy"), ensure_ascii=False))
print("reviewer :", json.dumps(doc.get("reviewer"), ensure_ascii=False))
jb = doc.get("judgedBy") or {}
for f in ("agentClass", "modelId", "modelVersion"):
    v = jb.get(f)
    flag = "OK" if v else "MISSING"
    print(f"  judgedBy.{f}: {v!r}  [{flag}]")
rv = doc.get("reviewer") or {}
for f, want in (("agentClass", "llm"), ("reviewerId", None), ("blindedToOtherReviewer", True)):
    v = rv.get(f)
    ok = (v == want) if want is not None else bool(v)
    print(f"  reviewer.{f}: {v!r}  [{'OK' if ok else 'MISSING/WRONG'}]")
print("reviewId :", doc.get("reviewId"))
