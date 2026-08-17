import json, os, sys
from collections import Counter
os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score
RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
raw = Counter(op.values())

# post-ruling overlay is authoritative for decisions + ADR-0008 labels (coordinator b1bc147)
rc_path = OUT + '/post-ruling-reclassification.json'
n_over = 0
if os.path.exists(rc_path):
    rc = json.load(open(rc_path, encoding='utf-8'))
    seen = set()
    for e in rc['entries']:
        cid = e['candidateId']
        assert cid in op, 'reclass id not judged: ' + cid
        assert cid not in seen, 'duplicate in reclass: ' + cid
        assert op[cid] == e['originalOpinion'], 'originalOpinion mismatch: ' + cid
        seen.add(cid)
        op[cid] = e['effectiveDecision']
        n_over += 1

# 協調者第 n+40 輪選項（丙）：跳頁補判之 critical-harms 紀錄已篩畢（計入前置
# 條件），但暫不進 labels 序列——直接接入會把相距上百頁的紀錄接在一起，
# windowSize（尾端連續無命中長度）就不再是「連續」的。逐頁推進到該筆所在頁
# 時自動納回（依清單內之 page 與目前連續判畢頁數比對，不需人工介入）。
by_page = {}
for it in w['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
contiguous = 0
while all(c in op for c in by_page.get(contiguous + 1, [None])):
    contiguous += 1

exc_path = OUT + '/p-score-sequence-exclusions.json'
excluded, reintegrated = set(), []
if os.path.exists(exc_path):
    for e in json.load(open(exc_path, encoding='utf-8'))['entries']:
        (reintegrated.append(e['candidateId']) if e['page'] <= contiguous
         else excluded.add(e['candidateId']))

labels = [1 if op[it['candidateId']] in ('advance','unclear') else 0
          for it in w['items']
          if it['candidateId'] in op and it['candidateId'] not in excluded]
print('raw      ', dict(raw), 'judged', len(op))
print('overlay  ', n_over, 'entries applied')
print('effective', dict(Counter(op.values())))
print(f'p 值序列排除中 {len(excluded)} 筆（已納回 {len(reintegrated)}）'
      f'；連續判畢至 page {contiguous}；序列長度 {len(labels)}')
print(json.dumps(p_score(labels, w['itemCount']), ensure_ascii=False, default=str))
