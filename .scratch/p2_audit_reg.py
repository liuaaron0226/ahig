"""Rule 5 stress test: would any registry-record verdict change if the
publication-type argument were struck out, leaving only substantive axes?"""
import json, os, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
OUT = Path(os.environ["AHIG_PRIVATE_ROOT"]) / "search-runs/b11-exogenous-cho-endurance/b11-full-run/safety-full-screen-pass-2"
sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
byid = {it["candidateId"]: it for it in sheet["items"]}
j = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))["entries"]
reg = [e for e in j if "registry-record" in e["candidateId"]]

# Strip the leading 文獻型態軸 sentence, see what substantive axes remain.
ABS_AXES = {
    "族群軸": "population (absolute per rule 1)",
    "時序軸": "timing (rule 2)",
    "介入軸": "intervention",
    "結局軸": "outcome",
    "對照軸": "comparator",
    "設計軸": "design",
}
weak = []
for e in reg:
    r = e["reason"]
    # remove the sentence(s) that argue from publication type
    stripped = re.sub(r"文獻型態軸：[^。]*。", "", r)
    axes = [k for k in ABS_AXES if k in stripped]
    it = byid[e["candidateId"]]
    # an entry is SAFE if population or timing or a clearly-stated intervention/outcome mismatch survives
    strong = ("族群軸" in stripped) or ("時序軸" in stripped) or ("結局軸" in stripped) or ("介入軸" in stripped)
    if not strong:
        weak.append((it["seq"], e["candidateId"], axes, it["title"][:70]))

print(f"registry records: {len(reg)}")
print(f"entries whose verdict rests on publication-type framing alone "
      f"(would need unclear per rule 5): {len(weak)}")
for seq, cid, axes, t in weak:
    print(f"  seq {seq} axes_left={axes}")
    print(f"    {t}")

# Distribution of surviving axes
from collections import Counter
c = Counter()
for e in reg:
    stripped = re.sub(r"文獻型態軸：[^。]*。", "", e["reason"])
    for k in ABS_AXES:
        if k in stripped:
            c[k] += 1
print("\nsurviving axis counts across the 45 registry records:")
for k, v in c.most_common():
    print(f"  {k}: {v}")
