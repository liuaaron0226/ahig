# -*- coding: utf-8 -*-
"""n+54 補充二：段內對照（page 222 起）。

🚨🚨 **本檔之結論已被 `.scratch/n54_did.py` 之陰性對照推翻，
保留僅為紀錄。不得引用其 57 倍差異。**

推翻理由：把同一個分組方式套到 (甲) 段——該段兩組在判讀時
「都」沒有摘要，本該無差異——仍得 3.4% vs 46.2%。
**故「補得到／補不到」這個分組本身就在挑記錄**（補不到者多為
極早年代、學位論文、會議摘要，本來就傾向 unclear），
本檔把該選擇效應誤讀為資訊條件之效果。正確比較見 n54_did.py。


(甲)(乙) 之段間比較被頁次趨勢混淆（訊號密度差 4.4 倍），判準
第四節第 3 項已據此判定不得歸因。**但 (乙) 段內部本身就是一組
對照**：同樣是「池內無摘要」的記錄，同樣的頁次範圍、同一位判讀者、
同一套規約，**差別只在補摘要有沒有補到**。

  (乙1) 補到摘要 → 判讀時有摘要
  (乙2) 上游終局無摘要 → 判讀時仍僅憑標題

頁次趨勢在段內幾乎不變，故此對照不受該混淆因子影響。
⚠️ 仍為觀察性分組（誰補得到不是隨機決定），且 (乙2) n 極小，
故一併報 Wilson 區間與 Fisher 精確檢定，結論從嚴。
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
    """雙尾 Fisher 精確檢定。表為 [[a,b],[c,d]]。"""
    def lc(n, k):
        return (math.lgamma(n + 1) - math.lgamma(k + 1)
                - math.lgamma(n - k + 1))
    n = a + b + c + dd
    r1, c1 = a + b, a + c

    def prob(x):
        return math.exp(lc(r1, x) + lc(n - r1, c1 - x) - lc(n, c1))
    obs = prob(a)
    lo = max(0, c1 - (n - r1))
    hi = min(r1, c1)
    return sum(prob(x) for x in range(lo, hi + 1)
               if prob(x) <= obs * (1 + 1e-9))


judged = [it for it in w['items'] if it['candidateId'] in op]
noabs = [it for it in judged if not (it.get('abstract') or '').strip()]
segb = [it for it in noabs if it['page'] >= 222]
b1 = [it for it in segb if it['candidateId'] in ab]
b2 = [it for it in segb if it['candidateId'] not in ab]

print('=== 段內對照：page 222 起之池內無摘要記錄 ===')
rows = []
for nm, g in (('(乙1) 補到摘要 → 判讀時有摘要', b1),
              ('(乙2) 上游終局無摘要 → 僅憑標題', b2)):
    n = len(g)
    unc = sum(1 for it in g if op[it['candidateId']] == 'unclear')
    adv = sum(1 for it in g if op[it['candidateId']] == 'advance')
    s = sum(1 for it in g if CHO_SIGNAL.search(it.get('title') or ''))
    lo, hi = wilson(unc, n)
    print('%-36s n=%-4d unclear %2d (%5.1f%%, CI %4.1f-%4.1f%%)  '
          'advance %d  CHO-signal %d (%.1f%%)'
          % (nm, n, unc, 100.0 * unc / n, 100 * lo, 100 * hi, adv,
             s, 100.0 * s / n))
    rows.append((n, unc, s))

(n1, u1, s1), (n2, u2, s2) = rows
p = fisher_2x2(u2, n2 - u2, u1, n1 - u1)
print()
print('Fisher 精確檢定（雙尾）：p = %.2e' % p)
print('unclear 率比：%.1f 倍（%.1f%% vs %.1f%%）'
      % ((u2 / n2) / (u1 / n1), 100.0 * u2 / n2, 100.0 * u1 / n1))
print()
print('⚠️ 混淆因子方向檢查：訊號密度 (乙2) %.1f%% vs (乙1) %.1f%%'
      % (100.0 * s2 / n2, 100.0 * s1 / n1))
print('   訊號密度低者 unclear 率應**較低**（基準線：無訊號 2.4%%、'
      '有訊號 12.2%%），')
print('   而 (乙2) 訊號密度較低卻 unclear 率較高'
      ' —— **混淆因子方向與觀測相反，故其存在只會低估此差異。**')
print()
print('⚠️ 侷限：(乙2) n=%d，Wilson 區間寬達 %.0f 個百分點；'
      % (n2, 100 * (wilson(u2, n2)[1] - wilson(u2, n2)[0])))
print('   且分組非隨機（能否補到摘要與文獻年代、資料庫收錄有關），'
      '不能當作隨機化實驗看待。')
print()
print('🚨 **以上結論已被 n54_did.py 之陰性對照推翻**：(甲) 段套用同一'
      '分組，兩組在判讀時皆無摘要、')
print('   本該無差異，仍得 3.4%% vs 46.2%%。**此差異是選擇效應，'
      '不是資訊效應。** 請改讀 n54_did.py。')
