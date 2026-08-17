import json
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
jent=j['entries'] if isinstance(j,dict) else j
op={e['candidateId']:e for e in jent}
for it in w['items']:
    a=it.get('abstract') or ''
    if '(continues)' in a and it['candidateId'] in op and op[it['candidateId']]['opinion']=='unclear':
        print('---', it['candidateId'][-8:], it.get('publicationTypes'), '|', (it.get('title') or '')[:75])
        print('   ', op[it['candidateId']]['reason'][:290].replace('\n',' '))
