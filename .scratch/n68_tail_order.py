# -*- coding: utf-8 -*-
"""尾端抽驗判讀之**順序核對**——獨立於各分塊建置檔。

⚠️ 第 336–337 輪教訓（頁 273 錯號）：編號由 worksheet 順序決定，
敘事順序不得覆蓋資料順序。頁面建置檔 `mk_p*.py` 自第 337 輪起
每檔自帶 assert；**尾端抽驗之六個分塊建置檔沒有**——第 348 輪查證發現。

🚨 這與 n+67（八）「誤讀檢查之涵蓋範圍」同型：我先前以為分塊檔各自帶
assert，實際 `grep assert` 六檔皆空。故補本檔集中核對，並**自報涵蓋範圍**。

本檔看得到：各 `n68_tail_dec_*.json` 之鍵順序 vs `n68_tail_sample.json`
之 `candidateIds[lo:hi]` 順序（以 short = 後 8 碼比對）。
本檔看不到：判讀內容對錯、樣本抽取本身是否正確、未產出之分塊。
"""
import glob
import io
import json

s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
ids = s['sample']['candidateIds']
assert len(ids) == 200, len(ids)
shorts = [c[-8:] for c in ids]

files = sorted(glob.glob('.scratch/n68_tail_dec_*.json'))
print('涵蓋自報：樣本 %d 筆；找到分塊判讀檔 %d 個' % (len(ids), len(files)))
bad = []
covered = 0
for p in files:
    lo = int(p.split('_')[-1].split('.')[0])
    got = list(json.load(io.open(p, encoding='utf-8')).keys())
    want = shorts[lo:lo + len(got)]
    ok = got == want
    covered += len(got)
    if not ok:
        first = next((i for i, (a, b) in enumerate(zip(got, want)) if a != b),
                     min(len(got), len(want)))
        bad.append((p, lo + first, got[first:first + 1], want[first:first + 1]))
    print('  %-32s [%3d:%3d] %d 筆  %s'
          % (p.split('/')[-1], lo, lo + len(got), len(got),
             'OK' if ok else '**順序不符**'))
print()
print('已判 %d/%d 筆；未判 %d 筆' % (covered, len(ids), len(ids) - covered))
if bad:
    print('🚨 順序不符明細：%s' % bad)
    raise SystemExit(1)
print('順序核對 PASS（🚨 順序對不代表判讀對，此檔只看順序）')
