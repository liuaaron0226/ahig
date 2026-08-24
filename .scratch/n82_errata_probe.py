# -*- coding: utf-8 -*-
"""n+82（一）(二)：錯標補正前的斷鏈實測。

🚨 裁定要求就地改 `.scratch/n68_tail_sample.json` 之 `anchor.source`。
本檔先測「就地改會發生什麼」，再決定怎麼改——因為若該產物之自我雜湊
涵蓋被改的欄位，改標籤就會把一個可自我驗證的凍結產物變成驗不過的產物。
⚠️ 那正是裁定想避免的傷害（稽核者誤判證據鏈斷裂），只是方向相反。

對每個含錯標之凍結產物，實測三件事：
  1. 記錄於檔內之自我雜湊欄位
  2. 原檔重算（去掉該雜湊欄位本身）→ 應相符，否則產物早已有問題
  3. 就地改標籤後重算 → 若不符，就地改即斷鏈

不採信任何自陳與裁定文字，全部現算（n+48 第二節、n+61）。
"""
import copy
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'ahig'))

from ahig.contracts.freeze import content_hash  # noqa: E402

SCRATCH = os.path.dirname(os.path.abspath(__file__))

# (檔名, 自我雜湊欄位, 錯標欄位路徑, 改後的值)
TARGETS = [
    ('n68_tail_sample.json', 'sampleHash',
     ('anchor', 'source'), 'content_hash(worksheet.json)'),
    ('n68_termination_evidence.json', 'terminationEvidenceHash',
     ('anchorNote',), '（測試用改寫）'),
    ('n49_sample.json', 'sampleHash',
     ('anchorNote',), '（測試用改寫）'),
]


def self_hash(doc, field):
    d = copy.deepcopy(doc)
    d.pop(field, None)
    return content_hash(d)


def set_path(doc, path, value):
    d = doc
    for k in path[:-1]:
        d = d[k]
    d[path[-1]] = value


rows = []
for name, hash_field, path, new_value in TARGETS:
    p = os.path.join(SCRATCH, name)
    if not os.path.exists(p):
        rows.append((name, 'MISSING', '', '', ''))
        continue
    doc = json.load(open(p, encoding='utf-8'))
    recorded = doc.get(hash_field)
    if recorded is None:
        # 自我雜湊不在頂層，改標籤不會動到它——需個別判定
        rows.append((name, 'NO-SELF-HASH', '(欄位 %s 不存在)' % hash_field, '', ''))
        continue
    before = self_hash(doc, hash_field)
    mutated = copy.deepcopy(doc)
    try:
        set_path(mutated, path, new_value)
    except (KeyError, TypeError):
        rows.append((name, 'NO-SUCH-FIELD', recorded[:22], before[:22], ''))
        continue
    after = self_hash(mutated, hash_field)
    verdict = 'BREAKS' if after != recorded else 'safe'
    rows.append((name, verdict, recorded[:22], before[:22], after[:22]))

print('檔案                              判定       記錄值                 原檔重算               改後重算')
print('-' * 118)
for name, verdict, rec, before, after in rows:
    print('%-33s %-10s %-22s %-22s %-22s' % (name, verdict, rec, before, after))
print()
print('BREAKS       = 就地改標籤會使該產物之自我雜湊驗不過 → 不得就地改，改立 errata')
print('safe         = 自我雜湊未涵蓋該欄位 → 可就地改')
print('NO-SELF-HASH = 頂層無該雜湊欄位，其完整性由他處引用保證 → 個別判定')
