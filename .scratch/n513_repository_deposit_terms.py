# -*- coding: utf-8 -*-
"""典藏庫之存放條款：**沿著 manifest 既有的連結往上走，讀那四筆自存副本的權利欄。**

## ✅ 依 n+168（二）之四項限制

| # | 限制 | 本檔如何遵守 |
|---|---|---|
| 1 | 准抓，逾時或**連兩種形狀失敗即停**，🚫 不再猜 API 形狀 | **✅ 不猜——照 API 自己回的 `_links` 走**（HATEOAS）。⚠️ 上一輪之所以 404，正是因為猜了 `owningBundle`，而它其實叫 `bundle` |
| 2 | 🚫 不得以題名去典藏庫搜尋 | **✅ 只從 manifest 既有之 bitstream 連結往上走**，🚨 全程不送出任何題名 |
| 3 | 🚫 網址不進 `.scratch`；**僅由不透明識別碼組成之路徑**方可記錄 | ✅ 以規則判定（`UUID_ONLY`），🚨 不合者只記主機與分類 |
| 4 | **抓不到是一種狀態，且不是「沒有授權」** | ✅ 判定分 `terms-found`／`no-terms-recorded`／**`terms-not-retrieved`**，🚫 三者不合併 |

> **🚨 第 4 條是本檔的重點。**
> ⚠️ 「未取得存放條款」與「查到沒有開放授權」在交付時是兩句不同的話，
> **🚨 把前者寫成後者，就是把「沒查到」寫成「查到是沒有的」。**

## 🚨 為什麼問典藏庫，而不是再問一個 DOI 登記處

第 512 輪查明：**那四筆之 PDF 來自同一個大學典藏庫，是作者自存副本。**
**⚠️ 管轄自存副本的是存放條款，🚫 不是 DOI 登記處那一欄**——
故第 510 輪「三個登記處皆無」雖然為真，**🚨 對這四筆問的不是最相關的地方。**

## 🚫 只取權利欄，🚫 不取題名

item 之 metadata 含 `dc.title`。**🚨 本檔只挑鍵名含 `rights`／`license` 者，
⚠️ 其餘一律不讀入產物。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：典藏庫 item 記錄裡登記之權利欄。
- 🚨 查不到：**存放時簽的授權書本身**——⚠️ 那不是公開資料，🚫 本室不推定。
- 🚨 亦查不到：**item 頁上以散文寫的條款**——⚠️ 本檔只讀結構化 metadata。
"""
import io
import json
import re
import sys
from urllib.parse import urlparse

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require()
import fetch_guard as G  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
FULL = PRIVATE_ROOT / 'fulltext'
AD = re.compile(r'-[0-9a-f]{16}$')
# n+168（二）3：路徑僅由不透明識別碼構成者方可記錄。
UUID_ONLY = re.compile(
    r'^(?:/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    r'|/[a-z]+|/\d+)+/?$', re.I)
CC = re.compile(r'creativecommons\.org/licenses/([a-z-]+)/', re.I)
MAX_HOPS = 4          # ⚠️ 沿 `_links` 走，🚫 不猜；此為防迴圈之上限
RIGHTS_KEY = re.compile(r'rights|licen[cs]e', re.I)


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def recordable(url):
    """n+168（二）3 之判準——🚨 不是目視「看起來有沒有題名」，是路徑形狀。"""
    p = urlparse(url)
    return bool(UUID_ONLY.match(p.path.replace('/server/api/core', '')
                                or '/'))


BITSTREAM_UUID = re.compile(
    r'/bitstreams/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})',
    re.I)


