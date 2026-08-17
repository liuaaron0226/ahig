import json, collections
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
q=json.loads((ROOT/'screening-queue'/'queue.json').read_text(encoding='utf-8'))
print('queue type', type(q), list(q.keys()) if isinstance(q,dict) else len(q))
items = q['items'] if isinstance(q,dict) and 'items' in q else q
print('n items', len(items))
print('sample keys', sorted(items[0].keys()))
print(json.dumps(items[0], ensure_ascii=False)[:700])
fl=collections.Counter()
for it in items:
    for f in (it.get('flags') or []):
        fl[f]+=1
print('FLAGS:'); [print('  ',v,k) for k,v in fl.most_common()]
