import json, collections
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
jent=j['entries'] if isinstance(j,dict) else j
op={e['candidateId']:e for e in jent}
items={it['candidateId']:it for it in w['items']}
# Preprint precedent
pre=[c for c,it in items.items() if 'Preprint' in (it.get('publicationTypes') or [])]
print('Preprint total in pool:', len(pre), 'judged:', sum(1 for c in pre if c in op))
for c in pre:
    if c in op:
        print('  ', c[-8:], op[c]['opinion'], '|', (items[c].get('title') or '')[:60])
        print('     ', op[c]['reason'][:180].replace('\n',' '))
print()
# mis-hit family notes: search reasons for 誤命中
mis=[e for e in jent if '誤命中' in e['reason'] or '術語家族' in e['reason']]
print('mis-hit annotated:', len(mis))
c=collections.Counter()
import re
for e in mis[-14:]:
    print('  ', e['candidateId'][-8:], e['reason'][:150].replace('\n',' '))
