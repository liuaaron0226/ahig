# -*- coding: utf-8 -*-
import json, re, os
OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs/'
       r'b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
rc = json.load(open(OUT + '/post-ruling-reclassification.json', encoding='utf-8'))
ov = {e['candidateId']: e['effectiveDecision'] for e in rc['entries']}
item = {it['candidateId']: it for it in w['items']}

pat = re.compile(r'recreationally[- ]trained', re.I)
rows = []
for e in d['entries']:
    cid = e['candidateId']
    ab = (item.get(cid, {}).get('abstract') or '')
    ti = (item.get(cid, {}).get('title') or '')
    if pat.search(ab) or pat.search(ti) or pat.search(e['reason']):
        rows.append((cid, e['opinion'], ov.get(cid, '(none)'),
                     'ABS' if pat.search(ab) else ('TITLE' if pat.search(ti) else 'reason-only'),
                     ti[:62]))
print('recreationally-trained matches:', len(rows))
for cid, raw, eff, src, ti in rows:
    eff_final = eff if eff != '(none)' else raw
    flag = '' if eff_final == 'unclear' else '   <<< NOT unclear'
    print(' -', cid[-8:], 'raw=%-8s eff=%-8s [%s]' % (raw, eff_final, src), ti, flag)
