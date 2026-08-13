#!/usr/bin/env python3
"""事後歸因：2025-01 ~ 2026-08 台股翻倍股的共同點，以及贏家/輸家在起點是否可區分。"""
import json, os, statistics as st, collections, math
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "expost_cache.json"), encoding="utf-8"))
META, PX = D["meta"], D["px"]

START = "2024-12"          # 起點＝2024 年 12 月收盤（等於 2025 全年 + 2026 年初至今）
LOOKBACK = 36


def series(code):
    return {m: (c, a) for m, c, a, v in PX[code]}


rows = []
skipped = collections.Counter()
for code, bars in PX.items():
    months = [b[0] for b in bars]
    if START not in months:
        skipped["起點無資料(2025後上市)"] += 1
        continue
    i0 = months.index(START)
    end = bars[-1]
    if end[0] < "2026-07":
        skipped["近期已停牌/下市"] += 1
        continue
    px0, adj0 = bars[i0][1], bars[i0][2]
    if not px0 or not adj0 or px0 <= 0 or adj0 <= 0:
        skipped["起點價格異常"] += 1
        continue
    ret = end[2] / adj0 - 1
    ret_raw = end[1] / px0 - 1
    hist = bars[max(0, i0 - LOOKBACK):i0 + 1]
    closes = [b[1] for b in hist if b[1]]
    hi, lo = max(closes), min(closes)
    r12 = r24 = None
    if i0 - 12 >= 0 and bars[i0 - 12][2]:
        r12 = adj0 / bars[i0 - 12][2] - 1
    if i0 - 24 >= 0 and bars[i0 - 24][2]:
        r24 = adj0 / bars[i0 - 24][2] - 1
    m = META.get(code, {})
    shares = m.get("shares") or 0
    mcap = px0 * shares / 1e8 if shares else None   # 億元
    vols = [b[3] for b in bars[max(0, i0 - 11):i0 + 1] if b[3]]
    rows.append(dict(code=code, name=m.get("name", ""), ind=m.get("industry", "?"),
                     px0=px0, ret=ret, ret_raw=ret_raw, mcap=mcap,
                     dd=1 - px0 / hi, off_low=px0 / lo - 1,
                     nhist=len(closes), r12=r12, r24=r24,
                     vol=st.median(vols) / 1000 if vols else None))

print(f"樣本：{len(rows)} 檔（全上市，2024-12 已上市且 2026-08 仍有報價）")
print("排除：", dict(skipped))
R = np.array([r["ret"] for r in rows])
Rraw = np.array([r["ret_raw"] for r in rows])
win = [r for r in rows if r["ret"] > 1.0]
lose = [r for r in rows if r["ret"] < 0]
print(f"\n【全市場 2025-01 ~ 2026-08 報酬（還原息值）】")
print(f"  中位 {np.median(R)*100:+.1f}%  平均 {R.mean()*100:+.1f}%")
print(f"  >100% 翻倍：{len(win)} 檔 ({len(win)/len(rows)*100:.1f}%)")
print(f"  <0%   下跌：{len(lose)} 檔 ({len(lose)/len(rows)*100:.1f}%)")
print(f"  ＞300%：{sum(1 for r in rows if r['ret']>3)} 檔   ＞500%：{sum(1 for r in rows if r['ret']>5)} 檔")
print(f"  【對照】不還原息（純股價）中位 {np.median(Rraw)*100:+.1f}%，翻倍 {sum(Rraw>1)} 檔")

print("\n═══ 1. 產業別分布 ═══")
byind = collections.defaultdict(list)
for r in rows:
    byind[r["ind"]].append(r)
print(f"{'產業':<18}{'檔數':>5}{'翻倍':>5}{'翻倍率':>8}{'中位報酬':>10}{'佔全部翻倍股':>13}")
print("-" * 62)
tab = []
for ind, v in byind.items():
    w = [x for x in v if x["ret"] > 1]
    tab.append((ind, len(v), len(w), len(w) / len(v) * 100,
                np.median([x["ret"] for x in v]) * 100, len(w) / len(win) * 100))
for t in sorted(tab, key=lambda x: -x[2])[:18]:
    print(f"{t[0]:<18}{t[1]:>5}{t[2]:>5}{t[3]:>7.1f}%{t[4]:>9.1f}%{t[5]:>12.1f}%")
