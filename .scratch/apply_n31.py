# -*- coding: utf-8 -*-
import json, io
OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs/'
       r'b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
p = OUT + '/post-ruling-reclassification.json'
d = json.load(open(p, encoding='utf-8'))
jud = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in jud['entries']}

targets = {
    '5274170fa317': '四臂 PP/CP/PC/CC、PC vs PP 為乾淨對比、命中 TT completion time。',
    '74d57a4efafd': 'recreationally trained 跑者。',
    '7056ad018b47': 'recreationally trained 女性。',
}
NOTE = ('裁定 n+31：`recreationally trained` 介於裁定 62 兩桶之間，語意浮動，'
        '**維持 unclear 送全文**（全文之 VO2max／訓練量數據定案）。'
        '本筆先前依裁定 62 覆蓋為 exclude 之處置已依 n+31 撤回，'
        'effective 回復為 unclear。')

hit = 0
for e in d['entries']:
    cid = e['candidateId']
    for k, extra in targets.items():
        if cid.endswith(k):
            assert e['effectiveDecision'] == 'exclude', 'unexpected state: ' + cid
            assert op[cid] == 'unclear', 'raw opinion changed: ' + cid
            e['effectiveDecision'] = 'unclear'
            e['ruling'] = 'n+31 (supersedes 62)'
            e['tag'] = 'population-recreationally-trained'
            e['note'] = NOTE + ' ' + extra
            hit += 1
assert hit == 3, 'expected 3 updates, got %d' % hit
d['producedAtJudgedCount'] = len(jud['entries'])
io.open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2))
print('reverted to unclear:', hit, '| overlay entries:', len(d['entries']))
