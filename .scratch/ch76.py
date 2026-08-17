import json, collections
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
q=json.loads((ROOT/'screening-queue'/'queue.json').read_text(encoding='utf-8'))
judged=set()
for d in ['standard-full-screen-pass-1','safety-full-screen-pass-1','safety-full-screen-pass-2',
          'critical-harms-sweep','critical-harms-sweep-orphans']:
    p=ROOT/d/'judgements.json'
    if p.exists():
        judged |= {e['candidateId'] for e in json.loads(p.read_text(encoding='utf-8'))['entries']}
ch=[it for it in q if 'critical-harms-signal' in (it.get('flags') or [])]
un=[it for it in ch if it['candidateId'] not in judged]
w=json.loads((ROOT/'standard-full-screen-pass-1'/'worksheet.json').read_text(encoding='utf-8'))
pg={it['candidateId']:it['page'] for it in w['items']}
seq={it['candidateId']:it['seq'] for it in w['items']}
print('critical-harms total', len(ch), 'unjudged now', len(un))
assert all(it['candidateId'] in pg for it in un), 'some not in standard worksheet'
pages=collections.Counter(pg[it['candidateId']] for it in un)
print('pages:', sorted(pages.items())[:10], '...', 'distinct pages', len(pages), 'min', min(pages), 'max', max(pages))
ids=sorted((seq[it['candidateId']], it['candidateId']) for it in un)
json.dump({'candidateIds':[c for _,c in ids],
           'note':'協調者第 n+40 輪裁定：跳頁補判之 critical-harms-signal 紀錄，'
                  '暫時排除於 ADR-0008 p 值 labels 序列，逐頁推進到該頁時自動納回。'},
          open('.scratch/ch76_list.json','w',encoding='utf-8'), ensure_ascii=False, indent=1)
print('wrote .scratch/ch76_list.json:', len(ids))
