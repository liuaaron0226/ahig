# -*- coding: utf-8 -*-
"""n+54 補充：以標題碳水訊號密度調整後之期望值比較。

判準第四節第 3 項只說「密度差 1.5 倍以上就不得歸因於補摘要」，
到此為止結論會停在「無法區辨」。**但混淆因子是可以調整的**：
n+51 已驗證訊號有無之鑑別力，故可用（丙）基準線分別算出
「有訊號」與「無訊號」之判讀率，再依各段之訊號組成算期望值。

⚠️ 這是判準之外的補充分析，**不用來推翻判準之結論**，
只用來說明「扣掉組成差異後還剩多少」。基準率一律由本次資料
現算，不引用記憶中的數字。
"""
import json
import math
import os
import re

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'

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

judged = [it for it in w['items'] if it['candidateId'] in op]


def sig(it):
    return bool(CHO_SIGNAL.search(it.get('title') or ''))


# ---- 基準線（丙）：分訊號有無算 advance / unclear 率 ----
base = [it for it in judged
        if (it.get('abstract') or '').strip() and it['page'] <= 211]
rates = {}
for has in (True, False):
    grp = [it for it in base if sig(it) == has]
    n = len(grp)
    adv = sum(1 for it in grp if op[it['candidateId']] == 'advance')
    unc = sum(1 for it in grp if op[it['candidateId']] == 'unclear')
    rates[has] = {'n': n, 'adv': adv / n, 'unc': unc / n}
    print('基準線（丙）%s訊號：n=%-5d advance %5.2f%%  unclear %5.2f%%'
          % ('有' if has else '無', n, 100 * rates[has]['adv'],
             100 * rates[has]['unc']))
print('  → advance 鑑別力 %.1f 倍'
      % (rates[True]['adv'] / rates[False]['adv']))
print()


def pois_upper_p(obs, exp):
    """觀測數 <= obs 之 Poisson 機率（單尾）。exp 為期望數。"""
    return sum(math.exp(-exp) * exp ** k / math.factorial(k)
               for k in range(obs + 1))


noabs = [it for it in judged if not (it.get('abstract') or '').strip()]
segs = [('(甲) p212-221 判讀時無摘要',
         [it for it in noabs if 212 <= it['page'] <= 221]),
        ('(乙) p222+ 判讀時無摘要',
         [it for it in noabs if it['page'] >= 222])]

print('=== 依訊號組成調整後之期望值 vs 實測 ===')
for label, grp in segs:
    n = len(grp)
    ns = sum(1 for it in grp if sig(it))
    e_adv = ns * rates[True]['adv'] + (n - ns) * rates[False]['adv']
    e_unc = ns * rates[True]['unc'] + (n - ns) * rates[False]['unc']
    o_adv = sum(1 for it in grp if op[it['candidateId']] == 'advance')
    o_unc = sum(1 for it in grp if op[it['candidateId']] == 'unclear')
    print('%s  n=%d（有訊號 %d）' % (label, n, ns))
    print('   advance：期望 %.1f 筆，實測 %d 筆 (P[X<=obs]=%.3f)'
          % (e_adv, o_adv, pois_upper_p(o_adv, e_adv)))
    print('   unclear：期望 %.1f 筆，實測 %d 筆（實測/期望 = %.2f）'
          % (e_unc, o_unc, o_unc / e_unc if e_unc else float('nan')))
