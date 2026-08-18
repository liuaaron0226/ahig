# -*- coding: utf-8 -*-
"""🚨 下結論前先問：協調者算那張表時，看得到那 2 筆命中嗎？

⚠️ 這一步不能跳。若他當時只看得到 150/200（1 命中，`ad555302` 在
第 25 筆），而 `7c2bf4df` 是我第 163 筆才判出來的，
**那他的前提在他寫的當下可能是對的**——那就不是「他錯」，
是資訊時間差。**指控之前先算清楚，這與 n+64「可驗證 vs 憑信任」同理。**

本檔看得到：兩筆命中各自落在抽驗樣本的第幾筆、屬哪個分塊、
以及該分塊是在哪個 commit 推送的。
本檔看不到：協調者實際讀到哪個 commit（我只能由其自述推斷）。
"""
import glob
import io
import json
import subprocess

s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
ids = s['sample']['candidateIds']
pos = {c[-8:]: i for i, c in enumerate(ids)}

hits = {}
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        if v[0] in ('advance', 'unclear'):
            hits[k] = (pos[k], v[0], p.split('/')[-1].split('\\')[-1])

print('抽驗樣本中之命中：')
for k, (i, op, f) in sorted(hits.items(), key=lambda x: x[1][0]):
    lo = (i // 25) * 25
    out = subprocess.run(
        ['git', 'log', '--format=%h %ad %s', '--date=iso', '-1', '--',
         '.scratch/n68_tail_dec_%03d.json' % lo],
        capture_output=True, text=True, encoding='utf-8')
    print('  第 %3d 筆  %s  %-8s  來自 %s' % (i, k, op, f))
    print('           該分塊之 commit：%s' % out.stdout.strip())

print()
print('協調者自述其於 n+71 時所見：`origin/claude/safety-pass-2` 在 711002c'
      '（抽驗 150/200，1 命中）')
out = subprocess.run(['git', 'log', '--format=%h %ad %s', '--date=iso', '-1',
                      '711002c'], capture_output=True, text=True,
                     encoding='utf-8')
print('  711002c = %s' % out.stdout.strip())
print()
print('🚨 結論：`7c2bf4df` 落在第 163 筆，屬 [150:175] 分塊，')
print('   **於 711002c 之後才推送**——他寫 n+71 那張表時看不到它。')
print('   ⚠️ 故「window 固定 177」在他寫的當下，以他能看到的資料'
      '（1 命中且該命中在第 25 筆、位於 window 之外？）是否成立，')
print('   需另外算——見下。')

# 以「只有 ad555302 一筆命中」重算：它是否會移動 window？
OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')
w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
page_of = {it['candidateId']: it['page'] for it in w['items']}
seq_of = {it['candidateId']: i for i, it in enumerate(w['items'], start=1)}
for k in hits:
    full = next(c for c in ids if c.endswith(k))
    print('   %s  page %d  seq %d' % (k, page_of[full], seq_of[full]))
print()
print('⚠️ 逐頁連續判畢至 p279（seq 6975）。兩筆命中之 seq 皆 > 6975，')
print('   **即兩筆都在目前序列尾端之後**——只要有任一筆併入，')
print('   「最後一筆相關」就會往後移，window 必然縮短。')
print('   🚨 故即使只有 `ad555302` 一筆，「window 固定 177」也不成立。')
