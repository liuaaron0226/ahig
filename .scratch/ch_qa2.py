import json, sys, collections
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')/sys.argv[3]
w=json.loads((ROOT/'worksheet.json').read_text(encoding='utf-8'))
d=json.loads((ROOT/'judgements.json').read_text(encoding='utf-8'))
judged={e['candidateId'] for e in (d.get('entries') or [])}
new=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
page=int(sys.argv[2])
want=[it['candidateId'] for it in w['items'] if it['page']==page]
got=[e['candidateId'] for e in new]
overlap=[c for c in got if c in judged]
dist=collections.Counter(e['opinion'] for e in new)
lens=[len(e['reason']) for e in new]
ok = got==want and len(set(got))==len(got) and not overlap and min(lens)>0
print(f"{sys.argv[3]} page {page}: n={len(got)} order-match={got==want} dupes={len(got)-len(set(got))} overlap={len(overlap)}")
print(f"  dist a/u/x = {dist['advance']}/{dist['unclear']}/{dist['exclude']}  reason len {min(lens)}-{max(lens)}")
print("QA PASS" if ok else "QA FAIL")
sys.exit(0 if ok else 1)
