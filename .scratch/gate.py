import json
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
q=json.loads((ROOT/'screening-queue'/'queue.json').read_text(encoding='utf-8'))
judged=set()
for d in ['standard-full-screen-pass-1','safety-full-screen-pass-1','safety-full-screen-pass-2',
          'critical-harms-sweep','critical-harms-sweep-orphans']:
    p=ROOT/d/'judgements.json'
    if p.exists():
        judged |= {e['candidateId'] for e in json.loads(p.read_text(encoding='utf-8'))['entries']}
# exact replication of statistical_termination.py precondition
mand=[e['candidateId'] for e in q
      if e['candidateId'] not in judged
      and (e.get('screeningLane')=='safety-review'
           or 'critical-harms-signal' in (e.get('flags') or []))]
safety_un=[e for e in q if e.get('screeningLane')=='safety-review' and e['candidateId'] not in judged]
ch_un=[e for e in q if 'critical-harms-signal' in (e.get('flags') or []) and e['candidateId'] not in judged]
print('mandatory unscreened TOTAL:', len(mand))
print('  safety-review lane unscreened:', len(safety_un))
print('  critical-harms unscreened   :', len(ch_un))
print('mandatoryLanesFullyScreened would be:', not mand)
print()
print('BEFORE this sweep it was:', 116+len(mand), 'unscreened (116 non-standard + these)')
