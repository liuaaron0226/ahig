# -*- coding: utf-8 -*-
"""n+97（三）：勘誤清單——先建清單，再核對。

## 🚨 為什麼要先建清單

第 412 輪本室停下核對工作，理由是三個數字對不上且都沒有清單可查：

| 來源 | 勘誤筆數 |
|---|---|
| n+86（9）裁示所稱 | **七筆** |
| 第 401 輪執行室自報 | **八筆** |
| 第 412 輪本室以判讀措辭樣式抓 | **四筆** |

n+97（三）裁示：**先建清單，再核對，順序不得顛倒**；且
**「三個數字之差異須逐一交代成因（哪個是序號、哪個是樣式命中、哪個是實際筆數），
不得只報最終正確值」。**

## 權威來源

**`worksheet.json` 之 `items[].publicationTypes`**——**⚠️ 這是建檔時之 metadata 欄位，
不是判讀者的措辭**。🚨 第 412 輪之「四筆」正是以判讀措辭樣式抓的，
**那是在量「判讀者怎麼寫」，不是在量「該文獻是什麼型別」。**

⚠️ 輸出只列 id、型別與頁次，**不輸出標題或摘要**（內容制衛生）。
"""
import io
import json
import re
import sys
from collections import Counter

sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash  # noqa: E402

ROOT = ('C:/Users/User/Desktop/claude/ahig-private/search-runs/'
        'b11-exogenous-cho-endurance/b11-full-run/standard-full-screen-pass-1')
DEST = '.scratch/n97_errata_roster.json'

W = json.load(io.open(ROOT + '/worksheet.json', encoding='utf-8'))
E = {e['candidateId']: e for e in
     json.load(io.open(ROOT + '/judgements.json', encoding='utf-8'))['entries']}

# 🚨 型別以 metadata 為準。⚠️ 大小寫與寫法不一，故正規化後比對。
ERRATUM_PAT = re.compile(r'errat|correction|corrigend', re.I)

roster, type_c = [], Counter()
for it in W['items']:
    pts = it.get('publicationTypes') or []
    hits = [t for t in pts if ERRATUM_PAT.search(str(t))]
    if not hits:
        continue
    for t in hits:
        type_c[t] += 1
    j = E.get(it['candidateId'])
    roster.append({
        'candidateId': it['candidateId'],
        'page': it.get('page'),
        'seq': it.get('seq'),
        'publicationTypes': pts,
        'matchedTypes': hits,
        'judged': bool(j),
        'opinion': (j or {}).get('opinion'),
        'hasAbstract': bool((it.get('abstract') or '').strip()),
    })

roster.sort(key=lambda r: (r['page'] or 0, r['seq'] or 0))

print('=' * 70)
print('勘誤清單（權威來源：worksheet.items[].publicationTypes）')
print('=' * 70)
print('共 %d 筆' % len(roster))
print()
print('%-26s %6s %8s  %s' % ('candidateId 末八碼', 'page', '判讀', 'matchedTypes'))
print('-' * 70)
for r in roster:
    print('%-26s %6s %8s  %s'
          % (r['candidateId'][-8:], r['page'], r['opinion'] or '未判',
             ','.join(r['matchedTypes'])))
print()
print('型別字面分布：%s' % dict(type_c))

# ── 三個數字之成因交代（n+97 三明令不得只報最終值）─────────────────
STYLE_PAT = re.compile(
    r'(發表型別為|publicationTypes 為|文獻型態[^。]{0,12})[^。]{0,30}'
    r'(Published Erratum|更正啟事|correction)')
style_hits = [cid for cid, j in E.items()
              if STYLE_PAT.search(j.get('reason', ''))]
mentions = [cid for cid, j in E.items()
            if 'Erratum' in j.get('reason', '') or '勘誤' in j.get('reason', '')]

print()
print('=' * 70)
print('三個數字之成因（n+97 三：不得只報最終正確值）')
print('=' * 70)
print('  n+86（9）裁示所稱                       7  '
      '← ⚠️ 協調者已於 n+97 自承：轉述執行室當時之提請用語，從未查證')
