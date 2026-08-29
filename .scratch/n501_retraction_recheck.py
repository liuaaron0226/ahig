# -*- coding: utf-8 -*-
"""撤稿狀態之現場重查——**交付當日那一步的預演，兼閘門之首次實網測試。**

## 🚨 為什麼 worksheet 裡的 `publicationTypes` 不夠

`RETRACT_FIELD_N` 取自私有根 worksheet 之 `publicationTypes`。
**⚠️ 而 worksheet 是建檔當下的快照。**

> **🚨 一篇在快照之後才被撤稿的文獻，欄位裡不會有任何痕跡。**
> **⚠️ 而撤稿正是那種「事後才發生」的事——這就是 n+86（十）要求交付當日重查的理由。**

**本檔即那一步**：拿本案母體之 PMID 去 **Europe PMC 現場查**，
**🚫 不看快照，看今天的狀態。**

## 🚨 這也是 `fetch_guard` 的第一次實網請求

n+150 受理閘門時，本室自陳：**九道探針全是合成案例，閘門從未在真實網路上跑過。**
**⚠️ 故本輪同時是它的首次實測**——計數、節流、封鎖、UA 皆由閘門產出並記入產物。

**🚨 而它在第一次就派上用場**：`AHIG_CONTACT_EMAIL` **不在本行程環境裡**
（使用者層級設定未進入此 shell），**⚠️ 依 n+150（三）閘門會直接拒送。**
**✅ 故已把 `contact_email()` 收進閘門**（環境變數 → `HKCU\\Environment`），
**🚨 因為「信箱從哪裡來」既然被立成閘門的契約，就該是閘門的事。**

## 🚨 兩道控制探針——缺一，「0 筆撤稿」就沒有意義

**⚠️ 本檔期待的答案幾乎必然是 0，而 0 有三種來源**：真的沒有、
**🚨 識別碼比對根本沒中**、**🚨 撤稿篩選語法寫錯**。三者輸出一模一樣。

| 探針 | 問的是 | 不過的話 |
|---|---|---|
| **甲：不加撤稿篩選** | `EXT_ID` 比對有沒有中 | **🚫 拒絕報告**——⚠️ 連文獻都沒對到，談何撤稿 |
| **乙：拿快照已標撤稿者去查** | 撤稿篩選語法對不對 | **🚫 拒絕報告**——🚨 篩選錯了，任何 0 都是假的 |

**⚠️ 乙之材料取自本案自己的 worksheet**（`publicationTypes` 含 `Retracted Publication` 者），
**🚨 故它同時回答了第二個問題：那些舊標記今天還成不成立。**

## 🚫 本檔不做什麼

- **🚫 不落盤任何文獻內容。** ⚠️ 查詢一律 `resultType=idlist`——
  **🚨 該模式只回識別碼，題名與摘要根本不會進到本行程。**
- **🚫 不改任何 manifest、不改報告。**
- **🚫 不做主題涵蓋之判斷**——⚠️ n+86（十）要求逐筆確認撤稿件是否與運動營養相關，
  **🚨 那是判讀不是檢索**（當年由 4 改為 5，關鍵正是那一筆的主題）。

## ⚠️ 這是預演，不是交付當日那一次

**🚨 本輪之結果 🚫 不得當作交付時的答案**——n+151（一）明訂逐格須為交付當日現算。
**✅ 本檔證明的是「這一步跑得動、且跑出來的 0 是可信的 0」。**
"""
import io
import json
import os
import re
import sys
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, 'ahig')
sys.path.insert(0, '.scratch')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
import fetch_guard as G  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
PRIV = Path(os.environ['AHIG_PRIVATE_ROOT'])
RUN = PRIV / 'search-runs' / 'b11-exogenous-cho-endurance' / 'b11-full-run'
API = 'https://www.ebi.ac.uk/europepmc/webservices/rest/search'
RETRACTED = 'PUB_TYPE:"Retracted Publication"'
CHUNK = 40


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def ask(values, retracted_only, email, label, field='EXT_ID'):
    """一次查詢。🚫 `resultType=idlist`——回傳只有識別碼，無題名無摘要。

    ⚠️ `field` 可為 `EXT_ID`（PMID）或 `DOI`——🚨 兩條路徑分開走，
    因為 **2 筆母體沒有 PMID**，而「查不到」與「沒有 PMID 所以沒查」不是同一件事。
    """
    q = '(%s)' % ' OR '.join('%s:"%s"' % (field, v) for v in values)
    if retracted_only:
        q += ' AND ' + RETRACTED
    url = ('%s?query=%s&format=json&resultType=idlist&pageSize=1000'
           % (API, quote(q, safe='')))
    r = G.fetch(url, email=email)
    if r['skipped'] or r['status'] != 200:
        return None, {'label': label, 'status': r['status'],
                      'error': r['error'], 'ids': None}
    body = json.loads(r['body'].decode('utf-8'))
    res = (body.get('resultList') or {}).get('result') or []
    # 🚨 `resultType=idlist` 之回應**沒有 `doi` 欄位**（實測：doi 為 None）。
    # ⚠️ 初版據此回推 DOI 集合，於是控制丙拿到空集合而報「篩選語法錯」——
    # 🚨 那是我讀錯回應形狀，不是語法錯。查證：同一個 DOI 查詢
    #    加不加引號都 hitCount=1，回傳之 pmid 正確、doi 為 None。
    # ✅ 故 DOI 路徑改為**一次一個 DOI**，命中與否即無歧義，🚫 不回推。
    got = {str(x.get('pmid') or x.get('id')) for x in res}
    return got, {'label': label, 'status': r['status'], 'field': field,
                 'hitCount': body.get('hitCount'), 'returned': len(res),
                 'error': ''}


