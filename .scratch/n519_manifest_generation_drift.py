# -*- coding: utf-8 -*-
"""latest manifest 與其 immutable generation 之落差：**有沒有沒被記成一代的編輯。**

## 🚨 為什麼要問這個

`_write_committed_manifest` 的做法是：**先寫一份 content-addressed generation，
再原子更新 latest**。⚠️ 故正常情況下，**latest 的內容必定等於某一代**。

> **🚨 反過來說：latest 若不等於任何一代，就有人在發佈路徑之外改過它。**
> **⚠️ 而那種編輯沒有留下自己的那一代，等於一次沒有紀錄的改動。**

**⚠️ 本室自己就做過七次**（第 505 輪補六筆授權、第 511 輪補一筆），
當時已載明「只改 latest、不另寫 generation」，並沿用既有五筆的做法。
**🚨 但「我知道我做過七次」與「全體只有那七次」是兩句話**——本檔量後者。

## 🚨 比對必須在**內容**層，不能比位元組

⚠️ generation 以 `_json_bytes`（indent=2＋換行）寫，latest 以 `atomic_write_json` 寫。
**🚨 兩者格式可能不同，故位元組比對會把每一筆都判成落差**——
**那不是發現，是把序列化差異讀成證據。**
**✅ 故以 `content_hash`（正規化後之內容雜湊）比對。**

## 判定

| 判定 | 意思 |
|---|---|
| `matches-a-generation` | ✅ latest 的內容就是某一代 |
| `accounted-licence` | ⚠️ 差異**只落在** `licence`／`licenceProvenance` —— 🚨 即本室已載明的那幾次補填 |
| **`unexplained`** | **🚨 差異落在其他欄位——⚠️ 一次沒有人記錄過的編輯** |

## 🚨 控制探針

**⚠️ 一個「什麼都比對得上」的比較器，會把每一筆都判成 `matches`。**
**✅ 故以合成資料驗兩向**：內容相同須判相同；改一個鍵須判出**那個鍵**。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：latest 是否等於某一代，不等時差在哪些鍵。
- 🚨 查不到：**generation 本身被刪掉的情形**——⚠️ 少了一代，latest 就對不上，
  **🚫 本檔分不出「改過 latest」與「刪過一代」。**
- 🚨 亦查不到：**改動的理由**——⚠️ 本檔只說有沒有、差在哪，🚫 不判斷該不該。
"""
import io
import json
import re
import sys

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require()
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
FULL = PRIVATE_ROOT / 'fulltext'
AD = re.compile(r'-[0-9a-f]{16}$')
LICENCE_KEYS = {'licence', 'licenceProvenance'}


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def diff_keys(a, b):
    """回傳 (頂層差異鍵, artifact 層差異鍵)。🚨 只回鍵名，🚫 不回值。"""
    top = sorted({k for k in set(a) | set(b)
                  if content_hash(a.get(k)) != content_hash(b.get(k))})
    art = set()
    aa, bb = (a.get('artifacts') or []), (b.get('artifacts') or [])
    for x, y in zip(aa, bb):
        art |= {k for k in set(x) | set(y)
                if content_hash(x.get(k)) != content_hash(y.get(k))}
    if len(aa) != len(bb):
        art.add('(artifacts 數量不同)')
    return top, sorted(art)


print('=== latest manifest 與 immutable generation 之落差（🚫 唯讀）===')
print()
print('一、控制探針——🚨 比不出差異的比較器會把每筆都判成相同')
same_a = {'x': 1, 'artifacts': [{'licence': 'cc-by', 'rawFile': 'r'}]}
same_b = json.loads(json.dumps(same_a))
d1 = diff_keys(same_a, same_b)
changed = json.loads(json.dumps(same_a))
changed['artifacts'][0]['rawFile'] = 'other'
d2 = diff_keys(same_a, changed)
ok1 = d1 == ([], [])
ok2 = d2[1] == ['rawFile']
print('   %s 內容相同 → 無差異（實得 %s）' % ('✅' if ok1 else '🚨', d1))
print('   %s 改一個鍵 → 指出該鍵（實得 %s）' % ('✅' if ok2 else '🚨', d2[1]))
if not (ok1 and ok2):
    sys.exit('🚨 控制探針未過——🚫 不報落差結果。')
print('   ✅ 兩向皆如預期。')
print()