print('  第 401 輪執行室自報                     8  '
      '← ⚠️ 亦為敘述，未附清單，本檔無從重建其當時之計數方式')
print('  第 412 輪以判讀措辭樣式抓             %3d  '
      '← 🚨 量的是「判讀者怎麼寫」，非文獻型別' % len(style_hits))
print('  判讀理由曾提及勘誤／Erratum 者        %3d  '
      '← ⚠️ 含「提到別人是勘誤」者，非自身為勘誤' % len(mentions))
print('  **本檔以 publicationTypes 實算        %3d  ← ✅ 權威來源**' % len(roster))
judged_n = sum(1 for r in roster if r['judged'])
unjudged = [r for r in roster if not r['judged']]
print()
print('🚨 而 7 與 8 的差異已找到，兩個都對，量的是不同東西：')
print('   已判讀之勘誤 %d 筆；尚未判讀 %d 筆（p%s，在 n+57 第 0 步停判線 p299 之後）'
      % (judged_n, len(unjudged),
         '／'.join(str(r['page']) for r in unjudged) or '—'))
print('   ⚠️ 即 n+86 之「七筆」＝已判讀者；第 401 輪之「八筆」＝含未判之全部。')
print('   🚨 兩者皆非錯誤，只是沒有人講明自己數的是哪一個母體。')
print()
print('⚠️ 五個數字量的是五件不同的事，故「哪個對」本身是問錯問題——')
print('   🚨 正確的說法是：**本 lane 之勘誤型文獻為 %d 筆（metadata 為準）**，' % len(roster))
print('   而 7／8 兩個數字是敘述性轉述，4 是措辭樣式命中數。')

doc = {
    'schemaVersion': 1,
    'documentType': 'errata-roster',
    'ruling': 'n+97(3) build the list before checking; n+86(9) the check itself',
    'authoritativeSource': 'worksheet.json items[].publicationTypes',
    'authoritativeSourceNote': (
        'Publication type metadata, not judgement wording. The round-412 count '
        'of 4 was matched against how judges phrased things, which measures '
        'something else entirely.'),
    'pattern': ERRATUM_PAT.pattern,
    'count': len(roster),
    'typeLiterals': dict(type_c),
    'reconciliation': {
        'n+86(9) ruling': {'value': 7, 'kind': 'narrative',
                           'note': 'coordinator self-corrected in n+97: '
                                   'restated the executor phrasing, never verified'},
        'round 401 executor': {'value': 8, 'kind': 'narrative',
                               'note': 'no list attached; counting method not '
                                       'reconstructible from the board'},
        'round 412 wording scan': {'value': len(style_hits), 'kind': 'pattern-hit',
                                   'note': 'measures judge phrasing, not type'},
        'judgements mentioning errata': {'value': len(mentions),
                                         'kind': 'pattern-hit',
                                         'note': 'includes records that merely '
                                                 'mention another record is an '
                                                 'erratum'},
        'this file (metadata)': {'value': len(roster), 'kind': 'authoritative'},
    },
    'sevenVsEightResolved': {
        'judged': sum(1 for r in roster if r['judged']),
        'unjudged': [{'candidateId': r['candidateId'], 'page': r['page']}
                     for r in roster if not r['judged']],
        'explanation': (
            'Both figures are correct over different populations. n+86 said '
            'seven, which is the judged errata; round 401 said eight, which '
            'includes one at p304 -- past the n+57 step-0 hold line at p299, '
            'so never judged. Nobody stated which population they were '
            'counting, which is the whole of the discrepancy.'),
    },
    'roster': roster,
    'contentNote': 'Ids, pages, types and opinions only. No titles or abstracts.',
}
doc['rosterHash'] = content_hash(doc['roster'])
io.open(DEST, 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %s' % DEST)
print('⚠️ 下一步（n+86 九）：逐筆核對其原著是否在池內——**清單已備，可以開始**。')
