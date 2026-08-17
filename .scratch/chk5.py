import json, re
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
items={it['candidateId']:it for it in w['items']}
op={e['candidateId']:e for e in j['entries']}
for p in [r'`exercise` 詞族誤命中第 (\d+) 筆', r'`endurance` 詞族誤命中第 (\d+) 筆',
          r'`glucose` 詞族誤命中第 (\d+) 筆', r'代謝性肌[^。]{0,20}?(\d+)\s*筆',
          r'個案研究[^。]{0,20}?(\d+)\s*筆', r'第(?:三|3)型[^。]{0,20}?(\d+)\s*例']:
    hits=[(int(m.group(1)), e['candidateId'][-8:]) for e in j['entries'] for m in re.finditer(p,e['reason'])]
    print(p, '->', hits[-1] if hits else None, 'max', max([h[0] for h in hits]) if hits else None)
print()
print('Historical Article records & pages:')
for c,it in items.items():
    if 'Historical Article' in (it.get('publicationTypes') or []):
        print('  p%-4d %s judged=%s | %s' % (it['page'], c[-8:], c in op, (it.get('title') or '')[:70]))
print()
print('4fd3e61c page/seq:', [(it['page'],it['seq']) for c,it in items.items() if '4fd3e61c' in c])
print('cluster pages:', [(k, items[c]['page'], items[c]['seq']) for k in ['090bc24d','6827b1a3','a6ae355c','cafe9ec5'] for c in items if k in c])
