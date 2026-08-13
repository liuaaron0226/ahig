#!/usr/bin/env python3
"""第二輪：交叉驗證的可預測性、產業動能是否事前可選、資料查核。"""
import json, os, collections, math, random
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "expost_cache.json"), encoding="utf-8"))
META, PX = D["meta"], D["px"]
START, LOOK = "2024-12", 36

rows = []
for code, bars in PX.items():
    months = [b[0] for b in bars]
    if START not in months:
        continue
    i0 = months.index(START)
    end = bars[-1]
    if end[0] < "2026-07":
        continue
    px0, adj0 = bars[i0][1], bars[i0][2]
    if not px0 or not adj0:
        continue
    hist = [b[1] for b in bars[max(0, i0 - LOOK):i0 + 1] if b[1]]
    m = META.get(code, {})
    sh = m.get("shares") or 0
    vols = [b[3] for b in bars[max(0, i0 - 11):i0 + 1] if b[3]]
    prior = {}
    for lb, key in ((12, "r12"), (24, "r24"), (36, "r36")):
        prior[key] = (adj0 / bars[i0 - lb][2] - 1) if i0 - lb >= 0 and bars[i0 - lb][2] else None
    rows.append(dict(code=code, name=m.get("name", ""), ind=m.get("industry", "?"),
                     px0=px0, ret=end[2] / adj0 - 1, mcap=px0 * sh / 1e8 if sh else None,
                     dd=1 - px0 / max(hist), off_low=px0 / min(hist) - 1,
                     vol=float(np.median(vols)) / 1000 if vols else None, **prior))

win = [r for r in rows if r["ret"] > 1]
base = len(win) / len(rows)
print(f"n={len(rows)}  翻倍 {len(win)} ({base*100:.1f}%)")


def auc(a, b):
    a, b = np.asarray(a, float), np.asarray(b, float)
    u = stats.mannwhitneyu(a, b, alternative="two-sided")
    return u.statistic / (len(a) * len(b)), u.pvalue


# ---------- A. 交叉驗證：真正的樣本外可預測性 ----------
print("\n═══ A. 5-fold 交叉驗證的樣本外 AUC（預測『會不會翻倍』）═══")
keys = ["px0", "mcap", "dd", "off_low", "r12", "r24", "vol"]
full = [r for r in rows if all(r[k] is not None for k in keys)]
y = np.array([1.0 if r["ret"] > 1 else 0.0 for r in full])
Xp = np.array([[math.log(max(r["px0"], .1)), math.log(max(r["mcap"], .1)), r["dd"],
                min(r["off_low"], 5), min(r["r12"], 5), min(r["r24"], 5),
                math.log(max(r["vol"], .1))] for r in full])
Xp = (Xp - Xp.mean(0)) / Xp.std(0)
inds = sorted({r["ind"] for r in full})
Xi = np.array([[1.0 if r["ind"] == i else 0.0 for i in inds] for r in full])


def fit(X, yy, lam=1.0, it=200):
    Xb = np.hstack([np.ones((len(X), 1)), X])
    w = np.zeros(Xb.shape[1])
    for _ in range(it):
        p = 1 / (1 + np.exp(-np.clip(Xb @ w, -30, 30)))
        g = Xb.T @ (yy - p) - lam * w
        H = (Xb * (p * (1 - p))[:, None]).T @ Xb + lam * np.eye(Xb.shape[1])
        w = w + np.linalg.solve(H, g)
    return w


def cv_auc(X, yy, folds=5, seed=7):
    idx = np.arange(len(yy)); rng = np.random.default_rng(seed); rng.shuffle(idx)
    s = np.zeros(len(yy))
    for f in range(folds):
        te = idx[f::folds]; tr = np.setdiff1d(idx, te)
        w = fit(X[tr], yy[tr])
        s[te] = np.hstack([np.ones((len(te), 1)), X[te]]) @ w
    return auc(s[yy == 1], s[yy == 0])[0], s


for tag, X in (("只有價格/規模特徵", Xp), ("只有產業別", Xi), ("產業＋價格特徵", np.hstack([Xi, Xp]))):
    a, s = cv_auc(X, y)
    # top-decile lift：照分數排序取前 10%，翻倍率多少
    o = np.argsort(-s); k = len(s) // 10
    hit = y[o[:k]].mean()
    print(f"{tag:<16} 樣本外 AUC={a:.3f}   前10%分數的翻倍率 {hit*100:.1f}%（基準 {base*100:.1f}%，"
          f"lift {hit/base:.2f}x）")

# 隨機基準：AUC 分布
ra = [auc(np.random.rand(int(y.sum())), np.random.rand(int(len(y) - y.sum())))[0] for _ in range(200)]
print(f"純隨機分數的 AUC 分布：中位 {np.median(ra):.3f}，95% 區間 "
      f"[{np.percentile(ra,2.5):.3f}, {np.percentile(ra,97.5):.3f}]")

# ---------- B. 產業動能：2024 年的產業表現能不能預測 2025-26 的產業表現？----------
print("\n═══ B. 事前可選產業嗎？用 2024 年產業報酬預測 2025-26 產業翻倍率 ═══")
byind = collections.defaultdict(list)
for r in rows:
    byind[r["ind"]].append(r)
