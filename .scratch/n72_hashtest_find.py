# -*- coding: utf-8 -*-
"""找出「其他 11 欄全同、只差 outOfSequenceCount」之情境。

思路：`notScreenedCount` 只看 `seen`。要它相同，兩邊**判讀筆數必須相同**。
故：兩邊都判 391 筆，差別在第 391 筆是進序列還是進第三態——
但那會讓 `screenedCount`（序列長度）不同。

改法：**兩邊都有一筆不進序列，只是走不同的路**——
  甲：`c391` 走排除清單（pScoreExcludedCount 1、outOfSequenceCount 0）
  乙：`c391` 走第三態  （pScoreExcludedCount 0、outOfSequenceCount 1）
惟 `pScoreExcludedCount` 也在清單內，兩邊仍會不同。

再改：**乙有兩筆第三態、甲有一筆第三態＋一筆…**——愈繞愈遠。

🚨 想清楚：`outOfSequenceCount` 一動，`notScreenedCount` 必動
（多一筆判讀＝少一筆未篩），除非同時有別的補償。
**故單獨隔離該欄位，需要一個補償項**：讓乙比甲多判一筆第三態，
同時讓乙的池子大一筆——但 `poolSize` 也在清單內。

**結論**：在真實輸出裡，`outOfSequenceCount` 與 `notScreenedCount`
是連動的，無法只差一個欄位。故正確的測法不是找那種情境，
而是**直接對 key 清單本身斷言**——它是一份明確的契約清單。
本檔驗證這個結論。
"""
import sys

sys.path.insert(0, 'ahig')
from ahig.search import statistical_termination as st  # noqa: E402


def queue(n):
    return [{'candidateId': f'c{i}', 'screeningLane': 'standard-screening',
             'flags': []} for i in range(1, n + 1)]


q = queue(400)
base = [(f'c{i}', 'exclude') for i in range(1, 391)]

# 甲：c391 走排除清單；乙：c391 走第三態。判讀筆數相同。
a = st.evaluate_termination(q, base + [('c391', 'exclude')],
                            p_score_excluded={'c391'})
b = st.evaluate_termination(q, base + [('c391', 'exclude')],
                            out_of_sequence={'c391'})
FULL = ('alpha', 'pScore', 'relevantFound', 'screenedCount', 'poolSize',
        'targetRecall', 'windowSize', 'notScreenedCount',
        'mandatoryLanesFullyScreened', 'pScoreExcludedCount',
        'outOfSequenceCount', 'allowedToStop')
print('甲（排除清單）vs 乙（第三態），判讀筆數相同：')
diff = [k for k in FULL if a[k] != b[k]]
for k in FULL:
    print('  %-30s %-8s vs %-8s %s'
          % (k, a[k], b[k], '**不同**' if a[k] != b[k] else ''))
print()
print('相異欄位：%s' % diff)
print()
print('⚠️ notScreenedCount 相同（兩邊都判 391 筆）；')
print('   相異的是 pScoreExcludedCount 與 outOfSequenceCount，')
print('   **兩者都在 key 清單內**——故仍無法單獨隔離其一。')
print()
print('🚨 結論：改用**對 key 清單直接斷言**——')
print('   那是一份契約清單，測試該釘住的正是「這兩個計數在清單內」。')
