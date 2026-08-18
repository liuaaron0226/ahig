# -*- coding: utf-8 -*-
"""n+77：驗證 `docs/w4b-design-inputs.md` 之條目可回溯性。

🚨 該檔存在的理由就是「條目要能回溯到記錄」，故這件事必須是可執行的檢查，
不是寫在前言裡的承諾。本檔驗三件事：
  1. 條目編號無重複；
  2. 每個引用之 candidateId 都真的存在於判讀庫；
  3. 條目數與 candidateId 數各為多少（合併條目會使前者少於後者）。

⚠️ 本檔**不**驗證「主張句是否忠於判讀原文」——那需要人讀。
不落地任何文獻內容（n+48 內容制衛生）。
"""
import collections
import io
import json
import re

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run')
E = json.load(io.open(ROOT + '/standard-full-screen-pass-1/judgements.json',
                      encoding='utf-8'))['entries']
known = {x['candidateId'][-8:] for x in E}

t = io.open('docs/w4b-design-inputs.md', encoding='utf-8').read()
ids = re.findall(r'^\| ([GDMSBKX]-\d+) \|', t, re.M)
cids = set(re.findall(r'`([0-9a-f]{8})`', t))

dup = sorted({i for i in ids if ids.count(i) > 1})
missing = sorted(cids - known)

print('條目總數           %d' % len(ids))
print('引用 candidateId   %d' % len(cids))
print('可回溯至判讀庫     %d' % len(cids & known))
print()
c = collections.Counter(i.split('-')[0] for i in ids)
for k in sorted(c):
    print('  %s  %2d 條' % (k, c[k]))
print()

assert not dup, '🚨 條目編號重複：%s' % dup
assert not missing, '🚨 以下 candidateId 在判讀庫中查無：%s' % missing
print('✅ 編號無重複；✅ 所有 candidateId 皆可回溯')
print()
print('⚠️ 本檔未驗證主張句是否忠於判讀原文——那需要人讀，不能由樣式代勞。')
