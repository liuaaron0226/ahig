"""Pre-append QA for a page of standard-lane judgements.

Recreated at page 138 — the original was untracked upstream (coordinator n+36
.scratch convention) and removed by the trunk merge. Same checks as before:
count, order-for-order match against the worksheet page, no dupes, no overlap
with already-judged, opinion distribution, non-empty reasons.
"""
import json, sys, collections
from pathlib import Path

RUN = Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
           r'/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')

w = json.loads((RUN / 'worksheet.json').read_text(encoding='utf-8'))
d = json.loads((RUN / 'judgements.json').read_text(encoding='utf-8'))
judged = {e['candidateId'] for e in (d.get('entries') or [])}

new = json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
page = int(sys.argv[2])

# Pages from 140 on are partially pre-filled by the n+40 option-(C) jumped-page
# batch, so the expected set is the page's *unjudged* items, in worksheet order.
want = [it['candidateId'] for it in w['items']
        if it['page'] == page and it['candidateId'] not in judged]
prefilled = sum(1 for it in w['items']
                if it['page'] == page and it['candidateId'] in judged)
got = [e['candidateId'] for e in new]
overlap = [c for c in got if c in judged]
dist = collections.Counter(e['opinion'] for e in new)
lens = [len(e.get('reason') or '') for e in new]
allowed = {'advance', 'unclear', 'exclude'}

ok = (got == want and len(set(got)) == len(got) and not overlap
      and lens and min(lens) > 0
      and all(e['opinion'] in allowed for e in new))

print(f"page {page}: n={len(got)} order-match={got == want} "
      f"dupes={len(got) - len(set(got))} overlap={len(overlap)} "
      f"prefilled={prefilled}")
print(f"  dist advance/unclear/exclude = "
      f"{dist['advance']}/{dist['unclear']}/{dist['exclude']}")
print(f"  reason len {min(lens)}-{max(lens)}")
print("QA PASS" if ok else "QA FAIL")
sys.exit(0 if ok else 1)
