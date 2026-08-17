"""Post-completion audit against briefing 判讀規約 rules 3 and 5."""
import json, os, re, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
ROOT = Path(os.environ["AHIG_PRIVATE_ROOT"])
OUT = ROOT / "search-runs" / "b11-exogenous-cho-endurance" / "b11-full-run" / "safety-full-screen-pass-2"
sheet = json.loads((OUT / "worksheet.json").read_text(encoding="utf-8"))
byid = {it["candidateId"]: it for it in sheet["items"]}
j = json.loads((OUT / "judgements.json").read_text(encoding="utf-8"))["entries"]

# --- Rule 5: registry-record must have positive out-of-scope evidence, not publication standards
reg = [e for e in j if "registry-record" in e["candidateId"]]
POSITIVE_AXIS = re.compile(r"族群軸|介入軸|時序軸|對照軸|結局軸|設計軸")
print(f"=== Rule 5: registry-record entries: {len(reg)} ===")
no_positive = [e for e in reg if not POSITIVE_AXIS.search(e["reason"])]
print(f"  reasons WITHOUT any substantive axis (type-only): {len(no_positive)}")
for e in no_positive:
    print(f"    seq {byid[e['candidateId']]['seq']} [{e['opinion']}]")
print(f"  opinions: {dict((o, sum(1 for e in reg if e['opinion']==o)) for o in set(x['opinion'] for x in reg))}")
lead_type = [e for e in reg if e["reason"].startswith("文獻型態軸")]
print(f"  reasons LEADING with 文獻型態軸 (wording flagged): {len(lead_type)}")

# --- Rule 3: same total dose, different CHO type/form comparison -> advance [cho-type-comparison]
TYPE_CMP = re.compile(r"醣種|不同醣類|醣類組成|葡萄糖\+果糖|果糖 vs|澱粉 vs|同劑量|等量葡萄糖|isomaltulose|大麥澱粉")
hits = [e for e in j if TYPE_CMP.search(e["reason"])]
print(f"\n=== Rule 3: same-dose / CHO-type comparison mentions: {len(hits)} ===")
for e in hits:
    it = byid[e["candidateId"]]
    pop = "族群軸" in e["reason"]
    tim = "時序軸" in e["reason"]
    print(f"  seq {it['seq']} [{e['opinion']}] pop_axis={pop} timing_axis={tim}")
    print(f"    {it['title'][:78]}")

# --- Rule 2 細則: segmented exercise / inter-segment gaps
SEG = re.compile(r"段落|回合間|兩回合|間歇 ?3[0-9]|恢復期回補")
seg = [e for e in j if SEG.search(e["reason"])]
print(f"\n=== Rule 2 細則: segmented-exercise gap mentions: {len(seg)} ===")
for e in seg:
    it = byid[e["candidateId"]]
    print(f"  seq {it['seq']} [{e['opinion']}] {it['title'][:70]}")
