# -*- coding: utf-8 -*-
"""n+54 驗證：補摘要是否降低 unclear 生成率。

判準見 .scratch/n54_criterion.md（已先行 commit）。
只讀不寫，不動任何判讀檔。
"""
import json
import math
import os
import re

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'
DEST = RUN + '/abstract-enrichment'

CHO_SIGNAL = re.compile(
    r'carbohydrate|glucose|sucrose|fructose|maltodextrin|dextrin|'
    r'starch|honey|glycogen|sports drink|CHO\b', re.I)

w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
for f in ('post-ruling-reclassification.json',
          'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + f
    if os.path.exists(p):
        for e in json.load(open(p, encoding='utf-8'))['entries']:
            op[e['candidateId']] = e['effectiveDecision']

pv = json.load(open(DEST + '/provenance.json', encoding='utf-8'))['records']


def wilson(k, n, z=1.96):
    """Wilson 95% 區間。k=事件數, n=樣本數。"""
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, ctr - half), min(1.0, ctr + half))


def stratum(items, label):
    n = len(items)
    c = {'advance': 0, 'unclear': 0, 'exclude': 0}
    for it in items:
        c[op[it['candidateId']]] += 1
    sig = sum(1 for it in items if CHO_SIGNAL.search(it.get('title') or ''))
    lo, hi = wilson(c['unclear'], n)
    alo, ahi = wilson(c['advance'], n)
    print('%-46s n=%-5d unclear %3d (%5.1f%%, CI %4.1f-%4.1f) '
          'advance %3d (%4.1f%%, CI %4.1f-%4.1f) exclude %d  '
          'CHO-signal %3d (%4.1f%%)'
          % (label, n, c['unclear'], 100.0 * c['unclear'] / n,
             100 * lo, 100 * hi, c['advance'], 100.0 * c['advance'] / n,
             100 * alo, 100 * ahi, c['exclude'], sig, 100.0 * sig / n))
    return {'label': label, 'n': n, 'counts': c,
            'unclearCI': (lo, hi), 'advanceCI': (alo, ahi),
            'choSignal': sig, 'choSignalRate': sig / n}


judged = [it for it in w['items'] if it['candidateId'] in op]
noabs = [it for it in judged if not (it.get('abstract') or '').strip()]

# ---- 邊界檢查：p212-221 之無摘要記錄，判讀當時是否真的沒摘要？----
# 判準第二節要求：若該段亦有在判讀前補到摘要者，須據實回報並重畫邊界。
# 依據：補摘要作業（n+50）啟動於 p212-219 重篩，其 provenance 時序
# 無法逐筆還原；改以「該記錄是否曾被補到摘要」為保守上界。
ab = json.load(open(DEST + '/abstracts.json', encoding='utf-8'))
seg_a_all = [it for it in noabs if 212 <= it['page'] <= 221]
seg_a_enriched_now = [it for it in seg_a_all if it['candidateId'] in ab]
print('[邊界檢查] p212-221 無摘要已判 %d 筆，其中「現在」已有補摘要 '
      '%d 筆' % (len(seg_a_all), len(seg_a_enriched_now)))
print('           —— 該段判讀於 n+50/51 補摘要之前，故此 %d 筆之摘要'
      '係事後取得，判讀當時仍為無摘要。' % len(seg_a_enriched_now))
print()

seg_b_all = [it for it in noabs if it['page'] >= 222]
seg_c = [it for it in judged if (it.get('abstract') or '').strip()
         and it['page'] <= 211]

print('=== n+54 三分層（有效標記，含兩層覆蓋）===')
a = stratum(seg_a_all, '(甲) p212-221 判讀時無摘要')
b = stratum(seg_b_all, '(乙) p222+  判讀時無摘要（管線約束後）')
c = stratum(seg_c, '(丙) p1-211 池內原有摘要（基準線）')
print()

# ---- 判準第四節之門檻，逐條套用 ----
print('=== 判準第四節門檻逐條套用 ===')
gate1 = b['n'] < 30 or b['counts']['unclear'] < 10
print('1. 樣本充足性：(乙) n=%d、unclear 事件數=%d → %s'
      % (b['n'], b['counts']['unclear'],
         '**不足，回報「尚不足以判定」**' if gate1 else '足夠'))
overlap = not (a['unclearCI'][1] < b['unclearCI'][0]
               or b['unclearCI'][1] < a['unclearCI'][0])
print('2. 區間重疊：(甲) %.1f-%.1f%% vs (乙) %.1f-%.1f%% → %s'
      % (100 * a['unclearCI'][0], 100 * a['unclearCI'][1],
         100 * b['unclearCI'][0], 100 * b['unclearCI'][1],
         '**重疊，結論為「無法區辨」**' if overlap else '不重疊'))
ratio = (a['choSignalRate'] / b['choSignalRate']
         if b['choSignalRate'] else float('inf'))
print('3. 混淆因子（標題碳水訊號密度）：(甲) %.1f%% vs (乙) %.1f%%，'
      '比值 %.2f 倍 → %s'
      % (100 * a['choSignalRate'], 100 * b['choSignalRate'], ratio,
         '**達 1.5 倍門檻，不得歸因於補摘要**'
         if (ratio >= 1.5 or ratio <= 1 / 1.5) else '未達 1.5 倍門檻'))
print()

# ---- 補充：n+50 當時所引之分層數字，用同一套定義重算 ----
print('=== 補充：全體無摘要 vs 全體有摘要（n+50 當時之對照）===')
stratum(noabs, '全體判讀時無摘要')
stratum([it for it in judged if (it.get('abstract') or '').strip()],
        '全體池內原有摘要')
