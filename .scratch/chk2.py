import json, re
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
jent=j['entries']; items={it['candidateId']:it for it in w['items']}
op={e['candidateId']:e for e in jent}
print('--- reasons mentioning 19.3 / road march ---')
for e in jent:
    if '19.3' in e['reason'] or '行軍' in e['reason']:
        print(' ', e['candidateId'][-8:], e['opinion'], e['reason'][:150].replace('\n',' '))
print()
print('--- Historical Article in pool ---')
ha=[c for c,it in items.items() if 'Historical Article' in (it.get('publicationTypes') or [])]
print('count', len(ha), 'judged', sum(1 for c in ha if c in op))
for c in ha[:8]:
    print('  ', c[-8:], op[c]['opinion'] if c in op else 'UNJUDGED', (items[c].get('title') or '')[:60])
print()
print('--- worksheet: other Nieman 2.5h marathon runner records ---')
for c,it in items.items():
    a=(it.get('abstract') or '')
    if '2.5 h' in a and 'marathon runners' in a:
        print('  ', c[-8:], op[c]['opinion'] if c in op else 'UNJUDGED', (it.get('title') or '')[:80])
