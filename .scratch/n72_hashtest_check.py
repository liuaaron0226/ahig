# -*- coding: utf-8 -*-
"""🚨 驗證那條雜湊測試不是假 PASS（第 7 型缺陷：模式太鬆→假 PASS）。

`test_out_of_sequence_count_is_inside_the_evidence_hash` 斷言兩份證據之
雜湊不同。**但 `notScreenedCount` 本來就不同**——若光靠它就能讓雜湊不同，
那條測試即使把 `outOfSequenceCount` 從 key 清單移除也會通過，
**它就沒有在測它宣稱要測的東西。**

本檔用突變測試回答：**把 `outOfSequenceCount` 從 key 清單拿掉，
那條測試會不會失敗？** 會失敗才算真的釘住。
"""
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402
from ahig.search import statistical_termination as st  # noqa: E402


def queue(n, *, safety=(), harms=()):
    return [{'candidateId': f'c{i}',
             'screeningLane': ('safety-review' if f'c{i}' in safety
                               else 'standard-screening'),
             'flags': ['critical-harms-signal'] if f'c{i}' in harms else []}
            for i in range(1, n + 1)]


q = queue(400)
base = [(f'c{i}', 'exclude') for i in range(1, 391)]
without = st.evaluate_termination(q, base)
with_perm = st.evaluate_termination(
    q, base + [('c391', 'exclude')], out_of_sequence={'c391'})

FULL = ('alpha', 'pScore', 'relevantFound', 'screenedCount', 'poolSize',
        'targetRecall', 'windowSize', 'notScreenedCount',
        'mandatoryLanesFullyScreened', 'pScoreExcludedCount',
        'outOfSequenceCount', 'allowedToStop')
MUTANT = tuple(k for k in FULL if k != 'outOfSequenceCount')

print('兩份證據之逐欄比較：')
for k in FULL:
    a, b = without[k], with_perm[k]
    print('  %-30s %-8s vs %-8s %s'
          % (k, a, b, '**不同**' if a != b else ''))
print()

h_full = (content_hash({k: without[k] for k in FULL}),
          content_hash({k: with_perm[k] for k in FULL}))
h_mut = (content_hash({k: without[k] for k in MUTANT}),
         content_hash({k: with_perm[k] for k in MUTANT}))
print('完整 key 清單    ：雜湊%s' % ('不同 ✅' if h_full[0] != h_full[1]
                                    else '相同 🚨'))
print('拿掉 outOfSequenceCount：雜湊%s'
      % ('不同 🚨（測試是假 PASS）' if h_mut[0] != h_mut[1]
         else '相同 ✅（測試確實釘住了它）'))
print()
if h_mut[0] != h_mut[1]:
    print('🚨 那條測試是**假 PASS**：`notScreenedCount` 已經不同，')
    print('   即使 `outOfSequenceCount` 不在清單內，雜湊照樣不同。')
    print('   **必須改成兩份證據之其他欄位完全相同的情境。**')
else:
    print('✅ 突變測試通過：拿掉該欄位後雜湊相同，')
    print('   故那條測試確實是靠 `outOfSequenceCount` 才分辨出兩份證據。')