email, src = G.contact_email()
print('=== 撤稿狀態現場重查（⚠️ 預演；🚫 非交付當日那一次）===')
print('   聯絡信箱 %s（來源 %s）' % (G.masked(email), src))
if not email:
    sys.exit('🚨 取不到聯絡信箱——依 n+150（三）不送出任何請求，中止。')

# ── 母體：校準集 60 ＋ 接受之遞補 ─────────────────────────────────
cal = jload(S + 'm1_step2_calibration_set.json')
bf = jload(S + 'm1_step3_backfill.json')
scope = {c for d in cal['draws'].values() for c in d['candidateIds']}
scope |= {r['candidateId'] for p in bf['pools']
          for r in (p.get('backfilled') or []) if r.get('accepted')}
queue = {i['candidateId']: i for i in jload(RUN / 'screening-queue' / 'queue.json')}
pmid_of, no_pmid = {}, []
for cid in sorted(scope):
    ids = (queue.get(cid) or {}).get('identifiers') or {}
    got = [str(x) for x in (ids.get('pmid') or []) if x]
    if got:
        pmid_of[got[0]] = cid
    else:
        doi = [str(x) for x in (ids.get('doi') or []) if x]
        no_pmid.append((cid, doi[0].lower() if doi else None))
print('   母體 %d 筆（校準集抽出 60 ＋ 接受之遞補 %d）；有 PMID 者 %d 筆'
      % (len(scope), len(scope) - 60, len(pmid_of)))
if no_pmid:
    print('   ⚠️ %d 筆無 PMID：%s——🚨 改走 DOI 路徑（見第二之二節）'
          % (len(no_pmid), '、'.join('%s（DOI %s）' % (c[-8:], '有' if d else '無')
                                     for c, d in no_pmid)))

# ── 控制乙之材料：快照已標撤稿者 ─────────────────────────────────
flagged = set()
for p in sorted(RUN.glob('*/worksheet.json')):
    for i in (jload(p).get('items') or []):
        if 'Retracted Publication' in (i.get('publicationTypes') or []):
            flagged.add(i['candidateId'])
flag_pmids, flag_dois = [], []
for cid in sorted(flagged):
    ids = (queue.get(cid) or {}).get('identifiers') or {}
    got = [str(x) for x in (ids.get('pmid') or []) if x]
    if got:
        flag_pmids.append(got[0])
    dd = [str(x).lower() for x in (ids.get('doi') or []) if x]
    if dd:
        flag_dois.append(dd[0])
