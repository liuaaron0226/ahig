import json
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
ov=json.load(open(RUN+'/post-ruling-reclassification.json',encoding='utf-8'))
items={it['candidateId']:it for it in w['items']}
op={e['candidateId']:e for e in j['entries']}
ovm={e['candidateId']:e for e in ov['entries']}
print('--- the two advance->exclude overlay entries ---')
for e in ov['entries']:
    if e.get('originalOpinion')=='advance':
        print(' ', e['candidateId'][-8:], 'page', items[e['candidateId']]['page'], e['ruling'], e['tag'])
        print('   ', e['note'][:260].replace('\n',' '))
print()
print('--- all effective advances: page + title (immune/cognitive scan) ---')
adv=[c for c in op if ovm.get(c,{}).get('effectiveDecision', op[c]['opinion'])=='advance']
print('effective advance count', len(adv))
import re
key=re.compile('immun|lymphocyte|natural killer|cytokine|IgA|leukocyte|granulocyte|neutrophil|interleukin', re.I)
hits=[c for c in adv if key.search((items[c].get('title') or '')+' '+(items[c].get('abstract') or '')[:400])]
print('advance with immune-flavoured title/abstract:', len(hits))
for c in sorted(hits, key=lambda c: items[c]['page']):
    print('  p%-4d %s %s' % (items[c]['page'], c[-8:], (items[c].get('title') or '')[:85]))
