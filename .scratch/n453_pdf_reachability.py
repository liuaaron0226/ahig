# -*- coding: utf-8 -*-
"""PDF 取得層之可行性實測——先量再建，且不下載整份、不落盤任何內容。

## 🚨 為什麼是探測不是下載

n+117／n+119 授權「PDF 路之取得層（抓 PDF 位元組）」不需安裝即可起跑。
**⚠️ 但在寫取得層之前，該先知道這個環境到底抓得到幾個 PDF**
——第 450 輪已量到 **11 個主機在本環境回 403**，
**🚨 若多數 PDF 根本取不到，取得層的形狀會完全不同**（例如需改走 API 或換出口）。

## 做法與其節制

對每一筆帶 PDF 網址者發 **range request（前 2,048 位元組）**：
- ✅ 足以驗 `%PDF-` 魔術位元組與 `Content-Type`
- 🚨 **不下載整份**：對來源站台之負擔最小，且本室無意在裁示前囤積檔案
- 🚫 **不落盤任何位元組**，產物只記 host、HTTP 狀態、是否為真 PDF

**⚠️ 產物一律只存 host 與 candidateId，🚫 不存完整網址**
——第 452 輪已查出 landing URL 之路徑內嵌逐字標題，而 n+48 五道抓不到該型。

## 判準

| 分類 | 條件 |
|---|---|
| `pdf-ok` | 2xx 且前綴為 `%PDF-` |
| `not-pdf` | 2xx 但前綴不是 `%PDF-`（多半是被導去 HTML 攔截頁或同意頁） |
| `blocked` | 4xx／5xx |
| `error` | 連線層失敗（**🚨 記完整訊息，不只類別名**） |

**🚨 涵蓋範圍聲明（n+80 三之紀律）**
- ✅ 查得到：此環境此刻能否取到該 PDF 之開頭位元組。
- 🚨 查不到：**該 PDF 是否為完整全文、是否可被解析**——⚠️ 前者要下載整份，後者要解析器。
- ⚠️ `blocked` 說的是**本環境**，🚫 不是「該文獻取不到」。
"""
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from collections import Counter
from urllib.parse import urlparse

sys.path.insert(0, 'ahig')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
from ahig.search.fulltext import _artifact_dir  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
MIN_INTERVAL = 1.5
EMAIL = os.environ.get('AHIG_CONTACT_EMAIL', '')
UA = 'Mozilla/5.0 (compatible; AHIG/0.2.1 pdf-probe; +mailto:%s)' % EMAIL

inv = json.load(io.open(S + 'm1_step3_inventory.json', encoding='utf-8'))
bf = json.load(io.open(S + 'm1_step3_backfill.json', encoding='utf-8'))
final = {r['candidateId']: r['status'] for r in inv['records']
         if r['status'] in set(bf['obtainableDefinition'])}
for pool in bf['pools']:
    for r in pool.get('backfilled') or []:
        if r.get('accepted'):
            final[r['candidateId']] = r['status']

targets = []
for cid, st in sorted(final.items()):
    if st != 'available-pdf':
        continue
    man = json.load(io.open(_artifact_dir(cid) / 'manifest.json',
                            encoding='utf-8'))
    url = man.get('availableUrl')
    if url:
        targets.append((cid, url))


def probe(url, attempts=2):
    """🚨 記完整例外訊息——第 450 輪把它吞成類別名，得出 28/33 的假結果。"""
    req = urllib.request.Request(url, headers={
        'User-Agent': UA, 'Range': 'bytes=0-2047', 'Accept': 'application/pdf,*/*'})
    last = ''
    for k in range(attempts):
        if k:
            time.sleep(2.0)
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                head = r.read(2048)
                return {'http': r.status,
                        'ct': (r.headers.get('Content-Type') or '').split(';')[0],
                        'isPdf': head[:5] == b'%PDF-', 'err': ''}
        except urllib.error.HTTPError as e:
            return {'http': e.code, 'ct': '', 'isPdf': False,
                    'err': 'HTTP %s' % e.code}
        except Exception as e:
            last = '%s: %s' % (type(e).__name__, str(e)[:110])
    return {'http': 'ERR', 'ct': '', 'isPdf': False, 'err': last}


print('=== PDF 取得層可行性（%d 筆；range 前 2KB；節流 %.1f 秒）==='
      % (len(targets), MIN_INTERVAL))
print('⚠️ 聯絡信箱 %s｜🚫 不下載整份、不落盤位元組'
      % ('已設定' if EMAIL else '🚨 未設定'))
print()
print('%-10s %-32s %6s %-26s %s' % ('id', 'host', 'HTTP', 'Content-Type', '判定'))
print('-' * 96)
rows = []
for i, (cid, url) in enumerate(targets):
    if i:
        time.sleep(MIN_INTERVAL)
    host = urlparse(url).netloc
    p = probe(url)
    kind = ('pdf-ok' if p['isPdf'] else
            'not-pdf' if isinstance(p['http'], int) and 200 <= p['http'] < 300 else
            'blocked' if isinstance(p['http'], int) else 'error')
    rows.append({'candidateId': cid, 'host': host, 'http': p['http'],
                 'contentType': p['ct'], 'isPdf': p['isPdf'],
                 'error': p['err'], 'verdict': kind})
    print('%-10s %-32s %6s %-26s %s'
          % (cid.split(':')[-1][:8], host[:32], p['http'], p['ct'][:26], kind))

c = Counter(r['verdict'] for r in rows)
print('-' * 96)
for k, v in c.most_common():
    print('   %-12s %2d' % (k, v))
print()
print('✅ 本環境確實取得到 PDF 開頭者：%d／%d' % (c['pdf-ok'], len(rows)))
print('⚠️ 加上 figshare API 之 2 筆，PDF 路在本環境之可取上界為 %d 筆。'
      % (c['pdf-ok'] + 2))
print('🚨 那仍是「取得到位元組」，🚫 不是「解析得出全文」——後者仍待授權之解析器。')

doc = {
    'schemaVersion': 1,
    'documentType': 'pdf-reachability-probe',
    'ruling': 'n+117(1)/n+119(1): the PDF fetch layer needs no installation',
    'population': 'records classed available-pdf among the 45 obtainable',
    'countingUnit': 'publication',
    'criterion': 'range request for the first 2048 bytes; pdf-ok requires a 2xx '
                 'and a %PDF- prefix',
    'counts': dict(c),
    'records': rows,
    'figshareApiAdds': 2,
    'reachableUpperBound': c['pdf-ok'] + 2,
    'coverageStatement': ('Says whether the first bytes arrive here and now. It '
                          'does not say the PDF is complete full text, nor that '
                          'a parser can read it. A blocked verdict describes '
                          'this environment, not the literature.'),
    'contentNote': 'Hosts, HTTP codes and a magic-byte boolean only. No URLs '
                   '(landing paths embed verbatim titles, round 452) and no '
                   'document bytes are stored.',
    'throttle': {'minIntervalSeconds': MIN_INTERVAL,
                 'rangeBytes': 2048,
                 'note': 'deliberately a probe, not a download'},
}
doc['probeHash'] = content_hash(doc['counts'])
io.open(S + 'n453_pdf_reachability.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn453_pdf_reachability.json' % S)
