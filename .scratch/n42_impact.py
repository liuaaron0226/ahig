import json, os, re, sys
from collections import Counter
os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
ent = {e['candidateId']: e for e in d['entries']}
op = {k: v['opinion'] for k, v in ent.items()}
rc = OUT + '/post-ruling-reclassification.json'
if os.path.exists(rc):
    for e in json.load(open(rc, encoding='utf-8'))['entries']:
        op[e['candidateId']] = e['effectiveDecision']

by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
contiguous = 0
while all(c in op for c in by_page.get(contiguous + 1, [None])):
    contiguous += 1
excluded = set()
exc = OUT + '/p-score-sequence-exclusions.json'
if os.path.exists(exc):
    for e in json.load(open(exc, encoding='utf-8'))['entries']:
        if e['page'] > contiguous:
            excluded.add(e['candidateId'])

def score(flip):
    labels = [1 if (op[it['candidateId']] in ('advance', 'unclear')
                    and it['candidateId'] not in flip) else 0
              for it in w['items']
              if it['candidateId'] in op and it['candidateId'] not in excluded]
    return p_score(labels, w['itemCount'])

base = score(set())
print('BASELINE           ', json.dumps({k: base[k] for k in
      ('pScore', 'relevantFound', 'windowSize')}, default=str))

# strict screen (28) and clean-cut hand-checked subset (3 confirmed)
CLEAN3 = {c for c in op if c.endswith(('a864959a',))}
import subprocess
for name, ids in [('clean-cut confirmed 3', None), ('strict screen 28', None)]:
    pass
print()
print('Effect of removing N unclear hits from the tail is what matters:')
for n in (3, 10, 28, 45):
    # simulate: flip the LAST n unclear records in sequence order (worst case for tail)
    seq = [it['candidateId'] for it in w['items']
           if it['candidateId'] in op and it['candidateId'] not in excluded]
    unc_seq = [c for c in seq if op[c] == 'unclear']
    flip = set(unc_seq[-n:])
    r = score(flip)
    print(f'  flip last {n:3d} unclear -> pScore {r["pScore"]:.4f}  '
          f'relevantFound {r["relevantFound"]}  windowSize {r["windowSize"]}')
