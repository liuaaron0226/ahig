# -*- coding: utf-8 -*-
"""n+58 之三筆改判對終止統計量之影響（唯讀量測，不寫任何檔案）。

⚠️ 量測目的：n+58 指示 `2eeb3e43` 與 `5e4acb5a` 判 exclude，
本執行室已判 unclear。改判方向為 unclear → exclude，
**即移除命中、拉長窗口、降低 pScore——方向有利於停止**。
n+43／n+53／n+56 三度確立「裁定與資訊皆不溯及既往」，
故須先量出影響再決定，不得逕改。
"""
import json
import math
import os

ROOT = r'C:/Users/User/Desktop/claude/ahig-private'
RUN = ROOT + '/search-runs/b11-exogenous-cho-endurance/b11-full-run'
OUT = RUN + '/standard-full-screen-pass-1'

w = json.load(open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(open(OUT + '/judgements.json', encoding='utf-8'))
op = {e['candidateId']: e['opinion'] for e in d['entries']}
for f in ('post-ruling-reclassification.json',
          'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + f
    if os.path.exists(p):
        for e in json.load(open(p, encoding='utf-8'))['entries']:
            op[e['candidateId']] = e['effectiveDecision']

items = [it for it in w['items'] if it['candidateId'] in op]
items.sort(key=lambda it: it['seq'])
N_TOTAL = len(w['items'])
TARGET_RECALL = 0.95
HIT = {'advance', 'unclear'}


def stats(labels):
    """labels: 依序之判讀清單。回傳 (rho, window, pScore)。"""
    rho = sum(1 for x in labels if x in HIT)
    window = 0
    for x in reversed(labels):
        if x in HIT:
            break
        window += 1
    screened = len(labels)
    remaining = N_TOTAL - screened
    # h0MinTotalRelevant: 使 recall < target 之最小總相關數
    k_min = None
    for total in range(rho, N_TOTAL + 1):
        if rho / total < TARGET_RECALL:
            k_min = total
            break
    missed = k_min - rho          # H0 下遺漏於未篩者之數量
    # 超幾何：自 remaining 中抽 window 筆全非相關之機率
    if missed <= 0 or window == 0:
        return rho, window, k_min, 1.0
    p = 1.0
    for i in range(window):
        num = (remaining - missed) - i
        den = remaining - i
        if num <= 0:
            p = 0.0
            break
        p *= num / den
    return rho, window, k_min, p


base = [op[it['candidateId']] for it in items]
r0, w0, k0, p0 = stats(base)
print('現況（本執行室已判）      rho=%d window=%3d k_min=%d pScore=%.6f'
      % (r0, w0, k0, p0))

TARGETS = {'2eeb3e43': 'n+58 (一) 明示', '5e4acb5a': 'n+58 (二) 明示',
           '54e29037': '同型（本執行室第 305 輪自行比附）'}

# 逐筆單獨改判之影響
for suf, why in TARGETS.items():
    mod = []
    for it in items:
        v = op[it['candidateId']]
        if it['candidateId'].endswith(suf):
            v = 'exclude'
        mod.append(v)
    r, wd, k, p = stats(mod)
    print('僅改 %s (%s)' % (suf, why))
    print('                          rho=%d window=%3d k_min=%d '
          'pScore=%.6f  (Δwindow %+d, ΔpScore %+.6f)'
          % (r, wd, k, p, wd - w0, p - p0))

# 三筆全改
mod = []
for it in items:
    v = op[it['candidateId']]
    if any(it['candidateId'].endswith(s) for s in TARGETS):
        v = 'exclude'
    mod.append(v)
r3, w3, k3, p3 = stats(mod)
print()
print('三筆全改為 exclude        rho=%d window=%3d k_min=%d pScore=%.6f'
      % (r3, w3, k3, p3))
print('                          Δwindow %+d, ΔpScore %+.6f'
      % (w3 - w0, p3 - p0))
print()
print('⚠️ 方向判讀：ΔpScore 為負值代表「更接近停止」。')
print('   n+43／n+53／n+56 三度確立裁定與資訊皆不溯及既往，')
print('   且 n+53 明言不溯及既往正是為了擋下「有利於停止之回頭改判」。')
