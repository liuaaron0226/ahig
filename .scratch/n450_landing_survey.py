# -*- coding: utf-8 -*-
"""33 個 landing page 之可取性實測——把「45 是上界」變成一個量到的數。

## 🚨 為什麼現在做，以及它不是什麼

本室自第 439 輪起三次載明：**「45 是上界不是保證，因為從未實際抓取過。」**
擁有者已裁示 45（兩條路都建），**⚠️ 而在任何人動手寫解析器之前，
🚨 該先知道那 33 頁裡有幾頁真的擺著可解析的全文。**
若實得遠低於 33，工單的範圍與切法都會不同。

**🚫 本檔不是取文**：不落盤任何文獻內容，不建 manifest，不動 `ahig/`。
**它只回答一個問題：這一頁看起來有沒有全文。**

## ⚠️ 判準寫在前面，且它是訊號不是證明

對每一頁記錄：HTTP 狀態、`Content-Type`、位元組數，以及三個結構訊號——

| 訊號 | 意義 |
|---|---|
| `pdfLink` | 頁內是否有指向 `.pdf` 之連結 |
| `fulltextMarker` | 是否含常見全文容器標記（`<article`、`fulltext`、`sec-` 等） |
| `textChars` | 去標籤後之字元數（**🚨 粗略代理，非正文長度**） |

**分類**：`textChars` ≥ 8000 且有 `fulltextMarker` → `fulltext-likely`；
有 `pdfLink` 但無上述 → `pdf-only`；2xx 但兩者皆無 → `abstract-only-likely`；
非 2xx → `blocked-or-error`。

**🚨 涵蓋範圍聲明（n+80 三之紀律）**
- ✅ 查得到：頁面是否取得到、其結構訊號、粗略字元量。
- 🚨 查不到：**該頁之全文是否可被正確切成節與偏移**——⚠️ 那要真的寫解析器才知道。
  **故 `fulltext-likely` 是「值得寫解析器去試」，🚫 不是「解析得出來」。**
- ⚠️ `textChars` 會把導覽列、參考文獻、cookie 條款一起算進去，**🚨 故門檻只用來排序，不用來斷言**。

## 節流與禮貌

沿用既有 `PacedTransport` 之 **1.2 秒**間隔，**🚫 不放寬**；
User-Agent 帶 `AHIG_CONTACT_EMAIL`（與 Unpaywall 同一個聯絡信箱）。
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
UA = ('Mozilla/5.0 (compatible; AHIG/0.2.1 landing-survey; +mailto:%s)' % EMAIL)

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
    if st == 'acquired':
        continue
    man = json.load(io.open(_artifact_dir(cid) / 'manifest.json',
                            encoding='utf-8'))
    url = man.get('availableUrl')
    if url:
        targets.append((cid, st, url))

TAG = re.compile(r'<[^>]+>')
MARKER = re.compile(r'<article\b|id="fulltext|class="fulltext|"sec-|'
                    r'<section\b[^>]*class="[^"]*(body|article)', re.I)
PDFLINK = re.compile(r'href="[^"]*\.pdf', re.I)


def probe(url, attempts=3):
    """🚨 第一版把例外吞成類別名（`ERR:URLError`），於是 28/33 看起來像「頁面取不到」。

    ⚠️ 事後單獨探測，那些主機多數正常回應——**失敗的是這次執行，不是主機**。
    🚨 本 run 第四次犯同型錯（grep -P、猜鍵名、HEAD 被拒），故本版：
      ① 記完整例外訊息，不只類別名；② 失敗重試並退避；③ 讀取上限縮小。
    """
    req = urllib.request.Request(url, headers={
        'User-Agent': UA,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8'})
    last = ''
    for k in range(attempts):
        if k:
            time.sleep(2.0 * k)          # 退避
        try:
            with urllib.request.urlopen(req, timeout=25) as r:
                raw = r.read(600_000)
                return {'status': r.status, 'finalHost': urlparse(r.geturl()).netloc,
                        'contentType': (r.headers.get('Content-Type') or '').split(';')[0],
                        'bytes': len(raw), 'body': raw, 'attempts': k + 1, 'error': ''}
        except urllib.error.HTTPError as e:
            return {'status': e.code, 'finalHost': urlparse(url).netloc,
                    'contentType': '', 'bytes': 0, 'body': b'',
                    'attempts': k + 1, 'error': 'HTTP %s' % e.code}
        except Exception as e:
            last = '%s: %s' % (type(e).__name__, str(e)[:120])
    return {'status': 'ERR', 'finalHost': urlparse(url).netloc,
            'contentType': '', 'bytes': 0, 'body': b'',
            'attempts': attempts, 'error': last}


def classify(p):
    if not (isinstance(p['status'], int) and 200 <= p['status'] < 300):
        return 'blocked-or-error', False, False, 0
    html = p['body'].decode('utf-8', errors='ignore')
    marker = bool(MARKER.search(html))
    pdf = bool(PDFLINK.search(html))
    chars = len(TAG.sub(' ', html).split())
    if marker and chars >= 8000:
        return 'fulltext-likely', marker, pdf, chars
    if pdf:
        return 'pdf-only', marker, pdf, chars
    return 'abstract-only-likely', marker, pdf, chars


print('=== landing page 可取性實測（%d 筆；節流 %.1f 秒／請求）==='
      % (len(targets), MIN_INTERVAL))
print('⚠️ 聯絡信箱 %s' % ('已設定' if EMAIL else '🚨 未設定'))
print()
print('%-10s %-24s %-34s %6s %7s %s'
      % ('id', '狀態', '最終主機', 'HTTP', '字數', '分類'))
print('-' * 104)
rows = []
for i, (cid, st, url) in enumerate(targets):
    if i:
        time.sleep(MIN_INTERVAL)
    p = probe(url)
    kind, marker, pdf, chars = classify(p)
    rows.append({'candidateId': cid, 'status': st,
                 'host': urlparse(url).netloc, 'finalHost': p['finalHost'],
                 'http': p['status'], 'contentType': p['contentType'],
                 'bytes': p['bytes'], 'attempts': p.get('attempts'),
                 'error': p.get('error',''), 'fulltextMarker': marker,
                 'pdfLink': pdf, 'textWords': chars, 'survey': kind})
    print('%-10s %-24s %-34s %6s %7s %s'
          % (cid.split(':')[-1][:8], st, p['finalHost'][:34], p['status'],
             chars, kind))

c = Counter(r['survey'] for r in rows)
print('-' * 104)
print('=== 分類彙總 ===')
for k, v in c.most_common():
    print('   %-24s %2d' % (k, v))
reachable = c['fulltext-likely'] + c['pdf-only']
print()
print('⚠️ 值得寫解析器去試者（fulltext-likely）：%d／%d' % (c['fulltext-likely'], len(rows)))
print('⚠️ 僅有 PDF 連結者：%d｜🚨 取不到頁面者：%d'
      % (c['pdf-only'], c['blocked-or-error']))
print('🚨 上界 45 之實測對照：12（已在手）＋ %d（本次判為有全文跡象）= %d'
      % (c['fulltext-likely'], 12 + c['fulltext-likely']))
print('⚠️ 🚨 這仍是跡象不是保證——分類為 fulltext-likely 只代表「值得寫解析器去試」。')

doc = {
    'schemaVersion': 1,
    'documentType': 'landing-page-reachability-survey',
    'ruling': "owner ruling 45 (round 449); survey precedes any parser work",
    'population': 'the 33 non-acquired records among the 45 obtainable',
    'countingUnit': 'publication',
    'criterion': 'HTTP fetch of manifest.availableUrl; classified by presence of '
                 'a full-text container marker, a .pdf link, and a de-tagged '
                 'word count with an 8000-word threshold',
    'thresholdNote': 'The word count includes navigation, references and cookie '
                     'banners, so the threshold orders candidates rather than '
                     'deciding them.',
    'counts': dict(c),
    'records': rows,
    'coverageStatement': ('Says whether a page looks like it holds full text, '
                          'not whether a parser can cut it into sections with '
                          'offsets. fulltext-likely means worth writing a '
                          'parser against, not parseable.'),
    'contentNote': 'Hosts, HTTP codes, byte and word counts only. No literature '
                   'content is stored.',
    'throttle': {'minIntervalSeconds': MIN_INTERVAL,
                 'note': 'same pacing as the existing PacedTransport; not relaxed'},
}
doc['surveyHash'] = content_hash(doc['counts'])
io.open(S + 'n450_landing_survey.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn450_landing_survey.json' % S)
