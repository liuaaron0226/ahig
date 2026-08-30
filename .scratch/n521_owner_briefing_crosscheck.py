# -*- coding: utf-8 -*-
"""擁有者簡報之層別數字對帳：**他要據以決定花不花錢的那兩個數。**

## 🚨 為什麼這一份特別要緊

辛節（第 508 輪）已對過。**⚠️ 而擁有者真正會讀、且正卡著四項待決的，是簡報。**
**🚨 簡報裡的層別數字，是他決定「要不要付費或動用圖書館」的依據。**

> **⚠️ 若那個數字取的是另一個母體，他會據以做一個不該做的決定。**
> **🚨 而本 run 之母體混用事故已達三次，🚫 沒有理由假設這裡不會。**

## 本檔對哪兩句

| 簡報所寫 | 取自哪個母體 | 🚨 同一層之另一個母體 |
|---|---|---|
| GI 層「原本設計要收 **15**，實際拿到 **3**」 | **抽出之 15 筆中取得者** | **該層在手合計**（含遞補） |
| TTE 層「原本要收 **8**，一篇都沒拿到」 | **抽出之 8 筆中取得者＝0** | **該層在手合計** |

**🚨 兩句都不是錯的**——⚠️ 它們對「抽出的那些」為真。
**🚫 但它們讀起來像「這一層我們手上有幾篇」，而那是另一個數。**

## 🚨 TTE 那一句尤其要緊，因為它後面接著一個後果

簡報寫：「一篇都沒拿到，**等於這項測試現在做不成**。」
**⚠️ 若該層實際在手不是 0，那個「做不成」就要重講一次。**

## 🚫 本檔不做什麼

- **🚫 不改簡報**——⚠️ 那是協調者的產物；本檔只對帳並回報。
- **🚫 不替擁有者選母體**——🚨 哪一個母體才是他該看的，是判斷，不是檢索。
  ✅ 本檔把兩個都算出來並排。

## 🚨 控制探針

**⚠️ 一個抓不到句子的抽取器，會安靜地回報「無不符」。**
**✅ 故先對注入版跑一次**（把 `3` 改成 `9`），🚨 必須抓到；抓不到即拒絕報告。

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 對得到：這兩句所引之數，與兩個母體之實算。
- 🚨 對不到：**簡報其餘各節**——⚠️ 本檔只挑取得層之層別數，🚫 不逐句掃描。
- ⚠️ 抽取以固定字樣為準，**🚨 措辭一改就抽不到**——故抽不到時本檔失敗，🚫 不當成通過。
"""
import io
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, 'ahig')
if '.scratch' not in sys.path:
    sys.path.insert(0, '.scratch')
import private_root  # noqa: E402
PRIVATE_ROOT, ROOT_PROVENANCE = private_root.require()
from ahig.search.fulltext import _candidate_directory_name  # noqa: E402
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
DOC = Path('docs/m1-owner-briefing.md')
# ⚠️ 粗體是包住「15 篇」整段而不是只包數字——🚨 初版的樣式假設了後者，
#    於是兩句都抽不到，而本檔**拒絕報告**而不是印出「無不符」。
#    ✅ 那正是這道控制探針的用處；樣式已依實際排版改寫。
GI = re.compile(r'原本設計要收\s*\*\*(\d+)\s*篇\*\*.{0,60}?'
                r'實際拿到\s*(\d+)\s*篇', re.S)
TTE = re.compile(r'原本要收\s*(\d+)\s*篇，\*\*(一篇都沒拿到)\*\*')


def jload(p):
    return json.load(io.open(p, encoding='utf-8'))


def stratum(pool_id):
    """回傳 (抽出數, 抽出中取得, 遞補接受數, 遞補中取得, 該層在手合計)。"""
    cal = jload(S + 'm1_step2_calibration_set.json')
    bf = jload(S + 'm1_step3_backfill.json')
    drawn = cal['draws'][pool_id]['candidateIds']
    acc = [r['candidateId'] for p in bf['pools'] if p['poolId'] == pool_id
           for r in (p.get('backfilled') or []) if r.get('accepted')]

    def got(ids):
        n = 0
        for c in ids:
            mp = (PRIVATE_ROOT / 'fulltext' / _candidate_directory_name(c)
                  / 'manifest.json')
            if mp.exists() and jload(mp).get('status') == 'acquired':
                n += 1
        return n
    dg, ag = got(drawn), got(acc)
    return len(drawn), dg, len(acc), ag, dg + ag


def read_claims(text):
    gi, tte = GI.search(text), TTE.search(text)
    return gi, tte


if not DOC.exists():
    sys.exit('🚨 找不到 %s——🚫 中止。' % DOC)
text = DOC.read_text(encoding='utf-8')

print('=== 擁有者簡報之層別數字對帳（🚫 唯讀，不改簡報）===')
print()
print('一、控制探針——🚨 抓不到即拒絕報告')
gi, tte = read_claims(text)
found = bool(gi) and bool(tte)
print('   %s 兩句皆抽得到（GI %s／TTE %s）'
      % ('✅' if found else '🚨', bool(gi), bool(tte)))
