# -*- coding: utf-8 -*-
"""擁有者指示：帶聯絡信箱重跑失敗之 7 筆，並追 5 筆落地頁之 PDF 連結。

## 兩件事

**（甲）重試**：第 453 輪有 4 筆回 `text/html`、3 筆 403，
**⚠️ 而該次執行時 `AHIG_CONTACT_EMAIL` 未進入環境變數**（腳本自己印了「未設定」）。
本輪帶信箱重試，看那 7 筆有幾筆是可救的。

**（乙）追連結**：第 450 輪判為 `pdf-only` 之 5 筆落地頁，其 PDF 連結未追。
**🚨 且該輪之樣式只認 `href="....pdf"`，而典藏庫多用 `/download/`、`?sequence=`、
`bitstream` 等形式**——⚠️ 故本輪改用較寬之候選樣式，再逐一驗魔術位元組。

## 🚫 不做什麼

- **不下載整份**（range 前 2KB），**不落盤任何位元組**。
- **不記完整網址**——⚠️ 落地頁路徑內嵌逐字標題（第 452 輪），
  **🚨 產物只記 host、HTTP、是否為真 PDF。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：帶信箱後能否取到、落地頁上是否有可取之 PDF 連結。
- 🚨 查不到：**該 PDF 是否為完整全文、是否可解析**——⚠️ 仍待下載與解析器。
- ⚠️ 候選樣式雖已放寬，**🚨 仍可能漏掉以 JavaScript 組出之連結**，故結果仍是下界。
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
from urllib.parse import urljoin, urlparse

sys.path.insert(0, 'ahig')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
from ahig.search.fulltext import _artifact_dir  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
GAP = 1.5
EMAIL = os.environ.get('AHIG_CONTACT_EMAIL', '')
UA = 'Mozilla/5.0 (compatible; AHIG/0.2.1 fulltext-acquisition; +mailto:%s)' % EMAIL
if not EMAIL:
    sys.exit('🚨 AHIG_CONTACT_EMAIL 未設定——🚫 本輪之目的正是帶信箱重試，中止。')


def get(url, rng=True, cap=2048):
    """🚨 記完整例外訊息；range 取前 2KB。"""
    h = {'User-Agent': UA, 'Accept': '*/*'}
    if rng:
        h['Range'] = 'bytes=0-%d' % (cap - 1)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h),
                                    timeout=30) as r:
            return {'http': r.status, 'url': r.geturl(),
                    'ct': (r.headers.get('Content-Type') or '').split(';')[0],
                    'body': r.read(cap), 'err': ''}
    except urllib.error.HTTPError as e:
        return {'http': e.code, 'url': url, 'ct': '', 'body': b'',
                'err': 'HTTP %s' % e.code}
    except Exception as e:
        return {'http': 'ERR', 'url': url, 'ct': '', 'body': b'',
                'err': '%s: %s' % (type(e).__name__, str(e)[:110])}


def verdict(r):
    if r['body'][:5] == b'%PDF-':
        return 'pdf-ok'
    if isinstance(r['http'], int) and 200 <= r['http'] < 300:
        return 'not-pdf'
    return 'blocked' if isinstance(r['http'], int) else 'error'


inv = json.load(io.open(S + 'm1_step3_inventory.json', encoding='utf-8'))
bf = json.load(io.open(S + 'm1_step3_backfill.json', encoding='utf-8'))
final = {r['candidateId']: r['status'] for r in inv['records']
         if r['status'] in set(bf['obtainableDefinition'])}
for pool in bf['pools']:
    for r in pool.get('backfilled') or []:
        if r.get('accepted'):
            final[r['candidateId']] = r['status']


def landing(cid):
    m = json.load(io.open(_artifact_dir(cid) / 'manifest.json', encoding='utf-8'))
    return m.get('availableUrl')


# ── 甲：帶信箱重試第 453 輪之 7 筆 ────────────────────────────────
prev = json.load(io.open(S + 'n453_pdf_reachability.json', encoding='utf-8'))
retry = [r for r in prev['records'] if r['verdict'] != 'pdf-ok']
print('=== 甲、帶聯絡信箱重試（%d 筆；信箱已設定）===' % len(retry))
print('%-10s %-30s %-14s %-14s %s'
      % ('id', 'host', '第 453 輪', '本輪', '變化'))
print('-' * 88)
a_rows = []
for i, r in enumerate(retry):
    if i:
        time.sleep(GAP)
    res = get(landing(r['candidateId']))
    v = verdict(res)
    changed = '✅ 已救回' if v == 'pdf-ok' else ('—' if v == r['verdict'] else '⚠️ %s' % v)
    a_rows.append({'candidateId': r['candidateId'], 'host': r['host'],
                   'before': r['verdict'], 'after': v, 'http': res['http'],
                   'contentType': res['ct'], 'error': res['err']})
    print('%-10s %-30s %-14s %-14s %s'
          % (r['candidateId'].split(':')[-1][:8], r['host'][:30],
             r['verdict'], v, changed))
rescued = sum(1 for x in a_rows if x['after'] == 'pdf-ok')
print('-' * 88)
print('   ✅ 帶信箱後救回：%d／%d' % (rescued, len(retry)))

# ── 乙：追 5 筆落地頁之 PDF 連結 ──────────────────────────────────
surv = json.load(io.open(S + 'n450_landing_survey.json', encoding='utf-8'))
pdf_only = [r for r in surv['records'] if r['survey'] == 'pdf-only']
# 🚨 樣式放寬：典藏庫之下載連結多不以 .pdf 結尾。
CAND = re.compile(
    r'href="([^"]*(?:\.pdf|/download|/bitstream|sequence=|'
    r'type=printable|content_type=pdf|/pdf/)[^"]*)"', re.I)
print()
print('=== 乙、追 %d 筆落地頁之 PDF 連結（樣式已放寬）===' % len(pdf_only))
print('%-10s %-30s %8s %s' % ('id', 'host', '候選連結', '結果'))
print('-' * 80)
b_rows = []
for i, r in enumerate(pdf_only):
    if i:
        time.sleep(GAP)
    base = landing(r['candidateId'])
    page = get(base, rng=False, cap=600_000)
    html = page['body'].decode('utf-8', errors='ignore')
    cands = []
    for h in CAND.findall(html):
        u = urljoin(page['url'], h)
        if u not in cands:
            cands.append(u)
    got, tried = None, 0
    for u in cands[:6]:
        tried += 1
        time.sleep(GAP)
        res = get(u)
        if verdict(res) == 'pdf-ok':
            got = urlparse(u).netloc
            break
    b_rows.append({'candidateId': r['candidateId'], 'host': r['host'],
                   'candidates': len(cands), 'tried': tried,
                   'pdfHost': got, 'pdfObtained': bool(got)})
    print('%-10s %-30s %8d %s'
          % (r['candidateId'].split(':')[-1][:8], r['host'][:30], len(cands),
             ('✅ 取到 PDF（%s）' % got) if got else
             ('🚨 %d 個候選皆非 PDF' % tried if cands else '🚨 頁內無候選連結')))
b_ok = sum(1 for x in b_rows if x['pdfObtained'])
print('-' * 80)
print('   ✅ 追到 PDF：%d／%d' % (b_ok, len(pdf_only)))

# ── 合計 ────────────────────────────────────────────────────────
base_pdf = prev['counts'].get('pdf-ok', 0)
total = 12 + base_pdf + 2 + rescued + b_ok
print()
print('=== 更新後之本環境實得 ===')
print('   已在手 JATS                12')
print('   available-pdf 直接可取     %d' % base_pdf)
print('   figshare API               2')
print('   帶信箱救回                 %d' % rescued)
print('   落地頁追到                 %d' % b_ok)
print('   ------------------------------')
print('   合計                       %d  （擁有者所選 45）' % total)
print('   🚨 仍是「位元組取得到」，🚫 不是「解析得出全文」。')

doc = {
    'schemaVersion': 1,
    'documentType': 'pdf-retry-and-landing-followup',
    'ruling': 'owner instruction (round 454): retry with the contact email and '
              'follow the five landing-page PDF links',
    'population': 'the 7 non-pdf-ok records of round 453, plus the 5 pdf-only '
                  'landing pages of round 450',
    'countingUnit': 'publication',
    'criterion': 'range request for the first 2048 bytes; pdf-ok requires a %PDF- '
                 'prefix. Landing pages are fetched in full, candidate links '
                 'extracted by a widened pattern, then each candidate probed.',
    'contactEmailSet': True,
    'retry': {'records': a_rows, 'rescued': rescued, 'attempted': len(retry)},
    'landingFollowup': {'records': b_rows, 'obtained': b_ok,
                        'attempted': len(pdf_only)},
    'tally': {'jatsInHand': 12, 'directPdf': base_pdf, 'figshare': 2,
              'rescuedByEmail': rescued, 'fromLandingLinks': b_ok,
              'total': total, 'ownerTarget': 45},
    'coverageStatement': ('Bytes arriving, not full text extracted. The widened '
                          'link pattern still cannot see links assembled by '
                          'JavaScript, so the landing figure remains a floor.'),
    'contentNote': 'Hosts, HTTP codes, counts and a magic-byte boolean only. No '
                   'URLs and no document bytes are stored.',
}
doc['tallyHash'] = content_hash(doc['tally'])
io.open(S + 'n454_pdf_retry_and_landing.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn454_pdf_retry_and_landing.json' % S)
