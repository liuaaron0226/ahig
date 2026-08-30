# -*- coding: utf-8 -*-
"""S5＋S6 含補抽之 7 篇版本分布（n+177 交辦⑤）：**建議站不站得住，繫於這個數。**

## 🚨 這一格為什麼直接影響擁有者的決定

簡報第三節建議「就用手上的」，理由是
「(b) 要動用的資源跟**它可能改善的那兩三篇**不成比例」。

> **⚠️ 那「兩三篇」是抽出的 3 篇裡的 2 篇作者稿。**
> **🚨 而手上實際有 7 篇——多出來的 4 篇裡有幾篇是作者稿，從來沒有量過。**
> **⚠️ 若那 4 篇多為作者稿，「能改善的沒幾篇」這個理由就不成立。**

**🚫 本檔不改建議，✅ 只把那個數量出來。**

## 🚨 這個 7 是兩批合成的，故合成規則要先寫明

| 子母體 | 幾篇 | 版本從哪來 |
|---|---|---|
| 抽出且取得 | **3** | ✅ `n489` 已量（校準 60 母體之內） |
| **補抽且取得** | **4** | **🚨 從未量過——本檔量的就是這 4 篇** |

**✅ 兩批用同一個來源與同一個判準**（OpenAlex `best_oa_location.version`，
與 n+486–488 相同），**🚨 故合起來才是合法的合成，🚫 不是把兩種量測相加。**

**⚠️ 併記一項時間差**：`n489` 那 3 篇是**當時**量的，本檔這 4 篇是**現在**量的。
**🚨 第三方書目資料會變，故合成值須併記兩次量測之時點。**

## 🚨 控制探針

**⚠️ 查詢路徑一壞，回來全是 `None`——而那與「OpenAlex 沒記版本」長得一模一樣。**
**✅ 故先重查一筆 `n489` 已量者，回傳須與其記錄相同；不同即中止，🚫 不報任何新值。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 量得到：該 7 篇在 OpenAlex 上登記之版本。
- 🚨 量不到：**版本標記是否正確**——⚠️ 第三方書目資料，🚫 非本室查證。
- 🚨 亦量不到：**作者稿與刊出版的數據差異有多大**——⚠️ 那要逐篇讀，
  **🚫 而那是萃取期的事。**
- ⚠️ 本檔**不判斷建議該不該改**——🚨 那是裁定，🚫 不是檢索。
"""
import io
import json
import sys
import time
from collections import Counter
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


def frag(cid):
    return cid.split(':')[-1][:16]


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

print('=== S5＋S6 含補抽之版本分布（n+177 交辦⑤）===')
print('   抽出且取得 %d 篇｜補抽且取得 %d 篇｜合計 %d 篇'
      % (len(drawn), len(back), len(drawn) + len(back)))
print()

n489 = jload(S + 'n489_calibration_versions.json')
known = {r['idFrag']: r['version'] for r in n489['records']}
have = {c: known.get(frag(c)) for c in drawn}
missing = [c for c in drawn + back if not known.get(frag(c))]
print('一、既有量測（`n489`，母體為校準 60）')
for c in drawn:
    print('   %s → %s' % (c[-8:], known.get(frag(c)) or '🚨 未量'))
print('   🚨 待量 %d 篇（補抽者 %d ＋ 抽出但未量者 %d）'
      % (len(missing), len([c for c in back if c in missing]),
         len([c for c in drawn if c in missing])))
print()

email, esrc = G.contact_email()
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出請求，中止。')
queue = {i['candidateId']: i
         for i in jload(PRIVATE_ROOT / RUNSUB / 'screening-queue' / 'queue.json')}


def doi_of(cid):
    ids = (queue.get(cid) or {}).get('identifiers') or {}
    return next((str(x) for x in (ids.get('doi') or []) if x), None)


def version_of(doi):
    url = ('https://api.openalex.org/works/doi:%s?mailto=%s'
           % (quote(doi, safe=''), email))
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, 'HTTP %s %s' % (r['status'], r['error'])
    w = json.loads(r['body'].decode('utf-8'))
    return (w.get('best_oa_location') or {}).get('version'), ''


print('二、控制探針——🚨 未過即不報任何新值')
ctl = next((r for r in n489['records'] if r.get('version')), None)
ctl_cid = next((c for c in queue if frag(c) == ctl['idFrag']), None) if ctl else None
ctl_doi = doi_of(ctl_cid) if ctl_cid else None
if not ctl_doi:
    sys.exit('🚨 找不到可用之對照筆——🚫 中止。')
