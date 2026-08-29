# -*- coding: utf-8 -*-
"""義務 41893 綁著的衍生數「期望漏失約 10 筆」——底數長大了，它沒動。

## 🚨 為什麼查這一條

n+116（五）自載：42 條義務勾稽只答得了「**有沒有文件談到**」，
**答不了「已不已辦」——後者須人讀，🚫 不得以該結果宣稱義務皆已完成。**
本檔即做那份人讀，先挑一條可以完全對數的。

## 一、同一個量，看板上有三個數

| 出處 | 值 | 時點／範圍 |
|---|---|---|
| 看板 41893（義務原文） | **77** | n+52（二）：`page < 212` |
| 看板 47917 | **133** | 其後某輪，範圍已放寬 |
| `title-only-judged-roster.json` `entryCount` | **175** | 現行；`segment` 自述「ALL judged pages… widened after n+53」 |

**✅ 名冊筆數本身有漂移機制**：骨架標 `TITLE_ONLY_N` 為**漂移值、交付時現算**，
交付清單已載 175。**⚠️ 這一格沒問題。**

## 🚨 二、有問題的是它旁邊那個衍生數

義務原文（看板 41893–41894）要求報告明列：
> **77 筆僅憑標題判讀、上游無摘要可補、期望漏失約 10 筆。**

**推導在看板 41875–41877**：
> 碳水訊號 100%，帶訊號且有摘要者 **advance 率 14.7%**，該段實得含升級後僅 4 筆。
> **期望缺口約 10 筆**，佔 advance 池（311）約 3%。

**🚨 該數在底數由 77 長到 133 的期間原封不動**——
看板 41894 與 47918 **都寫「約 10 筆」**，⚠️ 而 41893 的底數是 77、47917 的底數是 133。
**這是「它沒有被重算」的直接證據，不是推測。**

**🚨 且它在任何骨架裡都沒有佔位符**（已搜遍受追蹤之 `docs/` 與 `.scratch/`）。
**⚠️ 即：若報告寫它，只能從看板散文抄——而那正是本 run 一路在修的失效方式。**

## 三、⚠️ 依原推導法、換上現行底數會是多少

**🚫 本室不逕行改寫該數**——⚠️ 14.7% 這個率取自「帶訊號且有摘要者」之特定段落，
**🚨 它是否適用於放寬後的全體名冊，是判準問題，須協調者裁示。**
本檔只把算式攤開，讓裁示有數字可依。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：三個底數之出處與時點、衍生數是否隨底數變動、有無佔位符。
- 🚨 查不到：**14.7% 是否可套用於放寬後之名冊**——⚠️ 需重跑該段之判讀分布，
  且涉及判準選擇，🚫 本室不代為決定。
"""
import io
import json
import os
import re
import subprocess
import sys

ROSTER = (os.environ.get('AHIG_PRIVATE_ROOT',
                         r'C:/Users/User/Desktop/claude/ahig-private') +
          '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
          '/standard-full-screen-pass-1/title-only-judged-roster.json')

board = open('COORDINATION.md', 'rb').read().decode('utf-8').replace('\r\n', '\n')
lines = board.split('\n')
roster = json.load(io.open(ROSTER, encoding='utf-8'))

# 🚨 逐一以看板行號取值，不憑記憶
def line_has(n, pat):
    return bool(re.search(pat, lines[n - 1]))


bases = [('board 41893（義務原文）', 77, line_has(41893, r'77\s*筆')),
         ('board 47917', 133, line_has(47917, r'133\s*筆')),
         ('roster entryCount（現行）', roster['entryCount'], True)]
print('=== 一、同一個量之三個底數 ===')
for label, val, ok in bases:
    print('   %-30s %4s  %s' % (label, val, '✅ 已於該行現查' if ok else '🚨 該行未見'))
print('   roster.segment：%s' % roster.get('segment', '')[:96])

