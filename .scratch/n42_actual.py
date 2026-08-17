import json, os, sys
os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
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
seq = [it['candidateId'] for it in w['items']
       if it['candidateId'] in op and it['candidateId'] not in excluded]
pos = {c: i for i, c in enumerate(seq)}

def score(flip):
    return p_score([1 if (op[c] in ('advance', 'unclear') and c not in flip) else 0
                    for c in seq], w['itemCount'])

# hand-verified: axis fact established in the reason, no independent information gap
VERIFIED = ['a864959a', '74d1ada3', 'fbc5bc3f', '7f8e1ebc']
ids = [c for c in seq if c[-8:] in VERIFIED]
base = score(set())
print(f'baseline           pScore {base["pScore"]:.4f}  relevantFound {base["relevantFound"]}  windowSize {base["windowSize"]}')
r = score(set(ids))
print(f'convert verified {len(ids)}  pScore {r["pScore"]:.4f}  relevantFound {r["relevantFound"]}  windowSize {r["windowSize"]}')
print()
print('sequence position of each (tail =', len(seq), '):')
for c in ids:
    print(f'  {c[-8:]}  pos {pos[c]}  ({len(seq)-pos[c]} from tail)')
print()
print('ALPHA reference: allowedToStop requires pScore < alpha (0.05) AND preconditions')
