import json, collections
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
q=json.loads((ROOT/'screening-queue'/'queue.json').read_text(encoding='utf-8'))
judged=set()
for d in ['standard-full-screen-pass-1','safety-full-screen-pass-1','safety-full-screen-pass-2','critical-harms-sweep']:
    p=ROOT/d/'judgements.json'
    if p.exists():
        doc=json.loads(p.read_text(encoding='utf-8'))
        ids={e['candidateId'] for e in doc['entries']}
        judged |= ids
        print(f'{d}: {len(ids)}')
ch=[it for it in q if 'critical-harms-signal' in (it.get('flags') or [])]
un=[it for it in ch if it['candidateId'] not in judged]
print()
print('critical-harms total:', len(ch), 'still unjudged:', len(un))
print('  by lane:', collections.Counter(it['screeningLane'] for it in un))
# the 81 remaining are standard-lane; how many lie ahead in the standard worksheet?
w=json.loads((ROOT/'standard-full-screen-pass-1'/'worksheet.json').read_text(encoding='utf-8'))
pg={it['candidateId']:it['page'] for it in w['items']}
ahead=[pg[it['candidateId']] for it in un if it['candidateId'] in pg]
orph=[it for it in un if it['candidateId'] not in pg]
print('  in standard worksheet ahead:', len(ahead), 'pages', min(ahead) if ahead else '-', '-', max(ahead) if ahead else '-')
print('  ORPHANS (in no worksheet):', len(orph))
for it in orph:
    print('    ', it['candidateId'][-8:], it['priorityTier'], '|', (it.get('title') or '')[:70])
