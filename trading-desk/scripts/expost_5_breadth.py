#!/usr/bin/env python3
"""第四輪：市場廣度、群創自身可辨識度、後段行情是否換產業、關鍵 AUC 的信賴區間。"""
import json, os, collections, urllib.request, datetime
import numpy as np
from scipy import stats

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, "expost_cache.json"), encoding="utf-8"))
META, PX = D["meta"], D["px"]
UA = {"User-Agent": "Mozilla/5.0"}

# TWII 月線
r = json.load(urllib.request.urlopen(urllib.request.Request(
    "https://query1.finance.yahoo.com/v8/finance/chart/%5ETWII?interval=1mo&range=10y",
    headers=UA), timeout=30))["chart"]["result"][0]
TWII = {datetime.datetime.utcfromtimestamp(t).strftime("%Y-%m"): c
        for t, c in zip(r["timestamp"], r["indicators"]["quote"][0]["close"]) if c}

print("═══ A. 市場廣度：20 個月窗口內，有多少比例的個股贏過加權指數 ═══")
print(f"{'起點':<10}{'指數報酬':>10}{'個股中位':>10}{'贏過指數比例':>13}{'翻倍比例':>10}")
print("-" * 55)
out = []
for start in sorted(TWII):
    if not ("2016-01" <= start <= "2024-12"):
        continue
    ms = sorted(TWII)
    i = ms.index(start)
    if i + 20 >= len(ms):
        continue
    end = ms[i + 20]
    ir = TWII[end] / TWII[start] - 1
    rs = []
    for code, bars in PX.items():
        mm = {m: a for m, c, a, v in bars}
        if start in mm and end in mm and mm[start]:
            rs.append(mm[end] / mm[start] - 1)
    if len(rs) < 400 or start[5:] not in ("04", "08", "12"):
        continue
    beat = sum(1 for x in rs if x > ir) / len(rs) * 100
    out.append((start, ir * 100, np.median(rs) * 100, beat,
                sum(1 for x in rs if x > 1) / len(rs) * 100))
    print(f"{start:<10}{ir*100:>9.1f}%{np.median(rs)*100:>9.1f}%{beat:>12.1f}%"
          f"{sum(1 for x in rs if x>1)/len(rs)*100:>9.1f}%")
b = [o[3] for o in out]
print(f"\n歷史『贏過指數比例』中位 {np.median(b):.1f}%，最低 {min(b):.1f}%"
      f"（{min(out,key=lambda x:x[3])[0]}）")

print("\n═══ B. 起點 2024-12 的群創(3481)，在全市場的百分位 ═══")
START = "2024-12"
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
    r12 = adj0/bars[i0-12][2]-1 if i0 >= 12 and bars[i0-12][2] else None
    rows.append(dict(code=code, name=META.get(code, {}).get("name", ""),
                     ind=META.get(code, {}).get("industry", "?"), px0=px0,
                     ret=bars[-1][2]/adj0-1, mcap=px0*sh/1e8 if sh else None,
                     dd=1-px0/max(hist), off_low=px0/min(hist)-1, r12=r12,
                     vol=float(np.median(vols))/1000 if vols else None))
tgt = {r["code"]: r for r in rows}
for c in ["3481", "2408", "2383", "8021"]:
    if c not in tgt:
        continue
    t = tgt[c]
    p = {}
    for k in ["px0", "mcap", "dd", "off_low", "r12", "vol"]:
        v = [x[k] for x in rows if x[k] is not None]
        p[k] = stats.percentileofscore(v, t[k]) if t[k] is not None else float("nan")
    print(f"  {c} {t['name']:<8}({t['ind']}) 報酬 {t['ret']*100:+.0f}%  百分位："
          f"股價{p['px0']:.0f} 市值{p['mcap']:.0f} 回撤{p['dd']:.0f} "
          f"離低點{p['off_low']:.0f} 前12M{p['r12']:.0f} 量{p['vol']:.0f}")

