# -*- coding: utf-8 -*-
"""交付清單之「產物型 15」與「原始碼型 3」——逐一解析其指名路徑並取值。

## 🚨 為什麼掃完這兩類

第 440／441 輪對「不可及 8」與「看板 6」各問一次「真的只有那個來源嗎」，
**共查出 11 格分類需要更動**。⚠️ 剩下 18 格（產物 15、原始碼 3）尚未被同一把尺量過。

**⚠️ 這兩類的風險與前兩類不同**：前兩類是「分類填錯」，
**🚨 這兩類是「路徑寫得很具體，但沒有人執行過它」**——
本 run 已多次因欄位名不符而得到假結論（`source` vs `sourceId`、
`method` vs `unionGate`），**而寫在文件裡的路徑一樣會過期。**

## 本檔做什麼

對每一格：**解析其指名之檔案與欄位路徑，實際取值並印出**。
**🚨 路徑解析不到即判紅**——⚠️ 交付時才發現寫錯路徑，代價比現在高。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：檔案是否存在且受追蹤、欄位路徑是否解析得到、取到的值。
- 🚨 查不到：**該值是否為該佔位符語意上正確的量**——⚠️ 那要人讀骨架。
  第 441 輪之 `SEX_REPRESENTATION` 正是路徑有效而語意不符者，🚨 本檔抓不到那一型。
"""
import io
import json
import os
import re
import subprocess
import sys

S = '.scratch/'

# (佔位符, 檔案, 路徑規格)
#   路徑規格：'a.b.c' 取值；'len:a.b' 取長度；None 表示清單未指明確切欄位
ART = [
    ('NOT_SCREENED_STD', 'n78_termination_evidence.json', 'tailSpotCheckPopulation.count'),
    ('N_TOTAL_STD', 'n78_termination_evidence.json', 'standardLaneSequence.nTotal'),
    ('OCC1_HITS', 'n68_tail_result.json', None),
    ('OCC1_P', 'n78_termination_evidence.json', 'previousOccurrence.pScore'),
    ('OCC1_PAGE', 'n78_termination_evidence.json', 'previousOccurrence.atPage'),
    ('OCC1_POP', 'n68_termination_evidence.json', None),
    ('OCC1_W', 'n78_termination_evidence.json', 'previousOccurrence.windowSize'),
    ('OCC2_HITS', 'n78_tail_result.json', 'len:result.relevantOrUnclearFound'),
    ('OCC2_P', 'n78_termination_evidence.json', 'standardLaneSequence.pScore'),
    ('OCC2_POP', 'n78_termination_evidence.json', 'tailSpotCheckPopulation.count'),
    ('OCC2_W', 'n78_termination_evidence.json', 'standardLaneSequence.windowSize'),
    ('OUT_OF_SEQ', 'n78_termination_evidence.json', 'standardLaneSequence.outOfSequenceCount'),
    ('P_ALLQUEUE', 'n78_termination_evidence.json', 'evaluateTerminationStandardBasis.pScore'),
    ('SEQ_LEN', 'n78_termination_evidence.json', 'standardLaneSequence.screenedCount'),
    ('TRIGGER_CAUSE_ID', 'n78_termination_evidence.json', 'triggerCause.candidateId'),
]
SRC = [
    ('ALPHA', 'DEFAULT_ALPHA', 0.05),
    ('SPOT_N', 'DEFAULT_TAIL_SPOT_CHECK_N', 200),
    ('TARGET_RECALL', 'DEFAULT_TARGET_RECALL', 0.95),
]
SRC_FILE = 'ahig/ahig/search/statistical_termination.py'

tracked = set(subprocess.run(['git', 'ls-files'], capture_output=True,
                             text=True, encoding='utf-8').stdout.split('\n'))


def resolve(doc, spec):
    if spec is None:
        return '（清單未指明確切欄位）', 'unspecified'
    take_len = spec.startswith('len:')
    path = spec[4:] if take_len else spec
    cur = doc
    for part in path.split('.'):
        if not isinstance(cur, dict) or part not in cur:
            return None, '🚨 路徑解析失敗於 %r' % part
        cur = cur[part]
    if take_len:
        if not isinstance(cur, list):
            return None, '🚨 指定取長度但該欄非 list（%s）' % type(cur).__name__
        return len(cur), 'len'
    return cur, 'value'


