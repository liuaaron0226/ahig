# -*- coding: utf-8 -*-
"""n+60（二）（乙）2 之掛牌名單：**逐一現算筆數**（n+59 第四節）。

M1 報告要向擁有者列出「每一份掛牌名單就是一個可重新考慮的範圍問題」，
並宣稱「全部零重篩可回收」。**那些筆數會被引用，故不得手寫。**

本檔做兩件事：
  1. 依理由文字中之掛牌字樣，逐牌現算筆數與判讀分布。
  2. **查核「零重篩可回收」之前提**——即每一筆掛牌記錄是否確實
     留有可據以回收之判讀理由（非空、且含該掛牌字樣）。

⚠️ 限制須明說：掛牌以理由文字認定，**某筆屬該類但當初未掛牌者，
本檔看不到**。故本檔報的是「已掛牌者」之數，不是「該類母體」之數。

唯讀，不寫任何檔案。
"""
import io
import json
import os
import re

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

# ⚠️ 不是每一類都以 `[tag]` 方括號字樣記錄。n+60（二）點名的
# `[comparator-gap]`、`[instrument-gap]`、`[retracted]` 三者，
# 以方括號樣式查全為 0——查證後**不是資料沒有，是我的樣式錯**：
# 撤稿類記為 `Retracted Publication`／「撤稿」，comparator 與
# instrument 兩類則以 `allowedInstruments`／contract comparator
# 之敘述記錄，從未使用方括號掛牌。故每類各給一組替代樣式。
# （這正是 n+60 一節所述那族缺陷的反面：樣式比意圖窄，
#  少掉的部分會安靜地變成「零筆」。）
TAGS = [
    ('[outcome-adjacent]', r'\[outcome-adjacent\]'),
    ('[intermittent-team-sport]', r'\[intermittent-team-sport\]'),
    ('[age]', r'\[age\]'),
    ('[route]', r'\[route\]'),
    ('[cho-type-comparison]', r'\[cho-type-comparison\]'),
    ('[methodological]', r'\[methodological\]'),
    ('[chronic-strategy]', r'\[chronic-strategy\]'),
    ('[placebo-cho-vehicle]', r'\[placebo-cho-vehicle\]'),
    ('[mixed-nutrient]', r'\[mixed-nutrient\]'),
    ('[population]', r'\[population\]'),
    ('[title-only-judged]', r'\[title-only-judged\]'),
    ('撤稿（Retracted，非方括號）', r'Retracted Publication|撤稿'),
    ('comparator 缺口（敘述式）', r'契約 comparator|comparator allowlist'),
    ('instrument 缺口（敘述式）', r'allowedInstruments|儀器效度'),
]

E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']

# 有效判讀＝套用兩層覆蓋後之結果（與 term.py 同一套定義）
eff = {e['candidateId']: e['opinion'] for e in E}
for f in ('post-ruling-reclassification.json',
          'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + f
    if os.path.exists(p):
        for e in json.load(io.open(p, encoding='utf-8'))['entries']:
            eff[e['candidateId']] = e['effectiveDecision']

print('序列長度 %d' % len(E))
print()
print('%-26s %6s  %-22s %s' % ('掛牌', '筆數', 'advance/unclear/exclude',
                               '理由可回收'))
print('-' * 78)

total_flagged = set()
for label, pat in TAGS:
    rx = re.compile(pat)
    hits = [e for e in E if rx.search(e.get('reason', '') or '')]
    if not hits:
        print('%-26s %6d' % (label, 0))
        continue
    dist = {'advance': 0, 'unclear': 0, 'exclude': 0}
    for e in hits:
        dist[eff.get(e['candidateId'], e['opinion'])] += 1
        total_flagged.add(e['candidateId'])
    # 可回收＝理由非空且長度足以據以重判（此處以 >=80 字為門檻，
    # 該門檻僅用於偵測空殼理由，非品質判斷）
    recoverable = sum(1 for e in hits if len((e.get('reason') or '')) >= 80)
    print('%-26s %6d  %5d/%5d/%5d      %d/%d'
          % (label, len(hits),
             dist['advance'], dist['unclear'], dist['exclude'],
             recoverable, len(hits)))

print('-' * 78)
print('掛牌記錄去重後合計：%d 筆（同一筆可掛多牌）' % len(total_flagged))
print()

# 名冊為獨立檔案，另行核對
roster_p = OUT + '/title-only-judged-roster.json'
if os.path.exists(roster_p):
    r = json.load(io.open(roster_p, encoding='utf-8'))
    ent = r.get('entries', r)
    rd = {}
    for x in ent:
        rd[x.get('screeningDecision')] = rd.get(x.get('screeningDecision'), 0) + 1
    print('`[title-only-judged]` 名冊檔實際筆數：%d（%s）'
          % (len(ent), rd))
    print('⚠️ 名冊檔為權威來源；上表之 [title-only-judged] 係以理由')
    print('   文字認定，兩者不必然相等（早期判讀未必寫該字樣）。')
print()
print('⚠️ 限制：掛牌以理由文字認定，**某筆屬該類但未掛牌者本檔看不到**。')
print('   本檔報的是「已掛牌者」之數，不是「該類母體」之數。')
