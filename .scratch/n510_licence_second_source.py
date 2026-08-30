# -*- coding: utf-8 -*-
"""授權未記載之 6 筆：**換一個登記處再問一次。**

## 🚨 缺口現況

第 505 輪把 12 筆無授權補到 6 筆，**⚠️ 其餘 6 筆 OpenAlex 未記載**——
**🚨 而其中四筆共用同一個出版社前綴（`10.1139/apnm-*`），是系統性缺口，🚫 不是六次偶然。**

> **⚠️ 系統性缺口的意思正是：換一個登記處，它很可能就有。**
> **🚨 「一個登記處沒有」🚫 不等於「沒有授權」——那是把一份索引的界線當成世界的界線。**

**✅ 故本檔向 Crossref 再問一次。** 🚫 不改判準、🚫 不放寬，只多一個來源。

## 🚨 Crossref 的授權欄與 OpenAlex 不是同一種東西

| | OpenAlex | Crossref |
|---|---|---|
| 欄位 | `best_oa_location.license` | `message.license[]` |
| 值 | **代碼**（`cc-by`、`cc-by-nc-nd`…） | **網址**＋`content-version`（`vor`／`am`／`tdm`） |

**🚨 而 Crossref 之 `license[]` 常包含出版社自己的條款頁或 TDM 條款**——
**⚠️ 那是「使用條件」，🚫 不是開放授權。**

> **🚨 故本檔只在網址指向 `creativecommons.org` 時才映射成代碼；
> 其餘一律原樣記下網址並標為 `unmapped`。**
> **⚠️ 把出版社條款頁寫成「授權」，等於把一個限制讀成一個許可。**

## 🚨 控制探針

**⚠️ 若欄位路徑寫錯，回來的會是一片空——而那與「Crossref 也沒有」長得一模一樣。**
**✅ 故先查一筆已知為 `cc-by` 者**（第 505 輪自 OpenAlex 填得），
**🚨 其 Crossref 回應必須含 creativecommons 網址；不含即中止，🚫 不報任何新值。**

## 🚫 預設不寫入

**⚠️ 私有根不在版控內。** ✅ 預設只落盤計畫；`--apply` 才寫，且寫前備份。
**🚫 只加欄位、不覆寫既有值**；`licenceProvenance.source` 明記為 Crossref，
**🚨 與 OpenAlex 那批分得開——⚠️ 兩個來源的值不得混為一談。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：Crossref 對該 DOI 所登記之授權網址與其 `content-version`。
- 🚨 查不到：**該授權是否適用於我們手上的那一版**——
  ⚠️ `content-version` 為 `am`（作者稿）時，其條款未必等同刊出版。**已逐筆記下該欄。**
- 🚨 亦查不到：**出版社條款頁背後的實際權利**——⚠️ 那要人讀，**🚫 本室不推定。**
"""
import io
import json
import os
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
NOTE = ('Third-party bibliographic metadata from a second register, recorded as '
        'such. A publisher terms page is a condition of use, not an open '
        'licence, and is left unmapped.')


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def crossref(doi, email):
    url = 'https://api.crossref.org/works/%s?mailto=%s' % (doi, email)
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, 'HTTP %s %s' % (r['status'], r['error'])
    msg = json.loads(r['body'].decode('utf-8')).get('message') or {}
    out = []
    for lic in (msg.get('license') or []):
        u = lic.get('URL') or ''
        m = CC.search(u)
        out.append({'url': u, 'contentVersion': lic.get('content-version'),
                    'code': ('cc-' + m.group(1).lower()).replace('cc-cc-', 'cc-')
                    if m else None})
    return out, ''


email, src = G.contact_email()
print('=== 授權未記載者之第二來源（%s）==='
      % ('✅ --apply 寫入' if APPLY else '🚫 預設：只計畫不寫入'))
print('   聯絡信箱 %s（來源 %s）' % (G.masked(email), src))
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出任何請求，中止。')

