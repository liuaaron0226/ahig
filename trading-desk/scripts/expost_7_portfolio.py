#!/usr/bin/env python3
"""第五輪：最佳事後模型的組合報酬 vs 0050；下市股缺口；穩健性。"""
import json, os, math, collections, urllib.request
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "expost_cache.json"), encoding="utf-8"))
META, PX = D["meta"], D["px"]
START = "2024-12"
UA = {"User-Agent": "Mozilla/5.0"}

rows = []
for code, bars in PX.items():
    mm = [x[0] for x in bars]
    if START not in mm or bars[-1][0] < "2026-07":
        continue
    i0 = mm.index(START)
    px0, adj0 = bars[i0][1], bars[i0][2]
    if not px0 or not adj0:
        continue
    hist = [x[1] for x in bars[max(0, i0-36):i0+1] if x[1]]
    sh = META.get(code, {}).get("shares") or 0
    vols = [x[3] for x in bars[max(0, i0-11):i0+1] if x[3]]
    rows.append(dict(code=code, name=META.get(code, {}).get("name", ""),
                     ind=META.get(code, {}).get("industry", "?"),
                     ret=bars[-1][2]/adj0-1, px0=px0,
                     mcap=px0*sh/1e8 if sh else None,
                     dd=1-px0/max(hist), off_low=px0/min(hist)-1,
                     r12=adj0/bars[i0-12][2]-1 if i0 >= 12 and bars[i0-12][2] else None,
                     r24=adj0/bars[i0-24][2]-1 if i0 >= 24 and bars[i0-24][2] else None,
                     vol=float(np.median(vols))/1000 if vols else None))
keys = ["px0", "mcap", "dd", "off_low", "r12", "r24", "vol"]
full = [r for r in rows if all(r[k] is not None for k in keys)]
y = np.array([1.0 if r["ret"] > 1 else 0.0 for r in full])
ret = np.array([r["ret"] for r in full])
Xp = np.array([[math.log(max(r["px0"], .1)), math.log(max(r["mcap"], .1)), r["dd"],
                min(r["off_low"], 5), min(r["r12"], 5), min(r["r24"], 5),
                math.log(max(r["vol"], .1))] for r in full])
Xp = (Xp - Xp.mean(0)) / Xp.std(0)
inds = sorted({r["ind"] for r in full})
Xi = np.array([[1.0 if r["ind"] == i else 0.0 for i in inds] for r in full])


def fit(X, yy, lam=1.0, it=200):
    Xb = np.hstack([np.ones((len(X), 1)), X]); w = np.zeros(Xb.shape[1])
    for _ in range(it):
        p = 1/(1+np.exp(-np.clip(Xb@w, -30, 30)))
        g = Xb.T@(yy-p) - lam*w
        H = (Xb*(p*(1-p))[:, None]).T@Xb + lam*np.eye(Xb.shape[1])
        w = w + np.linalg.solve(H, g)
    return w


def cv_scores(X, yy, folds=5, seed=7):
    idx = np.arange(len(yy)); np.random.default_rng(seed).shuffle(idx)
    s = np.zeros(len(yy))
    for f in range(folds):
        te = idx[f::folds]; tr = np.setdiff1d(idx, te)
        s[te] = np.hstack([np.ones((len(te), 1)), X[te]]) @ fit(X[tr], yy[tr])
    return s


print("═══ A. 事後配適的『最佳選股模型』組合報酬 vs 買 0050(+107.2%) ═══")
print(f"{'模型':<20}{'挑幾檔':>7}{'等權平均':>10}{'中位':>10}{'翻倍率':>9}{'贏 0050?':>10}")
print("-" * 68)
for tag, X in (("價格/規模特徵", Xp), ("產業別", Xi), ("產業+價格(最強)", np.hstack([Xi, Xp]))):
    s = cv_scores(X, y)
    o = np.argsort(-s)
    for frac in (0.05, 0.10, 0.20):
        k = int(len(s)*frac)
        rr = ret[o[:k]]
        print(f"{tag:<20}{k:>7}{rr.mean()*100:>9.1f}%{np.median(rr)*100:>9.1f}%"
              f"{(rr > 1).mean()*100:>8.1f}%{'  是' if np.median(rr) > 1.072 else '  否':>10}")
