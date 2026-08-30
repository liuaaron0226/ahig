# -*- coding: utf-8 -*-
"""最後那一筆 `incomplete`：**三條路裡有兩條「不適用」，而那不等於「沒有」。**

## 🚨 收尾到這一筆為止

母體 84 之中未取得者 57 筆，本室已逐批查過：

| 批 | 筆數 | 已查於 |
|---|---|---|
| `no-oa-fulltext` | 38 | 第 526 輪（`locations[]` 全查，0 筆另有位址） |
| `available-pdf`／`available-landing-page` | 18 | `n450`／`n455`／`n477`／`n494`（本輪覆核：**18 筆全數在列**） |
| **`incomplete`** | **1** | **🚨 本檔** |

**✅ 38＋18＋1 ＝ 57，母體閉合。**

## 🚨 那一筆為什麼是 `incomplete` 而不是 `no-oa-fulltext`

```
europe-pmc   http 404   conclusion=miss
openalex     http —     conclusion=not-applicable     ← 🚨 無 DOI
unpaywall    http —     conclusion=not-applicable     ← 🚨 無 DOI
```

> **⚠️ 三條路只有一條真的問到了，另外兩條問不到。**
> **🚨 故狀態是 `incomplete` 而不是 `no-oa-fulltext`——那個區分是對的：**
> **「問不到」🚫 不等於「答案是沒有」。**

**⚠️ 而它有 PMCID。** 🚨 Europe PMC 回 404，**但 Europe PMC 不是 PMC 的唯一入口。**

## ✅ 本檔做什麼

**向 NCBI 之 PMC OA 服務問同一個 PMCID**——**🚨 同一個識別碼，換一個登記處**，
與第 510／511 輪對授權所做的是同一手。

**🚫 不下載全文、🚫 不改狀態**——⚠️ 狀態要不要改屬裁定。

## 🚨 控制探針

**⚠️ 端點或欄位一寫錯，回來的就是「查無」——而那與「真的沒有」長得一模一樣。**
**✅ 故先問一筆**已由 Europe PMC 取得**之 PMCID，NCBI 必須也說有；
🚨 說沒有即中止，🚫 不報那一筆的結果。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：NCBI 之 OA 服務對該 PMCID 說有沒有可取之全文。
- 🚨 查不到：**PMC 之外**——⚠️ 無 DOI 者本來就問不到 OpenAlex／Unpaywall，
  **🚫 本檔補不上那兩條。**
- ⚠️ 🚫 不改狀態：**「查過而仍無」與「可以標成 no-oa-fulltext」是兩件事**，
  🚨 後者是裁定。
"""
import io
import json
import re
import sys

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
# 🚨 兩種形狀都試過，兩種都 404（見 docstring「到此為止」一節）：
#   www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi   → 404
#   pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi       → 404
# ⚠️ 依 n+168（二）1，連兩種形狀失敗即停，🚫 不再猜。
# ✅ 改以**已驗證可用**之 Europe PMC `fullTextXML` 作為「這個問題問得成立」之證明，
#    🚨 但它與當初取得時走的是同一個服務，故**不構成第二個登記處**——
#    ⚠️ 本檔因此不宣稱「已換登記處查過」。
OA_TRIED = ('https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?id=%s',
            'https://pmc.ncbi.nlm.nih.gov/utils/oa/oa.fcgi?id=%s')
EPMC = 'https://www.ebi.ac.uk/europepmc/webservices/rest/%s/fullTextXML'
REC = re.compile(rb'<record\b')
ERR = re.compile(rb'<error\b[^>]*code="([^"]+)"')


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


cal = jload(S + 'm1_step2_calibration_set.json')
bf = jload(S + 'm1_step3_backfill.json')
scope = {c for d in cal['draws'].values() for c in d['candidateIds']}
scope |= {r['candidateId'] for p in bf['pools']
          for r in (p.get('backfilled') or []) if r.get('accepted')}
queue = {i['candidateId']: i
         for i in jload(PRIVATE_ROOT / RUNSUB / 'screening-queue' / 'queue.json')}


def manifest(cid):
    mp = (PRIVATE_ROOT / 'fulltext' / F._candidate_directory_name(cid)
          / 'manifest.json')
    return jload(mp) if mp.exists() else None


def pmcid_of(cid, man):
    if man and man.get('pmcid'):
        return man['pmcid']
    ids = (queue.get(cid) or {}).get('identifiers') or {}
    v = next((str(x) for x in (ids.get('pmcid') or []) if x), None)
    return v