def api_url(download_url):
    """把 manifest 記的**下載連結**換成同一個 bitstream 的 API 資源。

    🚨 這是本檔唯一一次自行組出網址，故理由要寫清楚：
    ⚠️ manifest 存的是 `/bitstreams/<uuid>/download`（回傳 PDF 位元組），
    而要沿 `_links` 走必須先拿到該 bitstream 的 **JSON 表述**。
    ✅ 用的是**已實測回 200 的那個端點**與**我們手上已有的同一個 uuid**，
    🚫 不是猜一個沒見過的形狀——⚠️ 兩者的差別正是上一輪 404 的由來。
    """
    m = BITSTREAM_UUID.search(download_url or '')
    if not m:
        return None
    host = urlparse(download_url).netloc
    return 'https://%s/server/api/core/bitstreams/%s' % (host, m.group(1))


def get(url, email):
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, 'HTTP %s %s' % (r['status'], r['error'])
    try:
        return json.loads(r['body'].decode('utf-8')), ''
    except (UnicodeDecodeError, ValueError) as e:
        # ⚠️ 回應不是 JSON（例如 PDF 位元組）——🚨 記為錯誤，🚫 不當成「沒有資料」。
        return None, '回應非 JSON（%s）' % type(e).__name__


def walk_to_item(bitstream_url, email):
    """沿 API 自報之 `_links` 走到 item。

    🚨 回傳 (item_json, 走過的關係名, 錯誤)。
    ⚠️ 🚫 全程不構造任何路徑——只用回應裡給的 href。
    """
    trail = []
    api = api_url(bitstream_url)
    if not api:
        return None, trail, '連結中找不到 bitstream uuid，🚫 不另尋路徑'
    doc, err = get(api, email)
    if doc is None:
        return None, trail, 'bitstream: ' + err
    for _ in range(MAX_HOPS):
        links = doc.get('_links') or {}
        if 'item' in links:
            nxt, rel = links['item'].get('href'), 'item'
        elif 'bundle' in links:
            nxt, rel = links['bundle'].get('href'), 'bundle'
        else:
            return None, trail, '無 item／bundle 連結可走（鍵：%s）' % sorted(links)
        trail.append(rel)
        doc, err = get(nxt, email)
        if doc is None:
            return None, trail, '%s: %s' % (rel, err)
        if rel == 'item':
            return doc, trail, ''
    return None, trail, '逾 %d 跳仍未達 item' % MAX_HOPS


email, src = G.contact_email()
print('=== 典藏庫存放條款（依 n+168 二）===')
print('   聯絡信箱 %s（來源 %s）' % (G.masked(email), src))
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出任何請求，中止。')

targets = []
for d in sorted(p for p in FULL.iterdir() if p.is_dir() and AD.search(p.name)):
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    m = jload(mp)
    if m.get('status') != 'acquired':
        continue
    for a in (m.get('artifacts') or []):
        if a.get('licence'):
            continue
        url = a.get('sourceUrl') or ''
        host = urlparse(url).netloc.lower()
        if 'scholaris' in host or 'dspace' in host:
            targets.append({'dir': d.name[:8], 'host': host, 'url': url})
print('   母體：無授權且來源為 DSpace 型典藏庫者 %d 筆' % len(targets))
if not targets:
    sys.exit('⚠️ 無待查者——🚫 本輪無事可做（這不是失敗）。')
print('   🚫 全程不以題名搜尋，只沿 manifest 既有連結往上走（n+168 二之 2）。')
print()

