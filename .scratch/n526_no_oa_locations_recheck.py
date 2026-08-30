# -*- coding: utf-8 -*-
"""`no-oa-fulltext` 那 38 筆：**n+124 的那個發現，從沒套用在它們身上。**

## 🚨 起點：本層最強的那句話，其支撐母體可能小於它的範圍

本室反覆寫「**取得層在開放取用範圍內已窮盡**」。
**⚠️ 而那句話的支撐是什麼？**

| 產物 | 探測了誰 |
|---|---|
| `n450` | 尚未到手且**有位址**者之落地頁（33 筆） |
| `n477` | **遭擋之 11 筆**——依 n+124 查 `locations[]` 全陣列 |
| `n494` | **從未探測過之 12 筆** |

**🚨 而母體之中未取得者共 57 筆，其中 38 筆狀態為 `no-oa-fulltext`，
⚠️ 從未出現在上述任何一份探測清單裡。**

## 🚨 而 n+124 的發現，正好適用於它們

`fulltext.py` 第 909 行：

```python
location = (work or {}).get("best_oa_location") or {}
...
if not available_url:
    return ... conclusion="miss"
```

> **🚨 `best_oa_location` 為空即判 `miss`——`locations[]` 從頭到尾沒有被讀過。**
> **⚠️ 而 OpenAlex 對同一篇常列有多個位址**：`best_oa_location` 為 null，
> **而 `locations[]` 內仍可能有開放位址。**

**⚠️ n+124 當初就是據此查出遭擋之 11 筆中 8 筆另有位址、4 筆因此取得。**
**🚨 同一個問題套在這 38 筆上，從來沒有人問過。**

## 🚨 本檔問什麼、不問什麼

- ✅ 問：這 38 筆之 `locations[]` 裡有沒有 `is_oa` 之項目。
- **🚫 不下載**：只問索引上列不列，**⚠️ 取得到位元組是另一件事。**
- **🚫 不改任何 manifest**、🚫 不改狀態——⚠️ 若真有，處置屬裁定。

## 🚨 兩道控制探針

**⚠️ 若欄位路徑寫錯，回來的會是一片空——而那與「真的沒有」長得一模一樣。**

| 探針 | 必須 |
|---|---|
| 正向：一筆**已取得**者 | `locations[]` 內須**有** OA 項目 |
| 對照：一筆 `n477` 已查者 | 其 OA 位址數須與 `n477` 所載**相符** |

**🚨 兩道都過，這批的「沒有」才讀得成沒有。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：OpenAlex `locations[]` 現在列了什麼。
- 🚨 查不到：**列了是否取得到**——⚠️ 那要實抓，本檔不抓。
- 🚨 亦查不到：**OpenAlex 之外**——⚠️ 其 `locations` 非窮盡，
  **🚫 故「查無」仍只是「這份索引上沒有」。**
- ⚠️ 無 DOI 者查不了，**🚨 一律列名為未涵蓋，🚫 不計入「已查無」。**
"""
import io
import json
import sys
import time
from collections import Counter
from urllib.parse import quote, urlparse

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
RUNSUB = 'search-runs/b11-exogenous-cho-endurance/b11-full-run'
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require(RUNSUB)
import fetch_guard as G  # noqa: E402
from ahig.search import fulltext as F  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


cal = jload(S + 'm1_step2_calibration_set.json')
bf = jload(S + 'm1_step3_backfill.json')
scope = {c for d in cal['draws'].values() for c in d['candidateIds']}
scope |= {r['candidateId'] for p in bf['pools']
          for r in (p.get('backfilled') or []) if r.get('accepted')}
queue = {i['candidateId']: i
         for i in jload(PRIVATE_ROOT / RUNSUB / 'screening-queue' / 'queue.json')}


def status_of(cid):
    mp = (PRIVATE_ROOT / 'fulltext' / F._candidate_directory_name(cid)
          / 'manifest.json')
    return jload(mp).get('status') if mp.exists() else None


def doi_of(cid):
    ids = (queue.get(cid) or {}).get('identifiers') or {}
    return next((str(x) for x in (ids.get('doi') or []) if x), None)


email, _src = G.contact_email()
print('=== `no-oa-fulltext` 之 locations[] 複查（n+124 從未套用於此母體）===')
print('   聯絡信箱 %s' % G.masked(email))
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出請求，中止。')

targets = sorted(c for c in scope if status_of(c) == 'no-oa-fulltext')
acquired = sorted(c for c in scope if status_of(c) == 'acquired')
print('   母體 %d｜`no-oa-fulltext` %d 筆（本檔之對象）' % (len(scope), len(targets)))
print()


def oa_locations(doi):
    url = ('https://api.openalex.org/works/doi:%s?mailto=%s'
           % (quote(doi, safe=''), email))
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, None, 'HTTP %s %s' % (r['status'], r['error'])
    w = json.loads(r['body'].decode('utf-8'))
    best = (w.get('best_oa_location') or {})
    oa = [l for l in (w.get('locations') or []) if l.get('is_oa')]
    return (bool(best.get('pdf_url') or best.get('landing_page_url')), oa, '')


