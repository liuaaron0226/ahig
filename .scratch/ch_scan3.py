import json, collections
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
q=json.loads((ROOT/'screening-queue'/'queue.json').read_text(encoding='utf-8'))
ch=[it for it in q if 'critical-harms-signal' in (it.get('flags') or [])]
print('critical-harms-signal total:', len(ch))
print('by lane:', collections.Counter(it['screeningLane'] for it in ch))

# what has been judged already, per lane store
std=json.loads((ROOT/'standard-full-screen-pass-1'/'judgements.json').read_text(encoding='utf-8'))
stdids={e['candidateId'] for e in std['entries']}
print('standard judged:', len(stdids))

safe_ids=set()
for d in ['safety-full-screen-pass-1','safety-full-screen-pass-2']:
    p=ROOT/d/'judgements.json'
    if p.exists():
        doc=json.loads(p.read_text(encoding='utf-8'))
        ents=doc['entries'] if isinstance(doc,dict) else doc
        safe_ids |= {e['candidateId'] for e in ents}
        print(d, len(ents))
print('safety judged union:', len(safe_ids))

judged = stdids | safe_ids
un=[it for it in ch if it['candidateId'] not in judged]
print('critical-harms UNJUDGED:', len(un))
print('  by lane:', collections.Counter(it['screeningLane'] for it in un))
print('  by tier:', collections.Counter(it['priorityTier'] for it in un))
json.dump([it['candidateId'] for it in un], open('.scratch/ch_unjudged.json','w'), indent=0)
