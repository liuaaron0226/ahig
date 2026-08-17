import json, re
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
items=w['items']
jent=j['entries'] if isinstance(j,dict) else j
op={e['candidateId']:e for e in jent}
by={it['candidateId']:it for it in items}

# 1) how were truncated "(continues)" abstracts judged?
trunc=[it for it in items if '(continues)' in (it.get('abstract') or '')]
print('truncated total:', len(trunc))
import collections
c=collections.Counter(op[it['candidateId']]['opinion'] for it in trunc if it['candidateId'] in op)
print('judged so far:', sum(c.values()), dict(c))
# show a few judged dissertations among them
n=0
for it in trunc:
    cid=it['candidateId']
    if cid in op and 'Dissertation' in (it.get('publicationTypes') or []):
        n+=1
        if n<=6:
            print('---', cid[-8:], op[cid]['opinion'], '|', (it.get('title') or '')[:80])
            print('    ', op[cid]['reason'][:300].replace('\n',' '))
print('judged dissertations among truncated:', n)

# 2) the Nieman 2.5h cluster
for key in ['b59d8173','4f8472d2','099900f6','196a38b4']:
    for it in items:
        if key in it['candidateId']:
            print('===',key, it.get('year'), (it.get('title') or '')[:95])
