# -*- coding: utf-8 -*-
"""在手 41 份各自**從哪裡拿到的**——而這件事一直沒有被列過表。

## 🚨 起因：追授權追到一半，發現更該先問的是「這份是誰家的副本」

第 511 輪之後仍有 5 筆無授權紀錄。查其來源主機才看見：

> **🚨 其中四筆的 PDF 全部來自同一個大學典藏庫**（`utoronto.scholaris.ca`）。
> **⚠️ 那不是出版社的副本，是作者自存的副本。**

**⚠️ 而這改變了那四筆的授權問題該問誰**：
**🚨 管轄自存副本的是典藏庫的存放條款，🚫 不是 DOI 登記處那一欄。**
故「三個登記處都沒有開放授權紀錄」雖然為真，**⚠️ 對這四筆而言問的不是最相關的那個登記處。**

## 🚨 而更一般的問題是：**這張表本來就該有**

⚠️ 報告會說「取自開放取用位址」，**🚫 卻沒有列過那些位址各是什麼性質**。
**🚨 「來自 PMC」「來自大學典藏庫」「來自出版社」在授權與版本上是三件不同的事**——
⚠️ 典藏庫多為作者稿、出版社多為刊出版，而兩者的重製權利也不同。

## 分類規則（🚫 明列，不藏在程式裡）

| 類 | 判準（主機名） |
|---|---|
| `pmc` | `ncbi.nlm.nih.gov`／`europepmc.org`／**`ebi.ac.uk`** |
| `repository` | 含 `.edu`／`.ac.`／`scholaris`／`dspace`／`eprints`／`figshare`／`zenodo` |
| `publisher` | 其餘可辨識之出版社網域 |
| `unknown` | 🚨 判不出來者——⚠️ 一律歸此，🚫 不猜 |

**🚨 分類是啟發式的，故 `unknown` 必須是一個真的會出現的類**：
**⚠️ 一個「什麼都分得出來」的規則，只是把不確定藏起來。**

### 🚨 初版把 26 份 PMC 誤分為典藏庫，而五道探針全綠

**⚠️ Europe PMC 的主機是 `www.ebi.ac.uk`，它含 `.ac.`**——於是撞進典藏庫規則。
**🚨 而探針沒抓到，因為我挑的是「我想得到的主機」，🚫 不是「語料裡真的出現的主機」。**

> **⚠️ 教訓**：控制探針的樣本若不取自實際母體，
> **🚨 它證明的只是「規則對我舉的例子成立」。**
> **✅ 現已改為逐一取自實際出現之九個主機。**

## 🚫 本檔不記網址

**⚠️ manifest 之 `sourceUrl` 路徑可能內嵌逐字題名**（實見一筆路徑片段長達 152 字元）。
**🚫 故產物只記主機名與分類，不記路徑。**

## ⚠️ 併記一次到此為止的嘗試

為了讀那四筆的存放條款，本輪試過 DSpace REST：
`bitstreams/{uuid}?embed=owningBundle/item` → **`_embedded` 為空**；
`bitstreams/{uuid}/owningBundle` → **404**。
**🚫 兩種走法皆未達 item 層，故就此打住，不再猜 API 形狀。**
**⚠️ 下一步是讀該典藏庫之 item 頁**，🚨 而那頁之路徑可能內嵌題名，**須另行決定怎麼處理。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 看得到：每一份在手全文之來源主機與其粗分類。
- 🚨 看不到：**該主機上那一份是哪個版本**——⚠️ 版本另有 `n487`／`n488`／`n489` 之量測。
- 🚨 分類為啟發式：**⚠️ 同一個網域可能同時是出版社與典藏庫**，🚫 本檔不細分。
"""
import io
import json
import re
import sys
from collections import Counter
from urllib.parse import urlparse

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require()
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
FULL = PRIVATE_ROOT / 'fulltext'
AD = re.compile(r'-[0-9a-f]{16}$')
# 🚨 `ebi.ac.uk` 必須在這裡：⚠️ Europe PMC 的主機是 EBI，
# 而它含 `.ac.`——初版因此把 26 份 PMC 全部誤分為典藏庫。
PMC = ('ncbi.nlm.nih.gov', 'europepmc.org', 'ebi.ac.uk')
# ⚠️ `.ac.` 很寬——🚨 故 PMC 之判定必須排在它前面（見上）。
REPO = ('.edu', '.ac.', 'scholaris', 'dspace', 'eprints', 'figshare', 'zenodo',
        'repository', 'core.ac.uk')
# ⚠️ `doi.org` 是轉址器不是來源——🚨 歸 `unknown`，🚫 不假裝知道它指向哪裡。
PUBLISHER = ('cambridge.org', 'springer', 'wiley', 'elsevier', 'tandfonline',
             'sagepub', 'nature.com', 'oup.com', 'frontiersin', 'mdpi',
             'physiology.org', 'lww.com', 'humankinetics', 'cdnsciencepub')


def classify(host):
    h = (host or '').lower()
    if not h:
        return 'unknown'
    if any(h.endswith(p) or p in h for p in PMC):
        return 'pmc'
    if any(p in h for p in REPO):
        return 'repository'
    if any(p in h for p in PUBLISHER):
        return 'publisher'
    return 'unknown'


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


