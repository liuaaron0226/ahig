"""n+30 fail-closed audit: did I claim '無對照臂/單臂' without the abstract explicitly saying so?"""
import json, os, re
from pathlib import Path

ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
OUT = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run" / "safety-full-screen-pass-2"
sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
byid = {it["candidateId"]: it for it in sheet["items"]}
j = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))["entries"]

CLAIM = re.compile(r"無對照臂|單臂|單組")
EXPLICIT = re.compile(r"single[- ]arm|uncontrolled|pre-post|prospective study|self-comparison|case report|前後", re.I)

flag = []
for e in j:
    it = byid[e["candidateId"]]
    if not CLAIM.search(e["reason"]):
        continue
    blob = ((it.get("title") or "") + " " + (it.get("abstract") or ""))
    explicit = bool(EXPLICIT.search(blob))
    flag.append((it["seq"], explicit, it["title"][:70]))

print(f"reasons claiming single-arm/no-control: {len(flag)}")
for seq, explicit, title in flag:
    mark = "OK-explicit" if explicit else "** CHECK **"
    print(f"  {seq:>5} {mark}  {title}")
