# -*- coding: utf-8 -*-
"""n+57 第二節【第 3 步】：抽取 200 筆尾端抽驗樣本。

⚠️ **種子錨定用 worksheet 之 SHA-256**（本 lane 無 `queueHash`，
依 n+51 已核准之等效替代），**並在產物中明載所用錨定值，
不得逕稱 queueHash**（n+57 第 3 步原文）。

⚠️ **順序證據寫進內容**（n+67 四）：記錄所讀入之第 1、2 步雜湊。
"""
import io
import json
import os
import sys
from datetime import datetime, timezone

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import (  # noqa: E402
    content_hash, draw_tail_spot_check)

RUN = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = RUN + '/standard-full-screen-pass-1'

step1 = json.load(io.open('.scratch/n68_termination_evidence.json',
                          encoding='utf-8'))
step2 = json.load(io.open('.scratch/n68_preconditions.json',
                          encoding='utf-8'))
assert step2['allPass'], '第 2 步未全數通過，不得進入第 3 步'

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
judged = {e['candidateId'] for e in d['entries']}
not_screened = [it['candidateId'] for it in w['items']
                if it['candidateId'] not in judged]

assert len(not_screened) == step1['counts']['notScreenedCount'], \
    ('未判筆數與第 1 步不符', len(not_screened),
     step1['counts']['notScreenedCount'])

anchor = step1['anchors']['worksheetSha256']
sample = draw_tail_spot_check(not_screened, queue_hash=anchor, n=200)

out = {
    'schemaVersion': 1,
    'documentType': 'termination-tail-spot-check-sample',
    'step': 'n+57 section 2 step 3 (draw 200-record tail spot check)',
    'producedAt': datetime.now(timezone.utc).isoformat(),
    'readsStep1': {'terminationEvidenceHash': step1['terminationEvidenceHash']},
    'readsStep2': {'preconditionsCheckHash': step2['preconditionsCheckHash']},
    'anchor': {
        'value': anchor,
        'source': 'worksheet.json 之 SHA-256',
        'note': ('⚠️ 本 lane 無 queueHash。依 n+51 核准之等效替代，'
                 '以 worksheet 雜湊為種子錨定。**此值不是 queueHash**，'
                 '報告中不得如此稱呼（n+57 第 3 步）。'),
    },
    'notScreenedCount': len(not_screened),
    'sample': sample,
}
out['sampleHash'] = content_hash(out)
json.dump(out, io.open('.scratch/n68_tail_sample.json', 'w',
                       encoding='utf-8'), ensure_ascii=False, indent=1)

# ⚠️ 第一版猜欄名 `sampledIds`，而生產程式用的是
#    `candidateIds`，於是回報「抽取 0 筆」——**那是假的**。
# 🚨 即 n+65 所記之第六種缺陷（猜欄名）又發生一次：
#    它不報錯，只安靜地給一個看似合理的數字。
#    改為**斷言鍵名存在**，而非以 or 鏈向下採。
assert 'candidateIds' in sample, sorted(sample.keys())
ids = sample['candidateIds']
assert len(ids) == sample['sampleSize'] == 200, (len(ids), sample['sampleSize'])
print('=' * 66)
print('n+57 第二節【第 3 步】尾端抽驗樣本已抽取並落盤')
print('=' * 66)
print('  未判母體：%d 筆' % len(not_screened))
print('  抽取筆數：%d' % len(ids))
print('  錨定值：%s' % anchor)
print('  ⚠️ 上列為 worksheet 雜湊，**不是 queueHash**')
print('  sample keys：%s' % sorted(sample.keys()))
print('  產物：.scratch/n68_tail_sample.json')
print('  sampleHash：%s' % out['sampleHash'])
