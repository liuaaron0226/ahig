# -*- coding: utf-8 -*-
"""n+52（二）：建立 [title-only-judged] 全文期名冊。

母體：**全體已判之無摘要記錄**中，**補摘要無法取得摘要者**
（`upstream-no-abstract` / `no-identifier` / `not-found-all-ids`）。
這批僅憑標題判讀，且上游本來就沒有摘要可補。

⚠️ **n+53 後之範圍擴充（原為 p<212）**：n+52 建檔時只涵蓋
p<212，因當時該區段是重篩母體之外緣。**惟 n+53 裁定明白以本名冊
為「標題具名即可判 exclude」之 recall 保護依據**——
「recall 保護已經由別的機制提供，不需要用標籤再做一次」。
**保護若只到 p211，則 p212 以後依該裁定判 exclude 之同型記錄
就沒有任何機制接住。** 故改為涵蓋全體已判頁。
本檔 `affectsTerminationStatistic: False`，擴充只增加全文取得筆數，
不動任何標籤與序列——方向為純保護，建檔前後統計量須完全相同。

⚠️ 依裁定：
  - **不改判、不動標籤序列**——升級會使這批（全在尾端窗口之外）
    的 k_min 變大、pScore 下降，方向反而有利於停止。
  - 本檔比照 post-ruling-deferred-tags.json，**明載不得被終止
    統計量讀取**。
  - 無論篩選判讀為何，一律取全文並於萃取期逐筆覆核。

只寫 AHIG_PRIVATE_ROOT；.scratch 僅留腳本與計數。
"""
import json, os

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
DEST = OUT + '/title-only-judged-roster.json'

UNFIXABLE = {'upstream-no-abstract', 'no-identifier', 'not-found-all-ids'}

w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}

# 有效標記（含兩層覆蓋）——名冊只記錄，不改動
rc = OUT + '/post-ruling-reclassification.json'
if os.path.exists(rc):
    for e in json.load(open(rc, encoding='utf-8'))['entries']:
        op[e['candidateId']] = e['effectiveDecision']
rs = OUT + '/post-ruling-abstract-rescreen.json'
if os.path.exists(rs):
    for e in json.load(open(rs, encoding='utf-8'))['entries']:
        op[e['candidateId']] = e['effectiveDecision']

pv = json.load(open(RUN + '/abstract-enrichment/provenance.json',
                    encoding='utf-8'))['records']

entries = []
for it in w['items']:
    cid = it['candidateId']
    if cid not in op:
        continue
    if (it.get('abstract') or '').strip():
        continue
    st = (pv.get(cid) or {}).get('status')
    if st not in UNFIXABLE:
        continue
    entries.append({
        'candidateId': cid,
        'seq': it['seq'],
        'page': it['page'],
        'publicationYear': it.get('publicationYear'),
        'screeningDecision': op[cid],
        'enrichmentStatus': st,
        'tag': 'title-only-judged',
    })

doc = {
    'schemaVersion': 1,
    'documentType': 'title-only-judged-roster',
    'source': 'standard-full-screen-pass-1',
    'ruling': 'n+52 (二), scope widened per n+53 (一)(二)',
    'producedBy': 'claude-opus-5[1m] executor-session',
    'semantics': (
        'Records judged from TITLE ONLY: no abstract in the pool and none '
        'obtainable upstream. This file is a FULL-TEXT-PHASE roster only. '
        'It records; it does not relabel. It MUST NOT be read by the '
        'termination statistic — screeningDecision here is a copy of the '
        'effective label, not an override. Every entry is to be acquired in '
        'full text and re-checked during extraction regardless of its '
        'screening decision; corrections, if any, go through n+43 class (甲) '
        'factual-error correction, not through this file.'),
    'affectsTerminationStatistic': False,
    'segment': (
        'ALL judged pages. Originally page < 212 under n+52 (二); widened '
        'after n+53 made this roster the stated recall-protection mechanism '
        'for title-only records judged exclude under independent-axis-first. '
        'Protection that stopped at page 211 would leave later records of the '
        'same kind uncovered. Widening only adds full-text acquisitions; it '
        'changes no label and no sequence position.'),
    'entryCount': len(entries),
    'entries': entries,
}
json.dump(doc, open(DEST, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)

from collections import Counter
print('roster entries:', len(entries))
print('by enrichmentStatus:', dict(Counter(e['enrichmentStatus'] for e in entries)))
print('by screeningDecision:', dict(Counter(e['screeningDecision'] for e in entries)))
print('year range:', min(e['publicationYear'] or 9999 for e in entries),
      '-', max(e['publicationYear'] or 0 for e in entries))
