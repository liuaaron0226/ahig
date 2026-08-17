import json, io, sys
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
want = sys.argv[1:]
buf = []
for it in w['items']:
    if any(k in it['candidateId'] for k in want):
        buf.append('=== %s' % it['candidateId'])
        buf.append('TITLE: %s' % it.get('title'))
        buf.append('ABS: %s' % (it.get('abstract') or '')[:2000])
        buf.append('')
io.open('.scratch/look.txt', 'w', encoding='utf-8').write('\n'.join(buf))
print('found', len(buf) // 4)
