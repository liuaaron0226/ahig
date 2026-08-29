# -*- coding: utf-8 -*-
"""校準集之獨立重抽：那 60 筆是不是文件所述程序真的會抽出來的那 60 筆。

## 🚨 為什麼要重抽，而不是「看數字對不對」

`m1_step2_draw.py` 末尾自己印了這句：

> **「🚨 可獨立重跑之驗證：任何人取 populationHash 與本檔之 seedDerivation，
> 即可重算每池種子並重跑 `random.Random(seed).sample(sorted(pool), quota)`。」**

**⚠️ 它邀請了這件事，而至今沒有人做。**

**🚨 「配額 12+10+8+10+15+5=60、無重複」只證明這份表整齊**，
**🚫 不證明它是那個程序抽出來的**——⚠️ 一份手打的、湊得剛剛好的名單同樣整齊。

> **🚨 分層抽樣之全部效力來自「抽的人事先無從挑選」。**
> **⚠️ 而那件事只有重抽驗得出來。**

## 本檔驗什麼（🚫 判準逐條取自 `m1_step2_draw.py`，不是猜的）

| # | 檢查 | 來源 |
|---|---|---|
| 1 | 抽樣框 `status == 'frozen'`，`totalSampleSize` 等於各池配額之和 | 第 43、44 行之 assert |
| 2 | 校準集之 `anchorHash` == assignment 之 `populationHash` | 第 41 行 |
| 3 | **逐池重算種子**：`sha256("m1-calibration-draw:<poolId>" + anchorHash)[:8]` | 第 49–51 行 |
| 4 | **逐池重抽**：`sorted(random.Random(seed).sample(sorted(pool), quota))` | 第 65 行 |
| 5 | `drawHash == content_hash(picked)` | 第 70 行 |
| 6 | 60 筆互斥且相異；合計等於 `totalSampleSize` | 第 78–80 行之 assert |
| 7 | **遞補之接受者不得已在抽出名單內**——🚨 否則遞補等於把同一筆算兩次 | n+103 之替代規則 |
| 8 | 抽出者與接受之遞補者**都要有 manifest 目錄**——⚠️ 否則它從未被嘗試過 | 本檔自訂 |

## 🚨 一項必須併記的限制：`random.sample` 之實作是直譯器的

**⚠️ 重抽相符，證明的是「在這個直譯器上相符」。**
**🚨 `random.Random.sample` 之演算法屬 CPython 實作細節，跨大版本不保證不變。**

**✅ 故本檔把直譯器版本寫進產物**——
**🚨 「可獨立重跑」這句話若不附版本，就比它聽起來弱。**

## 🚫 本檔不做什麼

- **🚫 不重抽 assignment 本身**——⚠️ 池怎麼來的（篩選、分層歸屬）不在本檔範圍；
  **🚨 本檔只驗「給定這些池，抽出的是不是這 60 筆」。**
- **🚫 不落盤任何文獻內容**——產物只有 id 片段、計數與判定。
- **🚫 不修任何檔案。**

## 涵蓋範圍聲明（n+80 三之紀律）

- ✅ 驗得到：種子、抽出名單、drawHash、互斥性、遞補未重複計入、皆已被嘗試。
- 🚨 驗不到：**池本身對不對**——⚠️ 若 assignment 之池就是錯的，重抽會忠實地重現那個錯。
  **🚨 重抽驗的是程序被忠實執行，不是程序被正確設計。**
- 🚨 亦驗不到：**`populationHash` 是否真的對應當時的判讀狀態**——
  ⚠️ 那要回到 M1 ①，🚫 不在取得端。
"""
import hashlib
import io
import json
import os
import random
import re
import sys
from pathlib import Path

sys.path.insert(0, 'ahig')
os.environ.setdefault('AHIG_PRIVATE_ROOT',
                      r'C:/Users/User/Desktop/claude/ahig-private')
from ahig.contracts.freeze import content_hash  # noqa: E402

S = '.scratch/'
ROOT = Path(os.environ['AHIG_PRIVATE_ROOT']) / 'fulltext'
PURPOSE = 'm1-calibration-draw'
ARTIFACT_DIR = re.compile(r'-[0-9a-f]{16}$')