print("...")
for t in sorted(tab, key=lambda x: -x[2])[-6:]:
    print(f"{t[0]:<18}{t[1]:>5}{t[2]:>5}{t[3]:>7.1f}%{t[4]:>9.1f}%{t[5]:>12.1f}%")

top = sorted(tab, key=lambda x: -x[2])
for k in (3, 5):
    sw = sum(t[2] for t in top[:k]) / len(win) * 100
    sn = sum(t[1] for t in top[:k]) / len(rows) * 100
    print(f"\n前 {k} 大產業佔全部翻倍股 {sw:.1f}%，但只佔全市場家數 {sn:.1f}%"
          f"（{'集中' if sw > sn + 10 else '未明顯集中'}）")
# HHI of winners across industries vs universe
hw = sum((t[2] / len(win)) ** 2 for t in tab)
hu = sum((t[1] / len(rows)) ** 2 for t in tab)
print(f"翻倍股產業 HHI = {hw:.4f}；全市場產業 HHI = {hu:.4f}"
      f"（比值 {hw/hu:.2f}；1.0 代表跟全市場一樣分散）")

print("\n═══ 2. 起點特徵：贏家 vs 輸家 ═══")
FEATS = [("起點股價(元)", "px0"), ("起點市值(億)", "mcap"), ("距36M高點回撤", "dd"),
         ("距36M低點漲幅", "off_low"), ("前12M報酬", "r12"), ("前24M報酬", "r24"),
         ("月成交量中位(張)", "vol")]


def auc(a, b):
    """P(隨機贏家特徵 > 隨機輸家特徵)；0.5 = 完全不可區分"""
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = stats.mannwhitneyu(a, b, alternative="two-sided")
    return u.statistic / (len(a) * len(b)), u.pvalue


print(f"{'特徵':<18}{'贏家中位':>12}{'輸家中位':>12}{'全體中位':>12}{'AUC':>8}{'p值':>10}")
print("-" * 74)
for lab, k in FEATS:
    aw = [r[k] for r in win if r[k] is not None]
    al = [r[k] for r in lose if r[k] is not None]
    aa = [r[k] for r in rows if r[k] is not None]
    if len(aw) < 5 or len(al) < 5:
        continue
    a, p = auc(aw, al)
    print(f"{lab:<18}{np.median(aw):>12.2f}{np.median(al):>12.2f}{np.median(aa):>12.2f}"
          f"{a:>8.3f}{p:>10.4f}")
print("AUC 0.5=完全無法區分，0.7 以上才算有實用鑑別力，1.0=完美。")

print("\n═══ 3. 用單一特徵在起點排序，各五分位的翻倍率 ═══")
base = len(win) / len(rows) * 100
for lab, k in FEATS:
    v = [r for r in rows if r[k] is not None]
    v.sort(key=lambda r: r[k])
    q = len(v) // 5
    cells = []
    for i in range(5):
        seg = v[i * q:(i + 1) * q] if i < 4 else v[4 * q:]
        cells.append(sum(1 for x in seg if x["ret"] > 1) / len(seg) * 100)
    print(f"{lab:<18} 低→高五分位翻倍率： " + "  ".join(f"{c:5.1f}%" for c in cells)
          + f"   (基準 {base:.1f}%)")

print("\n═══ 4. 原始假說條件套在 2024-12（起點）的實際表現 ═══")
have = [r for r in rows if r["nhist"] >= 30]
print(f"（有 30 個月以上歷史的 {len(have)} 檔）基準翻倍率 "
      f"{sum(1 for r in have if r['ret']>1)/len(have)*100:.1f}%，"
      f"中位報酬 {np.median([r['ret'] for r in have])*100:+.1f}%")
CONF = [("A 已翻倍+距高點>50%", 1.0, 0.50), ("B 已翻倍+距高點>100%", 1.0, 1.0),
        ("C 漲50%+距高點>50%", 0.5, 0.50), ("D 漲200%+距高點>50%", 2.0, 0.50),
        ("E 漲30%+距高點>30%", 0.3, 0.30)]
print(f"{'條件':<22}{'檔數':>6}{'翻倍率':>9}{'中位報酬':>11}{'跌破-20%':>10}")
print("-" * 60)
for lab, mo, mh in CONF:
    # to_high = hi/px-1 = dd/(1-dd)
    sel = [r for r in have if r["off_low"] >= mo and (r["dd"] / (1 - r["dd"])) >= mh]
    if not sel:
        print(f"{lab:<22}{0:>6}"); continue
    rr = [r["ret"] for r in sel]
    print(f"{lab:<22}{len(sel):>6}{sum(1 for x in rr if x>1)/len(rr)*100:>8.1f}%"
          f"{np.median(rr)*100:>10.1f}%{sum(1 for x in rr if x<-0.2)/len(rr)*100:>9.1f}%")

