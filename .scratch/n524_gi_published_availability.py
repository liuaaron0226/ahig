# -*- coding: utf-8 -*-
"""GI 層之作者稿有沒有免費正式版：**框住擁有者整個選擇的那一句，母體差一筆。**

## 🚨 那一句是什麼

簡報第 90 行：

> **「⚠️ 有一件事我已經查清楚了：這些作者稿**沒有免費的正式版可以拿**。
> 所以選擇不是『作者稿還是正式版』，是『作者稿還是什麼都沒有』。」**

**🚨 那句話框住了整個選擇。** ⚠️ 若其中有一篇拿得到免費正式版，
**選項就多了一個「先去拿那一篇」，而擁有者現在看不到它。**

## 🚨 母體：查過的是校準 60 裡的，而手上有 7 篇

`n490` 自述母體為「**校準 60 之內**的 6 篇非刊出版」，**🚫 不含補抽。**
而 GI 層含補抽之非刊出版為 **3 篇**：

| 尾 8 碼 | 來源 | 版本 | n490 是否涵蓋 |
|---|---|---|---|
| `7b1ae2a1` | 抽出 | acceptedVersion | ✅ 已查（無） |
| `24d22835` | 抽出 | submittedVersion | ✅ 已查（無） |
| **`9b2c5340`** | **補抽** | submittedVersion | **🚨 從未查過** |

**✅ 本檔補查那一筆，判準與 `n490` 相同**：
OpenAlex `locations[]` 中 `is_oa` 且 `version == publishedVersion` 者。

## 🚨 順帶記一個差點造成假結論的識別碼陷阱

`n490` 以 **id 尾段之前 16 碼**（`idFrag`）為鍵；
⚠️ 本室近期產物以 **尾 8 碼** 為鍵。**🚨 兩者直接比對，7 筆會全部判成「未涵蓋」。**
**✅ 已改為同時算出兩種切法再比**——⚠️ 這與第 522 輪那次是同一型。

## 🚫 本檔不做什麼

- **🚫 不改簡報**，🚫 不判「該不該去拿」——⚠️ 那是裁定。
- **🚫 不下載任何全文**：本檔只問「索引上列不列有刊出版之開放位址」。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：OpenAlex 是否列有刊出版之開放位址。
- 🚨 查不到：**列了是否真的取得到**——⚠️ `n490` 原註即如此，本檔沿用。
- 🚨 亦查不到：**索引之外是否另有**——⚠️ OpenAlex 之 `locations` 非窮盡。
"""
import io
import json
import sys
import time
from urllib.parse import quote

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
POOL = 'S5+S6-gi-merged'


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def acquired(ids):
    out = []
    for c in ids:
        mp = (PRIVATE_ROOT / 'fulltext' / F._candidate_directory_name(c)
              / 'manifest.json')
        if mp.exists() and jload(mp).get('status') == 'acquired':
            out.append(c)
    return out


cal = jload(S + 'm1_step2_calibration_set.json')
bf = jload(S + 'm1_step3_backfill.json')
drawn = acquired(cal['draws'][POOL]['candidateIds'])
back = acquired([r['candidateId'] for p in bf['pools'] if p['poolId'] == POOL
                 for r in (p.get('backfilled') or []) if r.get('accepted')])
vers = {r['idTail']: r['version']
        for r in jload(S + 'n523_s56_version_with_backfill.json')['records']}
n490 = {r['idFrag']: r for r in
        jload(S + 'n490_published_version_availability.json')['records']}

print('=== GI 層作者稿之免費正式版（補齊 `n490` 未涵蓋者）===')
print()
print('一、母體與既有涵蓋')
print('   %-10s %-18s %-10s %-18s %s'
      % ('尾8', '前16(idFrag)', '來源', '版本', 'n490'))
targets, covered = [], []
for c in drawn + back:
    tail = c.split(':')[-1]
    v = vers.get(tail[-8:])
    if not v or v == 'publishedVersion':
        continue
    rec = n490.get(tail[:16])
    row = {'idTail': tail[-8:], 'idFrag': tail[:16],
           'origin': 'drawn' if c in drawn else 'backfill', 'version': v,
           'candidateId': c}
    print('   %-10s %-18s %-10s %-18s %s'
          % (tail[-8:], tail[:16], row['origin'], v,
             '✅ 已查' if rec else '🚨 未涵蓋'))
    (covered if rec else targets).append(row)
print('   🚨 本檔須補查 %d 筆' % len(targets))
print('   ⚠️ 識別碼陷阱：`n490` 以**前 16 碼**為鍵、近期產物以**尾 8 碼**為鍵——')
print('      🚨 直接比對會把全部判成「未涵蓋」。✅ 已同時算兩種切法。')
print()

email, _src = G.contact_email()
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出請求，中止。')
queue = {i['candidateId']: i
         for i in jload(PRIVATE_ROOT / RUNSUB / 'screening-queue' / 'queue.json')}


