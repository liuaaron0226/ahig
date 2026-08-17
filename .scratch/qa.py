"""Pre-append QA for a standard-lane page judgement file.

Usage: python .scratch/qa.py .scratch/std_pNNN.json <page>
Checks: count, order-for-order match against the worksheet page, no dupes,
no overlap with already-judged ids, opinion distribution, non-empty reasons.
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
RUN = Path(r"C:/Users/User/Desktop/claude/ahig-private/search-runs"
           r"/b11-exogenous-cho-endurance/b11-full-run")
OUT = RUN / "standard-full-screen-pass-1"

path, page = sys.argv[1], int(sys.argv[2])
new = json.loads(Path(path).read_text(encoding="utf-8"))
w = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
d = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))
judged = {e["candidateId"] for e in (d.get("entries") or [])}

want = [it["candidateId"] for it in w["items"] if it["page"] == page]
got = [e["candidateId"] for e in new]

ok = True
if len(got) != len(want):
    print(f"FAIL count: got {len(got)} want {len(want)}"); ok = False
if got != want:
    for i, (g, x) in enumerate(zip(got, want)):
        if g != x:
            print(f"FAIL order at idx {i}: got {g[-16:]} want {x[-16:]}"); ok = False
if len(set(got)) != len(got):
    print("FAIL duplicates inside file"); ok = False
overlap = [c for c in got if c in judged]
if overlap:
    print(f"FAIL overlap with judged: {len(overlap)}"); ok = False
dist = {"advance": 0, "unclear": 0, "exclude": 0}
for e in new:
    if e["opinion"] not in dist:
        print(f"FAIL bad opinion {e['opinion']}"); ok = False
    else:
        dist[e["opinion"]] += 1
    if not (e.get("reason") or "").strip():
        print(f"FAIL empty reason {e['candidateId'][-16:]}"); ok = False
lens = [len(e["reason"]) for e in new]
print(f"page {page}: n={len(got)} order-match={got == want} dupes=0 overlap={len(overlap)}")
print(f"  dist advance/unclear/exclude = {dist['advance']}/{dist['unclear']}/{dist['exclude']}")
print(f"  reason len {min(lens)}-{max(lens)}")
print("QA PASS" if ok else "QA FAIL")
sys.exit(0 if ok else 1)
