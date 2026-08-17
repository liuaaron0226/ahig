import json, re
RUN='C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1'
w=json.load(open(RUN+'/worksheet.json',encoding='utf-8'))
j=json.load(open(RUN+'/judgements.json',encoding='utf-8'))
ov=json.load(open(RUN+'/post-ruling-reclassification.json',encoding='utf-8'))
items={it['candidateId']:it for it in w['items']}
op={e['candidateId']:e for e in j['entries']}
ovm={e['candidateId']:e for e in ov['entries']}
eff=lambda c: ovm.get(c,{}).get('effectiveDecision', op[c]['opinion']) if c in op else 'UNJUDGED'
print('--- every record whose abstract has "30 experienced marathon runners" ---')
for c,it in items.items():
    a=(it.get('abstract') or '')
    if re.search(r'[Tt]hirty experienced marathon runners|30 experienced marathon runners', a):
        print('  p%-4d seq%-5d %s  %-9s | %s' % (it['page'], it['seq'], c[-8:], eff(c), (it.get('title') or '')[:78]))
print()
print('--- c28ed3a2 ---')
for c,it in items.items():
    if 'c28ed3a2' in c:
        print('  p%d %s %s' % (it['page'], eff(c), it.get('title')))
        print('  ', (it.get('abstract') or '')[:320])
