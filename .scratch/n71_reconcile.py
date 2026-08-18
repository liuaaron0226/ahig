# -*- coding: utf-8 -*-
"""n+71（三）之方向表與本執行室 n+70 實測不符——本檔查出差在哪。

協調者公布：
    200 筆**不入**序列  n_seen 6975  n_start 2293  pScore 0.046023
    200 筆**併入**序列  n_seen 7175  n_start 2093  pScore 0.033741
    → 結論：不入序列 p 較高、較保守。

本執行室 n+70 實測：
    200 筆**併入**序列  pScore 0.480049  windowSize **37**（非 177）
    → 結論方向相反：併入之後 p 反而**更高**。

🚨 兩邊的 `pScore` 差了一個數量級，**不可能兩個都對**。
本檔不主張誰對，而是**把兩個數字各自的前提算出來**——
差異若出在前提，那就不是誰算錯，是兩人算的不是同一件事。

⚠️ 本檔看得到：p_score 之三個輸入（labels、n_total）與其導出量。
本檔看不到：協調者實際跑了什麼程式（我只有他公布的三個數字）。
"""
import glob
import io
import json
import os
import sys

os.environ['AHIG_PRIVATE_ROOT'] = r'C:/Users/User/Desktop/claude/ahig-private'
sys.path.insert(0, 'ahig')
from scipy import stats  # noqa: E402
from ahig.search.statistical_termination import p_score  # noqa: E402

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
for name in ('post-ruling-reclassification.json',
             'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + name
    if os.path.exists(p):
        for e in json.load(io.open(p, encoding='utf-8'))['entries']:
            op[e['candidateId']] = e['effectiveDecision']

s = json.load(io.open('.scratch/n68_tail_sample.json', encoding='utf-8'))
ids = s['sample']['candidateIds']
short2full = {c[-8:]: c for c in ids}
draw_order = []
for p in sorted(glob.glob('.scratch/n68_tail_dec_*.json')):
    for k, v in json.load(io.open(p, encoding='utf-8')).items():
        draw_order.append((short2full[k], v[0]))
assert len(draw_order) == 200
tail = set(ids)
N = w['itemCount']

# ---- 情境 A：200 筆不入序列（現行、n+70 甲）----
labA = [1 if op[it['candidateId']] in ('advance', 'unclear') else 0
        for it in w['items']
        if it['candidateId'] in op and it['candidateId'] not in tail]
A = p_score(labA, N)

# ---- 情境 B1：併入，依 **worksheet 順序**（我 n+70 實測所採）----
labB1 = [1 if op[it['candidateId']] in ('advance', 'unclear') else 0
         for it in w['items'] if it['candidateId'] in op]
B1 = p_score(labB1, N)

# ---- 情境 B2：併入，依 **抽驗抽出順序**接在序列尾端 ----
labB2 = labA + [1 if o in ('advance', 'unclear') else 0
                for _, o in draw_order]
B2 = p_score(labB2, N)

for lab, r in (('A  不入序列（現行）', A),
               ('B1 併入・worksheet 順序', B1),
               ('B2 併入・接在尾端', B2)):
    n_start = N - (r['screenedCount'] - r['windowSize'])
    print('%-26s n_seen %5d  rho %3d  k_min %3d  window %4d  '
          'n_start %5d  pScore %.6f'
          % (lab, r['screenedCount'], r['relevantFound'],
             r['h0MinTotalRelevant'] - r['relevantFound'],
             r['windowSize'], n_start, r['pScore']))

print()
print('協調者公布之兩列：')
print('  不入序列  n_seen 6975  n_start 2293  pScore 0.046023')
print('  併入序列  n_seen 7175  n_start 2093  pScore 0.033741')
print()
print('🚨 其「併入」列之 n_start 2093 = 9091 - (7175 - 177)')
print('   → **它把 windowSize 固定在 177**，即假設併入 200 筆之後')
print('     「最後一筆相關」的位置沒有移動。')
print()

# 驗證：把 window 硬固定在 177 是否重現 0.033741
for rho in (709, 711):
    k_target = (rho * 100) // 95 + 1
    k_min = k_target - rho
    p = float(stats.hypergeom.cdf(0, 2093, k_min, 177))
    print('   若 window=177、n_start=2093、rho=%d（k_min=%d）→ p=%.6f %s'
          % (rho, k_min, p, '← 重現協調者之數字' if abs(p - 0.033741) < 5e-6
             else ''))

print()
print('⚠️ 但那個前提在資料上不成立：本批 200 筆含 2 筆相關')
print('   （`7c2bf4df` advance 於 p282、`ad555302` unclear 於 p349），')
print('   **兩筆都落在目前 window（p280 起）之後**，故一旦併入，')
print('   「最後一筆相關」必然往後移，window 由 177 縮到 %d / %d。'
      % (B1['windowSize'], B2['windowSize']))
print()
print('🚨 方向因此相反：併入之後 pScore 由 %.6f 升到 %.6f（B1）／%.6f（B2）'
      % (A['pScore'], B1['pScore'], B2['pScore']))
print('   即**併入才是較保守的一側，不入序列才是較寬鬆的一側。**')
print('   ⚠️ n+70（甲）之過渡處置仍然安全——但安全的理由不是他寫的那個：')
print('      不是「不入序列比較保守」，而是**排除清單非空時一律不得終止**')
print('      （`allowedToStop False`，已實測），與 p 值大小無關。')