gap_lines = [(i + 1, l.strip()) for i, l in enumerate(lines) if '期望漏失' in l or '期望缺口' in l]
print()
print('=== 二、衍生數「期望漏失／缺口」出現處 ===')
for n, l in gap_lines:
    print('   %6d | %s' % (n, l[:104]))
unchanged = len({re.search(r'約\s*(\d+)', l).group(1) for _, l in gap_lines
                 if re.search(r'約\s*(\d+)', l)}) == 1
print('   🚨 各處之值是否一致（即未隨底數重算）：%s' % ('是——未重算' if unchanged else '否'))

# 有無佔位符
fs = subprocess.run(['git', 'ls-files', 'docs/', '.scratch/'],
                    capture_output=True, text=True, encoding='utf-8').stdout.split()
holder = [f for f in fs
          if re.search('期望漏失|期望缺口|EXPECTED_GAP|EXPECTED_MISS',
                       open(f, 'rb').read().decode('utf-8', errors='ignore'))]
print('   ⚠️ 骨架／清單中之佔位符：%s' % (holder or '🚨 無——只能自看板散文抄'))

RATE = 0.147
print()
print('=== 三、依原推導法換上各底數（🚫 不代為改寫，只攤開算式）===')
print('   推導（看板 41875–41877）：底數 × advance 率 14.7% − 該段實得 4 筆')
for label, n, _ in bases:
    print('   %-30s %3d × %.3f = %5.1f  → 減實得 4 = %5.1f'
          % (label, n, RATE, n * RATE, n * RATE - 4))
print('   ⚠️ 報告現被義務要求寫「約 10」；以現行底數 %d 計為 %.0f。'
      % (roster['entryCount'], roster['entryCount'] * RATE - 4))
print('   🚨 惟 14.7% 是否適用於放寬後之名冊屬判準問題，須協調者裁示。')

doc = {
    'schemaVersion': 1,
    'documentType': 'obligation-derived-figure-drift',
    'ruling': 'self-initiated; fills the gap n+116(5) named -- whether an '
              'obligation is discharged, not merely mentioned',
    'obligation': 'board 41893-41894',
    'population': 'the [title-only-judged] roster',
    'countingUnit': 'record',
    'criterion': 'board line numbers read directly; roster entryCount read from '
                 'the file',
    'baseFigures': [{'source': s, 'value': v} for s, v, _ in bases],
    'baseHasDriftMechanism': True,
    'baseNote': 'The roster count itself is fine: the skeleton marks '
                'TITLE_ONLY_N as a drift value to be recomputed at delivery, '
                'and the checklist carries 175.',
    'derivedFigure': {'text': '期望漏失約 10 筆',
                      'occurrences': [{'line': n, 'text': l} for n, l in gap_lines],
                      'unchangedAcrossBaseGrowth': unchanged,
                      'derivation': 'base x 14.7% advance rate, less the 4 '
                                    'actually obtained (board 41875-41877)',
                      'placeholderExists': bool(holder),
                      'placeholderFiles': holder},
    'arithmeticUnderStatedMethod': {str(v): round(v * RATE - 4, 1)
                                    for _, v, _ in bases},
    'claim': 'The base grew from 77 to 133 to 175 while the derived figure '
             'stayed at "about 10" in both places it appears, and it has no '
             'placeholder anywhere, so a report that states it would copy board '
             'prose. The obligation as written requires stating it.',
    'notDecidedHere': 'Whether the 14.7% rate, taken from records that had '
                      'signal and an abstract, transfers to the widened roster '
                      'is a criterion question for the coordinator. The '
                      'arithmetic is laid out so the ruling has numbers; it is '
                      'not a proposed replacement value.',
    'contentNote': 'Counts, rates and board line numbers only.',
}
io.open('.scratch/n447_expected_gap_drift.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → .scratch/n447_expected_gap_drift.json')
sys.exit(0)
