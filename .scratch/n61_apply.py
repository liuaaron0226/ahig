# -*- coding: utf-8 -*-
"""n+61（三）之改判：兩筆「已納入文獻之後續通信」寫入 n+43 覆蓋層。

⚠️ 範圍限於（Ａ）類——判讀當下明確記錄為待裁示、暫置 unclear 者：
  - `72580166`（第 253 輪判讀時即列為待裁事項第 1 項）
  - `76508848`（第 254 輪判讀時併入同一待裁事項）
`54e29037` 已由 n+58 判定並執行，屬（Ｂ）類，**不動**。

⚠️ 影響已先量測（`.scratch/n61_impact.py`）：兩筆皆位於最後一次
命中之前，**Δwindow = 0**（46 → 46）。依 n+59 第二節第二道閘，
影響為零者照裁定執行，不必再請示。

⚠️ `05fea7ad`（book-chapter）**不在本檔範圍**：依 n+61（二）
第三列，其內容無法判定是否含原始數據（上游無摘要且識別碼全查無），
**維持 unclear**——且其單獨改判之 Δwindow 為 +12，非零且方向
有利於停止，依同一道閘本就不得逕改。

只寫 AHIG_PRIVATE_ROOT；judgements.json 為 append-only，不改寫。
"""
import io
import json

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
OUT = (ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
       + '/standard-full-screen-pass-1')
DEST = OUT + '/post-ruling-reclassification.json'

CHANGES = {
    '72580166': ('exclude', 'n+61 (三)', ['methodological',
                                          'post-publication-correspondence']),
    '76508848': ('exclude', 'n+61 (三)', ['methodological',
                                          'post-publication-correspondence']),
}

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
doc = json.load(io.open(DEST, encoding='utf-8'))
existing = {e['candidateId'] for e in doc['entries']}

added = []
for it in w['items']:
    cid = it['candidateId']
    for suf, (new, ruling, tags) in CHANGES.items():
        if not cid.endswith(suf):
            continue
        assert cid in op, cid
        old = op[cid]
        assert cid not in existing, ('already in overlay: %s' % cid)
        assert (old, new) == ('unclear', 'exclude'), (cid, old, new)
        doc['entries'].append({
            'candidateId': cid,
            'seq': it['seq'],
            'page': it['page'],
            'originalOpinion': old,
            'effectiveDecision': new,
            'ruling': ruling,
            'tags': tags,
            'note': ('Post-publication correspondence on an included or '
                     'adjacent study: excluded on the publication-type axis '
                     'per n+61 (三), tagged [methodological], and added to '
                     'the new W4b list so the extraction phase checks each '
                     'included study for later correspondence. Impact '
                     'measured BEFORE applying: both sit before the last '
                     'hit, windowSize unchanged (46 -> 46).'),
        })
        added.append((cid[-8:], it['page'], old, new, ruling))

assert len(added) == len(CHANGES), added
doc['ruling'] = (str(doc.get('ruling', '')) + '; extended per n+61 (三)'
                 ).lstrip('; ')
json.dump(doc, io.open(DEST, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('entries now:', len(doc['entries']))
for a in added:
    print('  %s p%-4d %s -> %s  [%s]' % a)