tab = []
for ind, v in byind.items():
    if len(v) < 8:
        continue
    p24 = [r["r24"] for r in v if r["r24"] is not None]
    p12 = [r["r12"] for r in v if r["r12"] is not None]
    fwd = [r["ret"] for r in v]
    tab.append((ind, len(v), np.median(p12) * 100, np.median(p24) * 100,
                np.median(fwd) * 100, sum(1 for x in fwd if x > 1) / len(v) * 100))
print(f"{'產業':<16}{'檔數':>5}{'2024報酬中位':>13}{'2023-24報酬':>12}"
      f"{'2025-26中位':>12}{'2025-26翻倍率':>13}")
print("-" * 72)
for t in sorted(tab, key=lambda x: -x[5]):
    print(f"{t[0]:<16}{t[1]:>5}{t[2]:>12.1f}%{t[3]:>11.1f}%{t[4]:>11.1f}%{t[5]:>12.1f}%")
a12 = stats.spearmanr([t[2] for t in tab], [t[5] for t in tab])
a24 = stats.spearmanr([t[3] for t in tab], [t[5] for t in tab])
f12 = stats.spearmanr([t[2] for t in tab], [t[4] for t in tab])
print(f"\n產業 2024 報酬 vs 之後翻倍率  Spearman ρ={a12.statistic:+.3f} (p={a12.pvalue:.3f})")
print(f"產業 2023-24 報酬 vs 之後翻倍率 Spearman ρ={a24.statistic:+.3f} (p={a24.pvalue:.3f})")
print(f"產業 2024 報酬 vs 之後中位報酬  Spearman ρ={f12.statistic:+.3f} (p={f12.pvalue:.3f})")

# 更長的歷史：每年『前一年最強3產業』在隔年的表現（產業動能可持續性）
print("\n─ 產業動能可持續性（滾動：每年底看前12M最強/最弱產業，隔12M表現）─")
allm = sorted({m for b in PX.values() for m, *_ in b})
res = []
for yr in range(2017, 2026):
    t0, tm12, tp12 = f"{yr-1}-12", f"{yr-2}-12", f"{yr}-12"
    per = collections.defaultdict(lambda: ([], []))
    for code, bars in PX.items():
        mm = {m: a for m, c, a, v in bars}
        if t0 in mm and tm12 in mm and tp12 in mm and mm[tm12] and mm[t0]:
            ind = META.get(code, {}).get("industry", "?")
            per[ind][0].append(mm[t0] / mm[tm12] - 1)
            per[ind][1].append(mm[tp12] / mm[t0] - 1)
    tt = [(i, np.median(p), np.median(f)) for i, (p, f) in per.items() if len(p) >= 8]
    if len(tt) < 10:
        continue
    tt.sort(key=lambda x: -x[1])
    hi = np.mean([x[2] for x in tt[:3]]) * 100
    lo = np.mean([x[2] for x in tt[-3:]]) * 100
    allmed = np.median([x[2] for x in tt]) * 100
    rho = stats.spearmanr([x[1] for x in tt], [x[2] for x in tt]).statistic
    res.append((yr, hi, lo, allmed, rho))
    print(f"{yr}年：買前一年最強3產業 → {hi:+7.1f}% ；最弱3產業 → {lo:+7.1f}% ；"
          f"全產業中位 {allmed:+6.1f}% ；ρ={rho:+.2f}")
if res:
    print(f"平均：最強3產業 {np.mean([r[1] for r in res]):+.1f}%，最弱3產業 "
          f"{np.mean([r[2] for r in res]):+.1f}%，全體 {np.mean([r[3] for r in res]):+.1f}%；"
          f"平均 ρ={np.mean([r[4] for r in res]):+.3f}，勝出年數 "
          f"{sum(1 for r in res if r[1]>r[3])}/{len(res)}")

# ---------- C. 回撤深度的細節 ----------
print("\n═══ C. 「起漲前回撤要多深」的實況 ═══")
for lo, hi in [(-1, .1), (.1, .25), (.25, .4), (.4, .6), (.6, 2)]:
    seg = [r for r in rows if lo <= r["dd"] < hi]
    if len(seg) < 10:
        continue
    w = [r for r in seg if r["ret"] > 1]
    print(f"  回撤 {lo*100:3.0f}~{hi*100:3.0f}%：{len(seg):>4} 檔，翻倍 {len(w):>3} 檔 "
          f"({len(w)/len(seg)*100:5.1f}%)，中位報酬 {np.median([r['ret'] for r in seg])*100:+6.1f}%")
w_dd = [r["dd"] for r in win]
print(f"  翻倍股回撤分布：25%={np.percentile(w_dd,25)*100:.0f}%  "
      f"中位={np.median(w_dd)*100:.0f}%  75%={np.percentile(w_dd,75)*100:.0f}%  "
      f"（{sum(1 for x in w_dd if x<0.1)} 檔在起漲時根本就在歷史高點附近，回撤<10%）")

# ---------- D. 查核 ----------
print("\n═══ D. 資料查核 ═══")
for c in ["3481", "2330", "2408", "7610", "2383"]:
    if c in PX:
        b = {m: (px, a) for m, px, a, v in PX[c]}
        if START in b:
            print(f"  {c} {META.get(c,{}).get('name',''):<8} 2024-12 收 {b[START][0]:>8.2f} → "
                  f"{PX[c][-1][0]} 收 {PX[c][-1][1]:>8.2f}  "
                  f"（還原息報酬 {(PX[c][-1][2]/b[START][1]-1)*100:+.0f}%）")
print(f"  已抓到的月線最後一根：{sorted({b[-1][0] for b in PX.values()})[-3:]}")
