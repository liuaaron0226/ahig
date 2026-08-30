# -*- coding: utf-8 -*-
"""第三個登記處：**Crossref 回 404 的那一筆，該去它真正的登記機構問。**

## 🚨 這是上一輪自己留下的線頭

第 510 輪末寫：「學位論文那筆之 DOI 非 Crossref 登記（404），**應另循其典藏庫，本輪未追。**」
**⚠️ 一句「未追」若沒有下一輪，就只是把缺口換個地方寫。**

**🚨 而 404 本身是一項資訊，🚫 不是失敗**：
DOI 由多個登記機構（RA）分別管理——**Crossref 主要是期刊，DataCite 主要是典藏庫與資料集。**
**⚠️ 一個典藏庫 DOI 在 Crossref 查不到，是正常的；去錯地方問而已。**

## 🚨 這一筆為什麼特別要緊

它是本語料**篇幅最大**的一份（節切檢查所見：**348,621 字元、160 節**）。
**⚠️ 引用多少、能不能附進附錄，這一格影響的量最大。**

## 🚨 控制探針：這裡沒有「已知答案」可以對照

**⚠️ 前兩輪的探針都是「拿已知授權的一筆回查」。此處沒有已知的 DataCite 筆可用。**
**✅ 故改驗結構**：回應之 `data.attributes.doi` 必須等於我們問的那個 DOI。

> **🚨 那道探針分得出兩件事**：
> ⚠️ 「端點或欄位路徑寫錯」（拿不到 doi 欄）與
> **「登記處確實沒記授權」（doi 欄對得上，而 `rightsList` 是空的）。**
> **⚠️ 少了它，兩者都只是一片空白。**

## 🚫 本檔不做什麼

- **🚫 不映射非 CC 之權利敘述**——⚠️ 與第 510 輪同一條界線：
  **🚨 條款頁與 TDM 條款是使用條件，不是開放授權。**
- **🚫 預設不寫入**；`--apply` 才寫，寫前備份到私有根（🚫 不進版控）。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：DataCite 對該 DOI 所登記之 `rightsList`。
- 🚨 查不到：**典藏庫網頁上寫的授權**——⚠️ 那要讀網頁，🚫 本檔不抓落地頁
  （其路徑內嵌逐字題名，n+48 五道抓不到該型）。
- ⚠️ 三個登記處都查過之後仍無，**🚨 那句話的意思仍只是「三份索引裡沒有」。**
"""
import io
import json
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
RUNSUB = 'search-runs/b11-exogenous-cho-endurance/b11-full-run'
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require(RUNSUB)
import fetch_guard as G  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
FULL = PRIVATE_ROOT / 'fulltext'
RUN = PRIVATE_ROOT / RUNSUB
AD = re.compile(r'-[0-9a-f]{16}$')
APPLY = '--apply' in sys.argv
CC = re.compile(r'creativecommons\.org/licenses/([a-z-]+)/', re.I)


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def datacite(doi, email):
    url = 'https://api.datacite.org/dois/%s' % doi
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, None, 'HTTP %s %s' % (r['status'], r['error'])
    att = (json.loads(r['body'].decode('utf-8')).get('data') or {}) \
        .get('attributes') or {}
    rights = []
    for x in (att.get('rightsList') or []):
        u = x.get('rightsUri') or ''
        m = CC.search(u)
        rights.append({'uri': u, 'rights': x.get('rights'),
                       'identifier': x.get('rightsIdentifier'),
                       'code': ('cc-' + m.group(1).lower()) if m else None})
    return att.get('doi'), rights, ''


email, src = G.contact_email()
print('=== 第三個登記處：DataCite（%s）==='
      % ('✅ --apply 寫入' if APPLY else '🚫 預設：只計畫不寫入'))
print('   聯絡信箱 %s（來源 %s）' % (G.masked(email), src))
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出任何請求，中止。')

# ── 母體：第 510 輪 Crossref 回 404 者 ───────────────────────────
prev = jload(S + 'n510_licence_second_source.json')
targets = [r for r in prev['stillNone']]
queue = {i['candidateId']: i for i in jload(RUN / 'screening-queue' / 'queue.json')}
rows = []
for d in sorted(p for p in FULL.iterdir() if p.is_dir() and AD.search(p.name)):
    if d.name[:8] not in targets:
        continue
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    m = jload(mp)
    for idx, a in enumerate(m.get('artifacts') or []):
        if a.get('licence'):
            continue
        ids = (queue.get(m['candidateId']) or {}).get('identifiers') or {}
        doi = next((str(x) for x in (ids.get('doi') or []) if x), None)
        rows.append({'dir': d.name, 'idx': idx, 'doi': doi})
print('   母體：第 510 輪 Crossref 未登記者 %d 筆' % len(rows))
if not rows:
    sys.exit('⚠️ 無待查者——🚫 本輪無事可做（這不是失敗）。')
print()