print('   快照已標撤稿者 %d 筆，其中有 PMID 者 %d 筆（🚨 控制乙之材料）'
      % (len(flagged), len(flag_pmids)))
print()

probes, calls = [], []
sample = sorted(pmid_of)[:CHUNK]

print('一、控制探針（🚨 未過即拒絕報告結果）')
got_a, meta_a = ask(sample, False, email, 'A：不加撤稿篩選')
calls.append(meta_a)
ok_a = bool(got_a) and len(got_a) >= max(5, len(sample) // 2)
probes.append({'probe': 'A EXT_ID 比對是否會中', 'expect': '大量命中',
               'got': (len(got_a) if got_a is not None else None),
               'of': len(sample), 'passed': ok_a})
print('   %s 甲：%d／%d 筆對到（🚨 若近乎 0，代表識別碼比對就沒中）'
      % ('✅' if ok_a else '🚨', len(got_a or ()), len(sample)))

got_b, meta_b = ask(flag_pmids, True, email, 'B：撤稿篩選＋已知撤稿者')
calls.append(meta_b)
ok_b = bool(got_b)
probes.append({'probe': 'B 撤稿篩選語法是否有效', 'expect': '≥1',
               'got': (len(got_b) if got_b is not None else None),
               'of': len(flag_pmids), 'passed': ok_b})
print('   %s 乙：%d／%d 筆之撤稿標記今天仍成立（🚨 若為 0，篩選語法錯，任何 0 都是假的）'
      % ('✅' if ok_b else '🚨', len(got_b or ()), len(flag_pmids)))

if not (ok_a and ok_b):
    io.open(S + 'n501_retraction_recheck.json', 'w', encoding='utf-8').write(
        json.dumps({'documentType': 'retraction-recheck', 'aborted': True,
                    'probes': probes, 'calls': calls,
                    'fetchCounters': G.counters()}, ensure_ascii=False, indent=1))
    sys.exit('\n🚨 控制探針未過——🚫 本次結果不予採信，中止（產物已記錄探針與計數）。')
print('   ✅ 兩道控制探針皆過。')
print()

# ── 正題 ─────────────────────────────────────────────────────────
print('二、母體之現場撤稿查詢')
hits, keys = set(), sorted(pmid_of)
for i in range(0, len(keys), CHUNK):
    part = keys[i:i + CHUNK]
    got, meta = ask(part, True, email, '母體第 %d 批（%d 筆）'
                    % (i // CHUNK + 1, len(part)))
    calls.append(meta)
    if got is None:
        print('   🚨 第 %d 批失敗：%s' % (i // CHUNK + 1, meta['error']))
        continue
    hits |= got
    print('   第 %d 批 %2d 筆 → 撤稿 %d' % (i // CHUNK + 1, len(part), len(got)))

print('   ' + '-' * 60)
if hits:
    print('   🚨 現場查得撤稿 %d 筆：%s'
          % (len(hits), '、'.join('%s→%s' % (p, pmid_of.get(p, '?')[-8:])
                                  for p in sorted(hits))))
    print('   ⚠️ 🚫 本室不判斷其主題涵蓋——🚨 n+86（十）要求逐筆確認，那是判讀。')
else:
    print('   ✅ 母體 %d 筆之中，現場查得撤稿 0 筆。' % len(pmid_of))
    print('   🚨 這個 0 之所以可信，是因為控制甲證明識別碼對得到、'
          '控制乙證明篩選抓得到已知撤稿者。')

doi_targets = [d for _, d in no_pmid if d]
doi_hits, doi_probe = set(), None
print()
print('二之二、無 PMID 者之 DOI 路徑（🚨 各自帶控制探針）')
if not doi_targets:
    print('   ⚠️ 無可查之 DOI——🚨 該 %d 筆本輪未涵蓋。' % len(no_pmid))
else:
    # 控制丙：⚠️ 一次一個已知撤稿 DOI，🚨 命中與否無歧義。
    ctl, meta = ask([flag_dois[0]], True, email, 'C：DOI 路徑之撤稿篩選',
                    field='DOI')
    calls.append(meta)
    ok_c = bool(ctl)
    doi_probe = {'probe': 'C DOI 路徑之撤稿篩選是否有效（單一已知撤稿 DOI）',
                 'expect': '1', 'got': (len(ctl) if ctl is not None else None),
                 'of': 1, 'passed': ok_c}
    probes.append(doi_probe)
    print('   %s 丙：以單一已知撤稿 DOI 查詢，命中 %d'
          % ('✅' if ok_c else '🚨', len(ctl or ())))
    if ok_c:
        for d in doi_targets:
            got_d, meta_d = ask([d], True, email, '無 PMID 者之 DOI 查詢',
                                field='DOI')
            calls.append(meta_d)
            if got_d:
                doi_hits |= got_d
        print('   %s %d 筆以 DOI 逐一查詢，撤稿 %d 筆'
              % ('✅' if not doi_hits else '🚨', len(doi_targets), len(doi_hits)))
    else:
        print('   🚫 控制丙未過——⚠️ 不報 DOI 路徑之結果，該 %d 筆列為未涵蓋。'
              % len(doi_targets))

c = G.counters()
print()
print('三、對外請求（由閘門產出，🚫 非事後回想）')
print('   總數 %d｜逐主機 %s｜轉址跳 %d｜相異 URL %d｜封鎖主機 %s'
      % (c['totalRequests'], c['perRequestedHost'], c['redirectHops'],
         c['distinctUrls'], c['blockedHosts'] or '無'))

doc = {
    'schemaVersion': 1,
    'documentType': 'retraction-live-recheck',
    'ruling': 'n+151 delivery item 5 (n+86(10) / n+132): retraction status must '
              'be rechecked on the day of delivery. This is the rehearsal, and '
              "the fetch guard's first real network use.",
    'population': 'the calibration draw of 60 plus accepted n+103 backfill, '
                  'queried by PMID',
    'countingUnit': 'publication',
    'criterion': 'Europe PMC search, resultType=idlist, PUB_TYPE:"Retracted '
                 'Publication" restricted to the population EXT_IDs',
    'isRehearsal': True,
    'rehearsalNote': 'These values are not the delivery answer. n+151(1) '
                     'requires every cell to be computed on the day. What this '
                     'shows is that the step runs and that a zero from it is a '
                     'trustworthy zero.',
    'controlProbes': probes,
    'controlNote': 'A zero here has three possible causes -- nothing retracted, '
                   'no identifier matched, or a wrong filter -- and they look '
                   'identical. Probe A rules out the second, probe B the third.',
    'populationSize': len(scope),
    'withPmid': len(pmid_of),
    'withoutPmid': [{'idTail': c[-8:], 'hasDoi': bool(d)} for c, d in no_pmid],
    'doiRouteChecked': len(doi_targets),
    'doiRouteRetracted': sorted(doi_hits),
    'doiRouteControl': doi_probe,
    'snapshotFlagged': len(flagged),
    'snapshotFlaggedStillRetracted': len(got_b or ()),
    'liveRetractedInPopulation': sorted(hits),
    'calls': calls,
    'fetchCounters': c,
    'contactEmailSource': src,
    'notJudged': 'Whether a retracted record is topically relevant is a reading, '
                 'not a search. n+86(10) requires that per record; the count '
                 'once moved from 4 to 5 precisely on such a reading.',
    'coverageStatement': 'Records without a PMID go through a DOI query with '
                         'its own control; any that carry neither identifier are '
                         'listed as uncovered rather than counted as clean. '
                         'Europe PMC is one register: a retraction recorded '
                         'elsewhere and not there is invisible here.',
    'contentNote': 'Identifiers and counts only. resultType=idlist means no '
                   'title or abstract ever entered this process.',
}
doc['recheckHash'] = content_hash({'hits': sorted(hits), 'n': len(pmid_of)})
io.open(S + 'n501_retraction_recheck.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn501_retraction_recheck.json' % S)
