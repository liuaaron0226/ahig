"""Print worksheet page-dump items in a seq range (for reading long pages in chunks)."""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

buf = Path(sys.argv[1])
lo = int(sys.argv[2])
hi = int(sys.argv[3])
data = json.loads(buf.read_text(encoding="utf-8"))
for it in data["items"]:
    if lo <= it["seq"] <= hi:
        print("=" * 70)
        print(f"seq {it['seq']}  {it['candidateId']}")
        print(f"YEAR {it.get('publicationYear')}  TYPES {it.get('publicationTypes')}")
        print(f"TITLE {it['title']}")
        a = it.get("abstract")
        if isinstance(a, str) and len(a) > 3000:
            a = a[:3000] + f"  ...[TRUNCATED, total {len(a)} chars]"
        print("ABS:", a)
        print()
