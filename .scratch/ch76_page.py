import json, io, sys
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
w=json.loads((ROOT/'standard-full-screen-pass-1'/'worksheet.json').read_text(encoding='utf-8'))
items={it['candidateId']:it for it in w['items']}
lst=json.loads(Path('.scratch/ch76_list.json').read_text(encoding='utf-8'))['candidateIds']
lo,hi=int(sys.argv[1]),int(sys.argv[2])
buf=[]
n=0
for c in lst:
    it=items[c]
    if not (lo<=it['seq']<=hi): continue
    n+=1
    buf.append(f"--- seq{it['seq']} p{it['page']} {c}")
    buf.append(f"Y:{it.get('publicationYear')} T:{it.get('publicationTypes')}")
    buf.append(f"TITLE: {it.get('title')}")
    buf.append(f"ABS: {(it.get('abstract') or '(none)')[:1250]}")
    buf.append("")
io.open('.scratch/ch76_page.txt','w',encoding='utf-8').write('\n'.join(buf))
print('items',n,'seq range',lo,hi)
