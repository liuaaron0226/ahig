# -*- coding: utf-8 -*-
"""n+54 補充三：陰性對照與差異中之差異（DiD）。

⚠️ **本檔起因於一個把我自己的補充二打回去的發現。**

補充二拿 (乙1)「補到摘要」對 (乙2)「終局無摘要」，得 0.8% vs 46.7%
（57 倍，Fisher p=1.4e-08），看起來像補摘要之效果。**但把同一個
分組方式套到 (甲) 段做陰性對照——該段兩組在判讀時「都」沒有摘要
——竟仍得 3.4% vs 46.2%。**

**陰性對照本該無差異卻有大差異，代表「補得到／補不到」這個分組
本身就在挑記錄**（補不到者多為極早年代、學位論文、會議摘要等，
本來就資訊稀薄而傾向 unclear）。**補充二把這個選擇效應誤讀為
資訊條件之效果。**

**正確的比較是差異中之差異**：只看「補得到」這個子群體
（其可得性條件相同），比較它在兩段之判讀率——
(甲1) 判讀時無摘要 vs (乙1) 判讀時有摘要。
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
ab = json.load(open(DEST + '/abstracts.json', encoding='utf-8'))


def wilson(k, n, z=1.96):
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    ctr = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, ctr - half), min(1.0, ctr + half))


def fisher_2x2(a, b, c, dd):
    def lc(n, k):
        return (math.lgamma(n + 1) - math.lgamma(k + 1)
                - math.lgamma(n - k + 1))
    n = a + b + c + dd
    r1, c1 = a + b, a + c

    def prob(x):
        return math.exp(lc(r1, x) + lc(n - r1, c1 - x) - lc(n, c1))
    obs = prob(a)
    lo, hi = max(0, c1 - (n - r1)), min(r1, c1)
    return sum(prob(x) for x in range(lo, hi + 1)
               if prob(x) <= obs * (1 + 1e-9))


judged = [it for it in w['items'] if it['candidateId'] in op]
noabs = [it for it in judged if not (it.get('abstract') or '').strip()]


def cell(lo, hi, obtainable):
    g = [it for it in noabs if lo <= it['page'] <= hi
         and (it['candidateId'] in ab) == obtainable]
    n = len(g)
    u = sum(1 for it in g if op[it['candidateId']] == 'unclear')
    s = sum(1 for it in g if CHO_SIGNAL.search(it.get('title') or ''))
    return {'n': n, 'u': u, 'rate': u / n if n else 0.0,
            'ci': wilson(u, n), 'sig': s / n if n else 0.0}


a1 = cell(212, 221, True)    # 判讀時無摘要，事後補到
a2 = cell(212, 221, False)   # 判讀時無摘要，終局補不到
b1 = cell(222, 999, True)    # 判讀時**有**摘要
b2 = cell(222, 999, False)   # 判讀時無摘要，終局補不到

print('=== 2×2：頁段 × 補摘要可得性（格內為 unclear 率）===')
print('%-26s %-28s %s' % ('', '補得到（可得性相同）', '補不到'))
print('%-26s n=%-4d %5.1f%% (CI %4.1f-%4.1f)   n=%-3d %5.1f%%'
      % ('(甲) p212-221 判讀時無摘要', a1['n'], 100 * a1['rate'],
         100 * a1['ci'][0], 100 * a1['ci'][1], a2['n'],
         100 * a2['rate']))
print('%-26s n=%-4d %5.1f%% (CI %4.1f-%4.1f)   n=%-3d %5.1f%%'
      % ('(乙) p222+  判讀時有摘要', b1['n'], 100 * b1['rate'],
         100 * b1['ci'][0], 100 * b1['ci'][1], b2['n'],
         100 * b2['rate']))
print()

print('--- 陰性對照：「補不到」欄（兩段皆僅憑標題判讀）---')
print('    %.1f%% vs %.1f%% —— 幾乎相同，**符合陰性對照之預期**：'
      % (100 * a2['rate'], 100 * b2['rate']))
print('    該欄之資訊條件在兩段間沒有改變，判讀率就沒有改變。')
print('    ⚠️ 但它同時顯示「補不到」本身之 unclear 率就高達 ~46%%，')
print('    **遠高於同段「補得到」者**——故補充二之 57 倍差異'
      '主要是選擇效應，不是資訊效應。')
print()

print('--- 真正的檢定：「補得到」欄（可得性條件相同，只有資訊條件改變）---')
p = fisher_2x2(a1['u'], a1['n'] - a1['u'], b1['u'], b1['n'] - b1['u'])
print('    (甲1) %.1f%% (%d/%d) → (乙1) %.1f%% (%d/%d)'
      % (100 * a1['rate'], a1['u'], a1['n'],
         100 * b1['rate'], b1['u'], b1['n']))
print('    Fisher 精確檢定（雙尾）p = %.4f' % p)
print('    區間：(甲1) %.1f-%.1f%% vs (乙1) %.1f-%.1f%% → %s'
      % (100 * a1['ci'][0], 100 * a1['ci'][1],
         100 * b1['ci'][0], 100 * b1['ci'][1],
         '不重疊' if (a1['ci'][0] > b1['ci'][1]
                    or b1['ci'][0] > a1['ci'][1]) else '**重疊**'))
print('    混淆因子：訊號密度 (甲1) %.1f%% vs (乙1) %.1f%%（比值 %.2f）'
      % (100 * a1['sig'], 100 * b1['sig'],
         a1['sig'] / b1['sig'] if b1['sig'] else float('inf')))
print()
did = (a1['rate'] - a2['rate']) - (b1['rate'] - b2['rate'])
print('DiD（unclear 率）= (%.3f - %.3f) - (%.3f - %.3f) = %+.3f'
      % (a1['rate'], a2['rate'], b1['rate'], b2['rate'], did))
print('  即：以「補不到」欄為各段之基線，「補得到」欄相對基線之落差'
      '在 (乙) 段又擴大 %.1f 個百分點' % (100 * did))
print('  ——方向與預期一致（補摘要使 unclear 更少），'
      '惟 DiD 之基線欄 n 僅 13／15，估計極不精確。')
print()
print('⚠️ **主檢定（「補得到」欄）未過判準第四節之門檻**：'
      'p=%.4f > 0.05、區間重疊、' % p)
print('   且訊號密度比值 %.2f 倍 ≥ 1.5 —— **依判準第 3 項，'
      '不得歸因於補摘要。**'
      % (a1['sig'] / b1['sig'] if b1['sig'] else float('inf')))
