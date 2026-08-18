# -*- coding: utf-8 -*-
"""n+57 第二節【第 5 步】：傾印 200 筆尾端抽驗樣本，供逐筆判讀。

⚠️ 樣本順序即抽樣產物之 `candidateIds` 順序，**不重排**
（第 336–337 輪教訓：順序決定編號，敘事順序不得覆蓋資料順序）。

⚠️ 摘要來源優先序：worksheet 原始 `abstract` → `abstracts.json`
（第 344 輪教訓：worksheet 之 `abstract` 為原始欄位，
未判頁面尚未合併補摘要，只看它會低估涵蓋率）。

輸出 `.scratch/_tail.txt`（含 TITLE:／ABS: 全文，**不得 commit**，
已逐檔列名加入 .gitignore；n+65 一 2 禁 `git add -A`）。
用法：python -X utf8 .scratch/n68_step5_dump.py <起> <迄>
"""
import io
import json
import os
import sys

RUN = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run')
OUT = RUN + '/standard-full-screen-pass-1'
DEST = RUN + '/abstract-enrichment'

lo = int(sys.argv[1]) if len(sys.argv) > 1 else 0
hi = int(sys.argv[2]) if len(sys.argv) > 2 else 25

step3 = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
ids = step3['sample']['candidateIds']
assert len(ids) == 200, len(ids)

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
by = {it['candidateId']: it for it in w['items']}
ab = json.load(io.open(DEST + '/abstracts.json', encoding='utf-8'))
pv = json.load(io.open(DEST + '/provenance.json', encoding='utf-8'))['records']

chunk = ids[lo:hi]
lines = []
for i, cid in enumerate(chunk, start=lo):
    it = by[cid]
    raw = it['abstract']
    text = raw if (raw and raw != 'None') else ab.get(cid)
    st = (pv.get(cid) or {}).get('status', '(原始摘要)')
    lines.append('--- [%d] %s  p%s  %s' % (i, cid[-8:], it.get('page'), st))
    lines.append('Y:%s T:%s' % (it.get('publicationYear'),
                                it.get('publicationTypes')))
    lines.append('TITLE: %s' % it.get('title'))
    lines.append('ABS: %s' % ((text or '(無摘要)')[:1700]))
    lines.append('')

io.open('.scratch/_tail.txt', 'w', encoding='utf-8').write('\n'.join(lines))
print('dumped [%d:%d] = %d recs -> .scratch/_tail.txt' % (lo, hi, len(chunk)))
n_abs = sum(1 for cid in chunk
            if (by[cid]['abstract'] not in (None, 'None')) or ab.get(cid))
print('with-text %d/%d' % (n_abs, len(chunk)))
