# -*- coding: utf-8 -*-
"""第 408 輪：乙式殘量之重掃清單。

甲式（頁段制）808 筆已全數回填；乙式（引用制）756 筆。
**殘量 52 ＝ 判讀理由提及 W4b、頁段已排過、但本檔未引用其 candidateId 者。**

🚨 依 docs/w4b-design-inputs.md 之記載，殘量成因有二且性質不同：
  （一）第 371–390 輪判定「其 W4b 句僅為既有條目之佐證，不另立新條」，
        **而當時未留記錄** → 無法逐筆複查，只能重掃。
  （二）第 391 輪起改為「併入既有條目之 candidateId 欄」 → 此後產生者可回溯。

⚠️ 兩類不可混為一談：把已處理的當成漏掉的，會重複建條目。
**故本檔先依頁段切分，再輸出每筆之判讀 W4b 句供人讀。**

⚠️ 頁段與輪次之對應取自 docs 之回填進度表（頁段 → 輪次），
   **不逐筆猜測輪次**——只標「該頁段是在改做法之前或之後回填的」。

用法：
    python -X utf8 .scratch/n77_residue_scan.py          → 統計與分組
    python -X utf8 .scratch/n77_residue_scan.py <lo> <hi> → 列出該頁段殘量之 W4b 句
"""
import io
import json
import os
import re
import sys

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run')
OUT = ROOT + '/standard-full-screen-pass-1'
REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOC = os.path.join(REPO, 'docs', 'w4b-design-inputs.md')

E = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))['entries']
W = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
page_of = {it['candidateId']: it['page'] for it in W['items']}

doc = io.open(DOC, encoding='utf-8').read()
cited = set(re.findall(r'`([0-9a-f]{8})`', doc))

hits = [x for x in E if 'W4b' in x.get('reason', '')]
residue = [x for x in hits if x['candidateId'][-8:] not in cited]

# 🚨 改做法的分界：第 391 輪起「不另立新條者併入既有條目之 candidateId 欄」。
# 依回填進度表，第 391 輪回填的是 p235–239；故 p240 以上之頁段係在改做法之前
# 回填（第 371–390 輪），p239 以下係在改做法之後回填。
# ⚠️ 此分界只用於分類殘量成因，不用於判定任何一筆該不該補——那要讀原文。
CUTOFF = 240


def w4b_sentences(reason):
    """抽出含 W4b 的句子。⚠️ 只做切句，不改寫內容。"""
    parts = re.split(r'(?<=。)|(?<=\n)', reason)
    return [p.strip() for p in parts if 'W4b' in p]


if len(sys.argv) > 2:
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    sel = [x for x in residue if lo <= page_of.get(x['candidateId'], -1) <= hi]
    print('=== 殘量 page %d–%d，共 %d 筆 ===' % (lo, hi, len(sel)))
    for x in sorted(sel, key=lambda y: page_of[y['candidateId']]):
        print()
        print('-' * 74)
        print('%s  [%s]  p%d' % (x['candidateId'][-8:], x['opinion'],
                                 page_of[x['candidateId']]))
        for s in w4b_sentences(x['reason']):
            print('   ' + s)
    sys.exit(0)

print('甲層（判讀理由提及 W4b）  %d 筆' % len(hits))
print('本檔已引用                %d 筆' % (len(hits) - len(residue)))
print('殘量                      %d 筆' % len(residue))
print()

before = [x for x in residue if page_of.get(x['candidateId'], -1) >= CUTOFF]
after = [x for x in residue if page_of.get(x['candidateId'], -1) < CUTOFF]
print('=== 依成因分兩類（分界：p%d，即第 391 輪改做法之時點）===' % CUTOFF)
print('  （一）改做法之前回填之頁段（p%d 以上）  %2d 筆'
      '  ← 🚨 當時未留記錄，只能重掃' % (CUTOFF, len(before)))
print('  （二）改做法之後回填之頁段（p%d 以下）  %2d 筆'
      '  ← ⚠️ 理應已併入既有條目，須查為何未引用' % (CUTOFF - 1, len(after)))
print()

by_band = {}
for x in residue:
    pg = page_of.get(x['candidateId'], -1)
    band = (pg // 10) * 10
    by_band.setdefault(band, []).append(x['candidateId'][-8:])
print('=== 依頁段分布 ===')
for band in sorted(by_band, reverse=True):
    mark = '（一）' if band >= CUTOFF else '（二）'
    print('  p%-3d–%-3d  %s  %2d 筆   %s'
          % (band, band + 9, mark, len(by_band[band]),
             ' '.join(sorted(by_band[band]))))
print()
op = {}
for x in residue:
    op[x['opinion']] = op.get(x['opinion'], 0) + 1
print('=== 依判讀結果 ===')
for k, v in sorted(op.items(), key=lambda kv: -kv[1]):
    print('  %-10s %2d 筆' % (k, v))
