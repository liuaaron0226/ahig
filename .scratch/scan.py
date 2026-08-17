import json,re,sys
ok={'g','kg','ph','vs','mg','ml','mj','bmi','dxa','rm','kj','vo','iga','wgan','gp','xgboost','svr','mlp','geneactiv','asprosin','masld','comp','nefa','dnl','ebct','cacs','chd','vdr','er','colia','paq','fitnessgram','whr','ldl','hdl','tc','fbg','npa','ssb','who','ers','nhis','nsc','ct','ci','sd','se','n'}
d=json.load(open(sys.argv[1],encoding='utf-8'))
bad=0
for e in d:
    m=re.findall(r'[Ѐ-ӿ가-힯぀-ヿ]+|[A-Za-z]+(?=[一-鿿])|(?<=[一-鿿])[A-Za-z]{3,}', e['reason'])
    m=[x for x in m if x.lower() not in ok]
    if m:
        print(e['candidateId'][-8:], m[:6]); bad+=1
print('entries',len(d),'flagged',bad)
