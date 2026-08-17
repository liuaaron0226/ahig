# -*- coding: utf-8 -*-
import json, io, os
OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs/'
       r'b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
p = OUT + '/post-ruling-reclassification.json'
d = json.load(open(p, encoding='utf-8'))
jud = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in jud['entries']}
seen = {e['candidateId'] for e in d['entries']}

new = [
 {"candidateId": "ahig:candidate:publication:7b096a34371479e274697103",
  "originalOpinion": "unclear", "effectiveDecision": "exclude",
  "ruling": "n+30", "tag": "single-arm-uncontrolled",
  "note": ("題摘明示單臂：58 名 well-trained 男性全體同一處置（ad libitum 飲用含咖啡因之 "
           "7% CHO-電解質溶液），摘要通篇無任何比較條件、無隨機、無交叉敘述，"
           "研究問題為運動後尿液咖啡因濃度是否低於禁藥標準。符合裁定 n+30 之「明示」要件。")},
 {"candidateId": "ahig:candidate:publication:62718583a0248aeebb4eb6ab",
  "originalOpinion": "unclear", "effectiveDecision": "exclude",
  "ruling": "n+30", "tag": "single-arm-uncontrolled",
  "note": ("題摘明示單臂：11 名 well-trained 車手連續 4 日各 3 小時，全程單一補給方案"
           "（CHO 約 50 g/h），摘要唯一比較為「第 1 日 vs 第 2-4 日」之受試者內時間序列，"
           "無並行或交叉之比較條件。符合裁定 n+30 之「明示」要件。")},
]

for e in new:
    cid = e['candidateId']
    assert cid in op, 'not judged: ' + cid
    assert cid not in seen, 'already overlaid: ' + cid
    assert op[cid] == e['originalOpinion'], 'originalOpinion mismatch: ' + cid
    d['entries'].append(e)

d['producedAtJudgedCount'] = len(jud['entries'])
io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2))
print('overlay entries now', len(d['entries']))
