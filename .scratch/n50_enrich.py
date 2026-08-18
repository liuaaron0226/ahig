"""n+50 甲：前瞻批次補摘要——未判讀段之無摘要記錄。

依裁定：
  - 對象：未判讀且 worksheet abstract 為空者（實測 3,286 筆）
  - 來源：Europe PMC，依 PMCID / PMID / DOI
  - 節流：PacedTransport 1.2 秒（n+48 已裁定保留並預先授權）
  - 不需 AHIG_CONTACT_EMAIL
  - 摘要內容只寫 AHIG_PRIVATE_ROOT，不得進 repo
  - 溯源須讓「上游確認無摘要」與「未嘗試」可區分

產物（皆在 AHIG_PRIVATE_ROOT 之下）：
  abstract-enrichment/abstracts.json   candidateId -> abstract 內容
  abstract-enrichment/provenance.json  逐筆溯源（不含摘要內容，只含狀態）

可重入：已有結果者跳過，中斷後重跑安全。
"""
import json, os, sys, time, urllib.parse

os.environ.setdefault('AHIG_PRIVATE_ROOT', r'C:/Users/User/Desktop/claude/ahig-private')
sys.path.insert(0, 'ahig')
from ahig.search.fulltext import UrllibBinaryTransport

ROOT = os.environ['AHIG_PRIVATE_ROOT']
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
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


def ident_of(ids):
    def one(k):
        v = ids.get(k)
        if isinstance(v, list):
            v = v[0] if v else None
        return str(v).strip() if v else None
    return one('pmcid'), one('pmid'), one('doi')


def build_targets():
    """未判讀段之無摘要記錄（裁定甲），**外加** page 212-219 已判讀之
    無摘要記錄（裁定乙之重篩母體，197 筆）——後者若不補，單向棘輪
    重篩就沒有新資訊可讀，等於空轉。兩者皆只寫 AHIG_PRIVATE_ROOT。"""
    w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
    d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
    judged = {e['candidateId'] for e in d['entries']}
    pool = json.load(open(RUN + '/candidate-pool/candidates.json', encoding='utf-8'))
    ident = {c['candidateId']: (c.get('identifiers') or {}) for c in pool}
    out = []
    for it in w['items']:
        cid = it['candidateId']
        rescreen = 212 <= it['page'] <= 219 and cid in judged
        if cid in judged and not rescreen:
            continue
        if (it.get('abstract') or '').strip():
            continue
        pmcid, pmid, doi = ident_of(ident.get(cid, {}))
        out.append({'candidateId': cid, 'seq': it['seq'], 'page': it['page'],
                    'year': it.get('publicationYear'), 'rescreen': rescreen,
                    'pmcid': pmcid, 'pmid': pmid, 'doi': doi})
    # 重篩段優先：它擋住後續所有工作（n+50 第四節「重篩完成前不判新頁」）
    out.sort(key=lambda r: (not r['rescreen'], r['seq']))
    return out


def query_for(row):
    if row['pmcid']:
        return 'PMCID:%s' % row['pmcid'], 'pmcid'
    if row['pmid']:
        return 'EXT_ID:%s AND SRC:MED' % row['pmid'], 'pmid'
    if row['doi']:
        return 'DOI:"%s"' % row['doi'], 'doi'
    return None, None


def main():
    limit = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    os.makedirs(DEST, exist_ok=True)
    ab_path, pv_path = DEST + '/abstracts.json', DEST + '/provenance.json'
    abstracts = json.load(open(ab_path, encoding='utf-8')) if os.path.exists(ab_path) else {}
    # 收尾時寫的是含 metadata 的文件、中途寫的是扁平 dict；兩種都要能重入
    t = Paced(UrllibBinaryTransport(attempts=3, timeout=60))
    started = time.strftime('%Y-%m-%dT%H:%M:%S')
    prov = {}
    if os.path.exists(pv_path):
        loaded = json.load(open(pv_path, encoding='utf-8'))
        prov = loaded['records'] if isinstance(loaded.get('records'), dict) else loaded

    def write_prov(finished=None):
        """一律寫完整文件；中途存檔與收尾用同一格式，避免結構交替。"""
        json.dump({'documentType': 'abstract-enrichment-provenance',
                   'ruling': 'n+50',
                   'source': 'Europe PMC REST search (resultType=core)',
                   'startedAt': started,
                   'finishedAt': finished or 'in-progress',
                   'minIntervalSec': MIN_INTERVAL, 'httpCalls': t.calls,
                   'note': ('status=upstream-no-abstract means the record was '
                            'found and confirmed to have no abstract; '
                            'no-identifier/transport-error/http-* mean the '
                            'lookup was not completed'),
                   'records': prov},
                  open(pv_path, 'w', encoding='utf-8'), ensure_ascii=False)

    targets = build_targets()
    todo = [r for r in targets if r['candidateId'] not in prov]
    if limit:
        todo = todo[:limit]
    print('targets %d  already done %d  todo %d' % (
        len(targets), len(prov), len(todo)), flush=True)

    n = 0
    for row in todo:
        cid = row['candidateId']
        q, kind = query_for(row)
        rec = {'idKind': kind, 'attemptedAt': time.strftime('%Y-%m-%dT%H:%M:%S'),
               'source': 'europepmc-search'}
        if q is None:
            # 與「上游確認無摘要」明確可分：這是未嘗試
            rec['status'] = 'no-identifier'
            rec['hasAbstract'] = None
            prov[cid] = rec
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
            rec['hasAbstract'] = None
            prov[cid] = rec
            continue
        code = int(ex.get('status') or 0)
        if not 200 <= code < 300:
            rec['status'] = 'http-%d' % code
            rec['hasAbstract'] = None
            prov[cid] = rec
            continue
        try:
            body = json.loads(ex['body'].decode('utf-8'))
        except Exception:
            rec['status'] = 'bad-json'
            rec['hasAbstract'] = None
            prov[cid] = rec
            continue
        hits = (body.get('resultList') or {}).get('result') or []
        if not hits:
            rec['status'] = 'not-found'      # 查過但上游沒有這筆
            rec['hasAbstract'] = None
        else:
            ab = (hits[0].get('abstractText') or '').strip()
            if ab:
                rec['status'] = 'enriched'
                rec['hasAbstract'] = True
                rec['abstractChars'] = len(ab)
                abstracts[cid] = ab
            else:
                # 明確：查到了紀錄，上游確認沒有摘要（≠ 未嘗試）
                rec['status'] = 'upstream-no-abstract'
                rec['hasAbstract'] = False
        prov[cid] = rec
        n += 1
        if n % 50 == 0:
            json.dump(abstracts, open(ab_path, 'w', encoding='utf-8'),
                      ensure_ascii=False)
            write_prov()
            done = sum(1 for v in prov.values() if v['status'] == 'enriched')
            print('%d/%d  enriched %d  calls %d' % (
                n, len(todo), done, t.calls), flush=True)

    json.dump(abstracts, open(ab_path, 'w', encoding='utf-8'), ensure_ascii=False)
    write_prov(time.strftime('%Y-%m-%dT%H:%M:%S'))

    from collections import Counter
    c = Counter(v['status'] for v in prov.values())
    print()
    print('provenance', dict(c.most_common()))
    print('abstracts stored', len(abstracts), 'httpCalls', t.calls)


if __name__ == '__main__':
    main()