print('一、控制探針——🚨 未全過即不報結果')
ctl_ok = True
# 正向：已取得者必須有 OA 位址
cid = next((c for c in acquired if doi_of(c)), None)
if cid:
    hasbest, oa, err = oa_locations(doi_of(cid))
    good = bool(oa)
    ctl_ok = ctl_ok and good
    print('   %s 已取得之 %s：locations[] 內 OA 項目 %s %s'
          % ('✅' if good else '🚨', cid[-8:], len(oa) if oa is not None else '—', err))
# 對照：n477 已查者之數須相符
n477 = jload(S + 'n477_alt_oa_locations.json')
ref = next((r for r in n477['records'] if r.get('doi')
            and r.get('otherLocations') is not None), None)
if ref:
    hasbest, oa, err = oa_locations(ref['doi'])
    # n477 記的是「**扣掉已試過那個**之後」的其他位址數
    expect = ref['otherLocations']
    got = max(len(oa) - 1, 0) if oa is not None else None
    good = got == expect
    ctl_ok = ctl_ok and good
    print('   %s `n477` 已查之 %s：該檔記其他位址 %d／現算 %s %s'
          % ('✅' if good else '🚨', ref['candidateId'][-8:], expect, got, err))
else:
    print('   🚨 找不到 `n477` 對照筆')
    ctl_ok = False
if not ctl_ok:
    sys.exit('🚨 控制探針未全過——⚠️ 欄位路徑或判準有異，🚫 這批的「沒有」不予採信。')
print('   ✅ 兩道皆過：欄位讀得到，且與既有紀錄對得上。')
print()

print('二、逐筆（%d 筆）' % len(targets))
rows, nodoi = [], []
for c in targets:
    doi = doi_of(c)
    if not doi:
        nodoi.append(c[-8:])
        continue
    hasbest, oa, err = oa_locations(doi)
    if oa is None:
        rows.append({'idTail': c[-8:], 'error': err, 'oaLocations': None})
        continue
    hosts = sorted({urlparse(l.get('pdf_url') or l.get('landing_page_url') or '')
                    .netloc for l in oa if (l.get('pdf_url')
                                            or l.get('landing_page_url'))})
    rows.append({'idTail': c[-8:], 'hasBestOaLocation': hasbest,
                 'oaLocations': len(oa), 'hosts': hosts,
                 'versions': sorted({l.get('version') or '?' for l in oa})})
    if oa:
        print('   🚨 %s：`best_oa_location` %s，而 `locations[]` 有 %d 個 OA 位址'
              ' → %s' % (c[-8:], '有' if hasbest else '**無**', len(oa),
                         '／'.join(hosts)[:44]))
found = [r for r in rows if r.get('oaLocations')]
print('   ' + '-' * 74)
print('   ✅ 查得 %d 筆｜🚨 其中 locations[] 有 OA 位址者 %d 筆｜'
      '⚠️ 無 DOI 未涵蓋 %d 筆' % (len(rows), len(found), len(nodoi)))
print()

print('三、🚨 結論')
if found:
    print('   🚨 有 %d 筆被判為「無開放全文」，而索引上仍列有開放位址。' % len(found))
    print('   ⚠️ 成因與 n+124 相同：程式只讀 `best_oa_location`，🚫 沒讀 `locations[]`。')
    print('   🚫 本室未改狀態、未下載——⚠️ 處置屬裁定。')
    print('   🚨 而「取得層在 OA 範圍內已窮盡」這句話，須據此重講。')
else:
    print('   ✅ %d 筆之 `locations[]` 亦無開放位址。' % len(rows))
    print('   ⚠️ 故「已窮盡」這句話在這個母體上**也查過了**——')
    print('      🚨 先前它只查過遭擋與未探測那兩批，🚫 沒查過這 38 筆。')

c = G.counters()
doc = {
    'schemaVersion': 1,
    'documentType': 'no-oa-locations-recheck',
    'ruling': 'self-initiated: the exhaustion claim rested on probes of the '
              'blocked eleven and the unprobed twelve, while 38 records marked '
              'no-oa-fulltext had never had n+124 applied to them',
    'population': 'records in the calibration-plus-backfill scope whose manifest '
                  'status is no-oa-fulltext',
    'countingUnit': 'record',
    'criterion': 'OpenAlex locations[] entries with is_oa true; the acquisition '
                 'chain reads only best_oa_location (fulltext.py line 909)',
    'controlProbes': {'acquiredRecordHasOaLocations': True,
                      'n477ReferenceMatches': True,
                      'why': 'A wrong field path returns empty for everything, '
                             'which is indistinguishable from there being none.'},
    'targets': len(targets), 'checked': len(rows),
    'withOaLocations': len(found), 'noDoi': nodoi,
    'records': rows,
    'noChangeMade': 'No manifest, status or download was touched. What to do '
                    'about any finding is a ruling.',
    'fetchCounters': c,
    'coverageStatement': 'Whether the index lists an OA location, not whether it '
                         'can be fetched, and only this index -- OpenAlex '
                         'locations are not exhaustive, so finding none still '
                         'means none here.',
    'contentNote': 'Id tails, host names and counts only.',
}
doc['recheckHash'] = content_hash({'found': len(found), 'checked': len(rows)})
io.open(S + 'n526_no_oa_locations_recheck.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('四、對外請求：%d｜%s' % (c['totalRequests'], c['perRequestedHost']))
print('✅ 已落盤 → %sn526_no_oa_locations_recheck.json' % S)
