# -*- coding: utf-8 -*-
"""GROBID 之驗收：真實 PDF → TEI → `parse_tei`，逐檔看契約過不過。

## 🚨 驗收點在哪裡

**⚠️ 「GROBID 建置成功」不是驗收點。**
repo 內之 fixture 通過只證明 `parse_tei` 之實作正確，
**🚨 不證明 GROBID 對本案這 11 個真實 PDF 的輸出符合該契約。**

**本檔即那個驗收**：把每一個已下載之 PDF 送進 GROBID，
取回 TEI 後**原封餵給 `parse_tei`**，看它過不過、切出幾節、偏移合不合。

## 🚫 本檔不做什麼

- **不落盤任何文獻內容**——⚠️ 產物只有節數、字元數、雜湊與判定。
- **不修改 `ahig/`**——🚨 接線之實作待協調者裁示 PDF／TEI 雜湊記法（第 458 輪）。
- **不寫 manifest**——⚠️ 那是接線的事，本檔只驗契約。

## 判定

| 判定 | 條件 |
|---|---|
| `pass` | `parse_tei` 未拋錯，且 `sections` 非空、偏移單調遞增 |
| `parse-error` | `parse_tei` 拋 `FulltextError`（**⚠️ 記完整訊息**） |
| `empty` | 未拋錯但 `sections` 為空 —— 🚨 契約上不算取得全文 |
| `grobid-error` | GROBID 端非 2xx 或連線失敗 |

**🚨 偏移單調性須自己驗**：`parse_tei` 之測試以 fixture 驗過，
**⚠️ 但真實文件之節可能重疊或倒序，那會讓字元偏移失去意義。**

## 用法

先啟動 GROBID 服務（預設 `http://localhost:8070`），再執行本檔。
可以 `GROBID_URL` 覆寫位址。
"""
import io
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from collections import Counter

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash, file_hash  # noqa: E402
from ahig.search import fulltext  # noqa: E402

S = '.scratch/'
GROBID = os.environ.get('GROBID_URL', 'http://localhost:8070')
CACHE = os.path.join(os.environ.get('AHIG_PRIVATE_ROOT',
                                    r'C:/Users/User/Desktop/claude/ahig-private'),
                     'fulltext', 'pdf-cache')
TEI_OUT = os.path.join(os.path.dirname(CACHE), 'tei-cache')
os.makedirs(TEI_OUT, exist_ok=True)


def alive():
    try:
        with urllib.request.urlopen(GROBID + '/api/isalive', timeout=10) as r:
            return r.status == 200
    except Exception:
        return False


def to_tei(path):
    """multipart/form-data 上傳單一 PDF，取回 TEI。"""
    boundary = uuid.uuid4().hex
    body = b''.join([
        ('--%s\r\n' % boundary).encode(),
        b'Content-Disposition: form-data; name="input"; filename="d.pdf"\r\n',
        b'Content-Type: application/pdf\r\n\r\n',
        open(path, 'rb').read(),
        ('\r\n--%s\r\n' % boundary).encode(),
        b'Content-Disposition: form-data; name="consolidateHeader"\r\n\r\n0\r\n',
        ('--%s--\r\n' % boundary).encode()])
    req = urllib.request.Request(
        GROBID + '/api/processFulltextDocument', data=body,
        headers={'Content-Type': 'multipart/form-data; boundary=%s' % boundary,
                 'Accept': 'application/xml'})
    try:
        with urllib.request.urlopen(req, timeout=600) as r:
            return r.status, r.read(), ''
    except urllib.error.HTTPError as e:
        return e.code, b'', 'HTTP %s' % e.code
    except Exception as e:
        return 'ERR', b'', '%s: %s' % (type(e).__name__, str(e)[:140])


if not alive():
    sys.exit('🚨 GROBID 未在 %s 回應 /api/isalive——🚫 先啟動服務再跑本檔。' % GROBID)

files = sorted(f for f in os.listdir(CACHE) if f.endswith('.pdf'))
print('=== GROBID 驗收：%d 個真實 PDF（服務 %s）===' % (len(files), GROBID))
print('%-20s %8s %7s %9s %s' % ('檔案（id 片段）', 'TEI KB', '節數', '字元數', '判定'))
print('-' * 78)
rows = []
for fn in files:
    p = os.path.join(CACHE, fn)
    t0 = time.time()
    code, tei, err = to_tei(p)
    if not tei:
        rows.append({'file': fn[:-4], 'verdict': 'grobid-error', 'http': code,
                     'error': err, 'sections': 0, 'chars': 0})
        print('%-20s %8s %7s %9s %s' % (fn[:-4][:20], '—', '—', '—',
                                        '🚨 grobid-error %s' % (err or code)))
        continue
    # ⚠️ TEI 留在私有根供覆核，🚨 永不進版控。
    with open(os.path.join(TEI_OUT, fn[:-4] + '.tei.xml'), 'wb') as fh:
        fh.write(tei)
    try:
        parsed = fulltext.parse_tei(tei)
        secs = parsed['sections']
        mono = all(secs[i]['startOffset'] <= secs[i]['endOffset']
                   and (i == 0 or secs[i - 1]['endOffset'] <= secs[i]['startOffset'])
                   for i in range(len(secs)))
        v = 'pass' if secs and mono else ('empty' if not secs else 'offsets-not-monotonic')
        rows.append({'file': fn[:-4], 'verdict': v, 'http': code,
                     'teiBytes': len(tei), 'sections': len(secs),
                     'chars': len(parsed['content']), 'monotonic': mono,
                     'teiHash': file_hash(tei), 'seconds': round(time.time() - t0, 1),
                     'error': ''})
        print('%-20s %8d %7d %9d %s'
              % (fn[:-4][:20], len(tei) // 1024, len(secs), len(parsed['content']),
                 '✅ pass' if v == 'pass' else '🚨 ' + v))
    except Exception as e:
        rows.append({'file': fn[:-4], 'verdict': 'parse-error', 'http': code,
                     'teiBytes': len(tei), 'sections': 0, 'chars': 0,
                     'error': '%s: %s' % (type(e).__name__, str(e)[:160])})
        print('%-20s %8d %7s %9s %s'
              % (fn[:-4][:20], len(tei) // 1024, '—', '—',
                 '🚨 parse-error: %s' % str(e)[:44]))

c = Counter(r['verdict'] for r in rows)
print('-' * 78)
for k, v in c.most_common():
    print('   %-24s %2d' % (k, v))
print()
print('✅ 通過契約者：%d／%d' % (c['pass'], len(rows)))
print('🚨 通過只代表「切得出節且偏移單調」，🚫 不代表節名正確或內容完整——後者須人讀。')

doc = {
    'schemaVersion': 1,
    'documentType': 'grobid-contract-acceptance',
    'ruling': 'owner chose GROBID (round 457); this is the acceptance point',
    'population': 'the PDFs downloaded in round 455',
    'countingUnit': 'file',
    'criterion': 'parse_tei accepts the TEI, sections is non-empty, and offsets '
                 'are monotonic and non-overlapping',
    'grobidUrl': GROBID,
    'counts': dict(c),
    'files': rows,
    'coverageStatement': ('Passing means the document sections and offsets under '
                          'the contract. It does not mean the section names are '
                          'right or the text is complete; that needs a reader.'),
    'contentNote': 'Counts, sizes, hashes and verdicts only. TEI is written to '
                   'the private root, never to version control.',
}
doc['acceptanceHash'] = content_hash(doc['counts'])
io.open(S + 'n459_grobid_acceptance.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn459_grobid_acceptance.json' % S)
sys.exit(0 if c['pass'] == len(rows) else 1)
