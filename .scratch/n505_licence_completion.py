# -*- coding: utf-8 -*-
"""授權欄之補齊：41 份在手全文中，**12 份至今沒有任何授權紀錄**。

## 🚨 缺口有多大，以及為什麼它要緊

```
europe-pmc-jats   有 24 ／ 無  2      ← 自 JATS 之 <license> 自動擷取
grobid-tei        有  5 ／ 無 10      ← 無可自動擷取之來源，須外部查
合計              有 29 ／ 無 12
```

**⚠️ 一份取得了全文卻沒有授權紀錄的文獻，在交付時是一個說不出口的洞**：
🚨 引用多少、能不能重製、能不能附進附錄，全繫於那一格。
**⚠️ 而「開放取用」🚫 不等於「可任意重製」**——這正是既有五筆之 provenance 註記所寫的話。

## ✅ 程序照抄既有五筆，🚫 不另立

第 485 輪之後已有五筆依 n+138（三）填入，其形狀就是規範：

```json
"licence": "cc-by",
"licenceProvenance": {"source": "OpenAlex best_oa_location.license",
                      "retrievedAt": "YYYY-MM-DD", "note": "...第三方書目資料..."}
```

**🚨 本檔沿用同一來源、同一形狀、同一註記，🚫 不發明新欄位。**

## 🚨 一件我上一輪弄錯的事，順帶更正

`n500` 判斷 `LIC_FILLED` 用的是**授權欄之形狀**（字串 vs `{href,text}` 物件），
並自陳「此判準脆弱，因為沒有『由誰填』的欄位」。

> **⚠️ 有。就叫 `licenceProvenance`，五筆全都有，且自動擷取者一個也沒有。**
> **🚨 我當時沒去看欄位清單就下了那個結論，然後把自己的沒看，寫成了資料的缺陷。**

**✅ 判準已改為「有無 `licenceProvenance`」——明示、且與形狀無關。**

## 🚨 控制探針：拿已填的五筆回頭查

**⚠️ 若查詢路徑壞了（欄位名改了、DOI 對不上），回來的會是一片 `None`，
而那與「OpenAlex 真的沒記載」長得一模一樣。**

**✅ 故先查已填五筆之一，其回傳須與 manifest 所載相同**；
**🚨 不同即中止，🚫 不報任何新值。**

## 🚫 預設不寫入 manifest；寫入前先備份

**⚠️ 私有根不在版控內——🚨 寫壞了沒有 `git checkout` 可以救。**
**✅ 故預設只落盤到 `.scratch` 並印出逐筆計畫；`--apply` 才真的寫入，
且寫入前先把原檔複製到私有根之 `fulltext-manifest-backups/n505/`。**

**🚫 備份不放 `.scratch`**——⚠️ manifest 內之 `sourceUrl`／`finalUrl`
**路徑會內嵌逐字題名**，🚨 放進版控就是外洩（n+48 五道抓不到該型）。

**🚫 只加欄位，不動任何既有值**；已有授權者一律跳過，不覆寫。

### ⚠️ 一項已知後果，須併記

**🚨 本檔改的是 latest `manifest.json`，🚫 不另寫 immutable generation。**
⚠️ 故 latest 會多一個 generation 沒有的欄位。
**✅ 既有五筆就是這樣寫的**（實查其 generations 皆無 `licence`），
**🚨 本檔沿用同一作法以免兩種寫法並存；⚠️ 是否改為一併寫 generation 屬裁定。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：OpenAlex 對該 DOI 所記之 `best_oa_location.license`。
- 🚨 查不到：**該授權是否正確**——⚠️ 這是第三方書目資料，
  **🚫 不是本室的查證，也不是出版社的聲明。**
- 🚨 亦查不到：**OpenAlex 未記載者之真實授權**——⚠️ 一律記為未記載，
  **🚫 不以「開放取用」推定為可重製。**
"""
import io
import json
import os
import re
import sys
import time
from pathlib import Path

sys.path.insert(0, 'ahig')
sys.path.insert(0, '.scratch')
# 🚨 n+162（九之二）：來源不在就拒絕產出，🚫 不得寫入任何值。
# ⚠️ 原本這裡是 `os.environ.setdefault(...)`——那行在別台機器上會
#    「成功」地把根設成一個不存在的路徑，🚨 於是本支量到零並落盤，
#    而「量到零」與「量不到」在檔案裡長得一模一樣。
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require('search-runs/b11-exogenous-cho-endurance/b11-full-run')
import fetch_guard as G  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
PRIV = Path(os.environ['AHIG_PRIVATE_ROOT'])
FULL = PRIV / 'fulltext'
RUN = PRIV / 'search-runs' / 'b11-exogenous-cho-endurance' / 'b11-full-run'
AD = re.compile(r'-[0-9a-f]{16}$')
APPLY = '--apply' in sys.argv
NOTE = ('Third-party bibliographic metadata, recorded as such. Not a '
        'verification by this room, and open access does not imply a right to '
        'redistribute.')


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def acquired():
    for d in sorted(p for p in FULL.iterdir() if p.is_dir() and AD.search(p.name)):
        mp = d / 'manifest.json'
        if not mp.exists():
            continue
        m = jload(mp)
        if m.get('status') == 'acquired':
            yield d, m