queue = {i['candidateId']: i for i in jload(RUN / 'screening-queue' / 'queue.json')}
missing, known_cc = [], None
for d in sorted(p for p in FULL.iterdir() if p.is_dir() and AD.search(p.name)):
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    m = jload(mp)
    if m.get('status') != 'acquired':
        continue
    for idx, a in enumerate(m.get('artifacts') or []):
        ids = (queue.get(m['candidateId']) or {}).get('identifiers') or {}
        doi = next((str(x) for x in (ids.get('doi') or []) if x), None)
        if not a.get('licence'):
            missing.append({'dir': d.name, 'idx': idx, 'doi': doi,
                            'sourceType': a.get('sourceType')})
        elif known_cc is None and a.get('licence') == 'cc-by' and doi:
            known_cc = {'dir': d.name, 'doi': doi, 'licence': a['licence']}
print('   仍無授權者 %d 筆（其中有 DOI 者 %d）'
      % (len(missing), sum(1 for r in missing if r['doi'])))
print()

print('一、控制探針——🚨 未過即拒絕報告')
if known_cc is None:
    sys.exit('🚨 找不到已知為 cc-by 之對照筆——🚫 中止。')
ctl, err = crossref(known_cc['doi'], email)
ok = bool(ctl) and any(c['code'] for c in ctl)
print('   %s 已知 cc-by 之 %s：Crossref 回 %d 筆授權，含 CC 網址者 %d %s'
      % ('✅' if ok else '🚨', known_cc['dir'][:8], len(ctl or []),
         sum(1 for c in (ctl or []) if c['code']), err))
if not ok:
    sys.exit('🚨 對照筆未回出 CC 網址——⚠️ 欄位路徑或來源有變，🚫 不報任何新值。')
print('   ✅ 欄位讀得到，故下面的「Crossref 也沒有」才讀得成沒有。')
print()

print('二、逐筆')
print('   %-10s %-28s %s' % ('id', 'DOI', 'Crossref 授權'))
print('   ' + '-' * 82)
plan = []
for r in missing:
    if not r['doi']:
        r.update(licences=[], mapped=None, why='無 DOI')
        plan.append(r)
        print('   %-10s %-28s 🚨 無 DOI' % (r['dir'][:8], '—'))
        continue
    lics, err = crossref(r['doi'], email)
    codes = [c['code'] for c in (lics or []) if c['code']]
    r.update(licences=lics or [], mapped=(codes[0] if codes else None), error=err)
    plan.append(r)
    if codes:
        tag = '✅ %s（content-version %s）' % (
            codes[0], '／'.join(sorted({c['contentVersion'] or '?'
                                        for c in lics if c['code']})))
    elif lics:
        tag = ('⚠️ %d 筆條款網址（content-version %s），🚫 非 CC，不映射'
               % (len(lics), '／'.join(sorted({c['contentVersion'] or '?'
                                              for c in lics}))))
    else:
        tag = '🚨 Crossref 亦未記載%s' % ((' — ' + err) if err else '')
    print('   %-10s %-28s %s' % (r['dir'][:8], r['doi'][:28], tag))
print('   ' + '-' * 82)
gained = [r for r in plan if r.get('mapped')]
unmapped = [r for r in plan if not r.get('mapped') and r.get('licences')]
none = [r for r in plan if not r.get('licences')]
print('   ✅ 映射得出 CC 授權 %d 筆｜⚠️ 有條款網址但非 CC %d 筆｜🚨 仍無 %d 筆'
      % (len(gained), len(unmapped), len(none)))
print('   🚨 出版社條款頁是「使用條件」，🚫 不是開放授權——⚠️ 故不映射、不填。')

written = []
print()
if not APPLY:
    print('三、🚫 未寫入（預設）——⚠️ 私有根不在版控內。')
    print('   ✅ 計畫：對上列 %d 筆加入 `licence` 與 `licenceProvenance`'
          '（source＝Crossref），🚫 只加欄位。' % len(gained))