email, _src = G.contact_email()
print('=== 最後一筆 `incomplete` 之收尾（🚫 不下載、不改狀態）===')
print('   聯絡信箱 %s' % G.masked(email))
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出請求，中止。')

targets, acquired = [], []
for c in sorted(scope):
    m = manifest(c)
    if not m:
        continue
    if m.get('status') == 'incomplete':
        targets.append((c, m))
    elif m.get('status') == 'acquired' and pmcid_of(c, m):
        acquired.append((c, m))
print('   母體 84｜`incomplete` %d 筆｜可作對照之已取得（有 PMCID）%d 筆'
      % (len(targets), len(acquired)))
if not targets:
    sys.exit('⚠️ 無 `incomplete` 待辦——🚫 本輪無事可做（這不是失敗）。')
print()


def ncbi_oa(pmcid):
    """NCBI 之 OA 服務。🚨 兩種形狀皆試；兩種都失敗即回 (None, 原因)。"""
    notes = []
    for tmpl in OA_TRIED:
        r = G.fetch(tmpl % pmcid, email=email)
        if r['skipped'] or r['status'] != 200:
            notes.append('%s → HTTP %s' % (tmpl.split('?')[0][8:38], r['status']))
            continue
        body = r['body'] or b''
        if REC.search(body):
            return True, ''
        err = ERR.search(body)
        return False, (err.group(1).decode('ascii', 'replace') if err
                       else 'no-record')
    return None, '；'.join(notes)


def epmc_fulltext(pmcid):
    """Europe PMC 之 fullTextXML。⚠️ 與取得時同一服務，🚫 不是第二個登記處。"""
    r = G.fetch(EPMC % pmcid, email=email)
    if r['skipped'] or r['status'] != 200:
        return False, 'HTTP %s' % r['status']
    return bool((r['body'] or b'').lstrip().startswith(b'<?xml')), ''


print('一、控制探針——🚨 未過即不報結果')
ctl_cid, ctl_man = acquired[0]
ctl_pmcid = pmcid_of(ctl_cid, ctl_man)
ncbi_ctl, ncbi_note = ncbi_oa(ctl_pmcid)
print('   %s NCBI OA 服務對已取得之 %s（%s）：%s'
      % ('✅' if ncbi_ctl else '🚨', ctl_cid[-8:], ctl_pmcid,
         ('有' if ncbi_ctl else ('端點不可用：' + ncbi_note))))
epmc_ctl, epmc_note = epmc_fulltext(ctl_pmcid)
print('   %s Europe PMC fullTextXML 對同一筆：%s %s'
      % ('✅' if epmc_ctl else '🚨', '有' if epmc_ctl else '無', epmc_note))
if ncbi_ctl is None and not epmc_ctl:
    sys.exit('🚨 兩邊皆不可用——🚫 不報目標之結果。')
if ncbi_ctl is None:
    print('   ⚠️ NCBI 之 OA 服務兩種形狀皆 404，🚫 依 n+168（二）1 就此打住，不再猜。')
    print('   ✅ 而 Europe PMC 之 fullTextXML 對已取得者回得出全文——')
    print('      🚨 故「這個問題問得成立」有證，⚠️ 但那是**同一個服務**，'
          '🚫 不構成第二個登記處。')
print()

print('二、目標')
rows = []
for cid, man in targets:
    pmcid = pmcid_of(cid, man)
    ids = (queue.get(cid) or {}).get('identifiers') or {}
    row = {'idTail': cid.split(':')[-1][-8:], 'pmcid': pmcid,
           'hasDoi': bool(ids.get('doi')), 'hasPmid': bool(ids.get('pmid')),
           'attempts': [{'sourceId': a.get('sourceId'),
                         'httpStatus': a.get('httpStatus'),
                         'conclusion': a.get('conclusion')}
                        for a in (man.get('attempts') or [])]}
    if not pmcid:
        row.update(ncbiSaysAvailable=None, note='無 PMCID')
    else:
        ok, note = ncbi_oa(pmcid)
        row.update(ncbiSaysAvailable=ok, note=note)
        if ok is None:
            e_ok, e_note = epmc_fulltext(pmcid)
            row.update(europePmcFullText=e_ok, europePmcNote=e_note)
    rows.append(row)
    print('   %s（%s）' % (row['idTail'], pmcid or '無 PMCID'))
    print('      既有三條路：%s'
          % '；'.join('%s→%s' % (a['sourceId'], a['conclusion'])
                      for a in row['attempts']))
    if row['ncbiSaysAvailable'] is None:
        print('      NCBI OA 服務：🚫 端點不可用（%s）' % row['note'][:56])
        print('      Europe PMC fullTextXML（⚠️ 同一服務，非第二登記處）：%s %s'
              % ('🚨 有' if row.get('europePmcFullText') else '✅ 無',
                 row.get('europePmcNote') or ''))
    else:
        print('      NCBI OA 服務：%s %s'
              % ('🚨 有可取全文' if row['ncbiSaysAvailable'] else '✅ 無',
                 row['note']))
