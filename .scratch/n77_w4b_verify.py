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

# 🚨 檔頭自述之數字必須與實測一致。
# ⚠️ 第 383 輪教訓：檔頭停在 74／82 而實際已 153／179，且我改正時又手打成 154。
# **檔頭是每輪都要手動同步的欄位，正因如此它必須被檢查，而不是靠記得改。**
m = re.search(r'本檔現有 (\d+) 條、引用 (\d+) 個', t)
assert m, '🚨 檔頭之自述句不見了——它是本檔對外宣稱的規模，不得移除'
assert int(m.group(1)) == len(ids), (
    '🚨 檔頭自述 %s 條，實測 %d 條' % (m.group(1), len(ids)))
assert int(m.group(2)) == len(cids), (
    '🚨 檔頭自述引用 %s 個 ID，實測 %d 個' % (m.group(2), len(cids)))
# 🚨 兩種數法之數字必須各自與實測一致，且差值必須等於兩者之差。
# ⚠️ 第 391 輪教訓：進度原本只寫一個數字，實際上「頁段已排入」與「檔內確有引用」
# 是兩種數法，第 390 輪之 420 為前者、後者當時只有 384。兩個數字都對，
# 但只寫一個而不講數法，讀的人無從得知漏了哪 36 筆——**即 n+67(三) 所禁者。**
# **故三個數字（甲式、乙式、差值）全部入檢，且差值不得手打，必須等於相減。**
judged_ids = {x['candidateId'][-8:] for x in E
              if 'W4b' in x.get('reason', '')}
cite_done = len(judged_ids & cids)
m2 = re.search(r'\*\*乙式：引用制\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\*', t)
assert m2, '🚨 檔頭之乙式（引用制）進度列不見了'
assert int(m2.group(1)) == cite_done, (
    '🚨 檔頭自述乙式已完成 %s 筆，實測 %d 筆' % (m2.group(1), cite_done))
m3 = re.search(r'\*\*甲式：頁段制\*\* \| \*\*(\d+)\*\* \| \*\*(\d+)\*\*', t)
assert m3, '🚨 檔頭之甲式（頁段制）進度列不見了'
band_done = int(m3.group(1))
m4 = re.search(r'兩式之差 (\d+) 筆', t)
assert m4, '🚨 檔頭之兩式差值說明不見了——沒有它，兩個數字並列反而更誤導'
assert int(m4.group(1)) == band_done - cite_done, (
    '🚨 檔頭自述兩式之差 %s 筆，惟 %d − %d = %d'
    % (m4.group(1), band_done, cite_done, band_done - cite_done))

# 🚨 類別標題數必須等於條目代號數。
# ⚠️ 第 384 輪：有一節標題另立而條目沿用既有代號（劑型 vs 劑量與型態），
# 於是 17 個標題對 16 個代號——**讀者會以為有 17 類，實際只有 16 類可被引用。**
heads = re.findall(r'^## 類別：', t, re.M)
prefixes = {i.split('-')[0] for i in ids}
assert len(heads) == len(prefixes), (
    '🚨 類別標題 %d 個，條目代號 %d 種——有標題未配得自己的代號，'
    '或有代號未配得標題' % (len(heads), len(prefixes)))

print('✅ 編號無重複；✅ 所有 candidateId 皆可回溯；✅ 標題與代號數一致')
print()
print('⚠️ 本檔未驗證主張句是否忠於判讀原文——那需要人讀，不能由樣式代勞。')
