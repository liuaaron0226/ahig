# -*- coding: utf-8 -*-
"""n+78：執行 `3d617443` 之改判（unclear → exclude）。

🚨 協調者於 n+78 逐位重算後明示授權。依 n+62 三段式，判準（n+77 第五節，
文獻型態軸）先於量測（Δwindow +86），量測後停手請示，本輪始執行。

⚠️ 本檔會實際寫入 overlay，故先驗三件事再寫：
  1. 目標記錄目前確為 unclear（不是已被改過）；
  2. 該筆尚未列於 overlay（不重複寫入）；
  3. 改判前後之數字與協調者所裁者逐位相符——**不符即中止**。

寫入後不自行宣告終止（n+57）。
"""
import io
import json
import os
import sys
from datetime import datetime, timezone

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import p_score  # noqa: E402

RUN = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
       'b11-exogenous-cho-endurance/b11-full-run')
OUT = RUN + '/standard-full-screen-pass-1'
OVERLAY = OUT + '/post-ruling-reclassification.json'

W = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
J = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in J['entries']}
raw_op = dict(op)

ov = json.load(io.open(OVERLAY, encoding='utf-8'))
for e in ov['entries']:
    op[e['candidateId']] = e['effectiveDecision']
rs_path = OUT + '/post-ruling-abstract-rescreen.json'
if os.path.exists(rs_path):
    for e in json.load(io.open(rs_path, encoding='utf-8'))['entries']:
        op[e['candidateId']] = e['effectiveDecision']

TARGET = [c for c in op if c.endswith('3d617443')]
assert len(TARGET) == 1, '目標 candidateId 不唯一：%s' % TARGET
TARGET = TARGET[0]

# 驗 1：目前確為 unclear
assert op[TARGET] == 'unclear', '目前效力值非 unclear，而是 %s' % op[TARGET]
assert raw_op[TARGET] == 'unclear', 'judgements.json 之 opinion 非 unclear'
# 驗 2：尚未列於 overlay
assert not any(e['candidateId'] == TARGET for e in ov['entries']), \
    '該筆已列於 overlay，不重複寫入'

item = [it for it in W['items'] if it['candidateId'] == TARGET][0]

by_page = {}
for it in W['items']:
    by_page.setdefault(it['page'], []).append(it['candidateId'])
contiguous = 0
while all(c in op for c in by_page.get(contiguous + 1, [None])):
    contiguous += 1
skip = set()
for e in json.load(io.open(OUT + '/p-score-sequence-exclusions.json',
                           encoding='utf-8'))['entries']:
    if (e.get('state', 'pending-reintegration') == 'out-of-sequence-permanent'
            or e['page'] > contiguous):
        skip.add(e['candidateId'])


def labels(o):
    return [1 if o[it['candidateId']] in ('advance', 'unclear') else 0
            for it in W['items']
            if it['candidateId'] in o and it['candidateId'] not in skip]


before = p_score(labels(op), W['itemCount'])
after_op = dict(op)
after_op[TARGET] = 'exclude'
after = p_score(labels(after_op), W['itemCount'])

# 驗 3：與協調者所裁之數字逐位相符
EXPECT = {'before_window': 115, 'before_p': 0.076292,
          'after_window': 201, 'after_p': 0.012405}
assert before['windowSize'] == EXPECT['before_window'], before['windowSize']
assert after['windowSize'] == EXPECT['after_window'], after['windowSize']
assert abs(before['pScore'] - EXPECT['before_p']) < 5e-7, before['pScore']
assert abs(after['pScore'] - EXPECT['after_p']) < 5e-7, after['pScore']
print('✅ 三項前置驗證通過；數字與 n+78 所裁逐位相符')
print('   改判前 window %d  pScore %.6f' % (before['windowSize'], before['pScore']))
print('   改判後 window %d  pScore %.6f' % (after['windowSize'], after['pScore']))
print()

entry = {
    'candidateId': TARGET,
    'seq': item.get('seq'),
    'page': item['page'],
    'originalOpinion': 'unclear',
    'effectiveDecision': 'exclude',
    'ruling': 'n+77 (五) / n+78 (二)',
    'basis': 'publication-type axis: consensus statement is secondary '
             'literature, not a primary study. Abstract checked: reports no '
             'primary data, so the n+77 proviso does not apply.',
    'tags': ['review-source'],
    'note': (
        'Order per n+62: criterion FIRST (n+77 ruled it a round before its '
        'sequence position was known), impact measured second (window '
        '115->201, pScore 0.076292->0.012405, crossing alpha=0.05), then '
        'halted for authorisation because the impact was non-zero and '
        'favoured stopping. Authorised explicitly in n+78 after the '
        'coordinator recomputed both figures independently. This is the '
        'largest single-record impact in the lane (delta window +86), '
        'because the record was the last hit in the sequence. Executing it '
        'starts the n+57 termination procedure; frozen evidence carries '
        'triggerCause naming this reclassification. The original judgement '
        'cited consistency with 104852c6, which n+77 later ruled is not a '
        'reason -- that citation is superseded, not relied upon here.'),
    'appliedAtJudgedCount': len(J['entries']),
    'appliedAtUtc': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
}
ov['entries'].append(entry)
io.open(OVERLAY, 'w', encoding='utf-8').write(
    json.dumps(ov, ensure_ascii=False, indent=1))
print('✅ overlay 已寫入，現有 %d 筆' % len(ov['entries']))
print('⚠️ 依 n+57，本執行室不宣告終止；下一步為六步程序之凍結證據。')
