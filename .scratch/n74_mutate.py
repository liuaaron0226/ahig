# -*- coding: utf-8 -*-
"""n+74（二）之常規回頭適用於我自己：**其餘 5 條新測試也要突變驗證**。

🚨 n+74 立為常規：「凡為某項要求新增之測試，須以突變驗證其確實會失敗；
未經突變驗證者，不得以『全綠』作為該要求已滿足之證據。」

⚠️ 我在 n+72 只對**雜湊那一條**做了突變。其餘 5 條至今仍只是「綠燈」
——**依新常規，那 5 條目前不構成任何證據。** 本檔逐條補做。

作法：對 `statistical_termination.py` 施加一個**針對性突變**
（拿掉該測試所保護的那一行／那個條件），跑測試，看它是否失敗。
每條突變跑完即還原。**還原以檔案雜湊核對，不憑印象。**
"""
import hashlib
import io
import subprocess
import sys

SRC = 'ahig/ahig/search/statistical_termination.py'
orig = io.open(SRC, encoding='utf-8').read()
orig_hash = hashlib.sha256(orig.encode('utf-8')).hexdigest()
print('原始檔 sha256 %s' % orig_hash[:16])
print()

# (測試名, 說明, 被突變的原文, 換成什麼)
MUTANTS = [
    ('test_out_of_sequence_records_do_not_enter_labels',
     '拿掉「第三態不進 labels」之 continue → 它們會進序列',
     "        if cid in out_perm:\n"
     "            # 同上，惟依設計永久不納回（第三態，n+72）。\n"
     "            out_perm_seen.add(cid)\n"
     "            continue\n",
     "        if cid in out_perm:\n"
     "            out_perm_seen.add(cid)\n"),

    ('test_out_of_sequence_does_not_block_stopping',
     '讓第三態也擋終止 → 與排除清單無異，第三態失去意義',
     "    allowed = (preconditions_met and not pending_reintegration\n"
     "               and score[\"pScore\"] < alpha)",
     "    allowed = (preconditions_met and not pending_reintegration\n"
     "               and not out_of_sequence_seen\n"
     "               and score[\"pScore\"] < alpha)"),

    ('test_out_of_sequence_still_counts_as_screened',
     '不把第三態加入 seen → 它們會被算成 not-screened',
     "        seen.add(cid)\n        if cid in excluded:",
     "        if cid not in out_perm:\n            seen.add(cid)\n"
     "        if cid in excluded:"),

    ('test_out_of_sequence_and_excluded_must_be_disjoint',
     '拿掉互斥檢查（n+72 協調者補的第 2 項）',
     "    both = sorted(excluded & out_perm)\n"
     "    if both:\n"
     "        raise TerminationError(\n"
     "            f\"同一 candidateId 同時列於排除清單與永久不入序列集合：{both[:3]}\")\n",
     ""),

    ('test_out_of_sequence_rejects_unknown_or_unscreened_ids',
     '拿掉「不在 queue」與「未篩畢」兩道入口檢查',
     "    unknown_perm = sorted(out_perm - set(queue_by_id))\n"
     "    if unknown_perm:\n"
     "        raise TerminationError(\n"
     "            f\"永久不入序列集合的 candidateId 不在 queue：{unknown_perm[:3]}\")\n",
     ""),
]

results = []
for name, why, before, after in MUTANTS:
    if before not in orig:
        results.append((name, why, '🚨 突變無法套用（原文找不到）'))
        continue
    io.open(SRC, 'w', encoding='utf-8').write(orig.replace(before, after, 1))
    p = subprocess.run([sys.executable, '-X', 'utf8',
                        'ahig/tests/run_tests.py'],
                       capture_output=True, text=True, encoding='utf-8',
                       errors='replace')
    out = (p.stdout or '') + (p.stderr or '')
    io.open(SRC, 'w', encoding='utf-8').write(orig)
    now = hashlib.sha256(
        io.open(SRC, encoding='utf-8').read().encode('utf-8')).hexdigest()
    assert now == orig_hash, '還原失敗！'
    killed = name in out or 'failed' in out and ', 0 failed' not in out
    tail = [ln for ln in out.splitlines() if 'passed' in ln]
    results.append((name, why,
                    ('✅ 被殺死（測試確實會失敗）' if killed
                     else '🚨 存活（測試沒測到它宣稱的東西）')
                    + '　' + (tail[-1] if tail else '?')))

print('== 突變驗證結果 ==')
for name, why, verdict in results:
    print('  %s' % name)
    print('     突變：%s' % why)
    print('     %s' % verdict)
print()
now = hashlib.sha256(
    io.open(SRC, encoding='utf-8').read().encode('utf-8')).hexdigest()
print('還原核對：%s（%s）'
      % (now[:16], '與原始相符 ✅' if now == orig_hash else '🚨 不符'))
