# -*- coding: utf-8 -*-
"""n+70（甲）：把 200 筆尾端抽驗判讀併入主篩，並列入 p 值序列排除清單。

⚠️ **兩件事必須同時做，缺一即錯**：
  • 只 append judgements 而不列排除清單 → 200 筆亂序記錄接進 labels 序列，
    windowSize 由 177 掉到 37（已實測，見 `n70_measure.py`）——語意壞掉；
  • 只列排除清單而不 append judgements → 寫入器會擋（排除清單只適用已篩畢
    者，`evaluate_termination` 對未篩畢者丟 TerminationError）。

⚠️ 產出兩份：
  1. `.scratch/n70_std_tail.json`——判讀 entries，餵 `app.py` 固化；
  2. 直接改寫 `p-score-sequence-exclusions.json`（**該檔非 append-only**，
     其語意本就是「目前排除中」之集合，term.py 依頁數自動納回）。

🚨 排除清單之 `reintegrationRule` 為「判讀進度涵蓋該頁時自動移出」。
本批最遠一筆在 p364（＝全池最後一頁），**故最後一筆要到全部篩完才納回**
——n+70（乙）已明白告知此後果，本檔不隱藏它。

⚠️ 順序：entries 依 **worksheet 順序**輸出，不是抽驗順序
（第 336–337 輪錯號教訓：資料順序決定編號）。
"""
import glob
import io
import json

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
judged = {e['candidateId'] for e in d['entries']}

s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
ids = s['sample']['candidateIds']
short2full = {c[-8:]: c for c in ids}
dec = {}
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        dec[short2full[k]] = v
assert len(dec) == 200 == len(set(dec)), len(dec)
assert not (set(dec) & judged), '有已判過者，append 會被擋'

want = set(ids)
rows = [(i, it) for i, it in enumerate(w['items'], start=1)
        if it['candidateId'] in want]
assert len(rows) == 200, len(rows)

entries = [{'candidateId': it['candidateId'],
            'opinion': dec[it['candidateId']][0],
            'reason': dec[it['candidateId']][1]} for _, it in rows]
json.dump(entries, io.open('.scratch/n70_std_tail.json', 'w',
                           encoding='utf-8'), ensure_ascii=False, indent=1)
print('判讀 entries -> .scratch/n70_std_tail.json（%d 筆，worksheet 順序）'
      % len(entries))

# ---- 排除清單 ----
ep = OUT + '/p-score-sequence-exclusions.json'
doc = json.load(io.open(ep, encoding='utf-8'))
existing = {e['candidateId'] for e in doc['entries']}
assert not (existing & want), '與既有清單有交集'
before = len(doc['entries'])

add = [{'candidateId': it['candidateId'], 'page': it['page'], 'seq': seq,
        'source': 'n+57 尾端抽驗（200 筆隨機抽樣）',
        'ruling': '協調者第 n+70 輪（甲）'}
       for seq, it in rows]
doc['entries'] = sorted(doc['entries'] + add, key=lambda e: e['seq'])
doc['semantics'] += (
    '\n\n【n+70（甲）追加】第 n+57 尾端抽驗之 200 筆判讀亦列入本清單。'
    '其性質與原本者不同：原本者為「為解除前置條件而跳頁補判」，'
    '本批為「對剩餘池之獨立隨機稽核」。'
    '🚨 協調者於 n+70（丙）已指出「把獨立稽核之結果接進循序檢定之標籤流'
    '本身是範疇錯誤」，正解可能是永久獨立之第三態；'
    '在該裁定作成前，依（甲）先用既有排除清單機制。'
    '⚠️ 本批最遠一筆位於 p364（全池最後一頁），'
    '故實務上須篩至最後才會全部納回——n+70（乙）已載明此後果。')
io.open(ep, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1) + '\n')
print('排除清單 %d -> %d 筆（+%d）' % (before, len(doc['entries']), len(add)))
print('最遠一筆 page %d' % max(e['page'] for e in add))
