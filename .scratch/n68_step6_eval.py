# -*- coding: utf-8 -*-
"""n+57 第二節【第 6 步】：以生產程式評估尾端抽驗，**只回報，不宣告終止**。

🚨 n+57 第二節第 6 步明定：**執行室不得自行宣告終止成立或失效**，
本檔輸出的是 `evaluate_tail_spot_check` 的回傳值與命中內容，
終止之裁定屬協調者，且須先送擁有者。

⚠️ `decisions` 之鍵為**完整 candidateId**，非後 8 碼——
判讀檔以後 8 碼為鍵，故本檔先由樣本之 `candidateIds` 建立
後 8 碼 → 完整 id 之對照，並 assert 對照無碰撞（第 5 型缺陷：子字串碰撞）。

本檔看得到：抽驗之判定結果、命中清單、判讀分布。
本檔看不到：判讀內容是否正確（那要逐筆讀，已於第 5 步做過）。
"""
import glob
import io
import json
import sys

sys.path.insert(0, 'ahig')
from ahig.search import statistical_termination as st  # noqa: E402

s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
sample = s['sample']
ids = sample['candidateIds']

short2full = {}
for cid in ids:
    k = cid[-8:]
    assert k not in short2full, ('後 8 碼碰撞', k)
    short2full[k] = cid
assert len(short2full) == len(ids) == 200

decisions = {}
files = sorted(glob.glob('.scratch/n68_tail_dec_*.json'))
for p in files:
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        assert k in short2full, ('判讀之鍵不在樣本中', k, p)
        decisions[short2full[k]] = v[0]
print('涵蓋自報：判讀檔 %d 個，回填 %d/%d 筆'
      % (len(files), len(decisions), len(ids)))

res = st.evaluate_tail_spot_check(sample, decisions)
print()
print(json.dumps(res, ensure_ascii=False, indent=1))

print()
import collections  # noqa: E402
print('判讀分布：%s' % dict(collections.Counter(decisions.values())))
print()
print('命中 %d 筆：' % len(res['relevantOrUnclearFound']))
detail = {}
for p in files:
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        detail[short2full[k]] = v
for cid in res['relevantOrUnclearFound']:
    op, reason = detail[cid]
    pos = ids.index(cid)
    print('  [%d] %s  %s' % (pos, cid[-8:], op))
    print('      %s' % reason[:200])

out = {
    'documentType': 'tail-spot-check-report',
    'note': ('執行室回報，**不含終止裁定**——n+57 二 6：'
             '終止之成立或失效由協調者裁定並先送擁有者。'),
    # n+67：順序證據須寫在內容裡（git 不保留 mtime）。
    # 本檔讀的是第 3 步之樣本產物，故記其 sampleHash，
    # 並轉錄該產物自帶之 readsStep1／readsStep2，使鏈條從第 1 步串到本步。
    'readsStep3': {
        'sampleHash': s['sampleHash'],
        'itsReadsStep1': s['readsStep1'],
        'itsReadsStep2': s['readsStep2'],
    },
    'anchorNote': s['anchor']['note'],
    'result': res,
    'decisionCounts': dict(collections.Counter(decisions.values())),
}
io.open('.scratch/n68_tail_result.json', 'w', encoding='utf-8').write(
    json.dumps(out, ensure_ascii=False, indent=1))
print()
print('-> .scratch/n68_tail_result.json')
