# -*- coding: utf-8 -*-
"""第 367 輪：更正 p295 對 `gel` 詞族的計數宣稱。

p295 心跳寫「編號 100，實際筆數亦 100，兩者相等是巧合」。
本檔實測三個都可以叫做「gel 詞族筆數」的量，看它們是否一致。
不落地任何文獻內容，只輸出計數（n+48 內容制衛生）。
"""
import io
import json
import os
import re

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run')
E = json.load(io.open(os.path.join(ROOT, 'standard-full-screen-pass-1',
                                   'judgements.json'), encoding='utf-8'))['entries']
RS = [x.get('reason', '') for x in E]

# 量 A：帶「`gel` 詞族至此 N 筆」序號句型者
A = [int(m.group(1)) for r in RS
     for m in re.finditer(r'`gel` 詞族至此 (\d+) 筆', r)]
# 量 B：理由提及「gel 詞族」四字（不論有無序號）
B = [r for r in RS if 'gel` 詞族' in r or 'gel 詞族' in r]
# 量 C：理由中出現 gel 字串（含 hydrogel／gels／GelMA）
C = [r for r in RS if re.search(r'gel', r, re.I)]

print('量A（帶序號句型）       %3d 筆；序號最大值 %d' % (len(A), max(A)))
print('量B（提及「gel 詞族」）  %3d 筆' % len(B))
print('量C（理由含 gel 字串）   %3d 筆' % len(C))
print()

miss = [n for n in range(1, max(A) + 1) if n not in set(A)]
dup = sorted({n for n in A if A.count(n) > 1})
print('量A 缺號：%s' % miss)
print('量A 重號：%s' % dup)
print()

assert len(A) != max(A), '若相等則本檔的前提不成立，須重寫'
print('🚨 序號最大值 %d ≠ 帶序號筆數 %d，差 %d'
      % (max(A), len(A), max(A) - len(A)))
print('🚨 而三個量彼此皆不相等：%d / %d / %d' % (len(A), len(B), len(C)))
print()
print('⚠️ p295 心跳所寫「編號 100、實際筆數亦 100」，')
print('   其「實際筆數」用的是量B。量B 恰為 %d 純屬該量之巧合，' % len(B))
print('   換成量A 是 %d、量C 是 %d——**「實際筆數」本身就不是單一個數字**。'
      % (len(A), len(C)))
# 🚨 上面三個數字一律由實測代入，不得手打。
# 本檔第一版把量C 手打成 139（實測 143）——即本 lane 第九型缺陷
# 「拿自己的敘述當資料」，在一支專門講計數紀律的腳本裡犯。
print('⚠️ 故 n+67（三）真正的要求不是「量一次筆數」，')
print('   而是「講明白量的是哪一個定義」。p295 沒講明，本輪補上。')
