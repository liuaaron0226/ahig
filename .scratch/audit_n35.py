# Audit: effective-advance entries whose own recorded reason states the outcome
# is NOT in the frozen contract list -> exposure to n+35 rule 1.
import json, re
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
ov=json.load(open(RUN+'/post-ruling-reclassification.json',encoding='utf-8'))
items={it['candidateId']:it for it in w['items']}
op={e['candidateId']:e for e in j['entries']}
ovm={e['candidateId']:e for e in ov['entries']}
eff=lambda c: ovm.get(c,{}).get('effectiveDecision', op[c]['opinion'])
adv=[c for c in op if eff(c)=='advance']
pat=re.compile('非契約清單|非契約 inScopeOutcomes|不在契約清單|無任一契約清單|非清單內結局|非契約 outcome')
hits=[c for c in adv if pat.search(op[c]['reason'])]
print('effective advance:', len(adv))
print('advance whose reason states outcome NOT in contract list:', len(hits))
for c in sorted(hits, key=lambda c: items[c]['page']):
    m=pat.search(op[c]['reason'])
    s=max(0,m.start()-90); print('  p%-4d %s  %s' % (items[c]['page'], c[-8:], (items[c].get('title') or '')[:70]))
    print('        ...%s...' % op[c]['reason'][s:m.end()+40].replace('\n',' '))
