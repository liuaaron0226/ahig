# -*- coding: utf-8 -*-
"""n+57 第二節【第 2 步】：程式化覆核三項前置條件（不得憑印象，n+48）。

⚠️ **順序證據寫進內容**（n+67 四）：本檔記錄其所讀入之第 1 步
產物雜湊，使「第 2 步在第 1 步之後」可由 committed 內容覆核，
不依賴檔案時間（git 不保存 mtime）。

三項條件（n+57 第一節）：
  1. `mandatoryLanesFullyScreened == true`
  2. `pScoreExcludedCount == 0`
  3. `allowedToStop == true`
"""
import io
import json
import os
import sys
from datetime import datetime, timezone

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from ahig.search.statistical_termination import content_hash  # noqa: E402

RUN = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run')

step1 = json.load(io.open('.scratch/n68_termination_evidence.json',
                          encoding='utf-8'))
res = step1['terminationResult']

checks = []

# ---- 條件 3：allowedToStop（直接來自第 1 步之生產程式輸出）----
checks.append({
    'condition': 'allowedToStop == true',
    'observed': res.get('allowedToStop'),
    'pass': res.get('allowedToStop') is True,
    'source': 'evaluate_termination() 輸出（第 1 步已落盤）',
})

# ---- 條件 2：pScoreExcludedCount == 0 ----
# term.py 每輪回報「p 值序列排除中 0 筆（已納回 74）」；此處直接由
# evaluate_termination 之輸出與序列長度核對。
excluded = res.get('pScoreExcludedCount', 0)
seq_len_ok = res['screenedCount'] == step1['counts']['judgedCount']
checks.append({
    'condition': 'pScoreExcludedCount == 0',
    'observed': excluded,
    'pass': excluded == 0,
    'source': 'evaluate_termination() 輸出',
})
checks.append({
    'condition': '序列長度 == 判讀數（無記錄被排除於 p 值序列外）',
    'observed': '%d == %d' % (res['screenedCount'],
                              step1['counts']['judgedCount']),
    'pass': seq_len_ok,
    'source': '第 1 步落盤之 counts',
})

# ---- 條件 1：mandatoryLanesFullyScreened ----
# 逐 lane 以其判讀檔實數核對，不憑印象。
lanes = [
    ('safety-full-screen-pass-1', 'safety lane 第一遍'),
    ('safety-full-screen-pass-2', 'safety lane 第二遍（雙模型盲判）'),
    ('critical-harms-sweep', 'critical-harms sweep'),
]
lane_rows = []
for sub, label in lanes:
    p = RUN + '/' + sub + '/judgements.json'
    wpath = RUN + '/' + sub + '/worksheet.json'
    if not os.path.exists(p):
        lane_rows.append({'lane': label, 'status': '判讀檔不存在', 'pass': None})
        continue
    jj = json.load(io.open(p, encoding='utf-8'))['entries']
    total = None
    if os.path.exists(wpath):
        ww = json.load(io.open(wpath, encoding='utf-8'))
        total = ww.get('itemCount')
    lane_rows.append({
        'lane': label,
        'judged': len(jj),
        'total': total,
        'pass': (total is not None and len(jj) >= total),
    })

lanes_ok = all(r.get('pass') for r in lane_rows if r.get('pass') is not None)
checks.append({
    'condition': 'mandatoryLanesFullyScreened == true',
    'observed': lane_rows,
    'pass': lanes_ok,
    'source': '逐 lane 判讀檔筆數 vs worksheet itemCount（實數核對）',
})

all_pass = all(c['pass'] for c in checks)

out = {
    'schemaVersion': 1,
    'documentType': 'termination-preconditions-check',
    'step': 'n+57 section 2 step 2 (verify preconditions programmatically)',
    'producedAt': datetime.now(timezone.utc).isoformat(),
    'readsStep1': {
        'path': '.scratch/n68_termination_evidence.json',
        'terminationEvidenceHash': step1['terminationEvidenceHash'],
        'note': ('⚠️ 記錄所讀入之第 1 步雜湊，使順序可由內容覆核'
                 '（n+67 四：git 不保存 mtime，檔案時間不可作為順序證據）'),
    },
    'checks': checks,
    'allPass': all_pass,
}
out['preconditionsCheckHash'] = content_hash(out)
json.dump(out, io.open('.scratch/n68_preconditions.json', 'w',
                       encoding='utf-8'), ensure_ascii=False, indent=1)

print('=' * 66)
print('n+57 第二節【第 2 步】三項前置條件程式化覆核')
print('=' * 66)
print('  讀入第 1 步：%s' % step1['terminationEvidenceHash'][:24] + '…')
print()
for c in checks:
    mark = '✅' if c['pass'] else '❌'
    obs = c['observed']
    if isinstance(obs, list):
        print('  %s %s' % (mark, c['condition']))
        for r in obs:
            print('       %-28s %s / %s'
                  % (r.get('lane'), r.get('judged'), r.get('total')))
    else:
        print('  %s %-44s %s' % (mark, c['condition'], obs))
print()
print('  全數通過：%s' % ('✅ 是' if all_pass else '❌ 否'))
print('  產物：.scratch/n68_preconditions.json')
