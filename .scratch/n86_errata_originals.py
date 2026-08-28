# -*- coding: utf-8 -*-
"""n+86（9）：逐筆核對勘誤之原著是否在候選池內。

**前置條件已備**：清單由 `.scratch/n97_errata_roster.py` 以 `publicationTypes`
建立（8 筆），n+97（三）要求之「先建清單再核對」順序已滿足。

## 🚨 為什麼四筆已有結論者仍要重跑

判讀原文已載四筆之原著位置（p64／p105／p63／p105）。
**⚠️ 但那是判讀者當時寫下的敘述**，而 n+48 第二節之通則是
**「凡聲稱執行過的動作，一律以可驗證的指令輸出為憑」**。
**🚨 本檔對八筆一律以標題比對現算**，已知者用來**驗證方法本身**
——**⚠️ 若本檔對那四筆算不出相同的原著，錯的是本檔的方法，不是判讀。**

## 🚨 三筆是推定，不是核對

`1c7ff15b`（p193）之判讀原句：
> 「**依既有慣例**（勘誤之原始文獻皆已在池中，本執行室已四度實地檢驗），
>  **該原始文獻應已另筆存在**」

**⚠️ 那是從前四次的結果推出來的，不是查了這一筆。**
`4fa0585e`（p204）同型；`5d55778e`（p100）只載原著標題而未載其位置；
`9b05b6d0`（p304）從未判讀。**🚨 這四筆是本檔真正要回答的。**

## 比對方法

勘誤標題慣例為 `Corrigendum:／Correction:／Erratum:` ＋ 原著標題。
去前綴、正規化（小寫、去標點與多餘空白）後，在 worksheet 全體之標題中找相符者。
**⚠️ 先求完全相符，再退而求「一方包含另一方」**——
**🚨 並逐筆標明用了哪一種，因為包含比對會有偽陽性。**

⚠️ 輸出只有 id、頁次、判讀與比對方式，**不輸出任何標題文字**（內容制衛生）。
"""
import io
import json
import re
import sys

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
DEST = '.scratch/n86_errata_originals.json'

W = json.load(io.open(ROOT + '/worksheet.json', encoding='utf-8'))
E = {e['candidateId']: e for e in
     json.load(io.open(ROOT + '/judgements.json', encoding='utf-8'))['entries']}
roster = json.load(io.open('.scratch/n97_errata_roster.json',
                           encoding='utf-8'))['roster']

PREFIX = re.compile(
    r'^\s*(corrigendum|correction|erratum|errata|publisher\W*s?\s*(note|correction))'
    r'\s*(to|for|:|\u2014|-|\u2013)?\s*', re.I)


def norm(t):
    t = (t or '').strip()
    t = PREFIX.sub('', t)
    t = re.sub(r'[^0-9a-z\u4e00-\u9fff]+', ' ', t.lower())
    return re.sub(r'\s+', ' ', t).strip()


items = [{'candidateId': it['candidateId'], 'page': it.get('page'),
          'title': it.get('title') or '', 'norm': norm(it.get('title'))}
         for it in W['items']]
by_norm = {}
for it in items:
    by_norm.setdefault(it['norm'], []).append(it)

errata_ids = {r['candidateId'] for r in roster}
out = []
for r in roster:
    me = next(i for i in items if i['candidateId'] == r['candidateId'])
    target = me['norm']
    exact = [i for i in by_norm.get(target, [])
             if i['candidateId'] not in errata_ids]
    method, found = 'exact', exact
    if not found and len(target) >= 25:
        # ⚠️ 退而求包含關係——只在標題夠長時才做，短標題包含比對偽陽性太高
        found = [i for i in items
                 if i['candidateId'] not in errata_ids
                 and (target in i['norm'] or i['norm'] in target)]
        method = 'containment'
    j_self = E.get(r['candidateId'])
    rec = {
        'erratum': r['candidateId'], 'errataPage': r['page'],
        'erratumJudged': bool(j_self),
        'matchMethod': method if found else None,
        'originals': [{'candidateId': i['candidateId'], 'page': i['page'],
                       'opinion': (E.get(i['candidateId']) or {}).get('opinion')}
                      for i in found],
        'inPool': bool(found),
    }
    out.append(rec)

print('=' * 78)
print('勘誤之原著是否在池內（n+86 九）——八筆逐一現算')
print('=' * 78)
print('%-12s %6s %8s %-13s %s' % ('勘誤', 'p', '本身判讀', '比對方式', '原著（p／判讀）'))
print('-' * 78)
for r in out:
    origs = '／'.join('%s p%s %s' % (o['candidateId'][-8:], o['page'],
                                     o['opinion'] or '未判')
                      for o in r['originals']) or '🚨 未找到'
    print('%-12s %6s %8s %-13s %s'
          % (r['erratum'][-8:], r['errataPage'],
             '已判' if r['erratumJudged'] else '未判',
             r['matchMethod'] or '—', origs))

n_in = sum(1 for r in out if r['inPool'])
print('-' * 78)
print('在池內 %d / %d' % (n_in, len(out)))

doc = {
    'schemaVersion': 1,
    'documentType': 'errata-originals-check',
    'ruling': 'n+86(9), performed after n+97(3) roster',
    'rosterHash': json.load(io.open('.scratch/n97_errata_roster.json',
                                    encoding='utf-8'))['rosterHash'],
    'method': ('Strip Corrigendum/Correction/Erratum prefix, normalise case '
               'and punctuation, match against all worksheet titles excluding '
               'the errata themselves. Exact match first; containment only for '
               'titles of 25+ normalised characters, and the method used is '
               'recorded per record because containment can produce false '
               'positives.'),
    'verificationNote': (
        'All eight recomputed, including the four whose originals the '
        'judgements already named. Those four are the control: if this file '
        'cannot reproduce them, the method is wrong, not the judgement.'),
    'checked': out,
    'inPool': n_in,
    'total': len(out),
    'contentNote': 'Ids, pages, opinions and match method only. No titles.',
}
doc['checkHash'] = content_hash(doc['checked'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %s' % DEST)