print("\n═══ C. 關鍵虛無結果的信賴區間（bootstrap, 2000 次）═══")
win = [r for r in rows if r["ret"] > 1]
lose = [r for r in rows if r["ret"] < 0]


def auc_pt(a, b):
    return stats.mannwhitneyu(a, b, alternative="two-sided").statistic / (len(a)*len(b))


rng = np.random.default_rng(1)
for lab, k in [("距36M高點回撤", "dd"), ("距36M低點漲幅", "off_low"),
               ("起點股價", "px0"), ("起點市值", "mcap"), ("成交量", "vol")]:
    a = np.array([r[k] for r in win if r[k] is not None], float)
    b = np.array([r[k] for r in lose if r[k] is not None], float)
    bs = [auc_pt(rng.choice(a, len(a)), rng.choice(b, len(b))) for _ in range(2000)]
    print(f"  {lab:<14} AUC={auc_pt(a,b):.3f}  95%CI=[{np.percentile(bs,2.5):.3f}, "
          f"{np.percentile(bs,97.5):.3f}]  {'← 含 0.5，無鑑別力' if np.percentile(bs,2.5)<0.5<np.percentile(bs,97.5) else ''}")

print("\n═══ D. 後段行情（2025-12 → 2026-08）是同一批產業，還是換手到落後股？═══")
S2 = "2025-12"
sub = []
for code, bars in PX.items():
    mm = [x[0] for x in bars]
    if S2 not in mm or bars[-1][0] < "2026-07":
        continue
    i = mm.index(S2)
    if not bars[i][2]:
        continue
    sub.append((META.get(code, {}).get("industry", "?"), bars[-1][2]/bars[i][2]-1))
by = collections.defaultdict(list)
for i, v in sub:
    by[i].append(v)
print(f"（8 個月，n={len(sub)}，全體中位 {np.median([v for _, v in sub])*100:+.1f}%，"
      f"漲逾 50% 比例 {sum(1 for _,v in sub if v>0.5)/len(sub)*100:.1f}%）")
tt = [(i, len(v), np.median(v)*100, sum(1 for x in v if x > .5)/len(v)*100)
      for i, v in by.items() if len(v) >= 8]
print(f"{'產業':<16}{'檔數':>5}{'中位':>9}{'漲>50%比例':>12}")
for t in sorted(tt, key=lambda x: -x[2])[:10]:
    print(f"{t[0]:<16}{t[1]:>5}{t[2]:>8.1f}%{t[3]:>11.1f}%")
print("  …")
for t in sorted(tt, key=lambda x: -x[2])[-5:]:
    print(f"{t[0]:<16}{t[1]:>5}{t[2]:>8.1f}%{t[3]:>11.1f}%")

print("\n═══ E. 若在 2024-12 只買『前一年跌最慘 / 最便宜』的股票會怎樣 ═══")
for lab, key, rev in (("前12M報酬最差 100 檔", "r12", False),
                      ("股價最低 100 檔", "px0", False),
                      ("市值最小 100 檔", "mcap", False),
                      ("回撤最深 100 檔", "dd", True)):
    v = sorted([r for r in rows if r[key] is not None], key=lambda r: -r[key] if rev else r[key])[:100]
    rr = [r["ret"] for r in v]
    print(f"  {lab:<20} 翻倍率 {sum(1 for x in rr if x>1)/len(rr)*100:5.1f}%  "
          f"中位 {np.median(rr)*100:+7.1f}%  平均 {np.mean(rr)*100:+7.1f}%")
allr = [r["ret"] for r in rows]
print(f"  {'【對照】全市場等權':<20} 翻倍率 {sum(1 for x in allr if x>1)/len(allr)*100:5.1f}%  "
      f"中位 {np.median(allr)*100:+7.1f}%  平均 {np.mean(allr)*100:+7.1f}%")
print(f"  {'【對照】買 0050':<20} 報酬 +107.2%")
