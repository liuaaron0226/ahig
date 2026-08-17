"""QA for a batch of the 74 jumped-page critical-harms judgements."""
import json, sys, collections
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
          r'/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
w=json.loads((ROOT/'worksheet.json').read_text(encoding='utf-8'))
d=json.loads((ROOT/'judgements.json').read_text(encoding='utf-8'))
judged={e['candidateId'] for e in d['entries']}
allow=set(json.loads(Path('.scratch/ch76_list.json').read_text(encoding='utf-8'))['candidateIds'])
seq={it['candidateId']:it['seq'] for it in w['items']}
new=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
got=[e['candidateId'] for e in new]
bad_scope=[c for c in got if c not in allow]
overlap=[c for c in got if c in judged]
ordered = got == sorted(got, key=lambda c: seq[c])
dist=collections.Counter(e['opinion'] for e in new)
lens=[len(e.get('reason') or '') for e in new]
ok = not bad_scope and not overlap and len(set(got))==len(got) and ordered and min(lens)>0
print(f"batch {sys.argv[1]}: n={len(got)} in-scope={not bad_scope} dupes={len(got)-len(set(got))} "
      f"overlap={len(overlap)} seq-ordered={ordered}")
print(f"  dist a/u/x = {dist['advance']}/{dist['unclear']}/{dist['exclude']}  reason len {min(lens)}-{max(lens)}")
print("QA PASS" if ok else "QA FAIL")
sys.exit(0 if ok else 1)
