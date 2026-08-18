# -*- coding: utf-8 -*-
"""n+77：驗證 `docs/w4b-design-inputs.md` 之條目可回溯性。

🚨 該檔存在的理由就是「條目要能回溯到記錄」，故這件事必須是可執行的檢查，
不是寫在前言裡的承諾。本檔驗三件事：
  1. 條目編號無重複；
  2. 每個引用之 candidateId 都真的存在於判讀庫；
  3. 條目數與 candidateId 數各為多少（合併條目會使前者少於後者）。

⚠️ 本檔**不**驗證「主張句是否忠於判讀原文」——那需要人讀。
不落地任何文獻內容（n+48 內容制衛生）。

🚨 第 382 輪之教訓：條目編號樣式原寫死為 `[GDMSBKX]`，新增 P-／Q-／R-
三個類別後**它們完全不被檢查而檢查仍報綠燈**——即「樣式太窄造成假通過」，
本 lane 已登記之第七型缺陷。改為 `[A-Z]` 並加總數下限斷言，
**使「漏掉整個類別」會讓檢查亮紅燈而非靜默略過。**
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
ids = re.findall(r'^\| ([A-Z]-\d+) \|', t, re.M)
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

# 🚨 涵蓋斷言：以**不同的樣式**數「所有形如 <代號>-<數字> 的表格列」，
# 再與條目樣式所抓到的數量比對。兩個樣式必須不同——
# ⚠️ 本檔第一版用同一個樣式數兩次，於是恆等、永遠通過；
# 變異驗證（把 P-1 改成 PP-1）當場抓到它沒攔截。
rows_any = len(re.findall(r'^\|\s*[A-Za-z]{1,4}-\d+\s*\|', t, re.M))
assert rows_any == len(ids), (
    '🚨 表格中有 %d 列形如 代號-數字，但條目樣式只抓到 %d 條'
    '——代表有類別未被涵蓋' % (rows_any, len(ids)))
assert not dup, '🚨 條目編號重複：%s' % dup
assert not missing, '🚨 以下 candidateId 在判讀庫中查無：%s' % missing
print('✅ 編號無重複；✅ 所有 candidateId 皆可回溯')
print()
print('⚠️ 本檔未驗證主張句是否忠於判讀原文——那需要人讀，不能由樣式代勞。')
