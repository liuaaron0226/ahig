"""Re-check judged items 826-1025 against trunk rulings n+30 (single-arm) and n+31 (recreationally trained)."""
import json, os, re
from pathlib import Path

ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
RUN = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run"
OUT = RUN / "safety-full-screen-pass-2"

sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
byid = {it["candidateId"]: it for it in sheet["items"]}
j = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))["entries"]

# only items added in rounds 18-19 (pages 34-41 = seq 826-1025)
recent = [e for e in j if 826 <= byid[e["candidateId"]]["seq"] <= 1025]
print("recent judged:", len(recent))

REC = re.compile(r"recreational", re.I)
SINGLE = re.compile(r"single[- ]arm|uncontrolled|no control", re.I)

hits_rec, hits_single = [], []
for e in recent:
    it = byid[e["candidateId"]]
    blob = ((it.get("title") or "") + " " + (it.get("abstract") or ""))
    if REC.search(blob):
        hits_rec.append((it["seq"], it["title"][:80], e["opinion"]))
    if SINGLE.search(blob):
        hits_single.append((it["seq"], it["title"][:80], e["opinion"]))

print("\n=== n+31: 'recreational' wording in title/abstract ===")
for h in hits_rec:
    print(" ", h)
print("\n=== n+30: single-arm/uncontrolled wording ===")
for h in hits_single:
    print(" ", h)
