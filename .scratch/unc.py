import json, io
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
title = {}
for it in w['items']:
    title[it['candidateId']] = (it.get('title') or '')[:90]
buf = []
n = 0
for e in d['entries']:
    if e['opinion'] != 'unclear':
        continue
    n += 1
    buf.append('%d| %s' % (n, e['candidateId']))
    buf.append('   T: %s' % title.get(e['candidateId'], '?'))
    buf.append('   R: %s' % e['reason'])
    buf.append('')
io.open('.scratch/unc.txt', 'w', encoding='utf-8').write('\n'.join(buf))
print('unclear', n)
