"""Final integrity check for pass-2 completion."""
import json, os, sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
OUT = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run" / "safety-full-screen-pass-2"

sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
doc = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))
j = doc["entries"]

sheet_ids = [it["candidateId"] for it in sheet["items"]]
j_ids = [e["candidateId"] for e in j]

print(f"worksheet items : {len(sheet_ids)}")
print(f"judged entries  : {len(j_ids)}")
print(f"order identical : {sheet_ids == j_ids}")
print(f"duplicates      : {len(j_ids) - len(set(j_ids))}")
print(f"missing         : {len(set(sheet_ids) - set(j_ids))}")
print(f"extra           : {len(set(j_ids) - set(sheet_ids))}")
print(f"opinions        : {dict(Counter(e['opinion'] for e in j))}")
print(f"empty reasons   : {sum(1 for e in j if not e['reason'].strip())}")
lens = [len(e["reason"]) for e in j]
print(f"reason len      : min={min(lens)} mean={sum(lens)//len(lens)} max={max(lens)}")
print(f"judgedBy        : {doc.get('judgedBy')}")
print(f"adr             : {doc.get('adr')}")

byid = {it["candidateId"]: it for it in sheet["items"]}
print("\n--- ADVANCE entries ---")
for e in j:
    if e["opinion"] == "advance":
        it = byid[e["candidateId"]]
        print(f"seq {it['seq']}  {it['candidateId']}")
        print(f"  {it['title'][:100]}")