print(f"{'【對照】全市場等權':<20}{len(ret):>7}{ret.mean()*100:>9.1f}%{np.median(ret)*100:>9.1f}%"
      f"{(ret > 1).mean()*100:>8.1f}%{'  否':>10}")
print("注意：這是 5-fold CV，但特徵選擇與模型形式已經看過答案 → 仍偏樂觀。")

print("\n═══ B. 存活者偏誤：下市/終止上市家數 ═══")
try:
    js = json.load(urllib.request.urlopen(urllib.request.Request(
        "https://openapi.twse.com.tw/v1/company/suspendListingCsvAndHtml", headers=UA), timeout=40))
    print("  欄位：", list(js[0].keys()))
    cnt = collections.Counter(str(r.get("下市日期", ""))[:3] for r in js)
    for k in sorted(cnt)[-6:]:
        print(f"  民國 {k} 年終止上市 {cnt[k]} 家")
    n25 = cnt.get("114", 0) + cnt.get("115", 0)
    print(f"  → 2025-2026 合計 {n25} 家下市，相對 {len(rows)} 檔樣本 = {n25/len(rows)*100:.1f}%"
          f"（全部算成 -100% 也只把翻倍率從 {(ret>1).mean()*100:.1f}% 拉到 "
          f"{(ret>1).sum()/(len(ret)+n25)*100:.1f}%）")
except Exception as e:
    print("  抓取失敗：", e)

print("\n═══ C. 穩健性：改用『不還原息』與『只看 2025 全年』結論會不會變 ═══")


def build(s_key, e_key=None, use_adj=True):
    out = []
    for code, bars in PX.items():
        mm = [x[0] for x in bars]
        if s_key not in mm:
            continue
        i0 = mm.index(s_key)
        j = mm.index(e_key) if e_key and e_key in mm else len(bars)-1
        if j <= i0:
            continue
        a0 = bars[i0][2] if use_adj else bars[i0][1]
        a1 = bars[j][2] if use_adj else bars[j][1]
        if not a0 or not a1:
            continue
        hist = [x[1] for x in bars[max(0, i0-36):i0+1] if x[1]]
        sh = META.get(code, {}).get("shares") or 0
        vols = [x[3] for x in bars[max(0, i0-11):i0+1] if x[3]]
        out.append(dict(ind=META.get(code, {}).get("industry", "?"), ret=a1/a0-1,
                        px0=bars[i0][1], mcap=bars[i0][1]*sh/1e8 if sh else None,
                        dd=1-bars[i0][1]/max(hist),
                        vol=float(np.median(vols))/1000 if vols else None))
    return out


def report(tag, rs, thr=1.0):
    w = [r for r in rs if r["ret"] > thr]
    l = [r for r in rs if r["ret"] < 0]
    line = f"  {tag:<30} n={len(rs)} 翻倍{len(w)}({len(w)/len(rs)*100:.1f}%) "
    for lab, k in (("回撤", "dd"), ("市值", "mcap"), ("量", "vol")):
        a = [r[k] for r in w if r[k] is not None]
        b = [r[k] for r in l if r[k] is not None]
        if len(a) > 4 and len(b) > 4:
            u = stats.mannwhitneyu(a, b).statistic/(len(a)*len(b))
            line += f" {lab}AUC={u:.3f}"
    TECH = {"半導體業", "電子零組件業", "其他電子業", "光電業", "電腦及週邊設備業",
            "通信網路業", "電子通路業", "電機機械", "資訊服務業", "數位雲端"}
    tw = sum(1 for r in w if r["ind"] in TECH)/max(len(w), 1)*100
    line += f" 電子佔贏家{tw:.0f}%"
    print(line)


report("主結果 2024-12→now 還原息", build("2024-12"))
report("不還原息", build("2024-12", use_adj=False))
report("只看 2025 全年", build("2024-12", "2025-12"))
report("2025-06 起算", build("2025-06"))
report("門檻改 >200%", build("2024-12"), thr=2.0)
