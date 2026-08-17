"""Build the critical-harms sweep list per coordinator ruling n+38 item 1."""
import json, collections
from pathlib import Path
ROOT=Path(r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run')
q=json.loads((ROOT/'screening-queue'/'queue.json').read_text(encoding='utf-8'))
ch=[it for it in q if 'critical-harms-signal' in (it.get('flags') or [])]

std=json.loads((ROOT/'standard-full-screen-pass-1'/'judgements.json').read_text(encoding='utf-8'))
judged={e['candidateId'] for e in std['entries']}
for d in ['safety-full-screen-pass-1','safety-full-screen-pass-2']:
    p=ROOT/d/'judgements.json'
    if p.exists():
        doc=json.loads(p.read_text(encoding='utf-8'))
        judged |= {e['candidateId'] for e in (doc['entries'] if isinstance(doc,dict) else doc)}

un=[it for it in ch if it['candidateId'] not in judged]
non_std=[it for it in un if it['screeningLane']!='standard-screening']
in_std=[it for it in un if it['screeningLane']=='standard-screening']
print(f'unjudged critical-harms: {len(un)}  non-standard: {len(non_std)}  standard-lane: {len(in_std)}')
print('non-standard by lane:', collections.Counter(it["screeningLane"] for it in non_std))

# The standard-lane ones sit in the standard worksheet ahead of us and will be
# reached by ordinary paging; the ruling targets the 116 that no lane covers.
w=json.loads((ROOT/'standard-full-screen-pass-1'/'worksheet.json').read_text(encoding='utf-8'))
inwb={it['candidateId'] for it in w['items']}
print('of the standard-lane ones, in standard worksheet:', sum(1 for it in in_std if it['candidateId'] in inwb))
print('of the non-standard ones, in standard worksheet:', sum(1 for it in non_std if it['candidateId'] in inwb))

ids=[it['candidateId'] for it in non_std]
assert len(ids)==len(set(ids))
out={'candidateIds': ids,
     'note': '協調者第 n+38 輪裁定第 1 項：critical-harms-signal 且未經任何 lane 判讀者，'
             '排除 standard lane 內既有頁序可及者（81 筆，續跑主篩即會判到）。'}
Path('.scratch/ch_sweep_list.json').write_text(json.dumps(out,ensure_ascii=False,indent=1),encoding='utf-8')
print('wrote .scratch/ch_sweep_list.json with', len(ids), 'ids')
