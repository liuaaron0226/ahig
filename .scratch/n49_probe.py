"""n+49 診斷：查 Europe PMC 是否有摘要，只取存在與否。

依 n+49：只回報「上游有摘要者佔比」與年代分層佔比。
**不落地任何摘要內容**——只記布林值與長度，符合 n+48 內容制衛生。
沿用 PacedTransport 節流（n+48 已裁定保留並預先授權同類補強）。
不需 AHIG_CONTACT_EMAIL（Europe PMC 不要求）。
"""
import json, os, sys, time, urllib.parse

os.environ.setdefault('AHIG_PRIVATE_ROOT', r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')
from ahig.search.fulltext import UrllibBinaryTransport

SEARCH = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
MIN_INTERVAL = 1.2


class Paced:
    def __init__(self, inner):
        self.inner = inner
        self._last = 0.0
        self.calls = 0

    def get_bytes(self, *, url, headers=None):
        wait = MIN_INTERVAL - (time.monotonic() - self._last)
        if wait > 0:
            time.sleep(wait)
        self._last = time.monotonic()
        self.calls += 1
        return self.inner.get_bytes(url=url, headers=headers)


def query_for(row):
    if row.get('pmcid'):
        return 'PMCID:%s' % row['pmcid']
    if row.get('pmid'):
        return 'EXT_ID:%s AND SRC:MED' % row['pmid']
    if row.get('doi'):
        return 'DOI:"%s"' % row['doi']
    return None


def main():
    doc = json.load(open('.scratch/n49_sample.json', encoding='utf-8'))
    t = Paced(UrllibBinaryTransport(attempts=3, timeout=60))
    out = []
    for i, row in enumerate(doc['sample'], 1):
        q = query_for(row)
        rec = {'candidateId': row['candidateId'], 'year': row['year'],
               'idKind': ('pmcid' if row.get('pmcid') else
                          'pmid' if row.get('pmid') else
                          'doi' if row.get('doi') else None)}
        if q is None:
            rec['status'] = 'no-identifier'
            out.append(rec)
            continue
        url = SEARCH + '?' + urllib.parse.urlencode(
            {'query': q, 'resultType': 'core', 'format': 'json', 'pageSize': 1})
        try:
            ex = t.get_bytes(url=url, headers={
                'Accept': 'application/json',
                'User-Agent': 'AHIG/0.2.1 fulltext-calibration'})
        except Exception as exc:
            rec['status'] = 'transport-error'
            rec['detail'] = type(exc).__name__
            out.append(rec)
            print(i, rec['status'], flush=True)
            continue
        code = int(ex.get('status') or 0)
        if not 200 <= code < 300:
            rec['status'] = 'http-%d' % code
            out.append(rec)
            print(i, rec['status'], flush=True)
            continue
        try:
            body = json.loads(ex['body'].decode('utf-8'))
        except Exception:
            rec['status'] = 'bad-json'
            out.append(rec)
            continue
        hits = (body.get('resultList') or {}).get('result') or []
        if not hits:
            rec['status'] = 'not-found'
        else:
            ab = hits[0].get('abstractText')
            rec['status'] = 'found'
            # 只記存在與否＋長度，絕不落地內容
            rec['hasAbstract'] = bool(ab and ab.strip())
            rec['abstractChars'] = len(ab) if ab else 0
        out.append(rec)
        print(i, rec['status'], rec.get('hasAbstract'), flush=True)

    json.dump({'documentType': 'n49-abstract-availability-result',
               'anchor': doc['anchor'], 'httpCalls': t.calls,
               'results': out},
              open('.scratch/n49_result.json', 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)

    found = [r for r in out if r['status'] == 'found']
    withab = [r for r in found if r.get('hasAbstract')]
    print()
    print('sample', len(out), 'resolved', len(found), 'httpCalls', t.calls)
    print('UPSTREAM HAS ABSTRACT: %d/%d' % (len(withab), len(found)))
    for lo, hi, lab in ((0, 1999, 'pre-2000'), (2000, 2014, '2000-2014'),
                        (2015, 2030, '2015+')):
        g = [r for r in found if lo <= (r['year'] or 0) <= hi]
        gw = [r for r in g if r.get('hasAbstract')]
        if g:
            print('  %-10s %d/%d' % (lab, len(gw), len(g)))


if __name__ == '__main__':
    main()
