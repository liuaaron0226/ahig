import json, io, sys
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/critical-harms-sweep'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
judged = {e['candidateId'] for e in (d.get('entries') or [])}
lo, hi = int(sys.argv[1]), int(sys.argv[2])
items = [it for it in w['items'] if lo <= it['page'] <= hi and it['candidateId'] not in judged]
buf = []
for it in items:
    buf.append(f"--- seq{it['seq']} p{it['page']} {it['candidateId']}")
    buf.append(f"Y:{it.get('publicationYear')} T:{it.get('publicationTypes')}")
    buf.append(f"TITLE: {it.get('title')}")
    buf.append(f"ABS: {(it.get('abstract') or '')[:1300]}")
    buf.append("")
io.open('.scratch/ch_page.txt', 'w', encoding='utf-8').write('\n'.join(buf))
print('items', len(items), 'pages', lo, hi)
