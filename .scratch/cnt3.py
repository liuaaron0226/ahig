import json, re, collections
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
jent=j['entries']; pg={it['candidateId']:it['page'] for it in w['items']}
d=collections.defaultdict(collections.Counter)
for e in jent:
    d[pg[e['candidateId']]][e['opinion']]+=1
for p in range(126,137):
    c=d[p]; print(p, f"a{c['advance']} u{c['unclear']} x{c['exclude']}")
print()
for kw in ['McArdle','肌病','肝醣儲積','代謝性肌','案例研究','個案研究','n=1','熱環境','[context:heat]','軍','行軍']:
    hits=[e['candidateId'][-8:] for e in jent if kw in e['reason']]
    print(f'{kw}: {len(hits)}', hits[-5:])
