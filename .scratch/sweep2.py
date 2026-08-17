import json, io, os, re
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
rc = json.load(open(OUT + '/post-ruling-reclassification.json', encoding='utf-8'))
overlaid = {e['candidateId'] for e in rc['entries']}
item = {it['candidateId']: it for it in w['items']}
ids = ['bd4713f8','7cdbff76','bf02dc53','493c4c39','fdee2fcd','2744f70d','ef3bafff','7a743b59',
       '6a751c91','5a3a3a6c','a5bdf5ad','27a3a98f','d5d8b4e2','fbfbc4c4','60c040a2','ab24bad3',
       '74697103','eefd1d10','bb4eb6ab','12db0f5e']
buf = []
for e in d['entries']:
    cid = e['candidateId']
    if not any(k in cid for k in ids) or cid in overlaid or e['opinion'] != 'unclear':
        continue
    it = item.get(cid, {})
    buf.append('=== %s' % cid)
    buf.append('T: %s' % it.get('title'))
    buf.append('MY REASON: %s' % e['reason'])
    buf.append('ABS: %s' % (it.get('abstract') or '')[:1100])
    buf.append('')
io.open('.scratch/sweep2.txt', 'w', encoding='utf-8').write('\n'.join(buf))
print('dumped', len(buf)//5)
