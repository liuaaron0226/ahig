# -*- coding: utf-8 -*-
"""校準集「可得 45」之取文路徑分析——⚠️ 擁有者待決之二選一並未涵蓋全部。

## 🚨 本檔要回答的問題

擁有者面前的選擇被陳述為二選一：
**甲＝校準集縮成 45 篇（契約不動）｜乙＝開 PDF 解析（需 GROBID／Docling，n+8 所擋）。**

**⚠️ 但「可得 45」不是同質的 45 篇**——本檔把它拆開，看每條路各買到什麼。

## 先被證據否定的一個假設（記在這裡，因為它省下了一整輪的白工）

本室原本假設：那些 `available-*` 之所以沒取到全文，是**當初查法沒命中**
（例如只用 DOI 查而未用 PMID），故重查 Europe PMC 或有斬獲。

**🚨 實查 34 筆之 manifest：全部都做過 europe-pmc 嘗試，且結論全部是 `miss`。**
即 Europe PMC 對這些文獻沒有 PMCID，**⚠️ 重查不會有新結果，該路徑已窮盡。**

## ⚠️ 過程中本室犯的一個錯，一併記

第一次統計時本室**猜** manifest 的鍵名為 `attempts[].source`，
得到「34 筆全部沒有 europe-pmc 嘗試」這張表——**🚨 那是假的，實際鍵名是 `sourceId`。**

**⚠️ 而 `m1_step3_acquire.py` 的註解裡就寫著上一次猜鍵名的教訓**
（「第一次執行時我猜了五個鍵，全印 0」）。**🚨 同一個檔案裡的教訓，本室隔幾輪又犯一次。**
已改為**先傾印實際結構再統計**。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：每一篇之取文狀態，及其 Europe PMC 嘗試之結論。
- 🚨 查不到：**landing-page 之頁面實際是否含可解析全文**——⚠️ 那要真的去抓才知道，
  而抓取與解析屬新能力，🚫 本室不自行開通。故 16 這個數是**「需要 HTML 途徑」的上界**，
  不是「HTML 途徑必可取得」的保證。
"""
import io
import json
import os
import sys
from collections import Counter

sys.path.insert(0, 'ahig')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
from ahig.search.fulltext import _artifact_dir  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
inv = json.load(io.open(S + 'm1_step3_inventory.json', encoding='utf-8'))
bf = json.load(io.open(S + 'm1_step3_backfill.json', encoding='utf-8'))
OBT = set(bf['obtainableDefinition'])

final = {r['candidateId']: r['status'] for r in inv['records']
         if r['status'] in OBT}
for pool in bf['pools']:
    for r in pool.get('backfilled') or []:
        if r.get('accepted'):
            final[r['candidateId']] = r['status']

counts = Counter(final.values())
total = sum(counts.values())

# ── Europe PMC 是否已窮盡 ────────────────────────────────────────
# 🚨 鍵名以實際傾印為準，不猜（見檔頭）。
epmc = Counter()
for cid, st in final.items():
    if st == 'acquired':
        continue
    man = json.load(io.open(_artifact_dir(cid) / 'manifest.json',
                            encoding='utf-8'))
    hits = [a for a in (man.get('attempts') or [])
            if a.get('sourceId') == 'europe-pmc']
    epmc[hits[0].get('conclusion') if hits else 'no-attempt'] += 1

print('=== 「可得 %d」之組成 ===' % total)
LABEL = {
    'acquired': '✅ 全文已在手（Europe PMC JATS）',
    'available-pdf': '🚨 僅 PDF 連結 → 需 PDF 解析（n+8 所擋）',
    'available-landing-page': '🚨 僅出版社頁面 → 需 HTML 解析（本 repo 無此解析器）',
}
for st, n in counts.most_common():
    print('   %-24s %2d  %s' % (st, n, LABEL.get(st, st)))
print()
print('=== Europe PMC 路徑是否已窮盡（對非 acquired 之 %d 筆）==='
      % (total - counts['acquired']))
for conc, n in epmc.most_common():
    print('   結論 %-12s %2d 筆 %s' % (conc, n,
          '→ ⚠️ 無 PMCID，重查無用，該路徑已窮盡' if conc == 'miss' else ''))

print()
print('=== 二選一各買到什麼 ===')
print('   甲（縮成 45、契約不動）  → 有文可萃仍只有 %d 篇，其餘 %d 篇無文'
      % (counts['acquired'], total - counts['acquired']))
print('   乙（開 PDF 解析）        → 再加 %d 篇＝%d 篇；🚨 landing-page 之 %d 篇仍取不到'
      % (counts['available-pdf'],
         counts['acquired'] + counts['available-pdf'],
         counts['available-landing-page']))
print('   🚨 兩條路都不足以讓 %d 篇全部有文。' % total)
print('   ⚠️ landing-page 那 %d 篇需要的是 **HTML 解析**，與 PDF 解析是不同能力——'
      % counts['available-landing-page'])
print('      🚨 原本的二選一沒有涵蓋它。')

doc = {
    'schemaVersion': 1,
    'documentType': 'calibration-fulltext-route-analysis',
    'purpose': ('Splits the 45 obtainable records by what it would actually '
                'take to get text out of them, because the owner decision was '
                'framed as PDF-route-or-shrink and neither reaches all 45.'),
    'population': ('The 60-record calibration set after the n+103 backfill, '
                   'restricted to records whose status is in '
                   'obtainableDefinition.'),
    'countingUnit': 'publication',
    'criterion': 'status in %s' % sorted(OBT),
    'obtainableTotal': total,
    'byRoute': dict(counts),
    'routeMeaning': {
        'acquired': 'JATS full text already downloaded from Europe PMC.',
        'available-pdf': 'OA location is a PDF; extraction needs a PDF parser '
                         '(GROBID/Docling), which n+8 bars from unilateral '
                         'installation.',
        'available-landing-page': 'OA location is a publisher landing page; '
                                  'extraction needs an HTML full-text parser, '
                                  'which this repo does not have at all '
                                  '(only parse_jats and parse_tei exist).',
    },
    'europePmcExhausted': dict(epmc),
    'europePmcNote': ('Every non-acquired record was attempted at Europe PMC '
                      'and every one came back a miss, so those works have no '
                      'PMCID. Re-querying gains nothing; that route is done. '
                      'This refutes the hypothesis that the earlier lookup was '
                      'too narrow.'),
    'decisionImpact': {
        'optionA_shrinkTo45': '%d of %d still have no text' % (
            total - counts['acquired'], total),
        'optionB_enablePdf': 'reaches %d of %d; the %d landing-page records '
                             'remain out of reach' % (
                                 counts['acquired'] + counts['available-pdf'],
                                 total, counts['available-landing-page']),
        'uncoveredByBothOptions': counts['available-landing-page'],
        'note': 'The landing-page records need HTML parsing, a different '
                'capability from PDF parsing. The two-way choice as put to the '
                'owner does not cover them.',
    },
    'coverageStatement': ('Whether a given landing page actually serves '
                          'parseable full text is not checked here -- that '
                          'needs fetching, which is a new capability this room '
                          'does not enable on its own. So 16 is an upper bound '
                          'on what an HTML route could reach, not a promise.'),
    'contentNote': 'Counts and status labels only. No literature content.',
}
doc['analysisHash'] = content_hash(doc['byRoute'])
io.open(S + 'n438_fulltext_route.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn438_fulltext_route.json' % S)