got, err = version_of(ctl_doi)
ok = (got == ctl['version'])
print('   %s 已量之 %s：n489 記 %s／現查 %s %s'
      % ('✅' if ok else '🚨', ctl['idFrag'][:8], ctl['version'], got, err))
if not ok:
    sys.exit('🚨 現查與既有紀錄不符——⚠️ 查詢路徑或來源已變，🚫 不報新值。')
print('   ✅ 查詢路徑重現既有紀錄，故新查之值可讀。')
print()

print('三、逐篇（🚨 補抽者為本輪新量）')
today = time.strftime('%Y-%m-%d')
rows = []
for c in drawn + back:
    origin = 'drawn' if c in drawn else 'backfill'
    v, src, err = known.get(frag(c)), 'n489（%s）' % n489.get('retrievedAt', '當時'), ''
    if not v:
        doi = doi_of(c)
        if not doi:
            v, src, err = None, '—', '無 DOI'
        else:
            v, err = version_of(doi)
            src = 'OpenAlex（%s）' % today
    rows.append({'idTail': c[-8:], 'origin': origin, 'version': v,
                 'measuredBy': src, 'error': err})
    print('   %-10s %-9s %-18s %s%s'
          % (c[-8:], origin, v or '🚨 未記載', src, ('｜' + err) if err else ''))
print()

dist = Counter(r['version'] or 'unknown' for r in rows)
nonpub = sum(n for k, n in dist.items() if k != 'publishedVersion')
print('四、✅ 含補抽之 7 篇分布')
for k, n in sorted(dist.items()):
    print('   %-20s %d' % (k, n))
print('   🚨 非刊出版合計 %d／%d' % (nonpub, len(rows)))
print()
print('五、⚠️ 這個數對簡報建議的意思（🚫 本室不判該不該改）')
d3 = Counter(r['version'] or 'unknown' for r in rows if r['origin'] == 'drawn')
b4 = Counter(r['version'] or 'unknown' for r in rows if r['origin'] == 'backfill')
print('   抽出 3 篇：%s' % dict(d3))
print('   補抽 4 篇：%s' % dict(b4))
print('   ⚠️ 簡報所據之「兩三篇」是抽出那 3 篇裡的非刊出版數；')
print('   🚨 而含補抽之非刊出版為 %d 篇——⚠️ 建議之前提是否仍成立，屬裁定。' % nonpub)

doc = {
    'schemaVersion': 1,
    'documentType': 's56-version-with-backfill',
    'ruling': 'n+177(5): the briefing rests recommendation (a) on how few records '
              'a paid route could improve, and that figure was measured over the '
              'drawn three while seven are in hand',
    'population': 'S5+S6 acquired records, drawn plus accepted backfill',
    'countingUnit': 'record',
    'criterion': 'OpenAlex best_oa_location.version, the same source and criterion '
                 'as rounds 486-488 and n489',
    'compositionNote': 'Three versions come from n489 (measured then) and four are '
                       'measured now. Same source and criterion, so composing them '
                       'is legitimate -- but third-party metadata moves, so both '
                       'measurement times are recorded.',
    'controlProbe': {'idFrag': ctl['idFrag'], 'recorded': ctl['version'],
                     'refetched': got, 'agrees': ok,
                     'why': 'A broken lookup returns None for everything, which '
                            'is indistinguishable from no version on record.'},
    'records': rows,
    'distribution': dict(dist),
    'nonPublished': nonpub,
    'drawnDistribution': dict(d3),
    'backfillDistribution': dict(b4),
    'whatThisDoesNotSay': 'Whether the recommendation still holds. That is a '
                          'ruling. This supplies the figure it was resting on.',
    'coverageStatement': 'Says what OpenAlex records, not whether the label is '
                         'right, and nothing about how far an author manuscript '
                         'differs from the published version -- that needs '
                         'reading, at the extraction stage.',
    'contentNote': 'Id tails, origins and version labels only.',
}
doc['versionHash'] = content_hash(dict(dist))
io.open(S + 'n523_s56_version_with_backfill.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('六、對外請求（閘門產出）：%d｜%s'
      % (G.counters()['totalRequests'], G.counters()['perRequestedHost']))
print('✅ 已落盤 → %sn523_s56_version_with_backfill.json' % S)