print('=== 一、產物型 15：解析指名路徑並取值 ===')
print('%-20s %-36s %-14s %s' % ('佔位符', '檔案', '值', '判定'))
print('-' * 92)
bad = []
rows = {}
for name, fn, spec in ART:
    p = S + fn
    if not os.path.isfile(p):
        print('%-20s %-36s %-14s %s' % (name, fn, '—', '🚨 檔案不存在'))
        bad.append((name, 'file-missing'))
        continue
    intrack = '✅' if p.replace('\\', '/') in tracked else '🚨 未受追蹤'
    doc = json.load(io.open(p, encoding='utf-8'))
    val, how = resolve(doc, spec)
    mark = '✅ %s' % intrack if val is not None or how == 'unspecified' else how
    if val is None and how != 'unspecified':
        bad.append((name, how))
        mark = how
    rows[name] = {'file': fn, 'spec': spec, 'value': val, 'how': how,
                  'tracked': p.replace('\\', '/') in tracked}
    print('%-20s %-36s %-14s %s' % (name, fn, str(val)[:14], mark))

print()
print('=== 二、原始碼型 3：常數是否仍在指名位置 ===')
src = io.open(SRC_FILE, encoding='utf-8').read()
for name, const, expect in SRC:
    m = re.search(r'^%s\s*[:=][^=\n]*?=?\s*([0-9.]+)' % const, src, re.M)
    if not m:
        m = re.search(r'^%s.*?([0-9.]+)\s*$' % const, src, re.M)
    got = float(m.group(1)) if m else None
    ok = got == expect
    print('   %-18s %-30s 清單 %-6s 原始碼 %-6s %s'
          % (name, const, expect, got, '✅' if ok else '🚨 不符'))
    if not ok:
        bad.append((name, 'const-mismatch:%s' % got))
    rows[name] = {'file': SRC_FILE, 'spec': const, 'value': got,
                  'how': 'source-constant', 'tracked': True}

# ── 三、跨欄一致性：路徑各自解析得到，不代表彼此對得起來 ──────────
# 🚨 清單只保證「每格取得到值」，⚠️ 不保證「這些值放在一起說得通」。
#    本 run 反覆出現的正是後者（數字都對、母體不同）。
print()
print('=== 三、跨欄一致性（🚨 逐條寫明恆等式，不只印值）===')
V = {k: rows[k]['value'] for k in rows}
checks = [
    ('標準線閉合式：nTotal − screenedCount − outOfSequence = notScreened',
     V['N_TOTAL_STD'] - V['SEQ_LEN'] - V['OUT_OF_SEQ'], V['NOT_SCREENED_STD']),
    ('第二次尾端抽驗母體 = 標準線未篩數',
     V['OCC2_POP'], V['NOT_SCREENED_STD']),
]
cons_ok = True
for label, got, want in checks:
    good = got == want
    cons_ok &= good
    print('   %-52s %s vs %s  %s' % (label, got, want, '✅' if good else '🚨'))
if not cons_ok:
    bad.append(('cross-field', 'identity-broken'))

# ⚠️ 一項須提請而非自行處置者
same = [k for k in ('NOT_SCREENED_STD', 'OCC2_POP')]
print()
print('   ⚠️ %s 兩格指向**同一個欄位** `tailSpotCheckPopulation.count`。' % '／'.join(same))
print('      🚨 值相同（%s）不代表語意相同：前者依骨架為「閉合式之第三項」，'
      % V['NOT_SCREENED_STD'])
print('      後者為「第二次尾端抽驗之母體」。⚠️ 今日兩者恰好相等，')
print('      🚨 但若日後尾端抽驗改為分層抽樣（W7 改善提案，看板 1717–1719 已記帳），')
print('      母體就不再等於未篩全集，而清單會**同時**把兩格填成同一個錯值。')
print('      ⚠️ 提請：`NOT_SCREENED_STD` 改標為由閉合式導出，🚫 不逕取該欄位。')

print()
print('-' * 92)
if bad:
    print('🚨 %d 格未通過：' % len(bad))
    for n, why in bad:
        print('   • %-20s %s' % (n, why))
else:
    print('✅ 18 格之指名路徑全部解析成功且取到值。')
print('⚠️ 本檔只驗「路徑取得到值」，🚨 不驗「該值語意上是否正確」'
      '——第 441 輪之 SEX_REPRESENTATION 即路徑有效而語意不符者。')

doc = {
    'schemaVersion': 1,
    'documentType': 'placeholder-source-resolution',
    'ruling': 'self-initiated; completes the sweep begun in rounds 440-441',
    'population': 'the 18 placeholders classed 產物 (15) or 原始碼 (3) in '
                  'docs/m1-e-delivery-checklist.md',
    'countingUnit': 'placeholder',
    'criterion': 'the named file exists and is tracked, and the named field '
                 'path resolves to a value',
    'resolved': rows,
    'failures': [{'placeholder': n, 'why': w} for n, w in bad],
    'coverageStatement': ('Checks that a path yields a value, not that the '
                          'value is the right quantity. Round 441 found a '
                          'placeholder whose source resolved fine and measured '
                          'the wrong thing; this file cannot catch that class.'),
    'contentNote': 'Field paths and numeric values only.',
}
io.open(S + 'n442_placeholder_sources.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn442_placeholder_sources.json' % S)
sys.exit(0 if not bad else 1)