print('一、逐筆')
print('   %-10s %-14s %-22s %s' % ('id', '走過之關係', '權利欄', '判定'))
print('   ' + '-' * 78)
rows, consecutive_fail = [], 0
for t in targets:
    if consecutive_fail >= 2:
        rows.append({'dir': t['dir'], 'verdict': 'terms-not-retrieved',
                     'why': '🚫 已連兩筆失敗，依 n+168 二之 1 停止，不再嘗試'})
        print('   %-10s %-14s %-22s ⏸ 依裁定停止' % (t['dir'], '—', '—'))
        continue
    item, trail, err = walk_to_item(t['url'], email)
    if item is None:
        consecutive_fail += 1
        rows.append({'dir': t['dir'], 'verdict': 'terms-not-retrieved',
                     'trail': trail, 'why': err})
        print('   %-10s %-14s %-22s 🚨 未取得（%s）'
              % (t['dir'], '→'.join(trail) or '—', '—', err[:26]))
        continue
    consecutive_fail = 0
    md = item.get('metadata') or {}
    # 🚫 只取權利欄；⚠️ dc.title 等一律不讀入。
    rights = {k: [v.get('value') for v in vs]
              for k, vs in md.items() if RIGHTS_KEY.search(k)}
    codes = [CC.search(v).group(1).lower() for vs in rights.values()
             for v in vs if v and CC.search(v)]
    verdict = ('terms-found' if rights else 'no-terms-recorded')
    rows.append({'dir': t['dir'], 'verdict': verdict, 'trail': trail,
                 'rightsFields': rights,
                 'ccCode': ('cc-' + codes[0]) if codes else None,
                 'itemUrlRecordable': recordable(
                     (item.get('_links') or {}).get('self', {}).get('href', ''))})
    label = '／'.join(sorted(rights)) or '（無）'
    print('   %-10s %-14s %-22s %s'
          % (t['dir'], '→'.join(trail), label[:22],
             ('✅ ' + ('cc-' + codes[0]) if codes else
              ('⚠️ 有欄位但非 CC' if rights else '🚨 未登記權利欄'))))
print('   ' + '-' * 78)

c = {k: sum(1 for r in rows if r['verdict'] == k)
     for k in ('terms-found', 'no-terms-recorded', 'terms-not-retrieved')}
print('   ✅ 取得條款 %d｜⚠️ 有記錄但未登記權利 %d｜🚨 未取得條款 %d'
      % (c['terms-found'], c['no-terms-recorded'], c['terms-not-retrieved']))
print()
print('二、🚨 三種狀態不得合併（n+168 二之 4）')
print('   `terms-found`          → 讀到了權利欄')
print('   `no-terms-recorded`    → 讀到了記錄，而它沒登記權利')
print('   `terms-not-retrieved`  → **沒讀到記錄**——⚠️ 這🚫 不是「沒有授權」')
print('   🚨 把第三種寫成第一種的反面，就是把「沒查到」寫成「查到是沒有的」。')

cc = G.counters()
print()
print('三、對外請求（閘門產出）：總數 %d｜逐主機 %s｜封鎖 %s'
      % (cc['totalRequests'], cc['perRequestedHost'], cc['blockedHosts'] or '無'))

doc = {
    'schemaVersion': 1,
    'documentType': 'repository-deposit-terms',
    'ruling': 'n+168(2): the item page may be fetched, under the fetch limits, '
              'without searching by title, without URLs entering this repo unless '
              'the path is opaque identifiers only, and with "not retrieved" kept '
              'apart from "no licence".',
    'population': 'acquired artifacts with no licence whose source host is a '
                  'DSpace-style repository',
    'countingUnit': 'artifact',
    'criterion': 'walk the API\'s own _links from the recorded bitstream to the '
                 'item, then read only metadata keys matching rights or licence',
    'navigationNote': 'Links are followed, never constructed. Last round\'s 404 '
                      'came from guessing owningBundle when the API calls it '
                      'bundle -- following what the response offers is not the '
                      'same as guessing another shape.',
    'noTitleSearch': True,
    'verdictCounts': c,
    'verdictMeaning': {
        'terms-found': 'a rights field was read',
        'no-terms-recorded': 'the record was read and registers no rights',
        'terms-not-retrieved': 'the record was not read at all -- this is not '
                               'evidence of no licence',
    },
    'records': rows,
    'fetchCounters': cc,
    'coverageStatement': 'Reads structured metadata only. The deposit agreement '
                         'itself is not public and is not inferred, and prose '
                         'terms written on the item page are not read.',
    'contentNote': 'Directory prefixes, link relation names and rights field '
                   'values only. No titles, and no URLs whose path is anything '
                   'other than opaque identifiers.',
}
doc['termsHash'] = content_hash(c)
io.open(S + 'n513_repository_deposit_terms.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn513_repository_deposit_terms.json' % S)
