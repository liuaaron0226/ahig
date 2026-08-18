# -*- coding: utf-8 -*-
"""查明那兩條突變為何存活——**是備援路徑，不是測試寫錯**。

⚠️ 先問「為什麼」再改，否則會把一個沒壞的東西改壞。
"""
import sys

sys.path.insert(0, 'ahig')
from ahig.search import statistical_termination as st  # noqa: E402


def queue(n):
    return [{'candidateId': f'c{i}', 'screeningLane': 'standard-screening',
             'flags': []} for i in range(1, n + 1)]


q = queue(400)
decisions = [(f'c{i}', 'exclude') for i in range(1, 392)]

print('== 情境一：同一 id 同列兩集合（互斥檢查被拿掉時會發生什麼）==')
try:
    st.evaluate_termination(q, decisions, p_score_excluded={'c390', 'c391'},
                            out_of_sequence={'c391'})
except st.TerminationError as e:
    print('  現行（互斥檢查在）：%s' % e)
print('  ⚠️ 若拿掉互斥檢查：`c391` 會先被 `excluded` 分支接走'
      '（excluded 判斷在前），')
print('     於是 `out_perm_seen` 不含它 → 觸發「含未篩畢紀錄」那道檢查，')
print('     **一樣拋 TerminationError，訊息裡一樣有 c391**。')
print('  🚨 故我的測試只斷言「拋錯且訊息含 c391」——**兩條路都滿足**。')
print()

print('== 情境二：id 不在 queue（入口檢查被拿掉時會發生什麼）==')
try:
    st.evaluate_termination(q, decisions[:5], out_of_sequence={'c99'})
except st.TerminationError as e:
    print('  現行（入口檢查在）：%s' % e)
print('  ⚠️ 若拿掉入口檢查：`c99` 不在 decisions 中 → `out_perm_seen` 為空')
print('     → 一樣觸發「含未篩畢紀錄」那道檢查。')
print('  🚨 同樣是備援路徑接住。')
print()
print('⚠️ **結論：程式行為沒有錯**（兩種情況都確實被擋下）。')
print('   **錯的是我的測試太寬**——它只問「有沒有拋錯」，')
print('   沒問「是哪一道檢查擋下的」，於是拿掉任一道都還是綠的。')
print('🚨 這與雜湊那條同型：**斷言的粒度比要求的粒度粗。**')
print('   修法：斷言錯誤訊息之**特徵字串**，讓每道檢查各自可被釘住。')