def seed_for(pool_id, anchor):
    material = ('%s:%s%s' % (PURPOSE, pool_id, anchor)).encode('utf-8')
    return int.from_bytes(hashlib.sha256(material).digest()[:8], 'big')


def redraw(pool_ids, quota, pool_id, anchor):
    """重現 `m1_step2_draw.py` 第 62–70 行。🚫 不得簡化——順序就是結果。"""
    pool = sorted(pool_ids)
    seed = seed_for(pool_id, anchor)
    picked = sorted(random.Random(seed).sample(pool, quota))
    return seed, picked, content_hash(picked)


def verify_pool(pool_ids, quota, pool_id, anchor, recorded):
    """回傳問題清單（空 = 相符）。"""
    bad = []
    seed, picked, dh = redraw(pool_ids, quota, pool_id, anchor)
    if recorded.get('seed') != seed:
        bad.append('種子不符：記錄 %r ≠ 重算 %r' % (recorded.get('seed'), seed))
    if recorded.get('poolSize') != len(set(pool_ids)):
        bad.append('poolSize 不符：記錄 %r ≠ 實際 %d'
                   % (recorded.get('poolSize'), len(set(pool_ids))))
    if sorted(recorded.get('candidateIds') or []) != picked:
        rec = set(recorded.get('candidateIds') or [])
        bad.append('抽出名單不符：記錄獨有 %d 筆、重抽獨有 %d 筆'
                   % (len(rec - set(picked)), len(set(picked) - rec)))
    if recorded.get('drawHash') != dh:
        bad.append('drawHash 不符')
    return bad


def controls():
    """🚨 正反兩向；🚫 全部用合成資料，不碰真實池。"""
    out = []
    pool = ['ahig:x:%03d' % i for i in range(40)]
    anchor = 'sha256:' + '7' * 64
    seed, picked, dh = redraw(pool, 8, 'P-test', anchor)
    good = {'seed': seed, 'poolSize': len(pool),
            'candidateIds': list(picked), 'drawHash': dh}

    def probe(name, recorded, want_bad, ids=None, anch=None):
        bad = verify_pool(ids or pool, 8, 'P-test', anch or anchor, recorded)
        ok = bool(bad) == want_bad
        out.append({'probe': name, 'expectFail': want_bad, 'failed': bool(bad),
                    'findings': bad, 'asExpected': ok})
        print('   %s %-36s 期待%s／實得%s  %s'
              % ('✅' if ok else '🚨', name, '不過' if want_bad else '通過',
                 '不過' if bad else '通過', '；'.join(bad)[:50]))

    probe('正向：忠實重抽之紀錄', json.loads(json.dumps(good)), False)

    d = json.loads(json.dumps(good))
    d['candidateIds'][0] = 'ahig:x:999'
    probe('反向甲：名單換掉一筆', d, True)

    d = json.loads(json.dumps(good))
    d['seed'] = d['seed'] ^ 1
    probe('反向乙：種子差一個位元', d, True)

    d = json.loads(json.dumps(good))
    h = d['drawHash']
    d['drawHash'] = h[:-1] + ('0' if h[-1] != '0' else '1')
    probe('反向丙：drawHash 改一字元', d, True)

    # 🚨 最重要的一道：錨定雜湊變了，抽出來的就該是另一組。
    # ⚠️ 若這道通過，代表種子根本沒進到抽樣裡——那重抽就毫無效力。
    probe('反向丁：錨定雜湊換掉', json.loads(json.dumps(good)), True,
          anch='sha256:' + '8' * 64)

    # 反向戊：池多一筆 → 排序後位置移動，抽出應不同（🚨 證明池真的參與了抽樣）
    probe('反向戊：池多一筆', json.loads(json.dumps(good)), True,
          ids=pool + ['ahig:x:000a'])
    return out


print('=== 校準集之獨立重抽（🚫 唯讀）===')
print('   直譯器 %s——🚨 `random.sample` 是實作細節，重抽之效力繫於此。'
      % sys.version.split()[0])