if not found:
    sys.exit('🚨 抽取失敗——⚠️ 措辭可能已改，🚫 不得當成「無不符」。')
injected = text.replace('實際拿到 3 篇', '實際拿到 9 篇', 1)
gi2, _ = read_claims(injected)
caught = bool(gi2) and gi2.group(2) != gi.group(2)
print('   %s 注入（3 → 9）被抓到' % ('✅' if caught else '🚨'))
if not caught:
    sys.exit('🚨 注入未被抓到——🚫 結果不予採信。')
print('   ✅ 抽得到、也分得出改動。')
print()

rows = []
print('二、逐句')
for label, pool, claim_quota, claim_got in (
        ('GI（S5＋S6）', 'S5+S6-gi-merged', int(gi.group(1)), int(gi.group(2))),
        ('TTE（S3）', 'S3-tte', int(tte.group(1)), 0)):
    n_draw, draw_got, n_acc, acc_got, total = stratum(pool)
    rows.append({'label': label, 'pool': pool, 'briefingQuota': claim_quota,
                 'briefingAcquired': claim_got, 'drawn': n_draw,
                 'acquiredFromDrawn': draw_got, 'backfillAccepted': n_acc,
                 'acquiredFromBackfill': acc_got, 'stratumInHand': total,
                 'matchesDrawnPopulation': claim_got == draw_got,
                 'differsFromStratumTotal': claim_got != total})
    print('   %s' % label)
    print('      簡報：配額 %d／拿到 %d' % (claim_quota, claim_got))
    print('      實算：抽出 %d 中取得 %d｜遞補接受 %d 中取得 %d｜'
          '**該層在手合計 %d**' % (n_draw, draw_got, n_acc, acc_got, total))
    if claim_got == draw_got and claim_got != total:
        print('      ⚠️ 簡報之數對「抽出的那些」為真，'
              '🚨 而該層在手實為 %d——⚠️ 兩者差 %d。'
              % (total, total - claim_got))
    elif claim_got == total:
        print('      ✅ 與該層在手合計一致。')
    else:
        print('      🚨 兩個母體都對不上——⚠️ 須查。')
print()

gap = [r for r in rows if r['matchesDrawnPopulation']
       and r['differsFromStratumTotal']]
print('三、🚨 結論')
if gap:
    for r in gap:
        print('   ⚠️ %s：簡報 %d（抽出母體）｜該層在手 %d'
              % (r['label'], r['briefingAcquired'], r['stratumInHand']))
    print('   🚨 兩個數都不是錯的——⚠️ 它們是兩個母體。')
    print('   🚨 而簡報那句讀起來像「這一層我們手上有幾篇」，🚫 那是另一個數。')
    print('   ⚠️ TTE 那一句後面接著一個後果——「等於這項測試現在做不成」；')
    print('      🚨 該層在手若不是 0，那個「做不成」要重講一次。')
    print('   🚫 本室不替擁有者選母體——⚠️ 哪一個才是他該看的，是判斷不是檢索。')
else:
    print('   ✅ 兩句皆與該層在手合計一致。')

doc = {
    'schemaVersion': 1,
    'documentType': 'owner-briefing-stratum-crosscheck',
    'ruling': 'self-initiated: section G was read back in round 508, but the '
              'document the owner actually reads -- and is currently blocked on '
              '-- is the briefing, and its per-stratum figures are what a '
              'spend-money decision would rest on',
    'population': 'the two per-stratum claims in the owner briefing',
    'countingUnit': 'claim',
    'criterion': 'the quoted figure against both populations: acquired among the '
                 'drawn records, and acquired in that stratum including accepted '
                 'backfill',
    'controlProbe': {'bothClaimsExtracted': found, 'injectionCaught': caught,
                     'why': 'An extractor that matches nothing reports no '
                            'discrepancy, which reads as agreement.'},
    'claims': rows,
    'populationGap': [r['label'] for r in gap],
    'notThisRoomsCall': 'Which population belongs in front of the owner is a '
                        'judgement, not a search. Both are computed and set side '
                        'by side; neither is chosen here.',
    'consequenceNote': 'The TTE sentence carries a consequence -- that the '
                       'conflation check cannot be done. If the stratum holds a '
                       'record after backfill, that consequence needs restating.',
    'coverageStatement': 'Only the two acquisition-layer stratum claims, matched '
                         'on fixed wording. A change of wording makes extraction '
                         'fail, and failure is reported as failure rather than as '
                         'agreement.',
    'contentNote': 'Counts and pool ids only.',
}
doc['crosscheckHash'] = content_hash([r['stratumInHand'] for r in rows])
io.open(S + 'n521_owner_briefing_crosscheck.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print()
print('✅ 已落盤 → %sn521_owner_briefing_crosscheck.json' % S)
sys.exit(1 if gap else 0)
