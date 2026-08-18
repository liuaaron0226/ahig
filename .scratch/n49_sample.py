"""n+49 診斷：抽 30 筆已判之無摘要記錄，供 Europe PMC 摘要可得性查驗。

抽樣錨定（seed）之選擇說明：
  n+49 指示「seed 由 queueHash 導出」。本 lane 之 worksheet／manifest
  皆無 queueHash 欄位（該欄屬 prevalence-audit lane 之抽樣母體概念）。
  故改用等效且同樣可驗證的錨定：**worksheet.json 之 SHA-256**——
  它同樣是抽樣母體本身的內容雜湊，任何人可重算複現。
  此一替代已在心跳中明講，不自行宣稱為 queueHash。

只輸出 candidateId 與識別碼，不含標題或摘要內容（n+48 內容制衛生）。
"""
import hashlib, json, os, random

RUN = r'C:/Users/User/Desktop/claude/ahig-private/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'

raw = open(OUT + '/worksheet.json', 'rb').read()
anchor = 'sha256:' + hashlib.sha256(raw).hexdigest()

w = json.loads(raw.decode('utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
judged = {e['candidateId'] for e in d['entries']}

pool = json.load(open(RUN + '/candidate-pool/candidates.json', encoding='utf-8'))
ident = {c['candidateId']: (c.get('identifiers') or {}) for c in pool}

# 母體：已判讀且 worksheet 中 abstract 為空者
noabs = [it for it in w['items']
         if it['candidateId'] in judged and not (it.get('abstract') or '').strip()]

seed = int(anchor.split(':')[1][:16], 16)
rng = random.Random(seed)
sample = rng.sample(noabs, 30)

rows = []
for it in sample:
    ids = ident.get(it['candidateId'], {})
    def one(k):
        v = ids.get(k)
        if isinstance(v, list):
            v = v[0] if v else None
        return str(v).strip() if v else None
    rows.append({
        'candidateId': it['candidateId'],
        'seq': it['seq'], 'page': it['page'],
        'year': it.get('publicationYear'),
        'pmid': one('pmid'), 'pmcid': one('pmcid'), 'doi': one('doi'),
    })

doc = {
    'documentType': 'n49-abstract-availability-sample',
    'anchor': anchor,
    'anchorNote': ('worksheet.json SHA-256; used in place of queueHash, '
                   'which this lane does not have'),
    'seedDerivation': 'int(anchor_hex[:16], 16)',
    'populationDefinition': 'judged records whose worksheet abstract is empty',
    'populationSize': len(noabs),
    'judgedTotal': len(judged),
    'sampleSize': len(rows),
    'sample': rows,
}
json.dump(doc, open('.scratch/n49_sample.json', 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

have = sum(1 for r in rows if r['pmid'] or r['pmcid'] or r['doi'])
print('anchor', anchor)
print('population(no-abstract & judged)', len(noabs), 'of judged', len(judged))
print('sample', len(rows), 'with any identifier', have)
years = {}
for r in rows:
    years[r['year']] = years.get(r['year'], 0) + 1
print('year spread', dict(sorted(years.items())))