print()

found = [r for r in rows if r.get('ncbiSaysAvailable')
         or r.get('europePmcFullText')]
print('三、🚨 結論')
if found:
    print('   🚨 %d 筆在 NCBI 之 OA 服務上列有可取全文——'
          '⚠️ 而 Europe PMC 回 404。' % len(found))
    print('   ⚠️ 即：同一個 PMCID，兩個入口答案不同。🚫 處置屬裁定。')
else:
    print('   ✅ 可問到的入口都說無。')
    print('   🚨 而本輪**未能**換到第二個登記處**：NCBI 之 OA 服務兩種形狀皆 404，')
    print('      ⚠️ 依 n+168（二）1 就此打住，🚫 不再猜第三種。')
    print('   🚨 故該筆維持 `incomplete`，且理由要講準：')
    print('      ⚠️ 🚫 不是「已確認沒有開放全文」，')
    print('      ✅ 是「三條路裡兩條因無 DOI 問不到，第三條說無，'
          '而第二個 PMC 入口本輪問不到」。')
    print('   ⚠️ 若要續辦，具名之下一步是 NCBI E-utilities（`esummary`／`efetch`，'
          '不同服務而非同一形狀之再猜）——🚫 屬裁定。')

c = G.counters()
doc = {
    'schemaVersion': 1,
    'documentType': 'incomplete-record-closeout',
    'ruling': 'closes the scope: 38 no-oa-fulltext were rechecked in round 526, '
              'the 18 with an address are all covered by existing probes, and '
              'this is the remaining one',
    'population': 'records in the calibration-plus-backfill scope with status '
                  'incomplete',
    'countingUnit': 'record',
    'criterion': 'NCBI PMC OA service for the same PMCID Europe PMC missed; two '
                 'endpoint shapes tried, both 404, so per n+168(2)(1) no third '
                 'guess was made',
    'secondRegisterReached': False,
    'secondRegisterNote': 'The point of the check was to ask a second register. '
                          'Both shapes of the NCBI OA service returned 404, so it '
                          'was not reached. Europe PMC fullTextXML answers for the '
                          'control, which shows the question is well formed, but '
                          'it is the same service the chain already used and is '
                          'therefore not a second register.',
    'namedNextStep': 'NCBI E-utilities (esummary/efetch) -- a different service '
                     'rather than another guess at the same one. A ruling, not '
                     "this room to take.",
    'statusUnchangedReason': 'Not "confirmed to have no open full text" but '
                             '"two of three routes unaskable for want of a DOI, '
                             'the third says no, and the second PMC entry point '
                             'could not be reached this round".',
    'whyIncompleteNotNoOa': 'Two of the three routes returned not-applicable for '
                            'want of a DOI. Unable to ask is not the same as the '
                            'answer being no, which is what that status is for.',
    'controlProbe': {'idTail': ctl_cid.split(':')[-1][-8:], 'pmcid': ctl_pmcid,
                     'ncbiSaysAvailable': ncbi_ctl,
                     'ncbiNote': ncbi_note,
                     'europePmcFullText': epmc_ctl,
                     'why': 'A wrong endpoint returns not-found for everything, '
                            'which is indistinguishable from genuinely absent.'},
    'records': rows,
    'anyAvailableAtNcbi': [r['idTail'] for r in found],
    'scopeClosure': {'noOaFulltext': 38, 'withAddressProbed': 18,
                     'incomplete': len(rows), 'totalUnacquired': 57},
    'noChangeMade': 'No status changed, nothing downloaded. Whether this may now '
                    'be called no-oa-fulltext is a ruling.',
    'fetchCounters': c,
    'coverageStatement': 'Covers the PMC route only. Without a DOI the OpenAlex '
                         'and Unpaywall routes remain unaskable, and this does '
                         'not substitute for them.',
    'contentNote': 'Id tails, PMCIDs and conclusions only.',
}
doc['closeoutHash'] = content_hash({'found': len(found), 'n': len(rows)})
io.open(S + 'n527_incomplete_record_closeout.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('四、對外請求：%d｜%s' % (c['totalRequests'], c['perRequestedHost']))
print('✅ 已落盤 → %sn527_incomplete_record_closeout.json' % S)
