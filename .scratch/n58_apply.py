# -*- coding: utf-8 -*-
"""n+58（一）（二）之改判：寫入 post-ruling-reclassification.json。

⚠️ 為何用這個檔而不是棘輪檔：
  - `post-ruling-abstract-rescreen.json` 之棘輪只表示得出
    exclude→advance／unclear→advance／exclude→unclear 三種升級，
    **本次為 unclear→exclude 之降級，棘輪 assert 會擋下**（正確行為）。
  - `post-ruling-reclassification.json` 為 n+43 裁定所建之覆蓋層，
    現含 79 筆 unclear→exclude，**方向與本次相同**，是對的載體。

⚠️ 影響已先量測（`.scratch/n58_impact.py`）：三筆皆位於最後一次
命中之前，**Δwindow = 0、ΔpScore = 0.000000**，不觸及停止條件。
量測在前、改判在後，非事後找理由。

只寫 AHIG_PRIVATE_ROOT；judgements.json 為 append-only，不改寫。
"""
import json
import os

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
OUT = (ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
       + '/standard-full-screen-pass-1')
DEST = OUT + '/post-ruling-reclassification.json'

# suffix -> (新判, 裁定依據, 掛牌)
CHANGES = {
    '2eeb3e43': ('exclude', 'n+58 (一)', ['intermittent-team-sport']),
    '5e4acb5a': ('exclude', 'n+58 (二)', ['methodological']),
    '54e29037': ('exclude', 'n+58 (二) 同型適用', ['methodological']),
}

w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
doc = json.load(open(DEST, encoding='utf-8'))
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
        # 只允許本次明列之方向，避免誤寫
        assert (old, new) == ('unclear', 'exclude'), (cid, old, new)
        doc['entries'].append({
            'candidateId': cid,
            'seq': it['seq'],
            'page': it['page'],
            'originalOpinion': old,
            'effectiveDecision': new,
            'ruling': ruling,
            'tags': tags,
            'note': ('Downgraded per n+58. Impact measured BEFORE applying: '
                     'all three sit before the last hit, so windowSize and '
                     'pScore are unchanged (delta 0.000000). Recorded here '
                     'rather than in the ratchet file because the ratchet '
                     'represents upgrades only and would (correctly) refuse '
                     'a downgrade.'),
        })
        added.append((cid[-8:], it['page'], old, new, ruling))

assert len(added) == len(CHANGES), added
doc['ruling'] = (str(doc.get('ruling', '')) + '; extended per n+58 (一)(二)'
                 ).lstrip('; ')
json.dump(doc, open(DEST, 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

print('entries now:', len(doc['entries']))
for a in added:
    print('  %s p%-4d %s -> %s  [%s]' % a)
