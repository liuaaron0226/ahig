# -*- coding: utf-8 -*-
"""n+63（二）之改判：`518513f1` unclear → exclude，寫入 n+43 覆蓋層。

⚠️ 執行順序照 n+62 三段式，且本輪刻意先做第一步（上輪之教訓）：
  1. **先核對實質判準**：該筆結局軸為「網球擊球技能表現」，
     依 n+63（一）技能表現列為結局軸出局 → 實質判準說「應改判」。
  2. **再量測影響**：Δwindow = 0（45 → 45）。
  3. 影響為零 → 照裁定執行，同輪報備；不必請示。

⚠️ 依據為 **n+59（Ａ）掛待裁之暫置**，不是 n+43（甲）
——協調者於 n+63（二）明確更正本執行室原先之引據錯誤：
（甲）是「判讀時規則已存在但套錯」之事實錯誤更正，本案為
「新裁定適用於掛待裁之暫置」。結論相同，惟依據寫錯會使 M1
稽核誤判該筆性質。

寫入 `post-ruling-reclassification.json`（n+43 覆蓋層），
不寫棘輪檔——棘輪只表示得出三種升級方向，降級會被其 assert 擋下。
`judgements.json` 為 append-only，不改寫。
"""
import io
import json

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
OUT = (ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
       + '/standard-full-screen-pass-1')
DEST = OUT + '/post-ruling-reclassification.json'

CHANGES = {
    '518513f1': ('exclude', 'n+63 (一)(二)', ['outcome-adjacent',
                                              'skill-performance']),
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
            'basis': 'n+59 (A) parked-pending-ruling placeholder, NOT n+43 (A)',
            'tags': tags,
            'note': ('Skill performance (stroke accuracy, serve success, '
                     'putting) ruled an outcome-axis exclusion per n+63, on '
                     'the same footing as immune outcomes (n+42) and '
                     'cognitive function (n+35). Order per n+62: substantive '
                     'criterion checked FIRST, impact measured second '
                     '(Delta window = 0, 45 -> 45). Tagged for the M1 '
                     'contract review: zero re-screening to recover.'),
        })
        added.append((cid[-8:], it['page'], old, new, ruling))

assert len(added) == len(CHANGES), added
doc['ruling'] = (str(doc.get('ruling', '')) + '; extended per n+63 (二)'
                 ).lstrip('; ')
json.dump(doc, io.open(DEST, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('entries now:', len(doc['entries']))
for a in added:
    print('  %s p%-4d %s -> %s  [%s]' % a)
