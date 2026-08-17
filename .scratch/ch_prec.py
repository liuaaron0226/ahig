import json, collections, re
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
sw=json.loads((ROOT/'safety-full-screen-pass-1'/'worksheet.json').read_text(encoding='utf-8'))
sj=json.loads((ROOT/'safety-full-screen-pass-1'/'judgements.json').read_text(encoding='utf-8'))
items={it['candidateId']:it for it in sw['items']}
op={e['candidateId']:e for e in sj['entries']}
rev=[c for c,it in items.items() if any(t in ('Review','Systematic Review','Scoping Review') for t in (it.get('publicationTypes') or []))]
print('safety lane Review-type:', len(rev), collections.Counter(op[c]['opinion'] for c in rev if c in op))
for c in rev[:4]:
    print('  ', c[-8:], op[c]['opinion'], '|', op[c]['reason'][:180].replace('\n',' '))
print()
reg=[c for c in items if 'registry-record' in c]
print('safety lane registry-record:', len(reg), collections.Counter(op[c]['opinion'] for c in reg if c in op))
for c in reg[:4]:
    print('  ', c[-8:], op[c]['opinion'], '|', op[c]['reason'][:200].replace('\n',' '))