else:
    print('三、✅ 寫入（先備份）')
    backup = PRIVATE_ROOT / 'fulltext-manifest-backups' / 'n510'
    backup.mkdir(parents=True, exist_ok=True)
    today = time.strftime('%Y-%m-%d')
    for r in gained:
        mp = FULL / r['dir'] / 'manifest.json'
        m = jload(mp)
        a = m['artifacts'][r['idx']]
        if a.get('licence'):
            print('   ⏸ %s 已有授權，🚫 跳過' % r['dir'][:8])
            continue
        io.open(backup / (r['dir'] + '.json'), 'w', encoding='utf-8').write(
            io.open(mp, encoding='utf-8').read())
        a['licence'] = r['mapped']
        a['licenceProvenance'] = {
            'source': 'Crossref message.license (creativecommons URL)',
            'retrievedAt': today, 'note': NOTE,
            'contentVersions': sorted({c['contentVersion'] or '?'
                                       for c in r['licences'] if c['code']})}
        io.open(mp, 'w', encoding='utf-8').write(
            json.dumps(m, ensure_ascii=False, indent=2) + '\n')
        written.append(r['dir'][:8])
        print('   ✅ %s ← %s' % (r['dir'][:8], r['mapped']))
    print('   ✅ 已寫入 %d 筆。' % len(written))

c = G.counters()
print()
print('四、對外請求（閘門產出）：總數 %d｜逐主機 %s｜封鎖 %s'
      % (c['totalRequests'], c['perRequestedHost'], c['blockedHosts'] or '無'))

doc = {
    'schemaVersion': 1,
    'documentType': 'licence-second-source',
    'ruling': 'follows n+138(3) with a second register: OpenAlex recorded nothing '
              'for six artifacts, four of them sharing one publisher prefix, and '
              'a systematic gap in one index is exactly the case where another '
              'index may hold it.',
    'population': 'acquired artifacts still carrying no licence after round 505',
    'countingUnit': 'artifact',
    'criterion': 'Crossref message.license; mapped to a code only when the URL is '
                 'a creativecommons.org licence, otherwise recorded verbatim and '
                 'left unmapped',
    'whyUnmapped': 'Crossref license entries frequently carry the publisher\'s own '
                   'terms or TDM conditions. Those are conditions of use, not an '
                   'open licence; writing one into the licence field would read a '
                   'restriction as a permission.',
    'controlProbe': {'dir': known_cc['dir'][:8], 'knownLicence': known_cc['licence'],
                     'crossrefReturnedCc': ok,
                     'why': 'A wrong field path returns nothing, which is '
                            'indistinguishable from Crossref holding nothing.'},
    'stillMissingBefore': len(missing),
    'mapped': [{'dir': r['dir'][:8], 'licence': r['mapped'],
                'contentVersions': sorted({c['contentVersion'] or '?'
                                           for c in r['licences'] if c['code']})}
               for r in gained],
    'unmappedTermsOnly': [{'dir': r['dir'][:8], 'doi': r['doi'],
                           'entries': [{'url': c['url'],
                                        'contentVersion': c['contentVersion']}
                                       for c in r['licences']]}
                          for r in unmapped],
    'readingOfUnmapped': 'Two registers now agree that no open licence is on '
                         'record for these: OpenAlex holds no licence for the OA '
                         "location, and Crossref holds only the publisher's own "
                         'terms. That is a stronger statement than "unknown", and '
                         'a weaker one than "not open access" -- it says nothing '
                         'about rights that exist outside both registers.',
    'stillNone': [r['dir'][:8] for r in none],
    'applied': bool(APPLY),
    'written': written,
    'fetchCounters': c,
    'coverageStatement': 'Two registers now, not one. Neither is a publisher '
                         'statement and neither is a verification by this room. '
                         'Where the licence applies to an author manuscript the '
                         'content-version is recorded, because those terms need '
                         'not match the published version.',
    'contentNote': 'Directory prefixes, DOIs and licence URLs only.',
}
doc['secondSourceHash'] = content_hash({'mapped': len(gained),
                                        'none': len(none)})
io.open(S + 'n510_licence_second_source.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn510_licence_second_source.json' % S)
