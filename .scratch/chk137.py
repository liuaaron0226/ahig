import json
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
items=w['items']
p137=[it for it in items if it['page']==137]
print('fields:', sorted(p137[0].keys()))
print()
# retraction / erratum check for this page
for it in p137:
    pt=[t.lower() for t in (it.get('publicationTypes') or [])]
    if any('retract' in t or 'errat' in t or 'correct' in t for t in pt):
        print('!!! FLAG', it['candidateId'][-8:], it.get('publicationTypes'))
print('retraction/erratum on p137: none' )
print()
# b59d8173 abstract for dedup claim
for it in items:
    if 'b59d8173' in it['candidateId'] or '4f8472d2' in it['candidateId']:
        print('===', it['candidateId'][-8:], it.get('publicationTypes'))
        print(it.get('title'))
        print((it.get('abstract') or '')[:900])
        print()
