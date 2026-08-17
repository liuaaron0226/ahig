import json
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
ov=json.load(open(RUN+'/post-ruling-reclassification.json',encoding='utf-8'))
items={it['candidateId']:it for it in w['items']}
op={e['candidateId']:e for e in j['entries']}
ovm={e['candidateId']:e for e in ov['entries']}
for k in ['e8e117f1']:
    for c in items:
        if k in c:
            it=items[c]
            print('p%d seq%d %s' % (it['page'], it['seq'], op[c]['opinion']), 'overlay:', ovm.get(c,{}).get('effectiveDecision','-'))
            print('T:', it['title'])
            print('R:', op[c]['reason'])
