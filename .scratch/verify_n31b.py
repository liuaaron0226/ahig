# -*- coding: utf-8 -*-
import json, io
OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs/'
       r'b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
rc = json.load(open(OUT + '/post-ruling-reclassification.json', encoding='utf-8'))
ovr = {e['candidateId']: e for e in rc['entries']}
byid = {e['candidateId']: e for e in d['entries']}

# (a) the three IDs I reported in earlier rounds — search as substring anywhere
want = ['bea191ac', '7612fb41', '8304cc76']
print('=== previously reported IDs ===')
for k in want:
    hits = [c for c in byid if k in c]
    if not hits:
        print(' -', k, 'NOT FOUND in judgements')
    for c in hits:
        o = ovr.get(c)
        print(' -', k, '->', c[-12:], 'raw=', byid[c]['opinion'],
              'eff=', (o['effectiveDecision'] if o else byid[c]['opinion']),
              'ruling=', (o.get('ruling') if o else '-'))

# (b) the three overlaid unclear->exclude that matched the wording
print()
print('=== overlaid unclear->exclude with the wording ===')
for k in ['170fa317', '7a4efafd', 'ad018b47']:
    c = next(x for x in byid if x.endswith(k))
    o = ovr[c]
    print('---', k)
    print('  ruling:', o.get('ruling'), '| tag:', o.get('tag'))
    print('  note  :', (o.get('note') or '')[:300])
