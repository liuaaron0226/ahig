"""n+50 乙：產生 page 212–219 單向棘輪重篩之工作清單。

母體：page 212–219 中 worksheet abstract 為空、且已判讀之記錄（實測 197 筆）。
對每筆附上補摘要結果，供逐筆重讀。

⚠️ 只輸出 candidateId、原判、摘要「是否取得」與長度到 .scratch；
摘要內容留在 AHIG_PRIVATE_ROOT，符合 n+48 內容制衛生。
"""
import json, os, sys

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
DEST = RUN + '/abstract-enrichment'

w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}

ab = json.load(open(DEST + '/abstracts.json', encoding='utf-8')) \
    if os.path.exists(DEST + '/abstracts.json') else {}
pv_raw = json.load(open(DEST + '/provenance.json', encoding='utf-8')) \
    if os.path.exists(DEST + '/provenance.json') else {}
pv = pv_raw.get('records', pv_raw)

rows = []
for it in w['items']:
    if not (212 <= it['page'] <= 219):
        continue
    cid = it['candidateId']
    if cid not in op:
        continue
    if (it.get('abstract') or '').strip():
        continue
    rows.append({
        'candidateId': cid, 'seq': it['seq'], 'page': it['page'],
        'year': it.get('publicationYear'),
        'original': op[cid],
        'enrichStatus': (pv.get(cid) or {}).get('status', 'not-attempted'),
        'abstractChars': len(ab.get(cid, '')),
    })

json.dump({'documentType': 'n50-rescreen-worklist',
           'ruling': 'n+50 (乙) one-way ratchet',
           'segment': 'page 212-219',
           'count': len(rows), 'rows': rows},
          open('.scratch/n50_rescreen_list.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

from collections import Counter
print('worklist', len(rows))
print('original :', dict(Counter(r['original'] for r in rows)))
print('enrich   :', dict(Counter(r['enrichStatus'] for r in rows)))
got = [r for r in rows if r['abstractChars'] > 0]
print('with abstract now:', len(got))
