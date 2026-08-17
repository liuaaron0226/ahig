import json, os
from collections import Counter
from pathlib import Path

ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
RUN = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run"
q = json.loads((RUN / "screening-queue" / "queue.json").read_text(encoding="utf-8"))
print("type:", type(q), "n:", len(q))
print("entry keys:", sorted(q[0].keys()))
print(Counter(e.get("screeningLane") for e in q))
