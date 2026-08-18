# -*- coding: utf-8 -*-
"""n+77：建立 `docs/w4b-design-inputs.md` 之首批條目。

🚨 依 n+77 第三節，條目一律以 `candidateId` 為錨，回到判讀原文取材，
**不得從 COORDINATION.md 的敘述反推**——那正是第九型缺陷。

⚠️ 本檔只做兩件事：
  1. 量出兩個來源的規模差異（判讀理由 vs 看板區塊），供心跳如實回報；
  2. 產生「本輪批次」的候選清單（按輪次由新到舊，每輪一小批），
     由我逐筆讀判讀原文後手寫條目——**不自動生成主張句**，
     因為自動摘句等於讓樣式決定分類邊界。

不落地任何文獻標題或摘要（n+48 內容制衛生）：只輸出短碼與意見。
"""
import io
import json
import os
import sys

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run')
OUT = ROOT + '/standard-full-screen-pass-1'
E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
W = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
page_of = {it['candidateId']: it['page'] for it in W['items']}

hits = [x for x in E if 'W4b' in x.get('reason', '')]
board = io.open('COORDINATION.md', encoding='utf-8').read()

print('=== 兩個來源之規模（實測，非估計）===')
print('  甲 判讀理由提及 W4b        %4d 筆  ← 可回溯至 candidateId' % len(hits))
print('  乙 看板「W4b 設計輸入」區塊 %4d 次  ← 協調者所指之 111' %
      board.count('W4b 設計輸入'))
print()
print('🚨 兩者不是同一個集合，也不是包含關係：')
print('   甲是「判讀時寫下建議 W4b 如何使用本筆」者；')
print('   乙是「心跳中整理成區塊」者，一個區塊常涵蓋數筆或零筆記錄。')
print('⚠️ 回填必須以甲為準（有 candidateId），乙僅用來找出「僅存敘述」者。')
print()

if len(sys.argv) > 1:
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    batch = [x for x in hits if lo <= page_of.get(x['candidateId'], 0) <= hi]
    print('=== 本批次：page %d–%d，%d 筆 ===' % (lo, hi, len(batch)))
    for x in batch:
        print('  %s  %-7s  p%-4d' % (x['candidateId'][-8:], x['opinion'],
                                     page_of[x['candidateId']]))
else:
    print('用法：n77_w4b_seed.py <起頁> <迄頁>　→ 列出該頁段之候選')
    print()
    print('=== 各頁段分布（每 50 頁）===')
    import collections
    c = collections.Counter((page_of.get(x['candidateId'], 0) // 50) * 50
                            for x in hits)
    for k in sorted(c):
        print('  p%-4d–%-4d  %4d 筆' % (k, k + 49, c[k]))