print()
print('一、控制探針——🚨 未全數如預期則拒絕報告重抽結果')
ctl = controls()
if not all(c['asExpected'] for c in ctl):
    sys.exit('\n🚨 控制探針未全數如預期——🚫 本次重抽結果不予採信，中止。')
print('   ✅ %d 道控制探針全數如預期。' % len(ctl))
print()

a = json.load(io.open(S + 'm1_step2_assignment.json', encoding='utf-8'))
cal = json.load(io.open(S + 'm1_step2_calibration_set.json', encoding='utf-8'))
bf = json.load(io.open(S + 'm1_step3_backfill.json', encoding='utf-8'))
frame = json.load(io.open('ahig/calibration/b11-carbohydrate/strata.json',
                          encoding='utf-8'))
anchor = a['populationHash']

frame_bad = []
if frame.get('status') != 'frozen':
    frame_bad.append('抽樣框非 frozen（實為 %r）' % frame.get('status'))
quota_sum = sum(p['quota'] for p in a['pools'])
if frame.get('totalSampleSize') != quota_sum:
    frame_bad.append('totalSampleSize %r ≠ 池配額之和 %d'
                     % (frame.get('totalSampleSize'), quota_sum))
if cal.get('anchorHash') != anchor:
    frame_bad.append('校準集 anchorHash 與 assignment populationHash 不符')

print('二、抽樣框與錨定')
for b in frame_bad:
    print('   🚨 %s' % b)
if not frame_bad:
    print('   ✅ 框為 frozen；totalSampleSize %d == 池配額之和；anchorHash 相符。'
          % quota_sum)
print()

print('三、逐池重抽')
print('   %-34s %5s %6s %s' % ('抽樣池', '配額', '池大小', '判定'))
print('   ' + '-' * 66)
pools, all_ids = [], []
for p in a['pools']:
    pid = p['poolId']
    rec = cal['draws'].get(pid)
    if rec is None:
        pools.append({'pool': pid, 'verdict': 'missing-from-calibration-set',
                      'findings': ['校準集無此池']})
        print('   %-34s %5d %6d 🚨 校準集無此池' % (pid, p['quota'],
                                                   len(p['candidateIds'])))
        continue
    bad = verify_pool(p['candidateIds'], p['quota'], pid, anchor, rec)
    all_ids += rec.get('candidateIds') or []
    pools.append({'pool': pid, 'quota': p['quota'],
                  'poolSize': len(p['candidateIds']),
                  'verdict': 'reproduced' if not bad else 'divergent',
                  'findings': bad})
    print('   %-34s %5d %6d %s' % (pid, p['quota'], len(p['candidateIds']),
                                   '✅ 重抽相符' if not bad
                                   else '🚨 ' + '；'.join(bad)[:40]))
print('   ' + '-' * 66)
dup = len(all_ids) - len(set(all_ids))
print('   合計 %d 筆，相異 %d 筆%s'
      % (len(all_ids), len(set(all_ids)),
         '' if not dup else '  🚨 重複 %d 筆——互斥性被破壞' % dup))
size_ok = len(all_ids) == frame.get('totalSampleSize')
print('   %s 合計與 totalSampleSize %s'
      % ('✅' if size_ok else '🚨', '相符' if size_ok else '不符'))
print()

# ── 遞補之衛生 ───────────────────────────────────────────────────
print('四、遞補（n+103）之衛生')
drawn = set(all_ids)
accepted, bf_bad = [], []
for p in bf['pools']:
    acc = [r['candidateId'] for r in (p.get('backfilled') or [])
           if r.get('accepted')]
    if p.get('acceptedCount') is not None and p['acceptedCount'] != len(acc):
        bf_bad.append('%s：acceptedCount %r ≠ 實際 %d'
                      % (p['poolId'], p['acceptedCount'], len(acc)))
    overlap = [i for i in acc if i in drawn]
    if overlap:
        bf_bad.append('%s：%d 筆遞補者已在抽出名單內——🚨 會被算兩次'
                      % (p['poolId'], len(overlap)))
    accepted += acc
