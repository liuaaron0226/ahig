import json, io
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
item = {it['candidateId']: it for it in w['items']}
ids = ['ad5277cd','ac0acc92','9969a3d8','81e72b2c','cad305ad','b52d294c','02ad3c6b']
buf = []
for e in d['entries']:
    cid = e['candidateId']
    if not any(k in cid for k in ids):
        continue
    it = item.get(cid, {})
    buf.append('=== %s' % cid)
    buf.append('T: %s' % it.get('title'))
    buf.append('MY REASON: %s' % e['reason'])
    buf.append('ABS: %s' % (it.get('abstract') or '(blank)')[:950])
    buf.append('')
io.open('.scratch/sweep6.txt', 'w', encoding='utf-8').write('\n'.join(buf))
print('dumped', len(buf)//5)
