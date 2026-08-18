"""n+50 乙：輸出重篩段某一頁之新摘要，供逐筆重讀。

只印到終端供判讀，不寫入 .scratch（摘要內容留在 AHIG_PRIVATE_ROOT）。
用法：python .scratch/n50_show.py <page>
"""
import json, sys

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
DEST = RUN + '/abstract-enrichment'

page = int(sys.argv[1])
w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
ab = json.load(open(DEST + '/abstracts.json', encoding='utf-8'))
pv = json.load(open(DEST + '/provenance.json', encoding='utf-8'))['records']

n = 0
for it in w['items']:
    if it['page'] != page:
        continue
    cid = it['candidateId']
    if cid not in op or (it.get('abstract') or '').strip():
        continue
    n += 1
    st = (pv.get(cid) or {}).get('status', 'not-attempted')
    print('--- %s seq%s [%s] %s' % (cid[-8:], it['seq'], op[cid], st))
    print('Y:%s T:%s' % (it.get('publicationYear'), it.get('publicationTypes')))
    print('TITLE: %s' % it.get('title'))
    a = ab.get(cid)
    if a:
        print('ABS: %s' % a[:1500])
    print()
print('[page %d: %d no-abstract records, %d now enriched]'
      % (page, n, sum(1 for it in w['items'] if it['page'] == page
                      and it['candidateId'] in ab)))