def doi_of(cid):
    ids = (queue.get(cid) or {}).get('identifiers') or {}
    return next((str(x) for x in (ids.get('doi') or []) if x), None)


def published_oa_locations(doi):
    """判準與 `n490` 相同：`locations[]` 中 is_oa 且 version 為 publishedVersion。"""
    url = ('https://api.openalex.org/works/doi:%s?mailto=%s'
           % (quote(doi, safe=''), email))
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, 'HTTP %s %s' % (r['status'], r['error'])
    w = json.loads(r['body'].decode('utf-8'))
    hits = [l for l in (w.get('locations') or [])
            if l.get('is_oa') and l.get('version') == 'publishedVersion']
    return hits, ''


print('二、控制探針——🚨 未過即不報新值')
ctl = covered[0] if covered else None
if ctl is None:
    sys.exit('🚨 無已查者可作對照——🚫 中止。')
cdoi = doi_of(ctl['candidateId'])
hits, err = published_oa_locations(cdoi) if cdoi else (None, '無 DOI')
expect = len(n490[ctl['idFrag']].get('publishedOaLocations') or [])
ok = hits is not None and len(hits) == expect
print('   %s 已查之 %s：n490 記 %d 個／現查 %s %s'
      % ('✅' if ok else '🚨', ctl['idTail'], expect,
         len(hits) if hits is not None else '—', err))
if not ok:
    sys.exit('🚨 現查與既有紀錄不符——⚠️ 判準或來源已變，🚫 不報新值。')
print('   ✅ 判準重現得出，故「查無」讀得成查無。')
print()

print('三、補查')
today = time.strftime('%Y-%m-%d')
rows = []
for t in targets:
    doi = doi_of(t['candidateId'])
    if not doi:
        t.update(publishedOaLocations=None, error='無 DOI')
    else:
        hits, err = published_oa_locations(doi)
        t.update(publishedOaLocations=(None if hits is None else len(hits)),
                 hostTypes=sorted({(h.get('source') or {}).get('type') or '?'
                                   for h in (hits or [])}),
                 error=err, retrievedAt=today)
    rows.append(t)
    n = t.get('publishedOaLocations')
    print('   %-10s %-10s %s'
          % (t['idTail'], t['origin'],
             ('🚨 有 %d 個刊出版開放位址' % n) if n else
             ('✅ 無' if n == 0 else '⚠️ 查不到：' + str(t.get('error')))))
print()

found = [r for r in rows if r.get('publishedOaLocations')]
print('四、🚨 結論')
if found:
    print('   🚨 有 %d 筆列有免費之刊出版位址——⚠️ 簡報那句「沒有免費的正式版可以拿」'
          '對這幾筆不成立。' % len(found))
    print('   🚫 本室不判該不該去拿——⚠️ 那是裁定；✅ 但選項確實多了一個。')
else:
    print('   ✅ 補查之 %d 筆亦無免費刊出版位址。' % len(rows))
    print('   ⚠️ 故簡報那句在 GI 層含補抽之母體下**仍成立**——')
    print('      🚨 而它現在是查過的，🚫 不再是只查過一部分。')

doc = {
    'schemaVersion': 1,
    'documentType': 'gi-published-version-availability',
    'ruling': 'self-initiated: the briefing frames the whole choice on "these '
              'manuscripts have no free published version", and n490 measured '
              'that inside the calibration 60 only, while seven records are in '
              'hand',
    'population': 'non-published acquired records in S5+S6, drawn plus accepted '
                  'backfill',
    'countingUnit': 'record',
    'criterion': 'same as n490: OpenAlex locations[] entries that are OA and carry '
                 'version publishedVersion',
    'alreadyCovered': [r['idTail'] for r in covered],
    'newlyChecked': rows,
    'anyPublishedOaFound': [r['idTail'] for r in found],
    'idKeyTrap': 'n490 keys on the first 16 characters of the id tail while recent '
                 'artefacts key on the last 8. Compared directly, every record '
                 'reads as uncovered. Both slices are computed before comparing.',
    'controlProbe': {'idTail': ctl['idTail'], 'recorded': expect,
                     'refetched': len(hits) if hits is not None else None,
                     'agrees': ok},
    'fetchCounters': G.counters(),
    'coverageStatement': 'Whether a published-version OA location is listed, not '
                         'whether it could be fetched, and not whether it should '
                         'be sought -- n490\'s own caveat, kept.',
    'contentNote': 'Id slices, versions and counts only.',
}
doc['availabilityHash'] = content_hash([r['idTail'] for r in rows])
io.open(S + 'n524_gi_published_availability.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('五、對外請求：%d｜%s'
      % (G.counters()['totalRequests'], G.counters()['perRequestedHost']))
print('✅ 已落盤 → %sn524_gi_published_availability.json' % S)
