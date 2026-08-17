import json, os
from pathlib import Path

ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
RUN = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run"
q = json.loads((RUN / "screening-queue" / "queue.json").read_text(encoding="utf-8"))
lane_ids = sorted(e["candidateId"] for e in q if e.get("screeningLane") == "safety-review")
out = RUN / "safety-full-screen-pass-2-list.json"
out.write_text(json.dumps({"candidateIds": lane_ids}, ensure_ascii=False, indent=2), encoding="utf-8")
print("n:", len(lane_ids), "->", out)