def openalex_licence(doi, email):
    url = ('https://api.openalex.org/works/doi:%s?mailto=%s'
           % (doi, email))
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, 'HTTP %s %s' % (r['status'], r['error'])
    w = json.loads(r['body'].decode('utf-8'))
    return (w.get('best_oa_location') or {}).get('license'), ''


email, src = G.contact_email()
print('=== 授權欄補齊（%s）===' % ('✅ --apply 寫入模式' if APPLY else '🚫 預設：只計畫不寫入'))
print('   聯絡信箱 %s（來源 %s）' % (G.masked(email), src))
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出任何請求，中止。')

queue = {i['candidateId']: i for i in jload(RUN / 'screening-queue' / 'queue.json')}
missing, filled = [], []
for d, m in acquired():
    for idx, a in enumerate(m.get('artifacts') or []):
        rec = {'dir': d.name, 'idx': idx, 'sourceType': a.get('sourceType'),
               'candidateId': m.get('candidateId')}
        if a.get('licence'):
            rec['licence'] = a['licence']
            rec['hasProvenance'] = 'licenceProvenance' in a
            filled.append(rec)
        else:
            missing.append(rec)
print('   在手 artifact %d：有授權 %d（其中具 provenance %d）／無授權 %d'
      % (len(filled) + len(missing), len(filled),
         sum(1 for r in filled if r['hasProvenance']), len(missing)))
print()

# ── 控制探針：回頭查一筆已填者 ────────────────────────────────────
print('一、控制探針——🚨 未過即拒絕報告任何新值')
ctl_rec = next((r for r in filled if r['hasProvenance']), None)
if ctl_rec is None:
    sys.exit('🚨 找不到任何具 provenance 之已填紀錄可作對照——🚫 中止。')
ctl_doi = None
ids = (queue.get(ctl_rec['candidateId']) or {}).get('identifiers') or {}
ctl_doi = next((str(x) for x in (ids.get('doi') or []) if x), None)
if not ctl_doi:
    sys.exit('🚨 對照筆無 DOI——🚫 中止。')
got, err = openalex_licence(ctl_doi, email)
same = (got == ctl_rec['licence'])
print('   %s 已填之 %s：manifest 記 %r／現查 %r %s'
      % ('✅' if same else '🚨', ctl_rec['dir'][:8], ctl_rec['licence'], got,
         err))
if not same:
    sys.exit('🚨 現查與既有紀錄不符——⚠️ 查詢路徑或來源已變，🚫 不據以補任何一筆。')
print('   ✅ 查詢路徑重現了既有紀錄，故其回傳之 `None` 才能被讀成「未記載」。')
print()

# ── 逐筆查 ───────────────────────────────────────────────────────
print('二、無授權之 %d 筆' % len(missing))
print('   %-10s %-18s %-28s %s' % ('id', '路徑', 'DOI', '現查授權'))
print('   ' + '-' * 84)
plan = []
today = time.strftime('%Y-%m-%d')
for r in missing:
    ids = (queue.get(r['candidateId']) or {}).get('identifiers') or {}
    doi = next((str(x) for x in (ids.get('doi') or []) if x), None)
    if not doi:
        r.update(licence=None, why='無 DOI，🚫 無從查')
        plan.append(r)
        print('   %-10s %-18s %-28s 🚨 無 DOI' % (r['dir'][:8], r['sourceType'], '—'))
        continue
    lic, err = openalex_licence(doi, email)
    r.update(doi=doi, licence=lic, error=err)
    plan.append(r)
    print('   %-10s %-18s %-28s %s'
          % (r['dir'][:8], r['sourceType'], doi[:28],
             ('✅ ' + lic) if lic else ('🚨 ' + (err or 'OpenAlex 未記載'))))
print('   ' + '-' * 84)
got_n = sum(1 for r in plan if r.get('licence'))
print('   ✅ 查得授權 %d／%d；🚨 其餘記為「未記載」，🚫 不以開放取用推定可重製。'
      % (got_n, len(plan)))

