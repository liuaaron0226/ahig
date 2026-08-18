"""ADR-0008 evaluation through the real evaluate_termination, with the
n+40 option-(C) p-score exclusion list applied.

Exclusions auto-drop once standard-lane paging reaches that record's page:
the list on disk carries each record's page, and a record whose page is at or
below the last fully-judged standard page is reintegrated automatically.
"""
import json, os, sys
from collections import Counter
os.environ.setdefault('AHIG_PRIVATE_ROOT', r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import evaluate_termination
from pathlib import Path

ROOT = Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
            r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = ROOT / 'standard-full-screen-pass-1'
queue = json.loads((ROOT / 'screening-queue' / 'queue.json').read_text(encoding='utf-8'))
w = json.loads((OUT / 'worksheet.json').read_text(encoding='utf-8'))
op = {e['candidateId']: e['opinion']
      for e in json.loads((OUT / 'judgements.json').read_text(encoding='utf-8'))['entries']}
raw = Counter(op.values())

# overlay is authoritative for decisions + ADR-0008 labels (coordinator b1bc147)
rc = json.loads((OUT / 'post-ruling-reclassification.json').read_text(encoding='utf-8'))
seen = set()
for e in rc['entries']:
    cid = e['candidateId']
    assert cid in op, 'reclass id not judged: ' + cid
    assert cid not in seen, 'duplicate in reclass: ' + cid
    assert op[cid] == e['originalOpinion'], 'originalOpinion mismatch: ' + cid
    seen.add(cid)
    op[cid] = e['effectiveDecision']

# how far has ordinary paging got? last page with every item judged.
by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
done_pages = {p for p, ids in by_page.items() if all(c in op for c in ids)}
contiguous = 0
while contiguous + 1 in done_pages:
    contiguous += 1

# n+72 third state: the 200 tail-spot-check records are an independent random
# audit of the remaining pool, not a continuation of sequential screening, so
# they stay out of the label sequence permanently rather than pending
# reintegration. Split on the explicit `state` field, not on page numbers --
# by page, an audit record the paging front has reached looks reintegratable.
exc_doc = json.loads((OUT / 'p-score-sequence-exclusions.json').read_text(encoding='utf-8'))
out_of_sequence = {e['candidateId'] for e in exc_doc['entries']
                   if e.get('state') == 'out-of-sequence-permanent'}
temp = [e for e in exc_doc['entries'] if e['candidateId'] not in out_of_sequence]
reintegrated = [e['candidateId'] for e in temp if e['page'] <= contiguous]
excluded = {e['candidateId'] for e in temp if e['page'] > contiguous}
assert not (excluded & out_of_sequence), 'the two sets must be disjoint'

decisions = [(it['candidateId'], op[it['candidateId']])
             for it in w['items'] if it['candidateId'] in op]
# safety/other lanes were judged in their own stores; feed them too so the
# precondition sees them.
for d in ['safety-full-screen-pass-1', 'critical-harms-sweep',
          'critical-harms-sweep-orphans']:
    p = ROOT / d / 'judgements.json'
    if p.exists():
        for e in json.loads(p.read_text(encoding='utf-8'))['entries']:
            if e['candidateId'] not in op:
                decisions.append((e['candidateId'], e['opinion']))
                op[e['candidateId']] = e['opinion']

res = evaluate_termination(queue, decisions, p_score_excluded=excluded,
                           out_of_sequence=out_of_sequence)
print('raw       ', dict(raw))
print('overlay   ', len(rc['entries']), 'entries applied')
print('standard contiguous pages judged:', contiguous,
      '| exclusions still held:', len(excluded),
      '| auto-reintegrated:', len(reintegrated),
      '| out-of-sequence (n+72):', len(out_of_sequence))
for k in ('pScore', 'relevantFound', 'screenedCount', 'poolSize', 'windowSize',
          'h0MinTotalRelevant', 'mandatoryLanesFullyScreened',
          'pScoreExcludedCount', 'outOfSequenceCount', 'allowedToStop'):
    print(f'  {k}: {res[k]}')
print('  reason:', res['reason'])
