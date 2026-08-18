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
import json, os, re, sys, time, urllib.parse

# n+51（一）：標題碳水訊號——已驗證 16 倍鑑別力（advance 14.7% vs 0.9%）。
# ⚠️ 依裁定僅為相關性之代理指標，只用於排序與分層，**不得用作排除軸**。
CHO_SIGNAL = re.compile(
    r'carbohydrate|glucose|sucrose|fructose|maltodextrin|dextrin|'
    r'starch|honey|glycogen|sports drink|CHO\b', re.I)

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
        # n+51（二）：重篩範圍改為**全體已判之無摘要記錄**，不再挑區段。
        # 故此處不得再以頁次篩選——已判讀者只要無摘要就是重篩對象。
        rescreen = cid in judged
        if (it.get('abstract') or '').strip():
            continue
        pmcid, pmid, doi = ident_of(ident.get(cid, {}))
        out.append({'candidateId': cid, 'seq': it['seq'], 'page': it['page'],
                    'year': it.get('publicationYear'), 'rescreen': rescreen,
                    'pmcid': pmcid, 'pmid': pmid, 'doi': doi})
    # n+51（四）：改依標題碳水訊號優先（16 倍鑑別力）。
    # 理由——若中途中斷，已補的會是最可能藏著漏網 advance 的那批。
    # 只改順序不改範圍；重篩段仍排最前（它擋住重篩工作）。
    title = {it['candidateId']: (it.get('title') or '') for it in w['items']}
    for r in out:
        r['choSignal'] = bool(CHO_SIGNAL.search(title.get(r['candidateId'], '')))
    out.sort(key=lambda r: (not r['rescreen'], not r['choSignal'], r['seq']))
    return out


def queries_for(row):
    """回傳所有可用識別碼之查詢，依優先序。

    ⚠️ 原本一筆只試一種：pmcid 查不到就記 not-found。實測發現
    pmcid 失敗之 12 筆**全都另有 pmid 且查得到**——那是 fallback
    缺口，不是資料缺失。故改為逐一嘗試直到命中。"""
    out = []
    if row['pmcid']:
        out.append(('pmcid', 'PMCID:%s' % row['pmcid']))
    if row['pmid']:
        out.append(('pmid', 'EXT_ID:%s AND SRC:MED' % row['pmid']))
    if row['doi']:
        out.append(('doi', 'DOI:"%s"' % row['doi']))
    return out


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

    def atomic_dump(obj, path):
        """先寫暫存再 replace：避免其他行程讀到寫了一半的檔案。
        （實際發生過——本輪心跳讀取時撞上寫檔瞬間而 JSONDecodeError。）"""
        tmp = path + '.tmp'
        with open(tmp, 'w', encoding='utf-8') as fh:
            json.dump(obj, fh, ensure_ascii=False)
        os.replace(tmp, path)

    def write_prov(finished=None):
        """一律寫完整文件；中途存檔與收尾用同一格式，避免結構交替。"""
        atomic_dump({'documentType': 'abstract-enrichment-provenance',
                   'ruling': 'n+50',
                   'source': 'Europe PMC REST search (resultType=core)',
                   'startedAt': started,
                   'finishedAt': finished or 'in-progress',
                   'minIntervalSec': MIN_INTERVAL, 'httpCalls': t.calls,
                   'note': ('status=upstream-no-abstract means the record was '
                            'found and confirmed to have no abstract; '
                            'no-identifier/transport-error/http-* mean the '
                            'lookup was not completed'),
                   'records': prov}, pv_path)

    targets = build_targets()
    todo = [r for r in targets if r['candidateId'] not in prov]
    if limit:
        todo = todo[:limit]
    print('targets %d  already done %d  todo %d' % (
        len(targets), len(prov), len(todo)), flush=True)

    n = 0
    for row in todo:
        cid = row['candidateId']
        cands = queries_for(row)
        rec = {'attemptedAt': time.strftime('%Y-%m-%dT%H:%M:%S'),
               'source': 'europepmc-search',
               'triedKinds': [k for k, _ in cands]}
        if not cands:
            rec['idKind'] = None
            rec['status'] = 'no-identifier'   # 未嘗試
            rec['hasAbstract'] = None
            prov[cid] = rec
            continue
        resolved = False
        for kind, q in cands:
            url = SEARCH + '?' + urllib.parse.urlencode(
                {'query': q, 'resultType': 'core', 'format': 'json',
                 'pageSize': 1})
            try:
                ex = t.get_bytes(url=url, headers={
                    'Accept': 'application/json',
                    'User-Agent': 'AHIG/0.2.1 fulltext-calibration'})
            except Exception as exc:
                rec['status'] = 'transport-error'
                rec['detail'] = type(exc).__name__
                continue
            code = int(ex.get('status') or 0)
            if not 200 <= code < 300:
                rec['status'] = 'http-%d' % code
                continue
            try:
                body = json.loads(ex['body'].decode('utf-8'))
            except Exception:
                rec['status'] = 'bad-json'
                continue
            hits = (body.get('resultList') or {}).get('result') or []
            if not hits:
                continue                      # 換下一種識別碼
            ab = (hits[0].get('abstractText') or '').strip()
            rec['idKind'] = kind
            if ab:
                rec['status'] = 'enriched'
                rec['hasAbstract'] = True
                rec['abstractChars'] = len(ab)
                abstracts[cid] = ab
            else:
                # 查到紀錄，上游確認無摘要（≠ 未嘗試）
                rec['status'] = 'upstream-no-abstract'
                rec['hasAbstract'] = False
            resolved = True
            break
        if not resolved:
            rec.setdefault('idKind', cands[0][0])
            # 所有識別碼都試過仍查無，與「只試一種」明確可分
            rec['status'] = rec.get('status') if rec.get('status', '').startswith(
                ('transport-error', 'http-', 'bad-json')) else 'not-found-all-ids'
            rec['hasAbstract'] = None
        prov[cid] = rec
        n += 1
        if n % 50 == 0:
            atomic_dump(abstracts, ab_path)
            write_prov()
            done = sum(1 for v in prov.values() if v['status'] == 'enriched')
            print('%d/%d  enriched %d  calls %d' % (
                n, len(todo), done, t.calls), flush=True)

    atomic_dump(abstracts, ab_path)
    write_prov(time.strftime('%Y-%m-%dT%H:%M:%S'))

    from collections import Counter
    c = Counter(v['status'] for v in prov.values())
    print()
    print('provenance', dict(c.most_common()))
    print('abstracts stored', len(abstracts), 'httpCalls', t.calls)


if __name__ == '__main__':
    main()
