# -*- coding: utf-8 -*-
"""n+61（二）（三）之改判影響量測——**執行前先量，方向有利於停止者停手。**

n+61（二）就 `05fea7ad`（book-chapter）、（三）就三筆後續通信立裁定。
兩者若導致 `unclear → exclude`，方向皆為「移除命中」＝有利於停止，
**正是 n+43／n+53／n+59 立規則要擋的方向。** 故先以生產程式量測。

本檔唯讀，不寫任何檔案。
"""
import io
import json
import math
import os

OUT = (r'C:/Users/User/Desktop/claude/ahig-private/search-runs'
       r'/b11-exogenous-cho-endurance/b11-full-run'
       r'/standard-full-screen-pass-1')

POOL = 9091
TARGET_RECALL = 0.95

w = json.load(io.open(OUT + '/worksheet.json', encoding='utf-8'))
d = json.load(io.open(OUT + '/judgements.json', encoding='utf-8'))
order = [it['candidateId'] for it in w['items']]
base = {e['candidateId']: e['opinion'] for e in d['entries']}
for f in ('post-ruling-reclassification.json',
          'post-ruling-abstract-rescreen.json'):
    p = OUT + '/' + f
    if os.path.exists(p):
        for e in json.load(io.open(p, encoding='utf-8'))['entries']:
            base[e['candidateId']] = e['effectiveDecision']

HIT = {'advance', 'unclear'}


def stats(op):
    seq = [c for c in order if c in op]
    n = len(seq)
    rho = sum(1 for c in seq if op[c] in HIT)
    window = 0
    for c in reversed(seq):
        if op[c] in HIT:
            break
        window += 1
    h0 = math.ceil(rho / TARGET_RECALL)
    # ADR-0008 pScore：超幾何尾機率（與 term.py 同式）
    k_min = max(1, int(round(h0 * 0.0526)))
    if window == 0:
        p = 1.0
    else:
        p = 1.0
        remaining = POOL - n
        miss = h0 - rho
        if miss <= 0:
            p = 0.0
        else:
            p = 1.0
            for i in range(window):
                p *= max(0.0, (POOL - n + window - i - miss)) / (POOL - n + window - i)
    return n, rho, window, h0, k_min, p


print('=== 現況 ===')
n0, r0, w0, h0, k0, p0 = stats(base)
print('seq %d  rho %d  window %d  h0 %d  pScore(近似) %.6f' % (n0, r0, w0, h0, p0))
print()

# n+61（二）：05fea7ad 若由 unclear → exclude
CASES = [
    ('05fea7ad（book-chapter）', ['05fea7ad']),
    ('76508848（Pesta 通信，本執行室判 unclear）', ['76508848']),
    ('72580166（120 g/h 方法學評論）', ['72580166']),
    ('僅兩筆通信（不動 book-chapter）', ['76508848', '72580166']),
    ('三筆全改', ['05fea7ad', '76508848', '72580166']),
]

for label, shorts in CASES:
    op = dict(base)
    touched = []
    for s in shorts:
        cid = next((c for c in op if c.endswith(s)), None)
        if cid is None:
            print('%-44s [找不到 %s]' % (label, s))
            continue
        if op[cid] != 'unclear':
            print('%-44s [%s 現為 %s，非 unclear]' % (label, s, op[cid]))
            continue
        op[cid] = 'exclude'
        touched.append(s)
    if not touched:
        continue
    n, r, wd, h, k, p = stats(op)
    print('%-44s rho %d→%d  window %d→%d  Δwindow %+d  pScore %.6f→%.6f'
          % (label, r0, r, w0, wd, wd - w0, p0, p))

print()
print('⚠️ 依 n+59 第二節第二道閘：**影響為零者照裁定執行；')
print('   影響非零且方向有利於停止（拉長窗口／降低 pScore）者，')
print('   一律停手回報，須協調者逐筆明示授權後方得執行。**')
print()
print('⚠️ 本檔之 pScore 為近似式，與生產程式 term.py 之值略有出入')
print('   （現況 0.5319 vs term.py 0.5228）——**故結論一律以 window 為準**，')
print('   window 為直接計數、與 term.py 逐字相符；')
print('   真正執行前後仍須以 term.py 實測比對。')
