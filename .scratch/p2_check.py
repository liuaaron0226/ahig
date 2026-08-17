"""Pre-append check: page item count vs judgement file count, and id match."""
import json, os, sys
from pathlib import Path

ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
RUN = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run"
OUT = RUN / "safety-full-screen-pass-2"

page_no = int(sys.argv[1])
jfile = Path(sys.argv[2])

sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
page_ids = [it["candidateId"] for it in sheet["items"] if it["page"] == page_no]
judged = json.loads(jfile.read_text(encoding="utf-8"))
jids = [e["candidateId"] for e in judged]

print(f"page {page_no}: worksheet={len(page_ids)} judged={len(jids)}")
assert len(page_ids) == len(jids), "COUNT MISMATCH"
assert page_ids == jids, f"ID/ORDER MISMATCH: missing={set(page_ids)-set(jids)} extra={set(jids)-set(page_ids)}"
assert all(e["opinion"] in ("advance", "exclude", "unclear") for e in judged), "BAD OPINION"
assert all(e["reason"].strip() for e in judged), "EMPTY REASON"
from collections import Counter
print("OK 25/25" if len(page_ids) == 25 else f"OK {len(page_ids)}/{len(jids)}", Counter(e["opinion"] for e in judged))
