import json, re
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
ent=j['entries']
prev=[e for e in ent if e['candidateId'] not in
      {x['candidateId'] for x in json.load(open('.scratch/std_p137.json',encoding='utf-8'))}]
print('prior judged:', len(prev))
for name,p in [('個案研究', r'個案研究(?:累計)?第 (\d+) 筆'),
               ('代謝性肌病', r'代謝性肌病(?:系列)?(?:累計)?第 (\d+) 筆'),
               ('IV/靜脈', r'(?:靜脈|IV)[^。]{0,16}?(?:累計)?第 (\d+) 筆')]:
    hits=[(int(m.group(1)), e['candidateId'][-8:]) for e in prev for m in re.finditer(p,e['reason'])]
    print(f'{name}: last={hits[-1] if hits else None} max={max([h[0] for h in hits]) if hits else None} n={len(hits)}')
print()
print('--- loose: 個案研究 / 代謝性肌 mentions in prior ---')
for kw in ['個案研究','代謝性肌','靜脈']:
    c=[e['candidateId'][-8:] for e in prev if kw in e['reason']]
    print(f'  {kw}: {len(c)} entries; last 3 {c[-3:]}')
    for cid in c[-2:]:
        r=[e['reason'] for e in prev if e['candidateId'].endswith(cid)][0]
        i=r.find(kw); print('     ...', r[max(0,i-70):i+50].replace('\n',' '))