rows = []
for d in sorted(p for p in FULL.iterdir() if p.is_dir() and AD.search(p.name)):
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    latest = jload(mp)
    if latest.get('status') != 'acquired':
        continue
    gens = []
    gdir = d / 'manifests'
    if gdir.is_dir():
        for g in sorted(gdir.iterdir()):
            try:
                gens.append((g.name, jload(g)))
            except Exception:
                pass
    lh = content_hash(latest)
    if any(content_hash(g) == lh for _, g in gens):
        rows.append({'dir': d.name[:8], 'generations': len(gens),
                     'verdict': 'matches-a-generation'})
        continue
    # 🚨 找差異最小的一代作為對照——⚠️ 不是「最新」，因為檔名是雜湊，排序無意義。
    best, best_diff = None, None
    for name, g in gens:
        top, art = diff_keys(latest, g)
        n = len(top) + len(art)
        if best is None or n < best:
            best, best_diff, best_name = n, (top, art), name
    if best_diff is None:
        rows.append({'dir': d.name[:8], 'generations': 0,
                     'verdict': 'no-generation'})
        continue
    top, art = best_diff
    # 🚨 初版把 `only_lic` 寫成「頂層只能是空或 `artifacts`」，
    # ⚠️ 於是那五筆（授權同時寫在頂層與 artifact 層者）被判成 `unexplained`。
    # 🚨 那不是發現，是我的分類條件太窄——差異其實全部落在授權欄。
    # ✅ 判準改為：扣掉容器鍵 `artifacts` 之後，兩層之差異鍵皆須在授權欄之內。
    differing = (set(top) - {'artifacts'}) | set(art)
    only_lic = bool(differing) and differing <= LICENCE_KEYS
    rows.append({'dir': d.name[:8], 'generations': len(gens),
                 'closestGeneration': best_name,
                 'topLevelKeys': top, 'artifactKeys': art,
                 'verdict': 'accounted-licence' if only_lic else 'unexplained'})

from collections import Counter  # noqa: E402
c = Counter(r['verdict'] for r in rows)
print('二、在手 %d 份' % len(rows))
for k in ('matches-a-generation', 'accounted-licence', 'unexplained',
          'no-generation'):
    if c.get(k):
        mark = {'matches-a-generation': '✅', 'accounted-licence': '⚠️',
                'unexplained': '🚨', 'no-generation': '🚨'}[k]
        print('   %s %-24s %3d' % (mark, k, c[k]))
print()
un = [r for r in rows if r['verdict'] == 'unexplained']
if un:
    print('三、🚨 沒有紀錄的編輯（差異不只授權欄）')
    for r in un[:12]:
        print('   🚨 %-10s 代數 %d｜頂層差異 %s｜artifact 差異 %s'
              % (r['dir'], r['generations'],
                 '／'.join(r['topLevelKeys'])[:40] or '無',
                 '／'.join(r['artifactKeys'])[:44] or '無'))
    if len(un) > 12:
        print('   …另 %d 筆，見產物' % (len(un) - 12))
else:
    print('三、✅ 沒有無法交代的編輯——⚠️ 差異者皆只落在授權欄。')
lic = [r for r in rows if r['verdict'] == 'accounted-licence']
print('   ⚠️ 授權補填造成之落差：%d 筆（第 505 輪六筆、第 511 輪一筆，'
      '併既有五筆之同一做法）' % len(lic))
print('   🚨 那幾筆之 latest 沒有對應的 generation——'
      '⚠️ 是刻意的（n+163 二裁定只寫最新一代），🚫 但它確實是一種落差，故照實列。')

doc = {
    'schemaVersion': 1,
    'documentType': 'manifest-generation-drift',
    'ruling': 'self-initiated: publication writes a content-addressed generation '
              'and then updates latest, so latest should equal some generation. '
              'Where it does not, something edited it outside that path -- and '
              '"I know I did it seven times" is not the same as "there are only '
              'seven".',
    'population': 'acquired manifests under the private root',
    'countingUnit': 'record',
    'criterion': 'content_hash of latest against content_hash of each generation; '
                 'differences reported as key names against the closest one',
    'whyContentNotBytes': 'Generations are written with _json_bytes and latest '
                          'with atomic_write_json, so a byte comparison would flag '
                          'every record on formatting alone -- reading a '
                          'serialisation difference as evidence.',
    'controlProbes': {'identicalGivesNoDiff': ok1, 'changedKeyIsNamed': ok2},
    'counts': dict(c),
    'records': rows,
    'accountedNote': 'Licence-only differences are the backfills of rounds 505 and '
                     '511, which n+163(2) ruled should touch only the latest '
                     'manifest. Deliberate, but still a divergence, so it is '
                     'listed rather than hidden.',
    'coverageStatement': 'Cannot distinguish an edited latest from a deleted '
                         'generation -- both look like latest matching nothing. '
                         'Says whether and where, never whether it was right.',
    'contentNote': 'Directory prefixes, generation file names and key names only.',
}
doc['driftHash'] = content_hash(dict(c))
io.open(S + 'n519_manifest_generation_drift.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn519_manifest_generation_drift.json' % S)
sys.exit(1 if un else 0)