# ── 寫入（預設不做） ─────────────────────────────────────────────
print()
written = []
if not APPLY:
    print('三、🚫 未寫入（預設）——⚠️ 私有根不在版控內，寫壞了沒有 git 可以救。')
    print('   ✅ 計畫：對上列 %d 筆之 artifact 加入 `licence` 與 `licenceProvenance`，'
          % got_n)
    print('      🚫 只加欄位，不動任何既有值。確認後以 `--apply` 執行。')
else:
    print('三、✅ 寫入（先備份）')
    backup = PRIV / 'fulltext-manifest-backups' / 'n505'
    backup.mkdir(parents=True, exist_ok=True)
    print('   ⚠️ 備份目錄：%s（🚫 不在版控內，因 manifest 之網址內嵌題名）'
          % backup)
    for r in plan:
        if not r.get('licence'):
            continue
        mp = FULL / r['dir'] / 'manifest.json'
        m = jload(mp)
        a = m['artifacts'][r['idx']]
        if a.get('licence'):
            print('   ⏸ %s 已有授權，🚫 跳過（不覆寫）' % r['dir'][:8])
            continue
        # 🚨 先備份再改——⚠️ 私有根沒有 git 可以回頭。
        io.open(backup / (r['dir'] + '.json'), 'w', encoding='utf-8').write(
            io.open(mp, encoding='utf-8').read())
        a['licence'] = r['licence']
        a['licenceProvenance'] = {'source': 'OpenAlex best_oa_location.license',
                                  'retrievedAt': today, 'note': NOTE}
        io.open(mp, 'w', encoding='utf-8').write(
            json.dumps(m, ensure_ascii=False, indent=2) + '\n')
        written.append(r['dir'][:8])
        print('   ✅ %s ← %s' % (r['dir'][:8], r['licence']))
    print('   ✅ 已寫入 %d 筆。' % len(written))

c = G.counters()
print()
print('四、對外請求（閘門產出）：總數 %d｜逐主機 %s｜封鎖 %s'
      % (c['totalRequests'], c['perRequestedHost'], c['blockedHosts'] or '無'))

doc = {
    'schemaVersion': 1,
    'documentType': 'licence-completion',
    'ruling': 'n+138(3) established the procedure and a first batch of five was '
              'filled under it; this extends the same procedure to the rest. '
              'n486 raised the gap in round 485 and never got a ruling.',
    'population': 'artifacts of acquired manifests under the private root with no '
                  'licence recorded',
    'countingUnit': 'artifact',
    'criterion': 'OpenAlex best_oa_location.license for the artifact\'s DOI, '
                 'recorded with source and retrieval date in the same shape as '
                 'the existing five',
    'controlProbe': {'dir': ctl_rec['dir'][:8], 'recorded': ctl_rec['licence'],
                     'refetched': got, 'agrees': same,
                     'why': 'A broken query path returns None for everything, '
                            'which is indistinguishable from OpenAlex simply not '
                            'recording a licence. Reproducing an existing record '
                            'is what makes a None readable as "not recorded".'},
    'acquiredArtifacts': len(filled) + len(missing),
    'withLicence': len(filled),
    'withProvenance': sum(1 for r in filled if r['hasProvenance']),
    'missing': len(missing),
    'resolved': got_n,
    'plan': [{'dir': r['dir'][:8], 'sourceType': r['sourceType'],
              'licence': r.get('licence'), 'why': r.get('why', '')}
             for r in plan],
    'applied': bool(APPLY),
    'written': written,
    'backupDirectory': str(PRIV / 'fulltext-manifest-backups' / 'n505'),
    'backupNote': 'Outside version control on purpose: manifest URLs embed '
                  'verbatim titles, so a backup in .scratch would be a leak.',
    'generationNote': 'Only the latest manifest.json is edited; no new immutable '
                      'generation is written, so latest carries a field the '
                      'generations lack. The existing five were written the same '
                      'way -- their generations carry no licence either -- and '
                      'this follows that rather than introducing a second '
                      'practice. Whether generations should also be written is a '
                      'ruling.',
    'licFilledCriterionCorrection': 'n500 keyed LIC_FILLED on the shape of the '
                                    'licence field and called that fragile for '
                                    'want of a "who filled it" marker. There is '
                                    'one -- licenceProvenance -- on exactly the '
                                    'five filled records and on none of the '
                                    'automatically extracted ones.',
    'fetchCounters': c,
    'coverageStatement': 'OpenAlex is third-party bibliographic metadata, not a '
                         'verification by this room and not a publisher '
                         'statement. Where it records nothing the artifact says '
                         'so; open access is never taken to imply a right to '
                         'redistribute.',
    'contentNote': 'Directory prefixes, DOIs and licence codes only.',
}
doc['completionHash'] = content_hash({'resolved': got_n, 'missing': len(missing)})
io.open(S + 'n505_licence_completion.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn505_licence_completion.json' % S)
