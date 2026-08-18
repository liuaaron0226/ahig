"""n+50 補強：對 not-found 之記錄改用其他識別碼重試。

發現：`pmcid` 失敗 12 筆全都另有 pmid——原腳本一筆只試一種識別碼
（優先序 pmcid > pmid > doi），該筆在 PMC 索引查不到就記 not-found，
但它的 pmid 其實查得到。這是 fallback 缺口，不是資料缺失。

本腳本只處理已記 not-found 者，依序改試其餘識別碼。
成功者更新 provenance 為 enriched 並寫入 abstracts；
全部試完仍失敗者標 `not-found-all-ids`，**與只試過一種的 not-found
明確可分**（延續 n+50 之「未嘗試 vs 已確認」原則）。

符合 n+48 預先授權：不動 ahig/、方向為更完整、同輪報備實測。
"""
import json, os, sys, time, urllib.parse

os.environ.setdefault('AHIG_PRIVATE_ROOT', r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')
from ahig.search.fulltext import UrllibBinaryTransport

ROOT = os.environ['AHIG_PRIVATE_ROOT']
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
DEST = RUN + '/abstract-enrichment'
SEARCH = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
MIN_INTERVAL = 1.2


class Paced:
    def __init__(self, inner):
        self.inner, self._last, self.calls = inner, 0.0, 0

    def get_bytes(self, *, url, headers=None):
        wait = MIN_INTERVAL - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        self.calls += 1
        return self.inner.get_bytes(url=url, headers=headers)


def atomic_dump(obj, path):
    tmp = path + '.tmp'
    with open(tmp, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False)
    os.replace(tmp, path)


def one(ids, k):
    v = ids.get(k)
    if isinstance(v, list):
        v = v[0] if v else None
    return str(v).strip() if v else None


def main():
    ab_path, pv_path = DEST + '/abstracts.json', DEST + '/provenance.json'
    abstracts = json.load(open(ab_path, encoding='utf-8'))
    doc = json.load(open(pv_path, encoding='utf-8'))
    prov = doc['records']
    pool = {c['candidateId']: (c.get('identifiers') or {})
            for c in json.load(open(RUN + '/candidate-pool/candidates.json',
                                    encoding='utf-8'))}

    todo = [cid for cid, r in prov.items() if r['status'] == 'not-found']
    print('not-found to retry:', len(todo), flush=True)

    t = Paced(UrllibBinaryTransport(attempts=3, timeout=60))
    fixed = 0
    for cid in todo:
        ids = pool.get(cid, {})
        tried = prov[cid].get('idKind')
        # 依序試其餘識別碼
        cands = []
        for kind, q in (('pmcid', lambda v: 'PMCID:%s' % v),
                        ('pmid', lambda v: 'EXT_ID:%s AND SRC:MED' % v),
                        ('doi', lambda v: 'DOI:"%s"' % v)):
            if kind == tried:
                continue
            v = one(ids, kind)
            if v:
                cands.append((kind, q(v)))
        if not cands:
            prov[cid]['status'] = 'not-found-all-ids'
            prov[cid]['retriedKinds'] = []
            continue
        got = False
        for kind, q in cands:
            url = SEARCH + '?' + urllib.parse.urlencode(
                {'query': q, 'resultType': 'core', 'format': 'json',
                 'pageSize': 1})
            try:
                ex = t.get_bytes(url=url, headers={
                    'Accept': 'application/json',
                    'User-Agent': 'AHIG/0.2.1 fulltext-calibration'})
            except Exception:
                continue
            if not 200 <= int(ex.get('status') or 0) < 300:
                continue
            try:
                body = json.loads(ex['body'].decode('utf-8'))
            except Exception:
                continue
            hits = (body.get('resultList') or {}).get('result') or []
            if not hits:
                continue
            a = (hits[0].get('abstractText') or '').strip()
            prov[cid]['retriedKinds'] = [k for k, _ in cands]
            prov[cid]['resolvedByIdKind'] = kind
            if a:
                prov[cid]['status'] = 'enriched'
                prov[cid]['hasAbstract'] = True
                prov[cid]['abstractChars'] = len(a)
                abstracts[cid] = a
                fixed += 1
            else:
                prov[cid]['status'] = 'upstream-no-abstract'
                prov[cid]['hasAbstract'] = False
            got = True
            break
        if not got:
            prov[cid]['status'] = 'not-found-all-ids'
            prov[cid]['retriedKinds'] = [k for k, _ in cands]

    doc['records'] = prov
    doc['retryNote'] = ('not-found-all-ids means every available identifier '
                        'was tried; not-found means only the first-choice '
                        'identifier was tried')
    atomic_dump(abstracts, ab_path)
    atomic_dump(doc, pv_path)

    from collections import Counter
    print('recovered by retry:', fixed, '| httpCalls', t.calls)
    print('status now:', dict(Counter(v['status'] for v in prov.values())))


if __name__ == '__main__':
    main()
