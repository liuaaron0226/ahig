"""Verify ruling R3: no prior judgement contradicts IV-route / mouth-rinse exclusion,
and list instrument-validity ([methodological]) candidates."""
import json, os, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
RUN = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run"
OUT = RUN / "safety-full-screen-pass-2"

sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
byid = {it["candidateId"]: it for it in sheet["items"]}
j = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))["entries"]

IV = re.compile(r"靜脈|輸注|infusion|intravenous", re.I)
RINSE = re.compile(r"漱口|mouth rins|rinse")
METHOD = re.compile(r"效度|準確度|感測器|量測驗證|驗證用|示蹤劑|方法學")

print(f"total judged: {len(j)}")
for label, pat in (("IV", IV), ("RINSE", RINSE), ("METHOD", METHOD)):
    hits = [(byid[e["candidateId"]]["seq"], e["opinion"], byid[e["candidateId"]]["title"][:60])
            for e in j if pat.search(e["reason"])]
    print(f"\n--- {label}: {len(hits)} ---")
    for seq, op, t in hits:
        flag = "  <<< NOT EXCLUDE" if op != "exclude" else ""
        print(f"  seq {seq} [{op}] {t}{flag}")
