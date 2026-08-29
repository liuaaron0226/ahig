# -*- coding: utf-8 -*-
"""n+124 派工：11 筆遭擋者是否另有沒被試過的 OA 位址。

## 🚨 派工之由來

n+124 讀原始碼查明：`fulltext.py` 兩條探路（OpenAlex 第 843 行、Unpaywall 第 882 行）
**都只取 `best_oa_location`——單一位址。**
**⚠️ 而 OpenAlex 對同一篇通常列有多個 OA 位址**（機構典藏庫、PMC、出版社各一）。

> **🚨 即這 11 筆很可能另有一個從未被試過的 OA 位址，而它不擋機器人。**

**⚠️ 且此推測與已知事實相符**：可達之 16 筆中最大一類正是機構典藏庫，
**而典藏庫一般不做自動化阻擋。**

## 本檔做什麼

1. 取該 11 筆之 DOI（自各該 manifest 之 attempts 內的 OpenAlex 查詢網址回推）。
2. 查 OpenAlex **`locations` 全陣列**，列出每個 OA 位址之主機與型別。
3. **排除已試過者**（即 `best_oa_location`），對其餘逐一實測可達性。

**🚫 不做**：不下載整份、不落盤文獻內容、不記完整網址
（⚠️ 落地頁路徑內嵌逐字標題，n+48 五道抓不到該型）。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：OpenAlex 所列之其他 OA 位址、其主機、以及此環境能否取得。
- 🚨 查不到：**該位址之內容是否為完整全文**——⚠️ 取得到位元組不等於可萃取。
- ⚠️ OpenAlex 之 `locations` 亦非窮盡，**🚫 查無替代位址不等於不存在。**
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
GAP = 1.5
EMAIL = os.environ.get('AHIG_CONTACT_EMAIL', '')
if not EMAIL:
    sys.exit('🚨 AHIG_CONTACT_EMAIL 未設定——OpenAlex 之禮貌池需要它，中止。')
UA = 'AHIG/0.2.1 alt-oa-survey (mailto:%s)' % EMAIL


def get(url, rng=None, cap=400_000):
    h = {'User-Agent': UA, 'Accept': '*/*'}
    if rng:
        h['Range'] = 'bytes=0-%d' % (rng - 1)
    try:
        with urllib.request.urlopen(urllib.request.Request(url, headers=h),
                                    timeout=30) as r:
            return {'http': r.status, 'body': r.read(cap), 'err': ''}
    except urllib.error.HTTPError as e:
        return {'http': e.code, 'body': b'', 'err': 'HTTP %s' % e.code}
    except Exception as e:
        return {'http': 'ERR', 'body': b'',
                'err': '%s: %s' % (type(e).__name__, str(e)[:110])}


# ── 取遭擋之 11 筆及其 DOI ────────────────────────────────────────
surv = json.load(io.open(S + 'n450_landing_survey.json', encoding='utf-8'))
blocked = [r for r in surv['records']
           if not (isinstance(r['http'], int) and 200 <= r['http'] < 300)]
rows = []
print('=== n+124：%d 筆遭擋者之替代 OA 位址 ===' % len(blocked))
print('⚠️ 只列主機與型別，🚫 不記完整網址（路徑內嵌逐字標題）')
print()
print('%-10s %-26s %6s %s' % ('id', '已試過之主機', '其他位址', '可達之替代'))
print('-' * 82)
for i, r in enumerate(blocked):
    cid = r['candidateId']
    man = json.load(io.open(_artifact_dir(cid) / 'manifest.json',
                            encoding='utf-8'))
    oa = [a for a in man['attempts'] if a.get('sourceId') == 'openalex']
    doi = None
    if oa and oa[0].get('url'):
        m = re.search(r'doi%3A([^&]+)', oa[0]['url'])
        if m:
            doi = urllib.parse.unquote(m.group(1))
    if not doi:
        rows.append({'candidateId': cid, 'triedHost': r['finalHost'],
                     'doi': None, 'otherLocations': 0, 'reachable': [],
                     'note': 'no DOI recoverable from the recorded attempt'})
        print('%-10s %-26s %6s %s' % (cid.split(':')[-1][:8],
                                      r['finalHost'][:26], '—', '🚨 無 DOI 可回推'))
        continue
    if i:
        time.sleep(GAP)
    res = get('https://api.openalex.org/works/doi:%s?mailto=%s' % (doi, EMAIL))
    if res['http'] != 200:
        rows.append({'candidateId': cid, 'triedHost': r['finalHost'], 'doi': doi,
                     'otherLocations': 0, 'reachable': [],
                     'note': 'OpenAlex %s' % res['http']})
        print('%-10s %-26s %6s %s' % (cid.split(':')[-1][:8],
                                      r['finalHost'][:26], '—',
                                      '🚨 OpenAlex %s' % res['http']))
        continue
    w = json.loads(res['body'].decode('utf-8'))
    best = (w.get('best_oa_location') or {}).get('pdf_url') or \
           (w.get('best_oa_location') or {}).get('landing_page_url')
    cands = []
    for loc in (w.get('locations') or []):
        if not loc.get('is_oa'):
            continue
        u = loc.get('pdf_url') or loc.get('landing_page_url')
        if not u or u == best:
            continue
        src = (loc.get('source') or {})
        cands.append({'url': u, 'host': urlparse(u).netloc,
                      'type': loc.get('version') or src.get('type') or '?',
                      'isPdf': bool(loc.get('pdf_url'))})
    ok = []
    for c in cands[:6]:
        time.sleep(GAP)
        p = get(c['url'], rng=2048)
        good = p['body'][:5] == b'%PDF-'
        if good or (isinstance(p['http'], int) and 200 <= p['http'] < 300):
            ok.append({'host': c['host'], 'isPdf': good, 'http': p['http']})
    rows.append({'candidateId': cid, 'triedHost': r['finalHost'], 'doi': doi,
                 'otherLocations': len(cands),
                 'otherHosts': sorted({c['host'] for c in cands}),
                 'reachable': ok})
    tag = ('✅ %d 個（PDF %d）' % (len(ok), sum(1 for x in ok if x['isPdf']))
           if ok else ('🚨 %d 個皆不可達' % len(cands) if cands else '—— 無其他位址'))
    print('%-10s %-26s %6d %s' % (cid.split(':')[-1][:8], r['finalHost'][:26],
                                  len(cands), tag))

print('-' * 82)
gained = sum(1 for r in rows if any(x['isPdf'] for x in r['reachable']))
any_ok = sum(1 for r in rows if r['reachable'])
print('   ✅ 另有可達 OA 位址者：%d／%d' % (any_ok, len(rows)))
print('   ✅ 其中取得到 PDF 者：%d' % gained)
print('   ⚠️ 取得到位元組不等於可萃取——🚫 仍須經 GROBID 與 parse_tei 驗收。')

doc = {
    'schemaVersion': 1,
    'documentType': 'alternative-oa-locations',
    'ruling': 'n+124(3): query the full locations array, not best_oa_location',
    'population': 'the 11 records blocked in this environment (round 450)',
    'countingUnit': 'publication',
    'criterion': 'OA locations in OpenAlex locations[] other than the one already '
                 'attempted; reachable means 2xx, pdf means a %PDF- prefix',
    'records': rows,
    'anyAlternativeReachable': any_ok,
    'pdfObtainable': gained,
    'coverageStatement': ('OpenAlex locations are not exhaustive, so finding no '
                          'alternative does not prove none exists. And reaching '
                          'bytes is not extraction -- these still have to pass '
                          'GROBID and parse_tei.'),
    'contentNote': 'Hosts, counts and HTTP codes only. No URLs are stored, since '
                   'landing paths embed verbatim titles.',
}
doc['surveyHash'] = content_hash({'any': any_ok, 'pdf': gained})
io.open(S + 'n477_alt_oa_locations.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn477_alt_oa_locations.json' % S)
