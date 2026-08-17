"""n+47：以有效 advance 為清單產生 W4a-1 全文取得批次輸入。

判定沿用 term.py 的同一條規則：judgements.json 為底、
post-ruling-reclassification.json 覆蓋層 (effectiveDecision) 為準。
覆蓋層之外不作任何自行推斷。
"""
import json, os

RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'

w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}

rc_path = OUT + '/post-ruling-reclassification.json'
if os.path.exists(rc_path):
    for e in json.load(open(rc_path, encoding='utf-8'))['entries']:
        cid = e['candidateId']
        assert op[cid] == e['originalOpinion'], 'originalOpinion mismatch: ' + cid
        op[cid] = e['effectiveDecision']

# worksheet 順序（= 排序器名次）保留，讓取得順序與相關性排序一致
adv = [it['candidateId'] for it in w['items']
       if op.get(it['candidateId']) == 'advance']

assert len(adv) == len(set(adv)), 'duplicate candidateId in advance list'

pool = json.load(open(RUN + '/candidate-pool/candidates.json', encoding='utf-8'))
known = {c['candidateId'] for c in pool}
missing = [c for c in adv if c not in known]
assert not missing, 'advance id absent from candidate pool: %r' % missing[:3]

json.dump(adv, open('.scratch/adv_ids.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('advance', len(adv), 'all-in-pool', not missing)