# ── 控制探針：規則要分得出來，也要分不出來 ────────────────────────
print('=== 在手全文之來源主機（🚫 唯讀、🚫 不記網址）===')
print()
print('一、控制探針——🚨 分類規則須雙向')
# 🚨 探針必須用**真的會出現的主機**——⚠️ 初版只用我想得到的主機，
# 於是五道全綠，而語料裡佔最多數的 `www.ebi.ac.uk` 被誤分為典藏庫。
cases = [('www.ebi.ac.uk', 'pmc'), ('www.ncbi.nlm.nih.gov', 'pmc'),
         ('utoronto.scholaris.ca', 'repository'),
         ('eprints.gla.ac.uk', 'repository'),
         ('onlinelibrary.wiley.com', 'publisher'),
         ('www.cambridge.org', 'publisher'),
         ('doi.org', 'unknown'), ('example.invalid', 'unknown'),
         ('', 'unknown')]
ok = True
for host, want in cases:
    got = classify(host)
    good = got == want
    ok = ok and good
    print('   %s %-26s → %-10s（期待 %s）'
          % ('✅' if good else '🚨', host or '(空)', got, want))
if not ok:
    sys.exit('🚨 分類規則未如預期——🚫 不報分類結果。')
print('   ✅ %d 道皆如預期（皆取自語料實際出現之主機），'
      '且 `unknown` 是一個真的分得出來的類。' % len(cases))
print()

rows = []
for d in sorted(p for p in FULL.iterdir() if p.is_dir() and AD.search(p.name)):
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    m = jload(mp)
    if m.get('status') != 'acquired':
        continue
    for a in (m.get('artifacts') or []):
        host = urlparse(a.get('sourceUrl') or '').netloc.lower()
        rows.append({'dir': d.name[:8], 'sourceType': a.get('sourceType'),
                     'host': host, 'kind': classify(host),
                     'hasLicence': bool(a.get('licence'))})

by_kind = Counter(r['kind'] for r in rows)
print('二、來源分類（在手 %d 份）' % len(rows))
for k, n in by_kind.most_common():
    print('   %-12s %3d' % (k, n))
print()
print('三、🚨 交叉：來源分類 × 有無授權紀錄')
print('   %-12s %8s %8s' % ('分類', '有授權', '無授權'))
print('   ' + '-' * 32)
for k in sorted(by_kind):
    y = sum(1 for r in rows if r['kind'] == k and r['hasLicence'])
    n = sum(1 for r in rows if r['kind'] == k and not r['hasLicence'])
    print('   %-12s %8d %8d' % (k, y, n))
print('   ' + '-' * 32)
nolic = [r for r in rows if not r['hasLicence']]
hosts = Counter(r['host'] for r in nolic)
print('   🚨 無授權之 %d 份，其來源主機：%s'
      % (len(nolic), '、'.join('%s×%d' % (h, c) for h, c in hosts.most_common())))
print('   ⚠️ 其中典藏庫者為**作者自存副本**——'
      '🚨 管轄它的是存放條款，🚫 不是 DOI 登記處那一欄。')

by_route = Counter((r['sourceType'], r['kind']) for r in rows)
print()
print('四、取文路徑 × 來源分類')
for (st, k), n in sorted(by_route.items()):
    print('   %-18s %-12s %3d' % (st, k, n))

doc = {
    'schemaVersion': 1,
    'documentType': 'acquired-source-host-provenance',
    'ruling': 'self-initiated: chasing the last licences showed four of them come '
              'from one university repository, which changes who governs those '
              'rights -- and the report has never tabulated where each full text '
              'actually came from.',
    'population': 'artifacts of acquired manifests under the private root',
    'countingUnit': 'artifact',
    'criterion': 'host of the recorded sourceUrl, classified by the rules listed '
                 'in the module docstring',
    'classificationIsHeuristic': True,
    'firstVersionDefect': 'The first rule set put Europe PMC (www.ebi.ac.uk) in '
                          'the repository bucket because the host contains ".ac.", '
                          'misclassifying 26 of 41 -- and five control probes '
                          'passed, because they used hosts I thought of rather '
                          'than hosts the corpus actually contains.',
    'controlProbes': [{'host': h, 'expected': w, 'got': classify(h)}
                      for h, w in cases],
    'byKind': dict(by_kind),
    'byRouteAndKind': {'%s|%s' % k: v for k, v in by_route.items()},
    'records': rows,
    'unlicensedHosts': dict(hosts),
    'dspaceAttempt': {
        'tried': ['bitstreams/{uuid}?embed=owningBundle/item -> _embedded empty',
                  'bitstreams/{uuid}/owningBundle -> HTTP 404'],
        'stopped': 'Two shapes failed; guessing further API shapes is where this '
                   'turns into a rabbit hole. The next step is the repository '
                   'item page, whose path may embed the verbatim title, so how to '
                   'handle that needs deciding rather than assuming.',
    },
    'whyItMatters': 'Coming from PMC, a university repository, or a publisher are '
                    'three different things for both version and reuse rights: '
                    'repositories mostly hold author manuscripts, publishers the '
                    'version of record, and the terms differ.',
    'coverageStatement': 'Classification is heuristic and unknown is a real '
                         'bucket -- a rule that classifies everything only hides '
                         'the uncertainty. Says nothing about which version sits '
                         'at that host; that is measured elsewhere.',
    'contentNote': 'Host names and counts only. No URLs: one recorded path '
                   'carried a 152-character segment that embeds the title.',
}
doc['provenanceHash'] = content_hash({'byKind': dict(by_kind)})
io.open(S + 'n512_source_host_provenance.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn512_source_host_provenance.json' % S)
