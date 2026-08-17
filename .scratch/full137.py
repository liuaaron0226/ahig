import json,sys
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
keys=sys.argv[1:]
for it in w['items']:
    if any(k in it['candidateId'] for k in keys):
        print('===',it['candidateId'][-8:], it.get('year'), it.get('publicationTypes'))
        print('T:',it.get('title'))
        print('A:',(it.get('abstract') or '(none)'))
        print()