print("\n═══ 5. 前 30 名贏家（誰真的翻倍了）═══")
print(f"{'代號':<7}{'名稱':<10}{'產業':<14}{'起價':>8}{'市值(億)':>10}{'報酬':>9}{'回撤':>8}")
print("-" * 68)
for r in sorted(rows, key=lambda r: -r["ret"])[:30]:
    print(f"{r['code']:<7}{r['name']:<10}{r['ind']:<14}{r['px0']:>8.1f}"
          f"{(r['mcap'] or 0):>10.0f}{r['ret']*100:>8.0f}%{r['dd']*100:>7.0f}%")

print("\n═══ 6. 產業中性檢定：把產業效果拿掉後，價格特徵還剩多少鑑別力 ═══")
for lab, k in FEATS:
    conc = []
    for ind, v in byind.items():
        v2 = [r for r in v if r[k] is not None]
        if len(v2) < 12:
            continue
        w = [r[k] for r in v2 if r["ret"] > 1]
        l = [r[k] for r in v2 if r["ret"] < 0]
        if len(w) < 3 or len(l) < 3:
            continue
        a, _ = auc(w, l)
        conc.append((a, len(w) * len(l)))
    if conc:
        wsum = sum(w for _, w in conc)
        pooled = sum(a * w for a, w in conc) / wsum
        print(f"{lab:<18} 產業內加權平均 AUC = {pooled:.3f}  （{len(conc)} 個產業）")

print("\n═══ 7. 上限測試：用全部特徵事後配適 logistic，樣本內 AUC 能到多少 ═══")
keys = ["px0", "mcap", "dd", "off_low", "r12", "r24", "vol"]
full = [r for r in rows if all(r[k] is not None for k in keys)]
X = np.array([[math.log(max(r["px0"], .1)), math.log(max(r["mcap"], .1)), r["dd"],
               min(r["off_low"], 5), min(r["r12"], 5), min(r["r24"], 5),
               math.log(max(r["vol"], .1))] for r in full])
y = np.array([1 if r["ret"] > 1 else 0 for r in full])
X = (X - X.mean(0)) / X.std(0)
Xb = np.hstack([np.ones((len(X), 1)), X])
w = np.zeros(Xb.shape[1])
for _ in range(300):
    p = 1 / (1 + np.exp(-Xb @ w))
    g = Xb.T @ (y - p)
    H = (Xb * (p * (1 - p))[:, None]).T @ Xb + 1e-4 * np.eye(Xb.shape[1])
    w += np.linalg.solve(H, g)
s = Xb @ w
a, p = auc(s[y == 1], s[y == 0])
print(f"樣本內（＝已經偷看答案配適）AUC = {a:.3f}, n={len(full)}, 翻倍 {y.sum()} 檔")
print("係數(標準化)：" + "  ".join(f"{k}={c:+.2f}" for k, c in zip(keys, w[1:])))
print("這是『事前可預測性』的樂觀上限；樣本外只會更低。")

# 加入產業 one-hot，看樣本內 AUC 提升多少 → 產業資訊 vs 價格資訊誰重要
inds = sorted({r["ind"] for r in full})
IX = np.array([[1.0 if r["ind"] == i else 0.0 for i in inds] for r in full])
for tag, M in (("只有產業 one-hot", IX), ("產業＋價格特徵", np.hstack([IX, X]))):
    Xb2 = np.hstack([np.ones((len(M), 1)), M])
    w2 = np.zeros(Xb2.shape[1])
    for _ in range(200):
        p2 = 1 / (1 + np.exp(-Xb2 @ w2))
        g2 = Xb2.T @ (y - p2) - 1.0 * w2
        H2 = (Xb2 * (p2 * (1 - p2))[:, None]).T @ Xb2 + 1.0 * np.eye(Xb2.shape[1])
        w2 += np.linalg.solve(H2, g2)
    s2 = Xb2 @ w2
    a2, _ = auc(s2[y == 1], s2[y == 0])
    print(f"{tag:<16} 樣本內 AUC = {a2:.3f}")
