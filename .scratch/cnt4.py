import json, re
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
jent=j['entries']
for pat in [r'自選補給[^。]{0,20}?(\d+)\s*筆', r'學位論文[^。]{0,14}?(\d+)\s*筆',
            r'博士論文[^。]{0,14}?(\d+)\s*(?:筆|篇)', r'檢索雜訊[^。]{0,14}?(\d+)\s*筆',
            r'第(?:四|4)型[^。]{0,14}?(\d+)\s*例', r'第(?:五|5)型[^。]{0,20}?(\d+)\s*例',
            r'免疫[^。]{0,20}?(\d+)\s*筆', r'真實[^。]{0,24}?(\d+)\s*筆']:
    hits=[(int(m.group(1)), e['candidateId'][-8:], m.group(0)) for e in jent for m in re.finditer(pat,e['reason'])]
    print(pat)
    if hits:
        print('   last:', hits[-1], ' max:', max(h[0] for h in hits), ' n=',len(hits))
    else: print('   none')