dupacc = len(accepted) - len(set(accepted))
if dupacc:
    bf_bad.append('遞補者跨池重複 %d 筆' % dupacc)
for b in bf_bad:
    print('   🚨 %s' % b)
if not bf_bad:
    print('   ✅ 遞補接受 %d 筆；🚫 無一已在抽出名單內，🚫 無跨池重複，'
          'acceptedCount 逐池相符。' % len(accepted))
print()

# ── 是否真的被嘗試過 ─────────────────────────────────────────────
print('五、抽出者與遞補者是否都被嘗試過（有無 manifest）')
sys.path.insert(0, 'ahig')
from ahig.search.fulltext import _candidate_directory_name  # noqa: E402
never = [i for i in sorted(drawn | set(accepted))
         if not (ROOT / _candidate_directory_name(i) / 'manifest.json').exists()]
if never:
    print('   🚨 %d 筆從未產生 manifest——⚠️ 它們從未被嘗試過：%s'
          % (len(never), '、'.join(i[-8:] for i in never[:8])))
else:
    print('   ✅ %d 筆（抽出 %d ＋ 遞補 %d）全數有 manifest，'
          '🚨 惟「有 manifest」只代表被嘗試過，🚫 不代表取得成功。'
          % (len(drawn | set(accepted)), len(drawn), len(set(accepted))))

reproduced = sum(1 for p in pools if p['verdict'] == 'reproduced')
ok_all = (not frame_bad and not bf_bad and not never and not dup and size_ok
          and reproduced == len(pools))
print()
print('%s 總判定：%s' % ('✅' if ok_all else '🚨',
                        '校準集之 60 筆為文件所述程序在本直譯器上之忠實產物'
                        if ok_all else '有分歧，見上'))

doc = {
    'schemaVersion': 1,
    'documentType': 'calibration-draw-reproduction',
    'ruling': 'self-initiated: m1_step2_draw.py itself says the draw can be '
              'independently re-run, and nobody had. Tidy quota arithmetic does '
              'not distinguish a real stratified draw from a hand-picked list.',
    'population': 'the six sampling pools of the frozen frame',
    'countingUnit': 'pool for the redraw, record for the hygiene checks',
    'criterion': 'seed, picked list and drawHash all recomputed from the recorded '
                 'anchorHash by the procedure written in m1_step2_draw.py',
    'interpreter': sys.version.split()[0],
    'interpreterCaveat': 'random.Random.sample is a CPython implementation '
                         'detail and is not guaranteed stable across major '
                         'versions. A reproduction is evidence on this '
                         'interpreter; "independently re-runnable" is weaker '
                         'than it sounds unless the version travels with it.',
    'controlProbes': ctl,
    'anchorHash': anchor,
    'frameFindings': frame_bad,
    'pools': pools,
    'totals': {'drawn': len(all_ids), 'distinct': len(set(all_ids)),
               'totalSampleSize': frame.get('totalSampleSize'),
               'backfillAccepted': len(set(accepted))},
    'backfillFindings': bf_bad,
    'neverAttempted': [i[-8:] for i in never],
    'verdict': 'reproduced' if ok_all else 'divergent',
    'coverageStatement': 'Proves the documented procedure was followed on the '
                         'recorded pools. It cannot say the pools are right: if '
                         'assignment is wrong, the redraw faithfully reproduces '
                         'that wrong. And it says nothing about whether '
                         'populationHash matches the judgement state it claims '
                         '-- that is M1 step 1, not acquisition.',
    'contentNote': 'Pool ids, counts, seeds and hashes. Candidate ids appear '
                   'only as 8-character tails.',
}
doc['reproductionHash'] = content_hash({'pools': [p['verdict'] for p in pools],
                                        'verdict': doc['verdict']})
io.open(S + 'n499_calibration_redraw.json', 'w', encoding='utf-8').write(
    json.dumps(doc, ensure_ascii=False, indent=1))
print('✅ 已落盤 → %sn499_calibration_redraw.json' % S)
sys.exit(0 if ok_all else 1)
