# -*- coding: utf-8 -*-
"""S3 那一筆的事實表：**「做不成」那句話所繫的那一份，到底在不在手、完不完整。**

## 🚨 這一支只給事實，🚫 不給判斷

簡報寫「TTE 那一類一篇都沒拿到，**等於這項測試現在做不成**」。
第 521 輪查明：**⚠️ 該層在手不是 0，是 1**（遞補取得之 `d7fe9adf`）。

> **🚨 而「一筆夠不夠做那項檢查」是判斷，🚫 不是檢索。**
> **⚠️ 且 n+147 已明訂：S3 要量的東西，🚫 不得由取得端順手做掉。**

**✅ 故本檔只回答可檢索的部分**：那一份在不在手、切得出幾節、多長、哪個版本、
授權為何、從哪裡拿的、通不通過既有的完整性檢查。
**🚫 本檔不說它夠不夠用——那句話留給裁定。**

## 🚨 為什麼這件事值得單獨做一份

**⚠️ 擁有者正據「做不成」在決定要不要花錢。**
**🚨 而「一筆都沒有」與「有一筆，其性質如下」是兩種不同的決策處境**——
⚠️ 前者只能買，後者可以先看那一筆再決定。
**🚫 本室不替他決定，✅ 但那一筆的性質是可以先攤開的。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 給得出：該筆之取得狀態、節數、字元數、版本、授權、來源主機、檢查結果。
- 🚨 給不出：**它能不能支撐 S3 所設計的那項檢查**——⚠️ 那要讀內容並判斷，
  **🚫 而那正是 n+147 禁止取得端做的事。**
- ⚠️ 🚫 不記任何文獻內容（題名、摘要、節名一律不落盤）。
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
from ahig.search import fulltext as F  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402
from urllib.parse import urlparse  # noqa: E402

S = '.scratch/'
POOL = 'S3-tte'


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


cal = jload(S + 'm1_step2_calibration_set.json')
bf = jload(S + 'm1_step3_backfill.json')
drawn = cal['draws'][POOL]['candidateIds']
accepted = [r['candidateId'] for p in bf['pools'] if p['poolId'] == POOL
            for r in (p.get('backfilled') or []) if r.get('accepted')]

print('=== S3（TTE）層在手者之事實表（🚫 只給事實，不給判斷）===')
print('   抽出 %d 筆｜遞補接受 %d 筆' % (len(drawn), len(accepted)))
print()

rows = []
for cid in drawn + accepted:
    d = PRIVATE_ROOT / 'fulltext' / F._candidate_directory_name(cid)
    mp = d / 'manifest.json'
    if not mp.exists():
        continue
    man = jload(mp)
    if man.get('status') != 'acquired':
        continue
    origin = 'drawn' if cid in drawn else 'backfill'
    for a in (man.get('artifacts') or []):
        sp = d / (a.get('sectionsFile') or '')
        sec = jload(sp) if sp.name and sp.exists() else {}
        # 完整性：直接借用產線驗證器（🚨 它現在也對 sections 之來源指紋）。
        try:
            F._verify_committed_artifacts(d, man)
            verified, err = True, ''
        except Exception as e:
            verified, err = False, '%s: %s' % (type(e).__name__, str(e)[:90])
        host = urlparse(a.get('sourceUrl') or '').netloc
        rows.append({
            'idTail': cid[-8:], 'origin': origin,
            'route': a.get('sourceType'), 'sourceHost': host,
            'sections': len(sec.get('sections') or []),
            'chars': len(sec.get('content') or ''),
            'licence': a.get('licence'),
            'licenceProvenance': bool(a.get('licenceProvenance')),
            'verifierPasses': verified, 'verifierError': err,
        })

if not rows:
    print('🚨 該層在手 0 筆——⚠️ 與第 521 輪之實算不符，🚫 中止並須查。')
    sys.exit(1)

# 版本：取自既有量測，🚫 不重查外部
ver = {}
for f in ('n489_calibration_versions.json',):
    try:
        for r in jload(S + f)['records']:
            ver[r['idFrag']] = r['version']
    except Exception:
        pass

print('一、在手者逐筆')
for r in rows:
    r['version'] = ver.get(r['idTail'], '（本層不在 n489 母體內，未量）')
    print('   %s（%s）｜路徑 %s｜來源 %s'
          % (r['idTail'], r['origin'], r['route'], r['sourceHost'] or '—'))
    print('      節數 %d｜字元 %d｜版本 %s'
          % (r['sections'], r['chars'], r['version']))
    print('      授權 %s（provenance %s）｜產線驗證 %s'
          % (r['licence'] or '🚨 未登記', '有' if r['licenceProvenance'] else '無',
             '✅ 通過' if r['verifierPasses'] else '🚨 ' + r['verifierError']))
# ── 版本：唯一一格未量者，補上（🚨 沿用 n486–488 之來源與判準） ──
import fetch_guard as G  # noqa: E402
from urllib.parse import quote  # noqa: E402

print()
print('一之二、版本（🚨 唯一未量之格，本輪補上）')
email, esrc = G.contact_email()
queue = {i['candidateId']: i
         for i in jload(PRIVATE_ROOT / RUNSUB / 'screening-queue' / 'queue.json')}


def openalex_version(doi):
    url = ('https://api.openalex.org/works/doi:%s?mailto=%s'
           % (quote(doi, safe=''), email))
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, 'HTTP %s %s' % (r['status'], r['error'])
    w = json.loads(r['body'].decode('utf-8'))
    return (w.get('best_oa_location') or {}).get('version'), ''


if not email:
    print('   🚫 無聯絡信箱，依 n+150（三）不送出請求——⚠️ 版本維持未量。')
else:
    # 🚨 控制：先重查一筆 n489 已量者，回傳須相同。
    # ⚠️ 少了它，一個壞掉的查詢路徑回 None，會被讀成「OpenAlex 沒記版本」。
    ctl_frag, ctl_expect = None, None
    try:
        for rec in jload(S + 'n489_calibration_versions.json')['records']:
            if rec.get('version'):
                ctl_frag, ctl_expect = rec['idFrag'], rec['version']
                break
    except Exception:
        pass
    ctl_ok = False
    if ctl_frag:
        # 🚨 `idFrag` 是 candidateId 尾段之**前** 16 碼（見 n492 之取法），
        # ⚠️ 初版以 `c[-16:]` 比對（後 16 碼），於是永遠對不上，控制遂未跑成——
        # ✅ 而本檔因此拒絕報版本，🚫 沒有把「沒查」印成「查了沒有」。
        def frag(c):
            return c.split(':')[-1][:16]
        cid = next((c for c in drawn + accepted if frag(c) == ctl_frag), None)
        if cid is None:
            cid = next((c for c in queue if frag(c) == ctl_frag), None)
        ids = (queue.get(cid) or {}).get('identifiers') or {} if cid else {}
        cdoi = next((str(x) for x in (ids.get('doi') or []) if x), None)
        if cdoi:
            got, err = openalex_version(cdoi)
            ctl_ok = (got == ctl_expect)
            print('   %s 控制：已量之 %s，n489 記 %s／現查 %s %s'
                  % ('✅' if ctl_ok else '🚨', ctl_frag[:8], ctl_expect, got, err))
    if not ctl_ok:
        print('   🚫 控制未過或無對照可用——⚠️ 不報新查之版本，維持未量。')
    else:
        for r in rows:
            cid = next((c for c in drawn + accepted if c[-8:] == r['idTail']), None)
            ids = (queue.get(cid) or {}).get('identifiers') or {} if cid else {}
            doi = next((str(x) for x in (ids.get('doi') or []) if x), None)
            if not doi:
                print('   🚨 %s 無 DOI，🚫 無從查' % r['idTail'])
                continue
            v, err = openalex_version(doi)
            r['version'] = v or ('🚨 OpenAlex 未記載' + (' — ' + err if err else ''))
            r['versionProvenance'] = {
                'source': 'OpenAlex best_oa_location.version',
                'note': '第三方書目資料，🚫 非本室查證（與 n486–488 同一來源與判準）'}
            print('   %s %s → **%s**' % ('✅' if v else '⚠️', r['idTail'], r['version']))
    print('   對外請求：%d（%s）'
          % (G.counters()['totalRequests'], G.counters()['perRequestedHost']))

print()
print('二、🚨 本檔到此為止')
print('   ⚠️ 「一筆夠不夠支撐 S3 所設計的那項檢查」是判斷，🚫 不是檢索；')
print('   🚨 且 n+147 已明訂：S3 要量的東西不得由取得端順手做掉。')
print('   ✅ 故本檔只把那一筆攤開，🚫 不說它夠不夠用。')
print()
print('三、⚠️ 這份表為什麼有用')
print('   🚨 「一筆都沒有」與「有一筆，其性質如下」是兩種決策處境——')
print('   ⚠️ 前者只能買，後者可以先看那一筆再決定。🚫 而選哪一種不是本室的事。')

doc = {
    'schemaVersion': 1,
    'documentType': 's3-in-hand-factsheet',
    'ruling': 'follows round 521: the briefing says the TTE conflation check '
              'cannot be done because nothing was obtained, and one record is in '
              'fact in hand. What that record is, is retrievable; whether it '
              'suffices is not.',
    'population': 'acquired records in the S3-tte stratum, drawn plus accepted '
                  'backfill',
    'countingUnit': 'record',
    'criterion': 'manifest status acquired; facts read from the manifest and the '
                 'sections document, verification borrowed from the production '
                 'verifier',
    'drawn': len(drawn), 'backfillAccepted': len(accepted),
    'inHand': len(rows),
    'records': rows,
    'whatThisDoesNotSay': 'Whether one record can support the check S3 was '
                          'designed to run. That is a reading and a judgement, '
                          'and n+147 reserves it away from the acquisition end.',
    'whyItHelps': 'Nothing obtained and one record with these properties are '
                  'different decision situations: the first can only be bought, '
                  'the second can be looked at first. Choosing between them is '
                  'not this room\'s call.',
    'coverageStatement': 'Facts about the artifact, not about its contents. No '
                         'title, abstract or section name is recorded.',
    'contentNote': 'Id tails, counts, version and licence codes, host names.',
}
doc['factsheetHash'] = content_hash([r['idTail'] for r in rows])
io.open(S + 'n522_s3_record_factsheet.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn522_s3_record_factsheet.json' % S)
