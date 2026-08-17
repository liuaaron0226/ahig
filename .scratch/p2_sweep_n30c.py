"""n+30 fail-closed: for reasons claiming single-arm, is there an INDEPENDENT non-design axis?
If yes, the ruling changes nothing. If the design axis is the sole basis and the abstract
does not explicitly state single-arm, the item would need to become unclear."""
import json, os, re
from pathlib import Path

ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
OUT = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run" / "safety-full-screen-pass-2"
sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
byid = {it["candidateId"]: it for it in sheet["items"]}
j = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))["entries"]

CLAIM = re.compile(r"無對照臂|單臂|單組")
OTHER_AXIS = re.compile(r"族群軸|介入軸|結局軸|時序軸|文獻型態軸|對照軸")

sole = []
for e in j:
    it = byid[e["candidateId"]]
    r = e["reason"]
    if not CLAIM.search(r):
        continue
    axes = set(OTHER_AXIS.findall(r))
    # design axis alone (設計軸 not in OTHER_AXIS list) => no independent basis
    if not axes:
        sole.append((it["seq"], it["title"][:70], sorted(axes)))

print(f"items whose exclusion rests ONLY on the design axis: {len(sole)}")
for s in sole:
    print("  ", s)
if not sole:
    print("  -> none. Every single-arm exclusion carries an independent axis; n+30 requires no reversal.")