print('一、控制探針（🚨 此處無「已知答案」，故驗結構）')
probe = rows[0]
got_doi, rights, err = datacite(probe['doi'], email)
ok = (got_doi or '').lower() == (probe['doi'] or '').lower()
print('   %s 回應之 `data.attributes.doi` = %r，問的是 %r %s'
      % ('✅' if ok else '🚨', got_doi, probe['doi'], err))
if not ok:
    sys.exit('🚨 結構探針未過——⚠️ 端點或欄位路徑有問題，'
             '🚫 故任何「沒有授權」都只是一片空白，不予採信。')
print('   ✅ 端點與欄位路徑正確，故 `rightsList` 為空才讀得成「未登記授權」。')
print()

print('二、逐筆')
print('   %-10s %-30s %s' % ('id', 'DOI', 'DataCite rightsList'))
print('   ' + '-' * 84)
plan = []
for r in rows:
    if r is probe:
        d_doi, rl, e = got_doi, rights, err
    else:
        d_doi, rl, e = datacite(r['doi'], email)
    codes = [x['code'] for x in (rl or []) if x['code']]
    r.update(rights=rl or [], mapped=(codes[0] if codes else None), error=e)
    plan.append(r)
    if codes:
        tag = '✅ %s' % codes[0]
    elif rl:
        labels = [str(x['rights'] or x['identifier'] or x['uri'] or '?')
                  for x in rl]
        tag = '⚠️ %d 項權利敘述但非 CC：%s' % (len(rl), '／'.join(labels)[:40])
    else:
        tag = '🚨 未登記授權%s' % ((' — ' + e) if e else '')
    print('   %-10s %-30s %s' % (r['dir'][:8], (r['doi'] or '—')[:30], tag))
print('   ' + '-' * 84)
gained = [r for r in plan if r.get('mapped')]
print('   ✅ 映射得出 CC 授權 %d／%d' % (len(gained), len(plan)))

written = []
print()
if not APPLY or not gained:
    print('三、%s' % ('🚫 未寫入（預設）' if gained else '🚫 無可寫之值'))
    if gained:
        print('   ✅ 計畫：對 %d 筆加入 `licence` 與 `licenceProvenance`'
              '（source＝DataCite）。' % len(gained))
else:
    print('三、✅ 寫入（先備份）')
    backup = PRIVATE_ROOT / 'fulltext-manifest-backups' / 'n511'
    backup.mkdir(parents=True, exist_ok=True)
    today = time.strftime('%Y-%m-%d')
    for r in gained:
        mp = FULL / r['dir'] / 'manifest.json'
        m = jload(mp)
        a = m['artifacts'][r['idx']]
        if a.get('licence'):
            continue
        io.open(backup / (r['dir'] + '.json'), 'w', encoding='utf-8').write(
            io.open(mp, encoding='utf-8').read())
        a['licence'] = r['mapped']
        a['licenceProvenance'] = {
            'source': 'DataCite rightsList (creativecommons URI)',
            'retrievedAt': today,
            'note': 'Third-party metadata from the DOI registration agency that '
                    'actually holds this DOI. Not a verification by this room.'}
        io.open(mp, 'w', encoding='utf-8').write(
            json.dumps(m, ensure_ascii=False, indent=2) + '\n')
        written.append(r['dir'][:8])
        print('   ✅ %s ← %s' % (r['dir'][:8], r['mapped']))

c = G.counters()
print()
print('四、對外請求（閘門產出）：總數 %d｜逐主機 %s｜封鎖 %s'
      % (c['totalRequests'], c['perRequestedHost'], c['blockedHosts'] or '無'))

doc = {
    'schemaVersion': 1,
    'documentType': 'licence-third-register',
    'ruling': 'closes a loose end this room named itself in round 510: the DOI '
              'that returned 404 at Crossref is registered with a different '
              'agency, and a 404 there is information rather than failure.',
    'population': 'artifacts still without a licence whose DOI Crossref does not '
                  'hold',
    'countingUnit': 'artifact',
    'criterion': 'DataCite data.attributes.rightsList, mapped to a code only for '
                 'a creativecommons.org URI',
    'controlProbe': {'kind': 'structural', 'askedDoi': probe['doi'],
                     'returnedDoi': got_doi, 'matches': ok,
                     'why': 'No record here has a licence known in advance, so '
                            'the probe checks the endpoint and field path '
                            'instead: without it, a wrong path and a genuinely '
                            'empty rightsList are the same blank.'},
    'records': [{'dir': r['dir'][:8], 'doi': r['doi'],
                 'rights': r['rights'], 'mapped': r['mapped'],
                 'error': r.get('error', '')} for r in plan],
    'mapped': len(gained),
    'applied': bool(APPLY),
    'written': written,
    'fetchCounters': c,
    'coverageStatement': 'Three registers have now been asked. Still-absent means '
                         'absent from three indexes, not absent from the world; '
                         'the repository landing page is not fetched, since its '
                         'path embeds the verbatim title.',
    'contentNote': 'Directory prefixes, DOIs and rights URIs only.',
}
doc['thirdRegisterHash'] = content_hash({'mapped': len(gained), 'n': len(plan)})
io.open(S + 'n511_datacite_licence.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn511_datacite_licence.json' % S)
