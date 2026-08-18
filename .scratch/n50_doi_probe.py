"""驗證：W4a-1 之 8 筆「無 DOI」記錄能否經 PMID/PMCID 反查出 DOI。

動機：W4a-1 的 OpenAlex 與 Unpaywall 兩個來源都需要 DOI，這 8 筆
因池中無 DOI 而被記為 not-applicable——三來源鏈實際只跑了一個。
若 Europe PMC 查得到它們的 DOI，另兩個來源就能跑，全文可得率
可能提高。

本腳本**只讀不寫**：查 DOI 並回報，不改任何產物、不觸發取全文。
沿用 PacedTransport 節流。
"""
import json, os, sys, time, urllib.parse

os.environ.setdefault('AHIG_PRIVATE_ROOT', r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')
from ahig.search.fulltext import UrllibBinaryTransport

ROOT = os.environ['AHIG_PRIVATE_ROOT']
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
SEARCH = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
MIN_INTERVAL = 1.2

WANT = {'5a33d637', 'b45cbb41', '34fb8361', 'ad6642f1',
        '714e7292', '9b8c549d', 'c7fd1548', '22ae0b5d',
        '975af339', '57ca3b60'}


def one(ids, k):
    v = ids.get(k)
    if isinstance(v, list):
        v = v[0] if v else None
    return str(v).strip() if v else None


def main():
    pool = {c['candidateId']: (c.get('identifiers') or {})
            for c in json.load(open(RUN + '/candidate-pool/candidates.json',
                                    encoding='utf-8'))}
    inner = UrllibBinaryTransport(attempts=3, timeout=60)
    last = [0.0]
    calls = [0]

    def get(url):
        wait = MIN_INTERVAL - (time.monotonic() - last[0])
        if wait > 0:
            time.sleep(wait)
        last[0] = time.monotonic()
        calls[0] += 1
        return inner.get_bytes(url=url, headers={
            'Accept': 'application/json',
            'User-Agent': 'AHIG/0.2.1 fulltext-calibration'})

    rows = []
    for cid, ids in pool.items():
        if cid[-8:] not in WANT:
            continue
        pmcid, pmid, doi = one(ids, 'pmcid'), one(ids, 'pmid'), one(ids, 'doi')
        rec = {'id': cid[-8:], 'poolDoi': doi, 'pmcid': pmcid, 'pmid': pmid}
        q = ('PMCID:%s' % pmcid if pmcid else
             'EXT_ID:%s AND SRC:MED' % pmid if pmid else None)
        if q is None:
            rec['result'] = 'no-identifier'
            rows.append(rec)
            continue
        url = SEARCH + '?' + urllib.parse.urlencode(
            {'query': q, 'resultType': 'core', 'format': 'json', 'pageSize': 1})
        try:
            ex = get(url)
            body = json.loads(ex['body'].decode('utf-8'))
        except Exception as exc:
            rec['result'] = 'error:' + type(exc).__name__
            rows.append(rec)
            continue
        hits = (body.get('resultList') or {}).get('result') or []
        if not hits:
            rec['result'] = 'not-found'
        else:
            h = hits[0]
            rec['result'] = 'found'
            rec['upstreamDoi'] = h.get('doi')
            rec['isOpenAccess'] = h.get('isOpenAccess')
            rec['inEPMC'] = h.get('inEPMC')
            rec['hasPDF'] = h.get('hasPDF')
        rows.append(rec)

    for r in rows:
        print(json.dumps(r, ensure_ascii=False))
    got = [r for r in rows if r.get('upstreamDoi')]
    print()
    print('probed %d  resolved-with-DOI %d  httpCalls %d'
          % (len(rows), len(got), calls[0]))
    oa = [r for r in got if r.get('isOpenAccess') == 'Y']
    print('of those, isOpenAccess=Y: %d' % len(oa))


if __name__ == '__main__':
    main()
