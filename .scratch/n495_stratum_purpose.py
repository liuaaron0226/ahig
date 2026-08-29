# -*- coding: utf-8 -*-
"""七層各自要檢驗什麼，以及在手證據還撐不撐得起來。

## 🚨 為什麼做這件事

n+144 去讀了 `strata.json` 對 S3 寫的理由，發現它不是「多幾篇力竭時間的證據」，
而是**放在校準集裡的探針**：測抽取端會不會把 TT 與 TTE 併成同一 outcome。
**⚠️ 於是「S3 取得 0」的正確讀法變成「七件設計要做的事，有一件做不成了」。**

**🚨 同一個問題該問其餘六層**——本檔即逐層對照：
該層被設計來檢驗什麼、校準集內實得幾篇、那項檢驗還成不成立。

## 🚫 本檔不做的事

**不判斷「幾篇才夠」**——⚠️ 那是統計與判準問題，🚫 本室不代為決定。
本檔只把「設計意圖」與「實得筆數」並列，讓該判斷有依據。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 查得到：`strata.json` 之 rationale 原文、各層實得（兩母體）。
- 🚨 查不到：**某項檢驗在 N 篇之下是否仍有效**——⚠️ 需統計判斷，非檢索。
"""
import io, json, sys
sys.path.insert(0, 'ahig')
from ahig.contracts.freeze import content_hash

S = '.scratch/'
st = json.load(io.open('ahig/calibration/b11-carbohydrate/strata.json', encoding='utf-8'))
tbl = json.load(io.open(S + 'n492_stratum_table.json', encoding='utf-8'))
by = {r['pool']: r for r in tbl['rows']}
# 合併池對應兩個原始層
MERGED = {'S5-gi-harms-primary': 'S5+S6-gi-merged',
          'S6-gi-harms-secondary-only': 'S5+S6-gi-merged'}

print('=== 七層：設計要檢驗什麼 vs 校準集內實得 ===')
print('%-32s %5s %5s %5s  %s' % ('層', '配額', '甲', '乙', '該層被設計來檢驗什麼'))
print('-' * 104)
rows = []
for s in st['strata']:
    sid = s['stratumId']
    key = MERGED.get(sid, sid)
    r = by.get(key, {})
    a = r.get('acquiredCalibration60')
    b = r.get('acquiredWithBackfill')
    note = '（合併池，兩層共用）' if sid in MERGED else ''
    print('%-32s %5d %5s %5s  %s' % (sid, s['quota'], a, b, (s.get('rationale') or '')[:46]))
    rows.append({'stratumId': sid, 'quota': s['quota'], 'poolKey': key,
                 'acquiredCalibration60': a, 'acquiredWithBackfill': b,
                 'designedCheck': s.get('rationale'), 'note': note})
print('-' * 104)
print()
print('🚨 逐層之檢驗是否仍成立（⚠️ 只陳列事實，🚫 不判斷「幾篇才夠」）：')
print('   S3-tte              甲 0  → 🚨 該檢驗做不成（n+144 已裁）')
print('   S7-glycogen         甲 1  → ⚠️ 其 rationale 自載「篇數少但必須存在，'
      '否則量綱設計得不到任何實證檢驗」')
print('   S5+S6（合併）        甲 3  → ⚠️ 見下，該層之區分係設計上延後，非遺失')
print()
print('=== S5／S6 之區分：不是遺失，是設計上延到現在 ===')
print('   `m1_step2_assign.py` 第 28 行：「全文取得後依 GI 之主要性再分為 S5／S6」')
print('   ⚠️ 題摘層之 outcomeHints 不帶「主要性」，故當時無記錄可正面歸入 S5，')
print('      🚨 兩層遂合併抽樣（n+100 二採丙），並明載俟全文到手再分。')
print('   ✅ 而全文已到手（甲 3／乙 7）——🚨 即該分層動作之前提現已部分成就。')
print('   🚫 本室未執行該分層：判斷「GI 是否為主要結局」須讀全文內容，屬萃取期工作。')

doc = {
    'schemaVersion': 1,
    'documentType': 'stratum-purpose-vs-holdings',
    'ruling': 'generalises n+144, which read S3 rationale and found the loss is a check',
    'population': 'the seven contract strata',
    'countingUnit': 'stratum',
    'criterion': 'rationale quoted from strata.json; counts taken from n492 with '
                 'its two populations kept apart',
    'rows': rows,
    's5s6Split': {
        'status': 'deferred by design, not lost',
        'evidence': 'm1_step2_assign.py line 28 states the split happens once full '
                    'text is obtained; title-abstract outcomeHints carry no '
                    'primacy information, so nothing could be placed in S5 at '
                    'sampling time and the two were merged under n+100(2)',
        'preconditionNowMet': 'partly -- full text exists for 3 of the calibration '
                              'pool and 7 with backfill',
        'notDoneHere': 'deciding whether GI harms is a primary outcome requires '
                       'reading the full text, which is extraction-stage work',
    },
    'coverageStatement': 'States what each stratum was designed to check and how '
                         'many records are held. Whether a check remains valid at '
                         'a given N is a statistical judgement, not a lookup, and '
                         'is not answered here.',
    'contentNote': 'Stratum ids, quotas, counts and the rationale text from a '
                   'version-controlled design file.',
}
doc['tableHash'] = content_hash(doc['rows'])
io.open(S + 'n495_stratum_purpose.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn495_stratum_purpose.json' % S)
